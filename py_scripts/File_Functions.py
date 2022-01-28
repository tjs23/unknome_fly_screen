import os
import sys
import numpy as np
import pandas as pd


def writeFile(keySet, dataLists, headList, path, keys = True):
    
    if os.path.isfile(path):
        fileName = os.path.split(path)[1]
        answer = raw_input('This file (%s) already exists, overwrite it (y, n)? ' %fileName)
        answer.lower()
        
        while answer not in ['y', 'n']:
            answer = raw_input('Wrong answer! Please, enter Yes (y) or No (n)? ')
            answer.lower()
        
        if answer == 'n':
            return
    
        elif answer == 'y':
    
            fileObj = open(path, 'w')
            headLine = '\t'.join(headList) + '\n'
            fileObj.write(headLine)
            if keys == True:
                dataLists.insert(0, keySet)
            zipData = zip(*dataLists)
            
            for data in zipData:
                line = map('{}'.format, data)
                line = '\t'.join(line) + '\n'
                fileObj.write(line)
                
            return
    
    else:
        
        fileObj = open(path, 'w')
        headLine = '\t'.join(headList) + '\n'
        fileObj.write(headLine)
        if keys == True:
            dataLists.insert(0, keySet)
        zipData = zip(*dataLists)
        
        for data in zipData:
            line = map('{}'.format, data)
            line = '\t'.join(line) + '\n'
            fileObj.write(line)
            
        return 
        
        
                
def writeData(keySet, data, headList, path, keys = True):
    
    if os.path.isfile(path):
        fileName = os.path.split(path)[1]
        answer = raw_input('This file (%s) already exists, overwrite it (y, n)? ' %fileName)
        answer.lower()
        
        while answer not in ['y', 'n']:
            answer = raw_input('Wrong answer! Please, enter Yes (y) or No (n)? ')
            answer.lower()
        if answer == 'n':
            return
        elif answer == 'y':
            lines= []
    
            with open(path, 'w') as f:
                if len(headList) > 1:
                    headLine = '\t'.join(headList) + '\n'
                else:
                    headLine = headList[0] + '\n'  
                lines.append(headLine)
                
                if keys == True:
                    if  isinstance(data[0], (list,tuple)):
                        if isinstance(data[0], tuple):
                            data = [list(item) for item in data]
                        [item.insert(0, keySet[i]) for i, item in enumerate(data)]
          
                for item in data:   
                    if isinstance(data[0], (list, tuple, np.ndarray)):
                        line = map(str, item)
                        line = '\t'.join(line) + '\n'
                    elif isinstance(data[0], (str, float, int)):
                        line = '{}'.format(item)
                        line = line + '\n'
                    
                    lines.append(line)
                
                f.seek(0)
                f.writelines(lines)
                f.truncate()
                                
        
    else:
        
        with open(path, 'w') as f:
            lines = []
        
            if len(headList)>1:
                headLine = '\t'.join(headList) + '\n'
            else:
                headLine = headList[0] + '\n'
                
            lines.append(headLine)
            
            if keys == True:
                if  isinstance(data[0], (list,tuple)):
                    if isinstance(data[0], tuple):
                        data = [list(item) for item in data]
                    [item.insert(0, keySet[i]) for i, item in enumerate(data)]
    
            
            for item in data:   
                if isinstance(data[0], (list, tuple, np.ndarray)):
                    line = map(str, item)
                    line = '\t'.join(line) + '\n'
                elif isinstance(data[0], (str, float, int)):
                    line = '{}'.format(item)
                    line = line + '\n'
                
                lines.append(line)
            
            f.seek(0)
            f.writelines(lines)
            f.truncate()
            
    return     


def read_into_buffer(filename):
    buf = bytearray(os.path.getsize(filename))
    with open(filename, 'rb') as f:
        f.readinto(buf)
    return buf


