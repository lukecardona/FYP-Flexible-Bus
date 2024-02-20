from .busHandlerHelper import BusHandler
import gymnasium as gym
from gymnasium import spaces
import numpy as np

from pettingzoo import AECEnv
from pettingzoo.utils import wrappers
from pettingzoo.utils import agent_selector



import polyline
import ipyleaflet
from ipyleaflet import Map,AwesomeIcon,Marker,Polyline

ACCEPTED = 0
REJECTED = 1
REWARD_PER_PASSENGER = 125

busIcon = AwesomeIcon(
    name='bus',
    marker_color='green',
    icon_color='white',
    spin=False
)

class GymBusHandler(BusHandler):
    def __init__(self, numberOfBuses,numberOfRequests):
        super().__init__(numberOfBuses,numberOfRequests)
        self.numberOfBuses = numberOfBuses
        self.numberOfRequests = numberOfRequests
        self.currentRequestAccepted = False
        self.map = None

    """
    OVERWRITING THE TWO FUNCTIONS BELOW
    """

    def rejectRequest(self):
        #Error Checking
        if(self.currentRequestIndex >= len(self.requests)):
            raise ValueError("No more requests to reject, index exceeded the requests list length.")
        #Reject the current request and move to the next one
        self.rejectedRequests.append(self.currentRequest)
        self.currentRequestIndex += 1
    
    def acceptRequest(self, vehicleIndex):
        vehicleIndex = int(vehicleIndex)

        #Error Checking
        if(vehicleIndex >= len(self.vehicles)):
            raise ValueError("Vehicle index exceeded the vehicles list length.")

        #Accept the current request and move to the next one
        self.vehicles[vehicleIndex].addRequestToRoute(self.currentRequest)
        self.currentRequestIndex += 1

    def initMap(self):
        self.map = Map(center=[35.908915,14.442416], zoom=11)
        display(self.map)
        #create 10 colors 
        self.colors = ["red","blue","green","purple","orange","darkred","lightred","black","darkblue","darkgreen"]

    def acceptRequestAgent(self,agent):
        self.acceptRequest(agent)
        self.currentRequestAccepted = True

    def rejectRequestAgent(self):
        pass

    def _getBusRoute(self, index):
        route = self.vehicles[index].getListOfCords()
        npRoute = np.zeros((self.getCapacity()*2,2), dtype=np.float32)
        if route != None:
            for i in range(len(route)):
                npRoute[i] = [route[i].getLatitude(),route[i].getLongitude()]
        return npRoute
    
    def _clearMap(self):
        for layer in self.map.layers:
            if not isinstance(layer, ipyleaflet.TileLayer):
                self.map.remove_layer(layer)

    def get_info(self,agent):
        if self.vehicles[agent].getRouteSize() == 0:
            return{
                "distance": 0,
                "time": 0
            }
        else:
            return{
                "distance": self.vehicles[agent].getRouteDistance(),
                "time": self.vehicles[agent].getRouteTime()
            }
    
    def get_obs(self,agent):
        obs = {}
        obs["request"] = self.getRequestObservation()
        obs["bus"] = {}
        obs["bus"]["location"] = self.getBusLocationObservation(agent)
        obs["bus"]["passenger_count"] = self.vehicles[agent].getCurrentCapacity()
        obs["bus"]["route"] = self._getBusRoute(agent)
        return obs

    def getRequestObservation(self):
        #Create an np array of the following format:
        # [requestLocationLatitude,requestLocationLongitude, requestDestinationLatitude,requestDestinationLongitude, requestPassengerCount]
        request = self.currentRequest
        origin = request.getOrigin()
        destination = request.getDestination()
        requestObservation = np.array([origin.getLatitude(),origin.getLongitude(),destination.getLatitude(),destination.getLongitude(),request.getPassengerAmount()], dtype=np.float32)
        return requestObservation
    
    def getBusLocationObservation(self,agent):
        busesLocation = np.zeros((2), dtype=np.float32)
        location = self.vehicles[agent].getPosition()
        busesLocation[0] = location.getLatitude()
        busesLocation[1] = location.getLongitude()
        return busesLocation

    def getCapacity(self):
        return self.vehicles[0].getCapacity()
    
    def getReward(self):
        acceptedReward = 0
        distanceReward = 0
        waitingTimeReward = 0

        if self.currentRequestAccepted == True:
            acceptedReward += self.currentRequest.getPassengerAmount()*REWARD_PER_PASSENGER
        else:
            acceptedReward += self.currentRequest.getPassengerAmount()*REWARD_PER_PASSENGER*-1
        
        for vehicle in self.vehicles:
            distanceReward += ((vehicle.getDistanceTravelled()*-1)/1000)
            waitingTimeReward += ((vehicle.getRequestWaitingTime()*-1)/60)

        reward = acceptedReward + distanceReward + waitingTimeReward
        return reward
    
    def renderRoutes(self):

        self._clearMap()

        for i,vehicle in enumerate(self.vehicles):
            if vehicle.getRouteSize() > 0:
                routeGeometry = vehicle.getRouteGeometry()
                route =  polyline.decode(routeGeometry)
                routeLine = Polyline(locations=route, color=self.colors[i], weight=2, opacity=1)
                self.map.add_layer(routeLine)

            vehicleLocation = vehicle.getPosition()
            marker = Marker(location=(vehicleLocation.getLatitude(),vehicleLocation.getLongitude()),
                             icon=AwesomeIcon(name='bus', marker_color=self.colors[i], icon_color='white', spin=False),
                             draggable=False,
                             title="Bus "+str(i))
            self.map.add_layer(marker)

    def reset(self):
        super().__init__(self.numberOfBuses,self.numberOfRequests)
        if self.map != None:
            self._clearMap()

