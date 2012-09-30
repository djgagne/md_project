import os
import re
import urllib2
from datetime import datetime,timedelta
from pytz import timezone
from MD import MD

def getMDText(year,md_number):
    """getMDText
       Description:  Given a year and a discussion number, read the mesoscale discussion from the web and extract the discussion text"""
    if year < 2012:
        md_url = "http://www.spc.noaa.gov/products/md/%d/md%04d.html" % (year,md_number)
    else:
        md_url = "http://www.spc.noaa.gov/products/md/md%04d.html" % (md_number)
    
    try:
        md_site = urllib2.urlopen(md_url)
    except:
        return None
    md_web = md_site.read()
    md_site.close()
    start_match = re.search("<pre>",md_web)
    end_match = re.search("</pre>",md_web)
    if start_match is None:
        return None
    else:
        return md_web[start_match.end():end_match.start()]

def getMDYear(year,number=1):
    good = True
    while good:
        print number
        text = getMDText(year,number)
        if text is None:
            good = False
        else:
            outfile = open("spc_md_text/%d/%d_%04d.txt" % (year,year,number),"w")
            outfile.write(text)
            outfile.close()
            number += 1

def getForecasterAuthorCount(year):
    import os
    md_dir = "spc_md_text/%d/" % year
    discs = sorted(os.listdir(md_dir))
    forecasters = {}
    for disc_filename in discs:
        disc_file = open(md_dir + disc_filename)
        disc_str = disc_file.readlines()
        disc_file.close()
        for line in disc_str:
            fcst_re = re.match("\.\.[A-Z/]+\.\.",line.strip())
            if fcst_re is not None:
                forecaster_name = line[fcst_re.start():fcst_re.end()+1].strip().strip("..")
                if forecaster_name not in forecasters.keys():
                    forecasters[forecaster_name] = 1
                else:
                    forecasters[forecaster_name] += 1
    return forecasters

def convertIssueDate(date_str):
    dlist = date_str.split()
    year = int(dlist[-1])
    month = datetime.strptime(dlist[-3],"%b").month
    day = int(dlist[-2])
    hour = int(dlist[0][0:2])
    minute = int(dlist[0][2:])
    if dlist[1]=="PM" and hour < 12:
        hour = hour + 12
    if dlist[2]=="CST":
        return datetime(year,month,day,hour,minute,tzinfo=timezone("US/Central")).astimezone(timezone("UTC"))
    else:
        tz = timezone("US/Central")
        return tz.localize(datetime(year,month,day,hour,minute),is_dst=True).astimezone(timezone("UTC"))

def getMDMetadata(year,number):
    """Description:  Separate a mesoscale discussion into the various components"""
    md_filename = "spc_md_text/%d/%d_%04d.txt" % (year,year,number)
    md_file = open(md_filename)
    md_text = md_file.read()
    md_file.close()
    if len(md_text) < 10: 
        return None
    #print md_text
    issue_date_re = re.search("[0-9]{4} [AP]M C[SD]T [A-Z]{3} [A-Z]{3} [0-9]{2} [0-9]{4}",md_text) 
    issue_date = md_text[issue_date_re.start():issue_date_re.end()]
    issue_datetime = convertIssueDate(issue_date)
    #print issue_date,issue_datetime.timetuple()
    concerns_re = re.search("CONCERNING...[A-Z ...]+",md_text)
    concerns = md_text[concerns_re.start():concerns_re.end()]
    #print concerns.strip().split('...')[1:]
    concernList = concerns.strip().split('...')[1:]
    concerning = concernList[0]
    if len(concernList) > 1:
        watchLikely = concernList[1]
    else:
        watchLikely = 'NA'
    valid_re = re.search("VALID [0-9]{6}Z - [0-9]{6}Z",md_text)
    valid_text = md_text[valid_re.start():valid_re.end()]
    valid_list = valid_text.split()[1:]
    valid_start = datetime.strptime(issue_datetime.strftime("%Y%m") + valid_list[0],"%Y%m%d%H%MZ")
    valid_end = datetime.strptime(issue_datetime.strftime("%Y%m") + valid_list[2],"%Y%m%d%H%MZ")
    #print valid_list,valid_start,valid_end
    author_re = re.search(" \.\.[A-Z/]+\.\. ",md_text)
    #print md_text[author_re.start():author_re.end()].strip("..")
    author = md_text[author_re.start():author_re.end()].strip().strip("..")
    
    discussion_text = md_text[valid_re.end():author_re.start()].strip()
    discussion_list = discussion_text.split('\n   \n   ')
    summary = discussion_list[0].replace('\n   ',' ')
    discussion = '  '.join(discussion_list[1:]).replace('\n   ',' ')
    #print summary
    #print discussion

    attn_re = re.search("ATTN...[A-Z\.]+",md_text)
    attn = md_text[attn_re.start():attn_re.end()]
    attn_list =  attn.split("...")[2:-1]

    latlon_re = re.search("[0-9]{8} [0-9 \n]+",md_text)
    latlons = md_text[latlon_re.start():latlon_re.end()]
    lat_lon_list = latlons.strip().replace('\n','').split()
    lat_list = [float(x[:4])/100.0 for x in lat_lon_list]
    lon_list = [float(x[4:])/-100.0 for x in lat_lon_list]
    for i,lon in enumerate(lon_list):
        if lon > -50.0:
            lon_list[i] = lon - 100
    print lat_list
    print lon_list
    return MD("%d%04d" % (year,number),
              issue_datetime,
              valid_start,
              valid_end,
              concerning,
              watchLikely,
              summary,
              discussion,
              author,
              attn_list,
              lat_list,
              lon_list)



def compileMDs():
    import cPickle as pickle
    mds = []
    years = range(2004,2013)
    for year in years:
        print year
        md_files = sorted(os.listdir("spc_md_text/%d/" % year))
        for md_file in md_files:
            print md_file
            try:
                md = getMDMetadata(year,int(md_file[:-4].split('_')[1]))
            except AttributeError:
                print 'File Format Error'
                md = None
            if md is not None:
                mds.append(md)
    md_out = open('all_mds.csv','w')
    md_out.write(mds[0].getHeader() + '\n')
    for md in mds:
        md_out.write(md.toCSVRow() + '\n')
    md_out.close()
    md_pickle_file = open('all_mds.pkl','w')
    pickle.dump(mds,md_pickle_file)
    md_pickle_file.close()

def main():
    import sys
    #print getMDText(int(sys.argv[1]),int(sys.argv[2]))
    #getMDYear(int(sys.argv[1]),int(sys.argv[2]))
    print getForecasterAuthorCount(int(sys.argv[1]))
    getMDMetadata(int(sys.argv[1]),int(sys.argv[2]))
if __name__ == "__main__":
    compileMDs()
