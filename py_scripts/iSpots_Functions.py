import os
import sys
import numpy as np

class Dashboard():
    def __init__(self):
        cwd = os.getcwd()
        self.cwd = cwd
        self.dbdir = '%s\Dropbox\Unknome\Databases' %self.cwd
        self.dbpath = os.path.join(self.dbdir, 'iSpotsDB.db')
        self.basedir = 'U:\Proteostasis_screen'
        self.spotsdir = '%s\Dropbox\Unknome\Screens\ProteostasisScreen\iSpots' %self.cwd
        self.rawdatadir = os.path.join(self.spotsdir, 'RawData')
        self.pickledir = os.path.join(self.spotsdir, 'PickleFiles')
        self.workdir = os.path.join(self.spotsdir, 'FilesOut')
        self.batchdirnames = self.getBatchDirNames()
        self.controlsDict = self.controlsDict()
        self.ctrlnames = self.controlsNames()
        self.valRNAi = self.validationRNAis().values()
        self.usedcontrols = self.usedControls()
        
        
    def getMembers(self):
        import inspect
        methods = inspect.getmembers(self, predicate = inspect.ismethod)
        print(methods)
        return
        
    def getBatchDirNames(self):
        batchDirnames = os.listdir(self.rawdatadir)
        batchnumbers = [int(dirname.split('_')[0][5:]) for dirname in batchDirnames]
        batchdirnames = dict(zip(batchnumbers, batchDirnames))
        return batchdirnames
        
    def controlsDict(self):
        #Define dictionary
        controlsDict = {'EMPTY': 'Empty', 'GFPI': 'GFPi', 'W1118': 'w1118', 'HSP70' : 'Hsp70'}
        return controlsDict
    
    def validationRNAis(self):
        valRNAiDict = {'JS10':'50596', 'JS27':'44017', 'JS141':'21566', 'JS169':('38257', '40926'), 'JS188':'33882', 'JS190':('10646R1', '10646R2'), 'JS193':'11127', 'JS199':'37490'}
        return valRNAiDict
    
    def otherControlsDict(self):
        import cPickle as pickle
        picklepath = os.path.join(self.pickledir, 'otherControlsDict.pickle')
        with open(picklepath, 'r') as f:
            otherControlsDict = pickle.load(f) 
        return otherControlsDict
    
    def controlsNames(self):
        ctrlNames = self.controlsDict.values()
        return ctrlNames
    
    def usedControls(self):
        otherControls = self.otherControlsDict()
        usedControls = [stock for stock in otherControls.keys() if otherControls[stock][1] == 1]
        return usedControls
        
    def purgePickleDir(self, fnum = 2):
        '''It purges pickledir of older file versions; fnum (int) defines the maximum number of file versions to keep.
        Pickle files purged are: wingsDict, wingMetrics, trimAreasArr, clusterWingdata, clusterImgdata and rajenDict.'''
        #Define filenames
        filenames = ['assaySet', 'conflictData', 'dsetForPlotter', 'spotsDict', 'stocksDataDict', 'rajenDict']
        #Fetch and sort filelist
        filelist = [[f for f in os.listdir(self.pickledir) if f.startswith(name)] for name in filenames]
        [sublist.sort() for sublist in filelist] #sort filelist
        #Purge filelist
        filelist_topurge = [sublist[:-fnum] for sublist in filelist]
        #Purge pickleDir
        [[os.remove(os.path.join(self.pickledir, filename)) for filename in sublist] for sublist in filelist_topurge]
        return    
             
    def createSpotsDB(self):
        #Create Eye_Areas table
        SpotsDB().addAreasTable()
        #Fetch spots data and create batch tables
        batchnumbers = SpotsDB().batchdirnames.keys()
        SpotsDB().addBatchTable(batchnumbers)
        return   
        
    def resetMetrics(self):
        SpotsObjects().buildSpotsDict()
        SpotsObjects().fetchAssaySet()
        SpotsObjects().buildStocksDataDict()
        SpotsObjects().buildRepeatsDict()
        SpotsObjects().buildRajenDict()
        SpotsObjects().fetchDataForDsetPlotter()
        self.purgePickleDir()
        return
    
    def resetWorkEnv(self):
        self.createSpotsDB()
        self.resetMetrics()
        return
        
        
                                                    
