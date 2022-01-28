import os 
import sys


class Dashboard():
    
    def __init__(self):
        cwd = os.getcwd()
        self.cwd = cwd
        self.dbdir = '/data/unknome/unknome_joao/Joao/Databases' # '%s\Dropbox\Unknome\Databases' %self.cwd
        self.dbpath = os.path.join(self.dbdir, 'FertilityDB.db')
        self.basedir = '/data/unknome/unknome_joao/Fertility' #'U:\Fertility'
        self.fertilitydir = '/data/unknome/unknome_joao/Joao/Screens/Fertility/PyFertility' # '%s\Dropbox\Unknome\Screens\Fertility\PyFertility' %self.cwd
        self.rawdatadir = os.path.join(self.fertilitydir, 'RawData') 
        self.pickledir = os.path.join(self.fertilitydir, 'PickleFiles')
        self.workdir = os.path.join(self.fertilitydir, 'FilesOut')
        self.controlsDict = self.controlsDict()
        self.ctrlnames = self.controlsNames()
        self.valRNAi = self.validationRNAis().values()
        self.tablenames = self.getTablenames()
        
    def getMembers(self):
        import inspect
        methods = inspect.getmembers(self, predicate = inspect.ismethod)
        print(methods)
        return
    
    def controlsDict(self):
        #Define dictionary
        controlsDict = {'EMPTY': 'Empty', 'GFPI(9)': 'GFPi(9)', 'GFPI': 'GFPi', 'GFPI(5)': 'GFPi(5)', 'GFPI(4)': 'GFPi(4)', 'W1118': 'w1118',
        'F1': 'F1', 'F2': 'F2', 'F3': 'F3', 'F4': 'F4', 'F5': 'F5', 'M6': 'M6', 'M7': 'M7', 'M8': 'M8', 'M9': 'M9', 'M10': 'M10',}           
        return controlsDict
    
    def controlsNames(self):
         ctrlnames = self.controlsDict.values()
         return ctrlnames
    
    def validationRNAis(self):
        valRNAiDict = {'JS173':('31568', '5155R1', '5155R2')}
        return valRNAiDict
         
    def getTablenames(self):
            tablenames = ['females', 'males']
            return tablenames
            
    def loadBatchlist(self):
        import sqlite3
        #connect to database
        db = sqlite3.connect(self.dbpath)
        cursor = db.cursor()
        #fetch data
        data = []
        for tablename in self.tablenames:
            cursor.execute('''SELECT Batch FROM %s''' %tablename)
            tabledata = cursor.fetchall()
            data.append(tabledata)
        db.close()
        #extract batchlist from data
        batchlist = [[] for name in self.tablenames]
        for i, table in enumerate(data):
            for tupl in table:
                if tupl not in batchlist[i]:
                    batchlist[i].append(tupl)
        batchlist = [[tupl[0] for tupl in table] for table in batchlist]#unpack
        batchlist = dict(zip(self.tablenames, batchlist))
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
        data = []
        for table in self.tablenames:
            cursor.execute('''SELECT Batch, Stock FROM %s''' %table)
            tabledata = cursor.fetchall()
            data.append(tabledata)
        db.close()
        #cluster stocks according to batches
        stockset = [[[tupl[1] for tupl in table if tupl[0] == batch] for batch in batchlist[self.tablenames[i]]] for i, table in enumerate(data)]
        clusterStockset = [[list(set(batch)) for batch in table] for table in stockset]
        #split controls from stockset
        clusterStockset = [[listPartition(lambda x: x.startswith('JS'), batch) for batch in table] for table in clusterStockset]
        clusterStockset = [[[sorted(batch[0], key = lambda x: int(x[2:])), sorted(batch[1], key = lambda x: x)] for batch in table] for table in clusterStockset]#sort sublists
        clusterStockset = [[[val for sublist in batch for val in sublist] for batch in table] for table in clusterStockset]#rejoin sorted sublists
        clusterStockset = [dict(zip(batchlist[self.tablenames[i]], table)) for i, table in enumerate(clusterStockset)]
        clusterStockset = dict(zip(self.tablenames, clusterStockset))
        return clusterStockset
        
    def unpackStockset(self, tablename = False):
        #set tablenames
        if tablename:
            tablenames = [tablename]
        else:
            tablenames = self.tablenames
        #load data
        stockset = self.loadStockset()
        stockset = [stockset[tablename] for tablename in tablenames]
        batchlist = self.loadBatchlist()
        batchlist = [batchlist[tablename] for tablenames in tablenames]
        #unpack stockset
        unpStockset = [[['%s_%s' %(stock, batch) for stock in stockset[i][batch]] for batch in table] for i, table in enumerate(batchlist)]
        unpStockset = [[stock for sublist in table for stock in sublist] for table in unpStockset]
        if len(unpStockset) == 1:
            unpStockset = unpStockset[0]
        return unpStockset 
        
    def buildFertilityDB(self):
        textfilelist = ['iFertility_datasetF_raw.txt', 'iFertility_datasetM_raw.txt']
        for i, tablename in self.tablenames:
            textpath = os.path.join(self.rawdatadir, textfilelist[i])
            rows = FertilityDB().fetchRows(textpath)
            FertilityDB().createFertilityDB(rows, tablename)
            FertilityDB().addZscoresColumn(tablename)
        FertilityDB().createMetricsTable()
        FertilityDB().addNormDataColumns()
        return
        
    def purgePickleDir(self, fnum = 2):
        '''It purges pickledir of older file versions; fnum (int) defines the maximum number of file versions to keep.
        Pickle files purged are: fertilityDict, fertilityMetrics, trimBroodSizeArrs, clusterFertilityData, clusterImageData, normBatchdata and rajenDict.'''
        #Define filenames
        filenames = ['fertilityDict', 'clusterFertilityData', 'clusterImageData', 'fertilityMetrics', 'normBatchdata', 'trimBroodSizeArrs', 'rajenDict']
        #Fetch and sort filelist
        filelist = [[f for f in os.listdir(self.pickledir) if f.startswith(name)] for name in filenames]
        [sublist.sort() for sublist in filelist]#sort filelist
        #Purge filelist
        filelist_topurge = [sublist[:-fnum] for sublist in filelist]
        #Purge pickleDir
        [[os.remove(os.path.join(self.pickledir, filename)) for filename in sublist] for sublist in filelist_topurge]
        return
    
    def resetMetrics(self):
        self.buildFertilityDB()
        FertilityObjects().buildFertilityDict()
        FertilityObjects().ztrimBroodSizeArrs()
        FertilityObjects().clusterFertilityData()
        FertilityObjects().clusterImgdata()
        FertilityObjects().buildFertilityMetricsDict()
        FertilityObjects().buildnormBatchdataDict()
        FertilityObjects().buildRajenDict()
        self.purgePickleDir()
        return
    
    def resetWorkEnv(self):
        self.buildFertilityDB()
        self.resetMetrics()
        return
         

