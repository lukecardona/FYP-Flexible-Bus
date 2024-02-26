from busHandlerHelper import BusHandler
import requests
from datetime import datetime, time, timedelta

"""
Implentation of "A multi objective approach for DRT service using tabu search" by Torgal, Marta, Dias, Teresa Galvão, Fontes, Tânia
Transportation Research Procedia, 2021, pg 91-98 https://www.sciencedirect.com/science/article/pii/S2352146521001460 

Another neater Implementation: https://repositorio-aberto.up.pt/bitstream/10216/126884/2/392706.pdf
"""

EXCHANGE_TYPES = {
    "ROUTE": "ROUTE",
    "VEHICLE": "VEHICLE",
}

OSRM_HOST = "localhost"  # ROSRM server IP or hostname
OSRM_PORT = "5000"       # Port of OSRM server is listening on

from urllib3.util import Retry
from requests.adapters import HTTPAdapter

SESSION = requests.Session()
RETRY = Retry(connect=5, read=5, backoff_factor=0.3)
ADAPTER = HTTPAdapter(max_retries=RETRY)
SESSION.mount('http://', ADAPTER)
SESSION.mount('https://', ADAPTER)

#(EXCHANGE_TYPES["ROUTE"], VEHICLE_ID, INDEX_SWAP, INDEX_SWAP2)

def busHandlerToSolution(busHandler):
    solution = {}
    for vehicle in busHandler.vehicles:#
        veh_id = vehicle.getId()
        solution[veh_id] = [vehicle.currentPosition()] + [vehicle.getListOfCords()]
    return solution

def getPossibleRouteSwapExchanges(vehicleRoute, vehicleId):
    exchanges = []
    for i in range(1,len(vehicleRoute)-1):
        for j in range(1,len(vehicleRoute)-1):
            if i != j and vehicleRoute[i].requestId != vehicleRoute[j].requestId:
                exchanges.append((EXCHANGE_TYPES["ROUTE"], vehicleId, i, j))
    return exchanges

def getPossibleVehicleSwapExchanges(solution):
    exchanges = []
    for vehicle1 in solution:
        for vehicle2 in solution:
            if vehicle1 != vehicle2 and (len(solution[vehicle1]) > 1 or len(solution[vehicle2]) > 1): #If Not the same vehicle and at least ONE VEHICLE has more than 1 request
                if len(solution[vehicle2]) == 1:
                    requestIdPairs = getAllRequestIdsPairs(solution[vehicle1])
                    for requestIdPair in requestIdPairs:
                        exchanges.append((EXCHANGE_TYPES["VEHICLE"], vehicle1, vehicle2, requestIdPairs[requestIdPair], 1,2))

                elif len(solution[vehicle1]) == 1:
                    requestIdPairs = getAllRequestIdsPairs(solution[vehicle2])
                    for requestIdPair in requestIdPairs:
                        exchanges.append((EXCHANGE_TYPES["VEHICLE"], vehicle2, vehicle1, requestIdPairs[requestIdPair], 1,2))
              
                else: #Both vehicles have more than 1 request
                    requestIdPairs1 = getAllRequestIdsPairs(solution[vehicle1])
                    requestIdPairs2 = getAllRequestIdsPairs(solution[vehicle2])
                    for requestIdPair in getAllRequestIdsPairs(solution[vehicle1]):
                        for i in range(1,len(solution[vehicle2])):
                            for j in range(i+1,len(solution[vehicle1])):
                                exchanges.append((EXCHANGE_TYPES["VEHICLE"], vehicle1, vehicle2, requestIdPairs1[requestIdPair], i,j))
                
                    for requestIdPair in getAllRequestIdsPairs(solution[vehicle2]):  
                        for i in range(1,len(solution[vehicle1])):
                            for j in range(i+1,len(solution[vehicle2])):
                                exchanges.append((EXCHANGE_TYPES["VEHICLE"], vehicle2, vehicle1, requestIdPairs2[requestIdPair], i,j))        

def getAllRequestIdsPairs(route):
    startId = set()
    endId = set()
    IdPairs = {}

    for i in range(1,len(route)-1):
        reqId = route[i].getId()
        if reqId not in startId:
            startId.add(reqId)
            IdPairs[reqId] = [i]
        else:
            endId.add(reqId)
            IdPairs[reqId].append(i)
    
    #Remove Single Request Ids
    for reqId in IdPairs:
        if len(IdPairs[reqId]) == 1:
            del IdPairs[reqId]
    
    return IdPairs
        

