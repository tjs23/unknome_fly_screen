import os
import sys
import numpy as np

class QAFF_outliers():
    
    def __init__(self):
        self.cwd = os.getcwd()
        self.workdir = '%s\Dropbox\Unknome\Screens\Outliers\RajenAnalysis' %self.cwd
        self.screendir = os.path.join(self.workdir, 'QAFF')
        self.pickledir = os.path.join(self.workdir, 'Picklefiles')
        if not os.path.exists(self.pickledir):
            os.makedirs(self.pickledir)
        return
    
    def filenamePatterns(self):
        #filenames expression patterns
        metricsnames = ['area', 'count',  'H', 'L', 'S']
        dtype = ['RODs', 'nonRODs']
        mPatterns = ['males_%s' %name for name in metricsnames]
        fPatterns = ['females_%s_%s' %(dname, name)  for name in metricsnames for dname in dtype]
        patterns = mPatterns + fPatterns
        return patterns
        
             
    def buildRajenDict(self):
        import cPickle as pickle
        from itertools import chain
        from collections import OrderedDict
        from datetime import datetime
        #build empty dictionary container
        outliersDict = {}
        outliersDict['data'] = {} 
        outliersDict['data']['females'] = {}; 
        outliersDict['data']['females']['RODs'] = {}; outliersDict['data']['females']['nonRODs'] = {}
        outliersDict['data']['males'] = {}
        #boundaries dictionary
        outliersDict['boundary'] = {}
        outliersDict['boundary']['females'] = {} 
        outliersDict['boundary']['females']['RODs'] = {}; outliersDict['boundary']['females']['nonRODs'] = {}
        outliersDict['boundary']['males'] = {}
        #fetch filenames
        subdirnames = ['Males', 'Females']
        filenames = [os.listdir(os.path.join(self.screendir, name)) for name in subdirnames]
        filenames = list(chain(*filenames))
        #fetch data from files
        patterns = self.filenamePatterns()#filenames expression patterns
        for pattern in patterns:
            filepaths = [os.path.join(os.path.join(self.screendir, pattern.split('_')[0].title()), filename) for filename in filenames if pattern in filename]
            boundary, means, pvals = [np.genfromtxt (filepath, delimiter=",", dtype = None) for filepath in filepaths]
            stocks = means[1:,0]; stocks = [stock[1:-1] if stock[0] == '"' else stock for stock in stocks]
            stocks = ['JS%s' %stock if stock.isdigit() else stock for stock in stocks]
            stocks = ['GFPi' if stock == 'GFPi_' else stock for stock in stocks]
            #reformat data
            metric = np.asarray(means[1:,1], dtype = np.float64)
            pvals = np.asarray(pvals[1:,1], dtype = np.float64)
            boundary= np.asarray(boundary[1:,1], dtype = np.float64)
            #build dictionary
            values = [metric, pvals]
            values = zip(*values)
            metricDict = OrderedDict(zip(stocks, values))
            if pattern.split('_')[0] == 'males':
                gender, metricname = pattern.split('_')
                outliersDict['data'][gender][metricname] = metricDict
                outliersDict['boundary'][gender][metricname] = boundary
            elif pattern.split('_')[0] == 'females':
                gender, depositType, metricname = pattern.split('_')
                outliersDict['data'][gender][depositType][metricname] = metricDict
                outliersDict['boundary'][gender][depositType][metricname] = boundary
        #Fetch current time and date
        time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        #serialise dictionary
        filename = 'rajenQAFFDict_%s.pickle' %time
        picklepath = os.path.join(self.pickledir, filename)
        with open(picklepath, 'wb') as f:
            pickle.dump(outliersDict, f, protocol = 2)
        return
            
    def loadRajenDict(self):
        import cPickle as pickle
        filelist = [filename for filename in os.listdir(self.pickledir) if filename.startswith('rajenQAFF')]
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
        outliers = {}
        outliers['females'] = {}; 
        outliers['females']['RODs'] = {}; outliers['females']['nonRODs'] = {}
        outliers['males'] = {}
        #fetch outliers
        patterns = self.filenamePatterns()
        for pattern in patterns:
            if pattern.split('_')[0] == 'males':
                metric = pattern.split('_')[1]
                metricdict = rajenDict['data']['males'][metric]
                data = metricdict.values()
                metric_outliers = [metricdict.keys()[i] for i, tupl in enumerate(data) if tupl[1]<=0.05]
                outliers['males'][metric] = metric_outliers                  
            elif pattern.split('_')[0] == 'females':
                gender, dtype, metric = pattern.split('_')  
                metricdict = rajenDict['data']['females'][dtype][metric]
                data = metricdict.values()
                metric_outliers = [metricdict.keys()[i] for i, tupl in enumerate(data) if tupl[1]<=0.05]
                outliers['females'][dtype][metric] = metric_outliers
        #Fetch current time and date
        time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        #serialise dictionary
        picklepath = os.path.join(self.pickledir, 'outliersQAFFDict_%s.pickle' %time)
        with open(picklepath, 'wb') as f:
            pickle.dump(outliers, f, protocol = 2)  
        return
    
    def loadOutliersDict(self):
        import cPickle as pickle
        filelist = [filename for filename in os.listdir(self.pickledir) if filename.startswith('outliersQAFF')]
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
        if delimiter == 'all':
            outliers = []
            patterns = self.filenamePatterns()
            for pattern in patterns:
                if pattern.split('_')[0] == 'males':
                    metric = pattern.split('_')[1]
                    metricOutliers = outliersDict['males'][metric]
                    outliers.append((pattern, metricOutliers))
                elif pattern.split('_')[0] == 'females':
                    gender, dtype, metric = pattern.split('_')  
                    metricOutliers = outliersDict['females'][dtype][metric]
                    outliers.append((pattern, metricOutliers))
        #load a subset of the outliers
        else:
            try:
                #females
                gender, dtype, metric = delimiter
                outliers = outliersDict['females'][dtype][metric]
            except ValueError:
                #males
                gender, metric = delimiter
                outliers = outliersDict['males'][metric] 
        return outliers
        
        
    def intersectDatasets(self, plotdata):
        plotdata1, plotdata2 = plotdata
        stocks1, means1, pvals1, boundary1 = plotdata1
        stocks2, means2, pvals2, boundary2 = plotdata2
        stocks = stocks1 + stocks2
        intersectStocks = [stock for stock in stocks if stocks.count(stock) < 2]
        try:
            assert (len(intersectStocks) == 0), '%s do/does not belong to both datasets' %','.join(intersectStocks)
        except AssertionError, e:
            print(e)
            for stock in intersectStocks:
                if stock in stocks1:
                    idx = stocks1.index(stock)
                    templist = [stocks1, means1, pvals1]
                    [sublist.pop(idx) for sublist in templist]
                    templist.append(boundary1)
                    plotdata1 = templist
                else:
                    idx = stocks2.index(stock)
                    templist = [stocks2, means2, pvals2]
                    [sublist.pop(idx) for sublist in templist]
                    templist.append(boundary2)
                    plotdata2 = templist
            plotdata = [plotdata1, plotdata2]
        return plotdata
        
    
    def fetchPlotData(self, keys, intersect = False):
        #load dictionary
        rajenDict = self.loadRajenDict()
        #test whether keys is a list of lists
        if isinstance(keys[0], str):
            keys = [keys]
        #fetch data and unpack it
        plotdata = []
        for key in keys:
            try:
                #males
                gender, metric = key
                datadict = rajenDict['data'][gender][metric]
                stocks, data = datadict.keys(), datadict.values()
                means, pvals = [list(tupl) for tupl in zip(*data)]
                boundary = rajenDict['boundary'][gender][metric]   
            except ValueError:
                #females
                gender, dtype, metric = key
                datadict = rajenDict['data'][gender][dtype][metric]
                stocks, data = datadict.keys(), datadict.values()
                means, pvals = [list(tupl) for tupl in zip(*data)]
                boundary = rajenDict['boundary'][gender][dtype][metric]
            plotdata.append((stocks, means, pvals, boundary))
        if intersect:
            plotdata = self.intersectDatasets(plotdata)
        return plotdata
    
    
    def rajenPlotter(self, datakeys, intersect = True):
        import matplotlib.pyplot as plt
        import matplotlib.lines as mlines
        from mpldatacursor import datacursor
        #load data object
        plotdata = self.fetchPlotData(datakeys, intersect = intersect)
        #set plots
        plt.close('all')
        ax = plt.subplot(111)    
        if len(plotdata) == 1:
            stocks, means, pvals, boundary = plotdata[0]
            xset = np.arange(len(stocks))
            ax.scatter(xset, means, s = 12, c = '#CFD3D4')
        elif len(plotdata) == 2:
            plotdata1, plotdata2 = plotdata
            stocks1, means1, pvals1, boundary1 = plotdata1
            stocks2, means2, pvals2, boundary2 = plotdata2
            #set colors and sizes
            colorset = ['#CFD3D4' for stock in stocks1]
            sizeset = [8 for stock in stocks1]
            for i, key in enumerate(datakeys):
                outliers = self.fetchOutliers(delimiter = key)#fetch outliers
                #set colorset
                colors = ['r', 'b']
                colorset = [colors[i] if stock in outliers else colorset[j] for j, stock in enumerate(stocks1)]
                colorset = ['g' if (stock == 'LK' and stock in outliers) else colorset[j] for j, stock in enumerate(stocks1)]
                sizeset = [30 if stock in outliers else sizeset[j] for j, stock in enumerate(stocks1)]
                sizeset = [40 if stock == 'LK' and stock in outliers else sizeset[j] for j, stock in enumerate(stocks1)]
            #plot data
            ax.scatter(means1, means2, s = sizeset, c = colorset)
            #boundaries
            stepdict = {'count':5, 'area':5, 'H':5, 'L':0.05, 'S':0.005}#adjust step to data range
            step = stepdict[datakeys[0][-1]]
            ax.plot((boundary1[0], boundary1[0]), (boundary2[0]-step, boundary2[1]+step), color = 'r', linestyle = '--', alpha = 0.5)
            ax.plot((boundary1[1], boundary1[1]), (boundary2[0]-step, boundary2[1]+step), color = 'r', linestyle = '--', alpha = 0.5)
            ax.plot((boundary1[0]-step, boundary1[1]+step), (boundary2[0],boundary2[0]), color = 'b', linestyle = '--', alpha = 0.5)
            ax.plot((boundary1[0]-step, boundary1[1]+step), (boundary2[1],boundary2[1]), color = 'b', linestyle = '--', alpha = 0.5)
            #set axis labels
            if datakeys[0][0] == datakeys[1][0]:#same gender
                ax.set_xlabel('%s' %datakeys[0][1], fontsize = 13)
                ax.set_ylabel('%s' %datakeys[1][1], fontsize = 13)
                leglabels = [datakeys[0][1], datakeys[1][1]]
            else:
                ax.set_xlabel('%s' %datakeys[0][0].title(), fontsize = 13)
                ax.set_ylabel('%s' %datakeys[1][0].title(), fontsize = 13)
                leglabels = [datakeys[0][0], datakeys[1][0]]
            #set title
            try:
                metricnames = {'H':'hue', 'S':'saturation', 'L':'lightness'}
                metricname = metricnames[datakeys[0][-1]]
                ax.set_title('Deposits %s' %metricname, fontsize = 14)
            except KeyError:
                ax.set_title('Deposits %s' %datakeys[0][-1], fontsize = 14)
            #set legend: define handlers
            outliers1 = mlines.Line2D([], [], color='r', marker='.', linestyle = '', markersize=12, label='outliers: %s' %leglabels[0])
            outliers2 = mlines.Line2D([], [], color='b', marker='.', linestyle = '', markersize=12, label='outliers: %s' %leglabels[1])
            #LK in outliers
            if 'g' in colorset:
                outliers3 = mlines.Line2D([], [], color='g', marker='.', linestyle = '', markersize=12, label='LK')
                ax.legend(handles = [outliers1, outliers2, outliers3], fontsize = 12, loc = 'lower right')
            else:
                ax.legend(handles = [outliers1, outliers2], fontsize = 12, loc = 'best')
            #label datapoints interactively
            datacursor(ax.collections[0], hover=True, point_labels = stocks1, fontsize = 10, bbox= None, xytext=(0, 25), formatter=lambda **kwargs: kwargs['point_label'][0])      
        plt.show()
        return







#QAFF_outliers().rajenPlotter([('females', 'nonRODs', 'S'), ('females', 'RODs', 'S')], intersect = True)
#Outliers().buildRajenDict()
#Outliers().buildOutliersDict()
#rajendict = Outliers().loadRajenDict()
#outliers = Outliers().loadOutliers()
#outliers = outliers['females']['nonRODs']['area']
#print(rajendict['data']['males']['H'])