#!/usr/bin/python
#
# Module defining class ElsevierSciDirect that knows how to submit queries
#  to the Elsevier SciDirect API and format the results as a list of
#  records (python dictionary where keys are the fieldnames)

import json
import urllib
import urllib2
import traceback
from jakUtils import *

# the SciDirect subject classifications we should search
# OMITTING THIS FOR NOW. ADDING REALLY LONG LISTS SEEMS TO CREATE INVALID
#  QUERIES - maybe need to do POST instead of GETs?

#SCI_DIRECT_SUBJECTS = "ageing,anesthpain,animalandzoo,applmicrobiotech,behavneuro,biochem,biochemgenmolbiol,bioeng,bioengineering,biogen,biomatreioals,biophys,biopsychiatry,biotech,cancres,cardiol,catalysis,cellbio,cellmolneurosci,chemistry,chemistrygen,clinicalbio,clinneurol,cognneuro,dermatology,develop,developbio,developneurosci,devendedupsych,drugdiscov,econgen,ecovolut,endocrin,endocrinol,forensicmed,gastroenterology,genetics,geriatricandgeront,hematology,hepatology,hlthtoximuta,humcomp,humfactors,immumicrobiogen,immunallergol,immunolmicrobiol,immunology,infectious,inorganicchem,meddentgen,medicinedentistry,microbiology,molecbio,molmed,nephrology,neurology,neuroscience,neuroscigen,neurosciphypsych,nutrition,obstetgyn,occuptherapy,oncology,ophthalmology,optics,optometry,organicchem,orgbehaviorandhr,orthoped,otorhino,parasitology,pathol,perinatol,pharamacology,pharmasci,pharmatox,pharmgen,physgen,physiology,phystherapy,podiatry,psychiatry,psycholgen,psychology,pulmin,radiation,radiography,sensosys,signalproc,socpsychol,socscigen,structbiol,surgery,toxicology,transplantation,urology,virology"

#SCI_DIRECT_SUBJECTS = "behavneuro,biochem,genetics"

