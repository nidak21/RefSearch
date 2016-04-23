#!/usr/bin/python
# classes for computing and storing Precision and Recall for queries.
#
# Class PrecisionRecallStats - holds stats and computes P/R numeric values
# Class PrecisionRecallCalculator - computes P/R for a given result set
#   				See Class comments for an overview.

import collections

class PrecisionRecallStats(object):
    '''
    A PrecisionRecallStats object keeps track of the result counts for a
    particular query so we can compute the query's precision and recall.
    Keeps track of:
	numResults - the total number of results returned by the query
	numTruePositives - the number of results returned by the query that
				are considered positive results
	numGoldPositives  - the number of real positives typically determined
				by some "gold standard" for the result set.
    '''
    def __init__(self):
	self.numResults = 0		# total number of results from the query
	self.numTruePositives = 0	# total number of results counted as
					#    "positives"
	self.numGoldPositives = 0	# total number of true positives

    def incNumTruePositives(self, inc=1):
	''' Increment the number of true positive results
	'''
	self.numTruePositives += inc

    def incNumResults(self, inc=1):
	''' Increment the number of results
	'''
	self.numResults += inc

    def incNumGoldPositives(self, inc=1):
	''' Increment the number of Gold positives
	'''
	self.numGoldPositives += inc

    def incAll(self, pr):
	''' Increment all three counts from the given PrecisionRecall object.
	    Handy if you are aggregating P/R across multiple queries.
	'''
	self.incNumTruePositives( inc=pr.getNumTruePositives() )
	self.incNumResults(       inc=pr.getNumResults() )
	self.incNumGoldPositives( inc=pr.getNumGoldPositives() )

    def getNumTruePositives(self):
	return self.numTruePositives

    def getNumResults(self):
	return self.numResults

    def getNumGoldPositives(self):
	return self.numGoldPositives

    def precisionIsDefined(self):
	return (self.numResults != 0)

    def recallIsDefined(self):
	return (self.numGoldPositives != 0)

    def getPrecision(self):
	return float(self.numTruePositives)/float(self.numResults)

    def getRecall(self):
	return float(self.numTruePositives)/float(self.numGoldPositives)
# end class PrecisionRecallStats ---------------------

