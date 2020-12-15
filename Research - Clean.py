#!/usr/bin/env python
# coding: utf-8

# In[1]:


#Code Created By: Alexander Kostoff
#Last Update 12/15/2020
from neo4j import GraphDatabase
import numpy as np
import math

class neo4jData:

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()
        
    def insertNode(self, address, data, kernal,nodeId,dataCount, cycles, samples, cycleAverage, cycleStDeviation):
        with self.driver.session() as session:
            node = session.write_transaction(self.createNode, address, data, kernal, nodeId, dataCount,
                                             cycles, samples, cycleAverage, cycleStDeviation)
    
    @staticmethod     
    def createNode(tx, address, data, kernal, nodeId, dataCount, cycles, samples, cycleAverage, cycleStDeviation):
        result = tx.run("CREATE (a:Node) "
                        "SET a.address = $address "
                        "SET a.data = $data "
                        "SET a.kernal = $kernal "
                        "SET a.nodeId = $nodeId "
                        "SET a.dataCount = $dataCount "
                        "SET a.cycles = $cycles "
                        "SET a.samples = $samples "
                        "SET a.cycleAverage = $cycleAverage "
                        "SET a.cycleStDeviation = $cycleStDeviation ", address=address, data=data, kernal=kernal, nodeId=nodeId, 
                        dataCount=dataCount, cycles=cycles, samples=samples, cycleAverage=cycleAverage, 
                        cycleStDeviation=cycleStDeviation)
    
    @staticmethod
    def createChildRelation(tx, parentNodeId, childNodeId):
        result = tx.run("MATCH (a:Node),(b:Node) "
                        "WHERE a.nodeId = $parentNodeId AND b.nodeId = $childNodeId "
                        "CREATE (a)-[child:child]->(b) ", parentNodeId=parentNodeId, childNodeId=childNodeId)
    @staticmethod
    def createParentRelation(tx, parentNodeId, childNodeId):
        result = tx.run("MATCH (a:Node),(b:Node) "
                        "WHERE a.nodeId = $parentNodeId AND b.nodeId = $childNodeId "
                        "CREATE (b)-[parent:parent]->(a) ", parentNodeId=parentNodeId, childNodeId=childNodeId)
        
    def insertChildRelation(self, parentNodeId, childNodeId):
        with self.driver.session() as session:
            relation = session.write_transaction(self.createChildRelation, parentNodeId, childNodeId)
    
    def insertParentRelation(self, parentNodeId, childNodeId):
        with self.driver.session() as session:
            relation = session.write_transaction(self.createParentRelation, parentNodeId, childNodeId)
                
    @staticmethod
    def deleteChildRelation(tx, parentNodeId, childNodeId):
        result = tx.run("MATCH (a:Node)-[r:child]->(b:Node) " 
                        "WHERE a.nodeId = $parentNodeId AND b.nodeId = $childNodeId "
                        "DELETE r ", parentNodeId=parentNodeId, childNodeId=childNodeId)
    @staticmethod
    def deleteParentRelation(tx, parentNodeId, childNodeId):
        result = tx.run("MATCH (b:Node)-[r:parent]->(a:Node) " 
                        "WHERE a.nodeId = $parentNodeId AND b.nodeId = $childNodeId "
                        "DELETE r ", parentNodeId=parentNodeId, childNodeId=childNodeId)
        
    def insertDeleteChildRelation(self, parentNodeId, childNodeId):
        with self.driver.session() as session:
            relation = session.write_transaction(self.deleteChildRelation, parentNodeId, childNodeId)
    
    def insertDeleteParentRelation(self, parentNodeId, childNodeId):
        with self.driver.session() as session:
            relation = session.write_transaction(self.deleteParentRelation, parentNodeId, childNodeId)
    
    
    def findStartId(self):
        theReturn = -1
        nodeNumQuery = "MATCH (a:Node) RETURN a.nodeId "

        with self.driver.session() as session:
            nodeNums = session.run(nodeNumQuery)
            
            for nodeNum in nodeNums:
                theReturn = nodeNum[0]
                
        return theReturn
    


# In[2]:


neoData = neo4jData("bolt://localhost:7687", "neo4j", "test")
 
nodeId = neoData.findStartId()


cycleData = []
loopCount = []
if nodeId == -1:
    nodeId = nodeId
    startId = nodeId + 1
else:
    nodeId = nodeId+1
    startId = nodeId+1

samples = 0

class Node:
    """
    Class Node
    """
    def __init__(self, value, address, isKernel, cycleCount, cycleAverage, cycleStDeviation, prob, predecessor):
        self.data = value
        self.address = address
        self.isKernel = isKernel
        self.probability = prob
        self.predecessors = predecessor
        self.cycleCount = cycleCount
        self.cycles = []
        self.cycleAverage = cycleAverage
        self.cycleStDeviation = cycleStDeviation
        self.children = []
        self.count = 1
    #Rich comparison methods  
    def __lt__(self, other):
        return self.data < other.data

    def __eq__(self, other):
        return self.data == other.data


