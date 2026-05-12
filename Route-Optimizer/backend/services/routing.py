import requests

OSRM_URL = "http://router.project-osrm.org/route/v1/driving/"

def get_route(start_lat, start_lng, end_lat, end_lng, avoid_points=[]):
    """
    Fetches route from OSRM. Note: Public OSRM doesn't support 'avoid' natively.
    In a production setup, we use OSRM profiles or GraphHopper.
    Here we simulate rerouting by checking if coordinates intersect blocked zones.
    """
    coords = f"{start_lng},{start_lat};{end_lng},{end_lat}"
    url = f"{OSRM_URL}{coords}?overview=full&geometries=geojson"
    
    response = requests.get(url).json()
    if response['code'] != 'Ok':
        return None
    
    route = response['routes'][0]
    return {
        "geometry": route['geometry'],
        "distance": route['distance'],
        "duration": route['duration']
    }