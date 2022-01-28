import sys
import os
import numpy as np
#from bottleneck import median 

def Sn_file():
    cwd = os.getcwd()
    workDir = '%s\Dropbox\Unknome\PythonScripts\Stats' %cwd
    fileName = raw_input('Please, enter file name (e.g Sn12.txt)')
    path = os.path.join(workDir, fileName)
    data = np.fromfile(path, dtype=float, sep='\n') 
    medianArr = np.empty(1)
    for i in xrange(len(data)):
        med = np.median(abs(data - data[i]))
        medianArr = np.column_stack((medianArr, med))
    
    medianArr = np.delete(medianArr, 0)
    Sn = 1.1926 * np.median(medianArr)
    
    return Sn


def Sn_array(SnArr):
    n = len(SnArr)
    medianArr = np.empty(n)
    
    for i in xrange(len(SnArr)):
        medianArr[i] = np.median(abs(SnArr - SnArr[i]))
    
    Sn = 1.1926 * np.median(medianArr)
    
    return Sn


def statsZscores(arr, sn = False):
    '''import Sn_array'''
    if isinstance(arr[0], (list, tuple, np.ndarray)):
        ZscoreList = []; Snlist = []
        for i in xrange(len(arr)):
            med = np.median(arr[i])
            SnArr = abs(med - arr[i])
            Sn = Sn_array(SnArr)
            if sn:
                Snlist.append(Sn)
            zArr = (arr[i] - med)/Sn
            ZscoreList.append(zArr)
        if sn:
            zArr = [ZscoreList, Snlist]
        else:
            zArr = ZscoreList    
    else:
        med = np.median(arr)
        SnArr = abs(med - arr)
        Sn = Sn_array(SnArr)
        zArr = (arr - med)/Sn
        if sn:
            zArr = [zArr, Sn]   
    return zArr

   
def statsFDR(arrList, keySet, alpha = 0.01):
    if isinstance(arrList[0], (int, str, float, np.float64)):
        zipData = zip(keySet, arrList)
        zipData.sort(key=lambda x:x[1])
        data_sorted = zipData
        
        fdrArr = []
        size = float(len(arrList))
        [fdrArr.append(float((i+1))/size*alpha) for i, x in enumerate(arrList)]
        
        keySubsets_fdr = []
        [keySubsets_fdr.append(item[0]) for i, item in enumerate(data_sorted) if item[1] <= fdrArr[i]]
    
           
    else:
        zipData = [zip(keySet, arr) for arr in arrList]    
        [arr.sort(key = lambda x: x[1]) for arr in zipData]
        data_sorted = zipData
    
        fdrArr = []
        size = float(len(arrList[0]))
        [fdrArr.append(float((i+1))/size*alpha) for i, x in enumerate(arrList[0])]
        
        
        keySubsets_fdr = [[] for arr in arrList]
        for i, arr in enumerate(data_sorted):
            [keySubsets_fdr[i].append(item[0]) for j, item in enumerate(arr) if item[1] <= fdrArr[j]]
    
        
    return keySubsets_fdr
    


def dSet_trim(dataLists, headList, ctrlNames, batch = False):
    
    zIndx = [i for i, x in enumerate(headList) if x.startswith('Zscore') or x.startswith('zScore')]
    indx_stockList =[i for i, x in enumerate(headList) if x == 'Stock'][0]
    count = len(zIndx)
        
    if count == 1:
        idex_trim = []
        data_trim = [] 
        if batch:
            batchIndx = [i for i, x in enumerate(headList) if x.startswith('Batch')][0]
            batchSet = list(set(dataLists[batchIndx]))
            batch_trim = [[] for subset in batchSet]
        
        [idex_trim.append(i) for i, x in enumerate(dataLists[indx_stockList]) if x in ctrlNames]
        [idex_trim.append(i) for i, x in enumerate(dataLists[zIndx[0]]) if abs(x) >= 2.5]

        if batch == True:     
            [batch_trim[(dataLists[batchIndx][i])-1].append(x) for i, x in enumerate(dataLists[zIndx[0]-count]) if i not in idex_trim]
            [data_trim.append(x) for i, x in enumerate(dataLists[zIndx[0]-count]) if i not in idex_trim]
        else:
            [data_trim.append(x) for i, x in enumerate(dataLists[zIndx[0]-count]) if i not in idex_trim]
        
    else:
        idex_trim = [[] for i in xrange(count)]
        data_trim = [[] for i in xrange(count)] 
        if batch == True:
            batchIndx = [i for i, x in enumerate(headList) if x.startswith('Batch')][0]
            batchSet = list(set(dataLists[batchIndx]))
            batch_trim = [[[] for subset in batchSet] for i in xrange(count)]    
        for j in xrange(count):
            [idex_trim[j].append(i) for i, x in enumerate(dataLists[indx_stockList]) if x in ctrlNames]
            [idex_trim[j].append(i) for i, x in enumerate(dataLists[zIndx[j]]) if abs(x) >= 2.5]
            if batch == True:
                [batch_trim[j][(dataLists[batchIndx][i])-1].append(x) for i, x in enumerate(dataLists[zIndx[j]-count]) if i not in idex_trim[j]]
                [data_trim[j].append(x) for i, x in enumerate(dataLists[zIndx[j]-count]) if i not in idex_trim[j]] 
            else:
                [data_trim[j].append(x) for i, x in enumerate(dataLists[zIndx[j]-count]) if i not in idex_trim[j]]
    
    if batch == True:            
        return data_trim, batch_trim
    
    else:
        return data_trim


