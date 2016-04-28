#!/usr/bin/python
#
# Module defining class SciDirectConnection that knows how to submit queries
#  to the Elsevier SciDirect API and format the results as a list of
#  records (python dictionary where keys are the fieldnames)

import sys,string
import json
import urllib
import urllib2
import traceback

class SciDirectConnection:
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
	self.debugWriter = None	# function/method to write debug msgs to
				#  None means no debug messages

	# API details... ----------------------
	self.baseURL = 'http://api.elsevier.com/content/search/index:SCIDIR'
	# JAX/MGI Elsevier key
	self.apiKey = 'eee0efe83fddcc2ec0cdcbea15717bab'

	# Search param defaults ---------------------
	self.qstring	= query		# default query string
	self.subscribed = 'true'	# only search journals we subscribe to
	self.content    = 'journals'	# only search journals
	self.subjects	= '22,18'	# 22=biochem,genetics & molecular bio
					# 18=neuroscience
      #see: http://api.elsevier.com/content/subject/scidir?httpAccept=text/xml

	self.bufferSize = 1000		# max num of pubs to get per API call
					#  so we don't tax their server
	# End Search params ---------------------

    # end __init__() -------------------------------------------

    def setQuery( self, query		# SciDirect query string
		):
	self.qstring = query

    def setContent( self, s  # string, 'all', 'serial', 'nonserial', 'journals'
		  	     #    'allbooks'
		):
	self.content = s

    def setSubscribed( self, subscribed	# string, 'true' or 'false'
		):
	''' subscribed='true' (default) to search only MGI subscribed journals
	               'false' to search all SciDirect journals
	'''
	self.subscribed = subscribed

    def setSubjects( self, s  # string, comma separated (no spaces) list of
		  	      #     SciDirect subject codes
		):
	self.subjects = s

    def setBufferSize( self, n	# int
		):
	self.bufferSize = n

    def setDebugWriter( self, writer	# function to write debug msgs too
	):
	self.debugWriter = writer

    # end basic Set methods-------------------------------------------

    def debug( self,
    		msg	# string or [ strings ]
	):
	''' Write a debug msg if we have a writer to write to
	'''
	if self.debugWriter != None:
	    if type(msg) == type( ['list'] ):
		msg = string.join(msg,'\n') + '\n'
	    self.debugWriter(msg)
    # end debug() -------------------------------------

    def addDatesToQuery( self,
	    query,
	    startDate = None,	# yyyymmdd format
	    endDate = None	# yyyymmdd format
	):
	''' Convenience function for adding date formats to a query string.
	    Take a query string and add boolean code for startDate
	    and endDate, if they are set.
	    Return the modified query string.
	    If startDate and endDate are None, the query is not changed.
	'''
	if startDate != None:
	    newQ = 'Pub-Date AFT ' + startDate
	    if query == '' or query == None:
		query = newQ
	    else:
		query = newQ + ' AND ' + query
	if endDate != None:
	    newQ = 'Pub-Date BEF ' + endDate
	    if query == '' or query == None:
		query = newQ
	    else:
		query = newQ + ' AND ' + query
	return query
    # end addDatesToQuery() -----------------------------------------------

    def doCount( self,
		query=None	# query string, use default query if None
	):
	''' Return the number (int) of pubs at SciDirect that match the query.
	'''

	if query == None: query = self.qstring

	# query for 1 result, json includes total of all matching results
	(num, results) = self.unpackJson( self.hitExternalAPI( query, 1, 0) )

	return num
    # end doCount() -----------------------------------------

    def doQuery( self,
		query=None,	# query string, use default query if None
		numToGet=25,	# (max) num items to return from this query
		startIndex=0	# index of 1st doc to retrieve (0=first)
	):
	''' Submit the query and package up the results
	    Return: list of resulting publications (list of dictionaries)
			matching the query
	    This function knows how to build up a result set by iterative
	    queries to the SciDirect API to return the list of matching 
	    publications.
	'''
	if query == None: query = self.qstring	# use default

	# do query with only 1 result to get actual num of matching results
	(totalNumResults,results) = \
			    self.unpackJson( self.hitExternalAPI(query, 1, 0 ) )

	# set toGet to the exact number of results we want on this query
	toGet = min(numToGet,totalNumResults-startIndex)

	results = []
	while len(results) < toGet:
	    numThisPage = min(toGet - len(results), self.bufferSize)

	    self.debug("numThisPage = %d     startIndex = %d\n" % \
						(numThisPage, startIndex))
	    (tot, newr) = self.unpackJson( \
			self.hitExternalAPI(query, numThisPage, startIndex) )

	    results.extend(newr)
	    startIndex = startIndex + len(newr)

	return results

    # end doQuery() -----------------------------------------------

    def doQuery_Json( self,
		query=None,	# query string, use default query if None
		numToGet=5,	# (max) num items to return from this query
		startIndex=0, # index of 1st doc to retrieve (0=first)
	):
	''' Perform the query and return the SciDirect Json for the first
	    buffer-full of results. 
	    So the number of results returned is the
	    min(numToGet,self.bufferSize,number of matching results @ SciDirect)
	'''

	if query == None: query = self.qstring

	numToGet = min(numToGet, self.bufferSize)

	return self.hitExternalAPI( query, numToGet, startIndex)

    # end doQuery_Json() -----------------------------------------

    def unpackJson( self, jsonObj
		):
	""" Unpack a SciDirect json result object.
	    Return a 2-tuple: (x, y)
		1) the total number of SciDirect results matching the query
		2) list of the returned records (each rcd = python dict)
	    Note the total number of results may be different from the length
	        of the record list as the query may have specified a max to
		return.
	    See unpackOneReult() for the fields of a record in the list.
	"""
	try:
	    # get total number of rslts @ SciDirect
	    totalNumFromJson = \
			    jsonObj['search-results']['opensearch:totalResults']

	    totalNumResults = 0	# sometimes 0 comes back as None - go figure
	    if totalNumFromJson != None:
		totalNumResults = int(totalNumFromJson)

	    resultPubs = []  # result list

	    if int(jsonObj['search-results']['opensearch:itemsPerPage']) > 0:
					    # have some results (articles)

		# loop through results, creating record structures
		for r in jsonObj['search-results']['entry']:
		    resultPubs.append( self.unpackOneResult(r) )

	except Exception, e: # this is primarily to debug pulling data
			     # out of the json string.
	    print 
	    print 'Exception unpacking Json'
	    traceback.print_exc(None,sys.stdout)# print stacktrace of e

	    # print JSON
	    print 'Current json from SciDirect:'
	    print json.dumps( jsonObj, sort_keys=False, indent=4,
						separators=(',',': ') )
	    raise e			# re-raise e to end the program.

	return (totalNumResults, resultPubs)
    # end unpackJson() -----------------------------------------------

    def unpackOneResult( self, r  # Json object for one result (article)
		):
	""" Unpack one SciDirect json result object (for one article)
	    Return a python record (dictionary) for the result.
	    See below for the fields of each record returned in the list.
	"""
	def stringIt(u	# string or Unicode to return as string
	    ):
	    '''Local helper function:  Return 'u' as a string.
	       If it's Unicode, convert it to ascii encoded string
	    '''
	    encoding='ascii'
	    if type(u) == type(u'x'):
		thestring = u.encode( encoding, errors='backslashreplace' )
	    else: thestring = str(u)

	    if thestring == "None": thestring = "none"

	    return thestring
	# end strintIt() ---------------------
	
	rslt = {}	# new result record

	rslt['abstract'] = stringIt( r.get( 'dc:description', 'none'))
	rslt['authors']  = stringIt( r.get('authors', 'none'))
				    # authors are still a json string
				    # would take some work to unpack

	rslt['coverDate']= stringIt( r['prism:coverDisplayDate'])

	# get DOI id, remove leading "DOI:" if it is there
	doiString  = stringIt( r['dc:identifier'])
	if doiString[0:4] == "DOI:": rslt['DOI'] = doiString[4:]
	else: rslt['DOI'] = doiString

	rslt['elsevierLink'] = stringIt( r['link'][0]['@href'])
	rslt['endingPage']   = stringIt( r.get('prism:endingPage', 'none'))
	rslt['firstAuthor']  = stringIt( r.get('dc:creator', 'none'))
	rslt['issue']	     = stringIt( r.get('prism:issueIdentifier','none'))
	rslt['issueName']    = stringIt( r.get('prism:issueName','none'))
	rslt['journal']	     = stringIt( r['prism:publicationName'])
	rslt['prismType']    = stringIt( r['prism:aggregationType'])
	rslt['pubmed']	     = stringIt( r.get('pubmed-id', 'none'))
	rslt['pubType']	     = stringIt( r.get( 'pubType', 'none'))
	#rslt['raw']	     = r # raw json
	rslt['scidirectLink']= stringIt( r['link'][1]['@href'])
	rslt['startingPage'] = stringIt( r.get('prism:startingPage','none'))
	rslt['title']	     = stringIt( r.get('dc:title', 'none') )
	rslt['volume']       = stringIt( r.get('prism:volume', 'none'))
    
	return rslt
    # end unpackOneResult() -----------------------------------------------

    def hitExternalAPI( self,
		    query,	# SciDirect query string
		    numToGet,	# (max) num items to return from this query
		    startIndex=0, # index of 1st doc to retrieve (0=first)
	):
	''' Do one API query and return json result.
	    Number of results returned will be
		min(numToGet,number of matching results @ SciDirect)
	    Return: Json result (dictionary)
	    Exceptions ???
	    Low level routine, not intended to be called outside this class.

	    NOTE:  if startIndex > the totalnumber of matching results,
	           you seem to get a 404 ERROR FROM SCIDIRECT.
	'''
	# convert all the params to proper URL encoding
	query = string.join(query.split('\n'), " ")	# get rid of '\n's

	values =  { 
		    'query'	: query,
		    'apikey'	: self.apiKey,
		    'view'	: 'complete',	# get complete ref data
		    				# includes abstract

		    'suppressNavLinks' : 'true', # omit repetitious URLs
		    				 # in response

		    'subscribed': self.subscribed,
		    'content'	: self.content,  # journals, serials, allbooks..

		    'subj'	: self.subjects, # Not sure what is seached
		    				 # if we don't pass this.
						 # It does something,
						 # but doesn't seem to search
						 #  all subjects.
		    'start'	: startIndex,
		    'count'	: numToGet
		    }
	qparams = urllib.urlencode( values)
	url = self.baseURL + '?' +  qparams 
	#self.debug("API request: %s\n" % url)

	# make the request
	header = { 'Accept' : 'application/json' } # tell API we want json
	request = urllib2.Request( url, None, header)
				# 2nd param=None --> GET, not None -->Post
				# SciDirect does not seem to support Post (?)

	try: # NOT sure we should catch these exceptions of just pass them on
	    response = urllib2.urlopen( request)

	    #self.debug( "Info: %s\n" % str( response.info() ) )
	    #self.debug( "URL: %s\n"  % response.geturl() )
	    #self.debug( "Code: %s\n" % str( response.code ) )

	    responseText = response.read()
	    #self.debug( "responseText: '%s'\n" % responseText )
	    response.close()

	except urllib2.URLError as e:
	    if hasattr( e, 'reason'):
		msg = 'We failed to reach the server. Reason: %s' % e.reason
	    elif hasattr( e, 'code'):
		msg = 'The server could not fulfill the request. ' + \
			'Error code: %d\nRequest: %s' % (e.code, request)
	    raise

	return json.loads(responseText)
    # end hitExternalAPI() -----------------------------------------------

