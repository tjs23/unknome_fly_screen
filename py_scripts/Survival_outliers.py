import sys
import os
import numpy as np


class Survival_outliers():
    
    def __init__(self):
        from collections import OrderedDict
        from itertools import product
        self.cwd = os.getcwd()
        self.snames = ['ROS', 'Starvation']
        self.workdir = '%s\Dropbox\Unknome\Screens\Outliers\RajenAnalysis' %self.cwd
        self.rosdir, self.starvdir = [os.path.join(self.workdir, sname) for sname in self.snames]
        self.screendirDict = OrderedDict([('ROS', self.rosdir), ('Starvation', self.starvdir)]) 
        self.pickledir = os.path.join(self.workdir, 'Picklefiles')
        if not os.path.exists(self.pickledir):
            os.makedirs(self.pickledir)
        self.a_labels = ['Cox', 'medsurv']; self.t_labels = ['boundaries', 'estimates', 'density']
        f_labels = list(product(self.a_labels, self.t_labels))
        self.f_labels = ['%s_%s' %(a,b) for a,b in f_labels]
        return
    
    
    def buildSurvDatadict(self):
        import cPickle as pickle
        screen_items = self.screendirDict.items()
        dataDict = {}
        for sname, dirpath in screen_items:
            dataDict[sname] = {}
            filenames = ['%s_%s.csv' %(sname,label) for label in self.f_labels]
            filepaths = [os.path.join(dirpath, filename) for filename in filenames]
            for i, filepath in enumerate(filepaths):
                if self.f_labels[i].split('_')[-1] == 'boundaries':
                    boundaries = np.loadtxt(filepath, skiprows = 1, usecols = (1,), delimiter = ',')
                    dataDict[sname][self.f_labels[i]] = boundaries
                else:
                    data = np.genfromtxt(filepath, skip_header = 1, dtype = None, delimiter = ',', unpack = True)
                    if self.f_labels[i].split('_')[-1] == 'estimates':
                        fname = '%s_%s.csv' %(sname, 'pvals')
                        filepath = os.path.join(self.screendirDict[sname], fname)
                        pvals_data = np.genfromtxt(filepath, skip_header = 1, dtype = None, delimiter = ',', unpack = True)
                        data = [(stockId[1:-1], (estimate, pvals_data[z][1]))for z, (stockId, estimate) in enumerate(data)]
                        data = dict(data)
                    dataDict[sname][self.f_labels[i]] = data
        #serialise dictionary
        picklepath = os.path.join(self.pickledir, 'survDataDict.pickle')
        with open(picklepath, 'wb') as f:
            pickle.dump(dataDict, f, protocol = 2)
        return
        
    
    def loadSurvDataDict(self):
        import cPickle as pickle 
        picklepath = os.path.join(self.pickledir, 'survDataDict.pickle')
        with open(picklepath, 'rb') as f:
            survdataDict = pickle.load(f)
        return survdataDict
    
    
    def fetchSurvOutliers(self):
        #load data object
        survDatadict = self.loadSurvDataDict()
        #filter out outliers
        outliers_ros = [(stock, a) for (stock, (a,b)) in survDatadict['ROS']['medsurv_estimates'].items() if b<0.05]
        outliers_starv = [(stock, a) for (stock, (a,b)) in survDatadict['Starvation']['medsurv_estimates'].items() if b<0.05]
        outliers = {'ROS': outliers_ros, 'Starvation': outliers_starv}
        return outliers
    
    
    def plotCoxDensity(self, screenkey = 'ROS_medsurv'):
        import matplotlib.pyplot as plt
        #load data object
        survdataDict = self.loadSurvDataDict()
        outliersDict = self.fetchSurvOutliers()
        #load data and boundaries
        sname, a_label = screenkey.split('_')
        density = survdataDict[sname]['%s_density' %a_label]; x, y = density
        boundaries = survdataDict[sname]['%s_boundaries' %a_label]
        #fetch outliers datapoints
        outliers = outliersDict[sname] 
        x_outlier, y_outlier = zip(*outliers)[1], np.zeros(len(outliers))
        #plot definition
        ax = plt.subplot(111)
        colorset = ['r' if stock.startswith('JS') else '#B7E60E' for stock in zip(*outliers)[0]]#define marker color scheme
        ax.plot(x,y, c = 'g')#plot density
        ax.scatter(x_outlier, y_outlier, marker = 'o', s = 30, c = colorset, linewidth = 0.5)#plot outliers
        ax.scatter(survdataDict[sname]['%s_estimates' %a_label]['Empty'][0], 0, marker = 'x', s = 30, c = 'b')#plot Empty
        #plot boundaries
        [ax.axvline(bound, color = 'b', linestyle = '--', linewidth = 0.5) for bound in boundaries]
        #set axis labels
        ax.set_xlabel('Median survival (hours)', fontsize = 11)
        ax.set_ylabel('Hazard estimate', fontsize = 11)
        #set axis limits
        ax.set_ylim([-0.001, ax.get_ylim()[1]])
        if screenkey == 'Starvation_medsurv':
            ax.set_xlim([250, 430])
        #define custom artists for legends
        ouliers_Artist = plt.Line2D((), (), color='r', marker='o', ms = 3, mec = 'r', linestyle='')
        pos_Artist = plt.Line2D((), (), color='#B7E60E', marker='o', ms = 3, mec = '#B7E60E', linestyle='')
        neg_Artist = plt.Line2D((), (), color='b', marker='x', ms = 3, mec = 'b', linestyle='')
        #set legend
        handles = [ouliers_Artist, pos_Artist, neg_Artist]; labels = ['outliers', 'control(+)', 'control(-)']
        ax.legend(handles, labels, fontsize = 10)
        plt.show()
        return
    
    
    def intersectDatasets(self):
        from File_Functions import listPartition
        from itertools import chain
        from collections import Counter
        #load data object
        survdataDict = self.loadSurvDataDict()
        #fetch data
        dataDictionaries = [survdataDict[sname]['medsurv_estimates'] for sname in self.snames]
        data_values = [zip(*datadict.values()) for datadict in dataDictionaries]
        data_ros, data_starv = data_values; medsurv_ros, pvals_ros = data_ros; medsurv_starv, pvals_starv = data_starv #unpack
        stocksets = [datadict.keys() for datadict in dataDictionaries]
        stockset_counter = Counter(chain(*stocksets))
        commonStocks, uniqueStocks = listPartition(lambda x: x[1]==2, stockset_counter.items())
        uniqueStocks = listPartition(lambda x:x[0] in survdataDict['ROS']['medsurv_estimates'].keys(), uniqueStocks)
        uniqueStocks = dict(zip(self.snames, [[stock for (stock, val) in lst] for lst in uniqueStocks]))
        return commonStocks, uniqueStocks
    
    
    def plotOutliers(self):
        import matplotlib.pyplot as plt
        from mpldatacursor import datacursor
        #load data object
        survdataDict = self.loadSurvDataDict()
        commonStocks, uniqueStocks = self.intersectDatasets()
        js_commonStockset = [stock[0] for stock in commonStocks if stock[0].startswith('JS')]
        #fetch screen data
        dataDictionaries = [survdataDict[sname]['medsurv_estimates'] for sname in self.snames]
        boundaries = [survdataDict[sname]['medsurv_boundaries'] for sname in self.snames]
        #fetch data for each stock
        data_values = [[datadict[stockId] for stockId in js_commonStockset] for datadict in dataDictionaries]
        data_values = [zip(*lst) for lst in data_values]
        #unpack data
        data_ros, data_starv = data_values; medsurv_ros, pvals_ros = data_ros; medsurv_starv, pvals_starv = data_starv
        boundary_ros, boundary_starv = boundaries
        #define colorset and sizeset
        pvals = [pvals_ros, pvals_starv]; pvals_coded = zip(*[[1 if val<=0.05 else 0 for val in lst]for lst in pvals])
        colorset, sizeset = zip(*[('#CC3DCC', 20) if 1 in tupl else ('#CFD3D4', 7) for tupl in pvals_coded])
        #define plot
        ax = plt.subplot(111) 
        ax.scatter(medsurv_ros, medsurv_starv, c = colorset, s = sizeset, lw = 0.5)
        #plot empty and GFPi
        x_empty, y_empty = [survdataDict[sname]['medsurv_estimates']['Empty'][0] for sname in self.snames]
        x_gfpi, y_gfpi = [survdataDict[sname]['medsurv_estimates']['GFPi'][0] for sname in self.snames]
        ax.scatter(x_empty, y_empty, marker = 'x', c = 'b', s = 40)#empty
        ax.scatter(x_gfpi, y_gfpi, marker = 'x', c = '#CC3DCC', s = 40)#gfpi
        #draw boundaries
        ax.plot((boundary_ros[0], boundary_ros[0]), (boundary_starv[0]+20, boundary_starv[1]-20), color = 'r', linestyle = '--')
        ax.plot((boundary_ros[1], boundary_ros[1]), (boundary_starv[0]+20, boundary_starv[1]-20), color = 'r', linestyle = '--')
        ax.plot((boundary_ros[0]+10, boundary_ros[1]-10), (boundary_starv[0], boundary_starv[0]), color = 'g', linestyle = '--')
        ax.plot((boundary_ros[0]+10, boundary_ros[1]-10), (boundary_starv[1], boundary_starv[1]), color = 'g', linestyle = '--')
        #set axs limits
        ax.set_xlim([90, 210])
        ax.set_ylim([270, 410])
        #set axis labels
        ax.set_xlabel('ROS median survival (hours)', fontsize = 13)
        ax.set_ylabel('Starvation median survival (hours)', fontsize = 13)
        #set legend
        outlier_artist = plt.Line2D((), (), c = '#CC3DCC', marker = 'o', ms = 3, mec = '#CC3DCC', linestyle = '')
        neg_artist = plt.Line2D((), (), c = 'b', marker = 'x', ms = 3, mec = 'b', linestyle = '')
        gfpi_artist = plt.Line2D((),(), c = '#CC3DCC', marker = 'x', ms = 3, mec = '#CC3DCC', linestyle = '')
        handles = [outlier_artist, neg_artist, gfpi_artist]; labels =['outliers', 'control(-)', 'GFPi']
        ax.legend(handles, labels, fontsize = 10)
        #label datapoints interactively
        datapoints = ax.collections[0]
        datacursor(datapoints, hover=True, point_labels = js_commonStockset, fontsize = 10, bbox= None, xytext=(0, 25), formatter=lambda **kwargs: kwargs['point_label'][0])
        plt.show()
        return
        


#Survival_outliers().plotCoxDensity(screenkey = 'ROS_medsurv')
#Survival().buildSurvDatadict()
#Survival_outliers().plotOutliers()


