import requests
import json
import os 

# OSRM instance details
osrm_host = "localhost"  # ROSRM server IP or hostname
osrm_port = "5000"       # Port of OSRM server is listening on

start_coords = "14.4535735,35.9209566"  
end_coords = "14.4034303,35.8837824" #Random bus stops in Malta

url = f"http://{osrm_host}:{osrm_port}/route/v1/driving/{start_coords};{end_coords}?overview=false&steps=true"
response = requests.get(url)

print("=================================== TEST 1 ===================================================")
print("Testing OSRM with 2 coordinates")

print(url)
# Parsing the response
if response.status_code == 200:
    data = response.json()
    with open('Tests/osrmTests/test1.json', 'w+') as f:
        json.dump(data,f)
    distance = data['routes'][0]['distance']  # Distance in meters
    print(f"Distance: {distance/1000} km")  # Convert meters to kilometers
else:
    print("Failed to get a response from the OSRM server")


print("=================================== TEST 2 ===================================================")
print("Testing OSRM with 3 coordinates")

start_coords = "14.4535735,35.9209566"  
middle_coords = "14.5072541,35.8708978" #Longitudinal and latitudinal coordinates
end_coords = "14.4034303,35.8837824" #Random bus stops in Malta

url = f"http://{osrm_host}:{osrm_port}/route/v1/driving/{start_coords};{middle_coords};{end_coords}?overview=false&steps=true"
response = requests.get(url)

print(url)
# Parsing the response
if response.status_code == 200:
    data = response.json()
    #Save Data to a file
    with open('Tests/osrmTests/test2.json', 'w+') as f:
        json.dump(data,f)
    distance = data['routes'][0]['distance']  # Distance in meters
    print(f"Distance: {distance/1000} km")  # Convert meters to kilometers
else:
    print("Failed to get a response from the OSRM server")
    