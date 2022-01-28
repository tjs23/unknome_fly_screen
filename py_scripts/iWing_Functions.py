import os
import sys

class Dashboard():
    
    def __init__(self):
        cwd = os.getcwd()
        self.cwd = cwd
        self.dbdir = '%s\Dropbox\Unknome\Databases' %self.cwd
        self.dbpath = os.path.join(self.dbdir, 'WingsDB.db')
        self.basedir = 'U:\Wing screen'
        self.rajendir = '%s\Dropbox\Unknome\Screens\Outliers\RajenAnalysis' %self.cwd
        self.wingsdir = '%s\Dropbox\Unknome\Screens\WingScreen\PyWings' %self.cwd
        self.rawdatadir = os.path.join(self.wingsdir, 'RawData')
        self.pickledir = os.path.join(self.wingsdir, 'PickleFiles')
        self.workdir = os.path.join(self.wingsdir, 'FilesOut')
        self.controlsDict = self.controlsDict()
        self.ctrlnames = self.controlsNames()
        self.valRNAi = self.validationRNAis().values()
    
    def getMembers(self):
        import inspect
        methods = inspect.getmembers(self, predicate = inspect.ismethod)
        print(methods)
        return
        
    def controlsDict(self):
        #Define dictionary
        controlsDict = {'EMPTY': 'Empty', 'GFPI(9)': 'GFPi(9)', 'W1118': 'w1118', 'CHO': 'cho', 'HPO': 'hpo', 'LNK': 'lnk'}           
        return controlsDict
            
    def controlsNames(self):
         ctrlnames = self.controlsDict.values()
         return ctrlnames
    
    def validationRNAis(self):
        valRNAiDict = {'JS36': '9213R2', 'JS353': '50671', 'JS10': '50596', 'JS2': ('4662R3', '4662R4'), 'JS24': '42896', 'JS125': '40946', 'JS256': '31224', 'JS121': '17157'}
        return valRNAiDict     
         
    def loadBatchlist(self):
        import sqlite3
        #connect to database
        db = sqlite3.connect(self.dbpath)
        cursor = db.cursor()
        #fetch data
        cursor.execute('''SELECT Batch FROM Wings''' )
        data = cursor.fetchall()
        db.close()
        #extract batchlist from data
        batchlist = []
        for tupl in data:
            if tupl not in batchlist:
                batchlist.append(tupl)
        batchlist = [tupl[0] for tupl in batchlist]#unpack
        return batchlist

        
    def loadStockset(self):
        from File_Functions import listPartition
        import sqlite3
        #load batchlist
        batchlist = self.loadBatchlist()
        #connect to database
        db = sqlite3.connect(self.dbpath)
        cursor = db.cursor()
        #fetch data
        cursor.execute('''SELECT Batch, Stock FROM Wings''' )
        data = cursor.fetchall()
        db.close()
        #cluster stocks according to batches
        stockset = [[tupl[1] for tupl in data if tupl[0] == batch] for batch in batchlist]
        clusterStockset = [list(set(batch)) for batch in stockset]
        #split controls from stockset
        clusterStockset = [listPartition(lambda x: x.startswith('JS'), batch) for batch in clusterStockset]
        clusterStockset = [[sorted(batch[0], key = lambda x: int(x[2:])), sorted(batch[1], key = lambda x: x)] for batch in clusterStockset]#sort sublists
        clusterStockset = [[val for sublist in batch for val in sublist] for batch in clusterStockset]#rejoin sorted sublists
        clusterStockset = zip(batchlist, clusterStockset)
        clusterStockset = dict(clusterStockset)
        return clusterStockset
        
    
    def purgePickleDir(self, fnum = 2):
        '''It purges pickledir of older file versions; fnum (int) defines the maximum number of file versions to keep.
        Pickle files purged are: wingsDict, wingMetrics, trimAreasArr, clusterWingdata, clusterImgdata and rajenDict.'''
        #Define filenames
        filenames = ['wingsDict', 'wingMetrics', 'trimAreasArr', 'clusterWingdata', 'clusterImgdata', 'rajenDict']
        #Fetch and sort filelist
        filelist = [[f for f in os.listdir(self.pickledir) if f.startswith(name)] for name in filenames]
        [sublist.sort() for sublist in filelist] #sort filelist
        #Purge filelist
        filelist_topurge = [sublist[:-fnum] for sublist in filelist]
        #Purge pickleDir
        [[os.remove(os.path.join(self.pickledir, filename)) for filename in sublist] for sublist in filelist_topurge]
        return
        
    def buildWingsDB(self):
        rows = WingsDB().fetchRows()
        WingsDB().createWingsDB(rows)
        WingsDB().createZscoresTable()
        WingsObjects().buildWingsDict()
        WingsObjects().buildAreasTrimObject()
        WingsDB().createZscoresTable()
        return
                    
    def resetMetrics(self):
        WingsObjects().buildClusterWingObject()
        WingsObjects().buildWingMetricsDict()
        WingsObjects().buildImageDict()
        WingsObjects().buildRajenDict()
        self.purgePickledir()
        return
    
    def resetWorkEnv(self):
        self.buildWingsDB()
        self.resetMetrics()
        return



