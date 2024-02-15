import folium
import webbrowser
import polyline
import requests

OSRM_HOST = "localhost"  # ROSRM server IP or hostname
OSRM_PORT = "5000"       # Port of OSRM server is listening on
  
start_point = (35.918915, 14.372416)  # MGARR
end_point = (35.931628, 14.453427)  # TOP OF THE WORLD


url = f"http://{OSRM_HOST}:{OSRM_PORT}/route/v1/driving/{start_point[1]},{start_point[0]};{end_point[1]},{end_point[0]}?overview=full"
print(url)
response = requests.get(url)  

if response.status_code == 200:
    
    route_geometry = response.json()['routes'][0]['geometry'] # Extract the route geometry from the response (encoded polyline)
    route = polyline.decode(route_geometry) 
    m = folium.Map(location=[start_point[0], start_point[1]], zoom_start=12) # Create a Folium map centered around the start point
    folium.PolyLine(route, color="blue", weight=3, opacity=0.7).add_to(m) # Add the route to the map as a polyline
    m.save("map.html")
    webbrowser.open("map.html")
else:
    print("Failed to retrieve the route. Check your OSRM instance and URL.")