import os
import sys
from Flywheel_TrackFunctions import DataVis
import cPickle as pickle


def parseRecordsForTodDB(tablename):
    from Flywheel_TrackFunctions import Dashboard, DatabaseOperations , PlateTracker
    from datetime import datetime
    from itertools import chain
    #load data objects and fetch data 
    plateset = DatabaseOperations().fetchPlateSet()
    plateset_screen = plateset[tablename]
    #parse database records
    todRecords = []
    for fwid in plateset_screen:
        #fetch time of death
        batchdates = Dashboard().batchDates()
        batchdates = batchdates[tablename]
        try:
            stockdata = PlateTracker(fwid).loadStockdata()
            plateflytracks, todplate = stockdata
            todplate = todplate[1:]
        except UnboundLocalError:
            continue
        #fetch batch and wheel numbers 
        stock, date, fwkey = fwid.split('_')
        datetimeObj = datetime.strptime(date, '%d%m%Y').date()
        batchdates.append(datetimeObj); batchdates.sort()
        batchnumb = batchdates.index(datetimeObj)+1
        record_db = DatabaseOperations().fetchRecord(fwkey, 'fwKey', tablename = tablename)[0]
        metadata = (fwid, batchnumb, record_db[11])
        #parse record data
        metadataSet = [metadata]*len(todplate)
        assaydata = zip(metadataSet, todplate)
        assaydata = [list(chain(*entry)) for entry in assaydata]
        assaydata = [entry[:4]+entry[5:7] for entry in assaydata]
        todRecords.append(assaydata)
    #serialise list obj
    picklepath = 'C:\Users\Unknome\Dropbox\Unknome\Screens\Flywheel\PyWheel\PickleFiles\Other\Records%s_tod.pickle' %tablename
    with open(picklepath, 'wb') as f:
        pickle.dump(todRecords, f, protocol = 2)
    return

def fetchTodRecords(tablename):
    import cPickle as pickle
    picklepath = 'C:\Users\Unknome\Dropbox\Unknome\Screens\Flywheel\PyWheel\PickleFiles\Other\Records%s_tod.pickle' %tablename
    with open(picklepath, 'rb') as f:
        todRecords = pickle.load(f)
    return todRecords

            
def createTodTable(tablename, dbpath):
    import sqlite3
    #Connect to database
    db = sqlite3.connect(dbpath)
    cursor = db.cursor()
    #create table
    print('Creating table %s. \n' %tablename)
    createStatement = '''CREATE TABLE  %s (sqlKey INTEGER PRIMARY KEY AUTOINCREMENT, AssayID TEXT NOT NULL, Batch INTEGER NOT NULL, WheelN INTEGER NOT NULL, 
                        WellID TEXT NOT NULL, Censored INTEGER NOT NULL, Death_time REAL)''' %tablename
    cursor.execute(createStatement)
    return      

        
def createTodDB(tablenames, dbpath):
    from itertools import chain
    import sqlite3             
    #Connect to database
    db = sqlite3.connect(dbpath)
    cursor = db.cursor()
    #define tablenames   
    for i, tablename in enumerate(tablenames):
        try:    
            cursor.execute('''SELECT name FROM sqlite_sequence WHERE name = ?''', (tablename,))
            if len(cursor.fetchall()) == 0:
                createTodTable(tablename, dbpath)          
            else:
                print('Table %s already exists. \n' %tablename)  
        except:       
            createTodTable(tablename, dbpath)
        insertStatement = '''INSERT INTO %s (AssayID, Batch, WheelN, WellID, Censored, Death_time) VALUES(?,?,?,?,?,?)''' %tablename 
        print('Inserting data in table %s. \n' %tablename)
        todRecords = fetchTodRecords(tablename)
        todRecords = list(chain(*todRecords))
        todRecords = [todRecords]
        cursor.executemany(insertStatement, todRecords[0])
        db.commit()
    db.close()
    return
        
        
        