class WingsDB(Dashboard):
    
    def __init__(self):
        Dashboard.__init__(self)
    
    def getMembers(self):
        import inspect
        methods = inspect.getmembers(self, predicate = inspect.ismethod)
        print(methods)
        return
                 
    def fetchRows(self, textpath):
        import pandas as pd 
        #fetch column headings
        textpath = os.path.join(self.rawdatadir, 'Wings_rawdata.txt')
        with open(textpath, 'r') as f:
            colheads = f.readline()[:-1]
            colheads = colheads.split('\t')
        df = pd.read_csv(textpath, delimiter = '\t')
        data = [df[head] for head in colheads]
        rows = zip(*data)
        #convert datatypes
        rows = [(batch, filename, stock, int(AreaA), int(AreaP), float(AreaP)/AreaA, Comments) for (batch, filename, stock, AreaA, AreaP, Comments) in rows]
        return rows
            
            
    def createWingsTable(self, tablename):
        import sqlite3
        #Connect to database
        db = sqlite3.connect(self.dbpath)
        cursor = db.cursor()
        print('Creating table %s. \n' %tablename)
        createStatement = '''CREATE TABLE  %s (sqlKey INTEGER PRIMARY KEY AUTOINCREMENT, Batch TEXT NOT NULL, Filename CHAR(50) NOT NULL, 
                            
                            Stock CHAR(50) NOT NULL, AreaA INT NOT NULL, AreaP INT NOT NULL, AreaR REAL NOT NULL, Comments TEXT NOT NULL)''' %tablename       
        cursor.execute(createStatement)
        return 
    
    
    def createWingsDB(self, rows):
        import sqlite3             
        #Connect to database
        db = sqlite3.connect(self.dbpath)
        cursor = db.cursor()
        #define tablenames
        tablenames = ['Wings']
        if len(tablenames) == 1:
            rows = [rows]       
        for i, tablename in enumerate(tablenames):
            self.createWingsTable(tablename)
            insertStatement = '''INSERT INTO %s (Batch, Filename, Stock, AreaA, AreaP, AreaR, Comments) VALUES(?,?,?,?,?,?,?)''' %tablename 
            print('Inserting data in table %s. \n' %tablename)
            cursor.executemany(insertStatement, rows[i])
            db.commit()
            db.close()
            return


    def createZscoresTable(self):
        import sqlite3
        #Connect to database
        db = sqlite3.connect(self.dbpath)
        cursor = db.cursor()
        #create table
        tablename = 'zScores'
        createStatement = '''CREATE TABLE  %s (zKey TEXT NOT NULL, zA REAL NOT NULL, zP REAL NOT NULL, zR REAL NOT NULL)''' %tablename
        cursor.execute(createStatement)
        #calculate z scores
        zLists = WingMetrics().calculateAreasZscores()
        #parse rows
        zkey, zArrs = zLists #unpack
        rows = [(zkey[i], zA, zP, zR) for i, (zA, zP, zR) in enumerate(zip(*zArrs))]
        #insert data
        insertStatement = '''INSERT INTO zScores (zKey, zA, zP, zR) VALUES(?,?,?,?)'''
        cursor.executemany(insertStatement, rows)
        db.commit()
        db.close()
        return
        
    
    def createMetricsTable(self):
        import sqlite3
        #load data objects
        wingMetrics = WingsObjects().loadWingMetrics()
        stockset = self.loadStockset()
        batchlist = self.loadBatchlist()
        #parse rows
        rows = []
        for batch in batchlist:
            for stock in stockset[batch]:
                 arrA, arrP, arrR = wingMetrics[batch][stock]
                 meanA, errA, pA, zA = arrA
                 meanP, errP, pP, zP = arrP
                 meanR, errR, pR, zR = arrR
                 row = (stock, batch, meanA, errA, pA, zA, meanP, errP, pP, zP, meanR, errR, pR, zR)
                 rows.append(row)                  
        #Connect to database
        db = sqlite3.connect(self.dbpath)
        cursor = db.cursor()
        #create table
        tablename = 'WingMetrics'
        createStatement = '''CREATE TABLE  %s (Stock TEXT NOT NULL, Batch TEXT NOT NULL, meanA INT NOT NULL, errA REAL NOT NULL, pA REAL NOT NULL, zA REAL NOT NULL,
                            
                            meanP INT NOT NULL, errP REAL NOT NULL, pP REAL NOT NULL, zP REAL NOT NULL,
                            
                            meanR INT NOT NULL, errR REAL NOT NULL, pR REAL NOT NULL, zR REAL NOT NULL)''' %tablename                    
        cursor.execute(createStatement)
        #insert data
        insertStatement = '''INSERT INTO WingMetrics (stock, batch, meanA, errA, pA, zA, meanP, errP, pP, zP, meanR, errR, pR, zR) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)'''
        cursor.executemany(insertStatement, rows)
        db.commit()
        db.close()
        return
          
               

