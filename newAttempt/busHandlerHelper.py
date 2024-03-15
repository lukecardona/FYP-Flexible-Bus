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

BESTSOLTUIONKM = 0 
BESTSOLTUIONDEADHEAD = 1
BESTSOLTUIONVEHUSAGE = 2

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
        self.totalVehicleUsage = 0
        self.totalKMDistance = 0
        self.totalDeadHeadDistance = 0

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
    def _initRequests(self, numberOfRequests):
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
    def _endCheck(self):
        if self.currentRequestIndex < len(self.requests):
            self.currentRequest = self.requests[self.currentRequestIndex]
            return False
        else:
            return True
    def rejectRequest(self):
        self.rejectedRequests.append(self.currentRequest)
        self.currentRequestIndex += 1
        return self._endCheck()
    def acceptRequest(self, vehicleIndex):
        self.vehicles[vehicleIndex].route.routeList.insertAtEnd(self.currentRequest.origin)
        self.vehicles[vehicleIndex].route.routeList.insertAtEnd(self.currentRequest.destination)
    def checkBrokenTimeConstraints(self, vehicleIndex):
        vehicleRoute = self.vehicles[vehicleIndex].route.getListOfCords()
        routeString = ""
        for cords in vehicleRoute:
            routeString += f"{cords.getLongitude()},{cords.getLatitude()};"
        routeString[:-1] #Remove Semi Colon (Final Character)
        url = f"http://{OSRM_HOST}:{OSRM_PORT}/route/v1/driving/{self.vehicles[vehicleIndex].currentPosition.getLongitude()},{self.vehicles[vehicleIndex].currentPosition.getLongitude()};{routeString}?overview=full"
        response = SESSION.get(url)
        if response.status_code == 200:
            data = response.json()

            #Loop through the data and check if the time constraints are broken anywhere 
            currentTime = self.currentRequest.time
            for i,leg in enumerate(data["routes"][0]["legs"]):
                if vehicleRoute[i].getTimeWindow() > currentTime:
                    return True
                currentTime += timedelta(leg["duration"])
            
            return False
    def maintainRequestOrder(self, vehicleIndex):
        vehicleRoute = self.vehicles[vehicleIndex].route.getListOfCords()
        requestIds = []
        for node in vehicleRoute:
            if node.getStart(): #If the node is a request origin, check if request IDs exist
                if node.getRequestId() in requestIds:
                    return False
            requestIds.append(node.getRequestId())
        return True
    def moveToNextRequest(self):
        if self.currentRequestIndex < len(self.requests)-1: #If there are still requests to be processed
            currentRequest = self.requests[self.currentRequestIndex]
            nextRequest = self.requests[self.currentRequestIndex+1]
            timeDifference = (nextRequest.getTime()-currentRequest.getTime()).total_seconds()
            for vehicle in self.vehicles:
                vehicle.move(timeDifference) #Move the vehicle to the next request
            self.currentRequestIndex += 1
            return False
        else:
            return True
    #Getters
    def getCurrentRequest(self):
        return self.currentRequest
    def getTotalDistance(self):
        totalDistance = 0
        for vehicle in self.vehicles:
            if vehicle.getRouteSize() > 0:
                totalDistance += vehicle.getRouteDistance()
        return totalDistance
    def getTotalTime(self):
        totalTime = 0
        for vehicle in self.vehicles:
            if vehicle.getRouteSize() > 0:
                totalTime += vehicle.getRouteTime()
        return totalTime
    def getTotalVehicleUtilization(self):
        vehUsage = 0
        for vehicle in self.vehicles:
            if vehicle.getRouteSize() > 0:
                vehUsage += 1
        return vehUsage
    def getTotaLDeadHeadDistance(self):
        deadHeadDistance = 0
        for vehicle in self.vehicles:
            if vehicle.getRouteSize() > 0:
                deadHeadDistance += vehicle.getDeadHeadDistance()
        return deadHeadDistance
    def getRequestPairs(self,vehicleIndex):
        vehicleRoute = self.vehicles[vehicleIndex].route.getListOfCords()
        requestPairs = {}
        for i,node in enumerate(vehicleRoute):
            if node.getStart():
                requestPairs[node.getRequestId()] = [i]
            else:
                if node.getRequestId() in requestPairs:
                    requestPairs[node.getRequestId()].append(i)
        return requestPairs
class MultiObjectiveTabuSearch:
    def __init__(self, numberOfVehicles = 10, numberOfRequests = 100, totalNumberOfIterations=1000, totalNumberOfIterationsWithoutImprovement=50, threshold=20):
        self.busHandler = BusHandler(numberOfVehicles, numberOfRequests)
        self.listOfActions = []
        self.tabuList = set()
        self.totalNumberOfIterations = totalNumberOfIterations
        self.totalNumberOfIterationsWithoutImprovement = totalNumberOfIterationsWithoutImprovement
        self.threshold = threshold

    def _getOSRMBetween2Points(self, cords1, cords2):
        url = f"http://{OSRM_HOST}:{OSRM_PORT}/route/v1/driving/{cords1.getLongitude()},{cords1.getLatitude()};{cords2.getLongitude()},{cords2.getLatitude()}?overview=full"
        response = SESSION.get(url)
        if response.status_code == 200:
            data = response.json()
            return data
    def _getClosestVehicles(self, request):
        vechDict = {}
        for vehicle in self.busHandler.vehicles:
            data = self._getOSRMBetween2Points(request.origin, vehicle.getPosition())
            vechDict[vehicle.getId()] = data["routes"][0]["distance"]
        
        #Sort the dictionary by value and turn it into a list of vehicle IDs
        sortedVehicles = sorted(vechDict.items(), key=lambda x: x[1])
        sortedVehicles = [x[0] for x in sortedVehicles]
        return sortedVehicles   
    def run(self):
        end = False
        while end == False:
            solutionKM = self._handleMultipleObjectiveDARP()
            self.busHandler = copy.deepcopy(solutionKM)
            end = self.busHandler.moveToNextRequest()
            #Advance the request to the next one and calculate the bus movements 
        print("Run Excetued Successfully")  
    def _handleMultipleObjectiveDARP(self):
        #Get the current request
        currentRequest = self.busHandler.getCurrentRequest()

        solutionFound,initialSolution = self._ARV(currentRequest)
        bestSolution = [initialSolution, initialSolution, initialSolution]

        if not solutionFound:
            self.listOfActions.append("REJECT")
            return self.busHandler.rejectRequest()
        
        solutionList = [initialSolution]
        historyOfSolutions = [initialSolution]

        numberOfIterations = 0
        numberOfIterationsWithoutImprovement = 0

        #While the stopping conditions are not reached
        while numberOfIterations < self.totalNumberOfIterations and numberOfIterationsWithoutImprovement < self.totalNumberOfIterationsWithoutImprovement and solutionList != []:
            currentSolution = solutionList.pop(0)
            canditateList = self._CLG(currentSolution)

            #Check for dominance
            for candidate in canditateList:
                for candidate2 in canditateList:
                    if candidate2.totalKMDistance <= candidate.totalKMDistance and candidate2.totalDeadHeadDistance <= candidate.totalDeadHeadDistance and candidate2.totalVehicleUsage <= candidate.totalVehicleUsage:
                        if candidate2.totalKMDistance < candidate.totalKMDistance or candidate2.totalDeadHeadDistance < candidate.totalDeadHeadDistance or candidate2.totalVehicleUsage < candidate.totalVehicleUsage:
                            canditateList.remove(candidate)
                            break

            if canditateList == []:
                print("No candidates found")
                break
            
            #Check if the candidate list is larger than the threshold
            if len(canditateList) > self.threshold:
                n = self.threshold//3

                #Order the candidate list by the totalKMDistance,
                orderedCandidateListKM = sorted(canditateList, key=lambda x: (x.totalKMDistance))
                orderedCandidateListDeadHead = sorted(canditateList, key=lambda x: (x.totalDeadHeadDistance))
                orderedCandidateListVehicleUsage = sorted(canditateList, key=lambda x: (x.totalVehicleUsage))

                newNeighbourhood = orderedCandidateListKM[:n]
                
                i, j = 0, 0
                while i < n:
                    if orderedCandidateListDeadHead[j] not in newNeighbourhood:
                        newNeighbourhood.append(orderedCandidateListDeadHead[j])
                        i += 1
                        j += 1
                    else:
                        j += 1
                i, j = 0, 0
                while i < n:
                    if orderedCandidateListVehicleUsage[j] not in newNeighbourhood:
                        newNeighbourhood.append(orderedCandidateListVehicleUsage[j])
                        i += 1
                        j += 1
                    else:
                        j += 1

                for solution in newNeighbourhood:
                    if solution not in historyOfSolutions:
                        solutionList.append(solution)
                        historyOfSolutions.append(solution)
            else:
                for solution in canditateList:
                    if solution not in historyOfSolutions:
                        solutionList.append(solution)
                        historyOfSolutions.append(solution)
            
            #Increment the number of iterations
            numberOfIterations += 1
            improvement = False
            #Check if there where any improvements in the new neighbourhood
            for neighbourHood in solutionList:
                if neighbourHood.totalKMDistance < bestSolution[BESTSOLTUIONKM].totalKMDistance:
                    bestSolution[BESTSOLTUIONKM] = neighbourHood
                    improvement = True
                if neighbourHood.totalDeadHeadDistance < bestSolution[BESTSOLTUIONDEADHEAD].totalDeadHeadDistance:
                    bestSolution[BESTSOLTUIONDEADHEAD] = neighbourHood
                    improvement = True
                if neighbourHood.totalVehicleUsage < bestSolution[BESTSOLTUIONVEHUSAGE].totalVehicleUsage:
                    bestSolution[BESTSOLTUIONVEHUSAGE] = neighbourHood
                    improvement = True
            if improvement:
                numberOfIterationsWithoutImprovement = 0
            else:
                numberOfIterationsWithoutImprovement += 1

        return bestSolution[BESTSOLTUIONKM]

    def _ARV(self,request):
        orderedListOfClosestVehicles = self._getClosestVehicles(request)
        for vehicle in orderedListOfClosestVehicles:
            solutionFound, solution = self._ASRSV(request, vehicle)
            if solutionFound:
                #Compute the totalKM distance, the deadHeading disantance and vehicleUsage
                solution.totalKMDistance = solution.getTotalDistance()
                solution.totalDeadHeadDistance = solution.getTotaLDeadHeadDistance()
                solution.totalVehicleUsage = solution.getTotalVehicleUtilization()
                return solutionFound, solution
        return False, None
    def _ASRSV(self,request, vehicle):
        #Check that the capacity contraitns of the bus are not broken
        if self.busHandler.vehicles[vehicle].getRouteSize() + request.getPassengerAmount() > self.busHandler.vehicles[vehicle].getCapacity():
            return False, None

        #Create a deep copy of the busHandler class to check for time contraints
        copyBusHandler = copy.deepcopy(self.busHandler)
        copyBusHandler.acceptRequest(vehicle)

        #Check for broken time contriansts on that vehicle: 
        if copyBusHandler.checkBrokenTimeConstraints(vehicle):
            return False, None
        
        #If time contraisnts are not broken check if the request origin can be moved towards the beginning
        broken = False
        latestValid = copy.deepcopy(copyBusHandler)

        while not broken:
            currentOriginIndex = copyBusHandler.vehicles[vehicle].route.routeList.getIndex(request.origin)
            
            #If made it to the start of the route
            if currentOriginIndex == 0:
                break

            #Swap the origin with the previous node
            copyBusHandler.vehicles[vehicle].route.routeList.swapNodes(currentOriginIndex, currentOriginIndex-1)

            #Check if the time constraints are broken
            if copyBusHandler.checkBrokenTimeConstraints(vehicle):
                broken = True
            else:
                latestValid = copy.deepcopy(copyBusHandler)

        return True,latestValid
    def _CLG(self, solution): #Candidate List Generation
        candidateList = []
        #Check all swap exchanges for the current request
        for vehicle in solution.vehicles:
            #If route only has 1 or less points skip 
            if vehicle.getRouteSize() <= 1:
                continue

            print(f"Vehicle: {vehicle.getId()} RouteSize: {vehicle.getRouteSize()}")
            print(f"Route Len: {len(vehicle.route.routeList.getListOfCords())}")
                
            #For every point in the route
            for i in range(vehicle.getRouteSize()):
                for j in range(i,vehicle.getRouteSize()):
                    if i == j: # Skip if the two indexes are the same
                        continue

                    solutionCopy = copy.deepcopy(solution)
                    #Swap the two points
                    solutionCopy.vehicles[vehicle.getId()].route.routeList.switchNodes(i,j)
                    
                    if not solutionCopy.checkBrokenTimeConstraints(vehicle.getId()) and solutionCopy.maintainRequestOrder(vehicle.getId()):
                        solutionCopy.totalKMDistance = solutionCopy.getTotalDistance()
                        solutionCopy.totalDeadHeadDistance = solutionCopy.getTotaLDeadHeadDistance()
                        solutionCopy.totalVehicleUsage = solutionCopy.getTotalVehicleUtilization()
                        candidateList.append(solutionCopy)
            
            #Check if requests pairs can be moved to the beginning or end of the route
            requestPairs = solution.getRequestPairs(vehicle.getId()) #Reqeust Pairs is a dict with the following structure: {requestId: [index1, index2]}
            route = solution.vehicles[vehicle.getId()].route.routeList.getListOfCords()
            print(f"Vehicle {vehicle.getId()} Route: {route}")
            print(f"Request Pairs: {requestPairs}")
            for requestId in requestPairs:
                for vehicle2 in solution.vehicles:
                    if vehicle != vehicle2 and (route[requestPairs[requestId][0]].getPassengerAmount() + vehicle2.getCurrentCapacity() <= vehicle2.getCapacity()):
                        #Check if it can be inserted in the beginning
                        solutionCopy = copy.deepcopy(solution)
                        solutionCopy.vehicles[vehicle2.getId()].route.routeList.insertAtStart(route[requestPairs[requestId][1]])
                        solutionCopy.vehicles[vehicle2.getId()].route.routeList.insertAtStart(route[requestPairs[requestId][0]])
                        #Delete the nodes from the original vehicle
                        if not solutionCopy.checkBrokenTimeConstraints(vehicle2.getId()):
                            solutionCopy.vehicles[vehicle.getId()].route.routeList.deleteNode(route[requestPairs[requestId][0]])
                            solutionCopy.vehicles[vehicle.getId()].route.routeList.deleteNode(route[requestPairs[requestId][1]])
                            solutionCopy.totalKMDistance = solutionCopy.getTotalDistance()
                            solutionCopy.totalDeadHeadDistance = solutionCopy.getTotaLDeadHeadDistance()
                            solutionCopy.totalVehicleUsage = solutionCopy.getTotalVehicleUtilization()
                            candidateList.append(solutionCopy)
                        
                        if solution.vehicles[vehicle2.getId()].route.routeList.getSize() == 0: #Inserting at start at end will result in the same solution
                            continue

                        #Check if it can be inserted at the end of the solution 
                        solutionCopy2 = copy.deepcopy(solution)
                        solutionCopy2.vehicles[vehicle2.getId()].route.routeList.insertAtEnd(route[requestPairs[requestId][0]])
                        solutionCopy2.vehicles[vehicle2.getId()].route.routeList.insertAtEnd(route[requestPairs[requestId][1]])
                        if not solutionCopy2.checkBrokenTimeConstraints(vehicle2.getId()):
                            solutionCopy2.vehicles[vehicle.getId()].route.routeList.deleteNode(route[requestPairs[requestId][1]])
                            solutionCopy2.vehicles[vehicle.getId()].route.routeList.deleteNode(route[requestPairs[requestId][0]])
                            solutionCopy2.totalKMDistance = solutionCopy2.getTotalDistance()
                            solutionCopy2.totalDeadHeadDistance = solutionCopy2.getTotaLDeadHeadDistance()
                            solutionCopy2.totalVehicleUsage = solutionCopy2.getTotalVehicleUtilization()
                            candidateList.append(solutionCopy2)
 
        return candidateList

tabuSearch = MultiObjectiveTabuSearch()
tabuSearch.run()