class BusHandlerEnv(AECEnv):
    def __init__(self,numberOfBuses,numberOfRequests,render_mode=None):
        self.metadata = {'render_modes': ['human'], "name": "BusHandler-v0"}
        
        self.busHandler = GymBusHandler(numberOfBuses,numberOfRequests)
        self.numberOfBuses = numberOfBuses
        self.numberOfRequests = numberOfRequests

        self.possible_agents = list(range(self.numberOfBuses)) 
       
        self._action_spaces = {agent: spaces.Discrete(2) for agent in self.possible_agents}#Accept or reject the request
        self._observation_spaces = { 
            agent: 
                spaces.Dict({
                "observation": 
                    spaces.Dict({
                        "request": spaces.Box(low=0, high=90, shape=(5,), dtype=np.float32),
                        "bus": spaces.Dict({
                            "location": spaces.Box(low=0, high=90, shape=(2,), dtype=np.float32),
                            "passenger_count": spaces.Discrete(self.busHandler.getCapacity()),
                            "route": spaces.Box(low=0, high=90, shape=(self.busHandler.getCapacity()*2,2), dtype=np.float32)
                        }),
                    
                "action_mask": spaces.Box(low=0, high=1, shape=(2,), dtype=np.int8)
                }),
            }) for agent in self.possible_agents}
        
        print(self._observation_spaces[0]["observation"]["bus"]["route"].shape)

        assert render_mode is None or render_mode in self.metadata["render_modes"] #Ensure that the render mode selected is validd
        self.render_mode = render_mode

        if self.render_mode == "human":
            self.busHandler.initMap()

    def _get_mask(self,agent,obs):
        if (self.busHandler.vehicles[agent].getCurrentCapacity()+obs["request"][4]) <= self.busHandler.vehicles[agent].getCapacity():
            return np.array([1,1], dtype=np.int8)
        else:
            return np.array([0,1], dtype=np.int8)

    def _get_obs(self,agent):
        obs = self.busHandler.get_obs(agent)
        mask = self._get_mask(agent,obs)
        return {"obsesrvation": obs, "action_mask": mask}
    
    # def _get_info(self,agent):
    #     info = self.busHandler.get_info(agent)
    #     return info #Returns time and distance of a route
    
    def _render_frame(self):
        if self.render_mode == "human":
            self.busHandler.renderRoutes()

    def observation_space(self, agent):
        return self._observation_spaces[agent]
    
    def action_space(self, agent):
        return self._action_spaces[agent]
    
    def observe(self, agent):
        return self._get_obs(agent)
    
    def step(self,action):
        accepted = action
        reward = 0

        if accepted == REJECTED:
            self.busHandler.rejectRequestAgent() #Reject the request
        else:
            self.busHandler.acceptRequestAgent(self.agent_selection) #Accept the request

        if self._agent_selector.is_last():
            if self.busHandler.currentRequestAccepted == False: #If the request was not accepted, reject it
                self.busHandler.rejectRequest()

            termination = self.busHandler.endCheck()
            self.busHandler.updateState(termination) #Update the state of the environment
            self.terminations = {a: termination for a in self.agents} #Set the termination for all agents

            reward = self.busHandler.getReward() # Get the reward
            self.rewards = {a: reward for a in self.agents} #Set the reward for all agents
        else:
            self._clear_rewards()

        if self.render_mode == "human":
            self._render_frame()
        
        self.truncations = self.terminations
        self.agent_selection = self._agent_selector.next() #Select the next agent
        self._cumulative_rewards[self.agent_selection] = 0 #Reset the cumulative rewards for the next agent
        self._accumulate_rewards() #Accumulate the rewards for the next agent
    
    def reset(self, seed=None, options=None):
        self.agents = self.possible_agents
        self.busHandler.reset()
        
        self.infos = dict(zip(self.agents, [{} for _ in self.agents]))
        observations = {agent: self._get_obs(agent) for agent in self.possible_agents}

        self._agent_selector = agent_selector(self.agents)
        self.agent_selection = self._agent_selector.reset()
        self._cumulative_rewards = {a: 0 for a in self.agents}

        self.terminations = {a: False for a in self.agents}
        self.truncations = {a: False for a in self.agents}
        self.rewards = {a: 0 for a in self.agents}

        if self.render_mode == "human":
            self._render_frame()
    
    def close(self):
        pass