class SpotsDB(Dashboard):
    
    def __init__(self):
        Dashboard.__init__(self)

    def getMembers(self):
        import inspect
        methods = inspect.getmembers(self, predicate = inspect.ismethod)
        print(methods)
        return
     
    def fetchSpotsData(self, batchnumber):
        from File_Functions import dictFromFile
        batchname = 'Batch%i' %batchnumber
        print('Fetching rows from %s\n' %batchname) 
        #Fetch textfile's paths
        batchdirname = self.batchdirnames[batchnumber]#fetch batch directory
        batchdir = os.path.join(self.rawdatadir, batchdirname)
        textfilepathList = [os.path.join(batchdir, filename) for filename in os.listdir(batchdir) if not filename.startswith('TotalAreas')]
        #Fetch data from textfiles
        data = [dictFromFile(path, 1, skiprows = 1, usecols = [2,3,4,5,6,7], colasarr = False, order = True) for path in textfilepathList]
        #Rearrange data into rows
        print('Rearranging data into rows. \n')
        data = [[(['%s_b%i' %(key.split(':')[0][:-4],batchnumber), key] , subitem[key].values()) for key in subitem.keys()] for subitem in data]
        rows = [[[item for row in rows for item in row] for rows in batch] for batch in data]#unpack rows
        rows = [row for batch in rows for row in batch]#unpack batches
        rows = [[int(item) if isinstance(item, np.int64) else item for item in row] for row in rows]#reformat datatype
        #rows = [tuple(['nan' if isinstance(item, float) and np.isnan(item) else item for item in row]) for row in rows]
        return rows
    
    
    def fetchEyeAreas(self, batchnumber):
        from File_Functions import dictFromFile
        batchname = 'Batch%i' %batchnumber
        print('Fetching areas from batch %s\n' %batchname)
        #Fetch areas file path
        batchdirname = self.batchdirnames[batchnumber]#fetch batch directory
        batchdir = os.path.join(self.rawdatadir, batchdirname)
        areasPath = [os.path.join(batchdir, filename) for filename in os.listdir(batchdir) if filename.startswith('TotalAreas')][0]
        #Fetch data from textfile
        data = dictFromFile(areasPath, 1, usecols = 2, colasarr = False, order = True)
        #Rearrange data into rows
        print('Rearranging data into rows. \n')
        rows = [(batchnumber, '%s_b%i' %(key.split(':')[0][:-4], batchnumber) , data[key]) for key in data.keys()] 
        rows = [[int(item) if isinstance(item, np.int64) else item for item in row] for row in rows]#reformat datatype
        return rows
        
        
    def createBatchTable(self, tablename):
        import sqlite3
        #Connect to database
        db = sqlite3.connect(self.dbpath)
        cursor = db.cursor()
        print('Creating table %s. \n' %tablename)
        createStatement = '''CREATE TABLE  %s (sqlKey INTEGER PRIMARY KEY AUTOINCREMENT, Eye TEXT NOT NULL, Spot TEXT NOT NULL, Area INT NOT NULL,
            
        Mean REAL, stDev REAL, Min INT NOT NULL, Max INT NOT NULL, IntDensity REAL NOT NULL, FOREIGN KEY(Eye) REFERENCES Eye_Areas(Eye))''' %tablename
        cursor.execute(createStatement)
        db.commit()
        db.close()
        return   
           
           
    def fillBatchTable(self, tabledata):
        import sqlite3
        #Connect to database
        db = sqlite3.connect(self.dbpath)
        cursor = db.cursor()
        #Unpack tabledata
        tablename, rows = tabledata
        #test whether table alrady exists            
        try:    
            cursor.execute('''SELECT name FROM sqlite_sequence WHERE name = ?''', (tablename,))
            if len(cursor.fetchall()) == 0:
                self.createBatchTable()          
            else:
                print('Table %s already exists. \n' %tablename)
        except:       
            self.createBatchTable()
        #insert data    
        insertStatement = '''INSERT INTO %s (Eye, Spot, Area, Mean, StDev, Min, Max, IntDensity) VALUES(?,?,?,?,?,?,?,?)''' %tablename 
        print('Inserting data in table %s. \n' %tablename) 
        cursor.executemany(insertStatement, rows)
        db.commit()
        db.close()
        return
    
    
    def createAreasTable(self, tablename):
        import sqlite3
        #Connect to database
        db = sqlite3.connect(self.dbpath)
        cursor = db.cursor()
        #create table
        print('Creating table %s. \n' %tablename)
        createStatement = '''CREATE TABLE  %s (sqlKey INTEGER PRIMARY KEY AUTOINCREMENT, Batch INT NOT NULL, Eye TEXT NOT NULL, Area INT NOT NULL)''' %tablename
        cursor.execute(createStatement)
        db.commit()
        db.close()
        return
        
            
    def fillAreasTable(self, rows):
        import sqlite3
        #Connect to database
        db = sqlite3.connect(self.dbpath)
        cursor = db.cursor()
        #test whether table exists
        tablename = 'Eye_Areas'    
        try:    
            cursor.execute('''SELECT name FROM sqlite_sequence WHERE name = ?''', (tablename,))
            if len(cursor.fetchall()) == 0:
                self.createAreasTable(tablename)   
            else:
                answer = raw_input('Table %s already exists. Replace table(y/n)? \n' %tablename)
                while answer:
                    if answer.lower() == 'y':
                        cursor.execute('''DROP TABLE Eye Areas''')
                        self.createAreasTable(tablename)
                        break
                    elif answer.lower() == 'n':
                        print('Table %s remains unaltered. \n' %tablename)
                        sys.exit()
                    else:
                        answer = raw_input('Limit your answer to either yes (y) or no (n). Replace table %s (y/n)? \n' %tablename)
        except:       
            self.createAreasTable(tablename)   
        #insert data    
        insertStatement = '''INSERT INTO %s (Batch, Eye, Area) VALUES(?,?,?)''' %tablename
        print('Inserting data in table %s. \n' %tablename) 
        cursor.executemany(insertStatement, rows)
        db.commit()
        db.close()
        return
    
    
    def addBatchTables(self, batchnumbers):
        #test datatype
        if isinstance(batchnumbers, int):
            batchnumbers = [batchnumbers]
        elif not isinstance(batchnumbers, (list, tuple)):
            print('Datatype error: function arg datatype is either str or a sequence, list or tuple. ')
            return
        #add tables to database    
        for batchnumber in batchnumbers:
            rows = self.fetchSpotsData(batchnumber)
            tabledata = (self.batchdirnames[batchnumber], rows)
            self.fillBatchTable(tabledata)        
        return
        
    
    def addAreasTable(self): 
        #fetch batchnumbers
        batchnumbers = self.batchdirnames.keys()
        #fetch rows
        rows = [self.fetchEyeAreas(batchnumber) for batchnumber in batchnumbers]
        rows = [row for batch in rows for row in batch] #unpack rows
        #create tables
        self.fillAreasTable(rows)
        return 
    
    
    def updateAreasTable(self, batchnumber):
        import sqlite3
        #Connect to database
        db = sqlite3.connect(self.dbpath)
        cursor = db.cursor()
        #Define batch
        batchname = self.batchdirnames[batchnumber]
        #Fetch eye areas
        rows = self.fetchEyeAreas(batchnumber)
        #insert data and test whether table and entries already exist
        try:    
            cursor.execute('''SELECT Batch FROM Eye_Areas WHERE Batch = ?''', (batchnumber,))
            if len(cursor.fetchall()) == 0:
                insertStatement = '''INSERT INTO Eye_Areas (Eye, Area) VALUES(?,?)'''
                cursor.executemany(insertStatement, rows)
            else:
                print('Entries for %s are already in the table. \n' %batchname)
                sys.exit()
        except:
            print('The table Eye Areas does not exist in the datasbase. \n')
        return
                
                              

