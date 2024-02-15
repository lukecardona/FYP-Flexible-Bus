import sys

sys.path.append(r'C:\Users\lukec\Documents\Thesis\BusRouting\FYP-Flexible-Bus')

import routeLinkedList as rll
import classesDefinations as cdf

cords1 = cdf.Request_Cords(1,1,1,True)
cords2 = cdf.Request_Cords(2,2,1,False)
cords3 = cdf.Request_Cords(3,3,2,True)
cords4 = cdf.Request_Cords(4,4,2,False)
cords5 = cdf.Request_Cords(5,5,3,True)
cords6 = cdf.Request_Cords(6,6,3,False)
cords7 = cdf.Request_Cords(7,7,4,True)

print("=================================== TEST 1 ===================================================")
print("Creating Basic Cords to cords linked list Node Data: ")
print("cords 1 inseted at the end of the linked list: [1,True]")
print("cords 2 inseted at the end of the linked list: [1,False]")
print("cords 3 inseted at the start of the linked list: [2,True]")
print("cords 4 inseted at the end of the linked list: [2,False]")
print("cords 5 inseted at the start of the linked list: [3,True]")
print("cords 6 inseted at the end of the linked list: [3,False]")
print("cords 7 inseted at index 2 of the linked list: [4,True]")

# create a new linked list
llist = rll.RouteLinkedList()
 
# add nodes to the linked list
llist.insertAtEnd(cords1) #[1,True]
llist.insertAtEnd(cords2) #[[1,True],[1,False]]
llist.insertAtStart(cords3) #[[2,True],[1,True],[1,False]]
llist.insertAtEnd(cords4) #[[2,True],[1,True],[1,False],[2,False]]
llist.insertAtStart(cords5) #[[3,True],[2,True],[1,True],[1,False],[2,False]]
llist.insertAtEnd(cords6) #[[3,True],[2,True],[1,True],[1,False],[2,False],[3,False]]
llist.insertAtIndex(cords7, 2) #[[3,True],[2,True],[4,True],[1,True],[1,False],[2,False],[3,False]]
llist.printList()
print("\n")

print("=================================== TEST 2 ===================================================")
print("Deleting Nodes from the linked list: cords1, cords2, cords3")
llist.deleteNode(cords1) #[[3,True],[2,True],[4,True],[1,False],[2,False],[3,False]]
llist.deleteNode(cords2) #[[3,True],[2,True],[4,True],[2,False],[3,False]]
llist.deleteNode(cords3) #[[3,True],[4,True],[2,False],[3,False]]
 
llist.printList()
 
print("\nSize of linked list :", end=" ")
print(llist.getSize()) #4
print("\n")