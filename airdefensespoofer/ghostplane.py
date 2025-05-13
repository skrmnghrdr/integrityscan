#!/usr/bin/python3

import socket
import time
import random
import math
import argparse
import binascii

#change this later since this is africa lmao
AUGUSTA_LAT = 33.4740 
AUGUSTA_LON = -81.9748

#https://github.com/tinmarco
#buy this dude a coffee for the skeleton of the program
# Generate a Mode S message (ADS-B position report)

def crc24(msg):
    """
    Calculate CRC-24 for ADS-B messages.
    This is an accurate implementation of the specific CRC used in ADS-B.
    """
    #constant thing, do not change
    CRC_POLYNOMIAL = 0x1FFF409
    crc = 0

    for byte in msg:
        crc ^= (byte << 16)
        for _ in range(8):
            crc <<= 1
            if crc & 0x1000000:
                crc ^= CRC_POLYNOMIAL
    return crc & 0xFFFFFF

def encode_altitude(altitude_ft):

    """
    Encode altitude according to ADS-B protocol.
    For TC=11 (airborne position), uses Q-bit=1 for 25ft encoding.
    Returns:
        12-bit encoded altitude
    """

    # Convert to appropriate value (N)
    n = int((altitude_ft / 25) - 1)

    # Ensure it's within valid range
    n = max(0, min(n, 0x7FF))  # 11 bits max

    # Set Q-bit (25ft resolution)
    q_bit = 1

    # Combine into 12-bit value
    altitude_encoded = (q_bit << 11) | n
    return altitude_encoded



def encode_cpr_position(lat, lon, is_odd):

    """
    Encode position using Compact Position Reporting (CPR).
    This format is designed to efficiently encode lat/lon in ADS-B.
    Returns:
        (lat_cpr, lon_cpr) - 17-bit integers
    """
    #THERE MIGHT BE SOMETHING WRONG HERE AS WELL WITH THE GENERATION
    if is_odd:
        # Odd frame encoding (uses different zones)
        lat_index = int(((lat % 90) / 90.0) * 131072)  # 2^17 = 131072
        lon_index = int(((lon % 360) / 360.0) * 131072)
    else:
        # Even frame encoding
        lat_index = int(((lat % 90) / 90.0) * 131072)
        lon_index = int(((lon % 360) / 360.0) * 131072)
    # Ensure 17-bit values
    
    lat_cpr = lat_index & 0x1FFFF  # 17 bits
    lon_cpr = lon_index & 0x1FFFF  # 17 bits
    
    print("LAT CPT {} ::: LONG CPR {}".format(str(lat_cpr), str(lon_cpr)) )
    return lat_cpr, lon_cpr


def update_aircraft_position(aircraft):

    """Update aircraft position based on speed and heading"""
    # Calculate time since last update
    now = time.time()
    elapsed = now - aircraft['last_update']
    aircraft['last_update'] = now



    # Convert speed from knots to degrees per second
    # This is an approximation: 1 knot ≈ 0.000008 degrees per second at equator
    speed_deg_per_sec = aircraft['speed'] * 0.000008 * elapsed

    # Calculate new position
    heading_rad = math.radians(aircraft['heading'])
    aircraft['lat'] += math.cos(heading_rad) * speed_deg_per_sec
    aircraft['lon'] += math.sin(heading_rad) * speed_deg_per_sec / math.cos(math.radians(aircraft['lat']))

    # Update altitude (ft/min to ft/sec * elapsed seconds)
    aircraft['alt'] += (aircraft['climb_rate'] / 60.0) * elapsed
    # Toggle odd/even frame
    aircraft['odd_frame'] = not aircraft['odd_frame']
    return aircraft