class WingsObjects(Dashboard):
    
    def __init__(self):
        Dashboard.__init__(self)
    
    def getMembers(self):
        import inspect
        methods = inspect.getmembers(self, predicate = inspect.ismethod)
        print(methods)
        return
        
    def buildWingsDict(self):
        from collections import OrderedDict
        from datetime import datetime
        import cPickle as pickle
        import sqlite3
        #connect to database
        db = sqlite3.connect(self.dbpath)
        cursor = db.cursor()
        #fetch tablenames from database
        tablenames = ['Wings', 'zScores']
        #fetch data from database
        data = []
        for tablename in tablenames:
            cursor.execute('''SELECT * FROM %s''' %tablename)
            tabledata = cursor.fetchall()
            data.append(tabledata)
        db.close()    
        #parse data
        zipdata = zip(*data) #zip data
        zipdata = [[val for item in tupl for val in item] for tupl in zipdata]#unpack
        [sublist.pop(8) for sublist in zipdata]
        zipdata = [(item[0], item[1:]) for item in zipdata]
        #Fetch current time and date
        time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        #serialise dictionary
        wingsDict = OrderedDict(zipdata)
        picklepath = os.path.join(self.pickledir, 'wingsDict_%s.pickle' %time)
        with open(picklepath, 'wb') as f:
            pickle.dump(wingsDict, f, protocol = 2)
        return
        
  
    def loadWingsDict(self):
        import cPickle as pickle
        #load lists
        filelist = [filename for filename in os.listdir(self.pickledir) if filename.startswith('wingsDict')]
        filelist.sort()
        picklefile = filelist[-1]
        picklepath = os.path.join(self.pickledir, picklefile)
        with open(picklepath, 'rb') as f:
            wingsDict = pickle.load(f)
        return wingsDict
        
        
    def buildAreasTrimObject(self):
        from statsFunctions import zTrim
        import cPickle as pickle
        from datetime import datetime
        #load arrays
        zArrs = self.fetchZArrs()
        areaArrs = self.loadAreasArrs()
        ctrlkeys = self.fetchControlSQLkeys()
        #parse ctrlkeys
        ctrlkeys = zip(*ctrlkeys)[1]
        ctrlIdx = [val-1 for control in ctrlkeys for val in control]     
        #Trim areas and ratio arrays and filter out controls
        dataIdx_trim = zTrim(zArrs, zscore = 2.5, output = 'non-outlier')
        dataIdx_trim = [[val for val in arr if val not in ctrlIdx] for arr in dataIdx_trim]#Filter out controls
        areaArrs_trim = [[val for j, val in enumerate(arr) if j in dataIdx_trim[i]] for i, arr in enumerate(areaArrs)]
        #Fetch current time and date
        time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        #pickle trimmed arrays
        areaA_trim, areaP_trim, areaR_trim = areaArrs_trim
        picklepath = os.path.join(self.pickledir, 'trimAreaArrs_%s.pickle' %time)
        with open(picklepath, 'wb') as f:
            pickle.dump(areaArrs_trim, f, protocol = 2)
        return

                                                                                                                              
    def loadTrimmedAreas(self):
        import cPickle as pickle
        #load lists
        filelist = [filename for filename in os.listdir(self.pickledir) if filename.startswith('trimAreaArrs')]
        filelist.sort()
        picklefile = filelist[-1]
        picklepath = os.path.join(self.pickledir, picklefile)
        with open(picklepath, 'rb') as f:
            areaArrs_trim = pickle.load(f)
        return areaArrs_trim
        
    
    def buildClusterWingObject(self):
        import cPickle as pickle
        from datetime import datetime
        #load data
        wingsDict = self.loadWingsDict()
        wingdata = wingsDict.values()
        batchlist = self.loadBatchlist()
        clusterStockset = self.loadStockset()
        #cluster data
        clusterdata = [[tupl for tupl in wingdata if tupl[0] == batch] for batch in batchlist]
        clusterdata = [[(stock, [(tupl[3], tupl[4], tupl[5]) for tupl in batch if tupl[2] == stock]) for stock in clusterStockset[batchlist[i]]] for i, batch in enumerate(clusterdata)]
        clusterdata = [[(stock, zip(*arrs)) for (stock, arrs) in batch] for batch in clusterdata]
        clusterdata = [dict(batch) for batch in clusterdata]
        clusterdata = dict(zip(batchlist, clusterdata))
        #Fetch current time and date
        time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        #pickle dictionary
        picklepath = os.path.join(self.pickledir, 'clusterWingdata_%s.pickle' %time)
        with open(picklepath, 'wb') as f:
            pickle.dump(clusterdata, f, protocol = 2) 
        return
        
        
    def loadClusterWingdata(self):
        import cPickle as pickle
        filelist = [filename for filename in os.listdir(self.pickledir) if filename.startswith('clusterWingdata')]
        filelist.sort()
        picklefile = filelist[-1]
        picklepath = os.path.join(self.pickledir, picklefile)
        with open(picklepath, 'rb') as f:
            clusterWingdata = pickle.load(f) 
        return clusterWingdata
        
        
    def buildImageDict(self):
        import cPickle as pickle
        from datetime import datetime
        #load data
        wingsDict = self.loadWingsDict()
        wingdata = wingsDict.values()
        batchlist = self.loadBatchlist()
        clusterStockset = self.loadStockset()
        #cluster data
        clusterdata = [[tupl for tupl in wingdata if tupl[0] == batch] for batch in batchlist]
        clusterdata = [[(stock, [tupl[1] for tupl in batch if tupl[2] == stock]) for stock in clusterStockset[batchlist[i]]] for i, batch in enumerate(clusterdata)]
        clusterdata = [dict(batch) for batch in clusterdata]
        clusterdata = dict(zip(batchlist, clusterdata))
        #Fetch current time and date
        time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        #pickle dictionary
        picklepath = os.path.join(self.pickledir, 'clusterImgdata_%s.pickle' %time)
        with open(picklepath, 'wb') as f:
            pickle.dump(clusterdata, f, protocol = 2)   
        return
        
        
    def loadImageDict(self):
        import cPickle as pickle
        filelist = [filename for filename in os.listdir(self.pickledir) if filename.startswith('clusterImgdata')]
        filelist.sort()
        picklefile = filelist[-1]
        picklepath = os.path.join(self.pickledir, picklefile)
        with open(picklepath, 'rb') as f:
            clusterImgDict = pickle.load(f)
        return clusterImgDict    
        
        
    def buildWingMetricsDict(self):
        from collections import OrderedDict
        from datetime import datetime
        from statsFunctions import statsZscores
        import cPickle as pickle
        import numpy as np
        from scipy import stats
        #load data
        clusterdata = self.loadClusterWingdata()
        trimArrs = self.loadTrimmedAreas()
        stockset = self.loadStockset()
        batchlist = self.loadBatchlist()
        #calculate metrics
        wingMetrics = OrderedDict()
        meansArr = []
        for batch in batchlist:
            wingMetrics[batch] = OrderedDict()
            for stock in stockset[batch]:
                means = [np.mean(arr) for arr in clusterdata[batch][stock]]
                sem = [stats.sem(arr) for arr in clusterdata[batch][stock]]
                pAreas = [stats.ttest_ind(arr, trimArrs[i], equal_var=True)[1] for i, arr in enumerate(clusterdata[batch][stock])]
                meansArr.append((batch, stock, means))
                zipdata = zip(*[means, sem, pAreas])
                wingMetrics[batch][stock] = zipdata
        #calculate zscores
        batch, stock, means = zip(*meansArr)
        meanA, meanP, meanR = zip(*means)
        zArrs = statsZscores([meanA, meanP, meanR])
        #parse zscores
        zA, zP, zR = zArrs
        ztuples = zip(*[batch, stock, zA, zP, zR])
        #update wingMetrics dictionary
        for tupl in ztuples :
            (batch, stock, zA, zP, zR) = tupl
            [arrA, arrP, arrR] = wingMetrics[batch][stock]
            arrA = arrA + (zA,)
            arrP = arrP + (zP,)
            arrR = arrR + (zR,)
            wingMetrics[batch][stock] = [arrA, arrP, arrR]
        #Fetch current time and date
        time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        #pickle wingMetrics dictionary
        picklepath = os.path.join(self.pickledir, 'wingMetrics_%s.pickle' %time)
        with  open(picklepath, 'wb') as f:
            pickle.dump(wingMetrics, f, protocol = 2)
        return
        
    
    def loadWingMetrics(self):
        import cPickle as pickle
        filelist = [filename for filename in os.listdir(self.pickledir) if filename.startswith('wingMetrics')]
        filelist.sort()
        picklefile = filelist[-1]
        picklepath = os.path.join(self.pickledir, picklefile)
        with open(picklepath, 'rb') as f:
            wingMetrics = pickle.load(f)
        return wingMetrics
        
        
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            
class WingMetrics(WingsObjects):
    
    def __init__(self):
        WingsObjects.__init__(self)
        
    
    def getMembers(self):
        import inspect
        methods = inspect.getmembers(self, predicate = inspect.ismethod)
        print(methods)
        return                                                          
                                               
    def loadAreasArrs(self):
        #load wings dictionary
        wingsDict = self.loadWingsDict()
        wingdata = wingsDict.values()
        #extract arrays
        areaArrs = zip(*wingdata)[3:6]
        return areaArrs
        
    def calculateAreasZscores(self):
        from statsFunctions import statsZscores
        import sqlite3
        #connect to database
        db = sqlite3.connect(self.dbpath)
        cursor = db.cursor()
        #fetch areas from database
        cursor.execute('''SELECT Stock, sqlKey, AreaA, AreaP, AreaR FROM Wings''')
        data = cursor.fetchall()       
        data = [('%s_%s' %(stock, sqlkey), areaA, areaP, areaR)  for (stock, sqlkey, areaA, areaP, areaR) in data]
        db.close()
        #rearrange data
        arrs = zip(*data)
        zkey, arrA, arrP, arrR = arrs
        #Calculate zscores
        zArrs = statsZscores([arrA, arrP, arrR])
        zLists = [zkey, zArrs]
        return zLists              
                  
    def fetchZArrs(self):
        import sqlite3
        #connect to database
        db = sqlite3.connect(self.dbpath)
        cursor = db.cursor()
        #fetch data
        cursor.execute('''SELECT * FROM zScores''' )
        data = cursor.fetchall()
        db.close()
        #parse data
        zkey, zA, zP, zR  = zip(*data)
        zArrs = [zA, zP, zR]
        return zArrs 
        
                                                           
    def fetchControlSQLkeys(self):
        #load wings dictionary
        wingsDict = self.loadWingsDict()
        wingdata = wingsDict.values()
        #extract keys
        ctrlSQLkey = [(name, [i+1 for i, tupl in enumerate(wingdata) if tupl[2] == name]) for name in self.ctrlnames]
        return ctrlSQLkey
  
        
    def fetchWingMetricsArrays(self):
        #load data
        wingMetrics = self.loadWingMetrics()
        #unpack arrays from metrics data
        metricsData = wingMetrics.values()#stocks in bacthes
        metricsData = [sublist.values() for sublist in metricsData] #stocks
        metricsData = [val for sublist in metricsData for val in sublist]#unpack
        zipdata = zip(*metricsData)
        zipdata = [zip(*arr) for arr in zipdata]
        metricsArrs = arrA, arrP, arrR = zipdata
        return metricsArrs
        
    
    def fetchDatasetMeans(self):
        from statsFunctions import zTrim
        from scipy import stats
        import numpy as np
        #load data
        stockset = self.loadStockset()
        batchlist = self.loadBatchlist()
        #filter out controls from stockset
        stockset = [stockset[batch] for batch in batchlist]
        stockset = [stock for batch in stockset for stock in batch]
        stockset_trim_idx = [i for i, stock in enumerate(stockset) if stock not in self.ctrlnames]
        #load arrays and unpack
        metricsArrs = self.fetchWingMetricsArrays()
        arrA, arrP, arrR = metricsArrs
        meanA, errA, pA, zA = arrA
        meanP, errP, pP, zP = arrP
        #trim z arrays
        zArrs = [zA, zP]
        meanArrs = [meanA, meanP]
        dataIdx_trim = zTrim(zArrs, zscore = 2.5, output = 'non-outlier')
        meanArrs_trim = [[(j, mean) for j, mean in enumerate(arr) if j in dataIdx_trim[i]] for i, arr in enumerate(meanArrs)]#filter mean arrays
        meanArrs_trim = [[mean for (j, mean) in arr if j in stockset_trim_idx] for arr in meanArrs_trim]#filter out controls
        #calculate dataset means
        dsetMeans = [np.mean(arr) for arr in meanArrs_trim]
        dsetErr = [stats.sem(arr) for arr in meanArrs_trim] 
        dsetMetrics = [dsetMeans, dsetErr]
        return dsetMetrics

                      
    def fetchOutliers(self):
        from statsFunctions import zTrim
        #load data
        stockset = self.loadStockset()
        batchlist = self.loadBatchlist()
        metricsArrs = self.fetchWingMetricsArrays()
        #unpack stockset
        stockset = [stockset[batch] for batch in batchlist]
        stockset = ['%s_%s' %(stock, batchlist[i]) for i, batch in enumerate(stockset) for stock in batch]
        #unpack metrics arrays
        arrA, arrP, arrR = metricsArrs
        meanA, errA, pA, zA = arrA
        meanP, errP, pP, zP = arrP
        meanR, errR, pR, zR = arrR
        #filter out outliers
        zArrs = [zA, zP, zR]
        outlierIdx = zTrim(zArrs, zscore = 2.5, output = 'outlier')
        outliers = [[stockset[val] for val in arr] for arr in outlierIdx] 
        return outliers
              
        
    def fetchHits(self):
        from statsFunctions import statsFDR
        #load data
        stockset = self.loadStockset()
        batchlist = self.loadBatchlist()
        metricsArrs = self.fetchWingMetricsArrays()
        #unpack stockset
        stockset = [stockset[batch] for batch in batchlist]
        stockset = ['%s_%s' %(stock, batchlist[i]) for i, batch in enumerate(stockset) for stock in batch]
        #unpack metrics arrays
        arrA, arrP, arrR = metricsArrs
        meanA, errA, pA, zA = arrA
        meanP, errP, pP, zP = arrP
        meanR, errR, pR, zR = arrR
        #calculate FDR
        pList = [pA, pP, pR]
        fdrHits = statsFDR(pList, stockset)   
        return fdrHits
        
    def fetchMixedStocks(self):
        import sqlite3
        #connect to database
        db = sqlite3.connect(self.dbpath)
        cursor = db.cursor()
        #fetch mixed stocks from database
        cursor.execute('''SELECT Stock, Batch, Comments FROM Wings''')
        data = cursor.fetchall()       
        data = ['%s_%s' %(stock, batch)  for (stock, batch, comments) in data if comments == 'Mixed']
        db.close()
        #parse data
        mixedStockset = list(set(data))
        return mixedStockset
        
           
    def fetchRepeats(self, filterout = False):
        #load data
        assaylist = self.loadStockset()
        batchlist =self.loadBatchlist()
        mixedStockset = self.fetchMixedStocks()
        #parse assaylist and fetch list of stock repeats
        assaylist = [assaylist[batch] for batch in batchlist]
        assaylist = [item for batch in assaylist for item in batch]
        stockRepeats = list(set([item for item in assaylist if assaylist.count(item) > 1]))
        stockRepeats = [stock for stock in stockRepeats if stock not in self.ctrlnames]#filter out controls
        #fetch list of repeated assays
        repeatedAssays = [self.stockFetcher(stock) for stock in stockRepeats]
        if filterout == 'mixed':
            repeatedAssays = [[assay for assay in assaylist if assay[1] not in mixedStockset] for assaylist in repeatedAssays]
            repeatedAssays = [assaylist for assaylist in repeatedAssays if len(assaylist) > 1]#filterout repeats of mixed stocks
            stockRepeats = [assaylist[0][1].split('_')[0] for assaylist in repeatedAssays]
        repeatedAssays = [item for sublist in repeatedAssays for item in sublist]        

        repeats = [stockRepeats, repeatedAssays]
        return repeats
    
    
    def printRepeats(self, output = 'screen', filterout = False):
        from File_Functions import printList
        #fetch repeats
        repeats = self.fetchRepeats(filterout = filterout)
        stockRepeats, repeatedAssays = repeats
        stockRepeats = sorted(stockRepeats, key = lambda x:int(x[2:]))
        #print it
        if output == 'screen':
            printList(stockRepeats, 10)
        if output == 'file':
            path = os.path.join(self.workdir, 'repeatsList.txt')
            with open(path, 'w') as f:
                lines = '\n'.join(stockRepeats)
                f.writelines(lines)
        return
        
        
    def fetchMetricsForStockset(self, stockset):
        #load metrics dictionary
        wingMetrics = self.loadWingMetrics()
        if isinstance(stockset[0], (tuple, list)):
            keyset = [[(stock.split('_')[1], stock.split('_')[0]) for stock in subset] for subset in stockset]
            stocksetArrs = [[wingMetrics[batch][stock] for (batch, stock) in sublist] for sublist in keyset]
            stocksetArrs = [zip(*subset) for subset in stocksetArrs]
            stocksetArrs = [[zip(*arr) for arr in subset] for subset in stocksetArrs]
        elif isinstance(stockset[0], (str, unicode)):
            keyset = [(stock.split('_')[1], stock.split('_')[0]) for stock in stockset]
            stocksetArrs = [wingMetrics[batch][stock] for (batch, stock) in keyset]
            stocksetArrs = zip(*stocksetArrs)
            stocksetArrs = [zip(*arr) for arr in stocksetArrs]    
        return stocksetArrs
        
           
    def fetchRepeatsMetrics(self, filterout = False):
        #load data
        repeats = self.fetchRepeats(filterout = filterout)
        stockRepeats, repeatedAssays = repeats
        #parse list
        repAssayIDs = [assayID for (i, assayID) in repeatedAssays]
        #fetch repeats metrics
        repMetricArrs = self.fetchMetricsForStockset(repAssayIDs) 
        return repMetricArrs
        
        
    def fetchPhenoClasses(self):
        #load data
        stockset = self.loadStockset()
        batchlist = self.loadBatchlist()
        outliers = self.fetchOutliers()
        fdrHits = self.fetchHits()
        #unpack data
        out_zA, out_zP, out_zR = outliers
        outlierSet = set(out_zA + out_zP + out_zR)
        fdrA, fdrP, fdrR = fdrHits
        hitSet = set(fdrA + fdrP + fdrR)
        #parse stockset
        stockset = [stockset[batch] for batch in batchlist]
        stockset = ['%s_%s' %(stock, batchlist[i]) for i, batch in enumerate(stockset) for stock in batch]
        #outliers classes
        non_outliers = [key for key in stockset if key not in outlierSet]
        outlier_AP = [key for key in stockset if key in out_zA and key in out_zP]
        outlier_AnotP = [key for key in out_zA if key not in out_zP]
        outlier_PnotA = [key for key in out_zP if key not in out_zA]
        outlier_R = [key for key in stockset if key in outlierSet and (key not in out_zA and key not in out_zP)]
        #hits classes
        non_hit = [key for key in stockset if key not in hitSet]
        hit_AP = [key for key in stockset if key in fdrA and key in fdrP]
        hit_AnotP = [key for key in fdrA if key not in fdrP]
        hit_PnotA = [key for key in fdrP if key not in fdrA]
        hit_R = [key for key in stockset if key in hitSet and (key not in fdrA and key not in fdrP)]
        
        phenoclasses = {'outliers': [non_outliers, outlier_AP, outlier_AnotP, outlier_PnotA, outlier_R], 'hits': [non_hit, hit_AP, hit_AnotP, hit_PnotA, hit_R]}
        return phenoclasses
      
      
    def stockFetcher(self, stockID, output = None):
        #load data
        stockset = self.loadStockset()
        batchlist = self.loadBatchlist()
        #parse stockset
        stockset = [stockset[batch] for batch in batchlist]
        stockset = ['%s_%s' %(stock, batchlist[i]) for i, batch in enumerate(stockset) for stock in batch]
        #fecth stock
        stockID = stockID.upper()
        try:
            stockID = self.controlsDict[stockID]
            stockOut = [(i, stock) for i, stock in enumerate(stockset) if stock.startswith(stockID)]
        except KeyError:
            stockOut = [(i, stock) for i, stock in enumerate(stockset) if stock.split('_')[0] == stockID]
        
        while len(stockOut) == 0:
            stockInput = raw_input('Sorry, but this stock is not in the database! Please, choose a different stock or quit (q). \n')
            stockInput.upper()
            if stockInput == 'q':
                    sys.exit()   
            else:   
                stockOut = [(i, stock) for i, stock in enumerate(stockset) if stock.startswith(stockID)]     
        if output == 'screen':
            print(stockOut)
            
        return stockOut
    

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      
class WingDataVis(WingMetrics):
    
    def __init__(self):
        WingMetrics.__init__(self)
        self.binarydir = os.path.join(self.basedir, 'Binaries') 
        return
        
    def getMembers(self):
        import inspect
        methods = inspect.getmembers(self, predicate = inspect.ismethod)
        print(methods)
        return
        
    def fetchControlsIdx(self):
        #fetch controls indices
        controlsTuples = [self.stockFetcher(control) for control in self.ctrlnames]
        controlsTuples = [control for sublist in controlsTuples for control in sublist]
        
        return controlsTuples
            
    def arrayUnpacker(self, arrs):
        #dictionary keys
        classkeys = ['ns', 'AP', 'AnotP', 'PnotA', 'R']
        arrkeys = ['A', 'P', 'ratio']
        metrickeys = ['mean', 'err', 'p', 'z']
        
        #build dictionary
        arrayUnpacker = {}
        for i, subset in enumerate(arrs):
            arrayUnpacker[classkeys[i]] = {}
            for j, arr in enumerate(subset):
                arrayUnpacker[classkeys[i]][arrkeys[j]] = {}
                for z, metric in enumerate(arr):
                    arrayUnpacker[classkeys[i]][arrkeys[j]][metrickeys[z]] = metric
        return arrayUnpacker
        
    
    def generateColorMap(self, numbColors):
        from Plot_Functions import hsvGenerator
        from colorsys import hsv_to_rgb
        from matplotlib.colors import colorConverter
        cc = lambda arg: colorConverter.to_rgba(arg, alpha=0.6)
        step = 1/float(numbColors)
        hsvColorMap = hsvGenerator(step, 0.8, 0.8)
        rgbaColorMap = [cc(hsv_to_rgb(h,s,v)) for h,s,v in hsvColorMap]
        return rgbaColorMap 
        
    
    def datafeedForPlotter(self, stockID = False):
        #load data
        stockset = self.loadStockset()
        batchlist = self.loadBatchlist()
        wingMetrics = self.loadWingMetrics()
        metricsArrs = self.fetchWingMetricsArrays()
        phenoclasses = self.fetchPhenoClasses()
        #parse stockset
        stockset = [stockset[batch] for batch in batchlist]
        stockset = ['%s_%s' %(stock, batchlist[i]) for i, batch in enumerate(stockset) for stock in batch]
        #fetch stocks to plot
        if stockID:
            stocksOut = self.stockFetcher(stockID)#fetch stocks
        else:
            stocksOut = []
        #unpack phenoclasses
        outliers = phenoclasses['outliers']
        hits = phenoclasses['hits']
        #fetch metrics for phenoClasses
        outliers_arrs = self.fetchMetricsForStockset(outliers)
        hits_arrs = self.fetchMetricsForStockset(hits)
        #unpack arrays
        zArrs = self.arrayUnpacker(outliers_arrs)
        hArrs = self.arrayUnpacker(hits_arrs)
        #fetch dataset means
        dsetMetrics = self.fetchDatasetMeans()
        #pack data for plotter
        plotterData = [stockset, stocksOut, wingMetrics, metricsArrs, dsetMetrics, hArrs, zArrs]
        return plotterData
    
    
    def hitsLayout(self, args):
        #unpack args
        ax, hArrs, dsetMeans= args
        #hits        
        fdr_ns = ax.scatter(hArrs['ns']['A']['mean'], hArrs['ns']['P']['mean'], s = 6,  color = '#D1D1D1')
        fdr_AP = ax.scatter(hArrs['AP']['A']['mean'], hArrs['AP']['P']['mean'], s = 7,  color = 'b', alpha = 0.6)
        fdr_AnotP = ax.scatter(hArrs['AnotP']['A']['mean'], hArrs['AnotP']['P']['mean'], s = 7,  color = 'g', alpha = 0.6)
        fdr_PnotA = ax.scatter(hArrs['PnotA']['A']['mean'], hArrs['PnotA']['P']['mean'], s = 7,  color = '#F048E2', alpha = 0.6)
        fdr_R = ax.scatter(hArrs['R']['A']['mean'], hArrs['R']['P']['mean'], s = 7,  color = '#830B8A', alpha = 0.6)
        meanDset1 = ax.scatter(dsetMeans[0], dsetMeans[1], s = 12,  color = 'r', alpha = 0.5)
        #Legend
        ax.legend((fdr_ns, fdr_AP, fdr_AnotP, fdr_PnotA, fdr_R, meanDset1), ('n.s', 'A & P', 'A not P', 'P not A', 'R', 'meanDset'), loc = 'best', fontsize = 9)
        #axis labels
        ax.set_xlabel('Area A (pixel)')
        ax.set_ylabel('Area P (pixel)')
        #Title
        ax.set_title('Hits' , fontsize = 13)
        return ax  
     
     
    def outliersLayout(self, args):
        #unpack args
        ax, zArrs, dsetMeans= args
        #outliers
        z_ns = ax.scatter(zArrs['ns']['A']['mean'], zArrs['ns']['P']['mean'], s = 6, color = '#D1D1D1')
        z_AP = ax.scatter(zArrs['AP']['A']['mean'], zArrs['AP']['P']['mean'], s = 7, color = 'b', alpha = 0.6)
        z_AnotP = ax.scatter(zArrs['AnotP']['A']['mean'], zArrs['AnotP']['P']['mean'], s = 7, color = 'g', alpha = 0.6)
        z_PnotA = ax.scatter(zArrs['PnotA']['A']['mean'], zArrs['PnotA']['P']['mean'], s = 7, color = '#F048E2', alpha = 0.6)
        z_R = ax.scatter(zArrs['R']['A']['mean'], zArrs['R']['P']['mean'], s = 7, color = '#830B8A', alpha = 0.6)
        meanDset2 = ax.scatter(dsetMeans[0], dsetMeans[1], s = 12,  color = 'r', alpha = 0.5)
        #legend
        ax.legend((z_ns, z_AP, z_AnotP, z_PnotA, z_R, meanDset2), ('n.s', 'A & P', 'A not P', 'P not A', 'R', 'meanDset'), loc = 'best', fontsize = 9)
        #axis labels
        ax.set_xlabel('Area A (pixel)')
        ax.set_ylabel('Area P (pixel)')
        #title
        ax.set_title('Outliers', fontsize = 13)
        return ax
        
                    
    def repeatsLayout(self, args, filterout = False):
        ax, zArrs, dsetArrA, dsetArrP, dsetMeans = args
        #load data
        repeats = self.fetchRepeats(filterout = filterout)
        repMetricArrs = self.fetchRepeatsMetrics(filterout = filterout)
        #unpack
        stockRepeats, repeatedAssays = repeats
        repArrA, repArrP, repArrR = repMetricArrs
        #parse plotdata
        clusterRepAssays = [[(j,assayId) for j, (i, assayId) in enumerate(repeatedAssays) if assayId.split('_')[0]==stock] for stock in stockRepeats]
        plotArrs = [repArrA[0], repArrP[0]]
        plotdata = [[[arr[tupl[0]] for tupl in repeat] for repeat in clusterRepAssays] for arr in plotArrs]
        plotArrA, plotArrP = plotdata
        #generate color map
        numbColors = len(plotArrA)
        colorMap = self.generateColorMap(numbColors)
        #scatter plots
        args = ax, zArrs, dsetMeans
        ax = self.outliersLayout(args)
        for i, repeat in enumerate(plotArrA):
            ax.plot(repeat, plotArrP[i], color = colorMap[i]) 
        #title and axis labels
        ax.set_title('Repeats', fontsize = 13)
        return ax
        
        
    def volcanoLayout(self, args):
        from matplotlib import pyplot as plt
        import numpy as np
        #unpack args
        stockset, dsetMeans, dsetArrA, dsetArrP = args
        #define figure layout
        fig, ax = plt.subplots(1, 1, sharex = 'none', sharey = 'none')       
        #VOLCANO plot
        foldChange_A = [np.log(x/dsetMeans[0]) for x in dsetArrA[0]]
        foldChange_P = [np.log(x/dsetMeans[1]) for x in dsetArrP[0]]
        plog_A = [-np.log(x) for x in dsetArrA[2]]
        plog_P = [-np.log(x) for x in dsetArrP[2]]
        #build dictionary
        volcArrs = zip(*[foldChange_A, foldChange_P, plog_A, plog_P])
        volcDict = dict(zip(stockset, volcArrs))
        #plot definition
        vplot_A = ax.scatter(foldChange_A, plog_A, s = 7, color = 'b')
        vplot_P = ax.scatter(foldChange_P, plog_P, s = 7, color = 'g')
        #vertical lines
        ax.axvline(linewidth = 1, color = '#ADADAD')
        ax.axvspan(0, -0.26, facecolor='g', alpha=0.1, ec = 'None')
        #plotting settings
        ax.set_ylim([0, 700])
        ax.tick_params(axis = 'y', labelsize = 11) 
        #Legend
        ax.legend((vplot_A, vplot_P), ('meanA', 'meanP'), fontsize = 10, loc = 'best')
        #axis labels
        ax.set_xlabel('Fold change : log(R)')
        ax.set_ylabel('-log (p)')
        #Title
        ax.set_title('Volcano plot', fontsize = 13)
        return fig, ax, volcDict
        
    
    def barLayout(self, args):
        import numpy as np
        #unpack args
        ax, stocksOut, stockID, wingMetrics, dsetMeans, dsetErr = args
        #BAR plot
        #fetch stocks metrics
        stockArrs = [wingMetrics[stock.split('_')[1]][stock.split('_')[0]] for (i, stock) in stocksOut]
        stockArrs = zip(*stockArrs)
        stockArrs = [zip(*arr) for arr in stockArrs]
        arrA, arrP, arrR = stockArrs
        #define bar plotting sets 
        stockMeans= zip(arrA[0], arrP[0])
        stockErr = zip(arrA[1], arrP[1])
        dsetMeans = [dsetMeans[0], dsetMeans[1]]
        dsetErr = [dsetErr[0], dsetErr[1]]
        #some plotting settings
        colorMap = self.generateColorMap(len(stocksOut)+1)
        width = 0.1
        #bar plot definition
        xset = np.arange(2)
        plotSet = zip(stockMeans, stockErr)
        ax.bar(xset, dsetMeans, width = 0.1, color = colorMap[0], align = 'center', yerr =dsetErr)#dataset
        for i, (meani, erri) in enumerate(plotSet):
            ax.bar(xset + ((i+1) * width), meani, width = 0.1, color = colorMap[i+1], align = 'center', yerr =erri)#stocks bar sets
        #bar labels
        axlabels = ['meanA', 'meanP']
        ax.set_xticks(xset + len(stocksOut) * width/2)
        ax.set_xticklabels(axlabels, rotation = 60)
        #Legend
        legLabels = [stock for (i, stock) in stocksOut]
        legLabels.insert(0, 'dataset')
        legLabels = tuple(legLabels)
        ax.legend(legLabels, fontsize = 8, loc = 'best')
        #axis labels
        ax.set_ylabel('Area (pixel)')
        #Titles
        stockID = legLabels[1].split('_')[0]
        ax.set_title(('%s' %stockID), fontsize = 13)
        return ax
        
        
    def dotplotLayout(self, args):
        import numpy as np
        #unpack args
        ax, stocksOut, stockID = args
        #fetch stock data
        clusterdata = self.loadClusterWingdata()
        stockdata = []
        stockmeans = []
        for (i, key) in stocksOut:
            stock, batch = key.split('_')
            data = clusterdata[batch][stock]
            means = [np.mean(arr) for arr in data]
            stockdata.append(data)
            stockmeans.append(means)
        #SCATTER plot
        xticks = []
        for i, stock in enumerate(stockdata):
            #spacing between groups
            spacer1 = [0.5*(i+1)]*len(stock[0])
            spacer2 = [((0.5*len(stockdata)+2)+(0.5*i))]*len(stock[0])
            #datapoints
            ax.scatter(spacer1, stock[0], s = 10, color = '#1A14C4')
            ax.scatter(spacer2, stock[1], s = 10, color = '#07522F')
            #means
            ax.scatter(spacer1[0], stockmeans[i][0], marker = '_', c = 'r', s = 50)
            ax.scatter(spacer2[0], stockmeans[i][1], marker = '_', c = 'r', s = 50)
            #ticks container
            xticks.append(spacer1[0])
            xticks.append(spacer2[0])
        #set axis ticks and labels
        xticks.sort()
        ax.set_xticklabels([])
        ax.set_xticks(xticks)
        labels = [stock for (i, stock) in stocksOut]*2
        ax.set_xticklabels(labels, rotation = 60)
        #Legend
        ax.legend(['AreaA', 'AreaP', 'Mean'], fontsize = 10, loc = 'best')
        #axis labels
        ax.set_ylabel('Area (pixel)')
        #Titles
        stockID = labels[1].split('_')[0]
        ax.set_title(('%s' %stockID), fontsize = 13) 
        return ax
        
        
    def boxplot(self, stockID):
        import matplotlib.pyplot as plt
        #define figure layout
        fig, (ax1, ax2) = plt.subplots(1, 2, sharex = 'none', sharey = 'none')
        #load data for plotter
        plotterData = self.datafeedForPlotter(stockID = stockID)
        #unpack data
        stockset, stocksOut, wingMetrics, metricsArrs, dsetMetrics, hArrs, zArrs = plotterData
        #load dataset trimmed arrays
        dsetArr_trim = self.loadTrimmedAreas()
        dsetArrA_trim, dsetArrP_trim, dsetArrR_trim = dsetArr_trim
        dsetArrP_trim.sort()
        #fetch stock data
        clusterdata = self.loadClusterWingdata()
        stockdata = []
        for (i, key) in stocksOut:
            stock, batch = key.split('_')
            data = clusterdata[batch][stock]
            stockdata.append(data)
        
        #extract plotiing data from stockdata
        plotdata = [[stock[0] for stock in stockdata], [stock[1] for stock in stockdata]]
        plotdata[0].insert(0, dsetArrA_trim)
        plotdata[1].insert(0, dsetArrP_trim)
        #plotdata = [stock for arr in plotdata for stock in arr]
        #Boxplot
        axes = [ax1, ax2]
        [axes[i].boxplot(arr, showmeans = True) for i, arr in enumerate(plotdata)]
        #axis labels
        xlabel = ['AreaA (pixel)', 'AreaP (pixel)']
        [ax.set_ylabel(xlabel[i]) for i, ax in enumerate(axes)]
        #tick labels
        xticklabels = [stock for (i, stock) in stocksOut]
        xticklabels.insert(0, 'dataset')
        [ax.set_xticklabels(xticklabels, rotation = 60, fontsize = 10) for ax in axes]
        [ax.tick_params(axis = 'y', labelsize = 10) for ax in axes]
        #titles
        stockID = xticklabels[1].split('_')[0]
        [ax.set_title(stockID, fontsize = 13) for ax in axes]
        
        plt.tight_layout()
        plt.show()
        return     
    
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                
    def stockPlotter(self, stockID = False, plottype = 'dotplot'):
        from matplotlib import pyplot as plt
        #load data for plotter
        plotterData = self.datafeedForPlotter(stockID = stockID)
        #unpack data
        stockset, stocksOut, wingMetrics, metricsArrs, dsetMetrics, hArrs, zArrs = plotterData
        dsetArrA, dsetArrP, dsetArrR = metricsArrs
        dsetMeans, dsetErr = dsetMetrics
        #PLOTS
        if plottype == 'hits':
            #define figure layout
            fig, ax = plt.subplots(1, 1, sharex = 'none', sharey = 'none')
            #hits scatter
            args = ax, hArrs, dsetMeans
            ax1 = self.hitsLayout(args)
        elif plottype == 'outliers':
            #define figure layout
            fig, ax = plt.subplots(1, 1, sharex = 'none', sharey = 'none')
            #outliers scatter
            args = ax, zArrs, dsetMeans
            ax = self.outliersLayout(args)
        elif plottype == 'volcano':
            args = [stockset, dsetMeans, dsetArrA, dsetArrP]
            fig, ax, volcDict = self.volcanoLayout(args)                  
        elif plottype == 'dotplot':
            #figure layout
            figure, (ax1, ax2) = plt.subplots(1, 2, sharex = 'none', sharey = 'none')
            #BAR plot
            barArgs = [ax1, stocksOut, stockID, wingMetrics, dsetMeans, dsetErr]
            ax1 = self.barLayout(barArgs)
            #SCATTER plot
            dotplotArgs = ax2, stocksOut, stockID
            ax2 = self.dotplotLayout(dotplotArgs)
        elif plottype == 'boxplot':
            self.boxplot(stockID)
            return
        #Axes
        if plottype in ['boxplot', 'dotplot']:
            axes = [ax1, ax2]
        else:
            axes = [ax]
        [ax.tick_params(axis = 'y', labelsize = 10) for ax in axes]
        [ax.tick_params(axis = 'x', labelsize = 10) for ax in axes]
        #Anotations
        for i, (j, stock) in enumerate(stocksOut):
            if plottype in ['hits', 'outliers']:
                ax.scatter(dsetArrA[0][j], dsetArrP[0][j], s = 10, color = '#07EEFA')
                ax.annotate(stock, (dsetArrA[0][j], dsetArrP[0][j]), fontsize = 9)
            elif plottype == 'volcano':
                ax.scatter(volcDict[stock][0], volcDict[stock][2], s = 10, color = '#07EEFA')
                ax.annotate(stock, (volcDict[stock][0], volcDict[stock][2]), fontsize = 9)
                ax.scatter(volcDict[stock][1], volcDict[stock][3], s = 10, color = '#07EEFA')
                ax.annotate(stock, (volcDict[stock][1], volcDict[stock][3]), fontsize = 9)
        
        plt.tight_layout()
        plt.show()
        return
        
        
    def datasetPlotter(self, plottype = 'outliers', filterout = False):
        import matplotlib.pyplot as plt
        sys.path.append('C:\Python27\Lib\site-packages')
        from mpldatacursor import datacursor
        #define figure layout
        fig, ax = plt.subplots(1, 1, sharex = 'none', sharey = 'none')
        #load data for plotter
        plotterData = self.datafeedForPlotter()
        #unpack data
        stockset, stocksOut, wingMetrics, metricsArrs, dsetMetrics, hArrs, zArrs = plotterData
        dsetArrA, dsetArrP, dsetArrR = metricsArrs
        dsetMeans, dsetErr = dsetMetrics
        #outliers
        if plottype == 'outliers':
            args = ax, zArrs, dsetMeans
            ax = self.outliersLayout(args)
        #hits
        elif plottype == 'hits':
            args = ax, hArrs, dsetMeans
            ax = self.hitsLayout(args)
        #repeats
        elif plottype == 'repeats':
            args = ax, zArrs, dsetArrA, dsetArrP, dsetMeans
            ax = self.repeatsLayout(args, filterout = filterout)    
        #controls
        elif plottype == 'controls':
            #fetch controls metrics
            controlTuples = self.fetchControlsIdx()
            ctrlArrA = [dsetArrA[0][i] for (i, stock) in controlTuples]
            ctrlArrP = [dsetArrP[0][i] for (i, stock) in controlTuples]
            #scatter plots
            ax.scatter(dsetArrA[0], dsetArrP[0], s = 7, color = '#D1D1D1')
            ax.scatter(ctrlArrA, ctrlArrP, s = 10, color = '#28EDF7')
            ax.scatter(dsetMeans[0], dsetMeans[1], s = 20,  color = 'r')
            #title
            ax.set_title('Controls', fontsize = 13)
            #Anotations
            for i, (j, key) in enumerate(controlTuples):
                ax.annotate(key, (ctrlArrA[i],ctrlArrP[i]), fontsize = 9)
        #volcano
        elif plottype == 'volcano':
            args = stockset, dsetMeans, dsetArrA, dsetArrP
            fig, ax, volcDict = self.volcanoLayout(args)
        if plottype in ['hits', 'outliers', 'volcano', 'repeats']:   
            #Label ax datapoints interactively
            if plottype == 'volcano':
                datapoint_sets = ax.collections[:]
                datapoint_labels = [stockset, stockset]
            else:
                datapoint_sets = ax.collections[:-1]
                if plottype == 'repeats':
                    plottype = 'outliers'
                datapoint_labels = self.fetchPhenoClasses()[plottype]
            [datacursor(dataset, hover=True, point_labels = datapoint_labels[i], fontsize = 10, bbox= None, xytext=(0, 25), formatter=lambda **kwargs: kwargs['point_label'][0]) for i, dataset in enumerate(datapoint_sets)]
        plt.show()
        return   
    
          
    def wingImgFetcher(self, stockID):
        import matplotlib.pyplot as plt
        sys.path.append('C:\Python27\Lib\site-packages')
        import cv2
        import random
        #load image data dictionary
        clusterImgDict = self.loadImageDict()
        #Define dictionary of batch nomenclature
        batchDict = {'S': 'Batch1', 'R1': 'Batch2_Repeats_120607', 'R2': 'Batch3_Repeats_120801', 'R3': 'Batch4_Repeats_140221'}
        #fetch stock assays in the database
        stocksOut = self.stockFetcher(stockID = stockID)
        stockRepeats = [tupl[1] for tupl in stocksOut]
        #Fetch image filenames and capture exceptions
        for repeat in stockRepeats:
            fig = plt.figure() 
            batchdir = []
            imgset = []
            #Empty
            imgset_emp = random.sample(clusterImgDict['S']['Empty'], 3)
            imgset.append(imgset_emp)
            batchdir.append('Batch1')
            #Stock
            stock, batch = repeat.split('_')
            imgset_stock = random.sample(clusterImgDict[batch][stock], 3)
            imgset.append(imgset_stock)
            batchdir.append(batchDict[batch])
            #Chico
            try:
                imgset_cho = random.sample(clusterImgDict[batchdir[1]]['cho'], 3)
            except (ValueError, KeyError):
                imgset_cho = random.sample(clusterImgDict['S']['cho'], 3)
                batchdir.append('Batch1')
            imgset.append(imgset_cho)      
            #Hypo
            try:
                imgset_hpo = random.sample(clusterImgDict[batchdir[1]]['hpo'], 3)
            except (ValueError, KeyError):
                imgset_hpo = random.sample(clusterImgDict['S']['hpo'], 3)
                batchdir.append('Batch1')
            imgset.append(imgset_hpo)
            
            #Fetch image paths
            batchPath_list = [os.path.join(self.binarydir, name) for name in batchdir]
            pathset = [[os.path.join(batchPath_list[i], fname) for fname in sublist] for i, sublist in enumerate(imgset)]
            #Unpack image and path sets
            pathset = [val for sublist in pathset for val in sublist]
            #Define grid: number of rows
            rows = len(pathset)/3
            #Display images
            for i, path in enumerate(pathset):
                z = i+1
                img = cv2.imread(path, 0)         
                ax = plt.subplot(rows, 3, z)
                plt.imshow(img, cmap = 'gray', interpolation = 'bicubic')
                plt.xticks([])
                plt.yticks([])
                if i in [val for val in xrange(0,len(pathset),3)]:
                    xlabels = ['Empty', repeat, 'cho', 'hpo']
                    ax.set_ylabel(xlabels[i/3], fontsize = 14)
        
            fig.tight_layout(h_pad = 0.4, w_pad = 0.0)
            plt.show(fig)
        return 
    
          
      
#wdv = WingDataVis()
#wdv.stockPlotter(stockID = 'js84', plottype = 'boxplot')
#wdv.datasetPlotter(plottype = 'repeats', filterout = True)
#wdv.wingImgFetcher('JS84')
#wdv.stockFetcher('empty', output = 'screen')                                                                                                                                                                                                                                                                                                  
#wm = WingMetrics()
#wingsDict = wm.loadWingsDict()
#wm.fetchRepeats(filterout = 'mixed')
#wm.clusterImgdata()
#phenoclasses = wm.fetchPhenoClasses()
#wm.calculateWingMetrics()
#wm.fetchHits()
#wm.fetchDatasetMeans()
#wdv.boxplot('js204')
#wdb = WingsDB()
#wdb.createZscoresTable()
#wdb.createMetricsTable()


