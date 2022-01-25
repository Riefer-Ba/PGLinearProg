import math
import numpy as np
import networkx as nx
from gurobipy import GRB
import networkx.algorithms as algo
import itertools
import parse

def callback_hr(m, where):
    if not m._heuristik == 'None':

        if where == GRB.Callback.MIPNODE and m._cutPlaneChange <= 0:
            what = m.cbGet(GRB.Callback.MIPNODE_STATUS)
            if what == GRB.OPTIMAL:
                start = time.time()
                hilfsgraph = nx.complete_graph(m._G.number_of_nodes())
                for (v, w, var) in m._G.edges.data('var'):
                    hilfsgraph[v][w]['weight'] = 1 - m.cbGetNodeRel(var)


                solGraph = heuristik_map[m._heuristik](hilfsgraph)
                solGraph = opt2di(m, solGraph)[1]
                #solGraph = opt2(m, solGraph)[1]
                #solGraph = opt2_crossing(m, solGraph)

                for (v, w, var) in m._G.edges.data('var'):
                    m.cbSetSolution(var, solGraph[v][w]['var'])

                m._cutPlaneChange = int(np.floor(m._PlaneChangeLimit))
                m._PlaneChangeLimit += 0.1
                m._heuristic_time += time.time() - start

		bestObjVal = m.cbGet(GRB.Callback.MIPNODE_OBJBST)

		if solution < bestObjVal:
                m._hrSolCount += 1


def nearestNeighbour(graph):
    graph_copy = graph.copy()
    nx.set_node_attributes(graph_copy, False, "marked")
    nx.set_edge_attributes(graph_copy, 0, "var")

    v = 0

    graph_copy.nodes[v]["marked"] = True

    while any([not graph_copy.nodes[n]["marked"] for n in graph_copy.neighbors(v)]):
        neigh = [n for n in graph_copy.neighbors(v) if not graph_copy.nodes[n]["marked"]]
        nearest = v
        nearest_val = math.inf
        for n in neigh:
            if graph_copy.edges[v, n]["weight"] < nearest_val:
                nearest = n
                nearest_val = graph_copy.edges[v, n]["weight"]

        graph_copy.nodes[nearest]["marked"] = True
        graph_copy[v][nearest]["var"] = 1

        v = nearest
    graph_copy[v][0]["var"] = 1

    return graph_copy


def nearestNeighbourDouble(graph):
    graph_copy = graph.copy()

    nx.set_node_attributes(graph_copy, False, "marked")

    nx.set_edge_attributes(graph_copy, 0, "var")

    v_1 = 0
    v_2 = 0

    graph_copy.nodes[v_1]["marked"] = True

    while any([not graph_copy.nodes[n]["marked"] for n in graph_copy.neighbors(v_1) or n in graph_copy.neighbors(v_2)]):
        neigh_1 = [n for n in graph_copy.neighbors(v_1) if not graph_copy.nodes[n]["marked"]]
        neigh_2 = [n for n in graph_copy.neighbors(v_2) if not graph_copy.nodes[n]["marked"]]
        nearest_1 = v_1
        nearest_val_1 = math.inf
        nearest_2 = v_2
        nearest_val_2 = math.inf
        for n in neigh_1:
            if graph_copy.edges[v_1, n]["weight"] < nearest_val_1:
                nearest_1 = n
                nearest_val_1 = graph_copy[v_1][n]["weight"]

        for n in neigh_2:
            if graph_copy.edges[v_2, n]["weight"] < nearest_val_2:
                nearest_2 = n
                nearest_val_2 = graph_copy[v_2][n]["weight"]

        if nearest_val_1 < nearest_val_2:
            graph_copy.nodes[nearest_1]["marked"] = True
            graph_copy[v_1][nearest_1]["var"] = 1

            v_1 = nearest_1


        else:

            graph_copy.nodes[nearest_2]["marked"] = True
            graph_copy[v_2][nearest_2]["var"] = 1

            v_2 = nearest_2

    if (v_1 > v_2):
        v_1, v_2 = v_2, v_1

    graph_copy[v_1][v_2]["var"] = 1

    return graph_copy


def MST_Heuristic(graph):
    graph_copy = graph.copy()
    nx.set_node_attributes(graph_copy, False, "marked")
    nx.set_edge_attributes(graph_copy, 0, "var")
    T = nx.minimum_spanning_tree(graph_copy)
    unvisited = np.zeros(graph_copy.number_of_nodes())
    last = 0
    for e in nx.dfs_edges(T,source=0):
        if unvisited[e[1]] == 0:
            graph_copy[last][e[1]]["var"] = 1
            last = e[1]
    graph_copy[last][0]["var"] = 1
    return graph_copy


def opt2_crossing(model, solGraph):
    class Point:
        def __init__(self, x, y):
            self.x = x
            self.y = y

    # Code folgender Funktion wurde kopiert von https://www.geeksforgeeks.org/check-if-two-given-line-segments-intersect/
    def doIntersect(p1,q1,p2,q2):
        # The main function that returns true if
        # the line segment 'p1q1' and 'p2q2' intersect.

        # Given three colinear points p, q, r, the function checks if
        # point q lies on line segment 'pr'
        def onSegment(p, q, r):
            if ( (q.x <= max(p.x, r.x)) and (q.x >= min(p.x, r.x)) and
                   (q.y <= max(p.y, r.y)) and (q.y >= min(p.y, r.y))):
                return True
            return False

        def orientation(p, q, r):
            # to find the orientation of an ordered triplet (p,q,r)
            # function returns the following values:
            # 0 : Colinear points
            # 1 : Clockwise points
            # 2 : Counterclockwise

            # See https://www.geeksforgeeks.org/orientation-3-ordered-points/amp/
            # for details of below formula.

            val = (float(q.y - p.y) * (r.x - q.x)) - (float(q.x - p.x) * (r.y - q.y))
            if (val > 0):

                # Clockwise orientation
                return 1
            elif (val < 0):

                # Counterclockwise orientation
                return 2
            else:

                # Colinear orientation
                return 0


        # Find the 4 orientations required for
        # the general and special cases
        o1 = orientation(p1, q1, p2)
        o2 = orientation(p1, q1, q2)
        o3 = orientation(p2, q2, p1)
        o4 = orientation(p2, q2, q1)

        # General case
        if ((o1 != o2) and (o3 != o4)):
            return True

        # Special Cases

        # p1 , q1 and p2 are colinear and p2 lies on segment p1q1
        if ((o1 == 0) and onSegment(p1, p2, q1)):
            return True

        # p1 , q1 and q2 are colinear and q2 lies on segment p1q1
        if ((o2 == 0) and onSegment(p1, q2, q1)):
            return True

        # p2 , q2 and p1 are colinear and p1 lies on segment p2q2
        if ((o3 == 0) and onSegment(p2, p1, q2)):
            return True

        # p2 , q2 and q1 are colinear and q1 lies on segment p2q2
        if ((o4 == 0) and onSegment(p2, q1, q2)):
            return True

        # If none of the cases
        return False


    H = nx.Graph()
    for v,w, var in solGraph.edges.data('var'):
        if solGraph[v][w]['var'] == 1:
            H.add_edge(v,w)

    for i in range(model._2OPT):
        for (a,b), (c,d) in itertools.combinations(H.edges(),2):
            if a == c or a == d or b == c or b ==d:
                continue
            (A,B,C,D) = (Point(model._nodes[x][1],model._nodes[x][2]) for x in (a,b,c,d))
            if doIntersect(A,B,C,D):
                if not (H.has_edge(a,c) or H.has_edge(b,d)):
                    H.remove_edges_from([(a,b),(c,d)])
                    H.add_edges_from([(a,c),(b,d)])
                    if not algo.is_connected(H):
                        H.remove_edges_from([(a,c),(b,d)])
                        H.add_edges_from([(a,d),(b,c)])
                    break
        else:
            print(f"2 OPT terminated after {i} iterations")
            break
    else:
        print("2 OPT ran out of iterations")

    nx.set_edge_attributes(solGraph, 0, "var")

    for v,w in H.edges():
        solGraph[v][w]['var'] = 1

    return solGraph


def opt2di(model, hg):
    #ct = 0
    temp = nx.Graph()                                          # 1. erstellen von NetX graph der die aktuelle Tour darstellt
    temp.add_nodes_from(range(model._G.number_of_nodes()))
    for v,w, var in hg.edges.data('var'):
        if  (hg[v][w]["var"] == 1):
            temp.add_edge(v,w)
            #ct = ct + model._G[v][w]['weight']
    
    temp2 = nx.DiGraph()
    temp2.add_nodes_from(range(model._G.number_of_nodes()))
    temp2.add_edge(v,w)
    t = w
    vor = v
    while (t != v):
        for suc in temp.neighbors(t):
            if( suc != vor):
                temp2.add_edge(t,suc)
                vor = t
                t = suc
                break

    #print("starting opt")
    hasopt = False                                              # 2. 2opt anwenden
    it = int( model._G.number_of_nodes() / model._2OPT )
    for i in range(it):            # nur model._2OPT mal wird verbessert
        exitflag = False                    # bool ob in dieser itteration verbesseert wurde
        for (u, v), (e, f) in itertools.product(temp2.edges(), temp2.edges()):  # durch alle Kanten itterieren
            # falls wir verbessern, andern wir temp2, also wird dann wieder von vorne angefangen 
            if ( (u != e) and (v != e) and ( u!=f )):  # falls kanten disjunkt sind
                c0 = model._G[u][v]['weight'] + model._G[e][f]['weight']    # berechne neue kantenpaar gewichte
                n = model._G[u][e]['weight'] + model._G[v][f]['weight']
                if ( c0 > n ):                      # das erste paar ist kurzer, und beide kanten sind noch nicht in der tour
                    temp2.remove_edge(u, v)         # loschen der alten Kanten
                    temp2.remove_edge(e, f)
                    temp2.add_edge(u, e)            # neue Kanten hinzuf
                    temp2.add_edge(v, f)
                    t = next(temp2.neighbors(v))
                    while( not exitflag ):          # O(E) = O(V)
                        if( t != e ):
                            t2 = next(temp2.neighbors(t))
                        temp2.remove_edge(v, t)     # die richtung der kante aendern 
                        temp2.add_edge(t, v)
                                               # pointer, ist jetzt v, auf den nachfolger setzen
                        if ( t == e ):              # falls wir bei der Kante e angekommen, dann ist der gerichtete kreis wieder hergestellt
                            exitflag = True         # alle bis aus die aeusserste schleife verlassen
                        else:
                            v = t
                            t= t2
            if exitflag: break                      # falls exitflag gesetzt ist verlasse die Kanten loop
        if exitflag: hasopt = True                  # falls keine exitflag gesetzt ist, dh keine verbesserung, verlasse Funktion 
        else: break                                 # wenn wir uns verbessert haben ,speichere das in hasopt

    if hasopt:                               #3. erstellen von vollst. netX gr. fur set solution
        #cct = 0                                                # solution counter
        ctour = nx.complete_graph(model._G.number_of_nodes())   # erstelle Kompleten graphen
        nx.set_edge_attributes(ctour, 0, "var")                 # setzte all var zu 0
        for (v, w, var) in model._G.edges.data('var'):
            if (temp2.has_edge(v, w) or temp2.has_edge(w, v)):  # falls die kante existiert
                ctour[v][w]["var"] = 1                          # set the solution
                #cct = cct + model._G[v][w]['weight']           # hinzufug zur tour cost
        return [ hasopt, ctour, i]
    else: return [ hasopt, hg, 0]

def opt2(model, hg):
    ct = 0
    temp2 = nx.Graph()                                          # 1. erstellen von NetX graph der die aktuelle Tour darstellt
    temp2.add_nodes_from(range(model._G.number_of_nodes()))
    for v,w, var in hg.edges.data('var'):
        if  (hg[v][w]["var"] == 1):
            temp2.add_edge(v,w)
            ct = ct + model._G[v][w]['weight']

    hasopt = False                                              # 2. 2opt anwenden
    for i in range(model._2OPT):            # nur model._2OPT mal wird verbessert
        exitflag = False                    # bool ob in dieser itteration verbesseert wurde
        for (u, v), (e, f) in itertools.product(temp2.edges(), temp2.edges()):  # durch alle Kanten itterieren
            # falls wir verbessern, andern wir temp2, also wird cann wieder von vorne angefangen
            if ( (u != e) and (v != f) and (v != e) and ( u!=f )):  # falls kanten disjunkt sind
                c0 = model._G[u][v]['weight'] + model._G[e][f]['weight']    # berechne neue kantenpaar gewichte
                n1 = model._G[u][f]['weight'] + model._G[v][e]['weight']
                n2 = model._G[u][e]['weight'] + model._G[v][f]['weight']
                if ( c0 > n1 ) and ( not temp2.has_edge(u, f) ) and ( not temp2.has_edge(v, e) ):    # das erste paar ist kurzer, und beide kanten sind noch nicht in der tour
                    temp2.remove_edge(u, v)      # loschen alte kanten
                    temp2.remove_edge(e, f)
                    temp2.add_edge(u, f)  # neue kanten hinzuf
                    temp2.add_edge(v, e)
                    exitflag =  algo.is_connected(temp2)    # ob die verbesserung valide ist
                    if not exitflag:
                        temp2.remove_edge(u, f)      # losche die  gerade hinzugefügte Kanten
                        temp2.remove_edge(v, e)
                        temp2.add_edge(e, f)   #alte kanten wieder hinzufugen
                        temp2.add_edge(u, v)
                if ( c0 > n2 ) and (not exitflag)  and ( not temp2.has_edge(u, e) ) and ( not temp2.has_edge(v, f) ):   # das zweite paar ist kurzer, und beide kanten sind noch nicht in der tour
                    temp2.remove_edge(u, v)      # loschen alte kanten
                    temp2.remove_edge(e, f)
                    temp2.add_edge(u, e) # neue kanten hinzuf
                    temp2.add_edge(v, f)
                    exitflag = algo.is_connected(temp2)    # ob die verbesserung valide ist
                    if not exitflag:
                        temp2.remove_edge(v, f)      # losche die  gerade hinzugefügte Kanten
                        temp2.remove_edge(u, e)
                        temp2.add_edge(e, f)  #alte kanten wieder hinzufugen
                        temp2.add_edge(u, v)
            if exitflag: break          # falls braek flag verlasse die kanten loop
        if not exitflag: break          # falls keine breakflag, dh keine verbesserung, verlasse Funktion
        else: hasopt = True     # wenn wir uns verbessert haben ,speichere das in hasopt

    if hasopt:                               #3. erstellen von vollst. netX gr. fur set solution
        cct = 0     # solution counter
        ctour = nx.complete_graph(model._G.number_of_nodes())   # erstelle Kompleten graphen
        nx.set_edge_attributes(ctour, 0, "var")     # set all var to 0
        for (v, w, var) in model._G.edges.data('var'):
            if temp2.has_edge(v, w):        # falls die kante existiert
                ctour[v][w]["var"] = 1      # set the solution
                cct = cct + model._G[v][w]['weight']        # hinzufug zur tour cost
        return [ hasopt, ctour, i]
    else: return [ hasopt, hg, 0]

heuristik_map = {
    "NN": nearestNeighbour,
    "NNDS": nearestNeighbourDouble,
    "MST": MST_Heuristic
}