def fileAddCols(path, arrs, newcols):
    typeDict = {str: 's', float:'f', int: 'd', np.float64: 'f'}
    
    if isinstance(arrs[0], (list, tuple, np.ndarray)):
        newval_rows = zip(*arrs) 
    elif isinstance(arrs[0], (str, int, float)):
        newval_rows = arrs
    else:
        print('Unrecognised datatype: data arrays ')
        sys.exit()
    
    with open(path, 'r+') as f:
        newlines = []
        oldlines = f.readlines()
        oldlines = [line[:-1] for line in oldlines]
        
        if isinstance(newcols, (list, tuple)):
            if len(newcols) > 1:
                strNewcols = '\t'.join(newcols)
            else:
                strNewcols = newcols[0]
        elif isinstance(newcols, str):
            strNewcols = newcols
        else:
            print('Unrecognised datatype: newcols. ')
            sys.exit()
            
        headlist = '%s\t%s\n' %(oldlines[0], strNewcols)
        newlines.append(headlist)
        
        if isinstance(arrs[0], (list, tuple, np.ndarray)):
            for i, newrow in enumerate(newval_rows):
                oldline = oldlines[i+1]
                valtype = [type(val) for val in newrow]
                newvals = ['{0:{typ}}'.format(val, typ = typeDict[valtype[i]]) for i, val in enumerate(newrow)]
                newvals = '\t'.join(newvals)  
                newline = '%s\t%s\n' %(oldline, newvals)
                newlines.append(newline)
        else:
            for i, val in enumerate(newval_rows):
                oldline = oldlines[i+1]
                valtype = type(val)
                newvals = '{0:{typ}}'.format(val, typ = typeDict[valtype]) 
                newline = '%s\t%s\n' %(oldline, newvals)
                newlines.append(newline)
            
        f.seek(0)
        f.writelines(newlines)
        f.truncate()
        
    return



def dictFromFile(path, keycols, separator = '', skiprows = 0, usecols = 0, colasarr = False, order = False): 
    
    ''' It builds and returns a dictionary from a tab separated file. Arguments keycols and usecols are either integers 
    or, lists or tuples, of integers. skiprows = integer and separator = string.'''
    
    from itertools import chain
    from collections import OrderedDict
    
    #Fetch column headings from file
    with open(path, 'rU') as f:
        headline = f.readline()
        heads = headline[:-1].split('\t')

    #Fetch data from file
    df = pd.read_csv(path, delimiter = '\t')
    data = [df[head] for head in heads]

    #Generate keyset from keycols arg
    if isinstance(keycols, int):
        keyset = list(data[keycols])
    elif isinstance(keycols, (list, tuple)):
        keyset = [data[i] for i in keycols]
        keyset = zip(*keyset)
        keyset = [separator.join(map(str, key)) for key in keyset]
    else:
        print('Unrecognised datatype: keycols. ')
        sys.exit()
    
    #Generate dictionary: determine usecols instance
    if isinstance(usecols, (list, tuple)):
        #Flatten usecols
        for i, item in enumerate(iter(usecols)):
            if isinstance(item, (list, tuple)):
                continue
            elif isinstance(item, (int, float)):
                usecols[i] = [item] 
        usecols = [i for i in chain(*usecols)]
        
        #Fetch data and build dictionary       
        usedata = [data[i] for i in usecols]
        zipdata = zip(*usedata)
        subkeys = [heads[i] for i in usecols]
        
        if order:
            zipdata = [OrderedDict(zip(subkeys, item)) for item in zipdata]
            dataDict = OrderedDict(zip(keyset[skiprows:], zipdata[skiprows:]))
        else:    
            zipdata = [dict(zip(subkeys, item)) for item in zipdata]
            dataDict = dict(zip(keyset[skiprows:], zipdata[skiprows:]))
        
        #Conditional: add columns as arrays to dictionary
        if colasarr: 
            for i, head in enumerate(heads):
                if i in usecols:
                    dataDict[head] = np.asarray(data[i])
    
    elif isinstance(usecols, int) and usecols != 0:
        usedata = data[usecols]
        if order: 
            dataDict = OrderedDict(zip(keyset[skiprows:], usedata[skiprows:]))
        else:
            dataDict = dict(zip(keyset[skiprows:], usedata[skiprows:]))
            
        if colasarr: 
            dataDict[heads[usecols]] = np.asarray(data[usecols])
    
    elif usecols == 0:
        if isinstance(keycols, (list, tuple)):
            usedata = [data[i] for i in xrange(len(heads)) if i not in keycols]
            usecols = [i for i in xrange(len(heads)) if i not in keycols]  
        else:
            usedata = [data[i] for i in xrange(len(heads)) if i != keycols]
            usecols = [i for i in xrange(len(heads)) if i != keycols]

        zipdata = zip(*usedata)
        subkeys = [heads[i] for i in usecols]
        if order:
            zipdata = [OrderedDict(zip(subkeys, item)) for item in zipdata]
            dataDict = OrderedDict(zip(keyset[skiprows:], zipdata[skiprows:]))    
        else:
            zipdata = [dict(zip(subkeys, item)) for item in zipdata]
            dataDict = dict(zip(keyset[skiprows:], zipdata[skiprows:]))
        
        #Conditional: add columns as arrays to dictionary  
        if colasarr:
            for i, head in enumerate(heads):
                if isinstance(keycols, (list, tuple)):
                    if i not in keycols:
                        dataDict[head] = np.asarray(data[i])
                else:
                    if i != keycols:
                        dataDict[head] = np.asarray(data[i])
        
    return dataDict