class FertilityDB(Dashboard):
     
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
        with open(textpath, 'r') as f:
            colheads = f.readline()[:-1]
            colheads = colheads.split('\t')
        #fetch data
        df = pd.read_csv(textpath, delimiter = '\t')
        data = [df[head] for head in colheads]
        rows = zip(*data)
        #convert datatypes
        rows = [(int(batch), stock, filename, int(broodsize)) for (batch, stock, filename, broodsize) in rows]
        return rows
        
    def createFertilityTable(self, tablename):
        import sqlite3
        #Connect to database
        db = sqlite3.connect(self.dbpath)
        cursor = db.cursor()
        print('Creating table %s. \n' %tablename)
        createStatement = '''CREATE TABLE  %s (sqlKey INTEGER PRIMARY KEY AUTOINCREMENT, Batch INT NOT NULL, Stock CHAR(50) NOT NULL, Filename CHAR(50) NOT NULL, 
                            
                             BroodSize INT NOT NULL)''' %tablename
        cursor.execute(createStatement)
        return 
    
    
    def createFertilityDB(self, rows, tablenames):
        import sqlite3             
        #Connect to database
        db = sqlite3.connect(self.dbpath)
        cursor = db.cursor()
        #define tablenames
        if isinstance(tablenames, (str, unicode)):
            tablenames = [tablenames]
            rows = [rows]   
        for i, tablename in enumerate(tablenames):
            self.createFertilityTable(tablename)
            insertStatement = '''INSERT INTO %s (Batch, Stock, Filename, BroodSize) VALUES(?,?,?,?)''' %tablename 
            print('Inserting data in table %s. \n' %tablename)
            cursor.executemany(insertStatement, rows[i])
            db.commit()
            db.close() 
            return
            
            
    def calculateBroodZscores(self, tablename):
        from statsFunctions import statsZscores
        import sqlite3
        #connect to database
        db = sqlite3.connect(self.dbpath)
        cursor = db.cursor()
        #fetch areas from database
        cursor.execute('''SELECT Stock, sqlKey, BroodSize FROM %s''' %tablename)
        data = cursor.fetchall()       
        data = [('%s_%s' %(stock, sqlkey), broodsize)  for (stock, sqlkey, broodsize) in data]
        db.close()
        #rearrange data
        arrs = zip(*data)
        zkey, arrBS = arrs
        #Calculate zscores
        zArrs = statsZscores(arrBS)
        zLists = [zkey, zArrs]
        return zLists
        
    
    def addZscoresColumn(self, tablename):
        import sqlite3
        #Connect to database
        db = sqlite3.connect(self.dbpath)
        cursor = db.cursor()
        #create table
        alterStatement = '''ALTER TABLE %s ADD COLUMN zScore REAL;''' %tablename
        cursor.execute(alterStatement)
        #calculate z scores
        zLists = self.calculateBroodZscores(tablename)
        #parse rows
        zkey, zArrs = zLists #unpack
        rows = [(zBS, int(key.split('_')[1])) for (key, zBS) in zip(zkey, zArrs)]
        #insert data
        updateStatement = '''UPDATE %s SET zScore = ? WHERE sqlKey = ?''' %tablename
        cursor.executemany(updateStatement, rows)
        db.commit()
        db.close()
        return
        
        
    def createMetricsTable(self):
        import sqlite3
        #load wingMetrics dictionary
        fertMetrics = FertilityMetrics().loadFertilityMetrics()
        #load data
        stockset = self.loadStockset()
        stockset = [stockset[tablename] for tablename in self.tablenames]
        batchlist = self.loadBatchlist()
        batchlist = [batchlist[tablename] for tablename in self.tablenames]
        #parse rows
        rows = [[], []]
        for i, table in enumerate(batchlist):
            for batch in table:
                for stock in stockset[i][batch]:
                    arr = fertMetrics[self.tablenames[i]][batch][stock]
                    mean, sem, p, z = arr
                    row = (stock, batch, mean, sem, p, z)
                    rows[i].append(row)         
        #Connect to database
        db = sqlite3.connect(self.dbpath)
        cursor = db.cursor()
        #create metrics tables
        metricsTablenames = ['%sMetrics' %tablename[:-1] for tablename in self.tablenames]
        for i, name in enumerate(metricsTablenames):
            #create table
            createStatement = '''CREATE TABLE  %s (Stock TEXT NOT NULL, Batch INT NOT NULL, meanBS REAL NOT NULL, errBS REAL, p REAL, z REAL)''' %name                  
            cursor.execute(createStatement)
            #insert data
            insertStatement = '''INSERT INTO %s (stock, batch, meanBS, errBS, p, z) VALUES(?,?,?,?,?,?)''' %name
            cursor.executemany(insertStatement, rows[i])
            db.commit()
        db.close()
        return
        
        
    def addNormDataColumns(self):
        import sqlite3
        #Connect to database
        db = sqlite3.connect(self.dbpath)
        cursor = db.cursor()
        #create table
        tablenames = ['femaleMetrics', 'maleMetrics']
        colnames = ['normBS', 'errR', 'zR']
        for tablename in tablenames:
            for name in colnames:
                alterStatement = '''ALTER TABLE %s ADD COLUMN %s REAL;''' %(tablename, name)
                cursor.execute(alterStatement)
        #load unpacked stockset
        stockset = self.unpackStockset()
        #calculate z scores
        normBatchArrs = FertilityMetrics().loadNormBatchArrays()
        normBatchArrs = [[[val for batch in table for val in batch] for table in arr] for arr in normBatchArrs]#unpack arrays
        normBS, errors, zR = normBatchArrs
        #parse rows
        rows = [rowsF, rowsM] = [[normBS[0], errors[0], zR[0]], [normBS[1], errors[1], zR[1]]]
        rows = [[zip(sublist, stockset[i]) for sublist in table] for i, table in enumerate(rows)]
        rows = [[[(metric, assayId.split('_')[0], int(assayId.split('_')[1])) for (metric, assayId) in sublist] for sublist in table] for table in rows]
        #insert data
        for i, tablename in enumerate(tablenames):
            for j, column in enumerate(rows[i]):
                updateStatement = '''UPDATE %s SET %s = ? WHERE Stock = ? AND Batch = ?''' %(tablename, colnames[j])
                cursor.executemany(updateStatement, column)
                db.commit()
        db.close()
        return
                   
    

