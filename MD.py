class MD:
    def __init__(self,disc_id,issue_date,valid_start,valid_end,concerning,watchLikely,summary,discussion,author,wfos,lats,lons):
        self.disc_id = disc_id
        self.issue_date = issue_date
        self.valid_start = valid_start
        self.valid_end = valid_end
        self.concerning = concerning
        self.watchLikely = watchLikely
        self.summary = summary
        self.discussion = discussion
        self.author = author
        self.wfos = wfos
        self.lats = lats
        self.lons = lons
        self.header =  ["DiscID","IssueYear","IssueMonth","IssueDay","IssueHour","IssueMinute","IssueDate","ValidStart","ValidEnd","Concerning","WatchLikely","Author","Summary","Discussion","WFOs","Lat","Lon"]

    def getWordFrequencies(self,attribute,numWords=1):
        """getWordFrequencies
           Description:  Given a text attribute, find the how frequently each word or group of words is being used.
           Parameters:  attribute (string) - which attribute to use for word frequency
           numWords - number of words in each substring"""
        import re
        disc_text = getattr(self,attribute)
        split_text = re.split('[() ./,]+',disc_text)
        disc_words = {}
        for w in xrange(len(split_text) - numWords + 1):
            word = ' '.join(split_text[w:w+numWords])
            if word not in disc_words.keys():
                disc_words[word] = 1
            else:
                disc_words[word] += 1
        return disc_words



    def getHeader(self,delimiter=','):
        return delimiter.join(self.header)
   
    def toCSVRow(self,tfmt="%Y%m%d-%H:%M",delimiter=','): 
        rowList = [self.disc_id,
                   self.issue_date.strftime("%Y"),
                   self.issue_date.strftime("%m"),
                   self.issue_date.strftime("%d"),
                   self.issue_date.strftime("%H"),
                   self.issue_date.strftime("%M"),
                   self.issue_date.strftime(tfmt),
                   self.valid_start.strftime(tfmt),
                   self.valid_end.strftime(tfmt),
                   self.concerning,
                   self.watchLikely,
                   self.author,
                   self.summary,self.discussion,
                   " ".join(self.wfos),
                   " ".join(["%03.2f" % x for x in self.lats]),
                   " ".join(["%03.2f" % x for x in self.lons])]
        return delimiter.join(rowList) 