def fileDict(filePath, keycol = 0, usecol = all):
    
     df = pd.read_csv(filePath, delimiter = '\t')
     
     with open(filePath, 'rU') as f:
         headlist = f.readline()[:-1]
         headlist = headlist.split('\t')
         
     if isinstance(keycol, int):    
        keyset = df[headlist[keycol]]
        keycol = [keycol]
     elif isinstance(keycol, tuple):
         keyset = np.loadtxt(filePath, dtype = str, skiprows = 1, usecols = keycol)
         keyset = ['_'.join(key.tolist()) for key in keyset]
     
     if usecol == all:
         try:
            data = [df[head] for head in headlist if headlist.index(head) not in keycol]
            zipdata = zip(*data)
         except TypeError:
             data = [df[head] for head in headlist if headlist.index(head) != keycol]
             zipdata = data[0]
         fileDict = dict(zip(keyset,zipdata))        
     elif isinstance(usecol, (list, tuple)):
         keycol = [keycol]
         subheads = [headlist[i] for i in usecol if i not in keycol]
         data = [df[head] for head in subheads]
         zipdata = zip(*data)
         fileDict = dict(zip(keyset,zipdata))
     elif isinstance(usecol, int):
         if usecol != keycol:
            head = headlist[usecol] 
            data = df[head]
            fileDict = dict(zip(keyset, data))
         else:
            print('Error: variables keycol and usecol have identical values. ')
            sys.exit()
         
     return fileDict
     
def slicer(lst, n):
        chunk = len(lst)/n
        for i in xrange(0, len(lst), chunk):
            yield lst[i:i+chunk]

