
import sys
import string

from tabledatasetlib import *

class TriageCategory (object): #[
    ''' Represents a triage category  (A, G, T, E)
	including "None" - a special category
	Each category has (all strings)
	    a query for SciDirect
	    a letter code associated with MGI references
	    various flavors of names
    '''
    def __init__(self,
    		 name,
		 displayName,
		 mgiCode,	# must match the column heading in MGI refs
		 		#  tsv file.
				# For category "None" leave this ''
		 sdQueryString	# SciDirect query strings for this category
		):
	self.name = name
	self.displayName = displayName
	self.mgiCode = mgiCode
	self.sdQueryString = sdQueryString

    def getName(self):
	return self.name

    def getDisplayName(self):
	return self.displayName

    def getMgiCode(self):
	return self.mgiCode

    def getSdQueryString(self):
	return self.sdQueryString
# end class TriageCategory -------------------------- ]

class MgiRefs (object): #[
    '''
    an MgiRefs object represents a collection of references (articles) in MGI.
    Encapsulates the TableDataSet holding the MGI references.

    Customizes the TableDataSet for the needs of this program:
	populates field: startingPage
    '''
    def __init__(self, filename):
	print "Reading MGI references from %s ..." % filename
	sys.stdout.flush()
	self.mgiDs = TextFileTableDataSet( "MGI References",
		    filename,
		    readNow=0)
	self._initRefDataSet()
	print "done"
	sys.stdout.flush()
    # end __init__() ----------------------------

    def _initRefDataSet(self):
	''' read in the TableDataSet, set up indexes, etc.
	'''
	self.mgiDs.addIndexes( ["DOI", "pubmed", "journal"])
	self.mgiDs.readRecords()

	# JIM: eventually remove or mark MGI references to skip over so we
	#  can omit refs that MGI says are in a given year, but SciDirect
	#  has for a different year.

	# JIM: probably could delete this as we are not using these fields now
	# break 'pgs' up into startingPage and index by startingPage
	self.mgiDs.addField( 'startingPage', None)
	self.mgiDs.addIndexes( 'startingPage')
	self.mgiDs.addField( 'endingPage', None)

	for r in self.mgiDs.getRecords():
	    pgs = r['pgs'].strip()
	    pages = pgs.split('-')	# MGI's pgs fmt is like "87-94"
	    sp = pages[0]
	    if len(pages) == 2:
		ep = pages[1]
	    else:
		ep = ""
	    self.mgiDs.updateFields( r['_rcdkey'], 'startingPage', sp)
	    self.mgiDs.updateFields( r['_rcdkey'], 'endingPage', ep)

    # end _initRefDataSet() ---------------------------

    def getMgiRefsByJournal(self,
    		   j		# Journal, the Journal to get list of pubs from
		   ):
	''' Return the list of MGI refs from Journal j
	'''
	return self.mgiDs.getRecordsByIndex( 'journal', j.getMgiJname() )
    # end getMgiRefsByJournal() -----------------------------

    def matchRefById(self,
		    f,	# string, name of a field, typically "DOI" or "pubmed"
		    s	# string, the value of the ID to check
		  ):
	''' Return MGI reference record matching ID field f == s.
	    (if s == "None" or None, we don't count it as a match)
	    Return None if no match.
	    Throw exception if s matches more than one rcd (shouldn't happen)
	'''
	if s == "none" or s == None: return None

	rcds = self.mgiDs.getRecordsByIndex( f, s)
	if len(rcds) == 0:
	    return None
	if len(rcds) == 1:
	    return rcds[0]
	else:
	    raise JournalCompError(  \
		'%s: "%s" matches more than one MGI ref\n' % (f, s))
    # end matchRefById() ----------------------

    def matchRefByJVP(self,
		    j, 		# Journal
		    v,		# string, representing a volume
		    sp,		# string, representing starting Page number
		    ep		# string, representing ending Page number
		    ):
	''' Return MGI reference record matching Journal j, volume v, and
		startingPage p
	    (if any of j, v, p are None or "None", we don't count as a match)
	    Return None if no match.
	    Throw exception if j v p matches more than one rcd
	    (because it seems like this shouldn't happen. An alternative would
	     be to just return None)
	    JIM: no longer used
	'''
	if j == None: return None
	if v == None or v == "none": return None
	if p == None or p == "none": return None

	matchingRef = None
	jname = j.getMgiJname()
				# iterating over startingPage values seems
				#  more efficient than by journal or volume
	for mgiRef in self.mgiDs.getRecordsByIndex( 'startingPage', sp):
	    if mgiRef['journal'] == jname and mgiRef['vol'] == v \
	    	and mgiRef['endingPage'] == ep:
		if matchingRef == None:		# have a 1st match
		    matchingRef = mgiRef
		else:				# have a 2nd match
		    raise JournalCompError(  \
			'%s vol:%s page:%s matches more than one MGI ref\n' \
			% (jname, v, p))

	return matchingRef

    # end matchRefByJVP() ----------------------

    def refInTriageCategory(self,
		    ref,	# reference record
		    tc		# TriageCategory object
	):
	''' 
	Return True if the ref is in the specified TriageCategory
	'''
	field = tc.getMgiCode()
	if field == '':		# must be the "None" tc
	    return True		# always match. Sort of means ignore tc.
	else:
	    return ref[field] == 'true'

# end class MgiRefs --------------------- ]

