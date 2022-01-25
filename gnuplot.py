

def plotResult(model,name = "output.dat"):
    f = open("output/"+name,"w")
    f.write("Algo    Laufzeit    Knotenzahl    Heuristik\n")
    f.close()
    f = open("output/"+name,"a")
    f.write("1    "+str(model.Runtime)+"    "+str(model.NodeCount)+"    "+model._heuristik+"\n")
    f.close()