def routeSwap(exchange, solution):
    #  exchanges.append((EXCHANGE_TYPES["ROUTE"], vehicleId, i, j))
    solutionCopy = solution.copy()
    solutionCopy[exchange[1]][exchange[2]], solutionCopy[exchange[1]][exchange[3]] = solutionCopy[exchange[1]][exchange[3]], solutionCopy[exchange[1]][exchange[2]]
    return solutionCopy

def vehicleSwap(exchange, solution):
    """
    #exchanges.append((EXCHANGE_TYPES["VEHICLE"], vehicle1Index, vehicle2Index, requestIdPair, i,j)) #Request Id Pair = dict[reqId] = [i,j]
    # solutionCopy = solution.copy()
    # vehicle1Index = exchange[1]
    # vehicle2Index = exchange[2]
    # requestIdPair = exchange[3]
    # i = exchange[4]
    # j = exchange[5]

    # solutionCopy[vehicle2Index].insert(i,solutionCopy[vehicle1Index][requestIdPair[0]])
    # solutionCopy[vehicle2Index].insert(j,solutionCopy[vehicle1Index][requestIdPair[1]])
    # solutionCopy[vehicle1Index].remove(requestIdPair[0])
    # solutionCopy[vehicle1Index].remove(requestIdPair[1])
    """
    solutionCopy = solution.copy()
    solutionCopy[exchange[2]].insert(exchange[4],solutionCopy[exchange[1]][exchange[3][0]])
    solutionCopy[exchange[2]].insert(exchange[5],solutionCopy[exchange[1]][exchange[3][1]])
    solutionCopy[exchange[1]].remove(exchange[3][0])
    solutionCopy[exchange[1]].remove(exchange[3][1])
    return solutionCopy

# def isRouteValid(route):
#     routeString = ""
#     for i in range(len(route)-1):
#         routeString += f"{route[i].getLongitude()},{route[i].getLatitude()};"
#         #Remove Final Semicolon
#     routeString = routeString[:-1]
#     url = f"http://{OSRM_HOST}:{OSRM_PORT}/route/v1/driving/{routeString}?overview=full&steps={False}"
#     response = requests.get(url)

#     currentTime = None #NEED TO GET THE CURRENT TIME THAT THE SEARCH IS HAPPENING

#     if response.status_code == 200:
#         data = response.json()
#         for i,leg in enumerate(data["routes"][0]["legs"]):
#                 currentTime += timedelta(seconds=leg["duration"])
#                 if currentTime > route[i+1].getTimeWindow():
#                     return False
#     else:
#         raise ValueError("OSRM Server Error")

# def isValidCanditate(canditate):
#     for vehicle in canditate:
#         if len(canditate[vehicle]) > 1:
#             if not isRouteValid(canditate[vehicle]):  #Check timeWindowConstraints
#                 return False
#     return True

def getRouteOSRMURL(route):
        routeString = ""
        for i in range(len(route)-1):
            routeString += f"{route[i].getLongitude()},{route[i].getLatitude()};"
            #Remove Final Semicolon
        routeString = routeString[:-1]
        url = f"http://{OSRM_HOST}:{OSRM_PORT}/route/v1/driving/{routeString}?overview=full&steps={False}"
        return url

class Candidate:
    def __init__(self, solution):
        self.solution = solution
        self.totalKM = self._findTotalKM(solution)
        self.totalDeadHeading = self._findTotalDeadHeading(solution)
        self.vehicleUsage = self._findVehicleUsage(solution)

    def __str__(self):
        return f"Solution: {self.solution}\nTotal KM: {self.totalKM}\nTotal DeadHeading: {self.totalDeadHeading}\nVehicle Usage: {self.vehicleUsage}"

    def _findTotalKM(self, solution):
        solutionKM = 0
        for vehicle in solution:
            if len(solution[vehicle]) > 1:
                url = getRouteOSRMURL(solution[vehicle])
                response = SESSION.get(url)
                if response.status_code == 200:
                    data = response.json()
                    solutionKM += data["routes"][0]["distance"]
                else:
                    raise ValueError("OSRM Server Error")
        return solutionKM
    
    def _findTotalDeadHeading(self, solution):
        pass

    def _findVehicleUsage(self, solution):
        vehicleUsage = 0
        for vehicle in solution:
            if len(solution[vehicle]) > 1:
                vehicleUsage += 1
        return vehicleUsage

                               
