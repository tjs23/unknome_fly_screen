import sys
import os
import numpy as np
from Fertility_Functions import FertilityDB, Dashboard, FertilityMetrics



class Fertility_outliers():   
    
    def __init__(self):
        self.cwd = os.getcwd()
        self.workdir = '/data/unknome/unknome_joao/Joao/Screens/Outliers/RajenAnalysis' # '%s\Dropbox\Unknome\Screens\Outliers\RajenAnalysis' %self.cwd
        self.screendir = os.path.join(self.workdir, 'Fertility')
        self.pickledir = os.path.join(self.workdir, 'Picklefiles')
        if not os.path.exists(self.pickledir):
            os.makedirs(self.pickledir) 
        return
    
    def getMembers(self):
        import inspect
        methods = inspect.getmembers(self, predicate = inspect.ismethod)
        print(methods)
        return
    
    def buildOutliersDict(self):
        import cPickle as pickle
        from collections import OrderedDict
        from datetime import datetime
        #fetch data from file
        filenames = ['Fertility2_meansF.csv', 'Fertility2_meansM.csv', 'Fertility2_pvalsF.csv', 'Fertility2_pvalsM.csv', 'Fertility2_boundaryF.csv', 'Fertility2_boundaryM.csv']
        filepaths = [os.path.join(self.screendir, filename) for filename in filenames]
        data = [np.genfromtxt (filepath, delimiter=",", dtype = None) for filepath in filepaths]
        stocksF, stocksM = [data[0][1:,0], data[1][1:,0]]
        #reformat data
        meansF, meansM, pvalsF, pvalsM, boundaryF, boundaryM = [np.asarray(arr[1:,1], dtype = np.float64) for arr in data]
        #build dictionary
        keys = ['stocksF', 'stocksM', 'meansF', 'meansM', 'pvalsF', 'pvalsM', 'boundF', 'boundM']
        values = [stocksF, stocksM, meansF, meansM, pvalsF, pvalsM, boundaryF, boundaryM]
        outliersDict = OrderedDict(zip(keys, values))
        #Fetch current time and date
        time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        #serialise dictionary
        filename = 'outliersFertilityDict_%s.pickle' %time
        picklepath = os.path.join(self.pickledir, filename)
        with open(picklepath, 'w') as f:
            pickle.dump(outliersDict, f)
        return
        
    def loadOutliersDict(self):
        import cPickle as pickle
        #sys.path.insert(0, '/usr/lib/python2.7/')
        from collections import OrderedDict
        
        filelist = [filename for filename in os.listdir(self.pickledir) if filename.startswith('outliersFertility')]
        filelist.sort()
        picklefile = filelist[-1]
        filepath = os.path.join(self.pickledir, picklefile)
         
        with open(filepath, 'r') as f:
            outliersDict = pickle.load(f)
            
        return outliersDict
    
    def intersectDatasets(self):
        outliersDict = self.loadOutliersDict()
        stocksFM = [stock for stock in outliersDict['stocksF'] if stock in outliersDict['stocksM']]
        arrF = zip(outliersDict['stocksF'], outliersDict['meansF'], outliersDict['pvalsF'])
        arrM = zip(outliersDict['stocksM'], outliersDict['meansM'], outliersDict['pvalsM'])
        arrs = [arrF, arrM]
        arrFM = [[tupl for tupl in arr if tupl[0] in stocksFM] for arr in arrs]
        for arr in arrFM:
            arr.sort(key = lambda x: stocksFM.index(x[0]))
        arrFM = [(a, b, arrFM[1][i][1], c, arrFM[1][i][2]) for i, (a,b,c) in enumerate(arrFM[0])] 
        return arrFM
    
    def fetchOutliers(self):
        from File_Functions import listPartition
        #load data object
        outliersDict = self.loadOutliersDict()
        pvals = pvalsF, pvalsM = [outliersDict['pvalsF'], outliersDict['pvalsM']]
        ptuples = [[(i, pval) for i, pval in enumerate(arr)] for arr in pvals]
        ptuplesF, ptuplesM = [listPartition(lambda x:x[1]<=0.05, arr) for arr in ptuples]
        outliersF = [(outliersDict['stocksF'][i], outliersDict['meansF'][i], pval) for (i, pval) in ptuplesF[0]]
        outliersM = [(outliersDict['stocksM'][i], outliersDict['meansM'][i], pval) for (i, pval) in ptuplesM[0]]
        outliers = [outliersF, outliersM]
        return outliers
    
    def fetchPlotGroups(self):
        from File_Functions import listPartition
        from itertools import chain
        #load data object
        outliersDict = self.loadOutliersDict()
        outliers = self.fetchOutliers()
        arrFM = self.intersectDatasets(); arrFM = zip(*arrFM)
        #unpack data
        stocksF, stocksM, meansF, meansM, pvalsF, pvalsM, boundaryF, boundaryM = outliersDict.values()
        stocksFM, imeansF, imeansM, ipvalsF, ipvalsM = arrFM
        #set plot groups membership
        outliers = [zip(*sublist) for sublist in outliers];  outliers = [sublist[0] for sublist in outliers]; outliersF, outliersM = outliers
        ctrlnames = FertilityDB().ctrlnames
        
        
        
        posctrl, negctrl = listPartition(lambda x:x.startswith('M') or x.startswith('F'), ctrlnames)
        posctrlF, posctrlM = listPartition(lambda x:x.startswith('F'), posctrl)
        #fetch outliers and negctrl data
        plotgroup1 = [outliersF, outliersM, negctrl];  
        data1 = [[[(imeansF[i], imeansM[i], name) for i, stock in enumerate(stocksFM) if stock == name] for name in group] for group in plotgroup1]
        data1 = [zip(*list(chain(*plotgroup))) for plotgroup in data1]
        #fetch positive controls data
        plotgroup2 = [posctrlF, posctrlM]
        data2 = [[(meansF[list(stocksF).index(name)], meansM[list(stocksM).index(name)]) for name in group] for i, group in enumerate(plotgroup2)]
        data2 = [zip(*plotgroup) for plotgroup in data2]
        #fetch validation controls data
        valRNAiDict = Dashboard().validationRNAis()
        validationRNAi = valRNAiDict.items(); validationRNAi = list(chain(*validationRNAi)); valRNAi = []
        [valRNAi.extend(item) if isinstance(item, (list, tuple)) else valRNAi.append(item) for item in validationRNAi]
        valRNAi = [(meansF[list(stocksF).index(name)], meansM[list(stocksM).index(name)]) if name in stocksF else (0, meansM[list(stocksM).index(name)]) for name in valRNAi] 
        valRNAi = zip(*valRNAi)
        #pack data
        data = data1 + data2 + [valRNAi]#outliersF, outliersM, negctrl, posctrlF, posctrlM, valRNAi = data
        return data
    
    def outliersLayout(self):
        import matplotlib.pyplot as plt
        from mpldatacursor import datacursor
        #load data object
        outliersDict = self.loadOutliersDict()
        stocksF, stocksM, meansF, meansM, pvalsF, pvalsM, boundaryF, boundaryM = outliersDict.values()
        arrFM = self.intersectDatasets(); arrFM = zip(*arrFM)
        stocksFM, imeansF, imeansM, ipvalsF, ipvalsM = arrFM
        #set plots    
        ax = plt.subplot(111)
        ax.scatter(arrFM[1], arrFM[2], s = 12, c = '#CFD3D4')
        #boundaries
        ax.plot((boundaryF[0], boundaryF[0]), (boundaryM[0]-5,boundaryM[1]+5), color = 'g', linestyle = '--', alpha = 0.5)
        ax.plot((boundaryF[1], boundaryF[1]), (boundaryM[0]-5,boundaryM[1]+5), color = 'g', linestyle = '--', alpha = 0.5)
        ax.plot((boundaryF[0]-5, boundaryF[1]+5), (boundaryM[0],boundaryM[0]), color = 'b', linestyle = '--', alpha = 0.5)
        ax.plot((boundaryF[0]-5, boundaryF[1]+5), (boundaryM[1],boundaryM[1]), color = 'b', linestyle = '--', alpha = 0.5)
        #set axis labels and legend
        ax.set_xlabel('Female fertility: brood size', fontsize = 14)
        ax.set_ylabel('Male fertility: brood size', fontsize = 14)
        ax.set_xlim([-5, 140])
        ax.set_ylim([-5, 120])
        #label datapoints interactively
        #datacursor(ax.collections[0], hover=True, point_labels = arrFM[0], fontsize = 10, bbox= None, xytext=(0, 25), formatter=lambda **kwargs: kwargs['point_label'][0])
         
        return ax
        
    
    def outliersPlotter(self, controls = 'dataset'):
        import matplotlib.pyplot as plt
        from collections import defaultdict
        #fetch data objects
        
        cg_map = {}
        with open('CG_mapping.txt') as file_obj:
          for line in file_obj:
            js, cg = line.split()
            cg_map[js] = cg
        
        stock_meansF = defaultdict(list)
        stock_meansM = defaultdict(list)
                
        fm_dict =  FertilityMetrics().loadFertilityMetrics()
        
        for fm in fm_dict:
          if fm == 'females':
            smd = stock_meansF
          else:
            smd = stock_meansM
        
          for batch in fm_dict[fm]:
            for stock in fm_dict[fm][batch]:
              m, sem, p, z = fm_dict[fm][batch][stock]
              
              smd[stock].append(sem)

        stock_metricsF = {stock:np.mean(stock_meansF[stock]) for stock in stock_meansF}
        stock_metricsM = {stock:np.mean(stock_meansM[stock]) for stock in stock_meansM}
  
        plt.close('all')
        ax = self.outliersLayout()
        data = self.fetchPlotGroups()
        outliersF, outliersM, negctrl, posctrlF, posctrlM, valRNAi= data
        #set plots    
        if controls in ['dataset', 'posctrl']:
            
            stocks = outliersF[2]
            x = [stock_metricsF[s] for s in stocks]
            y = [stock_metricsM[s] for s in stocks]        
            #ax.errorbar(outliersF[0], outliersF[1],  x, y, fmt='none', ecolor='#B5EB10', zorder=1)
            ax.scatter(outliersF[0], outliersF[1], s = 50, color = '#B5EB10', edgecolor = 'black', label = 'outliersF', zorder=2)

            stocks = outliersM[2]
            x = [stock_metricsF[s] for s in stocks]
            y = [stock_metricsM[s] for s in stocks]        
            #ax.errorbar(outliersM[0], outliersM[1],  x, y, fmt='none', ecolor='#F582EB', zorder=1)
            ax.scatter(outliersM[0], outliersM[1], s = 50, color = '#F582EB', edgecolor = 'black', label = 'outliersM', zorder=2)
            
            # label static
            for i, text in enumerate(outliersM[2]):
              ax.annotate(cg_map[text], (outliersM[0][i], outliersM[1][i]), xytext=(5, 5), textcoords="offset points")
            for i, text in enumerate(outliersF[2]):
              ax.annotate(cg_map[text], (outliersF[0][i], outliersF[1][i]), xytext=(5, 5), textcoords="offset points")
              
            stocks = negctrl[2]
            x = [stock_metricsF[s] for s in stocks]
            y = [stock_metricsM[s] for s in stocks]
            #ax.errorbar(negctrl[0], negctrl[1],  x, y, fmt='none', ecolor='b', zorder=1)
            
            ax.scatter(negctrl[0], negctrl[1], c = 'b', s = 30, label = '- control')
            
            if controls == 'posctrl':
                ax.scatter(posctrlM[0], posctrlM[1], c = 'r', s = 30, label = '+ controlM', zorder=2)
                ax.scatter(posctrlF[0], posctrlF[1], c = 'g', s = 30, label = '+ controlF', zorder=2)
                
                
        elif controls == 'valRNAi':
            ax.scatter(valRNAi[0][0], valRNAi[1][0], c = '#F582EB', s = 50, label = self.validationRNAis().keys()[0])
            ax.scatter(valRNAi[0][1:], valRNAi[1][1:], c = 'r', s = 30, label = 'validation RNAi')
        
        #ax.scatter(x, y, s=20, color='k', zorder=3, marker='+')
        
        #for i, text in enumerate(stocks):
        #      ax.annotate(text, (x[i], y[i]), xytext=(5, 5), textcoords="offset points")
        
        ax.legend()
        plt.show()
        return

 
#Fertility_outliers().buildOutliersDict()  
#Fertility_outliers().fetchOutliers() 
Fertility_outliers().outliersPlotter()

        
    
    
