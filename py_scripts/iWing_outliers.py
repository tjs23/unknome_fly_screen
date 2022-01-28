import sys
import os
import numpy as np


class Wing_outliers():   
    
    def __init__(self):
        self.cwd = os.getcwd()
        self.workdir = '%s\Dropbox\Unknome\Screens\Outliers\RajenAnalysis' %self.cwd
        self.screendir = os.path.join(self.workdir, 'Wing')
        self.pickledir = os.path.join(self.workdir, 'Picklefiles')
        if not os.path.exists(self.pickledir):
            os.makedirs(self.pickledir) 
        return
        
    
    def buildOutliersDict(self):
        import cPickle as pickle
        from collections import OrderedDict
        from datetime import datetime
        #fetch data from file
        filenames = ['Wing_ellipse.csv', 'Wing_means.csv', 'Wing_pvals.csv']
        filepaths = [os.path.join(self.screendir, filename) for filename in filenames]
        ellipse, means, pvals = [np.genfromtxt (filepath, delimiter=",", dtype = None) for filepath in filepaths]
        stocks = means[1:,0]
        #reformat data
        meansA = np.asarray(means[1:,1], dtype = np.float64)
        meansP = np.asarray(means[1:,2], dtype = np.float64)
        areaA = np.asarray(ellipse[1:,1], dtype = np.float64)
        areaP = np.asarray(ellipse[1:,2], dtype = np.float64)
        pvals = np.asarray(pvals[1:,1], dtype = np.float64)
        #build dictionary
        keys = ['stocks', 'meansA', 'meansP', 'ellipseA', 'ellipseP', 'pvals']
        values = [stocks, meansA, meansP, areaA, areaP, pvals]
        outliersDict = OrderedDict(zip(keys, values))
        #Fetch current time and date
        time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        #serialise dictionary
        filename = 'outliersWingDict_%s.pickle' %time
        filepath = os.path.join(self.pickledir, filename)
        with open(filepath, 'w') as f:
            pickle.dump(outliersDict, f)
        return
    
    def loadOutliersDict(self):
        import cPickle as pickle
        filelist = [filename for filename in os.listdir(self.pickledir) if filename.startswith('outliersWing')]
        filelist.sort()
        picklefile = filelist[-1]
        filepath = os.path.join(self.pickledir, picklefile)
        with open(filepath, 'r') as f:
            outliersDict = pickle.load(f)
        return outliersDict
    
    def fetchOutliers(self):
        from File_Functions import listPartition
        #load data object
        outliersDict = self.loadOutliersDict()
        pvals = outliersDict['pvals']
        ptuples = [(i, pval) for i, pval in enumerate(pvals)]
        outliers, nonoutliers = listPartition(lambda x:x[1]<=0.05, ptuples)
        outliers = [(outliersDict['stocks'][i], outliersDict['meansA'][i], outliersDict['meansP'][i]) for (i, pval) in outliers]
        return outliers
    
    
    def outliersPlotter(self):
        from matplotlib import pyplot as plt
        from mpldatacursor import datacursor
        from itertools import chain
        #load data object
        outliersDict = self.loadOutliersDict()
        outliers = self.fetchOutliers()
        #fetch data
        stocks, meansA, meansP, ellipseA, ellipseP, pvals = outliersDict.values()
        outliers = zip(*outliers)
        #fetch controls data
        negctrl = ['Empty', 'w1118', 'GFPi(5)', 'GFPi(9)']
        posctrl = ['Hpo', 'Cho', 'Lnk']
        negctrl = [[(i, stock, meansA[i], meansP[i], pvals[i]) for i, stock in enumerate(stocks) if stock == name] for name in negctrl]; negctrl = list(chain(*negctrl))
        posctrl = [[(i, stock, meansA[i], meansP[i], pvals[i]) for i, stock in enumerate(stocks) if stock == name] for name in posctrl]; posctrl = list(chain(*posctrl))
        negctrl = zip(*negctrl)
        posctrl = zip(*posctrl)
        #set plots    
        plt.close('all')
        ax = plt.subplot(111)
        ax.plot(ellipseA, ellipseP, c = 'b', linestyle = '--', lw = 1.3)#ellipse
        ax.scatter(meansA, meansP, s = 12, c = '#CFD3D4')
        ax.scatter(outliers[1], outliers[2], s = 30, color = 'r', edgecolor = 'black', label = 'outliers')
        ax.scatter(negctrl[2], negctrl[3], c = 'b', s = 30, label = '- control')
        ax.scatter(posctrl[2], posctrl[3], c ='g', s = 30, label = '+ control')
        #set axis labels and legend
        ax.set_xlabel('AreaA (pixel)', fontsize = 14)
        ax.set_ylabel('AreaP (pixel)', fontsize = 14)
        ax.legend()
        #label datapoints interactively
        datacursor(ax.collections[0], hover=True, point_labels = stocks, fontsize = 10, bbox= None, xytext=(0, 25), formatter=lambda **kwargs: kwargs['point_label'][0])
        plt.show()
        return
        
        
#Wing_outliers().outliersPlotter()