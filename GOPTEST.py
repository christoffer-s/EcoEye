import time
import serial
import folium
from folium.plugins import HeatMap

krtdata = []

ser = serial.Serial(
    port='/dev/ttyAMA0',
    baudrate=9600, 
    parity=serial.PARITY_NONE,
    bytesize=serial.EIGHTBITS,
    timeout=1
)



def getMap(kartdata):
    mapObj = folium.Map(location = [63.8728448,8.6369276], 
                    zoom_start = 11, 
                    zoom_control = False)
    HeatMap(kartdata).add_to(mapObj)
    return mapObj

def parse_gpgga(data):
    #Dekoder en GPGGA-setningene. Returnerer latitude(bredde), longitute(lengde), og fix-status
    parts = data.split(",")
    if parts[6] == '0':  # Sjekker fix-status (0 = ingen fix)
        return None 
    lat = convert_to_decimal(parts[2], parts[3])
    lon = convert_to_decimal(parts[4], parts[5])
    return lat, lon

def parse_gprmc(data):
    #Dekoder en GPRMC-setning. Returnerer latitude(bredde), longitute(lengde), og hastighet
    parts = data.split(",")
    if parts[2] != 'A':  # Sjekker status (A = gyldig, V = ugyldig)
        return None
    lat = convert_to_decimal(parts[3], parts[4])
    lon = convert_to_decimal(parts[5], parts[6])
    # Hastighet(knop, så konvertert til km/t)
    speed_knots = float(parts[7])
    speed_kmh = speed_knots * 1.852
    return lat, lon, speed_kmh

def convert_to_decimal(coord, direction):
    # Konverterer lat/long koordinater fra NMEA til desimal, for folium
    if not coord:
        return None
    # Grader er de første to sifrene for breddegrad og første tre sifre for lengdegrad
    if direction in ['N', 'S']:  # Lat
        degrees = int(coord[:2])
        minutes = float(coord[2:])
    elif direction in ['E', 'W']:  # Long
        degrees = int(coord[:3])
        minutes = float(coord[3:])
    # Konverter til desimal
    decimal = degrees + minutes / 60
    if direction in ['S', 'W']:
        decimal = -decimal
    return decimal
def kart():
    while True:
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        if line.startswith("$GPGGA"):
            result = parse_gpgga(line)
            if result:
                lat, lon = result
                print(f"Breddegrad: {lat}, Lengdegrad: {lon}")
                if intens is None:
                    intens = 0
                koordliste = [lat, lon, intens]
                krtdata.append(koordliste)
                return (getMap(krtdata))
            else:
                print("Ingen fix")
        elif line.startswith("$GPRMC"):
            result = parse_gprmc(line)
            if result:
                lat, lon, speed = result
                print(f"Breddegrad: {lat}, Lengdegrad: {lon}, Hastighet: {speed:.2f} km/t")
                if intens is None:
                    intens = 0
                koordliste = [lat, lon, intens]
                krtdata.append(koordliste)
                return (getMap(krtdata))




