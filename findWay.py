import pandas as pd
from utils import *
import ast
import algorithm as al
from tqdm import tqdm
import redis

r = redis.Redis(db=4)
r2 = redis.Redis(db=3)
r3 = redis.Redis(db=5)
"""gen undirected graph"""
for node in nodes:
    minXleftOfNode = 100000
    minXrightOfNode = 100000
    minYupOfNode = 100000
    minYdownOfNode = 100000
    eNodes = []
    for node2 in nodes:
        temp = Euclidean(node[0], node[1], node2[0], node2[1])
        if node[0] == node2[0] and node[1] == node2[1]:
            continue
        if node[0] == node2[0] and (node[1] - node2[1]) < 0:
            if temp < minYupOfNode:
                minYupOfNode = temp
        if node[0] == node2[0] and (node[1] - node2[1]) > 0:
            if temp < minYdownOfNode:
                minYdownOfNode = temp

        if node[1] == node2[1] and node[0] - node2[0] < 0:
            if temp < minXrightOfNode:
                minXrightOfNode = temp
        if node[1] == node2[1] and node[0] - node2[0] > 0:
            if temp < minXleftOfNode:
                minXleftOfNode = temp

    for node3 in nodes:
        temp = Euclidean(node[0], node[1], node3[0], node3[1])
        if node[0] == node3[0] and temp == minYupOfNode and node[1] - node3[1] < 0:
            eNodes.append(node3)
        if node[0] == node3[0] and temp == minYdownOfNode and node[1] - node3[1] > 0:
            eNodes.append(node3)
        if node[1] == node3[1] and temp == minXleftOfNode and node[0] - node3[0] > 0:
            eNodes.append(node3)
        if node[1] == node3[1] and temp == minXrightOfNode and node[0] - node3[0] < 0:
            eNodes.append(node3)
    d[str(node)] = eNodes

vertexes = dict()
"""gen directed graph"""
for node1 in d:
    node1_change = ast.literal_eval(node1)
    list_node = []
    for node2 in d[node1]:
        dir = None
        temp = set(node2[2]).intersection(set(node1_change[2]))
        if node1_change[0] == node2[0]:
            if node1_change[1] - node2[1] > 0:
                dir = 'l'
            if node1_change[1] - node2[1] < 0:
                dir = 'r'
        if node1_change[1] == node2[1]:
            if node1_change[0] - node2[0] < 0:
                dir = 'd'
            if node1_change[0] - node2[0] > 0:
                dir = 'u'
        if dir in temp:
            list_node.append([node2[1], node2[0], Euclidean(node1_change[1], node1_change[0], node2[1], node2[0])])

    vertexes[str([node1_change[1], node1_change[0]])] = list_node

graph1 = al.Graph(vertexes)
for i in tqdm(outport):
    min = 100000
    shortest_inport = i.copy()
    for j in inport:
        distance = Euclidean(i[0], i[1], j[0], j[1])
        if distance < min:
            min = distance
            shortest_inport = j.copy()
    r2.set(str(i[0]) + "," + str(i[1]), str(shortest_inport[0]) + ',' + str(shortest_inport[1]))


for i in tqdm(outport):
    for j in inport:
        route = graph1.a_star_algorithm(str(i), str(j))
        if route is not None:
            r3.set(str(i[0]) + "," + str(i[1]) + ',' + str(j[0]) + ',' + str(j[1]), str(route))


for i in tqdm(inport):
    for j in outport:
        route = graph1.a_star_algorithm(str(i), str(j))
        if route is not None:
            r.set(str(i[0]) + "," + str(i[1]) + ',' + str(j[0]) + ',' + str(j[1]), str(route))

