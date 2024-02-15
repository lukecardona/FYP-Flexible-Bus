import routeLinkedList

import requests
import itertools
import math

REQUESTSTATES = {
    "NOT_CALLED": 0,
    "WAITING": 1,
    "SCHEDULED": 2,
    "IN_PROGRESS": 3,
    "COMPLETED": 4,
    "REJECTED": 5
    }

VEHICLESTATES = {
    "IDLE":0,
    "MOVING":1,
}

# OSRM instance details
OSRM_HOST = "localhost"  # ROSRM server IP or hostname
OSRM_PORT = "5000"       # Port of OSRM server is listening on

def calculateNewPosition(start_point, distance, bearing):
    # Radius of the Earth in meters
    R = 6371e3  
    bearing = math.radians(bearing)  # Convert bearing to radians

    lat1 = math.radians(start_point.getLatitude())  # Current lat point converted to radians
    lon1 = math.radians(start_point.getLongitude())  # Current long point converted to radians

    lat2 = math.asin(math.sin(lat1) * math.cos(distance / R) + 
                     math.cos(lat1) * math.sin(distance / R) * math.cos(bearing))

    lon2 = lon1 + math.atan2(math.sin(bearing) * math.sin(distance / R) * math.cos(lat1),
                             math.cos(distance / R) - math.sin(lat1) * math.sin(lat2))

    lat2 = math.degrees(lat2)
    lon2 = math.degrees(lon2)

    return (lat2, lon2)

class Cords:
    def __init__(self, latidude, longitude):
        self.latidude = latidude
        self.longitude = longitude
    
    def __str__(self):
        return "lat: "+ str(self.latidude) + ",long: " + str(self.longitude)
    
    def getLatitude(self):
        return self.latidude
    
    def getLongitude(self):
        return self.longitude
    
class Request_Cords(Cords):
    def __init__(self, latidude, longitude, request_id, start):
        super().__init__(latidude, longitude)
        self.start = start
        self.request_id = request_id
    
    def __str__(self):
        return "Req_Id: " + str(self.request_id) + ", lat: "+ str(self.latidude) + ", long: " + str(self.longitude) + ", " + str(self.start)
    
    def __eq__(self, requestCord):
        if self.request_id == requestCord.getRequestId() and self.start == requestCord.getStart():
            return True
        else:
            return False
        
    def getLatitude(self):
        return self.latidude
    
    def getLongitude(self):
        return self.longitude
    
    def getStart(self):
        return self.start
    
    def getRequestId(self):
        return self.request_id

class Request():
    def __init__(self, request_id, origin, destination, time, passengerAmount):
        self.request_id = request_id
        self.origin = Request_Cords(origin.getLatitude(), origin.getLongitude(), self.request_id, True)
        self.destination = Request_Cords(destination.getLatitude(), destination.getLongitude(), self.request_id, False)
        self.time = time
        self.state = REQUESTSTATES["NOT_CALLED"]
        self.passengerAmount = passengerAmount

    def __str__(self):
        return "Request: id: {}, passengerAmount: {}, time: {}, origin: {}, destination: {},".format(self.request_id, self.passengerAmount, self.time, self.origin, self.destination)
    
    def __repr__(self):
        return self.__str__()
    
    def __eq__(self, other):
        return self.request_id == other.request_id

    #Getters
    def getId(self):
        return self.request_id

    def getPassengerAmount(self):
        return self.passengerAmount
    
    def getOrigin(self):
        return self.origin
    
    def getDestination(self):
        return self.destination
    
    def getTime(self):
        return self.time
    
    def getState(self):
        return self.state
    
    def changeState(self, state):
        self.state = REQUESTSTATES[state]

class Route:
    def __init__(self):
        self.routeList = routeLinkedList.RouteLinkedList()
        self.idCounter = 0 #Used to give each request pair a unique id that is small in memory size

    def __str__(self):
        return "{\n"+str(self.routeList) + "}, idCounter: " + str(self.idCounter)

    def __repr__(self):
        return self.__str__()
    
    def _validateRoute(self,route):
        destinationSet = set()
        for cord in route:
            start = cord.getStart()
            requestId = cord.getRequestId()
            if start: #If start of destination point
                if requestId in destinationSet: #If destination is before origin
                    return False  
            else: #If destination point
                destinationSet.add(requestId)
        return True

    def _getValidPermutations(self, permutations):
        validPermuations = []
        for perm in permutations:
            if self._validateRoute(perm):
                validPermuations.append(perm)
        return validPermuations

    def _findShortestRoute(self, routes, vehiclePosition):
        count = 0
        shortestDistance = float('inf')
        shortestRoute = None
        for route in routes:
            newDist = self.calculateTotalDistance(vehiclePosition, route=route)
            # print (f"Route {count}: distance: {newDist}")
            if newDist < shortestDistance:
                shortestDistance = newDist
                shortestRoute = route
            count += 1
        return shortestRoute

    def _updateRoute(self, route):
        self.routeList = routeLinkedList.RouteLinkedList()
        for cord in route:
            self.routeList.insertAtEnd(cord)
        
    def getRequestOSRMJSON(self, vehiclePosition, steps=False, route=None):
        if(steps == False):
            steps = "false"
        else:
            steps = "true"
        start_coords = str(vehiclePosition.getLongitude()) + "," + str(vehiclePosition.getLatitude())
        middle_coords = ""
        
        if route == None: #If using normal route
            route = self.getRouteHead()
            #Traverse the linked list to get the coordinates
            while(route != None):
                middle_coords += str(route.cords.getLongitude()) + "," + str(route.cords.getLatitude()) + ";"
                route = route.next

        else: #If using an array route
            for cord in route:
                middle_coords += str(cord.getLongitude()) + "," + str(cord.getLatitude()) + ";"

        middle_coords = middle_coords[:-1]
        url = f"http://{OSRM_HOST}:{OSRM_PORT}/route/v1/driving/{start_coords};{middle_coords}?overview=full&steps={steps}"
        response = requests.get(url)
        # Parsing the response
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            Exception("Failed to get a response from the OSRM server")
    
    def optimizeRoute(self, vehiclePosition):
        cordsArray = self.routeList.getListOfCords()
        permutations = list(itertools.permutations(cordsArray))
        validPermuations = self._getValidPermutations(permutations)
        shortestRoute = self._findShortestRoute(validPermuations,vehiclePosition) #Find the shortest route
        self._updateRoute(shortestRoute) #Update the route

    def handleAddRequest(self, request, vehiclePosition):
        self.routeList.insertAtEnd(request.origin)
        self.routeList.insertAtEnd(request.destination)
        self.idCounter += 1
        if self.routeList.getSize() > 2:
            self.optimizeRoute(vehiclePosition)
        return (self.idCounter-1) #Return the id of the request pair

    def handleNextArrival(self):
        cordPoint = self.routeList.deleteAtStart()
        return cordPoint
    
    def calculateTotalDistance(self, vehiclePosition, route=None):
        if route == None:
            data = self.getRequestOSRMJSON(vehiclePosition)
        else:
            data = self.getRequestOSRMJSON(vehiclePosition, route=route)

        distance = data['routes'][0]['distance']  # Distance in meters
        return distance
    
    def calculateTotalTime(self, vehiclePosition, route=None):
        if route == None:
            data = self.getRequestOSRMJSON(vehiclePosition)
        else:
            data = self.getRequestOSRMJSON(vehiclePosition, route=route)
        duration = data['routes'][0]['duration']  # Duration in seconds
        return duration
    
    def getListOfCords(self):
        print("Route: ", self.routeList.printList())
        self.routeList.getListOfCords()
    
    def getRouteHead(self):
        return self.routeList.head
    
    def getSize(self):
        return self.routeList.getSize() #Does not include vehicle position
    
class BusStatistics():
    def __init__(self):
        #Helper variables for statistics
        self.onGoingRequestList = {}
        self.completedRequestList = {}
        self.waitingReuqestList = {}

        #LIST OF STATISTICS
        self._totalDistance = 0 #DONE

        self._totalTime = 0 #DONE

        self._totalIdleTime = 0 #DONE
        self._totalMovingTime = 0 #DONE

        self._totalRequests = 0 #DONE
        self._totalPassengers = 0 #DONE
        self._totalCompletedRequests = 0 #DONE

        self._currentDistance = 0 #DONE
        self._currentTime = 0 #DONE
        self._requestWaitingTime = {} #DONE

    def updateMovement(self,distance,time, steps=False):
        self._totalDistance += distance
        self._currentDistance += distance

        self._totalTime += time
        self._currentTime += time
        self._totalMovingTime += time

        if steps:
            self.addRequestWaitingTime(time)

    def acceptRequest(self,requestId,passengerAmount):
        self._totalRequests += 1
        self._totalPassengers += passengerAmount
        self._requestWaitingTime[requestId] = 0

    def completedRequest(self):
        self._totalCompletedRequests += 1
    
    def stayedIdle(self,time):
        self._totalIdleTime += time

    def resetCurrent(self):
        self._currentDistance = 0
        self._currentTime = 0

        self._requestWaitingTime = {}
        for key in self.waitingReuqestList:
            self._requestWaitingTime[key] = 0

    def addRequestWaitingTime(self,time):
        for key in self.waitingReuqestList:
            self._requestWaitingTime[key] += time

    def getRequestWaitingTime(self):
        time = 0
        for key in self.waitingReuqestList:
            time += self._requestWaitingTime[key]
        return time
    
    def getDistanceTravelled(self):
        return self._currentDistance