def generate_airborne_position_message(icao, lat, lon, altitude, is_odd):
    """
    Generate a complete ADS-B airborne position message (DF17/TC11).
    Args:
        icao: ICAO address (24-bit) as string or int
        lat: Latitude in degrees
        lon: Longitude in degrees
        altitude: Altitude in feet
        is_odd: CPR encoding (True=odd, False=even)
    Returns:
        Complete ADS-B message in Beast AVR format
    """
    # Convert ICAO to integer if it's a string
    if isinstance(icao, str):
        icao_int = int(icao, 16)
    else:
        icao_int = icao
    # Encode altitude
    altitude_encoded = encode_altitude(altitude)
    # Encode position
    lat_cpr, lon_cpr = encode_cpr_position(lat, lon, is_odd)

    # Message type - DF17 with CA=5
    df_ca = 0x8D


    # Type code 11 (airborne position) with surveillance status 0
    tc = 0x58  # TC=11 (01011), subtype=0, surveillance status=0
    # Create message data
    # Format (bits):
    # DF(5) + CA(3) + ICAO(24) + TC(5) + SS(3) + ALT(12) + T(1) + F(1) + CPR_LAT(17) + CPR_LON(17)

    # Create the raw message bytes
    msg_bytes = bytearray(11)  # 11 bytes for the message (excluding CRC)
    # Byte 0: DF + CA
    msg_bytes[0] = df_ca

    # Bytes 1-3: ICAO address
    msg_bytes[1] = (icao_int >> 16) & 0xFF
    msg_bytes[2] = (icao_int >> 8) & 0xFF
    msg_bytes[3] = icao_int & 0xFF


    # Byte 4: TC + first 3 bits of altitude
    msg_bytes[4] = tc

    # Bytes 5-6: Rest of altitude + T bit + F bit + start of lat_cpr
    # Altitude bits: 12 bits total, 3 in byte 4, 9 in bytes 5-6
    # T bit is always 0 (not barometric altitude from a different source)
    # F bit is 0 for even, 1 for odd
    t_bit = 0
    f_bit = 1 if is_odd else 0


    # Extract altitude, T, F, and lat_cpr bits for these bytes
    msg_bytes[5] = ((altitude_encoded >> 4) & 0xFF)
    msg_bytes[6] = ((altitude_encoded & 0x0F) << 4) | (t_bit << 3) | (f_bit << 2) | ((lat_cpr >> 15) & 0x03)


    # Bytes 7-8: Rest of lat_cpr
    #might be something wrong here
    msg_bytes[7] = (lat_cpr >> 7) & 0xFF
    msg_bytes[8] = ((lat_cpr & 0x7F) << 1) | ((lon_cpr >> 16) & 0x01)


    # Bytes 9-10: Rest of lon_cpr
    #might be something wrong here
    msg_bytes[9] = (lon_cpr >> 8) & 0xFF
    msg_bytes[10] = lon_cpr & 0xFF


    # Calculate CRC
    crc_value = crc24(msg_bytes)


    # Add CRC bytes
    msg_bytes.append((crc_value >> 16) & 0xFF)
    msg_bytes.append((crc_value >> 8) & 0xFF)
    msg_bytes.append(crc_value & 0xFF)
    # Format in Beast AVR format
    message_hex = binascii.hexlify(msg_bytes).decode('ascii').upper()
    avr_message = f"*{message_hex};"
    print("AVR MESSAGE: {}".format(str(avr_message)))
    pass
    return avr_message

def generate_aircraft():

    """Generate a realistic aircraft with ICAO address"""
    # Generate a random ICAO address (24-bit)
    #your aircraft name
    icao = f"{random.randint(0, 0xFFFFFF):06X}"



    # Create the aircraft object
    return {
        'icao': icao,
        'alt': random.choice([3500, 7500, 10000, 15000, 20750, 25000, 32000, 35000]),
        'speed': random.randint(250, 500),
        'heading': random.randint(0, 359),
        'climb_rate': random.choice([-500, -300, -100, 0, 0, 0, 100, 300, 500]),
        'lat': AUGUSTA_LAT,# + random.uniform(-0.5, 0.5),
        #try not to randomize sshit first
        'lon': AUGUSTA_LON,# + random.uniform(-0.5, 0.5),
        'odd_frame': False,  # Start with even frame
        'last_update': time.time()
    }