def writeColumns(path, arrs, colnames, newfile = True):
    import itertools
    
    typeDict = {str: 's', float:'f', int: 'd', np.float64: 'f'}
    
    if isinstance(arrs[0], (list, tuple, np.ndarray)):
        sizes = [len(arr) for arr in arrs]
        if sizes ==  len(sizes)*[sizes[0]]:       
            newval_rows = zip(*arrs)
        else:
            newval_rows = list(itertools.izip_longest(*arrs, fillvalue=''))
    elif isinstance(arrs[0], (str, int, float)):
        newval_rows = arrs
    else:
        print('Unrecognised datatype: data arrays ')
        sys.exit() 
    
    if not newfile:
        mode = 'r+'
    elif newfile:
        mode = 'w'
    else:
        print('\nValueError: newfile propertie values must be boolean.\nThe script was teminated.')
        sys.exit()
    
    with open(path, mode) as f:
        if not newfile:
            oldlines = f.readlines()
            oldlines = [line[:-1] for line in oldlines]
        
        if isinstance(colnames, (list, tuple)):
            if len(colnames) > 1:
                newheads = '\t'.join(colnames)
            else:
                newheads = colnames[0]
        elif isinstance(colnames, str):
            newheads = colnames
        else:
            print('Unrecognised datatype: colnames. ')
            sys.exit()
        
        if newfile:
            headlist = '%s\n' %newheads
        else:
            oldlines = f.readlines()
            oldlines = [line[:-1] for line in oldlines]   
            headlist = '%s\t%s\n' %(oldlines[0], newheads)
        
        text = []
        text.append(headlist)
        
        if isinstance(arrs[0], (list, tuple, np.ndarray)):
            for i, newrow in enumerate(newval_rows):
                valtype = [type(val) for val in newrow]
                newvals = ['{0:{typ}}'.format(val, typ = typeDict[valtype[i]]) for i, val in enumerate(newrow)]
                newvals = '\t'.join(newvals)
                
                if not newfile:
                    oldline = oldlines[i+1]  
                    newline = '%s\t%s\n' %(oldline, newvals)
                else:
                    newline = '%s\n' %newvals
                
                text.append(newline) 
        else:
            for i, val in enumerate(newval_rows):
                valtype = type(val)
                newvals = '{0:{typ}}'.format(val, typ = typeDict[valtype])
                
                if not newfile:
                    oldline = oldlines[i+1] 
                    newline = '%s\t%s\n' %(oldline, newvals)
                else:
                    newline = '%s\n' %newvals
                    
                text.append(newline)   
        
        f.seek(0)
        f.writelines(text)
        f.truncate()
        
    return


def getDirname(path, subdirname):
    while path:
        pathparts = os.path.split(path)
        if pathparts[1] == subdirname:
            dirname = os.path.split(pathparts[0])[1]
            return dirname
        else:
            path = pathparts[0]


def iterPartition(pred, iterable):
    from itertools import ifilterfalse, ifilter, tee
    '''Use a predicate to partition entries into false entries and true entries'''
    # partition(is_odd, range(10)) --> 0 2 4 6 8   and  1 3 5 7 9
    t1, t2 = tee(iterable)
    return ifilter(pred, t1), ifilterfalse(pred, t2)

def listPartition(pred, iterable):
    '''Use a predicate to split a list into two simultaneously''' 
    trues = []
    falses = []
    for item in iterable:
        if pred(item):
            trues.append(item)
        else:
            falses.append(item)
    return trues, falses


def printList(anyList, lineSize):
    quocient = len(anyList)/lineSize
    remainder = len(anyList)%lineSize
    
    for i in xrange(quocient):
        line = (lineSize * '%s\t ' + '\n') %tuple(anyList[(i*lineSize):((i+1)*lineSize)])
        print(line)
        if i+1 == quocient:
            line = (remainder * '%s\t') %tuple(anyList[((i+1)*lineSize):((i+1) *lineSize + (remainder + 1))])
            print(line)         
    return

def deepSplitSequence(seq):
    import numpy as np
    import copy

    depthlist = []
    while isinstance(seq[0], (tuple, list, np.ndarray)):
        depth = len(seq)
        depthlist.append(depth)
        seq = seq[0]
    depthlist.pop()
    depthlist.insert(0, len(seq))

    mirrorlists = []
    for val in reversed(depthlist):
        mirrorlists = [mirrorlists[:] for i in xrange(val)]
        mirrorlists = [copy.deepcopy(sublist) for sublist in mirrorlists]
    return mirrorlists

def flattenList(iterable):
    from itertools import chain
    while iterable:
        if isinstance(iterable[0], (list, tuple)):
            iterable = list(chain(*iterable))
        else:
            break
    return iterable


