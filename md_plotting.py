import cPickle as pickle
import matplotlib.pyplot as mpl
import numpy as np
from mpl_toolkits.basemap import Basemap
from matplotlib.nxutils import points_inside_poly

def countMDPoints(mds,indices,llcrnrlat=23.0,llcrnrlon=-125.0,urcrnrlat=55,urcrnrlon=-65.0):
    xs = np.arange(llcrnrlon,urcrnrlon,0.1)
    ys = np.arange(llcrnrlat,urcrnrlat,0.1)
    x,y = np.meshgrid(xs,ys)
    x, y = x.flatten(), y.flatten()
    points = np.vstack((x,y)).T
    nx = xs.shape[0]
    ny = ys.shape[0]
    counts = np.zeros((points.shape[0],))
    #print counts.shape
    #print x.shape
    #print y.shape
    for i,md in enumerate(mds):
        if i in indices:
            print i
            poly_xy = np.vstack((md.lons,md.lats)).T
            counts = np.where(points_inside_poly(points,poly_xy),counts+1,counts)
        
    counts = counts.reshape((ny,nx))
    counts = np.ma.array(counts,mask=counts<1)
    x = x.reshape((ny,nx))
    y = y.reshape((ny,nx))
    return counts,x,y


def makeLatLonLists(mds,indices):
    lat_list = []
    lon_list = []
    for i,md in enumerate(mds):
        if i in indices:
            print i
            lat_list.extend(md.lats)
            lon_list.extend(md.lons)
            lat_list.append(None)
            lon_list.append(None)
    return lat_list,lon_list

def getMonths(mds):
    months = [x.issue_date.month for x in mds]
    return np.array(months,dtype=int)

def getAuthors(mds):
    authors = [x.author for x in mds]
    return np.array(authors,dtype='S50')

def mdMonths(mds):
    months = getMonths(mds)
    for month in xrange(1,13):
        print "Month",month
        month_indices = np.nonzero(months==month)[0]
        counts,x,y = countMDPoints(mds,month_indices)
        mpl.figure(figsize=(10,6))
        mpl.subplots_adjust(0,0.02,1,0.9)
        m = Basemap(projection='cyl',resolution='l',llcrnrlon=-125.0,llcrnrlat=23.0,urcrnrlat=55.0,urcrnrlon=-65)
        m.drawstates()
        m.drawcountries()
        m.drawcoastlines()
        mpl.pcolormesh(x,y,counts)
        mpl.title('Mesoscale Discussion Spatial Frequency Month %d' % month)
        cbar = mpl.colorbar(orientation='horizontal',format='%d',extend='max',fraction=.06,aspect=65,shrink=.6,pad=0)
        
        mpl.savefig('md_frequency_month_%02d.png' % month)
        mpl.close()

def getCoAuthorIndices(mds,author):
    indices = []
    for i,md in enumerate(mds):
        if "/" in md.author:
            if author in md.author.split('/'):
                indices.append(i)
    return np.array(indices)

def mdAuthors(mds,author):
    authors = getAuthors(mds)
    #author = 'PETERS'
    author_indices = np.nonzero(authors==author)[0]
    author_indices = np.append(author_indices,getCoAuthorIndices(mds,author))
    counts,x,y = countMDPoints(mds,author_indices)
    mpl.figure(figsize=(10,6))
    mpl.subplots_adjust(0,0.02,1,0.9)
    m = Basemap(projection='cyl',resolution='l',llcrnrlon=-125.0,llcrnrlat=23.0,urcrnrlat=55.0,urcrnrlon=-65)
    m.drawstates()
    m.drawcountries()
    m.drawcoastlines()
    mpl.pcolormesh(x,y,counts)
    mpl.title('Mesoscale Discussion Spatial Frequency for Forecaster %s' % author)
    cbar = mpl.colorbar(orientation='horizontal',format='%d',extend='max',fraction=.06,aspect=65,shrink=.6,pad=0)
    
    mpl.savefig('md_frequency_%s.png' % author)
    mpl.close()

def allMdFrequencies(mds,numWords=1,showTop=100):
    import operator
    all_freq = {}
    for md in mds:
        if md.issue_date.month != 6:
            continue
        print md.disc_id, len(all_freq)
        word_freq = md.getWordFrequencies('discussion',numWords)
        for word,freq in word_freq.iteritems():
            if word in all_freq.keys():
                all_freq[word] += freq
            else:
                all_freq[word] = freq
    print "Number of unique words:  ",len(all_freq)
    sorted_all_freq = sorted(all_freq.iteritems(), key=operator.itemgetter(1),reverse=True)
    for s in sorted_all_freq[0:showTop]:
        print s
    sfile = open('sorted_all_freq_%d_word.csv' % (numWords),'w')
    sfile.write('Word,Frequency\n')
    for s in sorted_all_freq:
        sfile.write("%s,%d\n" % (s[0],s[1]))
    sfile.close()
    return sorted_all_freq
    
def main():
    mds = pickle.load(open('all_mds.pkl'))
    print "Loaded MDs"
    #mdMonths(mds)
    sorted_all_freq = allMdFrequencies(mds,1)

    #mdAuthors(mds,"COHEN")
if __name__=="__main__":
    main()
