import numpy as np
import sys
import os



class Dashboard():
    def __init__(self):
        self.cwd = os.getcwd()
        self.basedir = 'U:\iFly'
        self.dbdir = '%s\Dropbox\Unknome\Databases' %self.cwd
        self.workdir = '%s\Dropbox\Unknome\Screens\iFly\PyiFly' %self.cwd
        self.pickledir = os.path.join(self.workdir, 'PickleFiles')
        self.hdfpath_batch = os.path.join(self.pickledir, 'batchRawdata.hdf5')
        self.hdfpath_stock = os.path.join(self.pickledir, 'stockRawdata.hdf5')
        self.ctrlsynonyms = self.ctrlSynonyms()
        self.days = ['Day8', 'Day22']
        self.timepoints = [8, 22]
        self.dayfolders = [os.path.join(self.basedir, timepoint) for timepoint in self.days]
        self.batchnames = [os.listdir(dayfolder) for dayfolder in self.dayfolders][0]
        self.batchnumbers = [i+1 for i in xrange(len(self.batchnames))]
        self.metricnames = {'velocities':'velocities', 'dist2e':'dist2e', 'anglesInteraction':'angleInt', 'angles':'angle'}
        self.negControls = ['Empty', 'w1118', 'GFPi', 'GFPi(9)', 'Dicer-']
        self.posControls = ['Pink', 'Tinman', 'Flightin', 'Hand']
        return

    def ctrlSynonyms(self):                                                                                                                        
        synonyms = {'DAXEMPTY':'Dicer-', 'DDAXEMPTY':'Empty', 'DDAXFLIGHTINI':'Flightin', 'DDAXFLIGHTIN':'Flightin', 'DDAXGFPI':'GFPi', 'DDAXGFP':'GFPi', 'DDAXHANDI':'Hand', 'DDAXHAND':'Hand',
        'DDAXPINKI':'Pink', 'DDAXPINK':'Pink', 'DDAXTINMANI':'Tinman', 'DDAXTINMAN':'Tinman', 'DDAXW1118':'w1118', '367':'Empty', '396':'Pink', '442':'GFPi(9)', 'PINK':'Pink', 'PNK':'Pink', 'GFP':'GFPi', 
        'EMP':'Empty', 'GFPI':'GFPi', '368':'w1118', '399':'Flightin', 'GFPRNAI':'GFPi', 'TINMAN':'Tinman', 'HAND':'Hand', 'FLIGHTIN':'Flightin', 'DDAXGFP-RNAI':'GFPi', 'DDAXRNAI':'GFPi'}
        return synonyms
        


class RawdataOperations(Dashboard):
    def __init__(self):
        Dashboard.__init__(self)
        return
        
    def copyToRawdata_edited(self):
        from shutil import copytree
        dayBatchfolders = [[os.path.join(dayfolder, batch) for batch in self.batchnames] for dayfolder in self.dayfolders]
        rawdataBatchfolders = [[os.path.join(batchfolder,'Rawdata') for batchfolder in dayfolder] for dayfolder in dayBatchfolders]
        rawdataBatchfolders_edited = [[os.path.join(batchfolder,'Rawdata_edited') for batchfolder in dayfolder] for dayfolder in dayBatchfolders]
        for i, dayfolder in enumerate(rawdataBatchfolders):
            for j, batchfolder in enumerate(dayfolder):
                if os.path.exists(rawdataBatchfolders_edited[i][j]):
                    os.remove(rawdataBatchfolders_edited[i][j])
                print('Copying %s' %batchfolder)
                copytree(batchfolder, rawdataBatchfolders_edited[i][j], symlinks=False, ignore=None)
        return
        
    
    def filteroutRawdata(self):
        from itertools import ifilter
        dayBatchfolders = [[os.path.join(dayfolder, batch) for batch in self.batchnames] for dayfolder in self.dayfolders]
        archiveBatchfolders = [[os.path.join(os.path.join(batchfolder,'Archive\Results_old'), 'velocities') for batchfolder in dayfolder] for dayfolder in dayBatchfolders]
        rawdataBatchfolders_edited = [[os.path.join(batchfolder,'Rawdata_edited') for batchfolder in dayfolder] for dayfolder in dayBatchfolders]
        substring ='_velocities.dat'
        for i, dayfolder in enumerate(archiveBatchfolders):
            validFnames_batches = [[fname[:fname.index(substring)]+'.dat' for fname in os.listdir(archivepath)] for archivepath in dayfolder]
            notvalidFnames_batches = [list(ifilter(lambda x:x not in validFnames_batches[j], os.listdir(batchfolder))) for j, batchfolder in enumerate(rawdataBatchfolders_edited[i])]
            filesToDrop = [os.path.join(batchfolder, fname) for j, batchfolder in enumerate(rawdataBatchfolders_edited[i]) for fname in notvalidFnames_batches[j]]
            print(filesToDrop)
            [os.remove(rawdatapath) for rawdatapath in filesToDrop]
        return    
    
    
    