class BusHandlerTabuSearch(BusHandler):
    def __init__(self, numberOfBuses,numberOfRequest,numberOfIterations,numberOfIterationsWithoutImprovement,threshold = 12):
        super().__init__(numberOfBuses,numberOfRequest)
        self.tabuList = []
        self.currentKnownRequests = []
        self.numberOfIterations = numberOfIterations
        self.numberOfIterationsWithoutImprovement = numberOfIterationsWithoutImprovement
        self.threshold = threshold
        self.currentRequestTime = self.currentRequest.getTime()

    def __str__(self):
        return super().__str__() + "\nTabu List: " + str(self.tabuList) + "\nCurrent Known Requests: " + str(self.currentKnownRequests)
    
    """
    Private Methods used to generate the all the feasible solutions
    """
    def _isRouteValid(self,route):
        routeString = ""
        for i in range(len(route)-1):
            routeString += f"{route[i].getLongitude()},{route[i].getLatitude()};"
            #Remove Final Semicolon
        routeString = routeString[:-1]
        url = f"http://{OSRM_HOST}:{OSRM_PORT}/route/v1/driving/{routeString}?overview=full&steps={False}"
        response = requests.get(url)

        currentTime = self.currentRequestTime 

        if response.status_code == 200: #Request was successful
            data = response.json() #Get the data from the response
            for i,leg in enumerate(data["routes"][0]["legs"]): #For each leg in the route
                    currentTime += timedelta(seconds=leg["duration"]) #Add the duration of the leg to the current time
                    if currentTime > route[i+1].getTimeWindow(): #If the current time is greater than the time window of the next request
                        return False
            return True
        else:
            raise ValueError("OSRM Server Error")

    def _isValidCanditate(self,canditate):
        vehicleUsage = 0
        for vehicle in canditate:
            if len(canditate[vehicle]) > 1:
                if not self._isRouteValid(canditate[vehicle]):  #Check timeWindowConstraints
                    return False
                vehicleUsage += 1
        return True
            
    def _getAllPossibleExchanges(self,solution):
        exchanges = [] 
        for vehicle in solution: #For each vehicle get the possible exchanges of request
            exchanges += getPossibleRouteSwapExchanges(solution[vehicle],vehicle)
        exchanges += getPossibleVehicleSwapExchanges(solution)
        return exchanges

    
    def DARP_Optimization(self): #Implementation of the DARP Optimization Algorithm (Figure 4.3)
        initialSolution = self.generateInitialSolution() #Generaste initial solution using ARV algorithm
        listOfSolutions = [initialSolution] #Add solution to the list of solutions
        
        numberOfIterations = 0  
        numberOfIterationsWithoutImprovement = 0
        bestSolution = initialSolution

        """
        The stopping condition will be reached if one of the following happens:
        - There are no more solution candidates to be evaluated
        - All the solutions have been explored 
        - The maximum number of iterations has been reached
        - The maximum number of iterations without improvement has been reached
        """
        #Have Stopping conditions have been met?
        while numberOfIterations < self.numberOfIterations and numberOfIterations < self.numberOfIterationsWithoutImprovement and len(listOfSolutions) > 0: #
            
            canditateList = self.generateCLG(listOfSolutions.pop()) #Generate the Candidate List of Solutions
            
            for canditate in canditateList:
                isDominated = self.checkIfDominated(canditate, canditateList) #Check if the current solution is dominated by any other solution in the list
                if isDominated:
                    canditateList.remove(canditate)
            
            solutionList = self.getLowestDeadHeadingCost(canditateList) #Get the solution with the lowest deadheading cost
            solutionList = self.getLowestKilometersCost(solutionList,canditateList) #Get the solution with the lowest kilometers cost
            solutionList = self.getLowestWaitingTimeCost(solutionList,canditateList) #Get the solution with the lowest waiting time cost

            for solution in solutionList:
                if solution not in listOfSolutions:
                    listOfSolutions.append(solution)    
        
        return bestSolution #Return an ordered list of elementes that are being served by the vehicles
    
    def generateCLG(self, solution):
        exchanges = self._getAllPossibleExchanges(solution)
        canditate = None
        canditateSolutionList = []
        for i,exchange in enumerate(exchanges):
            type = exchange[0]
            if type == EXCHANGE_TYPES["ROUTE"]:
                canditate = self.routeSwap(exchange,solution)
            else:
                canditate = self.vehicleSwap(exchange,solution)
            
            if self._isValidCanditate(canditate):
                canditateSolutionList.append(Candidate(canditate))
        return canditateSolutionList #Return the list of solutions that are feasible as a candiate classes

busHandlerTabuSearch = BusHandlerTabuSearch(5, 10)
print(busHandlerTabuSearch.requests[2].origin.getTimeWindow())




        