import sys
import os

class Unknome():
    
    def __init__(self):
        from Flybase_Functions import Flybase
        self.cwd = os.getcwd()
        self.dbdir = '%s\Dropbox\Unknome\Databases' %self.cwd
        self.dbpath = os.path.join(self.dbdir, 'Unknome.db')
        self.datasetdir = '%s\Dropbox\Unknome\Archive\Dataset' %self.cwd
        self.kkdir = os.path.join(self.datasetdir, 'KKLibrary')
        self.dsetpickledir = os.path.join(self.datasetdir, 'PickleFiles')
        self.uIDs = self.loadUnknomeIDs()
        self.uCGs = self.loadUnknomeCGs()
        self.uFbgn = self.loadUnknomeFbgn()
        self.Flybase = Flybase()
        return
    
    def getMembers(self):
        import inspect
        methods = inspect.getmembers(self, predicate = inspect.ismethod)
        print(methods)
        return   
     
    def buildUnknomeObj(self):
        import cPickle as pickle
        import sqlite3
        #connect to database
        dbpath = os.path.join(self.dbdir, 'Unknome.db')
        db = sqlite3.connect(dbpath)
        cursor = db.cursor()
        #fetch table data from database
        cursor.execute('''SELECT * FROM Dataset''')
        tabledata = cursor.fetchall()
        db.commit()
        db.close()
        #fetch headings and tabledata
        tabledata = [entry[1:] for entry in tabledata]
        headings = list(map(lambda x: x[0], cursor.description))
        #build unknome object
        unknomeObj = [(entry[0], zip(headings[2:], entry[1:])) for entry in tabledata]
        unknomeDict = dict(unknomeObj)
        #serialise dictionary
        picklepath = os.path.join(self.dsetpickledir, 'Unknome.pickle')
        with open(picklepath, 'wb') as f:
            pickle.dump(unknomeDict, f, protocol = 2)
        return
    
    def loadUnknome(self):
        import cPickle as pickle
        picklepath = os.path.join(self.dsetpickledir, 'Unknome.pickle')
        with open(picklepath, 'rb') as f:
            unknomeDict = pickle.load(f)
        return unknomeDict
    
    def loadUnknomeDrosIDs(self):
        #load dictionary
        unknomeDict = self.loadUnknome()
        uitems = unknomeDict.items()
        #fetch fly IDs
        drosIDs = [(item[0], (item[1][8][1],item[1][9][1])) for item in uitems]
        drosIDs = dict(drosIDs)
        return drosIDs
        
    def loadUnknomeIDs(self):
        unknomeDict = self.loadUnknome()
        uIDs = unknomeDict.keys()
        return uIDs
    
    def loadUnknomeCGs(self):
        drosIDs = self.loadUnknomeDrosIDs()
        uCGs = [entry[1] for entry in drosIDs.values()]
        return uCGs
        
    def loadUnknomeFbgn(self):
        drosIDs = self.loadUnknomeDrosIDs()
        uFbgn = [entry[0] for entry in drosIDs.values()]
        return uFbgn
    
    def remapUnknomeFbgn(self):
        uFbgn = self.loadUnknomeFbgn()
        drosIDs = self.Flybase.fetchDrosIDs()
        fbgnMap = self.Flybase.loadFBgnMap()
        #remap uFBgn
        dros_fbgnlist = drosIDs.keys()
        miss_uFbgn = [Id for Id in uFbgn if Id not in dros_fbgnlist]
        for fbgn in miss_uFbgn:
            try:
               new_fbgn = fbgnMap[fbgn]
               idx = uFbgn.index(fbgn)
               uFbgn[idx] = new_fbgn
            except KeyError:
                print(fbgn)
                continue
        return uFbgn 
                      
    def loadKnownessDict(self):
        import cPickle as pickle
        picklepath = os.path.join(self.dsetpickledir, 'KnownessTime.pickle')
        with open(picklepath, 'r') as f:
            knownessdict = pickle.load(f)    
        return knownessdict
                                         
    def convertIDGenerator(self, identifier, output = 'fbgn'):
        from itertools import chain
        #load dictionaries 
        drosIDs = self.loadUnknomeDrosIDs()
        identifier = identifier.upper()
        #convert identifier
        try:
            idlist = drosIDs[identifier]#identifier == uID
            convertID = [Id for Id in idlist if Id.startswith(output[:2].upper())]
            yield convertID[0]  
        except KeyError:
            if identifier.startswith('FB'):
                identifier = 'FBgn'+ identifier[4:]#identifier == uFBgn
            idlist = [(i, Id) for i,Id in enumerate(drosIDs.values()) if identifier in Id]
            #Assertion error
            if len(idlist) == 0:
                yield identifier
            #fetch uFBgn or uCG numbers
            else:
                idxlist, idlist = zip(*idlist)    
                convertID = [Id for Id in chain(*idlist) if Id.startswith(output[:2].upper())]
                if len(convertID)==0:#output=js
                    convertID = [drosIDs.keys()[idx] for idx in idxlist]#fetch uIDs
                yield convertID[0]
            
    
    def convertID(self, identifier, outID = 'fbgn'):
        from File_Functions import listPartition
        if isinstance(identifier, str):
            identifier =[identifier]
        convertIDlist = [list(self.convertIDGenerator(ID, output = outID))[0] for ID in identifier]
        idlist = [Id.upper() for Id in identifier]
        mismatches, convertIDlist = listPartition(lambda x:x in idlist, convertIDlist)
        if len(mismatches)>0:
            print('%s are not part of the Unknome dataset.' % ','.join(mismatches))
        return convertIDlist
                
    def fetchViables(self, viability = 'Viable'):
        import sqlite3
        #Connect to database
        db = sqlite3.connect(self.dbpath)
        cursor = db.cursor()
        cursor.execute('''SELECT Stock_Id FROM Dataset WHERE Viability = ?''', (viability,))
        fetchedList = cursor.fetchall()
        viables = [tupl[0] for tupl in fetchedList]#unpack
        db.close()
        return viables
    
    def fetchLethals(self):
        kwList = ['Lethal', 'Semi']
        lethals = [self.fetchViables(viability = kw) for kw in kwList]
        lethals = lethals[0] + lethals[1]#concatenate lists
        lethals = sorted(lethals, key = lambda x:int(x[2:]))
        return lethals
        
    def unknomeFetcher(self, stockID, output = 'screen'):
        from File_Functions import listPartition
        #load dictionary
        unknomeDict = self.loadUnknome()
        #reformat input
        if isinstance(stockID, str):
            stockID =[stockID]
        stockIDlist = [name.upper() for name in stockID]
        #filter out mismatches and split ID types
        stockIDlist, mismatches = listPartition(lambda x:x.startswith('JS') or x.startswith('CG'), stockIDlist)
        CGlist, uIDlist= listPartition(lambda x:x.startswith('CG'), stockIDlist)
        fbgnlist, uIDlist =  listPartition(lambda x:x.startswith('FB'), stockIDlist)
        #convert uCGIDs to uIDs
        if len(CGlist)>0:
            uIDlist2 = self.convertID(CGlist, outID = 'js')
            uIDlist = uIDlist + uIDlist2
        #convert fbgnIDs to uIDs
        elif len(fbgnlist)>0:
            uIDlist3 = self.convertID(fbgnlist, outID = 'js')
            uIDlist = uIDlist + uIDlist3
        #fetch records
        records = [unknomeDict[uID] for uID in uIDlist]
        if len(mismatches)>0:
            print('%s is/are not part of the Unknome dataset.' %','.join(mismatches[:-1]))
        #choose output        
        if output == 'screen':
            for i, stock in enumerate(uIDlist):
                if len(uIDlist) > 1:
                    print('%s:\n%s\n' %(stock, records[i]))     
                elif len(uIDlist)==1:
                    print('%s:\n%s\n' %(stock, records))            
        elif output == 'html':
            args = records, uIDlist 
            self.unknomeHTMLtable(args)
        return
            

               
    def unknomeHTMLtable(self, args):
        from numpy import cumsum
        import webbrowser
        '''It reformats and displays the output of unknomeFetcher in a html table format .'''
        records, stocklist = args

        #if len(stocklist) == 1:
            #records = [records]
        
        #Sort stocklist
        stocklist_sorted = sorted(stocklist, key = lambda x:int(x[2:]))
        #Define headings and subheadings
        headers = ['Gene', 'RNAi', 'Orthologues', 'Protein', 'Fly stocks', 'Unknome']
        subheadings = ['unknome_id', 'CG_number', 'fbgn_id', 'gene_id', 'OrthoMCL_id', 'transf_id', 'insertion', 'status', 's19', 'CAN repeats', 'off-target', 'yeast_id(s)', 'worm_id(s)', 'zebrafish_id(s)', 'mouse_id(s)', 'human_id(s)', 'DMPL (83)', 'DPiM_PPI ', 'lethality']
        #Set headings spans
        headspan = [5, 6, 5, 1, 1, 1]
        
        #Set headings and subheadings colors
        headcolors = ['#D7E9FC', '#FCEAD7']
        subheadcolors = ['#F2F7FA', '#FAF5F2']
        #Generate headings row
        table_html = ['<TR><TABLE BORDER=1 CELLPADDING=5 CELLSPACING=10 RULES=ROWS FRAME=BOX>\n']
        for i, head in enumerate(headers):
            if i == 0 or i%2 == 0:
                row = '<TH COLSPAN=%i BGCOLOR=%s>%s</TH>' %(headspan[i], headcolors[0], head)
            else:
                row = '<TH COLSPAN=%i BGCOLOR=%s>%s</TH>' %(headspan[i], headcolors[1], head)
            table_html.append('%s\n' %row)
        table_html.append('</TR><TR>')
        
        #Generate subheadings row
        head_idx = cumsum(headspan)
        color = subheadcolors[0]
        for i, subhead in enumerate(subheadings):
            row = '<TH ALIGN=left BGCOLOR=%s><FONT SIZE=2>%s</FONT></TH>' %(color,subhead)
            table_html.append('%s\n' %row)
            #Set subheading background colors according to headings colors
            try:
                test = max([j for j, val in enumerate(head_idx) if i+1>= val])+1
            except ValueError:
                test = 0
            if test%2 == 0:
                color = subheadcolors[0]
            else:
                color = subheadcolors[1]
        table_html.append('</TR><TR>')
        
        #Generate stocks rows: fill cells with data
        color = subheadcolors[0]
        for i, stock in enumerate(stocklist_sorted):
            for j, key in enumerate(subheadings):
                try:
                    data = records[i][key]
                    row = '<TD BGCOLOR=%s><FONT SIZE=2>%s</FONT></TD>' %(color, data)
                    table_html.append('%s\n' %row)  
                except KeyError:
                    if j==0:
                        data = stocklist_sorted[i] 
                    elif j==1:
                        data = records[i]['cg_number']
                    elif j ==4:
                        data = records[i]['OrthoMCL id']
                    elif j==6:
                        data = records[i]['Insertion']
                    elif j==18:
                        data = records[i]['Lethality (Da-GAL4)']
                        
                    row = '<TD BGCOLOR=%s><FONT SIZE=2>%s</FONT></TD>' %(color, data)
                    table_html.append('%s\n' %row)    
                #Set cell background colors according to suheadings colors
                try:
                    test = max([z for z, val in enumerate(head_idx) if j+1>= val])+1
                except ValueError:
                    test = 0
                if test%2 == 0:
                    color = subheadcolors[0]
                else:
                    color = subheadcolors[1]
            table_html.append('</TR><TR>')      
        table_html.append('</TR></TABLE>')
        
        #Display html file
        table_html = ''.join(table_html)
        '''cwd = os.getcwd()
        path = '%s\Desktop\unknomeQuery.html' %cwd
        with open(path, 'w') as f:
            f.writelines(table_html)''' 
        #Display html file
        webbrowser.open_new_tab(table_html)
        return
    
    
    def plotUnknomeClustersMock(self):
        from mpl_toolkits.mplot3d import Axes3D
        import matplotlib as mpl
        from matplotlib import pyplot as plt
        from Plot_Functions import hsvGenerator
        from colorsys import hsv_to_rgb
        from matplotlib.colors import colorConverter
        import numpy as np
        import random
        
        #define sets
        xset = [i for i in xrange(10)]
        yset = [xset]*5
        sizes = [12, 30, 20, 25, 18, 30, 25, 18, 12, 60]
        sizes = [val*10 for val in sizes]
        
        #3d axes instance
        ax = plt.subplot(111, projection = '3d')
        
        #Generate colorMaps
        cc = lambda arg: colorConverter.to_rgba(arg, alpha=0.6)
        step = 1/float(5)
        hsvColorMap = hsvGenerator(step, 0.8, 0.8)
        rgbaColorMap = [cc(hsv_to_rgb(h,s,v)) for h,s,v in hsvColorMap]
        
        #plot: shuffle size and zset lists
        for i in xrange(5):
            zset = np.random.uniform(2.5, 4, 10)
            random.shuffle(sizes)
            if i == 4:
                idx = [1,3,6,7,8]
                for val in idx:
                    sizes[val]=0 
                    
            ax.scatter([xset[i]]*10, yset[i], zs = zset, zdir = 'z', s= sizes, c = rgbaColorMap[i], alpha = 0.6)
            
        #set ticks and labels 
        ax.set_xticks([0, 1, 2, 3, 4])
        xlabels = ['Gene%s' %str(i+1) for i in xrange(5)]
        ax.set_xticklabels(xlabels, rotation = 60)
        ax.set_yticks([])
        ax.set_zticks([])
        ax.set_ylabel('Species', fontsize = 12)
        ax.set_zlabel('Knowness', fontsize = 12)
        axis = ['x', 'y', 'z']
        [ax.tick_params(axis = item, labelsize = 10) for item in axis]
        
        plt.tight_layout()
        plt.show()
        
        return
    
    
    def plotUnknomeMock(self):
        from mpl_toolkits.mplot3d import Axes3D
        import matplotlib as mpl
        from matplotlib import pyplot as plt
        from Plot_Functions import hsvGenerator
        from colorsys import hsv_to_rgb
        from matplotlib.colors import colorConverter
        import numpy as np
        import random
        
        #define sets
        xset = [i for i in xrange(1000)]
        yset = np.random.uniform(0, 200, 1000)
        sizes = np.random.uniform(0,1000, 1000)
        
        #axes instance
        ax = plt.subplot(111)
        
        #Generate colorMaps
        cc = lambda arg: colorConverter.to_rgba(arg, alpha=0.6)
        step = 1/float(5)
        hsvColorMap = hsvGenerator(step, 0.8, 0.8)
        rgbaColorMap = [cc(hsv_to_rgb(h,s,v)) for h,s,v in hsvColorMap]
        
        #plot: random size and color samples        
        ax.scatter(xset, yset, s= sizes, c = '#DDDCE0', alpha = 0.6)
        ax.scatter(random.sample(xset, 5), random.sample(yset, 5), s = random.sample(sizes, 5), c = rgbaColorMap, alpha = 0.6)
        ax.set_xlim([-50, max(xset)+ 50])
        ax.set_ylim([-10, max(yset) + 10])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
            
        #set ticks and labels 
        ax.set_xticks([])
        ax.set_xlabel('Gene clusters', fontsize = 14)
        ax.set_yticks([])
        ax.set_ylabel('Knowness', fontsize = 14)
        
        plt.tight_layout()
        plt.show()
        
        return
    
    
    def plotUnknomeKnowness(self, years, outliers = False, threshold = 'max'):
        import numpy as np
        from matplotlib import pyplot as plt
        from Plot_Functions import gridSize
        
        #load knowness dict
        knownessdict = self.loadKnownessDict()
        
        #test argument datatype
        if years == 'all':
            keys = knownessdict.keys().sort(reverse = True)
        elif isinstance(years, int):
            keys = [str(years)]
        elif isinstance(years, (list, tuple)):
            if isinstance(years[0], int):
                years.sort(reverse = True)
                keys = [str(year) for year in years]
            else:
                raise Exception('Argument datatype error: not int type. ')
        
        #fetch knowness data 
        data = [knownessdict[key] for key in keys]
        data = [[val if val !=0 else 0.2 for val in year] for year in data] #edit knowness == 0 values  
        xset = np.arange(1, len(data[0])+1)#define x coordinates
        
        #calculate fraction of outliers above threshold
        if outliers:
            if threshold == 'max':
                try:
                    threshold = max(data[1])
                except IndexError:
                    threshold = np.mean(data[0])
            outliers = len([val for val in data[0] if val > threshold])/float(len(data[0]))
            print('Fraction of gene clusters above the knowness threshold: %.3f' %outliers)
        
        #define canvas gridsize and range of data to plot
        if len(data) > 1:
            rows, cols = gridSize(len(data)-1)
            datarange = data[1:]
        else:
            rows, cols = gridSize(len(data))
            datarange = [data]
            
        #sort knowness and fetch indices
        idxtuples = [(i, val) for i, val in enumerate(data[0])]
        tuples_sort = sorted(idxtuples, key = lambda x:x[1], reverse = True)
        sortkey, nowdata = zip(*tuples_sort)
            
        #define axes on grid
        for i, year in enumerate(datarange):
            colidx = list(np.arange(cols))*rows
            ax = plt.subplot2grid((rows, cols), (i/cols, colidx[i]), colspan = 1)
            
            presentyear = ax.bar(xset, nowdata, width = 0.8, color = '#B5B4B8', linewidth = 0, alpha = 0.8)
            if len(data) > 1:    
                otherdata = []  
                [otherdata.append(year[j]) for j in sortkey]
                otheryear = ax.bar(xset, otherdata, width = 0.8, color = 'b', linewidth = 0, alpha = 0.5)
            #define axis limits and labels        
            ax.set_xlim([-10, 375])
            ax.set_ylim([-2, 60])
            ax.set_xlabel('Unknome Gene Clusters', fontsize = 14)
            ax.set_ylabel('Knowness', fontsize = 14)
            
            #define legend
            if len(data) > 1:
                ax.legend((presentyear, otheryear), (keys[0], keys[i+1]), fontsize = 12)
            else:
                ax.legend([keys[0]], fontsize = 12)
    
        plt.show()
        
        return
        