class ElsevierSciDirect:
    '''Is a class that handles Elsevier Science Direct queries via their API.
       You can specify various query parameters. This class is responsible
       for packaging them up into the appropriate URL and parsing the
       results of the query.

       API documentation:
       http://api.elsevier.com/documentation/SCIDIRSearchAPI.wadl#simple

       doQuery() is the main method for performing a query.

       Parameters and attributes of this class:
       	query	- query string, mostly this specifies boolean expr of words
		  to search for in the publication text.
		  Can be specified on constructor, setQuery(), and doQuery()
	  Query syntax documentation:
	  http://api.elsevier.com/content/search/fields/scidir
	  http://api.elsevier.com/documentation/search/SCIDIRSearchTips.htm

	startDate - 'yyyymmdd', the earliest date to match publications from
	endDate   - 'yyyymmdd', latest date to match publications from
	subscribed - 'true' (default) or 'false' (note these are strings)
			'true' means only search our subscribed journals
			'false' means search all SciDirect
	content	   - 'all', 'serial', 'nonserial', 'journals' (default), or
			'allbooks'
	startIndex - param to doQuery() - the zero-based index of the first
			 item to return.  default = 0
	itemsPerPage - param to doQuery() - number of items to return from 
			the query.  default = 25
    '''
    def __init__( self,
	      query=''		# SciDirect query string
	):
	self.debug = False

	# API details... ----------------------
	self.baseURL = 'http://api.elsevier.com/content/search/index:SCIDIR'
	# JAX/MGI Elsevier key
	self.apiKey = 'eee0efe83fddcc2ec0cdcbea15717bab'
	# tell API we want json back
	self.headers = { 'Accept': 'application/json' }

	# Search param defaults ---------------------
	self.qstring	= query		# default query string
	self.subscribed = 'true'	# the default
	self.content    = 'journals'	# default
	#self.subj	= SCI_DIRECT_SUBJECTS # default
	self.subj	= "neuroscigen,genetics" # default

	self.startDate	= None		# means no start date
	self.endDate	= None		# means no end date
	self.defaultPubsPerPage = 200	# num of pubs to get per API call
	# End Search params ---------------------

	# results from the most recent call to doQuery()
	self.mrQuery	= ''	# most recent query
	self.results	= []	# list of dicts, one for each pub
	self.numResults	= 0
	self.apiTrace	= []	# list of strings, with the URLs called
				
    # end __init__() -------------------------------------------

    def setDebug( self,
    		  debug		# boolean
	):
	self.debug = debug

    def setQuery( self,
    		  query		# SciDirect query string
		):
	self.qstring = query

    def setStartDate( self,
    		  dateString	# string like 'yyyymmdd'
		):
	self.startDate = dateString

    def setEndDate( self,
    		  dateString	# string like 'yyyymmdd'
		):
	self.endDate = dateString

    def setContent( self,
    		  s	# string, 'all', 'serial', 'nonserial', 'journals'
		  	#    'allbooks'
		):
	self.content = s

    def setSubscribed( self,
    		  subscribed	# string, 'true' or 'false'
		):
	''' subscribed='true' (default) to search only MGI subscribed journals
	               'false' to search all SciDirect journals
	'''
	self.subscribed = subscribed

    def setSubjects( self,
    		  s	# string, comma separated (no spaces) list of SciDirect
		  	#    subject keywords
		):
	self.subj = s

    def setDefaultPubsPerPage( self,
		  n	# int
		):
	self.defaultPubsPerPage = n

    # end basic Set methods-------------------------------------------

    def doCount( self,
		query=None	# query string, use default query if None
	):
	''' Return the number (int) of pubs at SciDirect that match the query.
	    Return a string (error msg) if we had an error connecting to
		SciDirect.
	'''
	self.apiTrace = []	# clear the trace
	self.results = []	# clear the result list
	self.numResults = 0

	if query == None: query = self.qstring	# use default

	self.mrQuery = query	# remember query string

	# do query with only 1 result to get actual num of results
	# This sets self.totalNumResults
	data = self.doQuery_onepage( query, startIndex=0, itemsPerPage=1 )
	if type(data) == type('string'):    # had error
	    return data

	else: return self.totalNumResults
    # end doCount() -----------------------------------------

    def doQuery( self,
		query=None,	# query string, use default query if None
		starti=0,	# index of 1st doc to retrieve (0=first)
		maxrslts=25	# max number of results to return
	):
	''' Submit the query and package up the results
	    Return: list of resulting publications (list of dictionaries)
			matching the query
	    	    OR a string (error msg) if we had an error connecting to
			SciDirect.
	    This function knows how to build up a result set by iterative
	    queries to the SciDirect API to return the list of matching 
	    publications.
	'''
	self.apiTrace	= []	# clear the trace
	self.results	= []	# clear the result list
	self.numResults	= 0

	if query == None: query = self.qstring	# use default
	self.mrQuery = query	# remember query string

	# do query with only 1 result to get actual num of results
	# This sets self.totalNumResults
	data = self.doQuery_onepage( query, startIndex=0, itemsPerPage=1 )
	if type(data) == type('string'):    # had error
	    return data

	# get all the pubs
	totalnum = self.totalNumResults
	numToGet = min(maxrslts, totalnum - starti) # total number to return
	maxPubsPerPage = self.defaultPubsPerPage

	while len(self.results) < numToGet:
	    numThisPage = min(numToGet - len(self.results), maxPubsPerPage)
	    data = self.doQuery_onepage( query=query, startIndex=starti,
					    itemsPerPage=numThisPage )
	    if type(data) == type('string'):        # had error
		return data

	    self.numResults += numThisPage
	    self.results.extend(data)
	    starti = starti + len(data)

	return self.results

    # end doQuery() -----------------------------------------------

    def doQuery_onepage( self, query=None,	# SciDirect query string
		 startIndex=0,		# index of 1st doc to retrieve (0=first)
		 itemsPerPage=None	# num items to return from this query
		 			# use default if None
	):
	''' Submit the query and package up the results
	    Return: list of resulting publications (list of dictionaries)
	    	   or a string (error msg) if we had an error connecting to
		   SciDirect.
	    So this function knows how to do one "pageful" query by calling
	    doQuery_json() and then package up the returned article records
	    into a python record structure. I.e., knows the json structure from
	    SciDirect.
	'''
	if itemsPerPage == None:	# use default
	    itemsPerPage = self.defaultPubsPerPage

	try:
	    data = self.doQuery_json( query=query, startIndex=startIndex, 
				itemsPerPage=itemsPerPage)
	    if type(data) == type('string'): return data	# had error

	    rslts 		= data['search-results']

				    # remember total number of rslts @ SciDirect
	    if rslts['opensearch:totalResults'] == None: # sometimes comes back
	    					         # None, sometimes 0
		self.totalNumResults = 0
	    else:
		self.totalNumResults = int( rslts['opensearch:totalResults'] )

				    # get num results returned this pageful
				    # sometimes itemsPerPage is 1 when
				    #  totNumresults is 0 or None - go figure.
	    itemsRetrieved = min( self.totalNumResults, \
	    			  int( rslts['opensearch:itemsPerPage'] ) )

	    rslts_list = rslts['entry']
	    resultPubs = []

	    for i in range(itemsRetrieved):
		r = rslts_list[i]
		if self.debug and False:	# don't print this for now
		    print r
		rslt = {}
		rslt['raw']		= r
		rslt['pubmed']	= stringIt( r.get( 'pubmed-id', 'none'))
		rslt['title']	= stringIt( r.get('dc:title', 'none') )
		rslt['journal']	= stringIt( r['prism:publicationName'])

		# get DOI id, remove leading "DOI:" if it is there
		doiString		= stringIt( r['dc:identifier'])
		if doiString[0:4] == "DOI:": rslt['DOI'] = doiString[4:]
		else: rslt['DOI'] = doiString

		rslt['elsevierLink']= stringIt( r['link'][0]['@href'])
		rslt['scidirectLink']= stringIt( r['link'][1]['@href'])
		rslt['firstAuthor']	= stringIt( r.get('dc:creator', 'none'))
		rslt['authors']	= stringIt( r.get('authors', 'none'))
		rslt['startingPage']= stringIt(r.get('prism:startingPage','none'))
		rslt['endingPage']	= stringIt( r.get('prism:endingPage', 'none'))
		rslt['coverDate']	= stringIt( r['prism:coverDisplayDate'])

		rslt['volume']	= stringIt( r.get('prism:volume', 'none'))
		if rslt['volume'] == 'None': rslt['volume'] = 'none'
		
		rslt['issue']	= stringIt(
					r.get( 'prism:issueIdentifier', 'none'))
		rslt['issueName']	= stringIt( r.get( 'prism:issueName', 'none'))
		rslt['pubType']	= stringIt( r.get( 'pubType', 'none'))
		rslt['prismType']	= stringIt( r['prism:aggregationType'])
		rslt['abstract']	= stringIt( r.get( 'dc:description', 'none'))
	    
		resultPubs.append(rslt)
	except Exception, e:
	    traceback.print_exc()	# print stacktrace of e

	    # print JSON
	    print 'Current json from SciDirect:'
	    print self.currentResponseText

	    raise e			# re-raise e to end the program.

	return resultPubs
    # end doQuery_onepage() -----------------------------------------------

    def doQuery_json( self, query=None,	# SciDirect query string
		 startIndex=0,		# index of 1st doc to retrieve (0=first)
		 itemsPerPage=25	# num items to return from this query
	):
	''' Process parameters, do API query and return json result
	    Return: Json result (dictionary)
	    	    or a string (error msg) if we had trouble connecting.
	    So this function knows how to package up the query parameters,
	    dates, startIndex, itemsPerPage, etc. for the API call & get the
	    json results back.
	'''
	self.currentResponseText = ''	# in case an exception happens
					#   as we are constructing query

	if query == None: query = self.qstring	# use default

	# add start and end date parameters to the query string
	if self.startDate != None:
	    newQ = 'Pub-Date AFT ' + self.startDate
	    if query == '':
		query = newQ
	    else:
		query = newQ + ' AND ' + query
	if self.endDate != None:
	    newQ = 'Pub-Date BEF ' + self.endDate
	    if query == '':
		query = newQ
	    else:
		query = newQ + ' AND ' + query

	query = string.join(query.split('\n'), " ")	# get rid of '\n's
	# convert all the params to proper URL encoding
	values =  { 
		    'query'	: query,
		    'apikey'	: self.apiKey,
		    'view'	: 'complete',	# get complete ref data
		    				# includes abstract
		    'subscribed': self.subscribed,
		    'content'	: self.content,
		    #'subj'	: self.subj,
		    'start'	: startIndex,
		    'count'	: itemsPerPage
		    }
	qparams = urllib.urlencode( values)

	# make the request
	url = self.baseURL + '?' +  qparams 

	self.apiTrace.append( url)

	if self.debug:
	    print 'URL: ' + url
	request = urllib2.Request( url, None, self.headers)
				# 2nd param=None --> GET, not None -->Post
	try:
	    response = urllib2.urlopen( request)
	    #print "Info: ", response.info()
	    #print "URL: ", response.geturl()
	    #print "Code: ", response.code
	    responseText = response.read()
	    self.currentResponseText = responseText	# save so we can report
						    #  on exception in caller
	    #print "responseText: '%s'" % responseText
	    response.close()

	except urllib2.URLError as e:
	    if hasattr( e, 'reason'):
		msg = 'We failed to reach the server. Reason: %s' % e.reason
	    elif hasattr(e, 'code'):
		msg = 'The server could not fulfill the request. ' + \
			'Error code: %d\nRequest: %s' % (e.code, request)
	    return msg

	else:	# response with no error
	    return json.loads( responseText)
    # end doQuery_json() -----------------------------------------------

    # get info about the most recent call to doQuery()-----------
    def getApiTrace(self):
	''' Return list URL calls to the API. Last item is the most recent call
	'''
	return self.apiTrace

    def getMrQuery(self):	# most recent query string
	return self.mrQuery

    def getTotalNumResults(self):	# total num of results at SciDirect
	return self.totalNumResults

    def getSubjects(self):
	return self.subj

    def getNumRetrieved(self):
	return self.numResults

    def getResults(self):
	return self.results