class FertilityObjects(Dashboard):
    
    def __init__(self):
        Dashboard.__init__(self)
        
        
    def getMembers(self):
        import inspect
        methods = inspect.getmembers(self, predicate = inspect.ismethod)
        print(methods)
        return

    def buildFertilityDict(self):
        from datetime import datetime
        from collections import OrderedDict
        import cPickle as pickle
        import sqlite3
        #connect to database
        db = sqlite3.connect(self.dbpath)
        cursor = db.cursor()
        #fetch data from database
        data = []
        for tablename in self.tablenames:
            cursor.execute('''SELECT * FROM %s''' %tablename)
            tabledata = cursor.fetchall()
            data.append(tabledata)
        db.close()    
        #parse data
        data = [[(item[0], item[1:]) for item in table] for table in data]
        #Fetch current time and date
        time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        #serialise dictionary
        fertilityDict = [OrderedDict(table) for table in data]
        fertilityDict = dict(zip(self.tablenames, fertilityDict))
        picklepath = os.path.join(self.pickledir, 'fertilityDict_%s.pickle' %time)
        with open(picklepath, 'wb') as f:
            pickle.dump(fertilityDict, f, protocol = 2)
        return
        
  
    def loadFertilityDict(self):
        import cPickle as pickle
        #load lists
        filelist = [filename for filename in os.listdir(self.pickledir) if filename.startswith('fertilityDict')]
        filelist.sort()
        picklefile = filelist[-1]
        picklepath = os.path.join(self.pickledir, picklefile)
        with open(picklepath, 'rb') as f:
            fertDict = pickle.load(f)
        return fertDict


    def ztrimBroodSizeArrs(self):
        from datetime import datetime
        from statsFunctions import zTrim
        import cPickle as pickle
        #load arrays
        zArrs = self.fetchZArrs()
        bsArrs = self.loadBroodSizeArrs()
        ctrlkeys = self.fetchControlSQLkeys()
        #parse ctrlkeys
        ctrlkeys = [zip(*ctrlkeys[tablename])[1] for tablename in self.tablenames]
        ctrlIdx = [[val-1 for control in table for val in control] for table in ctrlkeys]       
        #Trim areas and ratio arrays and filter out controls
        dataIdx_trim = [zTrim(zArrs[key], zscore = 2.5, output = 'non-outlier') for key in self.tablenames]
        dataIdx_trim = [[val for val in arr if val not in ctrlIdx[i]] for i, arr in enumerate(dataIdx_trim)]#Filter out controls
        bsArrs_trim = [[val for j, val in enumerate(bsArrs[key]) if j in dataIdx_trim[i]] for i, key in enumerate(self.tablenames)]
        bsArrs_trim = dict(zip(self.tablenames, bsArrs_trim))
        #Fetch current time and date
        time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        #pickle trimmed arrays
        picklepath = os.path.join(self.pickledir, 'trimBroodSizeArrs_%s.pickle' %time)
        with open(picklepath, 'wb') as f:
            pickle.dump(bsArrs_trim, f, protocol = 2)
        return
        
    def loadTrimmedBSArrs(self):
        import cPickle as pickle
        #load lists
        filelist = [filename for filename in os.listdir(self.pickledir) if filename.startswith('trimBroodSizeArrs')]
        filelist.sort()
        picklefile = filelist[-1]
        picklepath = os.path.join(self.pickledir, picklefile)
        with open(picklepath, 'rb') as f:
            bsArrs_trim = pickle.load(f)
        return bsArrs_trim
        
        
    def clusterFertilityData(self):
        from datetime import datetime
        import cPickle as pickle
        #load data
        fertDict = self.loadFertilityDict()
        fertdata = [fertDict[table].values() for table in self.tablenames]
        batchlist = self.loadBatchlist()
        batchlist = [batchlist[table] for table in self.tablenames]
        clusterStockset = self.loadStockset()
        clusterStockset = [clusterStockset[table] for table in self.tablenames]
        #cluster data
        clusterdata = [[[tupl for tupl in table if tupl[0] == batch] for batch in batchlist[i]] for i, table in enumerate(fertdata)]
        clusterdata = [[[(stock, [(tupl[2], tupl[3], tupl[4]) for tupl in batch if tupl[1] == stock]) for stock in clusterStockset[i][j+1]] for j, batch in enumerate(table)] for i, table in enumerate(clusterdata)]
        clusterdata = [[[(stock, zip(*arrs)) for (stock, arrs) in batch] for batch in table] for table in clusterdata]
        clusterdata = [[dict(batch) for batch in table] for table in clusterdata]
        clusterdata = [dict(zip(batchlist[i], table)) for i,table in enumerate(clusterdata)]
        clusterdata = dict(zip(self.tablenames, clusterdata))
        #Fetch current time and date
        time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        #pickle dictionary
        picklepath = os.path.join(self.pickledir, 'clusterFertilityData_%s.pickle' %time)
        with open(picklepath, 'wb') as f:
            pickle.dump(clusterdata, f, protocol = 2)   
        return
        
    def loadClusterFertdata(self):
        import cPickle as pickle
        #load lists
        filelist = [filename for filename in os.listdir(self.pickledir) if filename.startswith('clusterFertilityData')]
        filelist.sort()
        picklefile = filelist[-1]
        picklepath = os.path.join(self.pickledir, picklefile)
        with open(picklepath, 'rb') as f:
            clusterFertdata = pickle.load(f)
        return clusterFertdata
        
        
    def clusterImgdata(self):
        from datetime import datetime
        import cPickle as pickle
        #load data
        fertDict = self.loadFertilityDict()
        fertdata = [fertDict[table].values() for table in self.tablenames]
        batchlist = self.loadBatchlist()
        batchlist = [batchlist[table] for table in self.tablenames]
        clusterStockset = self.loadStockset()
        clusterStockset = [clusterStockset[table] for table in self.tablenames]
        #cluster data
        clusterdata = [[[tupl for tupl in table if tupl[0] == batch] for batch in batchlist[i]] for i, table in enumerate(fertdata)]
        clusterdata = [[[(stock, [tupl[2] for tupl in batch if tupl[1] == stock]) for stock in clusterStockset[i][j+1]] for j, batch in enumerate(table)] for i, table in enumerate(clusterdata)]
        clusterdata = [[dict(batch) for batch in table] for table in clusterdata]
        clusterdata = [dict(zip(batchlist[i], table)) for i,table in enumerate(clusterdata)]
        clusterdata = dict(zip(self.tablenames, clusterdata))
        #fetch curent time
        time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        #pickle dictionary
        picklepath = os.path.join(self.pickledir, 'clusterImageData_%s.pickle' %time)
        with open(picklepath, 'wb') as f:
            pickle.dump(clusterdata, f, protocol = 2)  
        return
    
    def loadClusterImgDict(self):
        import cPickle as pickle
        #load lists
        filelist = [filename for filename in os.listdir(self.pickledir) if filename.startswith('clusterImageData')]
        filelist.sort()
        picklefile = filelist[-1]
        picklepath = os.path.join(self.pickledir, picklefile)
        with open(picklepath, 'rb') as f:
            clusterImgDict = pickle.load(f)
        return clusterImgDict 
        
                 
    def buildFertilityMetricsDict(self):
        import cPickle as pickle
        from datetime import datetime
        fertMetrics = FertilityMetrics().calculateFertilityMetrics()
        #fetch curent time
        time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        #pickle fertMetrics dictionary
        picklepath = os.path.join(self.pickledir, 'fertilityMetrics_%s.pickle' %time)
        with  open(picklepath, 'wb') as f:
            pickle.dump(fertMetrics, f, protocol = 2)
        return
            
    def loadFertilityMetrics(self):
        import cPickle as pickle
        #load lists
        filelist = [filename for filename in os.listdir(self.pickledir) if filename.startswith('fertilityMetrics')]
        filelist.sort()
        picklefile = filelist[-1]
        picklepath = os.path.join(self.pickledir, picklefile)
        with open(picklepath, 'rb') as f:
            fertMetrics = pickle.load(f)
        return fertMetrics 
        
    def buildnormBatchdataDict(self):
        from datetime import datetime
        import cPickle as pickle
        normBatchdata = FertilityMetrics().normaliseBatchdata()
        #fetch current time
        time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        #pickle dictionary
        picklepath = os.path.join(self.pickledir, 'normBatchdata_%s.pickle' %time)
        with open(picklepath, 'wb') as f:
            pickle.dump(normBatchdata, f, protocol = 2)
        return
        
    def loadNormBatchdata(self):
        import cPickle as pickle
        #load lists
        filelist = [filename for filename in os.listdir(self.pickledir) if filename.startswith('normBatchdata')]
        filelist.sort()
        picklefile = filelist[-1]
        picklepath = os.path.join(self.pickledir, picklefile)
        with open(picklepath, 'rb') as f:
            normBatchdata = pickle.load(f)
        return normBatchdata
   
                                            
                                                                                                              