class UnknomeExpression(Unknome):
    
    def __init__(self):
        Unknome.__init__(self)
        self.expressiondir = os.path.join(self.datasetdir, 'Expression')
        self.expressionDict = self.loadExpressionDict()
        
    def getMembers(self):
        import inspect
        methods = inspect.getmembers(self, predicate = inspect.ismethod)
        print(methods)
        return
           
    def buildExpressionDict(self):
        import cPickle as pickle
        from File_Functions import dictFromFile
        rawdatapath = os.path.join(self.expressiondir, 'Unknome_expression_rawdata.txt')
        
        usecols_l = [i for i in xrange(18, 29)]
        usecols_ad = [i for i in xrange(18)]
        expressionDict_l = dictFromFile(rawdatapath, keycols = 29, usecols= usecols_l, colasarr = True)
        expressionDict_ad = dictFromFile(rawdatapath, keycols = 29, usecols= [usecols_ad, 27, 28], colasarr = True)
        
        expressionDict = {'larvae': expressionDict_l, 'adult': expressionDict_ad}
        dsetpicklepath = os.path.join(self.dsetpickledir, 'ExpressionDict.pickle')
        with open(dsetpicklepath, 'w') as f:
            pickle.dump(expressionDict, f)
    
        return        
          
    def loadExpressionDict(self):
        import cPickle as pickle
        picklepath = os.path.join(self.dsetpickledir, 'ExpressionDict.pickle')
        with open(picklepath, 'r') as f:
            expressionDict = pickle.load(f)
        return expressionDict
        
    
    def loadLarvalExpDict(self):
        expressionDict_l = self.expressionDict['larvae']
        return expressionDict_l
        
    
    def loadAdultExpDict(self):
        expressionDict_ad = self.expressionDict['adult']
        return expressionDict_ad
        
    
    def stocksetPlotter(self, stockset, inputDict):
        from matplotlib import pyplot as plt
        from pylab import setp
        import numpy as np
        from itertools import chain 
        
    
        if inputDict.lower() == 'a':
            expressionDict_ad = self.loadAdultExpDict()
            tags_ad = ['flyMean', 'oligo', 'CG number']
            zipdata = [zip(*expressionDict_ad[stock].items()) for stock in stockset]
            labels = [key for i, key in enumerate(zipdata[0][0]) if key not in tags_ad]
            idxMean = [i for i, key in enumerate(zipdata[0][0]) if key == 'flyMean']
            idxTags = [i for i, key in enumerate(zipdata[0][0]) if key in tags_ad]
        
        elif inputDict.lower() == 'l':
            expressionDict_l = self.loadLarvalExpDict()
            tags_l = ['flyMean', 'CG number', 'lS2Mean']
            zipdata = [zip(*expressionDict_l[stock].items()) for stock in stockset]
            labels = [key for i, key in enumerate(zipdata[0][0]) if key not in tags_l]
            idxMean = [i for i, key in enumerate(zipdata[0][0]) if key == 'lS2Mean']
            idxTags = [i for i, key in enumerate(zipdata[0][0]) if key in tags_l]
        
        
        flatData = [tupl for sublst in zipdata for tupl in sublst]
        valtuples = flatData[1::2]
        values_trim = [[val for i, val in enumerate(tupl) if i not in idxTags] for tupl in valtuples ]
        
        normVal = [np.asarray(values)/valtuples[i][idxMean[0]]*100 for i, values in enumerate(values_trim)]
        
        #Plotting
        #Define plotting grid
        size = len(stockset)
        rows = int(round(np.sqrt(size)))
        cols = (size/rows) + (size%rows>0)
        figure, axs = plt.subplots(rows, cols, sharex = 'col')
        
        #Unpack axes
        unpkAxs = []
        axs = [axs]
        for ax in axs:
            try:
                sublist = chain(ax)
                for item in sublist:
                    try:
                        [unpkAxs.append(subitem) for subitem in chain(item)]
                    except TypeError:
                        unpkAxs.append(item)
                        
            except TypeError:
                unpkAxs.append(ax)
    
        
        #Define bar plots axes
        xset = np.arange(len(labels))
        width = 0.9
        [unpkAxs[i].bar(xset, normVal[i], width=width, color = 'b', align = 'center') for i in xrange(len(normVal))]
        
        #Set axes margins
        [ax.margins(0.01) for ax in unpkAxs]
        
        #Define legend labels:CG numbers
        if inputDict.lower() == 'a':
            leglabels = [expressionDict_ad[stockset[i]]['CG number'] for i in xrange(len(normVal))]
        elif inputDict.lower() == 'l':
            leglabels = [expressionDict_l[stockset[i]]['CG number'] for i in xrange(len(normVal))]
            
        #Set ticks, ticklabels, xy labels and legends
        delta = len(unpkAxs)-len(normVal)
        if delta ==0:
            delta = -len(unpkAxs)
        
        for i, ax in enumerate(unpkAxs[:-delta]):
            ax.set_xticks(xset)
            ax.tick_params(axis='x', direction='out')
            ax.xaxis.set_tick_params(labeltop='on', labelbottom='off')
            ax.set_xticklabels(labels, rotation = 60, fontsize = 10)
            if i >= cols:
                setp(ax.get_xticklabels(), visible=False)
            ax.yaxis.set_tick_params(labelsize=10)
            ax.set_ylabel('Enrichment (%)', fontsize = 12)
            ax.legend([leglabels[i]], fontsize = 9, loc = 'best')
            
        #Set window title    
        figure.canvas.set_window_title('Tissue expression pattern')  
        
        
        return figure


    def expressionPlotter(self):
        from matplotlib import pyplot as plt
        
        #Define input datatype and extract stock IDs accordingly
        while True:
            inputDict = raw_input('Plot gene expression on larval (l) or fly adult (a) tissues? ')
            inputStock = raw_input('Please, enter stocks (e.g. JS125, JS10, JS67) or path to file containing stocks. ')
            try:
                with open(inputStock, 'rU') as f:
                    data = f.readlines()
                    stocks = [line.strip('\t\n') for line in data]
                    stocks = [stock.upper() for stock in stocks]
                    break
            except IOError:
                if ',' in inputStock:
                    stocks = inputStock.split(',')
                    stocks = [stock.upper() for stock in stocks]
                    stocks = [stock.strip() for stock in stocks]
                    test = [stock for stock in stocks if 'JS' not in stock]
                    if len(test)>0:
                        stocknames = ', '.join(test)
                        print('Unrecognised stock names: %s . ' %stocknames)
                    else:
                        break                        
                elif len(inputStock)<6:
                    inputStock = inputStock.upper()
                    inputStock = inputStock.strip()
                    print(inputStock)
                    if 'JS' in inputStock:
                        stocks = [inputStock]
                        break              
                else:
                    print('Unrecognised datatype: %s' %inputStock)
                    sys.exit()                           
        #Calculate number of figures and number of plots per figure
        remainder = len(stocks)%25       
        numberFig = len(stocks)/25 + (remainder>0)
        if numberFig > 1:
            axNumber = len(stocks)/numberFig
        elif numberFig ==1:
            axNumber = len(stocks)  
        #Define stocks in stockSets; one stockSet per figure
        stockRange = [i for i in xrange(0, len(stocks), axNumber)]
        stockRange.append(len(stocks))
        stockSets = [item for item in stocks[i:stockRange[i+1]] for i in stockRange[:-1]]
        plt.close('all')
        #Plot stocksets
        if isinstance(stockSets[0], (list, tuple)):
            for stockset in stockSets:
                figure = self.stocksetPlotter(stockset, inputDict)
                plt.show(figure)        
        elif isinstance(stockSets[0], str):
            figure = self.stocksetPlotter(stockSets, inputDict)
            plt.show()
        return


