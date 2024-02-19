from .busHandlerHelper import BusHandler
import gymnasium as gym
from gymnasium import spaces
import numpy as np

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

    def initMap(self):
        self.map = Map(center=[35.908915,14.442416], zoom=11)
        display(self.map)
        #create 10 colors 
        self.colors = ["red","blue","green","purple","orange","darkred","lightred","black","darkblue","darkgreen"]

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

    def getRequestObservation(self):
        #Create an np array of the following format:
        # [requestLocationLatitude,requestLocationLongitude, requestDestinationLatitude,requestDestinationLongitude, requestPassengerCount]
        request = self.currentRequest
        origin = request.getOrigin()
        destination = request.getDestination()
        requestObservation = np.array([origin.getLatitude(),origin.getLongitude(),destination.getLatitude(),destination.getLongitude(),request.getPassengerAmount()], dtype=np.float32)
        return requestObservation
    
    def getBusesLocationsObservation(self):
        busesLocations = np.zeros((self.numberOfBuses,2), dtype=np.float32)
        for i,vehicle in enumerate(self.vehicles):
            location = vehicle.getPosition()
            busesLocations[i] = [location.getLatitude(),location.getLongitude()]
        assert busesLocations.shape == (self.numberOfBuses,2)
        return busesLocations
    
    def getPassengerCountsObservation(self):
        passengerCounts = np.zeros((self.numberOfBuses), dtype=np.int8)
        for i,vehicle in enumerate(self.vehicles):
            passengerCounts[i] = vehicle.getCurrentCapacity()
        assert passengerCounts.shape == (self.numberOfBuses,)
        return passengerCounts
    
    def getBusesRoutesObservation(self):
        busesRoutes = np.zeros((self.numberOfBuses,self.getCapacity()*2,2), dtype=np.float32)
        for i in range(self.numberOfBuses):
            busesRoutes[i] = self._getBusRoute(i)
        return busesRoutes

    def getCapacity(self):
        return self.vehicles[0].getCapacity()
    
    def getReward(self,action):
        acceptedReward = 0
        distanceReward = 0
        waitingTimeReward = 0

        if action == ACCEPTED:
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
                             icon=AwesomeIcon(name='bus', marker_color=self.colors[i], icon_color='white', spin=False))
            self.map.add_layer(marker)

class BusHandler(gym.Env):
    def __init__(self,numberOfBuses,numberOfRequests,render_mode=None):
        self.metadata = {'render_modes': ['human']}
        
        self.busHandler = GymBusHandler(numberOfBuses,numberOfRequests)
        self.numberOfBuses = numberOfBuses
        self.numberOfRequests = numberOfRequests
       
        self.action_space = spaces.Box(low=np.array([0,0]), high=np.array([1,self.numberOfBuses-1]),shape=(2,), dtype=np.int32)
        
        self.observation_space = spaces.Dict({
            "request": spaces.Box(low=0, high=90, shape=(5,), dtype=np.float32),
            "buses": spaces.Dict({
                "locations": spaces.Box(low=0, high=90, shape=(self.numberOfBuses,2), dtype=np.float32),
                "passenger_counts": spaces.Box(low=0, high=self.busHandler.getCapacity(), shape=(self.numberOfBuses,), dtype=np.int8),
                "routes": spaces.Box(low=0, high=90, shape=(self.numberOfBuses,self.busHandler.getCapacity()*2,2), dtype=np.float32)
            })
        })

        assert render_mode is None or render_mode in self.metadata["render_modes"] #Ensure that the render mode selected is validd
        self.render_mode = render_mode

    def _get_mask(self,obs):
        npMask = np.zeros((self.numberOfBuses,2), dtype=np.int8)
        requestAmount = obs["request"][4]
        for i,passengerAmount in enumerate(obs["buses"]["passenger_counts"]):
            if passengerAmount + requestAmount < self.busHandler.vehicles[i].getCapacity():
                npMask[i] = [1,1]
            else:
                npMask[i] = [0,0]
        pass

    def _get_obs(self):
        obs = {"request": self.busHandler.getRequestObservation(), "buses": {"locations": self.busHandler.getBusesLocationsObservation(), "passenger_counts": self.busHandler.getPassengerCountsObservation(), "routes": self.busHandler.getBusesRoutesObservation()}}
        mask = self._get_mask(obs)
        return obs
    
    def _get_info(self):
        return{
            "distance": self.busHandler.getTotalDistance(),
            "time": self.busHandler.getTotalTime()
        }
    
    def _render_frame(self):
        if self.render_mode == "human":
            self.busHandler.renderRoutes()
    
    def step(self,action):
        accepted = action[0]
        done = False
        reward = 0

        if accepted == REJECTED:
            done = self.busHandler.rejectRequest() #Reject the request
        else:
            done = self.busHandler.acceptRequest(action[1]) #Accept the request

        self.busHandler.updateState(done)

        reward = self.busHandler.getReward(action[0])
        observation = self._get_obs()
        info = self._get_info()

        if self.render_mode == "human":
            self._render_frame()
        
        truncated = done

        return observation, reward, done, truncated, info
    
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.busHandler = GymBusHandler(self.numberOfBuses,self.numberOfRequests)
        info = self._get_info()
        observation = self._get_obs()
        if self.render_mode == "human":
            self.busHandler.initMap()
            self._render_frame()

        return observation,info
    
    def close(self):
        pass