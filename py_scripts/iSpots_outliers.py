import sys
import os
import numpy as np


class iSpots_outliers():
    
    def __init__(self):
        self.cwd = os.getcwd()
        self.workdir = '%s\Dropbox\Unknome\Screens\Outliers\RajenAnalysis' %self.cwd
        self.screendir = os.path.join(self.workdir, 'iSpots')
        self.pickledir = os.path.join(self.workdir, 'Picklefiles')
        if not os.path.exists(self.pickledir):
            os.makedirs(self.pickledir)
        return
    
    def buildSpotsOutliersDict(self):
        import cPickle as pickle
        from collections import OrderedDict
        from datetime import datetime
        #fetch data from file
        filenames = ['Spots_ellipse.csv', 'Spots_means.csv', 'Spots_pvals.csv']
        filepaths = [os.path.join(self.screendir, filename) for filename in filenames]
        ellipse, means, pvals = [np.genfromtxt (filepath, delimiter=",", dtype = None) for filepath in filepaths]
        stocks = means[1:,0]; stocks = [stock[1:-1] for stock in stocks]
        #reformat data
        L50 = np.asarray(means[1:,1], dtype = np.float64)
        G50 = np.asarray(means[1:,2], dtype = np.float64)
        elpL50 = np.asarray(ellipse[1:,1], dtype = np.float64)
        elpG50 = np.asarray(ellipse[1:,2], dtype = np.float64)
        pvals = np.asarray(pvals[1:,1], dtype = np.float64)
        #build dictionary
        keys = ['stocks', 'L50', 'G50', 'elpL50', 'elpG50', 'pvals']
        values = [stocks, L50, G50, elpL50, elpG50, pvals]
        outliersDict = OrderedDict(zip(keys, values))
        #Fetch current time and date
        time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        #serialise dictionary
        filename = 'iSpotsDataDict_%s.pickle' %time
        picklepath = os.path.join(self.pickledir, filename)
        with open(picklepath, 'w') as f:
            pickle.dump(outliersDict, f)
        return
    
    def loadSpotsOutliersDict(self):
        import cPickle as pickle
        filelist = [filename for filename in os.listdir(self.pickledir) if filename.startswith('iSpots')]
        filelist.sort()
        picklefile = filelist[-1]
        filepath = os.path.join(self.pickledir, picklefile)
        with open(filepath, 'r') as f:
            rajenDict = pickle.load(f)
        return rajenDict
    
    def fetchScreenOutliers(self):
        from File_Functions import listPartition
        #load data object
        outliersDict = self.loadSpotsOutliersDict()
        pvals = outliersDict['pvals']
        ptuples = [(i, pval) for i, pval in enumerate(pvals)]
        outliers, nonoutliers = listPartition(lambda x:x[1]<=0.05, ptuples)
        screenOutliers = [(outliersDict['stocks'][i], outliersDict['L50'][i], outliersDict['G50'][i]) for (i, pval) in outliers]
        return screenOutliers   
        
    def fetchUnknomeOutliers(self):
        #load data object
        outliers = self.fetchScreenOutliers()
        unknomeOutliers = [stock[0] for stock in outliers if stock[0].startswith('JS')]
        return unknomeOutliers
        
 
    def outliersPlotter(self, controls = 'dataset'):
        import matplotlib.pyplot as plt
        from mpldatacursor import datacursor
        from itertools import chain
        from Plot_Functions import hsvGenerator
        from colorsys import hsv_to_rgb
        from matplotlib.colors import colorConverter
        from File_Functions import listPartition
        from iSpots_Functions import Dashboard
        #load data object
        outliersDict = self.loadSpotsOutliersDict()
        outliers = self.fetchScreenOutliers()
        #fetch data
        stocks, L50, G50, elpL50, elpG50, pvals = outliersDict.values()
        outliers = zip(*outliers)
        #Controls IDs
        negctrl = ['Empty', 'JS125']
        posctrl = ['Hsp70']
        enhancers = ['CG3991', 'CG2922'] 
        otherctrl = Dashboard().usedcontrols
        valRNAiDict = Dashboard().validationRNAis()
        validationRNAi = valRNAiDict.items(); validationRNAi_flat = [[] for i in validationRNAi] 
        [[validationRNAi_flat[i].extend(item) if isinstance(item, (list, tuple)) else validationRNAi_flat[i].append(item) for item in tupl] for i, tupl in enumerate(validationRNAi)]
        #fetch controls data
        negctrl = [[(i, stock, L50[i], G50[i], pvals[i]) for i, stock in enumerate(stocks) if stock == name] for name in negctrl]; negctrl = list(chain(*negctrl))
        posctrl = [[(i, stock, L50[i], G50[i], pvals[i]) for i, stock in enumerate(stocks) if stock == name] for name in posctrl]; posctrl = list(chain(*posctrl))
        otherctrl = [[(i, stock, L50[i], G50[i], pvals[i]) for i, stock in enumerate(stocks) if stock == name] for name in otherctrl]; otherctrl = list(chain(*otherctrl))
        otherctrl = listPartition(lambda x: x[1] in enhancers, otherctrl)
        validationRNAi_flat = [[[(i, stock, L50[i], G50[i], pvals[i]) for i, stock in enumerate(stocks) if stock == name] for name in lst] for lst in validationRNAi_flat]
        validationRNAi_flat = [list(chain(*sublist)) for sublist in validationRNAi_flat]
        #reformat arrays
        negctrl = zip(*negctrl)
        posctrl = zip(*posctrl)
        enhancers, nomodifiers = [zip(*sublist) for sublist in otherctrl]
        validationRNAi_flat = [zip(*sublist) for sublist in validationRNAi_flat]
        #set plots    
        plt.close('all')
        ax = plt.subplot(111)
        ax.plot(elpL50, elpG50, c = 'b', linestyle = '--', lw = 1.3)#ellipse
        ax.scatter(L50, G50, s = 12, c = '#CFD3D4')
        if controls in ['dataset', 'other']:
            ax.scatter(outliers[1], outliers[2], s = 30, color = 'r', edgecolor = 'black', label = 'outliers')
            if controls == 'other':
                ax.scatter(nomodifiers[2], nomodifiers[3], c = 'b', s = 30, label = 'no-modifier')
                ax.scatter(enhancers[2], enhancers[3], c = 'g', s = 30, label = 'enhancer')
            elif controls == 'dataset':
                ax.scatter(negctrl[2], negctrl[3], c = 'b', s = 30, label = '- control')
                ax.scatter(posctrl[2], posctrl[3], c ='g', s = 30, label = '+ control')
        elif controls == 'validation':
            #Generate colorMaps
            cc = lambda arg: colorConverter.to_rgba(arg, alpha = 1.0)
            step = 1/float(len(validationRNAi_flat))
            hsvColorMap = hsvGenerator(step, 0.8, 0.8)
            rgbaColorMap = [cc(hsv_to_rgb(h,s,v)) for h,s,v in hsvColorMap]
            for i, ctrlset in enumerate(validationRNAi_flat):
                #if ctrlset[1][0] in self.fetchOutliers():
                ax.scatter(ctrlset[2], ctrlset[3], color = rgbaColorMap[i], s = 50, edgecolor = 'black', label = ctrlset[1][0])
        #set axis labels and legend
        ax.set_xlabel('L50', fontsize = 14)
        ax.set_ylabel('G50', fontsize = 14)
        ax.legend()
        #label datapoints interactively
        datacursor(ax.collections[0], hover=True, point_labels = stocks, fontsize = 10, bbox= None, xytext=(0, 25), formatter=lambda **kwargs: kwargs['point_label'][0])
        plt.show()
        return 

#iSpots_outliers().outliersPlotter()