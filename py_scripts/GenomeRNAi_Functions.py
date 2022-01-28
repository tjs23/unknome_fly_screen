import os
import sys
#from tqdm import tqdm


class GenomeRNAi():
    
    def __init__(self):
        from Flybase_Functions import Flybase
        from Unknome_Functions import Unknome
        self.cwd = os.getcwd()
        self.archivedir = '%s\Dropbox\Unknome\Archive\ExternalSources' %self.cwd
        self.fbarchive = '%s\Dropbox\Unknome\Archive\Flybase_PrecomputedFiles' %self.cwd
        self.dbdir = '%s\Dropbox\Unknome\Databases' %self.cwd
        self.dsetpickledir = '%s\Dropbox\Unknome\Archive\Dataset\PickleFiles' %self.cwd
        self.Unknome = Unknome(); self.uIDs = self.Unknome.uIDs
        self.Flybase = Flybase()
        return
    
    def rebuildGenomeRNAiDatabases(self):
        self.buildDrosGenomeRNAiObject()
        self.buildDrosGenomeRNAiDB()
        self.buildHumGenomeRNAiObject()
        self.buildHumGenomeRNAiDB()
        return
    
    def resetDrosDataObjects(self):
        self.unknomeDrosRNAiObj()
        self.buildDrosParticipationDist()
        return
        
    def resetHumDataObjects(self):
        self.buildUnknomeHumIDObj()
        self.unknomeHumanGeneIDs()
        self.unknomeHumScreens()
        self.unkomeHumHits()
        return

    def buildDrosGenomeRNAiObject(self):
        from itertools import chain
        import cPickle as pickle
        #fetch lines from file
        drosGenRNAi_filepath = os.path.join(self.archivedir, 'GenomeRNAi_v15_Drosophila_melanogaster.txt')
        with open(drosGenRNAi_filepath, 'rU') as f:
            lines = f.readlines()    
        #split screen metadata and data from lines    
        lines = (''.join(lines)).split('//')
        lines = [screen.split('\n') for screen in lines]
        lines_split = [[(screen[:i+1], screen[i+2:-1])for i, entry in enumerate(screen) if entry.startswith('#Notes=')] for screen in lines] 
        lines_split = list(chain(*lines_split))
        metadata, screendata = zip(*lines_split)
        #reformat metadata
        metadata = [[entry.split('=') for entry in screen ] for screen in metadata]
        metadata = [screen if len(screen[0])>1 else screen[1:] for screen in metadata]
        #build metadata dict
        metadata_object = [(screen[0][1],[tuple(entry) for entry in screen]) for screen in metadata]
        metadataDict = dict(metadata_object)
        #build screendata dict
        screendata_headings = [(entry.split('#')[1]).split('\t')  for entry in lines[0][1:] if entry.startswith('#Stable ID')][0]
        screendata_object = [[zip(screendata_headings, entry.split('\t')) for entry in screen] for screen in screendata]
        screendataDict = dict([(screen[0][0][1], dict([(entry[2][1], entry) for entry in screen])) for screen in screendata_object if len(screen)>0])
        #serialise dictionaries
        picklepath = os.path.join(self.dsetpickledir, 'drosGenRNAi.pickle')
        with open(picklepath, 'wb') as f:
            drosGenRNAi = [metadataDict, screendataDict]
            pickle.dump(drosGenRNAi, f, protocol = 2)       
        return
        
    def loadDrosGenRNAi(self):
        import cPickle as pickle
        picklepath = os.path.join(self.dsetpickledir, 'drosGenRNAi.pickle')
        with open(picklepath, 'rb') as f:
            drosGenRNAi = pickle.load(f)
        return drosGenRNAi
    
    def buildDrosGenomeRNAiDB(self):
        from itertools import chain
        import sqlite3
        #load drosGenRNAi object
        drosGenRNAi = self.loadDrosGenRNAi()
        metadataDict , screendataDict = drosGenRNAi
        
        #extract rows and columns headings from metadataDict
        metadata_data = metadataDict.values()
        metadata_rows = [zip(*screen)[1] for screen in metadata_data]
        metadata_rows = [[val.decode('utf-8') for val in entry] for entry in metadata_rows]#convert to unicode
        metadata_headings = zip(*metadata_data[0])[0]
        #reformat headings
        metadata_headings = [head.split('#')[1] for head in metadata_headings]
        metadata_headings = [('_').join(head.split()) for head in metadata_headings]

        #extract rows and column headings from screendataDict
        screendata_data = [screen.values() for screen in screendataDict.values()]
        screendata_rows = [[zip(*entry)[1] for entry in screen] for screen in screendata_data]
        screendata_rows = list(chain(*screendata_rows))#unpack
        screendata_rows = [[val.decode('utf-8') for val in entry] for entry in screendata_rows]#convert to unicode
        screendata_headings = zip(*screendata_data[0][0])[0]
        #reformat headings
        screendata_headings = [('_').join(head.split()) for head in screendata_headings]
        
        #connect to database
        dbpath = os.path.join(self.dbdir, 'drosGenomeRNAi.db')
        db = sqlite3.connect(dbpath)
        cursor = db.cursor()
        #fetch existing tablenames
        tablenames = list(cursor.execute(''' SELECT NAME FROM sqlite_master WHERE TYPE = "table"'''))
        tablenames = list(chain(*tablenames))
        for tablename in tablenames:
                cursor.execute('''DROP TABLE IF EXISTS %s''' %tablename)
                db.commit()
        
        #create metadata table 
        headingsText_metadata = ['"%s" TEXT NOT NULL' %head if head == metadata_headings[0] else '%s TEXT' %head for head in metadata_headings]
        headingsText_metadata = ','.join(headingsText_metadata)
        createStatement = '''CREATE TABLE Metadata (%s)''' %headingsText_metadata
        cursor.execute(createStatement)
        #insert data
        valuesText_metadata = ','.join(metadata_headings)
        valuesVarText_metadata = '?,'*len(metadata_headings)
        insertStatement = '''INSERT INTO Metadata (%s) VALUES(%s)''' %(valuesText_metadata, valuesVarText_metadata[:-1])
        cursor.executemany(insertStatement, metadata_rows)
        db.commit()
        
        #create screendata table
        headingsText_screendata = ['"%s" TEXT NOT NULL' %head if head == metadata_headings[0] else '%s TEXT' %head for head in screendata_headings]
        headingsText_screendata = ','.join(headingsText_screendata)
        createStatement = '''CREATE TABLE ScreenData (%s)''' %headingsText_screendata
        cursor.execute(createStatement)
        db.commit()
        #insert data
        valuesText_screendata = ','.join(screendata_headings)
        valuesVarText_screendata = '?,'*len(screendata_headings)
        insertStatement = '''INSERT INTO ScreenData (%s) VALUES(%s)''' %(valuesText_screendata, valuesVarText_screendata[:-1])
        cursor.executemany(insertStatement, screendata_rows)
        db.commit()
        db.close()
        return
                                
    def buildDrosParticipationDist(self):
        from itertools import chain
        from collections import Counter
        import cPickle as pickle
        #load dictionaries
        drosGenRNAi = GenomeRNAi().loadDrosGenRNAi()
        metadataDict, screendataDict = drosGenRNAi
        fbgnList = [[entry[2][1] for entry in screen.values()] for screen in screendataDict.values()]
        fbgnList = list(chain(*fbgnList))
        participationDist = Counter(fbgnList)
        #serialise list
        picklepath = os.path.join(self.dsetpickledir, 'drosgenParticipationList.pickle')
        with open(picklepath, 'w') as f:
            pickle.dump(participationDist, f)
        return
    
    def loadDrosParticipationDist(self):
        import cPickle as pickle
        picklepath = os.path.join(self.dsetpickledir, 'drosgenParticipationList.pickle')
        with open(picklepath, 'r') as f:
            drosParticipationDist = pickle.load(f)
        return drosParticipationDist
        
    def unknomeDrosRNAiObj(self):
        import cPickle as pickle
        #fetch dictionaries and uFBgn
        drosGenRNAi = self.loadDrosGenRNAi()
        metadataDict, screendataDict = drosGenRNAi
        #remap uFBgn
        uFbgn = self.Unknome.remapUnknomeFbgn()
        #cluster GenomeRNAi entries according to uFbgn
        unknomeDrosRNAi = [[] for val in xrange(len(uFbgn))]
        for i, screen in enumerate(screendataDict.values()):
            fbgnlist = screen.keys()
            fbgn_subset = list(set(fbgnlist) & set(uFbgn))
            for fbgn in fbgn_subset:
                j = uFbgn.index(fbgn)
                print(i,j)
                try:
                    entry = screen[fbgn]
                    unknomeDrosRNAi[j].append(entry)    
                except KeyError:
                    continue
        #create dictionary
        unknomeDrosRNAi = dict(zip(uFbgn, unknomeDrosRNAi))
        #serialise dictionary
        picklepath = os.path.join(self.dsetpickledir, 'unknomeDrosRNAi.pickle')
        with open(picklepath, 'wb') as f:
            pickle.dump(unknomeDrosRNAi, f, protocol = 2)
        return
    
    def loadUnknomeDrosRNAi(self):
        import cPickle as pickle
        picklepath = os.path.join(self.dsetpickledir, 'unknomeDrosRNAi.pickle')
        with open(picklepath, 'rb') as f:
            unknomeDrosRNAi = pickle.load(f)
        return unknomeDrosRNAi
    
    def fetchUnknomeDrosRNAiHits(self):
        from itertools import ifilter
        unknomeDrosRNAi = self.loadUnknomeDrosRNAi()
        data = unknomeDrosRNAi.values()
        hits = [list(ifilter(lambda x:x[6][1]!='none', stock)) for stock in data]
        unknomeDrosHits =  dict(zip(unknomeDrosRNAi.keys(), hits))
        return unknomeDrosHits
    
    def fetchUnknomeDrosOutliers(self):
        from itertools import ifilter
        #fetch fly RNAi hits
        uRNAihits_dros = self.fetchUnknomeDrosRNAiHits()
        idxlist = [(i, hit) for i, hit in enumerate(uRNAihits_dros.values()) if len(hit)>0]
        idxlist = [i for (i, hit) in idxlist if len(list(ifilter(lambda x:x[8][1] == 'yes', hit)))> 0]
        outliers_uFbgn = [uRNAihits_dros.keys()[idx] for idx in idxlist]
        return outliers_uFbgn
    
    def fetchUnkParticipationDist(self):
        #load dictionary
        unknomeDrosRNAi = self.loadUnknomeDrosRNAi()
        uFbgn = self.Unknome.remapUnknomeFbgn()
        participationDist = [(uId, len(unknomeDrosRNAi[uId])) for uId in uFbgn]
        return participationDist
    
    def buildHumGenomeRNAiObject(self):
        from itertools import chain
        import cPickle as pickle
        #fetch lines from file
        drosGenRNAi_filepath = os.path.join(self.archivedir, 'GenomeRNAi_v15_Homo_sapiens.txt')
        with open(drosGenRNAi_filepath, 'rU') as f:
            lines = f.readlines()    
        #split screen metadata and data from lines    
        lines = (''.join(lines)).split('//')
        lines = [screen.split('\n') for screen in lines]
        lines_split = [[(screen[:i+1], screen[i+2:-1])for i, entry in enumerate(screen) if entry.startswith('#Notes=')] for screen in lines] 
        lines_split = list(chain(*lines_split))
        metadata, screendata = zip(*lines_split)
        #reformat metadata
        metadata = [[entry.split('=') for entry in screen ] for screen in metadata]
        metadata = [screen if len(screen[0])>1 else screen[1:] for screen in metadata]
        #build metadata dict
        metadata_object = [(screen[0][1],[tuple(entry) for entry in screen]) for screen in metadata]
        metadataDict = dict(metadata_object)
        #build screendata dict
        screendata_headings = [(entry.split('#')[1]).split('\t')  for entry in lines[0][1:] if entry.startswith('#Stable ID')][0]
        screendata_object = [[zip(screendata_headings, entry.split('\t')) for entry in screen] for screen in screendata]
        screendataDict = dict([(screen[0][0][1], dict([(entry[2][1], entry) for entry in screen])) for screen in screendata_object if len(screen)>0])
        #serialise dictionaries
        picklepath = os.path.join(self.dsetpickledir, 'humGenRNAi.pickle')
        with open(picklepath, 'wb') as f:
            humGenRNAi = [metadataDict, screendataDict]
            pickle.dump(humGenRNAi, f, protocol = 2)
        return
    
    def loadHumGenRNAi(self):
        import cPickle as pickle
        picklepath = os.path.join(self.dsetpickledir, 'humGenRNAi.pickle')
        with open(picklepath, 'rb') as f:
            humGenRNAi = pickle.load(f)
        return humGenRNAi
            
    def buildHumGenomeRNAiDB(self):
        from itertools import chain
        import sqlite3
        #load drosGenRNAi object
        humGenRNAi = self.loadHumGenRNAi()
        metadataDict , screendataDict = humGenRNAi
        #extract rows and columns headings from metadataDict
        metadata_data = metadataDict.values()
        metadata_rows = [zip(*screen)[1] for screen in metadata_data]
        metadata_rows = [[val.decode('utf-8') for val in entry] for entry in metadata_rows]#convert to unicode
        metadata_headings = zip(*metadata_data[0])[0]
        #reformat headings
        metadata_headings = [head.split('#')[1] for head in metadata_headings]
        metadata_headings = [('_').join(head.split()) for head in metadata_headings]
        #extract rows and column headings from screendataDict
        screendata_data = [screen.values() for screen in screendataDict.values()]
        screendata_rows = [[zip(*entry)[1] for entry in screen] for screen in screendata_data]
        screendata_rows = list(chain(*screendata_rows))#unpack
        screendata_rows = [[val.decode('utf-8') for val in entry] for entry in screendata_rows]#convert to unicode
        screendata_headings = zip(*screendata_data[0][0])[0]
        #reformat headings
        screendata_headings = [('_').join(head.split()) for head in screendata_headings]
        #connect to database
        dbpath = os.path.join(self.dbdir, 'humGenomeRNAi.db')
        db = sqlite3.connect(dbpath)
        cursor = db.cursor()
        #fetch existing tablenames
        tablenames = list(cursor.execute(''' SELECT NAME FROM sqlite_master WHERE TYPE = "table"'''))
        tablenames = list(chain(*tablenames))
        for tablename in tablenames:
                cursor.execute('''DROP TABLE IF EXISTS %s''' %tablename)
                db.commit()     
        #create metadata table 
        headingsText_metadata = ['"%s" TEXT NOT NULL' %head if head == metadata_headings[0] else '%s TEXT' %head for head in metadata_headings]
        headingsText_metadata = ','.join(headingsText_metadata)
        createStatement = '''CREATE TABLE Metadata (%s)''' %headingsText_metadata
        cursor.execute(createStatement)
        #insert data
        valuesText_metadata = ','.join(metadata_headings)
        valuesVarText_metadata = '?,'*len(metadata_headings)
        insertStatement = '''INSERT INTO Metadata (%s) VALUES(%s)''' %(valuesText_metadata, valuesVarText_metadata[:-1])
        cursor.executemany(insertStatement, metadata_rows)
        db.commit()
        #create screendata table
        headingsText_screendata = ['"%s" TEXT NOT NULL' %head if head == metadata_headings[0] else '%s TEXT' %head for head in screendata_headings]
        headingsText_screendata = ','.join(headingsText_screendata)
        createStatement = '''CREATE TABLE ScreenData (%s)''' %headingsText_screendata
        cursor.execute(createStatement)
        db.commit()
        #insert data
        valuesText_screendata = ','.join(screendata_headings)
        valuesVarText_screendata = '?,'*len(screendata_headings)
        insertStatement = '''INSERT INTO ScreenData (%s) VALUES(%s)''' %(valuesText_screendata, valuesVarText_screendata[:-1])
        cursor.executemany(insertStatement, screendata_rows)
        db.commit()
        db.close()
        return
    
    def buildUnknomeHumIDObj(self):
        from time import sleep
        import cPickle as pickle
        from bioservices.uniprot import UniProt
        #load unknome
        unknome = self.Unknome.loadUnknome()
        uniprot = UniProt()
        #fetch human orthologs IDs
        uIDs = sorted(self.uIDs, key = lambda x:int(x[2:]))
        uHumIDs = [unknome[Id][15][1] for Id in uIDs]
        #fetch entrez IDs   
        droplist = []; keylist = []
        for i, Id in enumerate(uHumIDs):
            print(uIDs[i])
            if Id!=unicode('nan'):
                Idlist = Id.split(',')#split entries with multiple IDs
                multiple_entries = []
                for item in Idlist:
                    sleep(1)
                    entrezID = uniprot.mapping('ID', 'P_ENTREZGENEID', str(item))   
                    if not entrezID:#empty dictionary
                        print(uIDs[i], Id)                    
                        continue
                    elif len(Idlist) == 1:#single entry
                        droplist.append(entrezID.items()[0])
                    elif len(Idlist) > 1:#multiple entries
                        multiple_entries.append(entrezID.items()[0])
                if  len(Idlist)==1 and not entrezID:#single entry returns empty dictionary
                    continue
                elif len(Idlist) > 1:
                    droplist.append(multiple_entries)
                keylist.append(uIDs[i])
            else:#Id == 'nan'
                continue
        #build and serialise dictionary            
        uHumID_dict = dict(zip(keylist, droplist))
        #serialise dictionary
        picklepath = os.path.join(self.dsetpickledir, 'uHumOrthologDict.pickle')
        with open(picklepath, 'wb') as f:
            pickle.dump(uHumID_dict, f, protocol = 2)
        return
    
    def loadUnknomeHumIDs(self):
        import cPickle as pickle
        picklepath = os.path.join(self.dsetpickledir, 'uHumOrthologDict.pickle')
        with open(picklepath, 'rb') as f:
            uHumIDs = pickle.load(f)
        return uHumIDs
    
    def unknomeHumanGeneIDs(self):
        import cPickle as pickle
        from itertools import chain
        uHumIDs = self.loadUnknomeHumIDs()
        geneIDs = []
        for item in uHumIDs.values():
            if isinstance(item, tuple):
                geneIDs.append(item)
            elif isinstance(item, list):
                [geneIDs.append(tupl) for tupl in item]   
        geneIDs = [y for (x,y) in geneIDs]
        geneIDs = list(chain(*geneIDs))
        uhumgeneIDs = list(set(geneIDs))
        #serialise list
        picklepath = os.path.join(self.dsetpickledir, 'unknomeHumGeneIDs.pickle')
        with open(picklepath, 'wb') as f:
            pickle.dump(uhumgeneIDs, f, protocol = 2)
        return

    def loadUnknomeHumGeneIDs(self):
        import cPickle as pickle
        picklepath = os.path.join(self.dsetpickledir, 'unknomeHumGeneIDs.pickle')
        with open(picklepath, 'rb') as f:
            uhumGeneIDs = pickle.load(f)
        return uhumGeneIDs
    
    def unknomeHumScreens(self):
        import cPickle as pickle
        from iterttols import ifilter    
        #load data objects    
        metadataDict, screendataDict = GenomeRNAi().loadHumGenRNAi()
        screenkeys = screendataDict.keys()
        uhumgeneIDs = self.loadUnknomeHumGeneIDs()
        #fetch screens with unknome participants
        uhumScreenList = [(key, list(ifilter(lambda x: unicode(x) in uhumgeneIDs, screendataDict[key].keys()))) for key in screenkeys]
        uhumScreenList = [screen for screen in uhumScreenList if len(screen[1])>0]#filter out negatives
        #serialise list
        picklepath = os.path.join(self.dsetpickledir, 'unknomeHumScreens.pickle')
        with open(picklepath, 'wb') as f:
            pickle.dump(uhumScreenList, f, protocol = 2)
        return
    
    def loadUnknomeHumScreens(self):
        import cPickle as pickle
        picklepath = os.path.join(self.dsetpickledir, 'unknomeHumScreens.pickle')
        with open(picklepath, 'rb') as f:
            uhumScreenList = pickle.load(f)
        return uhumScreenList
    
    def unkomeHumHits(self):
        import cpickle as pickle
        #load data objects
        uhumScreenList = self.loadUnknomeHumScreens()
        metadataDict, screendataDict = GenomeRNAi().loadHumGenRNAi()
        #filter out non-hits
        uhumHits = [[screendataDict[screenkey][Id] for Id in geneIDs if screendataDict[screenkey][Id][6][1]!='none'] for (screenkey, geneIDs) in uhumScreenList]
        #uhumHits = [screen for screen in uhumHits if len(screen)>0]
        #serialise list
        picklepath = os.path.join(self.dsetpickledir, 'unknomeHumHits.pickle')
        with open(picklepath, 'wb') as f:
            pickle.dump(uhumHits, f, protocol = 2)
        return
    
    def loadUnknomeHumHits(self):
        import cpickle as pickle
        picklepath = os.path.join(GenomeRNAi().dsetpickledir, 'unknomeHumHits.pickle')
        with open(picklepath, 'rb') as f:
            uhumHits = pickle.load(f)
        return uhumHits
    
    def unknomeHumOutliers(self):
        #load data objects
        uhumHits = self.loadUnknomeHumHits()
        uhumOutliers = [[entry for entry in screen if entry[8][1]=='yes'] for screen in uhumHits]
        uhumOutliers = [screen for screen in uhumOutliers if len(screen)>0]
        return uhumOutliers


#GenomeRNAi().fetchUnknomeDrosOutliers()
#GenomeRNAi().unknomeDrosRNAiObj()
#GenomeRNAi().buildDrosParticipationDist()
#GenomeRNAi().resetDrosDataObjects()
#GenomeRNAi().buildDrosParticipationDist()
#GenomeRNAi().buildUnknomeHumIDObj()
#print(GenomeRNAi().loadUnknomeHumIDs())
#uHumIDs = GenomeRNAi().loadUnknomeHumIDs()
#print(uHumIDs['JS3'])            
#GenomeRNAi().buildHumGenomeRNAiDB()