def buildTodWellsDist(tablename):
    from Flywheel_TrackFunctions import DatabaseOperations
    plateset = DatabaseOperations().fetchPlateSet()
    plateset_screen = list(plateset[tablename])
    dataset_tod = [data[1] for data in DataVis(plateset_screen).fetchStockdata()]
    dataset_tod = [sorted(tod, key = lambda x:x[0]) for tod in dataset_tod]
    dataset_tod = zip(*dataset_tod)
    dataset_tod = [[entry for entry in well if entry[2] == 1] for well in dataset_tod]
    dataset_tod = [(zip(*well)[0][0], zip(*well)[3]) for well in dataset_tod]
    dataset_tod = [well for well in dataset_tod if well[0] != 't0']
    datasetWells_tod = dict(dataset_tod)
    #serialise
    dirpath = os.path.join(DataVis('').pickledir, 'Other')
    picklepath = os.path.join(dirpath, 'todWellsDist_%s.pickle' %tablename)
    with open(picklepath, 'wb') as f:
        pickle.dump(datasetWells_tod, f, protocol = 2)
    return


def loadTodWellsDist(tablename = 'ROS'):
    dirpath = os.path.join(DataVis('').pickledir, 'Other')
    picklepath = os.path.join(dirpath, 'todWellsDist_%s.pickle' %tablename) 
    with open(picklepath, 'rb') as f:
        datasetTod_wells = pickle.load(f)
    return datasetTod_wells


def plotWellsTodDist(screen):
    import matplotlib.pyplot as plt
    import numpy as np
    from scipy.stats import sem
    #load data objects
    datasetTod_wells = loadTodWellsDist(tablename = screen)
    wellIDs = DataVis('').wellIds
    #calculate sample means and sem
    datasetWells_tod = [(Id, np.mean(datasetTod_wells[Id]), sem(datasetTod_wells[Id])) for Id in wellIDs]
    datasetWells_tod = sorted(datasetWells_tod, key = lambda x:(x[0][0], int(x[0][1:])))#sort on wellIDs
    #define plot variables
    ax = plt.subplot(111)
    colors = ['#9FAEC2', '#C29FBF']*4
    ticklabels = zip(*datasetWells_tod)[0]
    #define arrays to plot
    xset = np.arange(len(ticklabels))
    yset = zip(*datasetWells_tod)[1]
    errors = zip(*datasetWells_tod)[2]
    #plot data
    alpha = 0
    xticks = []
    for i, val in enumerate(xrange(0, 96, 12)):
        if i > 0:
            alpha = 1*i#spacing between bar clusters: plate rows
        ax.bar(np.array(xset[val:val+12]) + alpha, yset[val:val+12], width = 1, align = 'center', color=colors[i], yerr = errors[val:val+12], ecolor=colors[::-1][i])
        xticks = xticks + list(np.array(xset[val:val+12]) + alpha)#define xticks sequence
    #set plot features
    plt.xticks(np.array(xticks))
    ax.set_xticklabels(ticklabels, rotation = 60, fontsize = 11)
    ax.set_xlim([-1,len(ticklabels)+10])
    ax.set_ylim([0, max(yset)+50])
    ax.set_xlabel('Well ID', fontsize = 12)
    ax.set_ylabel('Median survival (hours)', fontsize = 12)
    plt.show()
    return


def calculateTodWellsBias(screen, bias_criteria = 0.05):
    from scipy.stats import ttest_ind
    from collections import Counter
    import numpy as np            
    #load data objects
    datasetTod_wells = loadTodWellsDist(tablename = screen)
    wellIDs = DataVis('').wellIds
    #calculate significance p-values
    ttests_wells = []
    for i, well in enumerate(wellIDs[:-1]):
        calculations = [(well, otherwell, ttest_ind(datasetTod_wells[well], datasetTod_wells[otherwell])) for otherwell in wellIDs[i+1:]]
        ttests_wells.append(calculations)
    significant = [[test for test in well if test[2][1] <= bias_criteria] for well in ttests_wells]#filter out non-significant differences
    significant = [(well[0][0], [test[1] for test in well]) for well in significant if len(well)>0]#fetch wellIDs
    #plate regional codes: E, edge; M, middle; 0, other
    keys = np.arange(1,13)
    values = ['E', 'E', '0', '0', 'M', 'M', 'M', 'M', '0', '0', 'E', 'E']
    plateMap= dict(zip(keys, values))
    #map and count differences
    significant = [[(well[0], plateMap[int(otherwell[1:])]) for otherwell in well[1]] for well in significant]
    significant = [(zip(*well)[0][0], zip(*well)[1]) for well in significant]
    significant = [(well[0], Counter(sorted(well[1]))) for well in significant]
    wellsBias_dict = dict(significant)
    return wellsBias_dict

