import os
import runTSP

input_dir = input("Bitte geben sie das Directory der zu untersuchenden TSP ein:\n")
input_heu = input("Bitte geben sie die zu nutzenden Heuristiken ein, getrennt mit einem Komma[None,NN,NNDS,MST]\n")
input_cut = input("Bitte geben sie die zu nutzenden Cutting Planes ein, getrennt mit einem Komma[frac,int]\n")
input_opt = input("Bitte geben sie die zu nutzenden 2opt Iterationen, getrennt mit einem Komma, ein.\n")


heu_list = input_heu.split(",")
cut_list = input_cut.split(",")
opt_list = input_opt.split(",")

if not os.path.exists("output"):
  os.makedirs("output")
path = "output/%s.%s" % ('output', 'dat')
uniq = 1
while os.path.exists(path):
  path = "output/%s%d.%s" % ('output',  uniq, 'dat')
  uniq += 1

output = open(path,"w")
output.write(", ".join(['TSP-Instanz','Algo','Laufzeit','Knotenzahl',
    'Heuristik','ObjVal','ObjBound','int/frac','Anzahl Opt Iterations','Anzahl durchgeführter Int Cuts', 'Anzahl frac cuts','Anzahl Constraints added',
    'Anzahl gefundener Heuristiklösungen','Anzahl gefundener Lösungen insgesamt', 'Zeit in Cutting', 'Zeit in Heuristik']) + '\n')
output.close()

algoNum = 0

for f in os.listdir(input_dir):
    if not f.endswith(".tsp"):
        continue

    algoNum = 0
    print(44*" " + f"--------   Instanz ist {f}   --------")
    for h in heu_list:
        for o in opt_list:
            for c in cut_list:
                algoNum+=1
                m = runTSP.runTSP(os.path.join(input_dir, f), h, int(o),
                    (True if c == "frac" else False))
                s = "    ".join(map(str,[f, algoNum, m.Runtime, m.NodeCount,
                    m._heuristik, m.ObjVal, m.ObjBound,c ,o , m._int_cut,
                     m._frac_cut, m._number_of_lazy_constraints,m._hrSolCount,m.SolCount,m._cutting_time, m.heuristic_time ])) +'\n'
                with open(path, 'a') as output:
                    output.write(s)
