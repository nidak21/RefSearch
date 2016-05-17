#!/usr/bin/python
#
# Module defining class RefQuery that encapsulates all the information
# about a reference query:
#	the query criteria
#	methods to get the results and page thru them, etc.

import sys,string
#import json
#import urllib
#import urllib2
#import traceback
import SciDirect

class RefQuery:
    '''Is a class that ...
    '''
    def __init__( self,
	      connection,	# (open) API connection obj to use
	      			#   should support doQuery()
	      debugWriter=None,	# function/method to write debug msgs to
				#  None means no debug messages
	      query='',		# query string
	      journals=[],	# the names of selected journals to search
	      			#  if None or [], search all
	      perPage=50,	# max number of results to return at a time
	      startIndex=0	# index of first result to return (0 based)
	):
	self.connection = connection
	self.debugWriter = debugWriter	
	self.query = query
	self.journals = journals
	self.perPage = perPage
	self.startIndex = startIndex
	self.totalNumResults = None	# total num of results in most recent
					#   query

    # end __init__() -------------------------------------------

    def setQuery( self, query		# SciDirect query string
		):
	self.query = query

    def getQuery( self):
	return self.query

    def setJournals( self, j  # list of journal names (strings) to search
		):
	self.journals = j

    def getJournals( self):
	return self.journals

    def setPerPage( self, perPage
		):
	self.perPage = perPage

    def getPerPage( self):
	return self.perPage

    def setStartIndex( self, i  # int, zero-based.
		):
	self.startIndex = i

    def getStartIndex( self):
	return self.startIndex

    def setDebugWriter( self, writer
	):
	self.debugWriter = writer

    def getTotalNumResults( self):
	return self.totalNumResults

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

    def doQuery( self,
		query=None,	# query string, use self.query if None
		journals=None,	# use self.journals if None
		startIndex=None	# index of 1st doc, self.startIndex if None
	):
	''' Submit the query and package up the results
	    Return a 2-tuple: (x, y)
		1) the total number of SciDirect results matching the query
		2) list of the returned records (each rcd = python dict)
	'''
	if query == None: query = self.query
	if journals == None: journals = self.journals
	if startIndex == None: startIndex = self.startIndex

	query = SciDirect.addJournalsToQuery( query, journals)

	# do query with only 1 result to get actual num of matching results
	(self.totalNumResults,results) = \
		    self.connection.doQuery( query, self.perPage, startIndex)

	return (self.totalNumResults,results)

    # end doQuery() -----------------------------------------------

# end class RefQuery -----------------------------

if __name__ == '__main__':

    # tests.... Should Junit or something smarter than this.

    ec = SciDirect.SciDirectConnection()
    rq = RefQuery( ec, sys.stdout.write, "Key(mouse)", [], 5, 0)

    if True:			 # test debug routine
	(totnum, results) = rq.doQuery(startIndex=2)
	print 'Query: "%s"  Total number of matches: %d,  Num Returned: %d' % \
					(rq.getQuery(),totnum, len(results))
	for r in results:
	    print SciDirect.articleFormat1(r)

	print
	q = "key(football)"
	(totnum, results) = rq.doQuery(q,journals=['"Cell"'])
	print 'Query: "%s"  Total number of matches: %d,  Num Returned: %d' % \
					(q,totnum, len(results))
	for r in results:
	    print SciDirect.articleFormat1(r)
	exit(0)
