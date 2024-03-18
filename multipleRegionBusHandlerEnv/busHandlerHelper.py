from  classesDefinations import Cords,Vehicle,Request
from urllib3.util import Retry
from requests.adapters import HTTPAdapter
import copy
import requests

CAPACITY = 5
BUS_ORIGIN = Cords(35.8942679, 14.5086503) #CORDS OF THE 15 VALLETTA BUS BAY)
BUS_STOP_DATA_PATH = "C:/Users/lukec/Documents/Thesis/BusRouting/FYP-Flexible-Bus/Data/BusStopsMalta/export.json"

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
        self.vehicles = self._initVehiles(vehicleAmount)
        self.requests = self._initRequests(numberOfRequests)
        self.currentRequest = self.requests[0]
        self.currentRequestIndex = 0
        self.rejectedRequests = []

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

    def _initVehiles(self, vehicleAmount):
        vehicles = []
        for i in range(vehicleAmount):
            vehicles.append(Vehicle(i, CAPACITY, BUS_ORIGIN))
        return vehicles