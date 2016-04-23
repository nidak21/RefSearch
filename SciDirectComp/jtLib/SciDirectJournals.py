#!/usr/bin/python
import sys
import string

class SciDirectJournal (object):
    '''
    SciDirectJournal class that knows MGI journal names and SciDirect journal
	names.
    Keeps dictionaries of both names to their corresponding SciDirectJournal
	instances.
    Knows how to read in a file of SciDirectJournal records.
    '''
    mgiNameIndex = {}	# dict MGI journal names: SciDirectJournal objects
    sdNameIndex = {}	# dict SciDirect journal names: SciDirectJournal objs
    journals = []	# list of all SciDirectJournal objects in this class

    def __init__(self,
    		 mgiJname,
		 sdJname,
		 prefixMatch=False,	# True => this journal name has variable
		 			#  suffixes in SciDirect, and sdJname
					# is the common prefix to match
		triagedBy=''		# String, if this journal is triaged,
					#  name of curator responsible
	    ):
	self.mgiJname = mgiJname
	self.sdJname  = sdJname
	self.prefixMatch = prefixMatch
	self.triagedBy = triagedBy
	self.__class__.mgiNameIndex[mgiJname] = self
	self.__class__.sdNameIndex[sdJname]  = self
	self.__class__.journals.append(self)
    # end __init__() -----------------------------------------

    def getMgiJname(self):
	return self.mgiJname

    def getSdJname(self):
	return self.sdJname

    def getTriagedBy(self):
	return self.triagedBy

    def isSdJname(self, s	# string
	):
	''' Return True iff s matches SdJname of this SciDirectJournal object.
	    Handles prefix matching for SciDirectJournals that have variable
		suffixes.
	'''
	if s == self.sdJname: return True	# have exact match
	if self.prefixMatch and s.startswith( self.sdJname): return True
	return False
    # end isSdJname() --------------------------

    @classmethod
    def sdName2Journal( cls, sdJname):
	''' Return the SciDirectJournal object whose SciDirect name is 'sdJname'
	    Raise KeyError if there is none.
	'''
	return cls.sdNameIndex[sdJname]

    @classmethod
    def mgiName2Journal( cls, mgiJname):
	''' Return the SciDirectJournal object whose MGI name is 'mgiJname'
	    Raise KeyError if there is none.
	'''
	return cls.mgiNameIndex[mgiJname]

    @classmethod
    def initSciDirectJournals( cls, filename):
	''' Read in the SciDirect Journals from the specified file and create
	    a SciDirectJournal object for each one.
	    Assumes file is tab delimited:
	      MGI_Journal_Name	SciDirect_Journal_Name Prefix_Match TriagedBy
	    w/ header line.
	    Skips lines that start w/ "#"
	    TriagedBy column is optional.
	    Prefix_Match column is 'true' or 'false'.
	    TriagedBy is blank or name of curator who triages the journal.
	    Returns list of SciDirectJournal objects.
	'''
	cls.journals = []

	fp = open( filename, 'r')
	lines = fp.readlines()
	fp.close()

	for line in lines[1:]:		# skip header line
	    if line[0] == "#": 	# skip comment lines
		continue

	    values = map(string.strip, line.split('\t'))
	    if len(values) == 3:	# no triaged by value
		values.append('')	# add null TriagedBy field
	    (mgi_name, sd_name, prefixMatch, triagedBy) = values

	    #print "'%s'	'%s'	'%s' '%s'" % \
	    #	    (mgi_name, sd_name, prefixMatch, triagedBy)
	    pmVal = prefixMatch.lower()=="true"

	    j = SciDirectJournal(mgi_name, sd_name, prefixMatch=pmVal,
							triagedBy=triagedBy)
	return cls.journals

    @classmethod
    def getJournals( cls):
	''' Return list of SciDirectJournals
	'''
	return cls.journals

    @classmethod
    def getTriagedJournals( cls):
	''' Return list of triaged SciDirectJournals
	'''
	triagedJournals = []
	for j in cls.journals:
	    if j.getTriagedBy() != '':
		triagedJournals.append(j)

	return triagedJournals

# end class SciDirectJournal -----------------------

# jim: look up pubTypes - "none" or "editorial" can have no dc:title
if __name__ == "__main__":
    
    SciDirectJournal.initSciDirectJournals( "Data/Journals/MGI_SciDirect_Journals2.txt")
    for j in SciDirectJournal.getJournals():

	print j.getMgiJname() + " ",
	print SciDirectJournal.mgiName2Journal(j.getMgiJname()).getSdJname()
	
    print
    print "Triaged Journals"
    for j in SciDirectJournal.getTriagedJournals():
	print "%s %s" % (j.getMgiJname(), j.getTriagedBy()) 
