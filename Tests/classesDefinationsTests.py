import sys

sys.path.append(r'C:\Users\lukec\Documents\Thesis\BusRouting\FYP-Flexible-Bus')

import classesDefinations as cdf

request1 = cdf.Request(1, cdf.Cords(35.9140339,14.4441213), cdf.Cords(35.9088368,14.5045232),0, 2)
request2 = cdf.Request(2, cdf.Cords(35.8708978,14.5072541), cdf.Cords(35.8275555,14.4456632),0, 2)
request3 = cdf.Request(3, cdf.Cords(35.8273755,14.4457106), cdf.Cords(35.8914893,14.5040276),0, 2)
request4 = cdf.Request(4, cdf.Cords(35.859368, 14.491918), cdf.Cords(35.886295, 14.496540),0, 2)

print("=================================== TEST 1 ===================================================")
print("Testing the Request class creation")

print("Request 1: ", request1)
print("Request 2: ", request2)
print("Request 3: ", request3)
print("Request 4: ", request4)

vehicle1 = cdf.Vehicle(1,10, cdf.Cords(35.8942679,14.5086503))
vehicle2 = cdf.Vehicle(2,10, cdf.Cords(35.8942679,14.5086503))

print("\n")

print("=================================== TEST 2 ===================================================")
print("Testing the Vehicle class creation")

print("Vehicle 1: ", vehicle1)
print("Vehicle 2: ", vehicle2)

vehicle1.addRequestToRoute(request1)
vehicle1.addRequestToRoute(request2)
vehicle2.addRequestToRoute(request3)
vehicle2.addRequestToRoute(request4)
print("\n")

print("=================================== TEST 3 ===================================================")
print("Testing the Vehicle class addRequestToRoute")

vehicle1.printRoute() #Print Vehicle one Route
vehicle2.printRoute() #Print Vehicle two Route

print ("Vehicle 1 Route Distance: "+str(vehicle1.getRouteDistance())+"m")
print ("Vehicle 1 Route TIme: ", str(vehicle1.getRouteTime()) + "s")
print ("Vehicle 2 Route Distance: "+str(vehicle2.getRouteDistance())+"m")
print ("Vehicle 2 Route TIme: ", str(vehicle2.getRouteTime()) + "s")
print("\n")

print("=================================== TEST 4 ===================================================")
print("Testing the Vehicle class arrivedAtNextStop")

print(vehicle1)
vehicle1.arrivedAtNextStop(20)
vehicle1.arrivedAtNextStop(20)
print(vehicle1)
vehicle1.printRoute()