def zTrim(zdata, zscore = 2.5, output = 'non-outlier'):
    
    if output == 'non-outlier':
        if isinstance(zdata[0], (list, tuple, np.ndarray)):
            zIdx_trim = [[i for i, val in enumerate(arr) if abs(val) < zscore] for arr in zdata]
        
        elif isinstance(zdata[0], (float, np.float64)):
            zIdx_trim = [i for i, val in enumerate(zdata) if abs(val) < zscore]
    
    elif output == 'outlier':
        if isinstance(zdata[0], (list, tuple, np.ndarray)):
            zIdx_trim = [[i for i, val in enumerate(arr) if abs(val) >= zscore] for arr in zdata]
        
        elif isinstance(zdata[0], (float, np.float64)):
            zIdx_trim = [i for i, val in enumerate(zdata) if abs(val) >= zscore]
    
    elif output == 'both':
        if isinstance(zdata[0], (list, tuple, np.ndarray)):
            outliers = [[i for i, val in enumerate(arr) if abs(val) >= zscore] for arr in zdata]
            nonoutliers = [[j for j in xrange(len(arr)) if j not in arr] for arr in outliers]
            zIdx_trim = zip(nonoutliers, outliers)
            
        elif isinstance(zdata[0], (float, np.float64)):
            outlier = [i for i, val in enumerate(zdata) if abs(val) >= zscore]
            nonoutlier = [j for j in xrange(len(zdata)) if j not in outlier]
            zIdx_trim = zip(nonoutlier, outlier)
    
    return zIdx_trim
        
     
def dsetTrimFromFile(path, zcols = False, zscore = 2.5, output = 'non-outlier'):
    import pandas as pd
    
    #Fetch headings from file
    with open(path, 'rU') as f:
            heading = f.readline()
            headlist = heading.split('\t')
    
    if zcols == False:
        zIdx = [i for i, x in enumerate(headlist) if x.startswith('Zscore') or x.startswith('zScore')]
    
    elif isinstance(zcols, (list, tuple)):
        zIdx = zcols
    
    elif isinstance(zcols, int):
        zIdx = [zcols]
    
    #Fetch zscores from file
    df = pd.read_csv(path, delimiter = '\t')
    zArrs = [np.asarray(df[headlist[val]]) for val in zIdx]
    
    #Filter out outliers or non-outliers
    if output == 'non-outlier':
        zIdx_trim = [[i for i, val in enumerate(arr) if abs(val) < zscore ] for arr in zArrs]

    elif output == 'outlier':
        zIdx_trim = [[i for i, val in enumerate(arr) if abs(val) >= zscore ] for arr in zArrs]
        
    
    return zIdx_trim


def pointInEllipse(x,y,xp,yp,d,D,angle):
    import math
    #tests if a point[xp,yp] is within
    #boundaries defined by the ellipse
    #of center[x,y], diameter d D, and tilted at angle

    cosa=math.cos(angle)
    sina=math.sin(angle)
    dd=(d/2.0)**2
    DD=(D/2.0)**2

    a =math.pow(cosa*(xp-x)+sina*(yp-y),2)
    b =math.pow(sina*(xp-x)-cosa*(yp-y),2)
    ellipse=(a/dd)+(b/DD)

    if ellipse <= 1.0:
        return True
    else:
        return False


