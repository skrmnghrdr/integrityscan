import math

def encode_latitude(lat, phase=1):
    """
    Encodes latitude using CPR (Compact Position Reporting) encoding.
    
    :param lat: Latitude in degrees (float)
    :param phase: Phase of the CPR (1 for odd, 2 for even)
    :return: CPR encoded latitude (17-bit integer)
    """
    # Latitude is scaled to a 131072 step (17-bit range)
    lat_index = math.floor(((lat % 90) / 90.0) * 131072)

    # Apply different phase offsets for odd/even frame
    if phase == 2:  # Even frame
        lat_index += 65536  # Shift by half the grid size (for even frame)
    
    # Mask to ensure 17 bits
    lat_index = lat_index & 0x1FFFF
    
    return lat_index


def encode_longitude(lon, phase=1):
    """
    Encodes longitude using CPR (Compact Position Reporting) encoding.
    
    :param lon: Longitude in degrees (float)
    :param phase: Phase of the CPR (1 for odd, 2 for even)
    :return: CPR encoded longitude (17-bit integer)
    """
    # Longitude is scaled to a 131072 step (17-bit range)
    lon_index = math.floor(((lon % 180) / 180.0) * 131072)

    # Apply different phase offsets for odd/even frame
    if phase == 2:  # Even frame
        lon_index += 65536  # Shift by half the grid size (for even frame)

    # Mask to ensure 17 bits
    lon_index = lon_index & 0x1FFFF
    
    return lon_index


def cpr_encode(lat, lon, phase=1):
    """
    Encodes a given latitude and longitude into CPR format (odd or even frame).
    
    :param lat: Latitude in degrees (float)
    :param lon: Longitude in degrees (float)
    :param phase: Phase of the CPR (1 for odd, 2 for even)
    :return: CPR encoded latitude and longitude as hexadecimal string
    """
    lat_encoded = encode_latitude(lat, phase)
    lon_encoded = encode_longitude(lon, phase)
    
    # Convert to binary string
    lat_bin = format(lat_encoded, '017b')
    lon_bin = format(lon_encoded, '017b')
    
    # Combine latitude and longitude binary to a single string
    cpr_message_bin = lat_bin + lon_bin
    
    # Convert to hex
    cpr_message_hex = hex(int(cpr_message_bin, 2))[2:].upper()

    return cpr_message_hex


# Example usage
#
#AUGUSTA_LAT = 33.4740 
#AUGUSTA_LON = -81.9748
latitude = 33.4740  # San Francisco latitude
longitude = -81.9748  # San Francisco longitude

# Odd frame encoding (phase 1)
odd_cpr = cpr_encode(latitude, longitude, phase=1)
print(f"Odd Frame CPR: {odd_cpr}")

# Even frame encoding (phase 2)
even_cpr = cpr_encode(latitude, longitude, phase=2)
print(f"Even Frame CPR: {even_cpr}")
