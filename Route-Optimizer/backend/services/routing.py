import math

import requests


OSRM_URL = "https://router.project-osrm.org/route/v1/driving/"


def _distance_m(lat1, lng1, lat2, lng2):
    lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    hav = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
    return 6371000 * 2 * math.asin(math.sqrt(hav))


def _point_segment_distance_m(point, start, end):
    px, py = point["lng"], point["lat"]
    ax, ay = start["lng"], start["lat"]
    bx, by = end["lng"], end["lat"]
    dx = bx - ax
    dy = by - ay
    if dx == 0 and dy == 0:
        return _distance_m(point["lat"], point["lng"], start["lat"], start["lng"])
    t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    projected = {"lng": ax + t * dx, "lat": ay + t * dy}
    return _distance_m(point["lat"], point["lng"], projected["lat"], projected["lng"])


def _blocked_route_segment(start, end, avoid_points):
    for block in avoid_points or []:
        radius = float(block.get("radius_meters", 700))
        if _point_segment_distance_m(block, start, end) <= radius + 450:
            return block
    return None


def _detour_waypoint(start, end, block):
    dx = end["lng"] - start["lng"]
    dy = end["lat"] - start["lat"]
    length = math.sqrt(dx * dx + dy * dy) or 1
    offset = max(float(block.get("radius_meters", 800)) / 111000, 0.012)
    return {
        "lat": block["lat"] + (dx / length) * offset,
        "lng": block["lng"] - (dy / length) * offset,
    }


def _request_route(points):
    coords = ";".join(f"{p['lng']},{p['lat']}" for p in points)
    url = f"{OSRM_URL}{coords}?overview=full&geometries=geojson"
    response = requests.get(url, timeout=7)
    data = response.json()
    if data.get("code") != "Ok":
        return None
    route = data["routes"][0]
    return {
        "geometry": route["geometry"],
        "distance": route["distance"],
        "duration": route["duration"],
    }


def _fallback_route(points):
    distance = 0
    for index in range(len(points) - 1):
        distance += _distance_m(points[index]["lat"], points[index]["lng"], points[index + 1]["lat"], points[index + 1]["lng"])
    return {
        "geometry": {"type": "LineString", "coordinates": [[p["lng"], p["lat"]] for p in points]},
        "distance": distance * 1.22,
        "duration": (distance * 1.22) / 8.5,
    }


def get_route(start_lat, start_lng, end_lat, end_lng, avoid_points=None):
    start = {"lat": start_lat, "lng": start_lng}
    end = {"lat": end_lat, "lng": end_lng}
    blocked_by = _blocked_route_segment(start, end, avoid_points)

    points = [start, end]
    if blocked_by:
        points = [start, _detour_waypoint(start, end, blocked_by), end]

    try:
        route = _request_route(points)
    except requests.RequestException:
        route = None

    if not route:
        route = _fallback_route(points)

    route["rerouted"] = bool(blocked_by)
    route["blocked_by"] = blocked_by["id"] if blocked_by else None
    return route
