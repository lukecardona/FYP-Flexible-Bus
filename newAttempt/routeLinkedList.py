class RouteNode:
    def __init__(self,cords):
        self.cords = cords
        self.next = None
    
    def __str__(self):
        return "Req Id: " + str(self.getRequestId()) + " -> " + str(self.cords)
    
    def __repr__(self):
        return "Req Id: " + str(self.getRequestId()) + " -> " + str(self.cords)
    
    def getLatitude(self):
        return self.cords.getLatitude()
    
    def getLongitude(self):
        return self.cords.getLongitude()
    
    def getStart(self):
        return self.cords.getStart()
    
    def getRequestId(self):
        return self.cords.getRequestId()
    
    def getTimeWindow(self):
        return self.cords.getTimeWindow()

class RouteLinkedList:
    def __init__(self):
        self.head = None
        self.tail = None
        self.size = 0

    def __str__(self):
        temp = self.head
        s = ""
        while temp != None:
            s += str(temp) + " \n"
            temp = temp.next
        return s
    
    def insertAtStart(self, cords):
        newNode = RouteNode(cords)
        if self.head == None:
            self.head = newNode
            self.tail = newNode
        else:
            newNode.next = self.head
            self.head = newNode
        self.size += 1

    def insertAtEnd(self, cords):
        newNode = RouteNode(cords)
        if self.head == None:
            self.head = newNode
            self.tail = newNode
        else:
            self.tail.next = newNode
            self.tail = newNode
        self.size += 1
    
    def insertAtIndex(self,cords, index):
        if index == 0:
            self.insertAtStart(cords)
        elif index == self.size:
            self.insertAtEnd(cords)
        elif index > self.size:
            print("Index out of bound")
        else:
            newNode = RouteNode(cords)
            temp = self.head 
            for i in range(index-1):
                temp = temp.next
            newNode.next = temp.next
            temp.next = newNode
            self.size += 1

    def switchNodes(self, index1, index2):
        if index1 == -1 or index2 == -1:
            raise ValueError("Invalid requests id or cordinates given")
        
        if index1 == index2:
            print("Same index given")
            return

        if index1 > index2:
            index1, index2 = index2, index1
        
        prev1 = prev2 = None
        node1 = node2 = self.head

        for i in range(max(index1, index2) + 1):
            if i < index1:
                prev1 = node1
                node1 = node1.next
            if i < index2:
                prev2 = node2
                node2 = node2.next

        # Handle cases where nodes are adjacent
        if index2 - index1 == 1:
            if prev1:
                prev1.next = node2
            else:
                self.head = node2
            node1.next = node2.next
            node2.next = node1
        else: # Non-adjacent nodes
            if prev1:
                prev1.next = node2
            else:
                self.head = node2
            if prev2:
                prev2.next = node1
            else:
                self.head = node1
            # Swap next pointers
            temp = node1.next
            node1.next = node2.next
            node2.next = temp

        # Update tail if necessary
        if index2 == self.size - 1:
            self.tail = node1
        elif index1 == self.size - 1:
            self.tail = node2


    def getIndex(self, cords):

        if self.head == None:
            print("List is empty")
            return -1

        #Else get the index
        temp = self.head
        index = 0
        while temp != None:
            if temp.cords == cords:
                return index
            temp = temp.next
            index += 1
        return -1
        
    def deleteAtStart(self):
        if self.head == None:
            raise ValueError("Called delete at start of Linked List, but list is empty")
        else:
            temp = self.head
            self.head = self.head.next
            self.size -= 1 
            return temp.cords
    
    def deleteNode(self,cords):
        if self.head == None:
            print("List is empty")
        else:
            temp = self.head
            if temp.cords == cords:
                self.head = self.head.next
                self.size -= 1
                return

            while temp.next != None:
                if temp.next.cords == cords:
                    temp.next = temp.next.next
                    self.size -= 1
                    break
                temp = temp.next

    def printList(self):
        temp = self.head
        while temp != None:
            print(temp)
            temp = temp.next

    def getNodeAtIndex(self, index):
        if index >= self.size:
            raise ValueError("Index out of bound")
        temp = self.head
        for i in range(index):
            temp = temp.next
        return temp
    
    def getPairOfRequest(self,reqId):
        temp = self.head
        pair = []
        for i in range(self.size):
            if temp.getRequestId() == reqId:
                pair.append(temp.requestId)
            temp = temp.next
        if len(pair) == 2:
            return pair
        else:
            Warning("Request Id Pair not found")

    def getSize(self):
        return self.size
    
    def getListOfCords(self):
        temp = self.head
        arr = []
        while temp != None:
            arr.append(temp.cords)
            temp = temp.next
        return arr