class iFlyObj(Dashboard):
    
    def __init__(self):
        Dashboard.__init__(self)
        return
            
    def createBatchH5Groups(self):
        import h5py
        #create group structure
        metricnames_files = self.metricnames.values()
        with h5py.File(self.hdfpath_batch, "w") as f:
            for x in metricnames_files:
                grpmetric = f.create_group(x)
                for y in self.days:
                    grpbatch = grpmetric.create_group(y[3:])
                    for z in self.batchnumbers:
                        grpbatch.create_group(str(z))
        return
        

    def buildBatchRawdataH5(self):
        from itertools import chain
        import h5py
        #define H5 group structure 
        if os.path.exists(self.hdfpath_batch):
            os.remove(self.hdfpath_batch)
        self.createBatchH5Groups()
        #add datasets to H5 groups
        with h5py.File(self.hdfpath_batch, 'r+') as f:
            metricnames_folders = self.metricnames.keys()
            for i, dayfolder in enumerate(self.dayfolders):
                metricfolders = [os.path.join(dayfolder, '%s\Results\%s' %(batchname, metric)) for batchname in self.batchnames for metric in metricnames_folders]#fetch paths to metric folders
                filenames_metrics = [[fname for fname in os.listdir(metricfolder) if fname[-3:] == 'dat'] for metricfolder in metricfolders]#fetch filenames in each metrics folder 
                indtestsIDs_metrics = [list(set([fname.split('.')[0] for fname in metricfolder])) for metricfolder in filenames_metrics]#fetch set of ID tags for independent tests in each metrics folder
                repeats = [[[fname for fname in filenames_metrics[i] if fname.split('.')[0]== indtest] for indtest in metric] for i, metric in enumerate(indtestsIDs_metrics)]#cluster repeats in each metrics folder
                for j, metricfolder in enumerate(metricfolders):
                    print(metricfolder)
                    metricname = os.path.split(metricfolder)[1]
                    metricnameFile = self.metricnames[metricname]
                    substring = '\Results\%s' %metricname
                    batchnumb = int(os.path.split(metricfolder[:-len(substring)])[1][4:])
                    for z, repeat in enumerate(repeats[j]):
                        repeats_metrics = ['%s%s.dat' %(fname[:fname.index(metricnameFile)], metricnameFile) for fname in repeat]#parse metrics filenames
                        data = list(chain(*[np.loadtxt(os.path.join(metricfolder,fname), skiprows=1, usecols=(0,), dtype=float, ndmin = 1) for fname in repeats_metrics]))
                        stockID, timetag, indtest = repeat[0].split('.')[0].split('_')
                        try:
                            stockID_upper = stockID.upper()
                            stock = self.ctrlsynonyms[stockID_upper]
                        except KeyError:
                            stock = 'JS%s'%stockID
                        print(stock, timetag, indtest)
                        try:
                            grpstock = f[metricnameFile][timetag][str(batchnumb)][stock]
                        except KeyError:
                            grpstock = f[metricnameFile][timetag][str(batchnumb)].create_group(stock)
                        grpstock.create_dataset('assay%s' %str(z+1), data = data)                         
        return
        
         
    def loadBatchdataH5(self, metric, timepoint, batch):
        import h5py
        with h5py.File(self.hdfpath_batch, 'r') as f:
            metricRawdata = f[metric][str(timepoint)][str(batch)]
            batchdata = {}
            for key in metricRawdata.keys():
                data = [repeat[:] for repeat in metricRawdata[key].values()]
                batchdata[key] = data
        return batchdata
                       

    def buildStockRawdataH5(self):
        import h5py
        stockset = self.fetchStockset()
        stocklist = self.loadStocklist()
        stocklist = stocklist.values()[0].values()
        batchkeys_stock = [(stock,[i+1 for i, batch in enumerate(stocklist) if stock in batch]) for stock in stockset]
        #test whether file exists
        if os.path.exists(self.hdfpath_stock):
            os.remove(self.hdfpath_stock)
        #create group structure for stockRawdataH5
        metricnames_files = self.metricnames.values()
        with h5py.File(self.hdfpath_stock, "w") as f:
            for (stock, batchlist) in batchkeys_stock:
                grpstock = f.create_group(stock)
                for x in metricnames_files:
                    grpmetric = grpstock.create_group(x)
                    for y in self.timepoints:
                        grptime = grpmetric.create_group(str(y))
                        for z in batchlist:
                            grpbatch = grptime.create_group(str(z))
                            #fetch data from batchRawdataH5
                            with h5py.File(self.hdfpath_batch, 'r') as g:
                                try:
                                    stockdata = g[x][str(y)][str(z)][stock]
                                    print(x,y,z,stock)
                                    for key, item in stockdata.items():
                                        grpbatch.create_dataset(key, data = item[:])#add datasets
                                except KeyError:
                                    continue    
        return
        
                           
    def loadStockdataH5(self, stockID, metric):
        import h5py
        with h5py.File(self.hdfpath_stock, 'r') as f:
            metricdata = f[stockID][metric]
            stockdata = {}
            for timepoint in self.timepoints:
                timedata = metricdata[str(timepoint)]
                stockdata[timepoint] = {}
                for key in timedata.keys():
                    data = [repeat[:] for repeat in timedata[key].values()]
                    stockdata[timepoint][int(key)] = data
        return stockdata
        
        
    def buildBatchdataDict(self):
        from scipy import stats
        import cPickle as pickle
        batchdataDict = {}
        for metricname in self.metricnames.values():
            batchdataDict[metricname] = {}
            for timepoint in self.timepoints:
                batchdataDict[metricname][timepoint] = {}
                for batchnumber in self.batchnumbers:
                    batchdataDict[metricname][timepoint][batchnumber] = {}
                    batchdata = iFlyObj().loadBatchdataH5(metricname, timepoint, batchnumber)
                    for key in batchdata.keys():
                        batchdataDict[metricname][timepoint][batchnumber][key] = {}
                        print(metricname, timepoint, batchnumber, key)
                        stockdata = batchdata[key]
                        if metricname == 'velocities':
                            stockdata, lambda_cox = zip(*[stats.boxcox(repeat) for repeat in stockdata])
                        data = [(np.mean(repeat), stats.sem(repeat), len(repeat)) for repeat in stockdata]
                        batchdataDict[metricname][timepoint][batchnumber][key] = data
        #serialise batchdata dictionary
        picklepath = os.path.join(Dashboard().pickledir, 'batchdataDict.pickle')
        with open(picklepath, 'wb') as f:
            pickle.dump(batchdataDict, f, protocol = 2)
        return


    def loadBatchdataDict(self):
        import cPickle as pickle
        picklepath = os.path.join(self.pickledir, 'batchdataDict.pickle')
        with open(picklepath, 'rb') as f:
            batchdataDict = pickle.load(f)
        return batchdataDict 
        
        
    def buildStockdataDict(self):
            from scipy import stats
            import cPickle as pickle
            #fetch stockset
            stockset = self.fetchStockset()
            #build dictionary
            stockdataDict = {}
            for stock in stockset:
                stockdataDict[stock] = {}
                for metricname in Dashboard().metricnames.values():
                    stockdataDict[stock][metricname] = {}
                    try:
                        stockdata = self.loadStockdataH5(stock, metricname)
                        timepoints, batchdata = zip(*stockdata.items())
                    except KeyError:
                        continue
                    for i, timepoint in enumerate(timepoints):
                        stockdataDict[stock][metricname][timepoint] = {}
                        for batchnumber in batchdata[0].keys():
                            stockdataDict[stock][metricname][timepoint][batchnumber] = {}
                            try:
                                stockdata = batchdata[i][batchnumber]
                                print(stock, metricname, timepoint, batchnumber)
                            except KeyError:
                                continue
                            if metricname == 'velocities':
                                stockdata, lambda_cox = zip(*[stats.boxcox(repeat) for repeat in stockdata])
                            data = [(np.mean(repeat), stats.sem(repeat), len(repeat)) for repeat in stockdata]
                            stockdataDict[stock][metricname][timepoint][batchnumber] = data
            #serialise stockdata dictionary
            picklepath = os.path.join(self.pickledir, 'stockdataDict.pickle')
            with open(picklepath, 'wb') as f:
                pickle.dump(stockdataDict, f, protocol = 2)
            return
            
                       
    def loadStockdataDict(self):
            import cPickle as pickle
            picklepath = os.path.join(self.pickledir, 'stockdataDict.pickle')
            with open(picklepath, 'rb') as f:
                stockdataDict = pickle.load(f)
            return stockdataDict
            
            
    def buildStocklistObj(self):
        import cPickle as pickle
        stockset = {}
        for timepoint in self.timepoints:
            stockset[timepoint] = {} 
            for batchnumber in self.batchnumbers:
                print(timepoint, batchnumber)
                batchdata = self.loadBatchdataH5('velocities', timepoint, batchnumber)#load batchdata for timepoint
                stocks_batch = batchdata.keys()
                stockset[timepoint][batchnumber]= stocks_batch
        #serialise dictionary object
        picklepath = os.path.join(Dashboard().pickledir, 'stocklist.pickle')
        with open(picklepath, 'wb') as f:
            pickle.dump(stockset, f, protocol = 2)
        return
        
        
    def loadStocklist(self):
        import cPickle as pickle
        picklepath = os.path.join(self.pickledir, 'stocklist.pickle')
        with open(picklepath, 'rb') as f:
            stocklist = pickle.load(f)
        return stocklist
        
    
    def fetchStockset(self):
        from File_Functions import listPartition
        from itertools import chain
        stocklist = self.loadStocklist()
        stocklist = [[stocklist[timepoint][batchnumber] for timepoint in self.timepoints] for batchnumber in self.batchnumbers]
        stocklist_flatten = list(chain(*list(chain(*stocklist))))
        stockset = list(set(stocklist_flatten))
        js_stocks, controls = listPartition(lambda x: x.startswith('JS'), stockset); controls.sort()
        stockset = sorted(js_stocks, key = lambda x: int(x[2:])) + controls
        return stockset


    def fetchToBeDoneList(self):
        from Unknome_Functions import Unknome
        viables =Unknome().fetchViables(viability = 'Viable')
        stockset = self.fetchStockset()
        jsStockset = [stock for stock in stockset if stock.startswith('JS')]
        tobedone = [stock for stock in viables if stock not in jsStockset]
        return tobedone

    
    def fetchRepeats(self):
        stockdataDict = self.loadStockdataDict()
        repeatBatches = lambda x: stockdataDict[x]['velocities'][8].keys()
        repeats = [(stock, repeatBatches(stock)) for stock in stockdataDict.keys() if len(repeatBatches(stock))>1]
        repeats = dict(repeats)
        return repeats