def plotWellTodBias(screen):
    import matplotlib.pyplot as plt
    from matplotlib.colors import colorConverter
    from Plot_Functions import hsvGenerator
    from colorsys import hsv_to_rgb
    import numpy as np
    #load data object
    wellsBias_dict = calculateTodWellsBias(screen)
    #set dictionary keys
    wellIDs = ['H12', 'G12', 'F12', 'E12', 'H1', 'G1', 'F1', 'E1']
    platemap_keys = ['M', '0', 'E']
    wellsBias = [[wellsBias_dict[Id][key] for key in platemap_keys] for Id in wellIDs]
    #set 
    ax = plt.subplot(111)
    xset = np.arange(3)
    #define color map
    step = 1/float(len(wellIDs))
    hsvColorMap = hsvGenerator(step, 0.9, 0.6)
    cc = lambda arg: colorConverter.to_rgba(arg, alpha=0.6)
    rgbaColorMap = [cc(hsv_to_rgb(h,s,v)) for h,s,v in hsvColorMap]
    #plot well counts
    xticks = []
    for i, well in enumerate(wellIDs):
        alpha = 4*i
        ax.bar(xset + alpha, wellsBias[i], width = 1, align = 'center', color = rgbaColorMap[i], label = well)
        xticks = xticks + list(xset + alpha)#define xticks sequence
    #set plot features
    plt.xticks(np.array(xticks))
    ax.set_xticklabels(platemap_keys*8)
    ax.set_xlim([-1, max(xticks)+1])
    ax.set_xlabel('Plate regions')
    ax.set_ylabel('Number of significant differences', fontsize = 13)
    ax.legend(fontsize = 10)
    plt.show()
    return


def fetchCalCurveData():
    from Flywheel_TrackFunctions import Dashboard
    import numpy as np
    from scipy.stats import sem
    #fetch ydata
    medsurvDict = Dashboard().medSurv_dict
    fwIds = ['w1118_p12_2.5mMParqt', 'w1118_p14_2.5mMParqt', 'w1118_p15_5mMParqt', 'w1118_p16_5mMParqt', 'w1118_p17_7.5mMParqt', 'w1118_p18_7.5mMParqt', 'w1118_p19_10mMParqt', 'w1118_p20_10mMParqt']
    medsurv_array = [medsurvDict[Id] for Id in fwIds]
    medsurv_array = [assay[0] for assay in medsurv_array]#filter out errors
    medsurv_array = [medsurv_array[i-2:i] for i in xrange(2,len(fwIds)+2, 2)]#cluster same [C]
    #calculate means and errors for each paraquat concentration
    medsurv_means = [(np.mean(condition), sem(condition)) for condition in medsurv_array]
    means, errors = zip(*medsurv_means)
    data = [means, errors]
    return data
    
        
def calculateParaquatCalCurve():
    import numpy as np
    from scipy.stats import linregress
    #fetch ydata
    data = fetchCalCurveData()
    means, errors = data
    #log of concentrations
    xset = np.log(np.arange(2.5, 12.5, 2.5))
    #calculate regression line and confidence interval
    m, b, r_value, p, serr = linregress(xset, means)
    ci_boundaries = [-2.58*serr, 2.58*serr]
    paraquatLinefit = [m, b, r_value, p, serr, ci_boundaries]
    return paraquatLinefit

def fetchEmptyParaqData():
    from Flywheel_TrackFunctions import Dashboard
    from ROS_analysis import calculateParaquatCalCurve
    import numpy as np
    from scipy.stats import sem
    from math import exp
    #fetch ydata
    medsurvDict = Dashboard().medSurv_dict
    fwIds = ['Empty_p113_7.5mMParqt', 'Empty_p114_7.5mMParqt']
    medsurv_array = [medsurvDict[Id] for Id in fwIds]
    medsurv_array = [assay[0] for assay in medsurv_array]#filter out errors
    #calculate means and errors for each paraquat concentration
    mean, error = [np.mean(medsurv_array), sem(medsurv_array)]
    linefit = calculateParaquatCalCurve()
    [m, b, r_value, p, serr, ci_boundaries] = linefit
    xfit = (mean-b)/float(m)
    data_empty = [mean, error, xfit] 
    return data_empty
        
    