# end class ElsevierSciDirect -----------------------------

def articleFormat1( pub		# dict, representing a publication rcd
    ):
    ''' Return a string representing the publication 'pub'.
        Assumes pub is a dict of the form returned by doQuery()
    '''
    rslt = []		# list of formatted lines
    rslt.append( "pubType: %s   prismType: %s   pubmed: %s\n" % \
	(pub['pubType'],
	 pub['prismType'],
	 pub['pubmed']
	 ) )
    rslt.append( "%s\n" % pub['title'])
    rslt.append( "(%s) %s\n" % (pub['firstAuthor'], pub['authors']) )
    rslt.append( "%s volume %s(%s/%s):%s-%s %s\n" % \
	(pub['journal'],
	 pub['volume'],
	 pub['issue'],
	 pub['issueName'],
	 pub['startingPage'],
	 pub['endingPage'],
	 pub['coverDate']
	 ) )
    rslt.append( "DOI: %s\n" % pub['DOI'])
    return string.join(rslt, '')
# end articleFormat1() -----------------------------

if __name__ == '__main__':

    # tests....
    eq = ElsevierSciDirect(
	    query='''ALL(mouse OR mice OR murine)
			AND srctitle("curr* biol*")
		  '''
			# to get journal name w/ a phrase match
			#AND srctitle("developmental cell")
		)
    eq.setStartDate('20121231')
    eq.setEndDate('20140101')

    if False:		# change to true to test the json structure
	eq.setDebug(True)
	data = eq.doQuery_json( startIndex=0, itemsPerPage=10)
	if type(data) == type('string'):	# had error
	    print data
	else:
	    print
	    print data.keys()
	    jsonCurse(data)
	    print "API Trace"
	    print eq.getApiTrace()
	exit(0)

    # test out doQuery_onepage()
    for j in [0, 5, 10]:	# 3 queries, 5 at a time
	pubs = eq.doQuery_onepage( startIndex=j, itemsPerPage=5)
	if type(pubs) == type('string'):	# had error
	    print pubs
	    continue

	# otherwise pubs is a list of resulting publication records
	print 'Total Results: %d' % eq.getTotalNumResults()
	print 'Num in page: %d' % len(pubs)

	i = j
	for pub in pubs:
	    print
	    print "%d %s" % (i, articleFormat1( pub) ), 
	    i = i +1

    # test out doCount()
    num = eq.doCount()
    print
    print "Testing doCount()"
    print "Total Results: %d" % num
    print eq.getApiTrace()
    print

    # test out doQuery()
    eq.setDefaultPubsPerPage(2)

    pubs = eq.doQuery(maxrslts=5)
    print
    print 'Total Results: %d' % eq.getTotalNumResults()
    print 'Num Retrieved: %d' % eq.getNumRetrieved()

    i = 0
    for pub in pubs:
	print
	print "%d %s" % (i, articleFormat1( pub) ), 
	i = i +1
    print eq.getApiTrace()