class GeometricMean():
    
    def candMedian(self, dataPoints):
        #Calculate the first candidate median as the geometric mean
        tempX = 0.0
        tempY = 0.0
        
        for i in range(0,len(dataPoints)):
            tempX += dataPoints[i][0]
            tempY += dataPoints[i][1]
        
        return [tempX/len(dataPoints),tempY/len(dataPoints)]
    
    def numersum(self, testMedian,dataPoint):
        import math
        # Provides the denominator of the weiszfeld algorithm depending on whether you are adjusting the candidate x or y
        return 1/math.sqrt((testMedian[0]-dataPoint[0])**2 + (testMedian[1]-dataPoint[1])**2)
    
    def denomsum(self, testMedian, dataPoints):
        import math
        # Provides the denominator of the weiszfeld algorithm
        temp = 0.0
        for i in range(0,len(dataPoints)):
            temp += 1/math.sqrt((testMedian[0] - dataPoints[i][0])**2 + (testMedian[1] - dataPoints[i][1])**2)
        return temp
    
    def objfunc(self, testMedian, dataPoints):
        import math
        # This function calculates the sum of linear distances from the current candidate median to all points
        # in the data set, as such it is the objective function we are minimising.
        temp = 0.0
        for i in range(0,len(dataPoints)):
            temp += math.sqrt((testMedian[0]-dataPoints[i][0])**2 + (testMedian[1]-dataPoints[i][1])**2)
        return temp
    
    def calculateGeoMean(self, dataPoints, numIter = 50):
        '''numIter depends on how long it take to get a suitable convergence of objFunc'''
        #unpack coordinates
        x,y = zip(*dataPoints)
        # Create a starting 'median'
        testMedian = self.candMedian(dataPoints)
        
        #minimise the objective function.
        while numIter:
            try:
                for x in range(0,numIter):
                    denom = self.denomsum(testMedian,dataPoints)
                    nextx = 0.0
                    nexty = 0.0
                
                    for y in range(0,len(dataPoints)):
                        nextx += (dataPoints[y][0] * self.numersum(testMedian,dataPoints[y]))/denom
                        nexty += (dataPoints[y][1] * self.numersum(testMedian,dataPoints[y]))/denom
                
                    testMedian = [nextx,nexty]
                break
            except ZeroDivisionError:
                    numIter = numIter-5
        geoMean = testMedian
        return geoMean 

    def plotGeoMean(self, dataPoints, numIter = 50):
        import matplotlib.pyplot as plt
        #create a plot
        #fig = plt.figure(1, figsize = [10,10], dpi=90)
        axScatter = plt.subplot(111)
        # add data points to scatter plot
        x,y = zip(*dataPoints)
        axScatter.scatter(x,y)
        axScatter.set_aspect(1.)
        # Create a starting 'median'
        testMedian = self.candMedian(dataPoints)
        #print testMedian
        #add mean to scatter plot
        axScatter.scatter(testMedian[0],testMedian[1],s = 50,color='green', marker='x')
        #minimise the objective function.
        testMedians = []
        for x in range(0,numIter):
            #print self.objfunc(testMedian,dataPoints)
            denom = self.denomsum(testMedian,dataPoints)
            nextx = 0.0; nexty = 0.0
            for y in range(0,len(dataPoints)):
                nextx += (dataPoints[y][0] * self.numersum(testMedian,dataPoints[y]))/denom
                nexty += (dataPoints[y][1] * self.numersum(testMedian,dataPoints[y]))/denom
            testMedian = [nextx,nexty]
            # add final median to scatter plot (to see progression add this line into the loop)
            if x < 49:
                testMedians.append(testMedian)
            elif x == numIter-1:
                geoMean = testMedian
                print geoMean
        #plot test medians
        testx, testy = zip(*testMedians)
        axScatter.scatter(testx,testy,  s = 10, color='#BEBCE6', marker='x')
        # add final median to scatter plot
        axScatter.scatter(testMedian[0],testMedian[1],s = 50, color='red', marker='x')
        #axScatter.annotate ('(%.f,%.f)' %(testMedian[0],testMedian[1]), xy = (testMedian[0],testMedian[1]), fontsize = 10)
        #create a legend for plot
        axScatter.legend(('Data Points', 'Centre Mass','Test Medians', 'Geom. Mean'), scatterpoints = 1, fontsize = 12)
        plt.show()
        return

def jointDistPlot(xarr, yarr):
    import seabors as sns
    import matplotlib.pyplot as plt
    #set joint plot
    sns.set(color_codes=True)
    g = sns.jointplot(x = xarr, y = yarr, kind = 'kde')
    #overlay scatter plot
    g.plot_joint(plt.scatter, c="w", s=30, linewidth=1, marker="+")
    g.ax_joint.collections[0].set_alpha(0)
    #set axis labels
    g.set_axis_labels("$X$", "$Y$");
    plt.show()
    return

def weighted_avg_and_sem(values, weights):
    import numpy as np
    from math import sqrt
    """
    Return the weighted average and standard error.
    values, weights -- Numpy ndarrays with the same shape.
    """
    average = np.average(values, weights=weights)
    variance = np.average((values-average)**2, weights = weights)  # Fast and numerically precise
    sem = sqrt(variance)/sqrt(len(values))
    return average, sem

def sumNormRndVar(meansArr, stdArr):
    from math import sqrt
    size = len(meansArr)
    mean = np.mean(meansArr)
    stdev = sqrt(sum(np.power(np.asarray(stdArr), 2)))/size
    return mean, stdev
       