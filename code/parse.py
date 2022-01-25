import networkx as nx
import math, sys
import gurobipy as gp
from gurobipy import GRB
import argparse

def read_tsp(source,heuristik,opt,fractional):

    nodes = []
    with open(source,'r') as f:
        for line in f:
            if line.startswith('DIMENSION'):
                n = int(line.split()[-1])
            if line.startswith("NODE_COORD_SECTION"):
                break
        for line in f:
            if line.startswith("EOF"):
                break
            nodes.append(line.split())

    nodes = sorted([(int(x),float(y),float(z)) for (x,y,z) in nodes], key=lambda x:x[0])
    if(nodes[0][0] <= 0 or nodes[-1][0] > n):
        print(f"Something is wrong with the dimension")
        raise ValueError

    m = gp.Model("tsp")
    m._nodes = nodes
    G = nx.Graph()

    for (x,y,z) in nodes:
        G.add_node(x-1,graphics = { 'x' : y*100, 'y' : z*100})

    def distance(node_1,node_2):
        return int(((node_1[1]-node_2[1])**2 + (node_1[2]-node_2[2])**2)**0.5 + 0.5)

    for i in range(n):
        for j in range(i+1,n):
            var = m.addVar(obj=distance(nodes[i],nodes[j]), vtype=GRB.BINARY, name=f'({i}, {j})')
            G.add_edge(i,j,weight=distance(nodes[i],nodes[j]), var=var)

    for v in G.nodes():
        expr = 0
        for neighbor in G.adj[v]:
            expr += G[v][neighbor]['var']
        m.addConstr(expr == 2)

    m._G = G

    # m._2OPT = args.opt
    # m._heuristik = args.heuristik
    # m._fractional_separation = args.fractional_separation
    m._2OPT = opt
    m._heuristik = heuristik
    m._fractional_separation = fractional

    m._PlaneChangeLimit = 3
    m._cutPlaneChange = m._PlaneChangeLimit

    m._hrSolCount = 0

    m.setParam("LazyConstraints", 1)

    return (m,G)

def calc_opt(G, file):
    tour = []
    with open(file,'r') as f:
        for line in f:
            if line.startswith('TOUR_SECTION'):
                break
        for line in f:
            if line.startswith("-1"):
                break
            tour.append(int(line))
    cost = 0
    last_node = tour[-1]
    for node in tour:
        cost += G[node-1][last_node-1]['weight']
        last_node = node
    print(f"Die optimale Tour kostet {cost}")

def create_gml_colored_edges(G,file="graph.gml"):
    for u,v in G.edges():
        G[u][v]['graphics'] = { 'fill' : "#cccccc", 'label' : G[u][v]['weight'] }
        if  G[u][v]['var'].getAttr('x') == 1:
            G[u][v]['graphics']['fill'] = '#aa0000'

    def printer(x):
        if type(x) is str:
            return x
        return x.getAttr("VarName")

    nx.write_gml(G, file, printer)

def create_gml(G,file="graph.gml"):
    H = nx.classes.function.create_empty_copy(G)
    for u,v in G.edges():
        if  G[u][v]['var'].getAttr('x') > 1e-5:
            H.add_edge(u,v)
    nx.write_gml(H, file)

def create_gml_solGraph(solGraph,file='solGraph.gml'):
    H = nx.classes.function.create_empty_copy(solGraph)
    for u,v in solGraph.edges():
        if  solGraph[u][v]['var'] > 1e-5:
            H.add_edge(u,v)
    nx.write_gml(H, file)