class PrecisionRecallCalculator(PrecisionRecallStats):
    ''' 
	Calculate Precision/Recall for a data retrieval (i.e., query) problem
    	Takes
	    a list (or iterator) of results from some query (data retrieval)
	    a list (or iterator) of "gold standard" (the known positive results)
	and computes precision and recall, letting you get various subsets
	of results back (e.g., the subset of the results that are true positives
	    or false positives...)

	"result" objs and "goldstd" objs do not have to be of the same type.
	    the findGoldstd() function that is passed maps result objs
	    to corresponding goldstd objs (if any) to determine if a result
	    obj is a positive or negative.

	Idea: the query "results" are trying to approximate the "gold standard"

				  In Gold Std set
				yes              no
			 +---------------+---------------+
	    Returned  yes| true positive | false positive|
	    by query     +---------------+---------------+
		       no| false negative| true negative |
			 +---------------+---------------+

	For example, a false positive: the query returned it,
					but it shouldn't have
		     a false negative: the query didn't return it,
		     			but it should have.

	Note, we cannot return the set of true negatives because they are not
		in the result set, nor in the gold standard set.
	But we can and do return the other three categories.
    '''
    def __init__(self, 
    		 results, 	# list of iterator of result objects
		 goldstd,	# list or iterator of "gold standard", true
		 		#	positive result objects
		 findGoldstd,	# function(result obj) and returns the
		 		#   corresponding goldstd obj (if any)
				#  or None if the result is not a "positive"
		 goldKey=None	# Function to return a hashable key for a
				#  goldstd object if indiv goldstd objs are
				#  not hashable (e.g, dicts)
		):
	super(self.__class__, self).__init__()
	self.results     = results
	self.findGoldstd = findGoldstd
	self.truePos	= []		# list of true positives:
					#    (result obj, goldstd obj) pairs
	self.falsePos	= []		# list of false positives
					#    result objs
	#self.falseNegs	= set(goldstd)	# set of false Negatives
					#    goldstd objs
					# = set of goldstd objs not yet matched
					#   by any results
	self.goldKey = goldKey
	self.falseNegs = {}		# dict mapping goldstd objs or their key
	for g in goldstd:
	    if self.goldKey == None:
		self.falseNegs[g] = 1
	    else:
		self.falseNegs[self.goldKey(g)] = g

	self.incNumGoldPositives( len(self.falseNegs) )
	# JIM: should this just call self.calculate()?
    # end __init__()

    def calculate(self):

	for r in self.results:
	    self.incNumResults()

	    matchingGold = self.findGoldstd( r)
	    if matchingGold != None:	# have a true positive
		self.truePos.append( (r,matchingGold) )
		self.incNumTruePositives()
		# Remove matchingGold object from self.falseNegs
		if self.goldKey == None:
		    del self.falseNegs[ matchingGold]
		else:
		    # JIM: this was Jnum that was getting deleted twice,
		    # i.e., matched multiple times on a given SciDirect
		    #  query - but then it went away - spurious SciDirect bug?
		    #if matchingGold['Jnum'] == 'J:192312':
		    #   print "%s matched %s" % (r['DOI'], matchingGold['Jnum'])
		    del self.falseNegs[ self.goldKey(matchingGold) ]

	    else:			# have a false positive
		self.falsePos.append(r)

	return self

    def getTruePositives(self):
	''' Return set of (result obj, goldst obj) pairs for the true positives
	'''
	return self.truePos

    def getFalsePositives(self):
	''' Return set of result objs that are false positives
	'''
	return self.falsePos

    def getFalseNegatives(self):
	''' Return set of goldstd objs that are false negatives
	'''
	if self.goldKey == None:
	    return self.falseNegs.keys()
	else:
	    return self.falseNegs.values()

# end class PrecisionRecallCalculator -------------------

if __name__ == "__main__":

    # some test code
    goldstd = [ 'red', 'green', 'yellow' ]
    results = [ 'red', 'yellow', 'cat', 'dog']

    def myFindGold( r):
	for g in goldstd:
	    if r == g: return g
	return None
    # end myFindGold() ---------

    pr = PrecisionRecallCalculator( results, goldstd, myFindGold).calculate()
    print "Goldstd: " 
    print goldstd
    print "Results: "
    print results
    print "True Positives : " 
    print pr.getTruePositives()
    print "False Positives: "
    print pr.getFalsePositives()
    print "False Negatives: "
    print pr.getFalseNegatives()
    print "NumTruePositives: %d" % pr.getNumTruePositives()
    print "NumResults: %d" % pr.getNumResults()
    print "NumGoldPositives: %d" % pr.getNumGoldPositives()
    print "Precision: %f (should be 1/2)" % pr.getPrecision()
    print "Recall   : %f (should be 2/3)" % pr.getRecall()

    # second example with results and goldstd as records (dicts)
    results = [ {'name': 'howard'}, {'name' : 'laura'} ] # 2 rcds
    goldstd = [ {'name': 'laura'}, {'name' : 'wendy'} ]
    def myFindGold2( r):
	for g in goldstd:
	    if g['name'] == r['name']: return g
	return None

    def goldKey( g):
	return g['name']

    print
    print "Second Example"
    pr = PrecisionRecallCalculator( results, goldstd, myFindGold2, goldKey=goldKey).calculate()
    print "Goldstd: " 
    print goldstd
    print "Results: "
    print results
    print "True Positives : " 
    print pr.getTruePositives()
    print "False Positives: "
    print pr.getFalsePositives()
    print "False Negatives: "
    print pr.getFalseNegatives()
    print "NumTruePositives: %d" % pr.getNumTruePositives()
    print "NumResults: %d" % pr.getNumResults()
    print "NumGoldPositives: %d" % pr.getNumGoldPositives()
    print "Precision: %f (should be 1/2)" % pr.getPrecision()
    print "Recall   : %f (should be 1/2)" % pr.getRecall()