class FertilityMetrics(FertilityObjects):
    
    def __init__(self):
        FertilityObjects.__init__(self)
           
    def getMembers(self):
        import inspect
        methods = inspect.getmembers(self, predicate = inspect.ismethod)
        print(methods)
        return                                                                    
             
    def loadBroodSizeArrs(self):
        #load wings dictionary
        fertDict = self.loadFertilityDict()
        bsdata = [fertDict[tablename].values() for tablename in self.tablenames]
        #extract arrays
        bsArrs = [zip(*table)[3] for table in bsdata]
        bsArrs = dict(zip(self.tablenames, bsArrs)) 
        return bsArrs
        
    def fetchZArrs(self):
        #load wings dictionary
        fertDict = self.loadFertilityDict()
        zdata = [fertDict[tablename].values() for tablename in self.tablenames]
        #extract arrays
        zArrs = [zip(*table)[4] for table in zdata]
        zArrs = dict(zip(self.tablenames, zArrs))
        return zArrs
        
    def fetchControlSQLkeys(self):
        #load wings dictionary
        fertDict = self.loadFertilityDict()
        #fetch data
        fertdata = [fertDict[tablename].values() for tablename in self.tablenames]
        #extract keys
        ctrlSQLkey = [[(name, [i+1 for i, tupl in enumerate(table) if tupl[1] == name]) for name in self.ctrlnames] for table in fertdata]
        #build dictionary
        ctrlSQLkey = dict(zip(self.tablenames, ctrlSQLkey))
        return ctrlSQLkey
    
        
    def calculateFertilityMetrics(self):
        from collections import OrderedDict
        from statsFunctions import statsZscores
        import numpy as np
        from scipy import stats
        #load data
        clusterdata = self.loadClusterFertdata()
        trimArrs = self.loadTrimmedBSArrs()
        stockset = self.loadStockset()
        batchlist = self.loadBatchlist() 
        #calculate metrics
        fertMetrics = {}
        meansArr = [[] for name in self.tablenames]
        for i, table in enumerate(self.tablenames):
            fertMetrics[table] = OrderedDict()
            for batch in batchlist[table]:
                fertMetrics[table][batch] = OrderedDict()
                for stock in stockset[table][batch]:
                    mean = np.mean(clusterdata[table][batch][stock][1])
                    sem = stats.sem(clusterdata[table][batch][stock][1])
                    p = stats.ttest_ind(clusterdata[table][batch][stock][1], trimArrs[table], equal_var=True)[1] 
                    meansArr[i].append((batch, stock, mean))
                    zipdata = [mean, sem, p]
                    fertMetrics[table][batch][stock] = zipdata
        #calculate zscores
        [batchF, stockF, meansF], [batchM, stockM, meansM] = [zip(*table) for table in meansArr]
        means = [meansF, meansM]
        zArrs = statsZscores(means)
        zArrF, zArrM = zArrs
        #parse zscores
        ztuples = [zip(*[batchF, stockF, zArrF]), zip(*[batchM, stockM, zArrM])]
        #update fertMetrics dictionary
        for i, table in enumerate(ztuples):
            for tupl in table :
                (batch, stock, z) = tupl
                tupl = mean, sem, p = fertMetrics[self.tablenames[i]][batch][stock]
                tupl = tupl + [z]
                fertMetrics[self.tablenames[i]][batch][stock] = tupl
        return fertMetrics
    
            
    def fetchFertilityMetricsArrays(self):
        #load data
        fertMetrics = self.loadFertilityMetrics()
        #unpack arrays from metrics data
        metricsData = [fertMetrics[tablename].values() for tablename in self.tablenames]#stocks in bacthes for males and females
        metricsData = [[sublist.values() for sublist in table] for table in metricsData] #stocks
        metricsData = [[val for sublist in table for val in sublist] for table in metricsData]#unpack
        zipdata = [zip(*table) for table in metricsData]
        metricsArrs = [arrF, arrM] = zipdata
        return metricsArrs
        
    def normaliseBatchdata(self):
        from collections import OrderedDict
        from statsFunctions import statsZscores
        import cPickle as pickle
        import numpy as np
        import math
        #load data
        batchlist = self.loadBatchlist()
        batchlist = [batchlist[tablename] for tablename in self.tablenames]
        stockset = self.loadStockset()
        stockset = [stockset[tablename] for tablename in self.tablenames]
        fertMetrics = self.loadFertilityMetrics()
        batchMetrics = self.loadBatchMeans()
        batchmeans, err_batchmeans = batchMetrics
        #fetch batchdata
        batchdata = [[[fertMetrics[self.tablenames[i]][batch][stock] for stock in stockset[i][batch]] for batch in table] for i, table in enumerate(batchlist)]
        batchdata = [[(zip(*batch)[0], zip(*batch)[1]) for batch in table] for table in batchdata]
        batchdata = [zip(*table) for table in batchdata]
        batchdata = zip(*batchdata)
        means, err = batchdata
        #batch normalise brood size means for each stock 
        normMeans = [[np.asarray(batch)/float(batchmeans[i][j]) for j, batch in enumerate(table)] for i, table in enumerate(means)]
        #calculate zscores
        normArrs = [[item for batch in table for item in batch] for table in normMeans]#unpack
        zArrs = statsZscores(normArrs)
        #calculate errors of normalised means
        normdata = []
        for i, table in enumerate(means):
            normdata.append([])
            count = 0
            for j, batch in enumerate(table):
                normdata[i].append([])
                for z, stockmean in enumerate(batch):
                    count +=1
                    error = normMeans[i][j][z] * np.sqrt(np.power(err_batchmeans[i][j]/batchmeans[i][j], 2) + np.power(err[i][j][z]/stockmean, 2))
                    if math.isnan(error):
                        error = 0.0    
                    normdata[i][j].append((normMeans[i][j][z], error, zArrs[i][count-1]))            
        normBatchdata = [[OrderedDict(zip(stockset[i][j+1], batch)) for j, batch in enumerate(table)] for i, table in enumerate(normdata)]
        normBatchdata = [OrderedDict(zip(table, normBatchdata[i])) for i, table in enumerate(batchlist)]   
        normBatchdata = OrderedDict(zip(self.tablenames, normBatchdata))
        return normBatchdata
         
    
    def loadNormBatchArrays(self):
        from File_Functions import deepSplitSequence
        #load data
        batchlist = self.loadBatchlist()
        batchlist = [batchlist[tablename] for tablename in self.tablenames]
        normBatchdata = self.loadNormBatchdata()
        #extract arrays from batchdata dictionary
        normBatchdata = normBatchdata.values()
        normBatchdata = [[batch.values() for batch in table.values()] for table in normBatchdata]
        #split clustered metrics
        normBatchArrs = deepSplitSequence(normBatchdata)
        for i, table in enumerate(normBatchdata):
            for j, batch in enumerate(table):
                arrs = zip(*batch)
                for z, arr in enumerate(arrs):
                    normBatchArrs[z][i][j].append(arr)             
        normBatchArrs = [[[[val for tupl in batch for val in tupl] for batch in table] for table in arr] for arr in normBatchArrs]#unpack tuples
        return normBatchArrs
  
              
    def loadBatchMeans(self):
        from scipy.stats import sem
        import numpy as np
        #load data
        batchlist = self.loadBatchlist()
        batchlist = [batchlist[tablename] for tablename in self.tablenames]
        plotgroups = FertilityDataVis().fetchPlotGroups()
        outliers, hits, ns, controls = plotgroups#unpack
        fertMetrics = self.loadFertilityMetrics()
        #calculate batch means and sem
        batchmetrics = [[[stock for stock in ns[i] if int(stock.split('_')[1]) == batch] for batch in table] for i, table in enumerate(batchlist)]
        batchmetrics = [[[fertMetrics[self.tablenames[i]][batchlist[i][j]][stock.split('_')[0]][0] for stock in batch] for j, batch in enumerate(table)] for i, table in enumerate(batchmetrics)]
        batchmeans = [[np.mean(batch) for batch in table] for table in batchmetrics]
        err_batchmeans = [[sem(batch) for batch in table] for table in batchmetrics]
        batchmetrics = [batchmeans, err_batchmeans]
        return batchmetrics
               
    def fetchDatasetMeans(self):
        from statsFunctions import zTrim
        from scipy import stats
        import numpy as np
        #load data
        stockset = self.loadStockset()
        stockset = [stockset[tablename] for tablename in self.tablenames]
        batchlist = self.loadBatchlist()
        batchlist = [batchlist[tablename] for tablenames in self.tablenames]
        #filter out controls from stockset
        stockset = [[stockset[i][batch] for batch in table] for i, table in enumerate(batchlist)]
        stockset = [[stock for batch in table for stock in batch] for table in stockset]
        stockset_trim_idx = [[i for i, stock in enumerate(table) if stock not in self.ctrlnames] for table in stockset]
        #load arrays and unpack
        metricsArrs = self.fetchFertilityMetricsArrays()
        arrF, arrM = metricsArrs
        meanBS_F, errF, pF, zF = arrF
        meanBS_M, errM, pM, zM = arrM
        #trim z arrays
        zArrs = [zF, zM]
        meanArrs = [meanBS_F, meanBS_M]
        dataIdx_trim = zTrim(zArrs, zscore = 2.5, output = 'non-outlier')
        meanArrs_trim = [[(j, mean) for j, mean in enumerate(arr) if j in dataIdx_trim[i]] for i, arr in enumerate(meanArrs)]#filter mean arrays
        meanArrs_trim = [[mean for (j, mean) in arr if j in stockset_trim_idx[i]] for i, arr in enumerate(meanArrs_trim)]#filter out controls
        #calculate dataset means
        dsetMeans = [np.mean(arr) for arr in meanArrs_trim]
        dsetErr = [stats.sem(arr) for arr in meanArrs_trim] 
        dsetMetrics = [dsetMeans, dsetErr]
        return dsetMetrics
        
    def fetchControlsIdx(self):
        #fetch controls indices
        controlsTuples = [[self.stockFetcher(control)[0] for control in self.ctrlnames], [self.stockFetcher(control)[1] for control in self.ctrlnames]]
        controlsTuples = [[control for sublist in table for control in sublist] for table in controlsTuples]
        return controlsTuples
        
    def fetchOutliers(self, norm = False):
        from statsFunctions import zTrim
        #load data
        stockset = self.loadStockset()
        stockset = [stockset[tablename] for tablename in self.tablenames]
        batchlist = self.loadBatchlist()
        batchlist = [batchlist[tablename] for tablenames in self.tablenames]
        #unpack stockset
        stockset = [[stockset[i][batch] for batch in table] for i, table in enumerate(batchlist)]
        stockset = [['%s_%s' %(stock, batchlist[j][i]) for i, batch in enumerate(table)  for stock in batch] for j, table in enumerate(stockset)]
        #unpack metrics arrays
        if norm:
            normBatchArrs = self.loadNormBatchArrays()
            normMeans, errors,  zscores= normBatchArrs
            zF , zM = [[val for batch in table for val in batch] for table in zscores]   
        else:
            metricsArrs = self.fetchFertilityMetricsArrays()
            arrF, arrM = metricsArrs
            meanBS_F, errF, pF, zF = arrF
            meanBS_M, errM, pM, zM = arrM
        #filter out outliers
        zArrs = [zF, zM]     
        outlierIdx = zTrim(zArrs, zscore = 2.5, output = 'outlier')
        outliers = [[stockset[i][val] for val in arr] for i, arr in enumerate(outlierIdx)]
        return outliers
        
    def fetchHits(self, norm = False):
        from statsFunctions import statsFDR
        #load data
        stockset = self.loadStockset()
        stockset = [stockset[tablename] for tablename in self.tablenames]
        batchlist = self.loadBatchlist()
        batchlist = [batchlist[tablename] for tablenames in self.tablenames]
        #unpack stockset
        stockset = [[stockset[i][batch] for batch in table] for i, table in enumerate(batchlist)]
        stockset = [['%s_%s' %(stock, batchlist[j][i]) for i, batch in enumerate(table)  for stock in batch] for j, table in enumerate(stockset)]
        #unpack metrics arrays
        metricsArrs = self.fetchFertilityMetricsArrays()
        arrF, arrM = metricsArrs
        meanBS_F, errF, pF, zF = arrF
        meanBS_M, errM, pM, zM = arrM
        #calculate FDR
        pList = [pF, pM]
        fdrHits = [statsFDR(pList[i], table) for i, table in enumerate(stockset)]     
        return fdrHits
        
    def fetchRepeats(self):
        #load data
        assaylist = self.loadStockset()
        assaylist = [assaylist[tablename] for tablename in self.tablenames]
        batchlist = self.loadBatchlist()
        batchlist = [batchlist[tablename] for tablenames in self.tablenames]
        #parse assaylist and fetch list of stock repeats
        assaylist = [[assaylist[i][batch] for batch in table] for i, table in enumerate(batchlist)]
        assaylist = [[item for batch in table for item in batch] for table in assaylist]
        stockRepeats = [list(set([item for item in table if table.count(item) > 1])) for table in assaylist]
        stockRepeats = [[stock for stock in table if stock not in self.ctrlnames] for table in stockRepeats]#filter out controls
        #fetch list of repeated assays
        repeatedAssays = [[self.stockFetcher(stock)[i] for stock in table] for i, table in enumerate(stockRepeats)]
        repeatedAssays = [[item for sublist in table for item in sublist]  for table in repeatedAssays]
        repeats = [stockRepeats, repeatedAssays]#pack
        return repeats
        
    def printRepeats(self, output = 'screen'):
        from File_Functions import printList
        #fetch repeats
        repeats = self.fetchRepeats()
        stockRepeats, repeatedAssays = repeats
        stockRepeats = [sorted(table, key = lambda x:int(x[2:])) for table in stockRepeats]
        #print it
        if output == 'screen':
            for i, table in enumerate(stockRepeats):
                print('\n%s:' %self.tablenames[i].title())
                printList(table, 10)
                print('\n')
        if output == 'file':
            path = os.path.join(self.workdir, 'repeatsList.txt')
            with open(path, 'w') as f:
                lines = '\n'.join(stockRepeats)
                f.writelines(lines)
        return
    
    def stockFetcher(self, stockID):
        #load data
        stockset = self.loadStockset()
        stockset = [stockset[tablename] for tablename in self.tablenames]
        batchlist = self.loadBatchlist()
        batchlist = [batchlist[tablename] for tablenames in self.tablenames]
        #parse stockset
        stockset = [[stockset[i][batch] for batch in table] for i, table in enumerate(batchlist)]
        stockset = [['%s_%s' %(stock, batchlist[j][i]) for i, batch in enumerate(table)  for stock in batch] for j, table in enumerate(stockset)]
        #fecth stock
        while stockset:
            try:
                stockID = stockID.upper()
                stockID = self.controlsDict[stockID]
                stockOut = [[(i, stock) for i, stock in enumerate(table) if stock.split('_')[0] == stockID] for table in stockset]
            except KeyError:
                stockID = stockID.upper()
                stockOut = [[(i, stock) for i, stock in enumerate(table) if stock.split('_')[0] == stockID] for table in stockset]
            if len([stock for table in stockOut for stock in table]) > 0:
                break
            else:
                stockInput = raw_input('Sorry, but this stock %s is not in the database! Please, choose a different stock or quit (q). \n' %stockID)
                if stockInput == 'q':
                        sys.exit()   
                else:
                    stockID = stockInput   
        return stockOut
        
    def fetchMetricsForStockset(self, stockset, tablename):
        #load metrics dictionary
        fertMetrics = self.loadFertilityMetrics()
        if isinstance(stockset[0], (tuple, list)):
            keyset = [[(stock.split('_')[1], stock.split('_')[0]) for stock in subset] for subset in stockset]
            stocksetArrs = [[fertMetrics[tablename][batch][stock] for (batch, stock) in sublist] for sublist in keyset]
            stocksetArrs = [zip(*subset) for subset in stocksetArrs]
            stocksetArrs = [[zip(*arr) for arr in subset] for subset in stocksetArrs]
        elif isinstance(stockset[0], (str, unicode)):
            keyset = [(stock.split('_')[1], stock.split('_')[0]) for stock in stockset]
            stocksetArrs = [fertMetrics[tablename][int(batch)][stock] for (batch, stock) in keyset]
            stocksetArrs = zip(*stocksetArrs) 
        return stocksetArrs
           
    def fetchRepeatsMetrics(self):
        #load data
        repeats = self.fetchRepeats()
        stockRepeats, repeatedAssays = repeats
        #parse list
        repAssayIDs = [[assayID for (i, assayID) in table] for table in repeatedAssays]
        #fetch repeats metrics
        repMetricArrs = [self.fetchMetricsForStockset(table, self.tablenames[i]) for i, table in enumerate(repAssayIDs)]
        return repMetricArrs
     
               