class KKLibScreen(Unknome):
    
    def __init__(self):
        Unknome.__init__(self)
        self.kkdir = os.path.join(self.datasetdir, 'KKLibrary')
    
    def getMembers(self):
        import inspect
        methods = inspect.getmembers(self, predicate = inspect.ismethod)
        print(methods)
        return
        
    def updateKKScreenDict(self):
        import cPickle as pickle
        from File_Functions import dictFromFile
        #Build dictionary from file
        filepath = os.path.join(self.kkdir, 'KKLibscreen.txt')
        kkDict = dictFromFile(filepath, keycols = 0, colasarr = True)
        picklefile = os.path.join(self.pickledir, 'KKscreen.pickle') 
        with open(picklefile, 'w') as f:
            pickle.dump(kkDict, f)
        return
        
    def loadKKScreenDict(self):
        import cPickle as pickle
        picklefile = os.path.join(self.dsetpickledir, 'KKscreen.pickle')
        with open(picklefile, 'r') as f:
            kkDict = pickle.load(f)   
        return kkDict
        
        
    def kkGroupMetrics(self):
        #load data objects
        kkDict = self.loadKKScreenDict()
        pkc26Locus = list(kkDict['pKC26'])
        keyset = kkDict.keys()
        stocks = [key for key in keyset if key.startswith('JS')]
        #fetch to be done list of stocks
        total = len([val for val in pkc26Locus if val!='nw' and val!='nd'])
        tbdList = [key for key in stocks if kkDict[key]['pKC26'] == 'nw']
        tbdList.sort()
        #Calculate insertion frequencies at each locus: canonical site
        pkc26Count = pkc26Locus.count('450')
        pkc26Idx = [i for i, val in enumerate(kkDict['Lethality']) if (val == 'Lethal' or val == 'Semi') and kkDict['pKC26'][i]=='450']
        pkc26Lethal_val = len([i for i in pkc26Idx if (kkDict['Validation'][i]=='Lethal' or kkDict['Validation'][i]== 'Semi')])
        pkc26Lethal_nval = len([i for i in pkc26Idx if kkDict['Validation'][i]=='Viable'])
        pkc26Lethal = len(pkc26Idx)
        pkc26Viable = len([i for i, val in enumerate(kkDict['Lethality']) if val == 'Viable' and kkDict['pKC26'][i]=='450'])
        #non-canonical site
        pkc43Count = pkc26Locus.count('1050')
        pkc43Idx = [i for i, val in enumerate(kkDict['Lethality']) if (val == 'Lethal' or val == 'Semi') and kkDict['pKC26'][i]=='1050']
        pkc43Lethal_val = len([i for i in pkc43Idx if (kkDict['Validation'][i]=='Lethal' or kkDict['Validation'][i]== 'Semi')])
        pkc43Lethal_nval = len([i for i in pkc43Idx if kkDict['Validation'][i]=='Viable'])
        pkc43Lethal = len(pkc43Idx)
        pkc43Viable = len([i for i, val in enumerate(kkDict['Lethality']) if val == 'Viable' and kkDict['pKC26'][i]=='1050'])
        #frequencies
        freq_pkc26 = float(pkc26Count)/float(total) *100
        freq_pkc43 = float(pkc43Count)/float(total) *100
        total_val = pkc26Lethal_val + pkc26Lethal_nval + pkc43Lethal_val + pkc43Lethal_nval
        #build groupmetrics dictionary
        kkgroupMetrics = {'can': [pkc26Count, pkc26Viable, pkc26Lethal, pkc26Lethal_val, pkc26Lethal_nval], 
                        'ncan': [pkc43Count, pkc43Viable, pkc43Lethal, pkc43Lethal_val, pkc43Lethal_nval], 'dset': [total, freq_pkc26, freq_pkc43, total_val]}
        return kkgroupMetrics, tbdList
        
        
    def kkPlotter(self):
        from matplotlib import pyplot as plt
        import numpy as np
    
        #fetch data and unpack
        kkgroupMetrics, tbdList = self.kkGroupMetrics()
        [pkc26Count, pkc26Viable, pkc26Lethal, pkc26Lethal_val, pkc26Lethal_nval] = kkgroupMetrics['can']
        [pkc43Count, pkc43Viable, pkc43Lethal, pkc43Lethal_val, pkc43Lethal_nval] = kkgroupMetrics['ncan']
        [total, freq_pkc26, freq_pkc43, total_val] = kkgroupMetrics['dset']
        
        #define axes on grid
        figure, (ax1, ax2, ax3) = plt.subplots(1, 3, sharex = 'none', sharey = 'none')
        
        xset = np.arange(2)
        width1 = 0.5
        width2 = 0.3
        barSet_count = [pkc26Count, pkc43Count]
        barSet_lethal = [pkc26Lethal, pkc43Lethal]
        barSet_viable = [pkc26Viable, pkc43Viable]
        barSet_valid = [pkc26Lethal_val, pkc43Lethal_val]
        barSet_nvalid = [pkc26Lethal_nval, pkc43Lethal_nval]
        
        ax1.bar(xset, barSet_count, width = width1, color = 'b', align = 'center')
        viable = ax2.bar(xset - width2/2, barSet_viable, width=width2, color = 'b', align = 'center')
        lethal = ax2.bar(xset + width2/2, barSet_lethal, width=width2, color = '#D0D0D6', align = 'center')
        lethal_val = ax3.bar(xset - width2/2, barSet_valid, width=width2, color = '#D0D0D6', align = 'center')
        lethal_nval = ax3.bar(xset + width2/2, barSet_nvalid, width=width2, color = 'b', align = 'center')
        
        axlabels = ['Can', 'nCan']
        ax1.set_xticks(xset)
        ax1.set_xticklabels(axlabels, fontsize = 12)
        ax1.set_ylabel('Count', fontsize = 14)
        ax1.set_title(('n = %s' %total), fontsize = 12)
        
        ax2.set_xticks(xset)
        ax2.set_xticklabels(axlabels)
        ax2.set_ylabel('Count', fontsize = 14)
        ax2.set_title(('n = %s' %total), fontsize = 12)
        legLabels = ['Viable', 'Semi/lethal']
        ax2.legend(legLabels, fontsize = 10, loc = 'best')
        
        ax3.set_xticks(xset)
        ax3.set_xticklabels(axlabels)
        ax3.set_ylabel('Count', fontsize = 14)
        ax3.set_title(('Validation: n = %s' %total_val), fontsize = 12)
        legLabels = ['Semi/lethal', 'Viable']
        ax3.legend(legLabels, fontsize = 10, loc = 'best')
        
        plt.tight_layout()
        plt.show()
        
        return
        
    def kkTobeDoneList(self, output = 'screen'):
        #fetch data
        kkgroupMetrics, tbdList = self.kkGroupMetrics()
        
        if output == 'screen':
            print(tbdList)
        
        elif output == 'file':
            #write to file
            heading = ['tobeDone']
            tbdpath = os.path.join(self.kkdir, 'tobeDoneList.txt')
            with open(tbdpath, 'w') as f:
                f.writeline('%s\n' %heading[0])
                lines = '\n'.join(tbdList)
                f.writelines(lines)
        
        return


