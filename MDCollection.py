from datetime import datetime,timedelta
import numpy as np
from numpy.lib import recfunctions as nprf

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
        else:
            self.data = data

    def loadData(self,fileName,delimiter=','):
        """Load Mesoscale Discussion data from CSV file"""
        dataFile = open(fileName)
        header = dataFile.readline()[:-1].split(delimiter)
        header_dtype = []
        for h in header:
            if h in ["DiscID","IssueYear","IssueMonth","IssueDay"]:
                header_dtype.append((h,int))
            elif h in ["IssueDate","ValidStart","ValidEnd","WFOs","Lat","Lon"]:
                header_dtype.append((h,object))
            else:
                header_dtype.append((h,"S5000"))
        data = []
        for r,row in enumerate(dataFile):
            rowList = row[:-1].split(delimiter)
            for i in xrange(len(header)):
                if header[i] in ["IssueDate","ValidStart","ValidEnd"]:
                    rowList[i] = datetime.strptime(rowList[i],"%Y%m%d-%H:%M")
                elif header[i] == "WFOs":
                    rowList[i] = np.array(rowList[i].split(),dtype="S3")
                elif header[i] in ["Lat","Lon"]:
                    rowList[i] = np.array(rowList[i].split(),dtype=float)
            print rowList[0]
            data.append(tuple(rowList))
        dataFile.close()
        print header_dtype
        all_data = np.array(data,dtype=header_dtype)
        self.data = all_data
        self.header = header
    
    def subsetCategory(self,column,value):
        if column not in self.header:
            print "Error:   %s is not a column in this dataset"
            return None
        subIndices = np.nonzero(self.data[column]==value)[0]
        kwargs = {column:value}
        for condition,value in self.conditions.iteritems():
            kwargs[condition] = value
        return MDCollection(data=self.data[subIndices],**kwargs)
        
                        
            
        
                