class iFlyDB(iFlyObj):
    
    def __init__(self):
        iFlyObj.__init__(self)
        self.columnsDict = {'velocities':'Speed', 'dist2e':'Dist2e', 'angle':'Angles', 'angleInt':'AngleInt'}
        return
    
    def createMetricsTable(self, metric):
        import sqlite3
        #connect to database
        dbname = 'iFlyDB_%s.db' %metric
        dbpath = os.path.join(self.dbdir, dbname)
        db = sqlite3.connect(dbpath)
        cursor = db.cursor()
        #define table
        print('Creating table %s. \n' %metric)
        createStatement = '''CREATE TABLE  %s (sqlKey INTEGER PRIMARY KEY AUTOINCREMENT, Stock CHAR(50) NOT NULL, 
        
                                Day INT NOT NULL,  Batch INT NOT NULL, Repeat INT NOT NULL, %s REAL) ''' %(metric, self.columnsDict[metric])
        cursor.execute(createStatement)
        return
    
     
    def createDB(self, metric):
        import sqlite3 
        #load data objects    
        stockset = iFlyObj().fetchStockset()            
        #Connect to database
        dbname = 'iFlyDB_%s.db' %metric
        dbpath = os.path.join(self.dbdir, dbname)
        db = sqlite3.connect(dbpath)
        cursor = db.cursor()
        #create tables
        self.createMetricsTable(metric)
        for stock in stockset:
            try:
                stockdata = self.loadStockdataH5(stock, metric)
            except KeyError:
                print('%s: data object contains no data for %s' %(metric.title(), stock))
                continue
            for timepoint in self.timepoints:
                batches = stockdata[timepoint].keys()
                batchdata = stockdata[timepoint].items()
                batchdata = [[zip([(stock, timepoint, batch, i+1)]*len(repeat), repeat) for i, repeat in enumerate(repeats)] for (batch, repeats) in batchdata]
                batchdata = [[[(a,b,c,d,val) for ((a,b,c,d), val)in repeat] for repeat in batch] for batch in batchdata]
                for i, batch in enumerate(batchdata):
                    print('Inserting (%s, %s, %s)' %(stock, timepoint, batches[i])) 
                    for repeat in batch:
                        insertStatement = '''INSERT INTO %s (Stock, Day, Batch, Repeat, %s) VALUES(?,?,?,?,?)''' %(metric, self.columnsDict[metric])
                        cursor.executemany(insertStatement, repeat)
                db.commit()
        db.close()  
        return 