def send_to_dump1090(aircraft_list, host='localhost', port=30001):
    """Send ADS-B messages to dump1090"""
    try:
        # Connect to dump1090 AVR input port
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        print(f"Connected to dump1090 AVR input at {host}:{port}")
        # Main simulation loop
        while True:
            for aircraft in aircraft_list:
                # Update aircraft position
                update_aircraft_position(aircraft)
                # Generate ADS-B message
                #meat and potatoes of what we werre tying to accomplish
                message = generate_airborne_position_message(
                    aircraft['icao'],
                    aircraft['lat'],
                    aircraft['lon'],
                    aircraft['alt'],
                    aircraft['odd_frame']
                )


                try:
                    # Send message
                    sock.sendall((message + "\n").encode('ascii'))
                    print(f"Sent: {message[:20]}...{message[-10:]} (ICAO: {aircraft['icao']}, Alt: {int(aircraft['alt'])}ft, Pos: {aircraft['lat']:.4f},{aircraft['lon']:.4f}, Frame: {'odd' if aircraft['odd_frame'] else 'even'})")

                    # Important: Send the opposite frame immediately after for position decoding
                    # Slight position adjustment to account for time difference
                    aircraft['odd_frame'] = not aircraft['odd_frame']
                    # Generate the other frame with the same position
                    opposite_message = generate_airborne_position_message(
                        aircraft['icao'],
                        aircraft['lat'],
                        aircraft['lon'],
                        aircraft['alt'],
                        aircraft['odd_frame']
                    )

                    #AIRCRAFT LON -81.97040174175896::
                    #AIRCRAFT LAT: 33.475121633821104

                    print("AIRCRAFT LON {}::".format(str(aircraft['lon'])))
                    print("AIRCRAFT LAT: {}".format(str(aircraft['lat'])))
                    # Send the opposite frame

                    sock.sendall((opposite_message + "\n").encode('ascii'))

                    print(f"    + Opposite frame (ICAO: {aircraft['icao']}, Frame: {'odd' if aircraft['odd_frame'] else 'even'})")
                    # Reset to original frame setting
                    aircraft['odd_frame'] = not aircraft['odd_frame']
                except Exception as e:
                    print(f"Error sending message: {e}")
                # Pause between aircraft updates
                time.sleep(random.uniform(0.05, 0.1))

            # Dynamic traffic management
            if random.random() < 0.05:  # 5% chance each cycle
                if len(aircraft_list) < 15 and random.random() < 0.7:
                    # Add a new aircraft
                    new_aircraft = generate_aircraft()
                    aircraft_list.append(new_aircraft)
                    print(f"New aircraft added: {new_aircraft['icao']}")
                elif len(aircraft_list) > 5:
                    # Remove an aircraft
                    removed = aircraft_list.pop(random.randint(0, len(aircraft_list)-1))
                    print(f"Aircraft removed: {removed['icao']}")
            # Pause between complete update cycles
            time.sleep(1)
            pass
    except KeyboardInterrupt:
        print("Simulation stopped by user")
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        sock.close()
        print("Connection closed")


def main():

    parser = argparse.ArgumentParser(description='ADS-B Traffic Generator for Augusta, GA')

    parser.add_argument('--host', default='localhost', help='dump1090 host')

    parser.add_argument('--port', type=int, default=30001, help='dump1090 AVR input port (default: 30001)')
    parser.add_argument('--aircraft', type=int, default=10, help='Number of aircraft to simulate')
    args = parser.parse_args()
    print(f"Simulating {args.aircraft} aircraft in the Augusta, GA area")
    print(f"Sending data to dump1090 at {args.host}:{args.port}")
    print("Press Ctrl+C to stop the simulation")
    # Generate initial aircraft
    aircraft_list = [generate_aircraft() for _ in range(args.aircraft)]
    # Start sending data
    send_to_dump1090(aircraft_list, args.host, args.port)
    pass
if __name__ == "__main__":
    main()