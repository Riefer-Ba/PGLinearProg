import parse
import cutting_plane
import heuristik
import gnuplot
# Verwendung des Skripts: python runTSP.py [filename]
# filename ist optional

# m ist das Model von Gurobi, G der Graph aus networkx
def callback(m, where):
    cutting_plane.fractional_cut(m,where)
    heuristik.callback_hr(m,where)

def runTSP(source,heuristik,opt,fractional, gml=False):
    m,G = parse.read_tsp(source,heuristik,opt,fractional)

    m.params.LazyConstraints = 1
    m.params.heuristics = 0
    m.params.cuts = 0
    m.params.SEED = 0
    m.params.TimeLimit = 1800	# 30 min
    m.params.THREADS = 1

    m.params.PoolSolutions = 100000  # damit solCount über 10 geht

    # Parameter zum Messen
    m._int_cut = 0
    m._frac_cut = 0
    m._number_of_lazy_constraints = 0
    m._heuristic_time = 0
    m._cutting_time = 0
    m.optimize(callback)

    if gml:
        parse.create_gml(G)

    return m
