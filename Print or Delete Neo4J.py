#!/usr/bin/env python
# coding: utf-8

# In[1]:


#Code Created By: Alexander Kostoff
#Last UpdateL 11/29/2020

from neo4j import GraphDatabase


# In[3]:


class graphNeo:

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def deleteAllNodes(self):
        deleteAll = "MATCH (a) DETACH DELETE a"
        with self.driver.session() as session:
            deleted = session.run(deleteAll)
    
    def printNodes(self):
        nodeQuery = "MATCH (a:Node) RETURN a"
        rootPrint = "MATCH (a:ROOT) RETURN a"
        with self.driver.session() as session:
            root = session.run(rootPrint)
            nodes = session.run(nodeQuery)

            for roots in root:
                print(root)
            
            for node in nodes:
                print(node)


neo = graphNeo("bolt://localhost:7687", "neo4j", "test")
neo.deleteAllNodes()
#neo.printNodes()
neo.close()


# In[ ]:




