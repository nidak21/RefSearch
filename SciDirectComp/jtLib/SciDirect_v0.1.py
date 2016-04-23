#!/usr/bin/python
#
# Module defining class ElsevierSciDirect that knows how to submit queries
#  to the Elsevier SciDirect API and format the results as a list of
#  records (python dictionary where keys are the fieldnames)

import json
import urllib
import urllib2
from jakUtils import *

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
	# Search params ---------------------
	self.qstring = query

	self.baseURL = 'http://api.elsevier.com/content/search/index:SCIDIR'

	# JAX/MGI Elsevier key
	self.apiKey = 'eee0efe83fddcc2ec0cdcbea15717bab'
	
	# tell API we want json back
	self.headers = { 'Accept': 'application/json' }

	self.subscribed = 'true'	# the default
	self.content    = 'journals'	# default

	self.startDate = None	# means no start date
	self.endDate = None	# means no end date
	# End Search params ---------------------

	self.debug = False

	# results from the API search:
	self.totalNumResults = 0
	self.itemsPerPage = 0
	self.startIndex = 0	# index of 1st item on this page full
	self.resultPubs = []	# list of dicts, one for each pub
				#    returned on this page full
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

    # end basic Set methods-------------------------------------------

    def doQuery( self, query=None,	# SciDirect query string
		 startIndex=0,		# index of 1st doc to retrieve (0=first)
		 itemsPerPage=25	# num items to return from this query
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
	data = self.doQuery_json( query=query, startIndex=startIndex, 
			    itemsPerPage=itemsPerPage)

	if type(data) == type('string'): return data

	rslts 		= data['search-results']
	rslts_query	= rslts['opensearch:Query']['@searchTerms']

	self.startIndex = int( rslts['opensearch:startIndex'])
	self.itemsPerPage = int( rslts['opensearch:itemsPerPage'])
	self.totalNumResults = int( rslts['opensearch:totalResults'])

	rslts_list = rslts['entry']
	self.resultPubs = []
	for i in range(self.itemsPerPage):
	    r = rslts_list[i]
	    if self.debug:
		print r
	    rslt = {}
	    rslt['raw']		= r
	    rslt['pubmedId']	= stringIt( r.get( 'pubmed-id', 'none'))
	    rslt['title']	= stringIt( r['dc:title'])
	    rslt['journal']	= stringIt( r['prism:publicationName'])
	    rslt['DOI']		= stringIt( r['dc:identifier'])
	    rslt['elsevierLink']= stringIt( r['link'][0]['@href'])
	    rslt['scidirectLink']= stringIt( r['link'][1]['@href'])
	    rslt['firstAuthor']	= stringIt( r.get('dc:creator', 'none'))
	    rslt['authors']	= stringIt( r.get('authors', 'none'))
	    rslt['startingPage']= stringIt( r.get('prism:startingPage', 'none'))
	    rslt['endingPage']	= stringIt( r.get('prism:endingPage', 'none'))
	    rslt['coverDate']	= stringIt( r['prism:coverDisplayDate'])

	    rslt['volume']	= stringIt( r.get('prism:volume', 'none'))
	    if rslt['volume'] == 'None': rslt['volume'] = 'none'
	    
	    rslt['issue']	= stringIt(
				    r.get( 'prism:issueIdentifier', 'none'))
	    rslt['issueName']	= stringIt( r.get( 'prism:issueName', 'none'))
	    rslt['pubType']	= stringIt( r.get( 'pubType', 'none'))
	    rslt['prismType']	= stringIt( r['prism:aggregationType'])
	
	    self.resultPubs.append(rslt)

	return self.resultPubs
    # end doQuery() -----------------------------------------------

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
	if query == None:
	    query = self.qstring
	else:
	    self.qstring = query	# remember query

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

	# convert all the params to proper URL encoding
	values =  { 
		    'query'	: query,
		    'apikey'	: self.apiKey,
		    'view'	: 'complete',	# get complete ref data
		    'subscribed': self.subscribed,
		    'content'	: self.content,
		    'start'	: startIndex,
		    'count'	: itemsPerPage
		    }
	qparams = urllib.urlencode( values)

	# make the request
	url = self.baseURL + '?' +  qparams 
	if self.debug or True: 		# always print submitted URL for now
	    print 'URL: ' + url
	request = urllib2.Request( url, None, self.headers)
				# 2nd param=None --> GET, not None -->Post
	try:
	    response = urllib2.urlopen( request)
	    #print "Info: ", response.info()
	    #print "URL: ", response.geturl()
	    #print "Code: ", response.code
	    responseText = response.read()
	    response.close()

	except urllib2.URLError as e:
	    if hasattr( e, 'reason'):
		msg = 'We failed to reach the server. Reason: %s' % e.reason
	    elif hasattr(e, 'code'):
		msg = 'The server could not fulfill the request. ' + \
			'Error code: %d' % e.code
	    return msg

	else:	# response with no error
	    return json.loads( responseText)
    # end doQuery_json() -----------------------------------------------

    def getStartIndex(self):
	return self.startIndex

    def getItemsPerPage(self):
	return self.itemsPerPage

    def getTotalNumResults(self):
	return self.totalNumResults

    def getResultPubs(self):
	return self.resultPubs

# end class ElsevierSciDirect -----------------------------

def articleFormat1( pub		# dict, representing a publication rcd
    ):
    ''' Return a string representing the publication 'pub'.
        Assumes pub is a dict of the form returned by doQuery()
    '''
    rslt = []		# list of formatted lines
    rslt.append( "pubType: %s   prismType: %s   pubmedId: %s\n" % \
	(pub['pubType'],
	 pub['prismType'],
	 pub['pubmedId']
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
	exit(0)

    # test out doQuery()
    for j in [0, 5, 10]:	# 3 queries, 5 at a time
	pubs = eq.doQuery( startIndex=j, itemsPerPage=5)
	if type(pubs) == type('string'):	# had error
	    print pubs
	    continue

	# otherwise pubs is a list of resulting publication records
	print 'Total Results: %d' % eq.getTotalNumResults()
	print 'Start Index: %d'   % eq.getStartIndex()
	print 'ItemsPerPage: %d'  % eq.getItemsPerPage()
	print 'Num in page: %d' % len(pubs)

	i = eq.getStartIndex()
	for pub in pubs:
	    print
	    print "%d %s" % (i, articleFormat1( pub) ), 
	    i = i +1
