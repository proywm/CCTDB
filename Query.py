#!/usr/bin/env python
# coding: utf-8

# In[1]:


from neo4j import GraphDatabase


# In[2]:


class graphNeo:

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()
    
    def query(self, nodeId):
        nodeQuery = "MATCH (a:Node)-[r:parent]->(b:Node) WHERE a.nodeId = $nodeId RETURN a.data,b.data,b.nodeId "
        
        with self.driver.session() as session:
            
            nodes = session.run(nodeQuery, nodeId = nodeId)
            
            for node in nodes:
                print(node[0] + " -> " + node[1])
                #print(node)
                self.query(node[2])
                    
        

neo = graphNeo("bolt://localhost:7687", "neo4j", "test")
inputId = input("Enter in the nodeId for path to Root: ")
print()
nodeId = int(inputId)
neo.query(nodeId)

neo.close()


# In[ ]:




