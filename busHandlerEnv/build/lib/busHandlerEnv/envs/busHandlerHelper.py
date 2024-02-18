from  .classesDefinations import Cords,Vehicle,Request

CAPACITY = 10
BUS_ORIGIN = Cords(35.8942679, 14.5086503) #CORDS OF THE 15 VALLETTA BUS BAY)
BUS_STOP_DATA_PATH = "C:/Users/lukec/Documents/Thesis/BusRouting/FYP-Flexible-Bus/Data/BusStopsMalta/export.json"

from datetime import datetime, timedelta
import json
import math
import random

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
    for i in range(n):
        interval_start = start_time + timedelta(seconds=i * interval_duration)
        intervals.append(interval_start.time())

    return intervals

def getTimeDifference(time1, time2):
    today = datetime.now().date()
    datetime1 = datetime.combine(today, time1)
    datetime2 = datetime.combine(today, time2)

    difference = datetime1 - datetime2
    return difference.seconds

class BusHandler():
    def __init__(self, vehicleAmount, numberOfRequests):
        self.vehicles = self.initVehiles(vehicleAmount)
        self.requests = self.initRequests(numberOfRequests)
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

    def initVehiles(self, vehicleAmount):
        vehicles = []
        for i in range(vehicleAmount):
            vehicles.append(Vehicle(i, CAPACITY, BUS_ORIGIN))
        return vehicles

    def initRequests(self, numberOfRequests):
        requestId = 0
        timeIntervals = divide_time_interval(numberOfRequests)
        f = open(BUS_STOP_DATA_PATH, "r",encoding="utf-8")
        data = json.load(f)
        elements = data["elements"]
        elementsLen = len(elements)
        requestList = []
        for i in range(numberOfRequests):
            #Get two random indexes from all the bus stops 
            r1 = random.randint(0, elementsLen-1)
            r2 = random.randint(0, elementsLen-1)
            while r1 == r2:
                r2 = random.randint(0, elementsLen-1)
            
            #Get the coordinates of the two bus stops
            lat1 = elements[r1]["lat"]
            lon1 = elements[r1]["lon"]
            lat2 = elements[r2]["lat"]
            lon2 = elements[r2]["lon"]

            #Create the request Cords
            reqPickup = Cords(lat1, lon1)
            reqDropoff = Cords(lat2, lon2)

            #Create the request
            requestList.append(Request(requestId, reqPickup, reqDropoff, timeIntervals[i],random.randint(1, 3)))

            #Increment the requestId
            requestId += 1
        f.close()
        return requestList
    
    def endCheck(self):
        if self.currentRequestIndex < len(self.requests):
            self.currentRequest = self.requests[self.currentRequestIndex]
            return False
        else:
            return True
    
    def rejectRequest(self):
        #Error Checking
        if(self.currentRequestIndex >= len(self.requests)):
            raise ValueError("No more requests to reject, index exceeded the requests list length.")
        #Reject the current request and move to the next one
        self.rejectedRequests.append(self.currentRequest)
        self.currentRequestIndex += 1
        return self.endCheck()
        
    def acceptRequest(self, vehicleIndex):
        #Error Checking
        if(vehicleIndex >= len(self.vehicles)):
            raise ValueError("Vehicle index exceeded the vehicles list length.")

        #Accept the current request and move to the next one
        self.vehicles[vehicleIndex].addRequestToRoute(self.currentRequest)
        self.currentRequestIndex += 1
        return self.endCheck()
        
    def getCurrentRequest(self):
        return self.currentRequest
    
    def updateState(self,done):
        if not done:
            timeDiffernce = getTimeDifference(self.currentRequest.getTime(),self.requests[self.currentRequestIndex-1].getTime())
            for vehicle in self.vehicles:
                vehicle.move(timeDiffernce) #Route size check happens latter

        if done:
            maxTime = 0
            for vehicle in self.vehicles:
                if vehicle.getRouteSize() > 0: 
                    routeTime = vehicle.getRouteTime()
                    if routeTime > maxTime:
                        maxTime = vehicle.getRouteTime()

            for vehicle in self.vehicles:
                timeToComplete = vehicle.completeRoute() #Returns Time, could be used for idle
                vehicle.stats.stayedIdle(maxTime - timeToComplete) #Stay idle for the remaining time

    def getTotalDistance(self):
        totalDistance = 0
        for vehicle in self.vehicles:
            if vehicle.getRouteSize() > 0:
                totalDistance += vehicle.getDistance()
        return totalDistance
    
    def getTotalTime(self):
        totalTime = 0
        for vehicle in self.vehicles:
            if vehicle.getRouteSize() > 0:
                totalTime += vehicle.getTime()
        return totalTime
