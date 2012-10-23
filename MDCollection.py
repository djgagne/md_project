from datetime import datetime
import numpy as np
import pylab
from numpy.lib import recfunctions as nprf
import re
import matplotlib.mlab as mlab
from mpl_toolkits.basemap import Basemap

class MDCollection:
    """MDCollection:  Set or subset of the Mesoscale Discussions.  The data can be subset by author, year, month, wfo, or what the discussion concerns."""
    def __init__(self,
                data=None,
                fileName="all_mds.csv",
                **kwargs):
        self.conditions = {}
        if len(kwargs) > 0:
            for arg,value in kwargs.iteritems():
                setattr(self,arg,value) 
                self.conditions[arg] = value
             
        if data is None:
            self.loadData(fileName)
            if 'Area' not in self.header:
                areas = self.getMDAreas()
                centroids = self.getMDCentroids()
                self.data = mlab.rec_append_fields(self.data,['Area','CentroidLon','CentroidLat'],[areas,centroids[:,0],centroids[:,1]])
                
                self.header = self.data.dtype.names
                
        else:
            self.header = data.dtype.names
            self.data = data
    
    def __call__(self):
        return self.data
    
    def loadData(self,fileName,delimiter=','):
        """Load Mesoscale Discussion data from CSV file"""
        dataFile = open(fileName)
        header = dataFile.readline()[:-1].split(delimiter)
        header_dtype = []
        for h in header:
            if h in ["DiscID","IssueYear","IssueMonth","IssueDay","IssueHour","IssueMinute"]:
                header_dtype.append((h,int))
            elif h in ["IssueDate","ValidStart","ValidEnd","WFOs","Lat","Lon"]:
                header_dtype.append((h,object))
            else:
                header_dtype.append((h,"S5000"))
        data = []
        for row in dataFile:
            rowList = row[:-1].split(delimiter)
            for i in xrange(len(header)):
                if header[i] in ["IssueDate","ValidStart","ValidEnd"]:
                    rowList[i] = datetime.strptime(rowList[i],"%Y%m%d-%H:%M")
                elif header[i] == "WFOs":
                    rowList[i] = np.array(rowList[i].split(),dtype="S3")
                elif header[i] in ["Lat","Lon"]:
                    rowList[i] = np.array(rowList[i].split(),dtype=float)
            data.append(tuple(rowList))
        dataFile.close()
        all_data = np.array(data,dtype=header_dtype)
        self.data = all_data
        self.header = header
    
    def subsetCategory(self,column,value):
        """
        subsetCategory(column,value)
        Description:  Find all of the Mesoscale discussions that have a particular value for a particular column in the data.
        Parameters:
            column (string) - identifies which column to search
            value (any type) - the quantity being matched.
        """
        if column not in self.header:
            print "Error:   %s is not a column in this dataset"
            return None
        subIndices = np.nonzero(self.data[column]==value)[0]
        if len(subIndices) > 0:
            kwargs = {column:value}
            for condition,value in self.conditions.iteritems():
                kwargs[condition] = value
            return MDCollection(data=self.data[subIndices],**kwargs)
        else:
            return None
        
    def uniqueCategories(self,column):
        """
        uniqueCategories(column):
        Description:  Create an array of the possible unique values for a given column
        Parameters:
            column (string) - identifies the column 
        Returns:  a numpy array with the unique values for a category
        """
        if column not in self.header:
            print "Error:  %s is not a column in this dataset"
        return np.unique(self.data[column])
        
    def subsetContains(self,column,value):
        """
        subsetContains(column,value)
        """
        if column not in self.header:
            print "Error:  %s is not a column in this dataset"
            return None
        subIndices = []
        for i,row in np.ndenumerate(self.data[column]):
            if value in row:
                subIndices.append(i[0])
        subIndices = np.array(subIndices,dtype=np.int64)
        if len(subIndices) > 0:
            kwargs = {column:value}
            for condition,value in self.conditions.iteritems():
                kwargs[condition] = value
            return MDCollection(data=self.data[subIndices],**kwargs)
        else:
            return None    
        
    def calcDiscussionLength(self,measure=('word','character')[0]):
        counts = np.zeros((len(self.data),),dtype=int)
        if measure == 'word':
            for i,disc in np.ndenumerate(self.data['Discussion']):
                counts[i[0]] = len(re.split('[ .-/]+',disc))
        else:
            for i,disc in np.ndenumerate(self.data['Discussion']):
                counts[i[0]] = len(disc)
        return counts
        

    def plotFrequencyMap(self,
                        llcrnrlon=-119.2,
                        llcrnrlat=23.15,
                        urcrnrlon=-65.68,
                        urcrnrlat=48.7):
        import pylab
        pylab.figure(figsize=(10,6))
        pylab.subplots_adjust(0,0,1,1)
        bmap = Basemap(projection="lcc",
                       llcrnrlon=llcrnrlon,
                       llcrnrlat=llcrnrlat,
                       urcrnrlon=urcrnrlon,
                       urcrnrlat=urcrnrlat,
                       resolution='l',
                       lat_0=38.5,
                       lat_1=38.5,
                       lon_0=-97.0)
        counts,x,y = self.countMDPoints(bmap)
        bmap.drawcoastlines()
        bmap.drawcountries(1.0)
        bmap.drawstates(0.5)

        pylab.pcolormesh(x,y,counts)
        pylab.colorbar(orientation='horizontal',format='%d',extend='max',fraction=.06,aspect=65,shrink=.6,pad=0)
        
    
    def countMDPoints(self,bmap,dx=20000,dy=20000):
        from matplotlib.nxutils import points_inside_poly
        xs = np.arange(bmap.llcrnrx,bmap.urcrnrx + dx,dx)
        ys = np.arange(bmap.llcrnry,bmap.urcrnry + dy,dy)
        lon,lat,x_grid,y_grid = bmap.makegrid(xs.shape[0],ys.shape[0],returnxy=True)
        x, y = x_grid.flatten(), y_grid.flatten()
        points = np.vstack((x,y)).T
        
        nx = xs.shape[0]
        ny = ys.shape[0]
        counts = np.zeros((points.shape[0],))

        for i in xrange(self.data.shape[0]):
            md_x,md_y = bmap(self.data['Lon'][i],self.data['Lat'][i])
            poly_xy = np.vstack((md_x,md_y)).T
            counts = np.where(points_inside_poly(points,poly_xy),counts+1,counts)
            
        counts = counts.reshape((ny,nx))
        counts = np.ma.array(counts,mask=counts<1)
        x = x.reshape((ny,nx))
        y = y.reshape((ny,nx))
        return counts,x,y
          
    def getMDAreas(self,dx=20000,dy=20000,
                    llcrnrlon=-119.2,
                    llcrnrlat=23.15,
                    urcrnrlon=-65.68,
                    urcrnrlat=48.7):
        bmap = Basemap(projection="lcc",
                       llcrnrlon=llcrnrlon,
                       llcrnrlat=llcrnrlat,
                       urcrnrlon=urcrnrlon,
                       urcrnrlat=urcrnrlat,
                       resolution='l',
                       lat_0=38.5,
                       lat_1=38.5,
                       lon_0=-97.0)
        from matplotlib.nxutils import points_inside_poly
        xs = np.arange(bmap.llcrnrx,bmap.urcrnrx + dx,dx)
        ys = np.arange(bmap.llcrnry,bmap.urcrnry + dy,dy)
        lon,lat,x_grid,y_grid = bmap.makegrid(xs.shape[0],ys.shape[0],returnxy=True)
        x, y = x_grid.flatten(), y_grid.flatten()
        points = np.vstack((x,y)).T
        
        nx = xs.shape[0]
        ny = ys.shape[0]
        areas = np.zeros((self.data.shape[0],))

        for i in xrange(self.data.shape[0]):
            md_x,md_y = bmap(self.data['Lon'][i],self.data['Lat'][i])
            poly_xy = np.vstack((md_x,md_y)).T
            areas[i] = np.nonzero(points_inside_poly(points,poly_xy))[0].shape[0] * dx * dy / 1000**2

        return areas

    def getMDCentroids(self):
        """
        getMDCentroids
        Purpose:  Calculate the centroid longitudes and latitudes.
        """
        centroids = np.zeros((self.data.shape[0],2))
        for i in xrange(self.data.shape[0]):
            centroids[i,0] = np.mean(self.data['Lon'][i])
            centroids[i,1] = np.mean(self.data['Lat'][i])
        return centroids

    def toCSV(self,outfilename,delimiter=','):
        outfile = open(outfilename,'w')
        outfile.write(delimiter.join(self.header) + '\n')
        
        for i in xrange(self.data.shape[0]):
            row = self.data[i]
            rowStr = ""
            for j,item in enumerate(row):
                if j in range(6):
                    rowStr += "%d" % item
                elif j in range(6,9):
                    rowStr += item.strftime("%Y%m%d-%H:%M") 
                elif self.header[j] in ['WFOs']:
                    rowStr += " ".join(list(item))
                elif self.header[j] in ['Lat','Lon']:
                    rowStr += " ".join(["%3.2f" % x for x in item])
                elif j > 16:
                    rowStr += "%8.4f" % item
                else:
                    rowStr += item
                rowStr += delimiter
            outfile.write(rowStr + '\n')
        outfile.close()
if __name__=="__main__":
    m = MDCollection()
    for year in range(2004,2013):
        d = m.subsetContains("Author", "CARBIN").subsetCategory("IssueYear", year)
        d.plotFrequencyMap() 
        pylab.savefig("md_carbin_year_%d.png" % (year),dpi=300)
        pylab.close()
