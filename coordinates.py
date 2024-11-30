# get_location.py

import requests

def get_coordinates_from_ip():
    try:
        # Fetch IP details from ipinfo.io
        response = requests.get("https://ipinfo.io")
        data = response.json()

        # Get the coordinates (latitude, longitude) from the IP info response
        coordinates = data.get("loc", "").split(",")
        
        if len(coordinates) == 2:
            latitude = float(coordinates[0])
            longitude = float(coordinates[1])
            return latitude, longitude
        else:
            print("Could not extract coordinates from the response.")
            return None, None

    except requests.exceptions.RequestException as e:
        print(f"Error fetching IP info: {e}")
        return None, None
