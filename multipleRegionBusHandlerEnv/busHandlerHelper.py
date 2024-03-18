from  classesDefinations import Cords,Vehicle,Request
from urllib3.util import Retry
from requests.adapters import HTTPAdapter
import copy
import requests

CAPACITY = 5
BUS_ORIGIN = Cords(35.8942679, 14.5086503) #CORDS OF THE 15 VALLETTA BUS BAY)
BUS_STOP_DATA_PATH = "C:/Users/lukec/Documents/Thesis/BusRouting/FYP-Flexible-Bus/Data/BusStopsMalta/clustered.json"

OSRM_HOST = "localhost"  # ROSRM server IP or hostname
OSRM_PORT = "5000"       # Port of OSRM server is listening on
SESSION = requests.Session()
RETRY = Retry(connect=5, read=5, backoff_factor=0.3)
ADAPTER = HTTPAdapter(max_retries=RETRY)
SESSION.mount('http://', ADAPTER)
SESSION.mount('https://', ADAPTER)

from datetime import time, datetime, timedelta
import json
import math
import random
import requests

#Rendering packages
import ipyleaflet
import polyline
from ipyleaflet import Map,AwesomeIcon,Marker,Polyline


def divide_time_interval(n):
    # Define start and end times
    start_time = datetime.strptime("08:00 AM", "%I:%M %p")
    end_time = datetime.strptime("12:00 AM", "%I:%M %p")

    # Calculate total duration in seconds
    total_duration = (end_time - start_time).seconds

    # Calculate duration of each interval in seconds
    interval_duration = total_duration / n

    # Generate time intervals
    intervals = []
    start = time(8, 0)
    datetime_obj = datetime.combine(datetime.today(), start)
    for i in range(n):
        interval_start = datetime_obj + timedelta(seconds=i * interval_duration)
        intervals.append(interval_start)
    return intervals

class BusHandler():
    def __init__(self, vehicleAmount, numberOfRequests):
        self.clusterData = self._getClusterData()
        self.vehicles = self._initVehiles(vehicleAmount)
        self.requests = self._initRequests(numberOfRequests)
        # self.currentRequest = self.requests[0]
        self.currentRequestIndex = 0
        self.rejectedRequests = []
        self.acceptedRequests = [] 
        self.map = None
        #Uncomment to render the map
        self._initMap()
        self.renderRoutes()

    def __str__ (self):
        stringOutput = "==========================================\n Vehicles: \n"
        for vehile in self.vehicles:
            stringOutput += str(vehile) + "\n"
        stringOutput += "==========================================\n Requests: \n"
        for request in self.requests:
            stringOutput += str(request) + "\n"
        stringOutput += "==========================================\n"
        return stringOutput
    def __eq__ (self, busHandler2):
        dict1 = {}
        for i in range(len(self.vehicles)):
            dict1[i] = [node.getRequestId() for node in self.vehicles[i].route.getListOfCords()]
        dict2 = {}
        for i in range(len(busHandler2.vehicles)):
            dict2[i] = [node.getRequestId() for node in busHandler2.vehicles[i].route.getListOfCords()]
        return dict1 == dict2

    def _getClusterData(self):
        self.clusterData = json.load(open(BUS_STOP_DATA_PATH))
        self.clusterAmount = self.clusterData["clusters"]
        return self.clusterData

    def _initVehiles(self, vehicleAmount):
        vehicles = []
        if vehicleAmount < self.clusterAmount:
            raise ValueError("Vehicle amount cannot be less than cluster amount")
        
        #Get the amount of bus stop in each cluster
        busStopsClusterCount = {}
        for cluster in self.clusterData["cluster_data"]:
            busStopsClusterCount[cluster] = len(self.clusterData["cluster_data"][cluster])
        
        totlaBusStops = sum(busStopsClusterCount.values())
        clusterRatios = {cluster: items/totlaBusStops for cluster, items in busStopsClusterCount.items()}
        
        #Distribute the bus stops to the vehicles
        distributedVehicles = {cluster: 1 for cluster in self.clusterData["cluster_data"]}
        remainingVehicles = vehicleAmount - self.clusterAmount

        for cluster, proportion in clusterRatios.items():
            additionalVehicles = round(proportion * remainingVehicles)
            distributedVehicles[cluster] += additionalVehicles

        #Check that the sum = 10
        if sum(distributedVehicles.values()) != vehicleAmount:
            raise ValueError("The vehicles are not distributed correctly")

        #Get the center of the clusters
        clusterCenters = self.clusterData["cluster_centers"]
        
        #For each cluster center find a busStop that is closest to it
        for cluster in clusterCenters:
            clusterCenter = [clusterCenters[cluster]["lat"], clusterCenters[cluster]["lon"]]
            closestBusStop = None
            closestDistance = math.inf
            for busStop in self.clusterData["cluster_data"][cluster]:
                busStopCords = [busStop["lat"], busStop["lon"]]
                distance = math.dist(clusterCenter, busStopCords)
                if distance < closestDistance:
                    closestDistance = distance
                    closestBusStop = busStopCords
            clusterCenters[cluster] = closestBusStop
        
        #Create the vehicles and assign them to the clusters
        veh_id = 0
        for cluster, amount in distributedVehicles.items():
            for _ in range(amount):
                vehicles.append(Vehicle(veh_id, CAPACITY, Cords(clusterCenters[cluster]["lat"], clusterCenters[cluster]["lon"]), cluster))
                veh_id += 1
        
        return vehicles

    def _initRequests(self, numberOfRequests):
        pass
    
    def _initMap(self):
        self.map = Map(center=[35.908915,14.442416], zoom=11)
        display(self.map)
        #create 10 colors 
        self.colors = ["red","blue","green","purple","orange","darkred","white","black","darkblue","darkgreen"]
    def _clearMap(self):
        for layer in self.map.layers:
            if not isinstance(layer, ipyleaflet.TileLayer):
                self.map.remove_layer(layer)
    def renderRoutes(self):
        self._clearMap()
        for i,vehicle in enumerate(self.vehicles):
            # print("Vehicle "+str(i),vehicle.getRouteSize())
            if vehicle.getRouteSize() > 0:
                routeGeometry = vehicle.getRouteGeometry()
                route =  polyline.decode(routeGeometry)
                routeLine = Polyline(locations=route, color=self.colors[i], weight=2, opacity=1, fill=False)
                self.map.add_layer(routeLine)

                routeCords = vehicle.getListOfCords()
                # print("Route cords",routeCords)
                # print(vehicle.route)
                for j,cord in enumerate(routeCords):
                    if cord.start:
                        color = "white"
                    else:
                        color = "black"
                    marker = Marker(location=(cord.getLatitude(),cord.getLongitude()),
                                    icon=AwesomeIcon(name='map-marker', marker_color=self.colors[i], icon_color=color, spin=False),
                                    draggable=False,
                                    title="Request dest "+str(j))
                    self.map.add_layer(marker)

            vehicleLocation = vehicle.getPosition()
            marker = Marker(location=(vehicleLocation.getLatitude(),vehicleLocation.getLongitude()),
                             icon=AwesomeIcon(name='bus', marker_color=self.colors[i], icon_color='white', spin=False),
                             draggable=False,
                             title="Bus "+str(i))
            
            self.map.add_layer(marker)