class FlybaseRef():
    
    def __init__(self):
        cwd = os.getcwd()
        self.cwd = cwd
        self.archivedir = '%s\Dropbox\Unknome\Archive' %self.cwd
        self.datasetdir = os.path.join(self.archivedir, 'Dataset')
        self.pickledir = os.path.join(self.datasetdir, 'PickleFiles')
        self.flybaseDatadir = os.path.join(self.archivedir, 'Flybase_PrecomputedFiles')
    
    def createDrosRefDict(self, year = 2015):
        import cPickle as pickle
        #fetch rawdata from pre-computed flybase file
        filepath = os.path.join(self.flybaseDatadir, 'FlyBase_Fields_%s.txt' %year)
        with open(filepath, 'rU') as f:
            f.readline()
            data = f.readlines()
        #build dictionary
        drosrefDict = {}
        for row in data:
            fbgn, fbid, name, fbref, species, symbol = row.split('\t')
            if species == 'melanogaster':
                fbref = fbref.split('<newline>')
                drosrefDict[fbgn.split()[0]]= (name, symbol[:-1], [key.split()[0] for key in fbref], len(fbref))
        #serialise dictionary
        picklefile = os.path.join(self.pickledir, 'drosRefDict.pickle')
        with open(picklefile, 'wb') as f:
            pickle.dump(drosrefDict, f, protocol = 2)
        
        return
    
    def loadDrosRefDict(self):
        import cPickle as pickle
        #load dictionary
        picklefile = os.path.join(self.pickledir, 'drosRefDict.pickle')
        with open(picklefile, 'rb') as f:
            drosRefDict = pickle.load(f)
        
        return drosRefDict
        
    def createRefCounterDict(self):
        from tqdm import tqdm
        import cPickle as pickle
        from itertools import ifilter, ifilterfalse, chain
        #load flybaseDict
        flybaseDict = self.loadFlybaseDict()
        #fetch references IDs and find set
        refdataset  = list(chain(*[val[-2] for val in flybaseDict.values()]))
        refset = set(refdataset)
        #count duplicates for each reference
        refcounterDict = {}
        for i, fbref in tqdm(enumerate(refset)):
            refcounterDict[fbref] = len(list(ifilter(lambda x: x==fbref, refdataset)))
            refdataset = list(ifilterfalse(lambda x: x==fbref, refdataset))
        #serialise dictionary
        picklefile = os.path.join(self.pickledir, 'refcounterDict.pickle')
        with open(picklefile, 'wb') as f:
            pickle.dump(refcounterDict, f, protocol = 2)
        
        return
    
    def loadRefCounterDict(self):
        import cPickle as pickle
        #load reference map
        picklefile = os.path.join(self.pickledir, 'refCounterDict.pickle')
        with open(picklefile, 'rb') as f:
            refcounterDict = pickle.load(f)
        
        return refcounterDict
    
    def filterCounterKeys(self, reftype = 'paper'):
        from File_Functions import dictFromFile
        import cPickle as pickle
        from itertools import ifilter
        from tqdm import tqdm
        #fetch reference keys for papers only
        fbrfkeysfile_path = os.path.join(self.flybaseDatadir, 'fbrf_pmid_pmcid_doi_fb_2015_05.txt')
        refDict = dictFromFile(fbrfkeysfile_path, 0, colasarr = True, order = True)
        dsetPaper = zip(refDict.keys(), refDict['pub_type'])
        dsetPaper = list(ifilter(lambda x: x[1] == reftype, dsetPaper))

        #load reference counter dictionary
        refcounterDict = self.loadRefCounterDict()
        
        #filter reference counter keys:
        paperKeys = zip(*dsetPaper)[0]    
        paperKeys_filtered = [key for key in paperKeys if key in refcounterDict]
        paperCounterDict = {}
        for key in tqdm(paperKeys_filtered):
            paperCounterDict[key] = refcounterDict[key]

        picklefile = os.path.join(self.pickledir, 'paperCounterDict.pickle')   
        with open(picklefile, 'w') as f:
            pickle.dump(paperCounterDict, f)
        
        return

    def loadPaperCounterDict(self):
        import cPickle as pickle
        #load dictionary
        picklefile = os.path.join(self.pickledir, 'paperCounterDict.pickle')
        with open(picklefile, 'r') as f:
            paperCounterDict = pickle.load(f)       
        return paperCounterDict

    def quantifyRefBins(self, binbounds = [0, 5, 10, 20, 30, 40, 50, 100]):
        from itertools import ifilter
        #load dictionary
        paperCounterDict = self.loadPaperCounterDict()
        papernumb = paperCounterDict.values()
        #count occurrences in each bin
        freqList = []
        counter = 0
        for i, val in enumerate(binbounds[:-1]):
            binsize = len(list(ifilter(lambda x: val<x<=binbounds[i+1], papernumb)))
            tupl = ('<=%i' %binbounds[i+1], binsize)
            freqList.append(tupl)
            counter += binsize

        freqList.append(('>%i' %binbounds[-1], len(papernumb)-counter))
        
        return freqList
    
    def filterPaperKeys(self, repeats = [1, 2, 3, 4, 5]):
        import cPickle as pickle 
        from itertools import ifilter
        #load dictionary
        paperCounterDict = self.loadPaperCounterDict()
        papertuples = paperCounterDict.items()
        #filter paper keys on the basis of the number of repeats
        paperkeysMap = {}
        if isinstance(repeats, int):
            repeats = [repeats]
        for val in repeats:
            paperkeysMap[val] = [tupl[0] for tupl in ifilter(lambda x: x[1] <= val, papertuples)]
        #serialise keys map dictionary
        picklefile = os.path.join(self.pickledir, 'paperkeysMap.pickle')
        with open(picklefile, 'wb') as f:
            pickle.dump(paperkeysMap, f, protocol = 2)
        
        return
    
    def loadPaperKeysMap(self):
        import cPickle as pickle
        #load dictionary
        picklefile = os.path.join(self.pickledir, 'paperkeysMap.pickle')
        with open(picklefile, 'rb') as f:
            paperkeysMap = pickle.load(f)
            
        return paperkeysMap

        
    def filterFbgn(self):
        import cPickle as pickle
        from tqdm import tqdm
        #load dictionaries
        drosrefDict = self.loadDrosRefDict()
        paperkeysMap = self.loadPaperKeysMap()
        #fetch (fbgn, fbrf) tuples from dictionary
        fbgnTuples = zip(drosrefDict.keys(), [val[2] for val in drosrefDict.values()])
        #filter fbrf lists
        filteredGeneRefMap = {}
        for key in paperkeysMap.keys():
            filteredGeneRefMap[key] = {}
            for (fbgn, fbrfList) in tqdm(fbgnTuples):
                refnumb = len(list(set(fbrfList) & set(paperkeysMap[key])))
                filteredGeneRefMap[key][fbgn] = refnumb
                
        #serialize dictionary
        picklefile = os.path.join(self.pickledir, 'filteredGeneRefMap.pickle')
        with open(picklefile, 'wb') as f:
            pickle.dump(filteredGeneRefMap, f, protocol = 2)
        
        return
    
    def loadGeneRefMap(self):
        import cPickle as pickle
        #load dictionary
        picklefile = os.path.join(self.pickledir, 'filteredGeneRefMap.pickle')
        with open(picklefile, 'rb') as f:
            filteredGeneRefMap = pickle.load(f)
        return filteredGeneRefMap
    
    def quantifyGeneBins(self, binbounds = [0, 1, 2, 3, 4, 5, 10, 20, 30, 40, 50, 100]):
        from itertools import ifilter
        #load dictionary
        generefMap = self.loadGeneRefMap()
        #count occurrences in each bin
        frequenciesMap = {}
        for key in generefMap.keys():
            papernumb = generefMap[key].values()
            freqList = []
            counter = 0
            for i, val in enumerate(binbounds[:-1]):
                if i == 0:
                    binsize = len(list(ifilter(lambda x: x == val, papernumb)))
                    tupl = ('=0', binsize)
                    freqList.append(tupl)
                    counter += binsize
                binsize = len(list(ifilter(lambda x: val<x<=binbounds[i+1], papernumb)))
                tupl = ('<=%i' %binbounds[i+1], binsize)
                freqList.append(tupl)
                counter += binsize
                
            freqList.append(('>%i' %binbounds[-1], len(papernumb)-counter))
            frequenciesMap[key] = freqList
        
        return frequenciesMap
    
    def cumsumRefDist(self):
        import cPickle as pickle
        import numpy as np
        #load dictionary
        generefMap = self.loadGeneRefMap()
        #calculate cumulative sums
        cumsumRefDist = {}
        for key in generefMap.keys():
            generefTuples = generefMap[key].items()
            #sort tuples
            generefTuples_sorted = sorted(generefTuples, key =lambda x:x[1], reverse = True)
            fbgn, refnumb = zip(*generefTuples_sorted)
            cumsumRef = np.cumsum(refnumb)
            cumsumTuples = [((i+1)/float(len(fbgn)), val/float(cumsumRef[-1])) for i, val in enumerate(cumsumRef)]
            cumsumRefDist[key] = cumsumTuples
        #serialise dictionary
        picklefile = os.path.join(self.pickledir, 'cumsumRefDist.pickle')
        with open(picklefile, 'wb') as f:
            pickle.dump(cumsumRefDist, f, protocol = 2)

        return cumsumRefDist
    
    def loadCumsumRefDist(self):
        import cPickle as pickle
        #load dictionary
        picklefile = os.path.join(self.pickledir, 'cumsumRefDist.pickle')
        with open(picklefile, 'rb') as f:
            cumsumRefDist = pickle.load(f)
        
        return cumsumRefDist


