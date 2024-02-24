from busHandlerHelper import BusHandler

"""
Implentation of "A multi objective approach for DRT service using tabu search" by Torgal, Marta, Dias, Teresa Galvão, Fontes, Tânia
Transportation Research Procedia, 2021, pg 91-98 https://www.sciencedirect.com/science/article/pii/S2352146521001460 

Another neater Implementation: https://repositorio-aberto.up.pt/bitstream/10216/126884/2/392706.pdf
"""

class BusHandlerTabuSearch(BusHandler):
    def __init__(self, numberOfBuses,numberOfRequest,numberOfIterations,numberOfIterationsWithoutImprovement,threshold = 12):
        super().__init__(numberOfBuses,numberOfRequest)
        self.tabuList = []
        self.currentKnownRequests = []
        self.numberOfIterations = numberOfIterations
        self.numberOfIterationsWithoutImprovement = numberOfIterationsWithoutImprovement
        self.threshold = threshold

    def __str__(self):
        return super().__str__() + "\nTabu List: " + str(self.tabuList) + "\nCurrent Known Requests: " + str(self.currentKnownRequests)
    
    def DARP_Optimization(self):
        initialSolution = self.generateInitialSolution() #Generaste initial solution using ARV algorithm
        listOfSolutions = [initialSolution] #Add solution to the list of solutions
        
        numberOfIterations = 0  
        numberOfIterationsWithoutImprovement = 0
        bestSolutionList = initialSolution

        """
        The stopping condition will be reached if one of the following happens:
        - There are no more solution candidates to be evaluated
        - All the solutions have been explored 
        - The maximum number of iterations has been reached
        - The maximum number of iterations without improvement has been reached
        """

        while numberOfIterations < self.numberOfIterations and numberOfIterations < self.numberOfIterationsWithoutImprovement and len(listOfSolutions) > 0:
            
            canditateList = self.generateCLG(bestSolution) #Generate the Candidate List of Solutions
            
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
        
        return bestSolutionList #Return an ordered list of elementes that are being served by the vehicles

busHandlerTabuSearch = BusHandlerTabuSearch(5, 10)
print(busHandlerTabuSearch.requests[2].origin.getTimeWindow())




        