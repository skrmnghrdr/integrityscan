import math
import socket
import struct
import binascii

def encode_latitude(lat, phase=1):
    """
    Encodes latitude using CPR (Compact Position Reporting) encoding.
    
    :param lat: Latitude in degrees (float)
    :param phase: Phase of the CPR (1 for odd, 2 for even)
    :return: CPR encoded latitude (17-bit integer)
    """
    lat_index = math.floor(((lat % 90) / 90.0) * 131072)

    if phase == 2:  # Even frame
        lat_index += 65536  # Shift for even frame
    
    lat_index = lat_index & 0x1FFFF
    return lat_index

def encode_longitude(lon, phase=1):
    """
    Encodes longitude using CPR (Compact Position Reporting) encoding.
    
    :param lon: Longitude in degrees (float)
    :param phase: Phase of the CPR (1 for odd, 2 for even)
    :return: CPR encoded longitude (17-bit integer)
    """
    lon_index = math.floor(((lon % 180) / 180.0) * 131072)

    if phase == 2:  # Even frame
        lon_index += 65536  # Shift for even frame

    lon_index = lon_index & 0x1FFFF
    return lon_index

def encode_message(icao_address, lat, lon, phase=1):
    """
    Encodes a full ADS-B message with ICAO address, CPR-encoded lat/lon, and CRC.
    
    :param icao_address: ICAO address (24-bit integer)
    :param lat: Latitude in degrees (float)
    :param lon: Longitude in degrees (float)
    :param phase: Phase of the CPR (1 for odd, 2 for even)
    :return: Full encoded ADS-B message in hex format
    """
    lat_encoded = encode_latitude(lat, phase)
    lon_encoded = encode_longitude(lon, phase)

    # ICAO address (24 bits, fixed for one aircraft)
    icao_hex = format(icao_address, '06X')

    # CPR lat and lon encoded to binary
    lat_bin = format(lat_encoded, '017b')
    lon_bin = format(lon_encoded, '017b')

    # Combine everything into a bitstream
    full_message_bin = lat_bin + lon_bin
    message_data = icao_hex + full_message_bin

    # Convert the binary message into a byte array
    byte_message = bytearray.fromhex(icao_hex) + struct.pack('>Q', int(full_message_bin, 2))

    # Calculate the CRC-24A checksum
    crc = crc24a(message_data)

    # Add the CRC at the end
    full_message = byte_message + crc
    full_message_hex = full_message.hex().upper()

    return full_message_hex

def crc24a(data):
    """
    Calculate the CRC-24A checksum for the given data.
    :param data: The data string to calculate CRC.
    :return: CRC-24A as bytes
    """
    crc = 0xFFFFFF
    polynomial = 0x864CFB
    for byte in data.encode('utf-8'):
        crc ^= byte << 16
        for _ in range(8):
            if crc & 0x800000:
                crc = (crc << 1) ^ polynomial
            else:
                crc = crc << 1
            crc &= 0xFFFFFF
    return struct.pack('>I', crc)

def send_message_to_port(message, host='127.0.0.1', port=30001):
    """
    Send the encoded ADS-B message to a UDP port (e.g., dump1090).
    :param message: The encoded ADS-B message in hex format.
    :param host: The destination host for the UDP message.
    :param port: The port on which to send the message (default is 30001 for dump1090).
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.sendto(bytes.fromhex(message), (host, port))
        print(f"Message sent to {host}:{port}")

# Example usage
icao_address = 0x8D40621D58C382D6  # Example ICAO address (24-bit)
latitude = 33.4740  # Augusta, Georgia latitude
longitude = -81.9748  # Augusta, Georgia longitude

# Odd frame encoding (phase 1)
odd_cpr_message = encode_message(icao_address, latitude, longitude, phase=1)
print(f"Odd Frame CPR Message (Hex): {odd_cpr_message}")

# Send the message to port 30001 (replace with the correct IP if needed)
send_message_to_port(odd_cpr_message)