class RefDataVis(FlybaseRef):
    
    def __init__(self):
        FlybaseRef.__init__(self)
    
    def barplotsRef(self, repfilter = 1):
        from Plot_Functions import hsvGenerator
        from colorsys import hsv_to_rgb
        from mpl_toolkits.mplot3d import Axes3D
        import matplotlib as mpl
        from matplotlib import pyplot as plt
        from matplotlib.colors import colorConverter
        #load frequencies map
        frequenciesMap = self.quantifyGeneBins()
        if isinstance(repfilter, int):
            repfilter = [repfilter]
        elif not isinstance(repfilter, (tuple, list)):
            raise AssertionError('Datatype error: repfilter must be int or, tuple or list datatype.')
        #fetch data for plotter
        data = [frequenciesMap[key] for key in repfilter]
        data = [zip(*sublist) for sublist in data]
        data = zip(*data)
        xlabels, ydata = data[0][0], data[1]
        xdata = list(xrange(len(xlabels)))

        #Define subplots on grid
        if len(ydata) == 1:
            ax1 = plt.subplot(111)
            [ax1.bar(xdata, ydata[i], width = 0.9, color = 'b') for i in xrange(len(ydata))]
            #set xtick labels
            ax1.set_xticks([i+0.5 for i in xrange(len(xlabels))])
            ax1.set_xticklabels(xlabels, fontsize = 10)
            #set yaxis limit
            ax1.set_ylim([-100, ydata[0][0] + 200])
            #set axis labels
            ax1.set_xlabel('Number of citations per gene', fontsize = 12)
            ax1.set_ylabel('Number of genes', fontsize = 12)
        else:
            ax1 = plt.subplot(111, projection = '3d')
            #Generate colorMap
            cc = lambda arg: colorConverter.to_rgba(arg, alpha=0.6)
            step = 1/float(len(ydata))
            hsvColorMap = hsvGenerator(step, 0.8, 0.8)
            rgbaColorMap = [cc(hsv_to_rgb(h,s,v)) for h,s,v in hsvColorMap]
            #Define 3d projection
            z = [(1 + i) for i in xrange(len(ydata))]
            [ax1.bar(xdata, ydata[i], zs = z[i], zdir = 'y', width = 0.9, color = rgbaColorMap[i]) for i in xrange(len(ydata))]
            #set axis ticks
            ax1.set_xticks([i+0.5 for i in xrange(len(xlabels))])
            ax1.set_yticks(z)
            ax1.set_xticklabels(xlabels, rotation = 10, fontsize = 10)
            ax1.set_yticklabels(repfilter, fontsize = 10)
            #set axis labels
            ax1.set_xlabel('Citations/gene', fontsize = 12)
            ax1.set_ylabel('Repeats/citation', fontsize = 12)
            ax1.set_zlabel('Genes/bin', fontsize = 12)         
        
        plt.tight_layout()
        plt.show()
        return
        
    def lineplotsRef(self, repfilter = 1):
        import matplotlib.pyplot as plt
        #load data
        cumsumRefDist = self.loadCumsumRefDist()
        #reset datatype
        if isinstance(repfilter, int):
            repfilter = [repfilter]
        #plot cumulative distributions
        for key in repfilter:
            data = cumsumRefDist[key]
            xdata, ydata = zip(*data)
            ax = plt.subplot(111)
            ax.plot(xdata, ydata, linewidth = 2, label = '#repeats = %s' %key)
            
        #set axis limits
        ax.set_ylim([0, 1.2])
        #set axis labels
        ax.set_xlabel('Fraction of the gene dataset', fontsize = 11)
        ax.set_ylabel('Fraction of the citations dataset', fontsize = 11)
        #set legend
        ax.legend(loc = 'best', fontsize =11)   
        
        plt.tight_layout()
        plt.show()
        
        return

            
#Unknome().plotUnknomeKnowness([2007, 2014], outliers = True, threshold = 5)
#Unknome().unknomeFetcher('js10', output = 'html')        
#fbrf = FlybaseRef()
#fbrf.cumsumRefDist() 
#rfplot = RefDataVis()
#rfplot.barplotsRef(repfilter = 5)
#freqmap = fbrf.quantifyGeneBins()
#print(freqmap)
#Unknome().buildUnknomeObj()
#print(Unknome().convertID(['cg5458'], outID = 'js'))
#print(fbgnlist)
#print(lethals)
#print(cglist)
#stock = unk.fromCGToStock('CG11103')
#print(stock)
#stocks = 'js151, js84, js204, js36'
#unk.unknomeFetcher(stockinput = stocks, output = 'html')
#ls = KKLibScreen()
#ls.kkPlotter()
#unk = UnknomeExpression()
#unk.expressionPlotter()