def plotParaquatCalCurve():
    from Flywheel_TrackFunctions import Dashboard
    import matplotlib.pyplot as plt
    import numpy as np
    from math import exp
    #load data objects
    medsurvDict = Dashboard().medSurv_dict
    data = fetchCalCurveData()
    means, errors = data
    #calculate paraquat calibration curve
    paraquatLinefit = calculateParaquatCalCurve()
    [m, b, r_value, p, serr, ci_boundaries] = paraquatLinefit
    #fetch empty paraquat data
    data_empty = fetchEmptyParaqData()
    [mean_emp, err_emp, xfit_emp] = data_empty
    #fetch medsurv for unknown concentrations
    test_fwIds = ['Empty_13112015_540', 'Empty_16122015_571']
    labels = ['Batch6', 'Batch7', 'Empty']
    labelsdict = dict(zip([1, 2, 3], labels))
    test_medsurv = [medsurvDict[Id] for Id in test_fwIds]
    test_medsurv = [assay[0] for assay in test_medsurv]#filter out errors
    #log of concentrations
    xset = np.log(np.arange(2.5, 12.5, 2.5))
    #calculate yfits
    yfits = np.polyval((m,b), xset)
    boundaries_fits = [np.polyval((m+val,b), xset) for val in ci_boundaries]
    #calculate xfits for test_medsurv
    test_xfits = [(val-b)/float(m) for val in test_medsurv]
    #add empty data to plot arrays
    test_medsurv = test_medsurv + [mean_emp]
    test_xfits = test_xfits + [xfit_emp]
    #plot data
    ax = plt.subplot(111)
    ax.scatter(xset, means)
    ax.errorbar(xset, means, color = 'g', yerr = errors, fmt='o')#error bars
    #plot linefit and confidence interval
    ax.plot(xset, yfits, color = 'r', linewidth = 0.3)
    for boundary in boundaries_fits:
        ax.plot(xset, boundary, color = 'b', linewidth = 0.2, linestyle = '--')#linefit confidence interval
    #plot test_yfits
    colors = ['b', 'm', 'r']
    mstyles = ['x', 'x', 'o']
    for i, xfit in enumerate(test_xfits):
        ax.scatter(xfit, test_medsurv[i], color = colors[i], marker = mstyles[i], s = 50, label = labelsdict[i+1])
        ax.annotate('[C] = %.1f' %exp(test_xfits[i]), (test_xfits[i]+0.05, test_medsurv[i]), textcoords = 'data', fontsize = 12)
    #annotate plot
    ax.annotate('r^2 = %.4f' %r_value**2, (1.0, 140), textcoords = 'data', fontsize = 12)
    #set ticks fontsize
    [tick.label.set_fontsize(10) for tick in ax.xaxis.get_major_ticks()]
    [tick.label.set_fontsize(10) for tick in ax.yaxis.get_major_ticks()]                 
    #set axis labels
    ax.set_xlabel('Paraquat concentration (log[C])')
    ax.set_ylabel('Median survival (hours)', fontsize = 13)
    ax.legend(fontsize = 12)#legend
    plt.show()
    return



'''import numpy as np
from scipy.stats import sem, f_oneway
from pyvttbl import Anova1way
#load data objects
datasetTod_wells = loadTodWellsDist('Starvation')
wellIDs = DataVis('').wellIds
#one-way ANOVA
datasetWells_tod = [np.asarray(datasetTod_wells[Id]) for Id in wellIDs]
fstats, pval = f_oneway(*datasetWells_tod)
print(pval)

datasetWells_tod = [list(datasetTod_wells[Id]) for Id in wellIDs]
conditions_list = wellIDs
D=Anova1way()
D.run(datasetWells_tod, conditions_list=conditions_list)
print(D)'''