class DataVis(iFlyObj):
    
    def __init__(self):
        iFlyObj.__init__(self)
        self.labelsDict = {'velocities':'speed', 'dist2e':'end-to-end distance', 'angle':'angle of movement', 'angleInt':'angle interaction'}
        return
    
    
    def fetchStockdataToPlot(self, stock, metric):
        from itertools import chain
        stockdataDict = self.loadStockdataDict()
        data = [stockdataDict[stock][metric][timepoint].values() for timepoint in self.timepoints]
        data = [[zip(*batch) for batch in timepoint] for timepoint in data]
        data = [zip(*timepoint) for timepoint in data]
        data_8, data_22 = [[list(chain(*param)) for param in timepoint] for timepoint in data]
        return data_8, data_22    
        
    
    def loadDatasetData(self, metric):
        from statsFunctions import weighted_avg_and_sem
        #load batchdata object
        batchdataDict = self.loadBatchdataDict()
        #retrieve data from batchdata object
        data, stocklist = [[[[] for j in xrange(len(self.batchnumbers))] for i in xrange(len(self.timepoints))] for z in xrange(2)]
        for i, timepoint in enumerate(self.timepoints):
            for j, batchnumber in enumerate(self.batchnumbers):
                batchdata = batchdataDict[metric][timepoint][batchnumber].values()
                stockset_batch = batchdataDict[metric][timepoint][batchnumber].keys()
                for z, stock in enumerate(batchdata):
                    try:
                        means, serr, size = zip(*stock)
                        weights = [val/float(sum(size)) for val in size]
                        average, sem = weighted_avg_and_sem(means, weights)#weighted means
                        data[i][j].append([average, sem])
                        stocklist[i][j].append(stockset_batch[z])
                    except KeyError:
                        continue
        return data, stocklist
        
    
    def stockPlotter(self, stock, metric):
        import seaborn as sns
        import matplotlib.pyplot as plt
        from itertools import chain
        #load stocks data
        if isinstance(stock, (list, tuple)):
            ctrldata, testdata = [self.fetchStockdataToPlot(name, metric) for name in stock]
        elif isinstance(stock, str):
            stocklist = ['Empty', stock] 
            ctrldata, testdata = [self.fetchStockdataToPlot(name, metric) for name in stocklist]
        #unpack data
        ctrldata_8, ctrldata_22 = ctrldata; testdata_8, testdata_22 = testdata
        #define data to plot
        means = [ctrldata_8[0], testdata_8[0], ctrldata_22[0], testdata_22[0]]
        yset = ctrldata_8[0] + testdata_8[0] + ctrldata_22[0] + testdata_22[0]
        xset = list(chain(*[[i+1]*len(means[i]) for i in xrange(4)]))
        hue = list(chain(*[[val]*len(means[i]) for i, val in enumerate([1,2]*2)]))
        #define plot
        fig, ax = plt.subplots(1,1)
        sns.swarmplot(x = xset, y = yset, s = 5, hue = hue, ax = ax, zorder = -1)
        #plot means for each timepoint
        averages = [np.mean(arr) for arr in means]
        ax.scatter(np.arange(len(means)), averages, color = '#000000', s = 25, marker = '*', zorder = 1)
        #set axis limits
        ax.set_ylim([0, ax.get_ylim()[1]])
        #set ticks and labels
        labels = ['Day%i' %timepoint for timepoint in Dashboard().timepoints]
        ax.set_xticks([0.5, 2.5])
        ax.set_xticklabels(labels, rotation = 60, fontsize = 12)
        ax.set_ylabel('%s' %self.labelsDict[metric], fontsize = 14)
        #set legend
        ax.legend(stocklist, fontsize = 12)
        plt.show()
        return 
                   
    
    def stockBatchPlotter(self,stock, metric, batch, scale = False, bins = 'knuth'):
        from Plot_Functions import colorMap
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d import Axes3D 
        from scipy import stats
        from astropy.stats import histogram
        #define timepoints and load data object           
        stockdata = self.loadStockdataH5(stock, metric)
        stockdata = [stockdata[timepoint][batch] for timepoint in self.timepoints]
        #data transformation
        if metric == 'velocities':
            stockdata = [[stats.boxcox(arr) for arr in timepoint] for timepoint in stockdata]
            stockdata = [zip(*timepoint)[0] for timepoint in stockdata]
        #figure definition
        fig = plt.figure(facecolor = 'white')
        #plots definitions
        hrange = [[0,1.0], [0.1, 0.8]]
        for i, timepoint in enumerate(stockdata):    
            #histograms
            histdata, bin_edges = zip(*[histogram(arr, bins = bins) for arr in timepoint])
            #define bin centers
            dx = [(arr[1]-arr[0])/2.0 for arr in bin_edges]
            binCenters = [[val+dx[idx] for val in arr[:-1]] for idx, arr in enumerate(bin_edges)]
            #Generate colorMaps
            step = len(histdata)
            rgbaColorMap = colorMap(step, 0.8, 0.8, hrange = hrange[i])
            #bar plot definition
            ax = fig.add_subplot(1,2,i+1, projection = '3d'); z = np.arange(1, len(histdata)+1)
            for j, hist in enumerate(histdata):
                ax.bar(binCenters[j], hist, zs=z[j], zdir='y', width = dx[j]*1.8, color=rgbaColorMap[j])
            #set xaxis labels
            if metric == 'angleInt':
                ax.set_xlabel('%s index' %self.labelsDict[metric])
            elif metric in ['dist2e', 'angle']:
                ax.set_xlabel('%s' %self.labelsDict[metric])
            else:
                ax.set_xlabel('%s (log)' %self.labelsDict[metric])
            #set plot title
            ax.set_title('Day%i' %self.timepoints[i], fontsize = 12, position = (0.8, 0.8))
        #set limits
        if scale:
            limits = np.asarray([(ax.get_xlim3d()[1], ax.get_zlim3d()[1]) for ax in fig.get_axes()])
            xf, zf = np.subtract(*limits)
            [ax.set_xlim([-2, limits[0][0]]) if xf > 0 else ax.set_xlim([-2, limits[1][0]]) for ax in fig.get_axes()]
            [ax.set_zlim([-2, limits[0][1]]) if zf > 0 else ax.set_zlim([-2, limits[1][1]]) for ax in fig.get_axes()]
        #set y,z axis labels
        [(ax.set_ylabel('Repeats'), ax.set_zlabel('Ocurrences')) for ax in fig.get_axes()] 
        #set axis tick labels size and padding
        axisIDs = ['x', 'y', 'z']
        [ax.tick_params(axis=Id, which='major', labelsize = 9, pad = 0.5) for Id in axisIDs for ax in fig.get_axes()]    
        #set figure title
        fig.suptitle('%s: %s histograms' %(stock, self.labelsDict[metric]), fontsize = 13)
        plt.tight_layout(); plt.show()
        return


    def batchPlotter(self, metric, scale = False):
        from Plot_Functions import colorMap
        import matplotlib.pyplot as plt
        '''Batch plotter implement controls option.'''
        #load batchdata object
        data, stocklist = self.loadDatasetData(metric)
        data = [[zip(*batch) for batch in data_timepoint] for data_timepoint in data]#unpack data
        #figure definition
        fig = plt.figure(facecolor = 'white')
        #Generate colorMaps
        step = len(self.batchnumbers)
        rgbaColorMap = colorMap(step, 0.8, 0.8)
        #plots definitions
        ax = plt.subplot(211)
        xset = np.arange(1, len(self.batchnumbers)+1)
        for j, timepoint in enumerate(data):
            ax = fig.add_subplot(2,1,j+1)
            for i, batch in enumerate(timepoint):
                means, serr = batch
                x = [xset[i]]*len(means); batch_mean = (np.mean(means))
                ax.scatter(x, means, s = 20, c = rgbaColorMap[i])
                ax.scatter(x[0], batch_mean, s = 100, c = 'r', marker = '_')
                ax.set_title('Day%i' %self.timepoints[j], fontsize = 11, position = (0.95, 0.85))
        #set ylimits
        limits = np.asarray([(ax.get_xlim()[1], ax.get_ylim()[1]) for ax in fig.get_axes()])
        xf, yf = np.subtract(*limits)
        if scale:
            [ax.set_ylim([0, limits[0][1]]) if yf > 0 else ax.set_ylim([0, limits[1][1]]) for ax in fig.get_axes()]
        else:
            [ax.set_ylim([0, limits[i][1]]) for i, ax in enumerate(fig.get_axes())]
        #set xlimits
        [ax.set_xlim([0, len(self.batchnumbers) + 1]) for ax in fig.get_axes()]
        #set xtick labels
        [ax.set_xticks(xset) for ax in fig.get_axes()]
        [ax.set_xticklabels([]) for i, ax in enumerate(fig.get_axes()) if i==0]
        #set axis labels
        [ax.set_ylabel('%s' %self.labelsDict[metric]) for ax in fig.get_axes()]
        ax.set_xlabel('Batches')
        #set figure title
        fig.suptitle('%s: batch variation' %(self.labelsDict[metric]), fontsize = 13)
        plt.show()
        return


    def datasetPlotter(self, metric, fitbound, controls = False):
        '''Implement dynamic labelling of data.'''
        import seaborn as sns
        from statsFunctions import pointInEllipse
        import matplotlib.pyplot as plt
        from matplotlib.patches import Ellipse
        from astroML.stats import fit_bivariate_normal
        from itertools import chain
        #load dataset data
        data, stocklist = self.loadDatasetData(metric)
        #unpack data
        data = [[zip(*batch) for batch in timepoint] for timepoint in data]
        data_8, data_22 = [zip(*timepoint) for timepoint in data]
        #flatten data
        means_8 = list(chain(*data_8[0])); means_22 = list(chain(*data_22[0]))
        stockset = list(chain(*stocklist[0]))
        # compute non-robust and robust statistics
        (mu_nr, sigma1_nr,sigma2_nr, alpha_nr) = fit_bivariate_normal(means_8, means_22, robust=False)
        (mu_r, sigma1_r,sigma2_r, alpha_r) = fit_bivariate_normal(means_8, means_22, robust=True)
        #plots definitions
        fig, ax = plt.subplots(1,1)
        # Draw elipses showing the fits
        for Nsig in [fitbound]:
            #Non-robust fit
            E_nr = Ellipse(mu_nr, sigma1_nr * Nsig, sigma2_nr * Nsig,
                        (alpha_nr * 180. / np.pi),
                        ec='g', fc='none', linestyle='dotted', lw=1.5)
            ax.add_patch(E_nr)
            #Robust fit
            E_r = Ellipse(mu_r, sigma1_r * Nsig, sigma2_r * Nsig,
                        (alpha_r * 180. / np.pi),
                        ec='r', fc='none', linestyle='dashed')
            ax.add_patch(E_r)
        #define color depending if point in ellipse
        xytuples = zip(means_8, means_22)
        x,y = mu_nr; d, D = (sigma1_nr * Nsig, sigma2_nr * Nsig); angle = (alpha_nr * 180. / np.pi)
        colorsizes = [('#C3CFDE', 8) if pointInEllipse(x,y,xp,yp,d,D,angle - 0.9) else ('#DE43C7', 14) for (xp,yp) in xytuples]
        #define color for controls
        if controls:
            posControls_idx = [i for i, stock in enumerate(stockset) if stock == 'Pink']
            negControls_idx = [i for i, stock in enumerate(stockset) if stock == 'Empty']
            colorsizes = [('b', 14) if i in posControls_idx else tupl for i, tupl in enumerate(colorsizes)]
            colorsizes = [('g', 14) if i in negControls_idx else tupl for i, tupl in enumerate(colorsizes)]
        colors, sizes = zip(*colorsizes)
        #scatter plot definition
        ax.scatter(means_8, means_22, c = colors, s = sizes, alpha= 0.8)
        #set axis limits
        xmin, xmax = ax.get_xlim(); ymin, ymax = ax.get_ylim()
        ax.set_xlim([-1, xmax]); ax.set_ylim([-1, ymax])
        #set axis labels
        [ax.set_xlabel('Day%i' %self.timepoints[0]), ax.set_ylabel('Day%i' %self.timepoints[1])]
        #set legend
        ax.legend((E_nr, E_r),('non-robust fit', 'robust fit'), fontsize = 11, loc = 'lower right')
        #set title
        plt.title('Climbing speeds', fontsize = 14)
        plt.show()
        return
        
        

#stock, metric, batch = ('Pink', 'angle', 9)    
#DataVis().stockBatchPlotter(stock, metric, batch, scale = True, bins = 'knuth')
#metric = 'angle'
#DataVis().batchPlotter(metric, scale = True)
#metric = 'velocities'; fitbound = 3.0
#DataVis().datasetPlotter(metric, fitbound, controls = True)
#stock = 'w1118'; metric = 'velocities'
#DataVis().stockPlotter(stock, metric)
#stockdata = iFlyObj().loadStockdataH5('Hand', 'velocities')


