import numpy as np

def gridSize(numbax):
    
    while numbax:
        blocks = [[i for i in xrange(numbax+1) if i*j == numbax] for j in xrange(numbax+1)]
        blocks = [val for sublist in blocks for val in sublist]
        blocks = [[(i, val) for val in blocks if val*i == numbax] for i in blocks]
        blocks = [val for sublist in blocks for val in sublist]
        if numbax > 3:
            blocks = [tupl for tupl in blocks if tupl[0] != numbax and tupl[1] != numbax]
            if len(blocks) == 0:
                numbax +=1
            else:
                break
        else:
            break
            
    sortkey = [(abs(a-b), i) for i, (a,b) in enumerate(blocks)]
    sortkey = sorted(sortkey, key = lambda x:x[0])
    sortkey = [tupl for tupl in sortkey if tupl[0] == sortkey[0][0]]
    
    blocks = [blocks[key[1]] for key in sortkey]
    blocks = sorted(blocks, key = lambda x:x[0])
    rows, cols = blocks[0]
    
    return rows, cols


def hsvGenerator(step, s, v, hrange = [0,1.0]):
    hmin, hmax = hrange
    hue = [i for i in np.linspace(hmin, hmax, num = step, endpoint = False)]
    colorRange = [(h, s, v) for h in hue]
    return colorRange

def colorMap(step, s, v, hrange = [0,1.0]):
    from colorsys import hsv_to_rgb
    from matplotlib.colors import colorConverter
    #Generate colorMaps
    hsvColorMap = hsvGenerator(step, s, v, hrange = hrange)
    cc = lambda arg: colorConverter.to_rgba(arg, alpha=0.6)
    rgbaColorMap = [cc(hsv_to_rgb(h,s,v)) for h,s,v in hsvColorMap]
    return rgbaColorMap

#rows, cols = gridSize(7)
#print('\n%i rows and %i cols' %(rows, cols))