import os
import sys
import numpy as np

class iFly_outliers():
    
    def __init__(self):
        self.cwd = os.getcwd()
        self.workdir = '%s\Dropbox\Unknome\Screens\Outliers\RajenAnalysis' %self.cwd
        self.screendir = os.path.join(self.workdir, 'iFly')
        self.pickledir = os.path.join(self.workdir, 'Picklefiles')
        if not os.path.exists(self.pickledir):
            os.makedirs(self.pickledir)
        self.metricnames = ['velocities', 'angle',  'angleInt', 'dist2e']
        self.ftypes = ['means', 'pvals', 'ellipse']
        self.controls = {'ctrl+':['Pink', 'Hand', 'Flightin', 'Tinman'], 'ctrl-': ['w1118', 'Empty', 'Dicer-', 'GFPi', 'GFPi(9)']}
        return


    def buildRajenDict(self):
        import cPickle as pickle
        from itertools import product
        from collections import OrderedDict
        from datetime import datetime
        #declare nested dictionary object
        keys = ['data', 'boundary']
        outliersDict = {key: {metricname: {} for metricname in self.metricnames} for key in keys}
        #fetch data from files
        for metricname in self.metricnames:
            fnames = ['iFly_var_%s_%s.csv' %(metricname, ftype) for (metricname, ftype) in product([metricname], self.ftypes)]
            filepaths = [os.path.join(self.screendir, fname) for fname in fnames]
            means, pvals, ellipse = [np.genfromtxt (filepath, delimiter=",", dtype = None) for filepath in filepaths]
            #reformat data
            metric = np.asarray(means[1:,1:], dtype = np.float64)
            pvals = np.asarray(pvals[1:,1], dtype = np.float64)
            boundary = np.asarray(ellipse[1:,1:], dtype = np.float64)
            #fetch stocks
            stocks = means[1:,0]; stocks = [stock[1:-1] if stock[0] == '"' else stock for stock in stocks]
            #build dictionary
            values = zip(*[metric, pvals])
            metricDict = OrderedDict(zip(stocks, values))
            outliersDict['data'][metricname] = metricDict
            outliersDict['boundary'][metricname] = boundary
        #Fetch current time and date
        time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        #serialise dictionary
        filename = 'rajen_iFlyDict_%s.pickle' %time
        picklepath = os.path.join(self.pickledir, filename)
        with open(picklepath, 'wb') as f:
            pickle.dump(outliersDict, f, protocol = 2)
        return
            
    def loadRajenDict(self):
        import cPickle as pickle
        filelist = [filename for filename in os.listdir(self.pickledir) if filename.startswith('rajen_iFly')]
        filelist.sort()
        picklefile = filelist[-1]
        filepath = os.path.join(self.pickledir, picklefile)
        with open(filepath, 'rb') as f:
            rajenDict = pickle.load(f)
        return rajenDict
    
    def buildOutliersDict(self):
        from datetime import datetime
        import cPickle as pickle
        #load data object
        rajenDict = self.loadRajenDict()
        #build empty dictionary container
        outliers = {metricname: {} for metricname in self.metricnames}
        #fetch outliers
        for metricname in self.metricnames:
            metricdict = rajenDict['data'][metricname]
            data = metricdict.values()
            metric_outliers = [metricdict.keys()[i] for i, tupl in enumerate(data) if tupl[1]<=0.05]
            outliers[metricname] = metric_outliers                  
        #Fetch current time and date
        time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        #serialise dictionary
        picklepath = os.path.join(self.pickledir, 'outliers_iFlyDict_%s.pickle' %time)
        with open(picklepath, 'wb') as f:
            pickle.dump(outliers, f, protocol = 2)  
        return
        
    
    def loadOutliersDict(self):
        import cPickle as pickle
        filelist = [filename for filename in os.listdir(self.pickledir) if filename.startswith('outliers_iFly')]
        filelist.sort()
        picklefile = filelist[-1]
        filepath = os.path.join(self.pickledir, picklefile)
        with open(filepath, 'rb') as f:
            outliers = pickle.load(f)
        return outliers
        
    
    def fetchOutliers(self, delimiter = 'all'):
        #load data
        outliersDict = self.loadOutliersDict()
        #load all outliers
        outliers = []  
        if delimiter == 'all':
            for metricname in self.metricnames:
                metricOutliers = outliersDict[metricname]
                outliers.append((metricname, metricOutliers))
        #load a subset of the outliers
        elif isinstance(delimiter, (tuple, list)):
            for metricname in delimiter:
                try:
                    metricOutliers = outliersDict[metricname]
                    outliers.append((metricname, metricOutliers))
                except KeyError:
                    print('%s is not a valid metricname' %metricname)
                    continue
        #load outliers for a metric
        else:
            try:
                outliers = outliersDict[delimiter]
            except KeyError:
                print('%s is not a valid metricname' %delimiter)
                outliers = None
        return outliers
        
    
    def fetchPlotData(self, metricname):
        #load dictionary
        rajenDict = self.loadRajenDict()
        #fetch data and unpack it
        plotdata = []
        try:
            datadict = rajenDict['data'][metricname]
            stocks, data = datadict.keys(), datadict.values()
            means, pvals = [list(tupl) for tupl in zip(*data)]
            boundary = rajenDict['boundary'][metricname]
            plotdata.append((stocks, means, pvals, boundary))   
        except KeyError:
            pass        
        return plotdata
    
    def rajenPlotter(self, metricname):
        import matplotlib.pyplot as plt
        import matplotlib.lines as mlines
        from mpldatacursor import datacursor
        #load data objects
        plotdata = self.fetchPlotData(metricname)
        ctrlkeys = ['ctrl+', 'ctrl-']
        posCtrl, negCtrl = [self.controls[key] for key in ctrlkeys]
        controls = posCtrl + negCtrl
        #test whether plotdata is empty 
        assert len(plotdata[0])>0, '%s is not a valid metricname' %metricname
        #set plots
        plt.close('all')
        ax = plt.subplot(111)    
        #unpack plotdata
        stocks, means, pvals, boundary = plotdata[0]
        day8, day22 = zip(*means)
        ax.scatter(day8, day22, s = 12, c = '#CFD3D4')
        #set colors and sizes
        outliers = self.fetchOutliers(delimiter = metricname)#fetch outliers
        #set colorsets and sizesets
        colorset = ['r' if stock in outliers else '#CFD3D4' for stock in stocks]
        colorset = ['b' if stock in posCtrl else colorset[j] for j, stock in enumerate(stocks)]
        colorset = ['g' if stock in negCtrl else colorset[j] for j, stock in enumerate(stocks)]
        sizeset = [30 if stock in outliers else 8 for stock in stocks]
        sizeset = [40 if stock in controls else sizeset[j] for j, stock in enumerate(stocks)]
        #plot data
        ax.scatter(day8, day22, s = sizeset, c = colorset)
        #boundaries
        xset, yset = zip(*boundary)
        ax.plot(xset, yset, color = '#851E81', linestyle = '--', alpha = 0.5, linewidth = 2.0)
        #set axis labels
        ax.set_xlabel('Day8', fontsize = 13)
        ax.set_ylabel('Day22', fontsize = 13)
        #set title
        labelsDict = dict(zip(self.metricnames, ['Speed of movement', 'Angle of movement', 'Angle of interaction', 'End-to-end distance']))
        ax.set_title('%s' %labelsDict[metricname], fontsize = 14)
        #set legend: define handlers
        leglabels = ['dataset', 'outlier'] + ctrlkeys; colors = ['#CFD3D4', 'r', 'b', 'g']
        outliers = [mlines.Line2D([], [], color=colors[i], marker='.', linestyle = '', markersize = 12, label = '%s' %leglabels[i]) for i, label in enumerate(leglabels)] 
        ax.legend(handles = outliers, fontsize = 12, loc = 'best')
        #label datapoints interactively
        datacursor(ax.collections[0], hover=True, point_labels = stocks, fontsize = 10, bbox= None, xytext=(0, 25), formatter=lambda **kwargs: kwargs['point_label'][0])      
        plt.show()
        return



#iFly_outliers().loadRajenDict()
#iFly_outliers().buildOutliersDict()
#outliers = iFly_outliers().fetchOutliers(delimiter = 'all')
#plotdata = iFly_outliers().fetchPlotData('angle')
iFly_outliers().rajenPlotter('angle')
