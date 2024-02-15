import bushandler

import gymnasium as gym
from gymnasium import spaces
import numpy as np

import folium
import polyline

from ipyleaflet import Map,AwesomeIcon, Marker

ACCEPTED = 0
REJECTED = 1
REWARD_PER_PASSENGER = 125

busIcon = AwesomeIcon(
    name='bus',
    marker_color='green',
    icon_color='white',
    spin=False
)

class GymBusHandler(bushandler.BusHandler):
    def __init__(self, numberOfBuses,numberOfRequests):
        super().__init__(numberOfBuses,numberOfRequests)
        self.numberOfBuses = numberOfBuses
        self.numberOfRequests = numberOfRequests
        self.map = folium.Map(location=[35.918915, 14.372416], zoom_start=12)
        
        #create 10 colors 
        self.colors = ["red","blue","green","purple","orange","darkred","lightred","beige","darkblue","darkgreen"]

    def _getBusRoute(self, index):
        route = self.vehicles[index].getListOfCords()
        npRoute = np.zeros((self.getCapacity()*2,2), dtype=np.float32)
        if route != None:
            for i in range(len(route)):
                npRoute[i] = [route[i].getLatitude(),route[i].getLongitude()]
        return npRoute

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
            distanceReward += (vehicle.getDistanceTravelled()*-1)
            waitingTimeReward += (vehicle.getRequestWaitingTime()*-1)

        reward = acceptedReward + distanceReward + waitingTimeReward
        return reward
    
    def renderRoutes(self):
        map = self.map
        for i,vehicle in enumerate(self.vehicles):
            if vehicle.getRouteSize() > 0:
                routeGeometry = vehicle.getRouteGeometry()
                route =  polyline.decode(routeGeometry)
                folium.PolyLine(route, color=self.colors[i], weight=2.5, opacity=1).add_to(map)

            folium.Marker(
                [vehicle.getPosition().getLatitude(),vehicle.getPosition().getLongitude()],
                icon=folium.Icon(icon="bus",prefix="fa",color=self.colors[i]),
                popup="Bus "+str(i)).add_to(map)
        display(map)


class BusRoutingSystem(gym.Env):
    def __init__(self,numberOfBuses,numberOfRequests,render_mode=None):
        self.metadata = {'render_modes': ['human']}
        
        self.busHandler = GymBusHandler(numberOfBuses,numberOfRequests)
        self.numberOfBuses = numberOfBuses
        self.numberOfRequests = numberOfRequests
       
        self.action_space = spaces.Box(low=np.array([0,0]), high=np.array([1,self.numberOfBuses-1]), dtype=np.int8)
        
        self.observation_space = spaces.Dict({
            "request": spaces.Box(low=0, high=1, shape=(5,), dtype=np.float32),
            "buses": spaces.Dict({
                "locations": spaces.Box(low=0, high=90, shape=(self.numberOfBuses,2), dtype=np.float32),
                "passenger_counts": spaces.Box(low=0, high=self.busHandler.getCapacity(), shape=(self.numberOfBuses,), dtype=np.int8),
                "routes": spaces.Box(low=0, high=90, shape=(self.numberOfBuses,self.busHandler.getCapacity()*2,2), dtype=np.float32)
            })
        })

        assert render_mode is None or render_mode in self.metadata["render_modes"] #Ensure that the render mode selected is validd
        self.render_mode = render_mode

    def _get_obs(self):
        return {"request": self.busHandler.getRequestObservation(), "buses": {"locations": self.busHandler.getBusesLocationsObservation(), "passenger_counts": self.busHandler.getPassengerCountsObservation(), "routes": self.busHandler.getBusesRoutesObservation()}}
    
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

        reward = self.busHandler.getReward()
        observation = self._get_obs()
        info = self._get_info()

        if self.render_mode == "human":
            self._render_frame()
        
        return observation, reward, done, info
    
    def reset(self, seed=None):
        self.busHandler = GymBusHandler(self.numberOfBuses,self.numberOfRequests)
        info = self._get_info()
        observation = self._get_obs()
        if self.render_mode == "human":
            self._render_frame()
        return observation,info
    
    def close(self):
        pass

busRoutingSystem = BusRoutingSystem(5,10)
obs,info = busRoutingSystem.reset()