class FertilityDataVis(FertilityMetrics):
    
    def __init__(self):
        FertilityMetrics.__init__(self) 
        return
        
    def getMembers(self):
        import inspect
        methods = inspect.getmembers(self, predicate = inspect.ismethod)
        print(methods)
        return
        
    def generateColorMap(self, numbColors):
        from Plot_Functions import hsvGenerator
        from colorsys import hsv_to_rgb
        from matplotlib.colors import colorConverter
        cc = lambda arg: colorConverter.to_rgba(arg, alpha=0.6)
        step = 1/float(numbColors)
        hsvColorMap = hsvGenerator(step, 0.8, 0.8)
        rgbaColorMap = [cc(hsv_to_rgb(h,s,v)) for h,s,v in hsvColorMap]
        return rgbaColorMap
    
    def generatePropertySequence(self, plotset, proptyVal, **kargs):
        #assertion
        if isinstance(plotset[0], (str, unicode)):
            plotset = [plotset]
        assert (len(plotset[0]) != len(proptyVal)), 'Plotset and proptyVal length must be the same.'
        #load data
        stockset = self.unpackStockset(**kargs)
        #attach property values to each plotset
        propertyseq = []
        for i, seq in enumerate(plotset):
            sublist = [(proptyVal[i], item) for item in seq]
            propertyseq.append(sublist)
        #unpack
        propertyseq = [item for sublist in propertyseq for item in sublist]
        #match propertyseq order to stockset order
        propertyseq = [[(i, val, item) for (val, item) in propertyseq if item == stock] for i, stock in enumerate(stockset)]#match to stockset order
        propertyseq = [item for sublist in propertyseq for item in sublist]#unpack
        propertyseq = sorted(propertyseq, key = lambda x:x[0])#re-order
        propertyseq = [tupl[1] for tupl in propertyseq]#unpack property values only
        return propertyseq
    
    def getBatchLimits(self):
        import numpy as np
        #load data
        stockset = self.loadStockset()
        stockset = [stockset[tablename] for tablename in self.tablenames]
        batchlist = self.loadBatchlist()
        batchlist = [batchlist[tablename] for tablenames in self.tablenames]
        #fetch batch limits from stockset
        batchLimits = [[len(table[batch]) for batch in batchlist[i]] for i, table in enumerate(stockset)]
        batchLimits = [np.cumsum(table)-1 for table in batchLimits]
        return batchLimits
        
    def fetchPlotGroups(self, norm = False):
        #load data
        unpStockset = self.unpackStockset()
        outliers = self.fetchOutliers(norm = norm)
        if not norm:
            hits = self.fetchHits()
        #unpack controls
        ctrlTuples = self.fetchControlsIdx()
        controls = [[ctrlname for (i, ctrlname) in table] for table in ctrlTuples]
        #fetch non-signifcant groups
        outliers = [[stock for stock in table if stock not in controls[i]] for i, table in enumerate(outliers)]
        if norm:
            ns = [[stock for stock in table if stock not in outliers[i]+controls[i]] for i, table in enumerate(unpStockset)]
            plotgroups = [outliers, ns, controls]
        else:
            hits = [[stock for stock in table if stock not in outliers[i]+controls[i]] for i, table in enumerate(hits)]
            ns = [[stock for stock in table if stock not in outliers[i]+hits[i]+controls[i]] for i, table in enumerate(unpStockset)]
            plotgroups = [outliers, hits, ns, controls]
        return plotgroups
        
    def datafeedForPlotter(self, norm = False, stockID = False):
        #load data to plot
        if stockID:
            #fetch stocks to plot
            stocksOut = self.stockFetcher(stockID)#fetch stocks
            stocksOut = [[stockID for (i, stockID) in table] for table in stocksOut]#discard indices
            #load data
            clusterFertData  = self.loadClusterFertdata()
            stockdata = [[clusterFertData[self.tablenames[i]][int(stockId.split('_')[1])][stockId.split('_')[0]] for stockId in table] for i,table in enumerate(stocksOut)]
            stockdata = [[stock[1] for stock in table] for table in stockdata]#extract brood sizes
            stockmetrics = [self.fetchMetricsForStockset(stocksOut[i], tablename) for i, tablename in enumerate(self.tablenames)]#fetch brood size means
            stockmetrics = [[table[0], table[1]] for table in stockmetrics]#extract brood size means and errors
        else:
            stocksOut = []
            #load data
            stockset = self.unpackStockset()
            plotgroups = self.fetchPlotGroups(norm = norm)
            batchlimits = self.getBatchLimits()
            #unpack phenoclasses
            if norm:
                outliers, ns, controls = plotgroups
                metricsArrs = self.loadNormBatchArrays()
            else:
                metricsArrs = self.fetchFertilityMetricsArrays()
                outliers, hits, ns, controls = plotgroups
        #fetch batch and dataset metrics
        dsetMetrics = self.fetchDatasetMeans()
        batchMetrics = self.loadBatchMeans()
        #pack data for plotter
        if stockID:
            plotterData = [stocksOut, stockdata, batchMetrics, stockmetrics]
        else:
            plotterData = [stockset, stocksOut, metricsArrs, dsetMetrics, batchMetrics, batchlimits]
        return plotterData
    
    def datasetLayout(self, args):
        import matplotlib.pyplot as plt
        import numpy as np
        #unpack args
        ax1, ax2, stockset, metricsArrs, dsetMetrics, batchMetrics, batchlimits, norm = args
        #fetch plotgroups and unpack
        plotgroups = self.fetchPlotGroups(norm = norm)
        if norm:
            outliers, ns, controls = plotgroups
        else:
            outliers, hits, ns, controls = plotgroups 
        #define xsets
        xsetF, xsetM = [np.arange(len(table)) for table in stockset]
        #unpack metrics arrays
        dsetF, dsetM = dsetMetrics
        batchmeans, err_batchmeans= batchMetrics
        if norm:
            metricsArrs = [[[val for batch in table for val in batch] for table in metric] for metric in metricsArrs]#unpack
            arrF, arrM = zip(*metricsArrs)
        else:
            arrF, arrM = metricsArrs
        #generate color and size sequences
        if norm:
            plotsets = [[outliers[i], controls[i], ns[i]] for i in xrange(len(self.tablenames))]
            colourSet = ['r', 'y', '#D1D1D1']
            sizeSet = [10, 8, 6]
        else:
            plotsets = [[outliers[i], hits[i], controls[i], ns[i]] for i in xrange(len(self.tablenames))]
            colourSet = ['r', 'b', 'y', '#D1D1D1']
            sizeSet = [10, 10, 8, 6]
        
        colorseqF, colorseqM = [self.generatePropertySequence(plotset, colourSet, tablename = self.tablenames[i]) for i, plotset in enumerate(plotsets)]
        sizeseqF, sizeseqM = [self.generatePropertySequence(plotset, sizeSet, tablename = self.tablenames[i]) for i, plotset in enumerate(plotsets)]
        #calculate batchmeans xcoord
        xbatchmeans = [[int(val + (table[i+1]-val)/2) for i, val in enumerate(table[:-1])] for table in batchlimits]
        [table.insert(0, int(batchlimits[i][0]/2)) for i, table in enumerate(xbatchmeans)]
        xbatchmeansF, xbatchmeansM = xbatchmeans
        #Brood size plots    
        ax1.scatter(xsetF, arrF[0], s = sizeseqF,  color = colorseqF)
        if not norm:
            ax1.scatter(xbatchmeansF, batchmeans[0], s = 8, color = '#080707', alpha = 0.5)
            ax1.errorbar(xbatchmeansF, batchmeans[0], yerr = err_batchmeans[0], fmt= None, ecolor = '#000608')
        
        ml = min(len(xsetM), len( arrM[0]))
        #ax2.scatter(xsetM, arrM[0], s = sizeseqM,  color = colorseqM)
        ax2.scatter(xsetM[:ml], arrM[0][:ml], s = sizeseqM,  color = colorseqM)
        if not norm:
            ax2.scatter(xbatchmeansM, batchmeans[1], s = 8, color = '#080707', alpha = 0.5)
            ax2.errorbar(xbatchmeansM, batchmeans[1], yerr = err_batchmeans[1], fmt= None, ecolor = '#000608')
        #titles
        ax1.set_title('Female fertility', fontsize = 14)
        ax2.set_title('Male fertility', fontsize = 14)
        #xAxis ticks, labels and lines
        ax1.set_xticks(xsetF)
        ax1.set_xticklabels(stockset[0], rotation = 60, size = 10)
        ax2.set_xticks(xsetM)
        ax2.set_xticklabels(stockset[1], rotation = 60, size = 10)
        #limits
        if norm:
            ax1.set_ylim([-0.1, 2.0])
            ax2.set_ylim([-0.1, 2.0])
        else:    
            ax1.set_ylim([-10, 160])
            ax2.set_ylim([-10, 100])
        #custom artists for legends
        zArtist = plt.Line2D((0,0), (0, 1), color='r', marker='o', ms = 3, mec = 'r', linestyle='')
        ctrlArtist = plt.Line2D((2,0), (2, 1), color='y', marker='o', ms = 3, mec = 'y', linestyle='')
        #legends
        if norm:
            ax1.legend([zArtist, ctrlArtist], ['Outliers', 'Controls (+)'], fontsize = 8)
            ax2.legend([zArtist, ctrlArtist], ['Outliers', 'Controls (+)'], fontsize = 8)
        else:
            batchMean_artist = plt.Line2D((3,0), (3, 1), color='#080707', alpha = 0.5, marker='o', ms = 3, mec = '#080707', linestyle='')
            fdrArtist = plt.Line2D((1,0), (1, 1), color='b', marker='o', ms = 3, mec = 'b', linestyle='')
            ax1.legend([zArtist, fdrArtist, ctrlArtist, batchMean_artist], ['z >= 2.5', "< FDR", 'Controls (+)', 'batch mean'], fontsize = 8)
            ax2.legend([zArtist, fdrArtist, ctrlArtist, batchMean_artist], ['z >= 2.5', "< FDR", 'Controls (+)', 'batch mean'], fontsize = 8)
        #Margins
        axes = [ax1, ax2]
        [ax.margins(0.01) for ax in axes]
        #batch limits: verical lines
        for i, table in enumerate(batchlimits):
            for limit in table:
                axes[i].axvline(limit, 0, color = '#ADADAD', linestyle = '--', alpha = 0.5)
        #Axes labels and limits
        if norm:
            for ax in axes:        
                ax.set_xlabel('RNAi line')
                ax.set_ylabel('Batch normalised brood size')
        else:
            for ax in axes:        
                ax.set_xlabel('RNAi line')
                ax.set_ylabel('Brood size')
        return ax1, ax2
        
    def datasetPlotter(self, norm = False, cursor = False):
        import matplotlib.pyplot as plt
        #sys.path.append('C:\Python27\Lib\site-packages')
        from mpldatacursor import datacursor
        #define figure layout
        fig, (ax1, ax2) = plt.subplots(2, 1, sharex = 'none', sharey = 'none')
        #load data
        plotterData = self.datafeedForPlotter(norm = norm)
        [stockset, stocksOut, metricsArrs, dsetMetrics, batchMetrics, batchlimits] = plotterData
        #define arguments
        args = ax1, ax2, stockset, metricsArrs, dsetMetrics, batchMetrics, batchlimits, norm
        ax1, ax2 = self.datasetLayout(args)
        if cursor:
            axes = [ax1, ax2]
            datapoint_sets = [ax.collections[0] for ax in axes]
            datapoint_labels = [self.unpackStockset()[i] for i, ax in enumerate(axes)]
            #label datapoints interactively
            for i, ax in enumerate(axes):
                datacursor(datapoint_sets[i], hover=True, point_labels = datapoint_labels[i], fontsize = 10, bbox= None, xytext=(0, 25), formatter=lambda **kwargs: kwargs['point_label'][0])
        plt.tight_layout()
        plt.show()
        return 
        
    def stockLayout(self, args):
        import matplotlib.pyplot as plt
        import numpy as np
        #unpack args
        ax1, ax2, stocksOut, stockdata, batchMetrics, stockmetrics = args
        batchmeans , err_batchmeans = batchMetrics
        stockmetricsF, stockmetricsM = stockmetrics
        #define xsets
        xsets = [[[i+1]*len(stock) for i, stock in enumerate(table)] for table in stockdata]
        xsetF, xsetM = [[val for stock in table for val in stock] for table in xsets]#unpack
        #unpack stockdata
        stockdata = [[val for stock in table for val in stock] for table in stockdata]
        arrF, arrM = stockdata
        stocksF, stocksM = stocksOut
        stockname = stocksF[0].split('_')[0]
        #fetch batch means
        batchnumbers = [[int(stockId.split('_')[1]) for stockId in table] for table in stocksOut]
        batchmeans = [[batchmeans[i][batchnumber-1] for batchnumber in table]for i, table in enumerate(batchnumbers)]
        err_batchmeans = [[err_batchmeans[i][batchnumber-1] for batchnumber in table]for i, table in enumerate(batchnumbers)]
        #Brood size plots    
        ax1.scatter(xsetF, arrF, s = 9, color = 'b')
        ax1.scatter(np.arange(1, len(stocksF)+1), stockmetricsF[0], marker = "_", s = 50, color = 'r')#assay means
        ax1.errorbar(np.arange(1, len(stocksF)+1), stockmetricsF[0], yerr = stockmetricsF[1], fmt= None, ecolor = '#C1C7C9')#errors
        ax1.scatter(np.arange(1, len(stocksF)+1), batchmeans[0], marker = "^", s = 14, color = 'r')#batch means
        ax1.errorbar(np.arange(1, len(stocksF)+1), batchmeans[0], yerr = err_batchmeans[0], fmt= None, ecolor = '#0F0F0F')#batch errors
        bsM = ax2.scatter(xsetM, arrM, s = 9, color = 'b')
        bsMean = ax2.scatter(np.arange(1, len(stocksM)+1), stockmetricsM[0], marker = "_", s = 50, color = 'r')#assay means
        ax2.errorbar(np.arange(1, len(stocksM)+1), stockmetricsM[0], yerr = stockmetricsM[1], fmt= None, ecolor = '#C1C7C9')#errors
        batchMean = ax2.scatter(np.arange(1, len(stocksM)+1), batchmeans[1], marker = "^", s = 14, color = 'r')#batch means
        ax2.errorbar(np.arange(1, len(stocksM)+1), batchmeans[1], yerr = err_batchmeans[1], fmt= None, ecolor = '#0F0F0F')#batch errors
        #legends
        ax2.legend([bsM, bsMean, batchMean], ['Brood size', 'Mean brood size', 'Batch mean'], fontsize = 10)
        #titles
        ax1.set_title('%s: females' %stockname, fontsize = 13)
        ax2.set_title('%s: males' %stockname, fontsize = 13)
        #xAxis ticks, labels and lines
        ax1.set_xticks(np.arange(1, len(stocksF)+1))
        ax1.set_xticklabels(stocksF, rotation = 60, size = 10)
        ax2.set_xticks(np.arange(1, len(stocksM)+1))
        ax2.set_xticklabels(stocksM, rotation = 60, size = 10)
        #Axes labels
        ax1.set_xlabel('AssayID')
        ax1.set_ylabel('Brood size')
        ax2.set_xlabel('AssayID')
        ax2.set_ylabel('Brood size')
        return ax1, ax2 

          
    def stockPlotter(self, stockID):
        import matplotlib.pyplot as plt
        #define figure layout
        fig, (ax1, ax2) = plt.subplots(1, 2, sharex = 'none', sharey = 'none')
        #load data
        plotterData = self.datafeedForPlotter(stockID = stockID)
        [stocksOut, stockdata, batchMetrics, stockmetrics] = plotterData
        #define arguments
        args = ax1, ax2, stocksOut, stockdata, batchMetrics, stockmetrics
        ax1, ax2 = self.stockLayout(args)
        plt.tight_layout()
        plt.show()
        return 
   
    
    def imageFetcher(self, stockID, gender, batch):
        import matplotlib.pyplot as plt
        #sys.path.append('C:\Python27\Lib\site-packages')
        import cv2
        #fetch stocks to plot
        stocksOut = self.stockFetcher(stockID)#fetch stocks
        stocksOut = [[stockID for (i, stockID) in table] for table in stocksOut]#discard indices
        stockname = stocksOut[0][0].split('_')[0]
        #fetch image names
        clusterFertdata = self.loadClusterFertdata()
        filenames, broodsizes, zscores = clusterFertdata[gender][batch][stockname]
        filenames = [filename[:-4] + '_overlay.jpg' for filename in filenames]
        #fetch image paths
        subdirsDict = {'females':'MTD', 'males':'BAM'}
        overlaysDir = os.path.join(self.basedir, 'UK%s\%s\Overlays' %(batch, subdirsDict[gender]))
        imgPaths = [os.path.join(overlaysDir, filename) for filename in filenames]
        #Define grid: number of rows
        rows = len(imgPaths)/3 + int(len(imgPaths)%3>0)
        #Display images
        fig = plt.figure()
        for i, path in enumerate(imgPaths):
            img = cv2.imread(path, 1)
            ax = plt.subplot(rows, 3, i+1)
            ax.text(0.95, 0.01, 'N = %i' %broodsizes[i], verticalalignment = 'bottom', horizontalalignment = 'right', transform = ax.transAxes, color='#0D0D0D', fontsize = 10)
            plt.imshow(img, interpolation = 'bicubic')
            plt.xticks([])
            plt.yticks([])
        plt.suptitle('AssayID: %s_%s (%s)' %(stockname, batch, gender), fontsize = 13)
        if len(imgPaths) <= 3:
            fig.tight_layout(pad = 2.5 , h_pad = 0.3, w_pad = 1)
        elif 3 < len(imgPaths) <= 6:
            fig.tight_layout(pad = 2.5 , h_pad = 0.3, w_pad = 1)
        elif 6 < len(imgPaths) <= 9:
            fig.tight_layout(pad = 2.5 , h_pad = 0.5, w_pad = -1.0)  
        else:    
            fig.tight_layout(pad = 2.5 , h_pad = 0.3, w_pad = -12)
        plt.show(fig)
        return



    

#fdb = FertilityDB()        
#fm = FertilityMetrics()         
#fdv = FertilityDataVis()
#fdv.datasetPlotter(norm = False)
#fdv.stockPlotter('js40')
#fdv.imageFetcher('empty', 'females', 6)
#fdv.stockPlotter('js19')
#outliers = fm.fetchOutliers(norm = True)