# end class SciDirectConnection -----------------------------

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
    #rslt.append( "(%s) %s\n" % (pub['firstAuthor'], pub['authors']) )
    rslt.append( "(%s)\n" % (pub['firstAuthor']) )
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
    eq = SciDirectConnection()
    if False:			 # test debug routine
	eq.debug("this should print nothing\n")
	eq.setDebugWriter( sys.stdout.write )
	eq.debug("This should go to stdout\n")
	eq.debug([ "these lines", "should also", "go to stdout" ])

	exit(0)

    if False:			 # test hitExternalAPI
	eq.setDebugWriter( sys.stdout.write )
	print json.dumps( eq.hitExternalAPI("ALL(mouse)", 5, 0),
			    sort_keys=False,
			    indent=4, separators=(',',': ') )

	exit(0)

    if False:			 # test unpackJson
	eq.setDebugWriter( sys.stdout.write )
	(num, rslts) =  eq.unpackJson( eq.hitExternalAPI("ALL(mouse)", 3, 0) )
	print
	print "Query one: totalNumResults = %d" % num
	for r in rslts:
	    print articleFormat1(r)
	    print
	(num,rslts) = eq.unpackJson(eq.hitExternalAPI('ALL("snoodle")',1,0))
	print
	print "Query two: totalNumResults = %d (should be 0)" % num
	for r in rslts:
	    print articleFormat1(r)
	    print

	exit(0)

    if False:			 # test doCount
	print
	#eq.setDebugWriter( None )
	eq.setDebugWriter( sys.stdout.write )
	#num = eq.doCount( "All(mouse)" )
	num = eq.doCount( 'ALL(football AND turkey)' )
	print "totalNumResults = %d (should be around 67)" % num
	num = eq.doCount( 'ALL("fot print")' )
	print "totalNumResults = %d (should be 0)" % num
	exit(0)

    if False:			 # test doQuery_Json
	eq.setDebugWriter( None )
	print "First query: (should have 2 results)"
	print json.dumps( eq.doQuery_Json("ALL(football AND turkey)",2, 0),
			    sort_keys=False,
			    indent=4, separators=(',',': ') )
	print "\nSecond Query: (should have 0 results)"
	print json.dumps( eq.doQuery_Json("ALL(snoodle)",5, 0),
			    sort_keys=False,
			    indent=4, separators=(',',': ') )
	exit(0)

    if True:			 # test doQuery
	eq.setDebugWriter( sys.stdout.write )
	rslts = eq.doQuery("ALL(football AND turkey)", 2, 0)
	print "First query: %d results  (should have 2 results)" % len(rslts)
	for r in rslts:
	    print articleFormat1(r)
	    print
	rslts = eq.doQuery("ALL(football AND turkey)", 100, 63)
	print "Second query: %d results  (should have 1 results)" % len(rslts)
	for r in rslts:
	    print articleFormat1(r)
	    print
	eq.setBufferSize(2)
	rslts = eq.doQuery("ALL(football AND turkey)", 7, 0)
	print "Third query: %d results  (should have 7 results)" % len(rslts)
	for r in rslts:
	    print articleFormat1(r)
	    print
	exit(0)

    query='''ALL(mouse OR mice OR murine)
		AND srctitle("curr* biol*")
	  '''
		# to get journal name w/ a phrase match
		#AND srctitle("developmental cell")

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

