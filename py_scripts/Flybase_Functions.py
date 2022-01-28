import os
import sys


class Flybase():
    
    def __init__(self):
        self.cwd = os.getcwd()
        self.archivedir = '%s\Dropbox\Unknome\Archive\ExternalSources' %self.cwd
        self.fbarchive = '%s\Dropbox\Unknome\Archive\Flybase_PrecomputedFiles' %self.cwd
        self.dbdir = '%s\Dropbox\Unknome\Databases' %self.cwd
        self.dsetpickledir = '%s\Dropbox\Unknome\Archive\Dataset\PickleFiles' %self.cwd
        return
    
    def rebuildDataObjects(self):
        self.buildFlybaseGeneIDsObj()
        self.buildDrosIDObj()
        self.buildFBgnMap()
        return
           
    def buildFlybaseGeneIDsObj(self):
        from itertools import dropwhile
        import cPickle as pickle
        #load flybase precomputed file
        filepath = os.path.join(self.fbarchive, 'fbgn_annotation_ID_fb_2016_01.tsv')
        with open(filepath, 'rU') as f:
            lines = f.readlines()
        #extract headings and data from lines
        lines = list(dropwhile(lambda x: '##gene_symbol' not in x.split('\t'), lines))#filter out metadata
        headings = ((lines[0][:-1].split('##')[1]).split())
        data = [(line.split('\n')[0]).split('\t') for line in lines[1:]]
        #build dictionary
        data = [ zip(headings,entry) for entry in data]
        data = [(entry[1][1], entry)for entry in data]
        fbGeneID_dict = dict(data)
        #serialise dictionary
        picklepath = os.path.join(self.dsetpickledir, 'fbGeneIDs.pickle')
        with open(picklepath, 'wb') as f:
            pickle.dump(fbGeneID_dict, f, protocol = 2)
        return
        
    def loadFlybaseGeneIDs(self):
        import cPickle as pickle
        #load dictionary
        picklepath = os.path.join(self.dsetpickledir, 'fbGeneIDs.pickle')
        with open(picklepath, 'rb') as f:
            fbGeneIDs = pickle.load(f)
        return fbGeneIDs
    
    def buildDrosIDObj(self):
        import cPickle as pickle
        #fetch lines
        filepath = os.path.join(self.fbarchive, 'fbgn_annotation_ID_fb_2016_04.tsv')
        with open(filepath, 'rU') as f:
            lines = f.readlines()
            lines = lines[5:]
        #parse entries    
        lines = [(line.split('\n'))[0].split('\t') for line in lines if '\\' not in line.split('\t')[0]]
        symbgn, fbgn, s_fbgn, cgnumber, s_cgnumber = zip(*lines)
        s_fbgn = [item.split(',') for item in s_fbgn]; s_fbgn = [[] if len(item) == 1 and item[0] == '' else item for item in s_fbgn]
        s_cgnumber = [item.split(',') for item in s_cgnumber]; s_cgnumber = [[] if len(item) == 1 and item[0] == '' else item for item in s_cgnumber]
        #build dictionary object
        heads = ['annotationID', 'sec_annotationID', 'sec_FBgn', 'gene_symbol']
        values = zip(cgnumber, s_cgnumber, s_fbgn, symbgn)
        values = [zip(heads, item) for item in values] 
        DrosIDs = dict(zip(fbgn, values))
        #serialise dictionary
        picklepath = os.path.join(self.dsetpickledir, 'DrosIDs_dict.pickle')
        with open(picklepath, 'wb') as f:
            pickle.dump(DrosIDs, f, protocol = 2)
        return 
    
    def fetchDrosIDs(self):
        import cPickle as pickle
        picklepath = os.path.join(self.dsetpickledir, 'DrosIDs_dict.pickle')
        with open(picklepath, 'rb') as f:
            DrosIDs = pickle.load(f)
        return DrosIDs
    
    def buildFBgnMap(self):
        from itertools import chain
        import cPickle as pickle
        #fetch drosIDs
        drosIDs = self.fetchDrosIDs()
        #fetch secondary fbgn(s)
        cgnumber, s_cgnumber, s_fbgn, symbgn = zip(*drosIDs.values())
        s_fbgn  = [item[1] for item in s_fbgn]
        #build dictionary
        fbgnlist = drosIDs.keys()
        fbgn_tuples = [tupl for tupl in zip(s_fbgn, fbgnlist) if len(tupl[0]) > 0]#filter out genes with no secondary fbgn(s)
        fbgn_tuples = [(a, [b]*len(a)) for (a, b) in fbgn_tuples]#generate sequence of primary fbgn(s)
        fbgnMap = [zip(*tupl)for tupl in fbgn_tuples]
        fbgnMap = dict(list(chain(*fbgnMap)))
        #serialise dictionary
        picklepath = os.path.join(self.dsetpickledir, 'fbgnMap.pickle')
        with open(picklepath, 'wb') as f:
            pickle.dump(fbgnMap, f, protocol = 2)
        return
    
    def loadFBgnMap(self):
        import cPickle as pickle
        picklepath = os.path.join(self.dsetpickledir, 'fbgnMap.pickle')
        with open(picklepath, 'rb') as f:
            fbgnMap = pickle.load(f)
        return fbgnMap



#drosIDs = Flybase().fetchDrosIDs()
