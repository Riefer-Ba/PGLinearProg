import math, sys
import argparse
import runTSP

parser = argparse.ArgumentParser(description='Solve a TSP instance with gurobi LP Solver')
parser.add_argument("file", help='Only *.tsp file are accepted as input')
parser.add_argument('-heuristik',default="None", choices=['None','NN','NNDS','MST'])
parser.add_argument('-opt',default=0,type=int, help='An integer determining the maximum number of 2 OPT iterations. Default=0')
parser.add_argument('-fractional_separation', default=False, action='store_true',help="If provided, MIPNODEs will be processed with Stör Wagner.")
args = parser.parse_args()

runTSP.runTSP(args.file,args.heuristik,args.opt,args.fractional_separation, gml=True)