class SpotsObjects(Dashboard):
    
    def __init__(self):
        Dashboard.__init__(self)
        self.assayset = self.loadAssayset()
    
    def buildSpotsDict(self):
        from itertools import chain
        import cPickle as pickle
        from datetime import datetime
        import sqlite3
        #Connect to database
        db = sqlite3.connect(self.dbpath)
        cursor = db.cursor()
        #Fetch tablenames
        cursor.execute('''SELECT name FROM sqlite_sequence''')
        tablenames = [str(name) for name in chain(*cursor.fetchall()) if name.startswith('Batch')]
        tablenames = sorted(tablenames, key = lambda x: int(x.split('_')[0][5:]))
        #Fetch eyes from each batch
        selectStatement = ['''SELECT Eye FROM Eye_Areas WHERE Batch = %i ''' %(i+1) for i, name in enumerate(tablenames)]
        eyes = []
        for selection in selectStatement:
            cursor.execute(selection)
            batchdata = [str(name) for name in chain(*cursor.fetchall())]
            eyes.append(batchdata)
        #Fetch spots areas for each eye
        selectStatement = [['SELECT Area FROM %s WHERE Eye = "%s"' %(name, eye) for eye in eyes[i]] for i, name in enumerate(tablenames)]
        data = []
        for i, batch in enumerate(selectStatement):
            data.append([])
            for selection in batch:
                cursor.execute(selection)
                eyedata = cursor.fetchall()
                data[i].append(eyedata)
        #Cluster spots with eyes
        data = [[zip(*eye) for eye in batch] for batch in data]
        #Fetch stockset
        stockset = list(set([eye.split('_')[0] for batch in eyes for eye in batch]))
        #Cluster eyes with stocks
        data = [zip(batch, data[i]) for i, batch in enumerate(eyes)]#cluster areas with respective eye Ids
        data = [eye for batch in data for eye in batch]#unpack data
        excludEyes = [eye[0] for eye in data if len(eye[1]) == 0]#eyes excluded
        data = [(eye[0], eye[1][0]) for eye in data if len(eye[1]) > 0]#filter out stocks not in the database
        data = [[eye for eye in data if eye[0].split('_')[0] == stock] for stock in stockset]#cluster eyes per stock
        tbdStocks = [stockset[i] for i, stock in enumerate(data) if len(stock) == 0]#stocks not in the database
        fewEyes = [stock[0][0].split('_')[0] for stock in data if 0 < len(stock) < 7]#stocks with few eyes
        data = [(stock[0][0].split('_')[0], stock) for stock in data if len(stock) > 0]
        #Fetch current time and date
        time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        #Serialize dictionary of data
        spotsDict = dict(data)
        filename = 'spotsDict_%s.pickle' %time
        picklepath = os.path.join(self.pickledir, filename)
        with open(picklepath, 'w') as f:
            pickle.dump(spotsDict, f)   
        #Serialize lists of conflicting eyes and stocks
        conflictData = [excludEyes, fewEyes, tbdStocks]
        filename = 'conflictData_%s.pickle' %time
        picklepath = os.path.join(self.pickledir, filename)
        with open(picklepath, 'w') as f:
            pickle.dump(conflictData, f)
        return
        
    def loadSpotsDict(self):
        import cPickle as pickle
        '''Loads the latest version of spotsDict.'''
        #Load spots dictionary
        filelist = [filename for filename in os.listdir(self.pickledir) if filename.startswith('spotsDict')]
        filelist.sort()
        picklefile = filelist[-1]
        picklepath = os.path.join(self.pickledir, picklefile)
        with open(picklepath, 'r') as f:
            spotsDict = pickle.load(f)       
        return spotsDict
    
        
    def fetchAssaySet(self):
        from datetime import datetime
        import cPickle as pickle
        from File_Functions import listPartition
        spotsDict = self.loadSpotsDict()
        eyeIDs, spotAreas = zip(*[eye for stock in spotsDict.values() for eye in stock])
        batchset, assayset = zip(*[('%s'%eye.split('_')[2], '%s_%s' %(eye.split('_')[0], eye.split('_')[2])) for eye in eyeIDs])
        batchset = sorted(set(batchset), key = lambda x:int(x[1:]))#order batches
        batchnumbers = [int(batch[1:]) for batch in batchset]
        #rearrange assayset
        assayset = sorted(set(assayset), key = lambda x:int(x.split('_')[1][1:]))#sort assayset in batches
        assayset = [[eye for eye in assayset if eye.split('_')[1] == batch] for batch in batchset]#cluster assays in batches
        assayset = [listPartition(lambda x:x.startswith('JS'), batch) for batch in assayset]#split assayset in stocks and controls
        assayset = [(sorted(batch[0], key = lambda x:int(x.split('_')[0][2:])), sorted(batch[1], key = lambda x:x)) for batch in assayset]#sort stocks and controls
        assayset = [(batch[0] + batch[1]) for batch in assayset]#join stocks and controls
        #build dictionary 
        assayset = dict(zip(batchnumbers, assayset))
        #Fetch current time and date
        time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        #serialize dictionary
        filename = 'assaySet_%s.pickle' %time
        picklepath = os.path.join(self.pickledir, filename)
        with open(picklepath, 'w') as f:
            pickle.dump(assayset, f)
        return  
        
    def loadAssayset(self):
        import cPickle as pickle
        #Load spots dictionary
        filelist = [filename for filename in os.listdir(self.pickledir) if filename.startswith('assaySet')]
        filelist.sort()
        picklefile = filelist[-1]
        picklepath = os.path.join(self.pickledir, picklefile)
        with open(picklepath, 'r') as f:
            assayset = pickle.load(f)
        return assayset
        
    def loadConflictData(self):
        import cPickle as pickle
        '''Loads the latest version of conflictData.'''
        #Load conflicting data
        filelist = [filename for filename in os.listdir(self.pickledir) if filename.startswith('conflictData')]
        filelist.sort()
        picklefile = filelist[-1]
        picklepath = os.path.join(self.pickledir, picklefile)
        with open(picklepath, 'r') as f:
            conflictData = pickle.load(f)
        return conflictData
        
    def loadAreasDict(self):
        import sqlite3
        #Connect to database
        db = sqlite3.connect(self.dbpath)
        cursor = db.cursor()
        #Fetch data from areas table
        cursor.execute('''SELECT Eye, Area FROM Eye_Areas ''')
        data = cursor.fetchall()
        data = [(str(eye[0]), eye[1]) for eye in data]#refomat keys datatype
        #build dictionary
        areasDict = dict(data)
        return areasDict
        
    def buildRepeatsDict(self):
        import cPickle as pickle
        #load dictionaries
        spotsDict = self.loadSpotsDict()
        stockset = spotsDict.keys()
        assayset = self.loadAssayset()
        #fetch repeats
        assayset = [assay for batch in assayset.values() for assay in batch]#unpack
        repeats = [[assay for assay in assayset if assay.split('_')[0] == stock] for stock in stockset]
        repeats = [sublist for sublist in repeats if len(sublist)>1]#filter out repeats
        repeats = [(sublist[0].split('_')[0], sublist) for sublist in repeats]#unpack
        #build dictionary and serialise it
        repeatsDict = dict(repeats)
        picklepath = os.path.join(self.pickledir, 'repeats.pickle')
        with open(picklepath, 'w') as f:
            pickle.dump(repeatsDict, f)
        return
    
    def loadRepeatsDict(self):
        import cPickle as pickle
        picklepath = os.path.join(self.pickledir, 'repeats.pickle')
        with open(picklepath, 'r') as f:
            repeatsDict = pickle.load(f)
        return repeatsDict
        
    def buildStocksDataDict(self):
        from datetime import datetime
        import cPickle as pickle
        #fetch stockdata
        stocksdata = []
        for stock in self.stockset:
            print('Fetching %s stockdata' %stock)
            stockdata = self.stockDataFetcher(stock)
            stocksdata.append(stockdata)
        #build dictionary
        stockdataDict = dict(zip(self.stockset, stocksdata))
        #Fetch current time and date
        time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        #serialise dictionary
        filename = 'stocksDataDict_%s.pickle' %time
        picklepath = os.path.join(self.pickledir, filename)
        with open(picklepath, 'wb') as f:
            pickle.dump(stockdataDict, f, protocol = 2)
        return
        
    def loadStocksData(self):
        import cPickle as pickle
        #Load stocksdata dictionary
        filelist = [filename for filename in os.listdir(self.pickledir) if filename.startswith('stocksDataDict')]
        filelist.sort()
        picklefile = filelist[-1]
        picklepath = os.path.join(self.pickledir, picklefile)
        with open(picklepath, 'rb') as f:
            stocksDataDict = pickle.load(f)
        return stocksDataDict
        
    
    def fetchDataForDsetPlotter(self):
        from datetime import datetime
        import cPickle as pickle
        from itertools import ifilter
        #load dictionaries
        spotsDict = self.loadSpotsDict()
        stocksdata = self.loadStocksData()
        ctrlnames = self.controlsNames()
        stockset_unfiltered = spotsDict.keys()
        stockset_filtered = list(ifilter(lambda x:x not in ctrlnames, stockset_unfiltered))
        stocksets = [stockset_unfiltered, stockset_filtered]
        keys = ['unfiltered', 'filtered']
        #Fetch batchdata and assayset labels
        dsetForPlotter = {}
        for i, sublist in enumerate(stocksets):
            batchdata = []
            assayset = []
            for stock in sublist:
                try:
                    stockdata = stocksdata[stock][1]['batches']['geomean50']
                    [batchdata.append(batch) for batch in stockdata]
                except TypeError:
                    stockdata = stocksdata[stock][1]['stocks']['geomean50']
                    batchdata.append(stockdata)
                #fetch assayIds
                eyeIds = stocksdata[stock][0][0]
                if isinstance(eyeIds[0], str):
                    eyeIds = [eyeIds]
                assaylabels = [batch[0] for batch in eyeIds]
                assaylabels = ['%s_%s' %(label.split('_')[0], label.split('_')[2]) for label in assaylabels]
                [assayset.append(label) for label in assaylabels]    
                                                        
            x, y = zip(*batchdata)
            data = [x, y, assayset]
            dsetForPlotter[keys[i]] = data
        #Fetch current time and date
        time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        #serialize data
        picklepath = os.path.join(self.pickledir, 'dsetForPlotter_%s.pickle' %time)
        with open (picklepath, 'w') as f:
            pickle.dump(dsetForPlotter, f)
        return
        
        
    def loadDataForDsetPlotter(self):
        import cPickle as pickle
        filelist = [filename for filename in os.listdir(self.pickledir) if filename.startswith('dsetForPlotter')]
        filelist.sort()
        picklefile = filelist[-1]
        picklepath = os.path.join(self.pickledir, picklefile)
        with open(picklepath, 'r') as f:
            dataForPlotter = pickle.load(f)
        return dataForPlotter
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          
        
                    
class SpotsMetrics(SpotsObjects):
    
    def __init__(self):
        SpotsObjects.__init__(self)
    
    def getMembers(self):
        import inspect
        methods = inspect.getmembers(self, predicate = inspect.ismethod)
        print(methods)
        return       
        
    def printConflictData(self):
        '''Print conflicting data: excluded eye images, stocks to be done and stocks whose samples are small'''
        conflictData = self.loadConflictData()
        excludEyes, fewEyes, tbdStocks = conflictData
        print('Exluded eye images: %s\n\nSample small: %s\n\nStocks to be done: %s' %(excludEyes, fewEyes, tbdStocks))
        return
        
    def isControl(self, name):
        #fetch control name
        try:
            name = name.upper()
            stockname = self.controlsDict[name]
        except KeyError:
            stockname = name 
        return stockname
    
    def fetchRepeats(self):
        repeatsDict = SpotsObjects().loadRepeatsDict()
        repeats = repeatsDict.keys()
        return repeats     
           
    def loadStockset(self):
        from File_Functions import listPartition
        #load spots dictionary
        spotsDict = self.loadSpotsDict()
        stocks, controls = listPartition(lambda x: x.startswith('JS'), spotsDict.keys())
        controls.sort()
        stocks = sorted(stocks, key = lambda x:int(x[2:]))
        stockset = stocks + controls
        return stockset
    
                              
    def clusterEyes(self, eyeData_stock):
        eyeIds, spotAreas = eyeData_stock#unpack
        batchlist = list(set([eye.split('_')[2] for eye in eyeIds]))
        if len(batchlist) > 1:
            batchlist = sorted(batchlist, key = lambda x:int(x[1:]))#sort batchlist
            clusterData = [[(i, eye, spotAreas[i]) for i, eye in enumerate(eyeIds) if eye.split('_')[2] == batch] for batch in batchlist]
            zipdata = [zip(*batch) for batch in clusterData]
            clusterEyes_stock = idx, eyeIds, spotAreas = [batch[0] for batch in zipdata], [batch[1] for batch in zipdata], [batch[2] for batch in zipdata]
        elif len(batchlist) == 1:
            clusterEyes_stock = None
        return clusterEyes_stock, batchlist  
    
    
    def spotAreasHistogram(self, rawdata, trim = True, rank = 0.95):
        from scipy import stats
        #Test input data
        try:
            eyes_keys, spotAreas = rawdata
        except ValueError:
            spotAreas = rawdata
        #Calculate histogram range and number of bins 
        unpackdata = [val for eye in spotAreas for val in eye] # unpack data
        limits = (float(min(unpackdata)), float(max(unpackdata)))
        binNumber = int(float(limits[1] - limits[0])/5)
        #Calculate areas histograms for each eye
        spotAreasHist_eye = [np.histogram(eye, bins=binNumber, range=limits, density=False) for eye in spotAreas]
        if trim:
            #Determine tail cutoff for a 0.95 percentile
            sumDist = sum(zip(*spotAreasHist_eye)[0])#stock distribution
            totalArea = sum(sumDist)
            normDist = [sum(sumDist[:i+1])/float(totalArea) for i, val in enumerate(sumDist)]
            cutoff = min([i for i, val in enumerate(normDist) if val > rank])
            #Trim histogram
            spotAreasHist_eye = [(hist[:cutoff], edges[:cutoff]) for (hist, edges) in spotAreasHist_eye]
            remainder = [sum(hist[cutoff:]) for (hist, edges) in spotAreasHist_eye]
            #Add data beyond cutoff to last bin
            for i, val in enumerate(remainder):
                spotAreasHist_eye[i][0][-1] = spotAreasHist_eye[i][0][-1] + val
    
        #Cluster eyes in batches
        rawdata_cluster, batchlist = self.clusterEyes(rawdata)
        if len(batchlist) > 1:
            idxList, eyeIds_cluster, spotAreas_cluster = rawdata_cluster #unpack data
            spotAreasHist_eye_cluster = [[spotAreasHist_eye[idx] for idx in batch] for batch in idxList]
            #Calculate histograms for batches
            batchHist = [sum(zip(*batch)[0])/float(len(batch)) for batch in spotAreasHist_eye_cluster]
            errBins_batch = [stats.sem(zip(*batch)[0]) for batch in spotAreasHist_eye_cluster]
            binedges_batch = spotAreasHist_eye[0][1]
            spotAreasHist_batch = [batchHist, binedges_batch, errBins_batch]
            #Calculate stock histogram
            stockHist = sum(batchHist)/float(len(batchHist))
            errBins_stock = [np.sqrt(np.sum([np.power(errBins_batch[j][i], 2) for j, batch in enumerate(errBins_batch)])) for i, val in enumerate(errBins_batch[0])]
            binedges_stock = spotAreasHist_eye[0][1]     
        elif len(batchlist) == 1:
            spotAreasHist_batch = None
            #Calculate stock histogram
            stockHist = sum(zip(*spotAreasHist_eye)[0])/float(len(spotAreas))
            errBins_stock = stats.sem(zip(*spotAreasHist_eye)[0])
            binedges_stock = spotAreasHist_eye[0][1]
        spotAreasHist_stock = [stockHist, binedges_stock, errBins_stock]
        histograms = [spotAreasHist_eye, spotAreasHist_batch, spotAreasHist_stock]
        return histograms           
       
    
    def trimHistogram(self, histdata, rank = 0.95):
        #unpack data
        hist, edges, error = histdata
        #Determine tail cutoff for a 0.95 percentile
        totalArea = sum(hist)
        normDist = [sum(hist[:i+1])/float(totalArea) for i, val in enumerate(hist)]
        cutoff = min([i for i, val in enumerate(normDist) if val > rank]) 
        #Trim histogram
        histdata_trim = [hist[:cutoff], edges[:cutoff], error[:cutoff]]
        remainder = sum(hist[cutoff:])
        lastbin_error = np.sqrt(np.sum([np.power(error, 2) for error in error[cutoff:]]))
        #Add data beyond cutoff to last bin
        histdata_trim[0][-1] = histdata_trim[0][-1] + remainder
        histdata_trim[2][-1] = lastbin_error 
        return histdata_trim                                                              
                                                                                                                                
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        
    def stockDataFetcher(self, stockinput):
        from statsFunctions import GeometricMean
        from File_Functions import listPartition
        #from astroML.stats import fit_bivariate_normal
        from scipy import stats
        #Load spotsDict and areasDict
        spotsDict = self.loadSpotsDict()
        areasDict = self.loadAreasDict()
        #Fetch data from dictionary
        if isinstance(stockinput, str):
            stockinput = stockinput.upper()
            try:
                data  = spotsDict[stockinput]    
            except KeyError:
                try:
                    stockinput = self.isControl(stockinput)
                    data = spotsDict[stockinput]
                except KeyError:
                    print('%s is not in the database. \n' %stockinput)
                    sys.exit()
        else:
            print('DatatypeError: datatype of function argument must be str. \n')
            sys.exit()
            
        #Filter out spots smaller < 3 pixels
        eyeIds, spotAreas = zip(*data) #unpack data
        spotAreas = [[val for val in eye if val > 3] for eye in spotAreas]
        rawdata = [eyeIds, spotAreas]
        #Calculate spots' areas histograms: eyes and stock 
        histograms = self.spotAreasHistogram(rawdata, trim = True, rank = 0.95)
        spotAreasHist_eye, spotAreasHist_batch, spotAreasHist_stock = histograms#unpack data
        #Calculate eye measures
        spotCount = np.asarray([len(eye) for eye in spotAreas]) #spot count
        meanA_eye = np.asarray([np.mean(eye) for eye in spotAreas]) #mean spot area per eye
        errA_eye = np.asarray([stats.sem(eye) for eye in spotAreas]) #error
        eyeAreas = np.asarray([areasDict[eyeId] for eyeId in eyeIds], dtype = np.float) #fetch eye areas
        eyeD = eyeAreas/spotCount #eye spot density 
        eyeFA = [sum(eye)/eyeAreas[i]*100 for i, eye in enumerate(spotAreas)] #eye spot fractional area
        spot50 = [listPartition(lambda x: x<=50, eye) for eye in spotAreas]#split spots on size
        spot50 = [[len(sublist) for sublist in eye]for eye in spot50]#count spots on each bin
        spot50 = [tuple(eye) for eye in spot50]
        #Define eyes dictionary
        arrEyes_keys = ['spotCount', 'eyeA', 'eyeD', 'eyeFA', 'errA', 'hist', 'spot50']
        arrEyes = [spotCount, meanA_eye, eyeD, eyeFA, errA_eye, spotAreasHist_eye, spot50]#pack eye data
        
        #Cluster eyes in batches
        rawdata_cluster, batchlist = self.clusterEyes(rawdata)
        if len(batchlist) > 1:
            idxList, eyeIds_cluster, spotAreas_cluster = rawdata_cluster #unpack data
            rawdata = [eyeIds_cluster, spotAreas_cluster]
            arrEyes = [spotCount, meanA_eye, eyeD, eyeFA, errA_eye, spotAreasHist_eye, spot50] = [[[arr[idx] for idx in batch] for batch in idxList] for arr in arrEyes]         
        arrDict_eyes = dict(zip(arrEyes_keys, arrEyes))#assemble dictionary
        if len(batchlist) > 1:
            #Calculate batch measures
            meanCount_batch = [np.mean(batch) for batch in spotCount]
            meanA_batch = [np.mean(batch)for batch in meanA_eye]
            meanD_batch = [np.mean(batch) for batch in eyeD]
            meanFA_batch = [np.mean(batch) for batch in eyeFA]
            geomean50_batch = [GeometricMean().calculateGeoMean(batch) for batch in spot50]
            #calculate errors
            errCount_batch = [stats.sem(batch) for batch in spotCount]
            errA_batch = [np.sqrt(np.sum([np.power(val, 2) for val in batch ])) for batch in errA_eye]
            errD_batch = [stats.sem(batch) for batch in eyeD]
            errFA_batch = [stats.sem(batch) for batch in eyeFA]
            #Define batches dictionary
            arrBatch_keys = ['meanCount', 'meanA', 'meanD', 'meanFA', 'errCount', 'errA', 'errD', 'errFA', 'hist', 'geomean50']
            arrBatch = [meanCount_batch, meanA_batch, meanD_batch, meanFA_batch, errCount_batch, errA_batch, errD_batch, errFA_batch, spotAreasHist_batch, geomean50_batch]#pack batch data
            arrDict_batch = dict(zip(arrBatch_keys, arrBatch))
            #Calculate stock measures
            meanCount_stock = np.mean(meanCount_batch)
            meanA_stock = np.mean(meanA_batch)
            meanD_stock = np.mean(meanD_batch)
            meanFA_stock = np.mean(meanFA_batch)
            geomean50_stock = GeometricMean().calculateGeoMean(geomean50_batch)
            #calculate errors
            errCount_stock = stats.sem(meanCount_batch)
            errA_stock = np.sqrt(np.sum([np.power(val, 2) for val in errA_batch]))
            errD_stock = stats.sem(meanD_batch)
            errFA_stock = stats.sem(meanFA_batch)
        if len(batchlist) == 1:
            arrDict_batch = None
            #Calculate stock spot metrics
            meanCount_stock = np.mean(spotCount)
            meanA_stock = np.mean(meanA_eye)
            meanD_stock = np.mean(eyeD)
            meanFA_stock = np.mean(eyeFA)
            geomean50_stock = GeometricMean().calculateGeoMean(spot50)
            #calculate errors
            errCount_stock = stats.sem(spotCount)
            errA_stock = np.sqrt(np.sum([np.power(val, 2) for val in errA_eye]))
            errD_stock = stats.sem(eyeD)
            errFA_stock = stats.sem(eyeFA)
        
        #Define stocks dictionary    
        arrStocks_keys = ['meanCount', 'meanA', 'meanD', 'meanFA', 'errCount', 'errA', 'errD', 'errFA', 'hist','geomean50']
        arrStocks = [meanCount_stock, meanA_stock, meanD_stock, meanFA_stock, errCount_stock, errA_stock, errD_stock, errFA_stock, spotAreasHist_stock, geomean50_stock]#pack stock data
        arrDict_stocks = dict(zip(arrStocks_keys, arrStocks))
        #Pack stocks data
        arrDict = {'eyes': arrDict_eyes, 'batches': arrDict_batch, 'stocks': arrDict_stocks}
        stockData = [rawdata, arrDict]
        return stockData
        
   

class SpotsDataVis(SpotsMetrics):
    
    def __init__(self):
        SpotsMetrics.__init__(self) 
        return
        
    def getMembers(self):
        import inspect
        methods = inspect.getmembers(self, predicate = inspect.ismethod)
        print(methods)
        return
        
    def unpackDataForStockPlotter(self, stockinput, args):
        from itertools import ifilter
        plotType, control, batchnumber  = args
        #Fetch stocks data
        stocksdataDict = self.loadStocksData()
        #Fetch data from dictionary
        if isinstance(stockinput, str):
            stockinput = stockinput.upper()
            try:
                stockdata  = stocksdataDict[stockinput]    
            except KeyError:
                try:
                    stockinput = self.isControl(stockinput)
                    stockdata = stocksdataDict[stockinput]
                except KeyError:
                    print('%s is not in the database. \n' %stockinput)
                    sys.exit()
        else:
            print('DatatypeError: datatype of function argument must be str. \n')
            sys.exit()
        rawdata, arrDict = stockdata
        eyeIds, spotAreas = rawdata
        if isinstance(eyeIds[0], str):
                numbatches = 1
                eyeIds = [eyeIds]
        else:
            numbatches = len(eyeIds)
        
        if plotType == 'batches': 
            #Fetch aggregates metrics
            metrics_eye = [meanA_eye, eyeD, eyeFA] = arrDict['eyes']['eyeA'], arrDict['eyes']['eyeD'], arrDict['eyes']['eyeFA']
            if numbatches == 1:
                metrics_eye = meanA_eye, eyeD, eyeFA = [meanA_eye], [eyeD], [eyeFA]
        
            try: 
                metrics_batch = [meanA_batch, meanD_batch, meanFA_batch] = arrDict['batches']['meanA'], arrDict['batches']['meanD'], arrDict['batches']['meanFA']
            except TypeError:
                metrics_stock = [meanA_stock, meanD_stock, meanFA_stock] = arrDict['stocks']['meanA'], arrDict['stocks']['meanD'], arrDict['stocks']['meanFA']
            histdata = arrDict['stocks']['hist']
            histdata_trim = self.trimHistogram(histdata)
            hist_trim, edges_trim, error_trim = histdata_trim
            if numbatches == 1:
                stockdata = [numbatches, eyeIds, metrics_eye, metrics_stock, histdata_trim]
            else:
                stockdata = [numbatches, eyeIds, metrics_eye, metrics_batch, histdata_trim]
        elif plotType == 'eyes':
            if not batchnumber:
                batchnumber = raw_input('Please indicate the number of the batch to plot.')
            if numbatches == 1:
                stockdata = [eyeIds[0], arrDict['eyes']['hist']]
            else:
                batchIdx = [idx for (idx, bnumber) in ifilter(lambda x: x[1] == int(batchnumber), [(i,int(batch[0].split('_')[2][1:])) for i, batch in enumerate(eyeIds)])][0]
                stockdata = [eyeIds[batchIdx], arrDict['eyes']['hist'][batchIdx]]    
        return stockdata    
        
        
    def fetchDataForStockPlotter(self, stockinput, args ):    
        #unpack data     
        plotType, control, batchnumber  = args
        stockdata = self.unpackDataForStockPlotter(stockinput, args)   
        if control: 
            controldata = self.unpackDataForStockPlotter('JS125', args)
            data = [stockdata, controldata]     
        else:
            data = stockdata
        return data
        
    def batchLayout(self, stockdata, fig):
        from Plot_Functions import hsvGenerator
        from colorsys import hsv_to_rgb
        from matplotlib import pyplot as plt
        import matplotlib.gridspec as gridspec
        from matplotlib.colors import colorConverter
        #unpack stockdata
        numbatches, eyeIds, metrics_eye, metrics_batch, histdata_trim = stockdata
        meanA_eye, eyeD, eyeFA = metrics_eye
        meanA_batch, meanD_batch, meanFA_batch = metrics_batch
        hist_trim, edges_trim, error_trim = histdata_trim
        #Define subplots on grid
        gs0 = gridspec.GridSpec(1, 2)
        gs00 = gridspec.GridSpecFromSubplotSpec(3, 1, subplot_spec=gs0[0])
        scatterPlots = ax1, ax2, ax3 = [plt.Subplot(fig, gs00[i]) for i in xrange(3)]
        [fig.add_subplot(ax) for ax in scatterPlots]
        gs01 = gridspec.GridSpecFromSubplotSpec(10, 10, subplot_spec=gs0[1]) 
        ax4 = fig.add_subplot(gs01[1:-1, 1:-1])
        axes = [ax1, ax2, ax3, ax4]
        #Generate colorMaps
        cc = lambda arg: colorConverter.to_rgba(arg, alpha=0.6)
        step = 1/float(3)
        hsvColorMap = hsvGenerator(step, 0.8, 0.8)
        rgbaColorMap = [cc(hsv_to_rgb(h,s,v)) for h,s,v in hsvColorMap]
        #Define plots
        xdset = [[i+1]*len(meanA_eye[i]) for i in xrange(numbatches)]
        xdset_mean = [i+1 for i in xrange(numbatches)]
        scatterplots = [[ax.scatter(xdset[j], metrics_eye[i][j], c = rgbaColorMap[i-1], edgecolor = '#CFD0D1') for j in xrange(numbatches)] for i, ax in enumerate(axes[:-1])]
        if numbatches > 1:
            scaterplots_mean = [[ax.scatter(xdset_mean[j], metrics_batch[i][j], marker = '_', c = 'r', s = 50) for j in xrange(numbatches)] for i, ax in enumerate(axes[:-1])]  
        else:
            scaterplots_mean = [ax.scatter(xdset_mean, metrics_batch[i], marker = '_', c = 'r', s = 1000) for i, ax in enumerate(axes[:-1])]   
        ax4.bar(edges_trim, hist_trim, width = 4, color = rgbaColorMap[2], yerr = error_trim, ecolor = '#BEC4C3')
        ax4.set_ylim([0, max(hist_trim)+10])
        #Define tick labels
        [ax.minorticks_on() for ax in axes[:-1]]#switch on minor tick labels
        [ax.set_xticklabels([]) for ax in axes[:-2]]#remove tick labels
        xlabels = [batch[0].split('_')[2] for batch in eyeIds]
        ax3.set_xticks([i+1 for i in xrange(numbatches)])
        ax3.set_xticklabels(xlabels, rotation = 60)
        axis = ['x', 'y']
        [[ax.tick_params(axis = item, labelsize = 9) for item in axis] for ax in axes]
        #Define axis labels and titles
        ax3.set_xlabel('Batchnumber', fontsize = 10)#set xlabel
        ax4.set_xlabel('Area (pixel)', fontsize = 10)
        yaxis_labels = ['Mean area (pixel)', 'Eye area/aggregate count', 'Cum. aggr. area/eye area (%)', 'Aggregate count']
        [ax.set_ylabel(yaxis_labels[i], fontsize = 10) for i, ax in enumerate(axes)]#set ylabels
        #set titles
        titles = ['Size', 'Interspace', 'Fractional area', 'Aggregates size distribution']
        [ax.set_title(titles[i], fontsize = 12) for i, ax in enumerate(axes)]#set subplots titles
        plt.tight_layout()
        plt.show()
        return
                            
    def pairedBatchLayout(self, data, args):
        from Plot_Functions import hsvGenerator
        from colorsys import hsv_to_rgb
        from mpl_toolkits.mplot3d import Axes3D
        import matplotlib as mpl
        from matplotlib import pyplot as plt
        import matplotlib.gridspec as gridspec
        from matplotlib.colors import colorConverter
        fig, stockinput = args#unpack
        #Define subplots on grid
        gs0 = gridspec.GridSpec(1, 2)
        gs00 = gridspec.GridSpecFromSubplotSpec(3, 1, subplot_spec=gs0[0])
        scatterPlots = ax1, ax2, ax3 = [fig.add_subplot(gs00[i]) for i in xrange(3)]
        gs01 = gridspec.GridSpecFromSubplotSpec(10, 10, subplot_spec=gs0[1]) 
        ax4 = fig.add_subplot(gs01[1:-1,:], projection = '3d')
        axes = [ax1, ax2, ax3, ax4]
        #Generate colorMaps
        cc = lambda arg: colorConverter.to_rgba(arg, alpha=0.6)
        step = 1/float(2)
        hsvColorMap = hsvGenerator(step, 0.8, 0.8)
        rgbaColorMap = [cc(hsv_to_rgb(h,s,v)) for h,s,v in hsvColorMap]
        meanColors = ['k', 'r']
        for idx, stockdata in enumerate(data[::-1]):
            #unpack stockdata
            numbatches, eyeIds, metrics_eye, metrics_batch, histdata_trim = stockdata
            meanA_eye, eyeD, eyeFA = metrics_eye
            meanA_batch, meanD_batch, meanFA_batch = metrics_batch
            hist_trim, edges_trim, error_trim = histdata_trim
            #Define scatter plots
            if idx == 0:
                xdset_mean = [i+1 for i in xrange(13)]
                xdset_mean.pop(9)
                xdset = [[val]*len(meanA_eye[i]) for i, val in enumerate(xdset_mean)]
            else:
                xdset_mean = [int(batch[0].split('_')[2][1:])+0.5 for batch in eyeIds]
                xdset_mean.sort()
                xdset = [[val]*len(meanA_eye[i]) for i, val in enumerate(xdset_mean)]
    
            scatterplots = [[ax.scatter(xdset[j], metrics_eye[i][j], c = rgbaColorMap[idx], edgecolor = '#CFD0D1') for j in xrange(numbatches)] for i, ax in enumerate(axes[:-1])]
            if numbatches > 1:
                scaterplots_mean = [[ax.scatter(xdset_mean[j], metrics_batch[i][j], marker = '_', c = meanColors[idx], s = 50) for j in xrange(numbatches)] for i, ax in enumerate(axes[:-1])]
            else:
                scaterplots_mean = [ax.scatter(xdset_mean, metrics_batch[i], marker = '_', c = meanColors[idx], s = 50) for i, ax in enumerate(axes[:-1])]
            #define 3d projection
            z = (idx * 10) + 5
            ax4.bar(edges_trim, hist_trim, zs = z, zdir = 'y', width = 4, color = rgbaColorMap[idx])
            ax4.set_ylim([0, 20])
            #Define tick labels and legend
            if idx == 0:
                [ax.set_xticks([i+1 for i in xrange(13)]) for ax in axes[:-1]]
                [ax.set_xticklabels([]) for ax in axes[:-2]]#remove tick labels
                xlabels = ['b%i' %(val+1) for val in xrange(13)]
                ax3.set_xticklabels(xlabels, rotation = 60)
                axis = ['x', 'y', 'z']
                [[ax.tick_params(axis = item, labelsize = 9) for item in axis] for ax in axes]
                yticklabels = ['control', '%s' %stockinput]
                ax4.set_yticks([5, 15])
                ax4.set_yticklabels(yticklabels, rotation = -20, verticalalignment = 'baseline', horizontalalignment = 'left', fontsize = 10)
        #define axis labels
        ax3.set_xlabel('Batchnumber', fontsize = 10)#set xlabel
        ax4.set_xlabel('Area (pixel)', fontsize = 10)
        yaxis_labels = ['Mean area (pixel)', 'Eye area/aggregate count', 'Cum. aggr. area/eye area (%)']
        [ax.set_ylabel(yaxis_labels[i], fontsize = 10) for i, ax in enumerate(axes[:-1])]#set ylabels
        ax4.set_zlabel('Aggregate count', fontsize = 10)
        #define and set titles
        titles = ['Size', 'Interspace', 'Fractional area', 'Aggregates size distribution']
        [ax.set_title(titles[i], fontsize = 12) for i, ax in enumerate(axes)]#set subplots titles
        #set legend
        l1, l2 = [mpl.lines.Line2D((1,0), (0,1), marker = 'o', linestyle = 'None', color = rgbaColorMap[i], markeredgecolor = '#CFD0D1', ms = 4.0, figure = fig) for i in xrange(2)]
        leg = fig.legend((l1, l2), ('control', '%s' %stockinput), fontsize = 10, bbox_to_anchor=[0.82, 0.15], ncol = 2)
        leg.get_frame().set_linewidth(0.0)
        
        #plt.tight_layout()
        plt.show()
        return
        
                                                          
    def eyesLayout(self, data, args):
        from Plot_Functions import hsvGenerator
        from colorsys import hsv_to_rgb
        from mpl_toolkits.mplot3d import Axes3D
        import matplotlib as mpl
        from matplotlib import pyplot as plt
        from matplotlib.colors import colorConverter
        #unpack
        fig, stockinput = args
        eyeIds, histdata = data
        numbeyes = len(eyeIds)
        #Define subplots on grid
        ax1 = plt.subplot(111, projection = '3d')
        #Generate colorMaps
        cc = lambda arg: colorConverter.to_rgba(arg, alpha=0.6)
        step = 1/float(numbeyes)
        hsvColorMap = hsvGenerator(step, 0.8, 0.8)
        rgbaColorMap = [cc(hsv_to_rgb(h,s,v)) for h,s,v in hsvColorMap]
        #Define 3d projection
        z = [(5 + 10*i) for i in xrange(numbeyes)]
        [ax1.bar(histdata[i][1], histdata[i][0], zs = z[i], zdir = 'y', width = 4, color = rgbaColorMap[i]) for i in xrange(numbeyes)]
        ax1.set_ylim([0, 10*numbeyes])
        #Define tick labels and legend
        yticklabels = [eyeId for eyeId in eyeIds]
        ax1.set_yticks(z)
        ax1.set_yticklabels(yticklabels, rotation = -20, verticalalignment = 'baseline', horizontalalignment = 'left', fontsize = 10)    
        #Define axis labels and titles
        ax1.set_xlabel('Area (pixel)', fontsize = 10)
        ax1.set_zlabel('Aggregate count', fontsize = 10)
        ax1.set_title('%s: aggregates size distribution ' %stockinput, fontsize=12)
        plt.tight_layout()
        plt.show()
        return
        
                                                                                                                                                                                                                                                                                                                                                                                                           
    def stockPlotter(self, stockinput, plotType = 'batches', control = False, batchnumber = False):
        from matplotlib import pyplot as plt
        plt.switch_backend('WXAgg')
        #Fetch data and upack it
        args = [plotType, control, batchnumber]
        data = self.fetchDataForStockPlotter(stockinput, args)
        #unpack data
        if control:
            stockdata , controldata = data
        else:
            stockdata = data
        #Define figure
        stockinput = stockinput.upper()
        stockinput = self.isControl(stockinput)
        fig = plt.figure('%s' %stockinput, figsize = plt.figaspect(0.65))
        #Plot data
        if plotType == 'batches':
            fig.suptitle('%s: Htt.EGFP aggregates metrics ' %stockinput, fontsize = 13, x = 0.6, y = 0.98)
            if control:
                args =[fig, stockinput]
                self.pairedBatchLayout(data, args)
            else:
                self.batchLayout(stockdata, fig)
        elif plotType == 'eyes':
            args = [fig, stockinput]
            self.eyesLayout(stockdata, args)  
        return
    

    def datasetLayout(self, dataset, fitbound):
        import seaborn as sns
        import matplotlib.pyplot as plt
        from matplotlib.patches import Ellipse
        from scipy import stats
        from astroML.stats import fit_bivariate_normal
        import numpy as np
        #fetch data to plot
        x, y, assayset = self.loadDataForDsetPlotter()[dataset]
        #boxcox transformation
        xarr_cox, lambda_x = stats.boxcox(np.asarray(x))
        yarr_cox, lambda_y = stats.boxcox(np.asarray(y))
        x, y = xarr_cox, yarr_cox
        # compute non-robust and robust statistics
        (mu_nr, sigma1_nr,sigma2_nr, alpha_nr) = fit_bivariate_normal(x, y, robust=False)
        (mu_r, sigma1_r,sigma2_r, alpha_r) = fit_bivariate_normal(x, y, robust=True)
        # scatter the points
        ax = plt.subplot(1,1,1)
        ax.scatter(x, y, s=10, lw=0, c='b', alpha=0.3)
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
        #set legend
        ax.legend((E_nr, E_r),('non-robust fit', 'robust fit'), fontsize = 11, loc = 'lower right')
        #set axis limits and labels
        ax.set_xlabel('$X$')
        ax.set_ylabel('$Y$')
        ax.set_xlim([0,22])    
        ax.set_ylim([-1,22])
        data = [ax, x, y, assayset]
        return data
    
    
    def datasetPlotter(self, stockinput = None, dataset = 'filtered', labels = False, fitbound = 3.0):
        from itertools import chain
        import matplotlib.pyplot as plt
        from mpldatacursor import datacursor
        #fetch data for stockinput
        if stockinput is not None:
            #test whether stockinput is a control
            stockinput = stockinput.upper()
            try:
                stockinput = self.controlsDict[stockinput]
                stockinput = [stockinput]
                dataset = 'unfiltered'
            except KeyError:
                #test whether stockinput is a valid database entry
                if stockinput not in self.stockset:
                    print('KeyError: %s is not in the database.' %stockinput)
                    sys.exit()
                valRNAiDict = self.validationRNAis()
                try:
                    valrnai = valRNAiDict[stockinput]
                    if isinstance(valrnai, basestring):
                        stockinput = [stockinput, valrnai]
                    elif isinstance(valrnai, (tuple, list)):
                        valrnai =list(chain(valrnai))
                        stockinput = [stockinput] + valrnai
                except KeyError:
                    stockinput = [stockinput]      
            #load dataset layout
            ax, x, y, assayset = self.datasetLayout(dataset, fitbound)                                     
            #fetch stockdata
            stockTuples = [[(i, label) for i, label in enumerate(assayset) if label.split('_')[0] == stock] for stock in stockinput]
            stockTuples = [tupl for sublist in stockTuples for tupl in sublist]
            if len(stockTuples) > 1:
                idxlist, assayIds = zip(*stockTuples)
            elif len(stockTuples) == 1:
                idxlist, assayIds = stockTuples[0]
                idxlist = [idxlist] 
            x_stock, y_stock = zip(*[(x[idx], y[idx])for idx in idxlist])
            #plot stockdata
            ax.scatter(x_stock, y_stock, s=20, color ='#BD45E6', alpha = 0.6)
            ax.legend(ax.patches + ax.collections, ('non-robust fit', 'robust fit', 'dataset','%s' %stockinput[0]), fontsize = 11, loc = 'lower right')
        elif stockinput is None:
            #load dataset layout
            ax, x, y, assayset = self.datasetLayout(dataset, fitbound)
        #Label axes datapoints interactively
        if labels:
            dsetCollection = ax.collections[0]
            datacursor(dsetCollection, hover=True, point_labels = assayset, fontsize = 10, bbox= None, xytext=(0, 25), formatter=lambda **kwargs: kwargs['point_label'][0])
        #reset axis limits
        if dataset == 'unfiltered':
            ax.set_xlim([0, 20])
            ax.set_ylim([-1, 20])
        plt.show()
        return
    
            
    def eyesImgFetcher(self, stockID, batchnumber):
        import matplotlib.pyplot as plt
        sys.path.append('C:\Python27\Lib\site-packages')
        import cv2
        import random
        #Fetch overlays path
        batchname = 'Batch%i' %batchnumber
        dirname = [dirname for dirname in os.listdir(self.basedir) if dirname.split('_')[0] == batchname][0]
        overlayspath = os.path.join(self.basedir, '%s\Overlays') %dirname
        #Fetch set of images and sort them
        stockID = stockID.upper()
        stockID = self.isControl(stockID)
        imgset = [filename for filename in os.listdir(overlayspath) if filename.split('_')[0] == stockID]
        imgset_sorted = sorted(imgset, key = lambda x:int(x.split('_')[1]))
        #Fetch image paths
        pathset = [os.path.join(overlayspath, fname) for fname in imgset_sorted]
        #Grid: calculate number of rows and columns
        size = len(pathset)
        if size >= 9:
            cols = 3
            rows = 3
            if size > 9:
                imgset_sorted = random.sample(imgset_sorted, 9)
                imgset_sorted = sorted(imgset_sorted, key = lambda x:int(x.split('_')[1]))
                pathset = [os.path.join(overlayspath, fname) for fname in imgset_sorted]    
        elif size <= 6:
            cols = 3
            rows = 2
        #Display images
        for i, path in enumerate(pathset):
            z = i+1
            img = cv2.imread(path, 0)
            plt.subplot(rows, cols, z)
            plt.imshow(img, interpolation = 'bicubic')
            title = '_'.join(imgset_sorted[i].split('_')[:2])
            plt.title(title, fontsize = 10)
            plt.xticks([])
            plt.yticks([])
        
        plt.tight_layout()
        plt.show()
        return
        
        
    def plotSpotsAreaCorr(self, lowerbound = 3, upperbound = 250):        
        from File_Functions import listPartition
        import matplotlib.pyplot as plt
        from scipy import stats          
        spotsDict = self.loadSpotsDict()
        eyes = spotsDict.values()
        eyes = [eye[1] for assay in eyes for eye in assay]
        eyes = [[val for val in eye if val > lowerbound and val <= upperbound] for eye in eyes]#filter out small aggregates
        eyes = [listPartition(lambda x: x <= 50, eye) for eye in eyes]#split aggregates on size
        areaBincounts = [[len(sublist) for sublist in eye]for eye in eyes]# size bin pairs
        areaBincounts = [tuple(sublist) for sublist in areaBincounts]
        xarr, yarr = x, y = zip(*areaBincounts)
        #calculate regression line
        slope, intercept, r_value, p_value, std_err = stats.linregress(xarr,yarr)
        #plot area bin pairs
        ax = plt.subplot(1,1,1)
        ax.scatter(xarr, yarr)
        #plot regression line
        ax.plot((0,200), (intercept, slope*200+intercept), linestyle = '--', color = 'g', linewidth = 2)#regression line
        #set axis limits
        ax.set_xlim([0, 250])
        ax.set_ylim([-5, max(yarr)+10])
        #set axis labels
        ax.set_xlabel('Number of Aggr. per Eye: size <= 50 (pixels)')
        ax.set_ylabel('Number of Aggr. per Eye: size > 50 (pixels)')
        #add text
        ax.text(0.95, 0.03, 'R^2 = %f' %r_value**2, verticalalignment = 'bottom', horizontalalignment = 'right', transform = ax.transAxes, color='#0D0D0D', fontsize = 10)
        plt.show()    
        return



#sm = SpotsMetrics()
#sm.otherControlsDict()
#repeats = sm.fetchRepeats()
#sm.buildStocksDataDict()
#stockdata = sm.stockDataFetcher('js272') 
#rawdata, arrDict = stockdata
#print(arrDict['batches']['mean50R'])      
#stocksdataDict = sm.loadStocksData()
#print(stocksdataDict['JS15'][1]['batches'])
#plt.switch_backend('WXAgg')
#sdv = SpotsDataVis()
#sdv.fetchDataForDsetPlotter()
#stockinput = 'js163'
#sdv.datasetPlotter(stockinput, labels = True, fitbound = 2.5)
#sdv.plotSpotsAreaCorr()
#stockinput = 'js125'
#sdv.stockPlotter(stockinput, plotType = 'eyes', control = True, batchnumber = 7)
#sdv.eyesImgFetcher(stockinput, 7)             