class Tree:
    
    
    """
    Class tree will provide a tree as well as utility functions.
    """
    
    def __init__(self):
        self.root = None
        self.contexts = dict()
        self.jointprob = dict()

    def createNode(self, data, address, isKernel, cycles, cycleAverage, cycleStDeviation, prob=0, predecessor=0):
        """
        Utility function to create a node.
        """
        
        node = Node(data, address, isKernel, cycles, cycleAverage, cycleStDeviation, prob, predecessor)
        
        if self.root is None:
            self.root = node
        return node

    def insertChild(self, node , childNode):
        """
        Insert function will insert a node into tree.
        Duplicate keys are not allowed.
        """
        
        #if tree is empty , return a root node
        if node is None:
            return childNode

        for child in node.children:
            if child is not None and child.data == childNode.data:
                child.count = child.count + 1
                return child
        node.children.append(childNode)
        
        return childNode
    
    def insertCycles(self, leafNode, cycles):
        leafNode.cycles.append(cycles)
        cycleSum = leafNode.cycleCount = sum(leafNode.cycles)
        average = leafNode.cycleAverage = round(cycleSum/len(leafNode.cycles),2)
        
        total = 0
        for x in leafNode.cycles:
            total = total + math.pow(x - average,2)
            
        #print(leafNode.data + ":")
        #print(total)
        
        variance = total/len(leafNode.cycles)
        leafNode.cycleStDeviation = round(math.sqrt(variance),2)
        
    
    def insertIntoGraphDFS(self, root, parentId, arrow="", prob=1):
        #global loopCount
        
        if root is None:# or root.data.upper() == "EOS":
            #print ("EOS")
            return

        #if(root.probability * prob < 0.01):
            #return
            
        #print(parentId)
        
        #if root.data.upper() != "SOS3":
        arrow = arrow + "->"
        global nodeId
        nodeId = nodeId + 1
        
        global samples
        samples = root.count
        #if dataCount == 1:
        neoData.insertNode(root.address.upper(), root.data.upper(), root.isKernel.upper(), nodeId, root.count, root.cycleCount,samples,root.cycleAverage,root.cycleStDeviation)
        neoData.insertChildRelation(parentId, nodeId)
        neoData.insertParentRelation(parentId, nodeId)
        
        parentId = nodeId
        
        #print(arrow, root.data.upper(), " probability: ", root.probability ," joint prob (", root.probability * prob, ")", " count (", root.count, ")")
                
       
                 
        for child in sorted(root.children):
            self.insertIntoGraphDFS(child, parentId, arrow, prob * root.probability)
            
        if len(root.children) == 0:
            
            nodeId = nodeId + 1
            neoData.insertChildRelation(startId, nodeId)
            neoData.insertParentRelation(startId, nodeId)
            neoData.insertDeleteChildRelation(startId, nodeId-1)
            neoData.insertDeleteParentRelation(startId, nodeId-1)
            
            if root.data.upper() == "PLACEHOLDER FOR IF 1 PROCESS":
                neoData.inDeleteSpecificNode()
                nodeId = nodeId-1
            
            #print(arrow+"->"+"EOS", " probability: ", root.probability ," joint prob (", root.probability * prob, ")", " count (", root.count, ")")
            
            
    def testPrint(self,root):
        for child in sorted(root.children):
            self.testPrint(child)
        print(root.data.upper() + "," +str(root.cycleCount) + "->")


# In[3]:


inFile = open('out.swf', 'r')

address = ""
data = ""
kernel = ""
cycles = 0
samples = 0
cycleAverage = 0
cycleStDeviation = 0
#bool for if there are no processes
hasNoProcesses = []
hasNoProcesses.append("x")
processCount = 0

theTree = Tree()
parent = theTree.createNode("Root", "", "",0,0,0)

#read file from bottom to top
for line in reversed(list(inFile)):
    #print(line.rstrip())
    line.rstrip()
    #print(line)
    lineSplit = line.rsplit(' ', 3)
    #lineSplit[-1] = lineSplit[-1].strip()
    lineSplit[0] = lineSplit[0].strip()
    #print(lineSplit)
    
    if not line.strip():
        continue
    
    if lineSplit[0] != '':  
        address = lineSplit[0]
        #print(address) 
        
    if lineSplit[1] != '':  
        data = lineSplit[1]
        
        #print(data)
        
    if lineSplit[2] != '':
        if lineSplit[2] == "cycles:":
            kernel = ""
            #print()
            
            if processCount == 1:
                cyclesStr = lineSplit[0][-6:]
                cycles = int(cyclesStr)
                
                #print(parent.data)
                theTree.insertCycles(parent, cycles)
                cycles = 0
                
                returnNode = theTree.createNode("Placeholder for if 1 process", "x", "x", 0, 0, 0)
                parent = theTree.insertChild(parent, returnNode)
                
            processCount = 0
            
            hasNoProcesses.append("x")
            if len(hasNoProcesses) == 1:
                cyclesStr = lineSplit[0][-6:]
                cycles = int(cyclesStr)
                
                #print(parent.data)
                theTree.insertCycles(parent, cycles)
                cycles = 0
                
                parent = theTree.root
                
            
           
            continue
            
        else:
            kernel = lineSplit[2]
            #print(kernal)
    
    processCount = processCount + 1
    hasNoProcesses.clear()
    returnNode = theTree.createNode(data, address, kernel, cycles, cycleAverage, cycleStDeviation)
    #print(parent.data,"->", returnNode.data)
    parent = theTree.insertChild(parent, returnNode)
    

theTree.insertIntoGraphDFS(theTree.root, nodeId)
#theTree.testPrint(theTree.root) 

neoData.close()
inFile.close()


# In[ ]:





# In[ ]:





# In[ ]:




