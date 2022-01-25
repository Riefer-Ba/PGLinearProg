from gurobipy import GRB
import networkx as nx
import networkx.algorithms as algo
import time

def fractional_cut(m, where):
    # m._G should contain the original graph
    if where == GRB.Callback.MIPSOL:
        start = time.time()
        m._int_cut += 1
        H = nx.Graph()
        H.add_nodes_from(range(m._G.number_of_nodes()))
        for (v,w, var) in m._G.edges.data('var'):
            if m.cbGetSolution(var) > 1e-5:
                H.add_edge(v,w,weight=m.cbGetSolution(var))
        if not algo.is_connected(H):
            add_connected_constraint(H,m)
            m._number_of_lazy_constraints += 1
        m._cutting_time += time.time() - start

    if where == GRB.Callback.MIPNODE and m._fractional_separation:
        what = m.cbGet(GRB.Callback.MIPNODE_STATUS)
        if what == GRB.OPTIMAL:
            start = time.time()
            m._frac_cut += 1
            H = nx.Graph()
            H.add_nodes_from(range(m._G.number_of_nodes()))
            for (v,w, var) in m._G.edges.data('var'):
                # Ist die Variable wirklich nichtnegativ?
                if m.cbGetNodeRel(var) > 1e-5:
                    H.add_edge(v,w,weight=m.cbGetNodeRel(var))

            if not algo.is_connected(H):
                add_connected_constraint(H,m)
                m._number_of_lazy_constraints += 1
            else:
                cut_value, (cut, comp_cut) = nx.algorithms.connectivity.stoerwagner.stoer_wagner(H)
                # Schneller ohne Abfrage?
                if cut_value < 2 + 1e-5:
                    expr = 0
                    for v in cut:
                        for w in comp_cut:
                            expr += m._G[v][w]['var']
                    m.cbLazy(expr >= 2)
                    m._cutPlaneChange -= 1
                    m._number_of_lazy_constraints += 1
            m._cutting_time += time.time() - start

def add_connected_constraint(H, m):
    for cut in nx.algorithms.components.connected_components(H):
        comp_cut = {i for i in range(m._G.number_of_nodes())} - cut

        expr = 0
        for v in cut:
            for w in comp_cut:
                expr += m._G[v][w]['var']
        m.cbLazy(expr >= 2)
        m._cutPlaneChange -= 1
