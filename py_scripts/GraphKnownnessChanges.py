import os
import sys
import cPickle
import numpy as np
from collections import defaultdict
from datetime import date
from matplotlib import pyplot as plt
 
NUM_QUANTS = 10
   
colors = ['#FF0000', '#FF8000', '#C0C000', '#80C000', '#00C000',
          '#00C080', '#00C0C0', '#0080FF', '#0000FF', '#8000FF']
          
cwd = os.getcwd()
pickledir = '%s\Dropbox\Unknome\Archive\Dataset\PickleFiles' %cwd
picklefile =   os.path.join(pickledir,'Knownness_by_year.pickle')

cluster_date_scores = cPickle.load(open(picklefile))

years = list(range(2007, 2015))
dates = [date(year, 12, 31) for year in years]


fig, axarr = plt.subplots(2, 2)
fig.set_size_inches(12, 18)  

start_date = dates[0]

sort_list = [(cluster_date_scores[cl][start_date],  cl) for cl in cluster_date_scores]
sort_list.sort(reverse=True)

initial_scores, initial_clusters = zip(*sort_list)

n = len(initial_scores)
quant_width = n / float(NUM_QUANTS)

# Collect cluster membership and scores for initial year quantiles

orig_score_limits = []
orig_quant_clusters = []
for q in range(NUM_QUANTS):
  a = int(quant_width*q)
  b = int(quant_width*(q+1)) + 1 
  
  orig_quant_clusters.append(set(initial_clusters[a:b]))
  orig_score_limits.append(max(initial_scores[a:b]))

orig_score_limits.reverse()

# Plot scores for each year according to the membership of the first year

graph_data = []
for clusters in orig_quant_clusters:
  
  kSums = defaultdict(float)
  kCounts = defaultdict(float)
    
  for cid in clusters:
    for d in dates:
      kSums[d] += cluster_date_scores[cid][d]
      kCounts[d] += 1.0
  
  vals = [kSums[d]/kCounts[d] for d in dates]

  graph_data.append(vals)
  
ax = axarr[0,0]

for i, vals in enumerate(graph_data):
  ax.plot(years, vals, color=colors[i])

ax.set_xlabel('Year')
ax.set_ylabel('Mean score of original quantile')
ax.set_xticklabels(years)

# Track jumps across original quantiles
# - see how many original members remain in each year's quantiles

x_vals = dates
y_vals = [[] for q in range(NUM_QUANTS)]
y_vals_2 = [[] for q in range(NUM_QUANTS)]
date_quants_prev = None
date_rank_dict = {}

for d in dates:
  
  date_ranks = []
  for cid in cluster_date_scores:
    date_ranks.append( (cluster_date_scores[cid][d], cid) )

  date_ranks.sort(reverse=True)
  date_rank_dict[d] = reversed(date_ranks)
  
  date_quants = []
  for q in range(NUM_QUANTS):
    a = int(quant_width*q)
    b = int(quant_width*(q+1)) + 1
    date_quants.append(set([x[1] for x in date_ranks[a:b]]))
  
  # Loss relative to first year
  
  for q in range(NUM_QUANTS):
    loss = orig_quant_clusters[q] - date_quants[q]
    n_lost = len(loss)
    y_vals[q].append(100.0 * n_lost/float(len(orig_quant_clusters[q])))
  
  if date_quants_prev:
    # Loss from last year
  
    for q in range(NUM_QUANTS):
      loss = date_quants_prev[q] - date_quants[q]
      n_lost = len(loss)
      y_vals_2[q].append(100.0 * n_lost/float(len(orig_quant_clusters[q])))
 
  date_quants_prev = date_quants

# Plot changes from first year

ax = axarr[0,1]
for q in range(NUM_QUANTS):
  ax.plot(x_vals, y_vals[q], color=colors[q], label='%d' % (10*(q+1)))

ax.set_xlabel('Year')
ax.set_ylabel('Original quantile loss (%)')
ax.set_xticklabels(years)
ax.legend(fontsize=10)

# Plot changes from previous year

ax = axarr[1,0]
for q in range(NUM_QUANTS):
  ax.plot(x_vals[1:], y_vals_2[q], color=colors[q], label='%d' % (10*(q+1)))

ax.set_xlabel('Year')
ax.set_ylabel('Year to year quantile loss (%)')
ax.set_xticklabels(years[1:])
ax.legend(fontsize=10)


# Plot counts given original quantile limits

threshold_distrib = [[] for q in range(NUM_QUANTS)]

for d in dates:
  threshold_counts = [0.0] * NUM_QUANTS
  
  i = 0
  th = orig_score_limits[i]
  
  for k_val, cid in date_rank_dict[d]:
    while (k_val > th) and (i < NUM_QUANTS-1):
      i += 1
      th = orig_score_limits[i]
      
    threshold_counts[i] += 1.0
  
  print d, threshold_counts
  
  for q in range(NUM_QUANTS):
    threshold_distrib[q].append(threshold_counts[q]) 

ax = axarr[1,1]   
x_vals = np.arange(len(dates))

threshold_distrib = np.array(threshold_distrib)

bar_width = 0.8

for q in range(NUM_QUANTS):
  
  if q == 0:
    ax.bar(x_vals, threshold_distrib[q], width=bar_width, color=colors[q], label='%d' % (10*(q+1)))
    bottom = threshold_distrib[q]
  else:
    ax.bar(x_vals, threshold_distrib[q], width=bar_width, bottom=bottom, color=colors[q], label='%d' % (10*(q+1)))
    bottom += threshold_distrib[q]

ax.set_xlim((0, x_vals.max() + bar_width))    
ax.set_ylim((0, n))  

ax.set_xlabel('Year')
ax.set_ylabel('Counts for orginal quantile threshold')
ax.xaxis.set_ticks(x_vals + bar_width/2) 
ax.set_xticklabels(years)
#ax.legend()

plt.show()