class Vehicle():
    def __init__(self, vehicle_id, capacity, origin):
        self.vehicle_id = vehicle_id
        self.capacity = capacity
        self.currentCapacity = 0
        self.currentPosition = origin
        self.state = VEHICLESTATES["IDLE"]
        self.route = Route()
        self.stats = BusStatistics()

    def __str__(self):
        return "Vehicle: id: {}, currentPassengers: {}, route_size: {}, currentPosition: ({})".format(self.vehicle_id, self.currentCapacity, self.route.getSize(), self.currentPosition)
    
    def __repr__(self):
        return self.__str__()
    
    def __eq__(self, other):
        return self.vehicle_id == other.vehicle_id
    
    def _completedLegs(self,data,timeDifference):
        routeTime = 0
        for i in range(len(data['routes'][0]['legs'])):
            routeTime += data['routes'][0]['legs'][i]['duration']

            #If routeTime is greater than timeDifference, then the vehicle has not reached the next stop
            if routeTime > timeDifference:
                routeTime -= data['routes'][0]['legs'][i]['duration']
                return i,routeTime
            else:
                self.arrivedAtNextStop(data['routes'][0]['legs'][i]['duration'])
                self.stats.updateMovement(data['routes'][0]['legs'][i]['distance'],data['routes'][0]['legs'][i]['duration'])  #The vehicle has reached the next stop - Add the statistcs

        return len(data['routes'][0]['legs']),routeTime #If the vehicle would have completed the route
    
    def _completedSteps(self,data,timeLeft,completedLegs):
        for i in range(len(data["routes"][0]["legs"][completedLegs]["steps"])):
            timeLeft -= data["routes"][0]["legs"][completedLegs]["steps"][i]["duration"] #Advance a step
            if timeLeft < 0:
                timeLeft += data["routes"][0]["legs"][completedLegs]["steps"][i]["duration"]
                return (i-1),timeLeft
            else:
                self.stats.updateMovement(data["routes"][0]["legs"][completedLegs]["steps"][i]["distance"],data["routes"][0]["legs"][completedLegs]["steps"][i]["duration"],steps=True) #The vehicle has moved a step - Add the statistcs
        raise Exception("Failed to find the step that the vehicle is on") #Calculations are wrong 
    
    def addRequestToRoute(self, request):
        if request.getPassengerAmount() + self.currentCapacity > self.capacity: #Check Passengers Limit
            Exception("Request exceeds capacity of vehicle")
      
        self.route.handleAddRequest(request,self.currentPosition) #Add request to route
        requestId = request.getId()
        self.currentCapacity += request.getPassengerAmount() #Update the amount of passengers in the vehicle
        request.changeState("SCHEDULED") #Change the state
        # print("Added Request id: ", requestId)

        self.stats.acceptRequest(requestId,request.getPassengerAmount()) #Update the statistics

        self.stats.waitingReuqestList[requestId] = request

    def arrivedAtNextStop(self, time):
        cords = self.route.handleNextArrival()
        requestId = cords.getRequestId()
    
        self.stats.addRequestWaitingTime(time) #Update the statistics

        if cords.getStart() == True:
            self.stats.waitingReuqestList[requestId].changeState("IN_PROGRESS") #Change the state

            self.stats.onGoingRequestList[requestId] = self.stats.waitingReuqestList[requestId] #Add the request to the onGoing list
            del self.stats.waitingReuqestList[requestId] #Remove the request from the waiting list
            
            #No need to add the passengers to the vehicle since they are acounted for in the addReuqestToRoute method
            self.currentPosition = Cords(cords.getLatitude(), cords.getLongitude()) #Update the position of the vehicle
        else:
            self.stats.onGoingRequestList[requestId].changeState("COMPLETED") #Change the state
            self.stats.completedRequestList[requestId] = self.stats.onGoingRequestList[requestId] #Add the request to the completed list
            self.currentCapacity -= self.stats.onGoingRequestList[requestId].getPassengerAmount() #Update the amount of passengers in the vehicle
            del self.stats.onGoingRequestList[requestId] #Remove the request from the onGoing list
            self.currentPosition = Cords(cords.getLatitude(), cords.getLongitude()) #Update the position of the vehicle 

            self.stats.completedRequest() #Update the statistics
        return cords
    
    def move(self,timeDifference):
        #Get the OSRM data for the whole route
        if self.route.getSize() == 0:
            self.stats.stayedIdle(timeDifference)
            return
        
        self.stats.resetCurrent() #Reset the current distance travelled
        
        # print("Vehicle ",self.vehicle_id," is moving")
        
        data = self.route.getRequestOSRMJSON(self.currentPosition,steps=True)
        completedLegs,routeTime =  self._completedLegs(data,timeDifference)  

        # print("Completed Legs ",completedLegs, "Len Legs ",len(data['routes'][0]['legs']))
        if completedLegs == len(data['routes'][0]['legs']): #If entire route is completed
            return
        
        #Get an estimate of the vehicle's position
        # print("Time Difference ",timeDifference)
        timeLeft = timeDifference - routeTime
        # print(timeLeft)
        completedSteps, timeLeft = self._completedSteps(data,timeLeft,completedLegs)
        
        currentCord = Cords(data['routes'][0]['legs'][completedLegs]['steps'][completedSteps]['maneuver']['location'][1], data['routes'][0]['legs'][completedLegs]['steps'][completedSteps]['maneuver']['location'][0])
        
        bearing = data['routes'][0]['legs'][completedLegs]['steps'][completedSteps]['maneuver']['bearing_after']
        # print("Completed Legs ",completedLegs, "Completed Steps ",completedSteps, "Time Left ",timeLeft, "Bearing ",bearing)
        if  data['routes'][0]['legs'][completedLegs]['steps'][completedSteps]['duration'] != 0:
            speed =  data['routes'][0]['legs'][completedLegs]['steps'][completedSteps]['distance'] / data['routes'][0]['legs'][completedLegs]['steps'][completedSteps]['duration']
            distance = timeLeft * speed
            lat, lon = calculateNewPosition(currentCord, distance, bearing)
            currentCord = Cords(lat, lon)
        else: 
            currentCord = Cords(data['routes'][0]['legs'][completedLegs]['steps'][completedSteps]['maneuver']['location'][1], data['routes'][0]['legs'][completedLegs]['steps'][completedSteps]['maneuver']['location'][0])
        self.currentPosition = currentCord

    def completeRoute(self):

        if self.route.getSize() == 0:
            return 0
        
        self.stats.resetCurrent() #Reset the current distance travelled
        time = 0
        data = self.route.getRequestOSRMJSON(self.currentPosition,steps=False)

        for i in range(len(data['routes'][0]['legs'])):
            time += data['routes'][0]['legs'][i]['duration']
            self.arrivedAtNextStop(data['routes'][0]['legs'][i]['duration'])
            self.stats.updateMovement(data['routes'][0]['legs'][i]['distance'],data['routes'][0]['legs'][i]['duration'])  #The vehicle has reached the next stop - Add the statistcs
            
        return time
            
    def printRoute(self):
        print("Vehile "+ str(self.vehicle_id)+" route: "+str(self.route))

    def getRouteDistance(self):
        return self.route.calculateTotalDistance(self.currentPosition)
    
    def getRouteTime(self):
        return self.route.calculateTotalTime(self.currentPosition)
    
    def getPosition(self):
        return self.currentPosition
    
    def getCurrentCapacity(self):
        return self.currentCapacity
    
    def getCapacity(self):
        return self.capacity

    def getRouteSize(self):
        return self.route.getSize()
    
    def getListOfCords(self):
        return self.route.getListOfCords()
    
    def getRouteGeometry(self):
        data = self.route.getRequestOSRMJSON(self.currentPosition)
        return data['routes'][0]['geometry']
    
    def getRequestWaitingTime(self):
        return self.stats.getRequestWaitingTime()
    
    def getDistanceTravelled(self):
        return self.stats.getDistanceTravelled()