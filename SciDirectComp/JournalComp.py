#!/usr/bin/python

import sys
import os
import time
import string
import ConfigParser
import argparse

sys.path.append( os.path.join(sys.path[0],'jtLib') )
from jinja2 import Environment, FileSystemLoader, Template
from jakUtils import *
from SciDirect import *
from SciDirectJournals import *
from PrecisionRecall import *
from MGIarticles import *

# Various Constants
SDQUERYDELIM = '|||'	# delimiter in config for joining SDquery strings
TCABBREVDELIM = ','	# delimiter in config for list of triage category abbrev
JOURNALDELIM = '|'	# delimiter in config for list of journal names

class ArgParser (object):
    """ ArgParser instantiates ConfigParser object,
	handles command line args and uses them to update the config.
	This class only knows about the args and the config
    """
    def __init__(self):
	DEFAULTCONFIG=os.path.join(sys.path[0],'config.cfg')
				    # default filename of config file in the
				    # directory where this script lives
	self.parser = argparse.ArgumentParser( description=\
	"""Compare results of SciDirect Queries to MGI triage selections.""")
				#usage='\n%(prog)s [options]')
	self.parser.add_argument('-c','--config', metavar='config_file',
				dest='configFile', 
				default=DEFAULTCONFIG,
				help='Config filename')
	self.parser.add_argument('-A', metavar='filename',
			dest='Acategory', nargs='+', default=argparse.SUPPRESS,
			help='files holding A & P queries. "-" for default')
	self.parser.add_argument('-G', metavar='filename',
			dest='Gcategory', nargs='+', default=argparse.SUPPRESS,
			help='files holding GO queries. "-" for default')
	self.parser.add_argument('-T', metavar='filename',
			dest='Tcategory', nargs='+', default=argparse.SUPPRESS,
			help='files holding Tumor queries. "-" for default')
	self.parser.add_argument('-E', metavar='filename',
		    dest='Ecategory', nargs='+', default=argparse.SUPPRESS,
		    help='files holding Expression queries. "-" for default')
	self.parser.add_argument('-N', metavar='filename',
			dest='Ncategory', nargs='+', default=argparse.SUPPRESS,
	help='files holding "None" queries - ignores triage category. "-" for default')

	self.parser.add_argument('-j', metavar='MGI_journal_name',
				dest='journals', nargs='+',  default=[],
				help='analyze these journals only')

	self.parser.add_argument('-o', metavar='output_directory',
			dest='outputDir', default=argparse.SUPPRESS,
			help='output directory, current dir is default')
	self.parser.add_argument('-y', metavar='year',
			dest='year', default=argparse.SUPPRESS,
			choices=['2011','2012','2013'],
			help='year to analyze (2011, 2012, 2013 -default)')
	self.parser.add_argument('--maxFalseNegs',metavar='num',
			dest='numFalseNegatives', default=argparse.SUPPRESS,
			type=int,
			help='max num of false negatives to display')
	self.parser.add_argument('--maxFalsePos',metavar='num',
			dest='numFalsePositives', default=argparse.SUPPRESS,
			type=int,
			help='max num of false positives to display')
	self.parser.add_argument('-d', action='store_true', 
			dest='dumpQueries', default=False,
			help=
		    '''causes all SciDirect results & false negatives to be
		    dumped in tab-delimited files in the output directory''')
    def parse_args(self):
	return self.parser.parse_args()

    def handleArgsAndConfig( self):
	''' Idea: parse command line args, read config file (ConfigParser).
	    Merge all things specified on the command line into the
	    ConfigParser object - and return that object & store it in
	    ConfigHolder.
	    That way, everything from here on can just look at the ConfigParser
	    object.
	'''
	args = ArgParser().parse_args()
	print args
	#exit(1)
	argdict = vars(args)	# args as a dictionary

	# get config
	co = ConfigParser.SafeConfigParser()
	configName = args.configFile
	co.readfp( open( configName, 'r') , configName)

	# update config object based on journal cmd line args
	if args.journals != []:		# journal sublist specified
	    co.set('Journals','journalSubList',
				string.join(args.journals,JOURNALDELIM))
	
	# update config triage category list and Triage Category query strings
	#   from command line
	tcLabelHandler = TcLabelHandler()
	tcList = []		# list of triage categories on command line
	for abb in tcLabelHandler.getAbbrevList():
	    argLabel = tcLabelHandler.abbrev2ArgLabel(abb)
	    if argdict.has_key(argLabel): # category was specified on cmd line
		tcList.append(abb)
		tcSection = tcLabelHandler.abbrev2ConfigSection(abb)
		queries = []			# list of queries for this cat
		for qsrc in argdict[argLabel]:	# get list from cmd line
		    if qsrc == '-':	# use default query from config
			q = co.get(tcSection,'sdQueryString')
		    else:		# from file instead
			q = open(qsrc,'r').read()
		    queries.append(q)
		co.set(tcSection, 'sdQueryString',
				    string.join(queries,SDQUERYDELIM))
	if len(tcList) > 0:	# some on the command line, overide config
	    co.set('DEFAULT','TriageCategoryList',
					string.join(tcList,TCABBREVDELIM) )

	# update output directory based on cmd line
	if argdict.has_key('outputDir'):
	    co.set('DEFAULT', 'OutputDir', argdict['outputDir'] )

	# set dump option from cmd line
	co.set('DEFAULT','DumpQueries',str(args.dumpQueries)) 

	# update year from cmd line
	if argdict.has_key('year'):
	    co.set('DEFAULT', 'Year', argdict['year'] )

	# update numFalsePositives from cmd line
	if argdict.has_key('numFalsePositives'):
	    co.set('HTML Output','numFalsePositives',
					str( argdict['numFalsePositives'] ) )
	# update numFalseNegatives from cmd line
	if argdict.has_key('numFalseNegatives'):
	    co.set('HTML Output','numFalseNegatives',
					str( argdict['numFalseNegatives'] ) )
	#self.printConfig( co)
	#exit(1)

	ConfigHolder.setConfig(co)
	return co
    # end handleArgsAndConfig() ---------------------------

    def printConfig(self, co	# ConfigParser object
    		):
	""" for debugging """
	for s in co.sections():
	    print s
	    for i in co.items(s):
		print "%s : %s" % (i[0], i[1])
	    print 
# end class ArgParser --------------------------

class TcLabelHandler (object):
    ''' Class that knows what the triage category abbreviations are and
	how to map them to command line arg labels (used in ArgParser)
	and Config Section headings (in ConfigParser)
    '''
    def getAbbrevList(self):
	return ['A', 'G', 'E', 'T', 'N']

    def abbrev2ArgLabel(self, abbrev):
	return abbrev + "category"

    def abbrev2ConfigSection(self, abbrev):
	return "Triage Category: " + abbrev
# end class TcLabelHandler ------------------------

class Processor (object): # [

    def __init__(self):

	self.config = ArgParser().handleArgsAndConfig()

	self.mgiRefs = MgiRefs( self.config.get('MGIReferences','filename') )

	self.sd = self.initSciDirectConnection()

	self.journals = self.initSciDirectJournals()
	print "%d Journals" % len(self.journals)

	self.triageCategories = self.initTriageCategories()
	self.nonExactJournals = {} 	# set in self.getSciDirectResults()

	# output files for triage category None
	self.sdAllResultsWriter = None	# all SD results across all journals
	self.sdFalseNegsWriter = None	# false neg rslts across all journals

	# jinja2 template stuff
	tmpltDir = self.config.get('DEFAULT','TemplateDir')
	self.jinja2Env = Environment( loader=FileSystemLoader(tmpltDir),
							    trim_blocks=True)

	self.process()
	return
    # end __init__() -------------------------------

    def initTriageCategories(self,):
	'''
	Return list TriageCategories to process.
	'''
	# get category abbrevations from section headings of config file
	catAbbrevs = self.config.get('DEFAULT',
				    'TriageCategoryList').split(TCABBREVDELIM)
	tcLabelHandler = TcLabelHandler()
	co = self.config

	tcList = []		# list of TriageCategory objs to return
	for ca in catAbbrevs:
	    section = tcLabelHandler.abbrev2ConfigSection(ca)
	    print section
	    queries = co.get(section,'sdQueryString').split(SDQUERYDELIM)
	    n = 1		# counter for number of queries for this TC
	    for q in queries:
		name = "%s_%d" % (co.get(section,'name'), n)
		displayName = "%s; Query %d" % (co.get(section,'displayName'),n)
		tc = TriageCategory(name,
				    displayName,
				    co.get( section, 'mgiCode'),
				    q)
		tcList.append(tc)
		n = n+1
		    
	return tcList
    # end initTriageCategories() -------------------------------

    def initSciDirectConnection(self):

	sd = ElsevierSciDirect()
	section = 'SciDirect'

	# compute start and end dates from 'Year'
	year = self.config.getint(section, 'Year')
	startDate = "%d1231" % (year-1)
	endDate = "%d0101" % (year+1)
	#print "StartDate '%s'    EndDate '%s'" % (startDate, endDate)

	sd.setStartDate( startDate)
	sd.setEndDate  ( endDate)

	sd.setContent  ( self.config.get(section, 'Content') )
	sd.setSubscribed( self.config.getboolean( section, 'Subscribed') )
	sd.setDebug     ( self.config.getboolean( section, 'Debug') )

	return sd
    # end initSciDirectConnection() -------------------------------

    def initSciDirectJournals(self):
	'''
	Return list of SciDirectJournal objects to process.
	'''
	section = 'Journals'
	filename = self.config.get(section, 'filename')
	journalList = SciDirectJournal.initSciDirectJournals(filename)

	journalSubList = []
	if self.config.has_option(section, 'journalSubList') \
	    and self.config.get(section, 'journalSubList') != '':
	    journalSubList = self.config.get(section, \
					'journalSubList').split(JOURNALDELIM) 

	if journalSubList != []:		# filter by this list of names
	    return [x for x in journalList if x.getMgiJname() in journalSubList]
	else:
	    return SciDirectJournal.getTriagedJournals()
    # end initSciDirectJournals() -------------------------------

    def process( self):

	self.results = PRresults(self.triageCategories, self.journals)
	self.dataRangler = DisplayDataRangler( self.results)

	for self.tc in self.triageCategories:
	    self.processTc()

	# render summary page using self.results
	t = self.jinja2Env.get_template('runSummary.html')
	d = self.dataRangler.getRunSummaryData()
	indexPathName = "%s/index.html" % self.config.get('DEFAULT','OutputDir')
	print "Writing RunSummary to %s" % indexPathName
	fp = open(indexPathName, 'w')
	fp.write( t.render(d) )
	fp.close()
    # end process() --------------------------------

    def processTc(self):
	print "Triage Category: %s\nSciDirect query:\n'%s'" % \
		    (self.tc.getDisplayName(), self.tc.getSdQueryString())

	for j in self.journals:
	    jPRStats = self.processJournal( j)

	    self.results.addJournalResults(self.tc, j, jPRStats)

	#self.outputPRStats( self.tcPRStats, "Totals Across All Journals")

	# render Triage category page using self.results
	#self.tcHtmlPage.endJournals()
	#self.tcHtmlPage.addTcSummary(self.tc, self.tcPRStats, self.journals)
	#tcPathName = "%s/category_%s.html" % \
	#	(self.config.get('DEFAULT', 'OutputDir'), self.tc.getName())
	#self.tcHtmlPage.write( tcPathName)

    # end processTc() --------------------------------

    def processJournal( self, j):

	self.outputJournalHeader( j)

	sdResults = self.getSciDirectResults(j)

	goldResults = self.getGoldResults( j)

	pr = PrecisionRecallCalculator( sdResults, goldResults,
			self.sdRef2MgiRef, goldKey=self.gold2key).calculate()

	self.outputResultsDumps( sdResults, pr)
	self.outputNonExactJournals( )

	header = "Totals for %s" % j.getMgiJname()
	self.outputPRStats( pr, header)
	self.outputFalseNegatives( j) # JIM think about params
	self.outputFalsePositives( j)

	return pr
    # end processJournal() --------------------------------

    def getSciDirectResults(self, j):
	''' Return list of SciDirectResults for the given journal and
	       self.tc TriageCategory.
	    Also set self.nonExactJournals for any articles returned
	      by the query that match journal names by words, but are not
	      exact matches.
	'''
	# query SciDirect query string for this triage category
	qstring = self.tc.getSdQueryString()
	# add journal name
	jname = j.getSdJname().replace("&", " ")	# SciDirect bungles &
	qstring = ( 'srctitle("%s") AND\n' % jname ) + qstring

	self.sd.setQuery(qstring)

	sdNumPubsJW = self.sd.doCount() # num of pubs matching journal words
					#   is upper bound on num Refs

	self.nonExactJournals = {}	# dict w/ keys being journal names
				    #  from SciDirect that match our journal
				    #  words, but not the journal title.
				    # So we can report these.
				    # nonExactJournals[x] = num of refs w/
				    #			    journalname x
	data = self.sd.doQuery( maxrslts=sdNumPubsJW)
	if type(data) == type("string"):	# had error
	    raise JournalCompError( data)

	results = []
	for sdRef in data:		# for each pub returned from SciDirect

	    sdJournal = sdRef['journal']
	    if  j.isSdJname( sdJournal ):	# have journal name match
		results.append(sdRef)
	    else:				# no journal name match
		self.nonExactJournals[ sdJournal ] = \
			self.nonExactJournals.get( sdJournal, 0) +1

	#print "Scidirect query: %d results" % len(results)
	return results

    # end getSciDirectResults() ----------------------------

    def getGoldResults(self, j):
	goldResults = []

	for r in self.mgiRefs.getMgiRefsByJournal( j):
	    if self.mgiRefs.refInTriageCategory(r, self.tc):
		goldResults.append(r)
	#print "GoldResults: %d" % len(goldResults)
	return goldResults
    # end getGoldResults() ----------------------------

    def sdRef2MgiRef( self, sdRef):
	''' For the current self.tc,
		match the sdRef against MGI refs.
	    Return the matching MGI ref record if one matches,
	    Return None if no match
	'''
	mgiRef = self.mgiRefs.matchRefById( 'DOI', sdRef['DOI'])
	if mgiRef == None:		# not found by DOI
	    mgiRef = self.mgiRefs.matchRefById( 'pubmed', sdRef['pubmed'])
	    if mgiRef == None:		# not found by pubmed ID
		return None

	# have a reference that matched by DOI or pubmed, check tc
	# if mgiRef.tc is wrong: return None # use self.tc
	if self.mgiRefs.refInTriageCategory(mgiRef, self.tc):
	    return mgiRef
	else:
	    return None
    # end sdRef2MgiRef() ------------------------------------

    def gold2key(self, g):
	'''
	Given a goldstd MgiRef object,
	Return a hashable key for it
	JIM: maybe this should be in MgiRef's class?
	'''
	return g['Jnum']

    def outputJournalHeader( self, j):

	print "----------------------"
	print "Journal: '%s',  SciDirect: '%s' for %s" % \
	    ( j.getMgiJname(), j.getSdJname(), self.tc.getDisplayName() )
	sys.stdout.flush()
    # end outputJournalHeader() -----------------------------

    def outputPRStats(self, pr, header):
	print
	print "%s; category: %s" % (header, self.tc.getDisplayName())
	print \
"MGI Pubs (Gold positives): %d;  SciDirect Results: %d;  TruePositives: %d" \
	    % (pr.getNumGoldPositives(),
	       pr.getNumResults(),
	       pr.getNumTruePositives())
	if pr.precisionIsDefined():
	    print "Precision  %4.2f     " % ( pr.getPrecision()) , 
	if pr.recallIsDefined():
	    print "Recall %4.2f" % (pr.getRecall()) ,
	print
    # end outputPRStats() -----------------------------

    class ReferencesWriter (object): #[
	''' object that knows how to write Reference results to a tab delimited
	    output file
	'''
	def __init__(self,
		    filename,	# string, filename to write to
		    fields	# list of field names from the result records to
		    		#  write
		    ):
	    self.fp = open(filename, "w")
	    self.fields = fields
	    self.fp.write( string.join( self.fields,'\t') + '\n')

	def writeReference(self, reference):
	    values = []
	    for f in self.fields:
		values.append( reference.get(f, '') )
	    self.fp.write( string.join( values, '\t') + '\n')

	def writeReferences(self, refs):
	    '''refs is a list of Reference result records
	    '''
	    for r in refs:
		self.writeReference( r)
    # end class ReferencesWriter -------------------------- ]

    def outputResultsDumps(self, sdResults, pr):
	""" Create a few special dumps of results.
	    Dump of all results returned from SciDirect.
	    Dump of all false negative results.
	"""
	if not self.config.getboolean('DEFAULT','dumpqueries'):
	    return
	sdFields = [ 'pubmed',	# fields from sdResults to output
		     'DOI',
		     'journal',
		     'volume',
		     'startingPage',
		     'endingPage',
		     'coverDate',
		     'pubType',
		     'prismType',
		     'title',
		   ]
	if self.sdAllResultsWriter == None:		# need a writer
	    filename = self.config.get( "DEFAULT", "sdAllResultsFile")
	    self.sdAllResultsWriter = self.ReferencesWriter( filename, sdFields)

	self.sdAllResultsWriter.writeReferences( sdResults)

	mgiFields = ['Jnum',	# fields from falseNegs (MGI rcds) to output
		     'pubmed',
		     'DOI',
		     'year',
		     'journal',
		     'title',
		   ]
	if self.sdFalseNegsWriter == None:		# need a writer
	    filename = self.config.get( "DEFAULT", "sdFalseNegsFile")
	    self.sdFalseNegsWriter = self.ReferencesWriter( filename, mgiFields)

	self.sdFalseNegsWriter.writeReferences( pr.getFalseNegatives() )

    def outputNonExactJournals(self):
	if self.tc.getName() == "None" and len(self.nonExactJournals) != 0:
	    print "SciDirect Journals matched inexactly by words in name: %d" \
			% ( len(self.nonExactJournals.keys()) )
	    for nej in self.nonExactJournals.keys():
		print "Non-matching journal: '%s'  (%d articles)" % \
				    (nej, self.nonExactJournals[ nej])

    def outputFalsePositives(self, j):
	return

    def outputFalseNegatives(self, j):
	return
	# JIM: should only need to do this if Recall is not 1 -right?
	for un in self.mgiRefs.getUnmatchedRefsByJournal( j):
	    print "%s was not found in SciDirect query" % un['Jnum']
	
	sys.stdout.flush()

    # end outputFalseNegatives() --------------------------------

# end class Processor ----------------------------------- ]

class PRresults (object):
    ''' a PRresults object holds the results from a run of searches for
        one or more TriageCategories and a list of SciDirectJournals.

	Each tc gets PrecisionRecallStats object that aggregates results from
	   each Journal analyzed for that tc.
	The PrecisionRecallCalculator object is stored for each (tc, journal) 
	    pair.
    '''
    def __init__(self, tclist, journals):
	self.triageCategories = tclist
	self.journals         = journals
	self.OverallPR = {}	# dict[tc] = PrecisionRecallStats obj that
				#   summarized data across all journals
	for tc in self.triageCategories:
	    self.OverallPR[tc] = PrecisionRecallStats()

	self.PR = {}		# dict mapping (tc,journal) pairs to their
				#   PrecisionRecallCalculator objects

    def addJournalResults(self, tc, journal, pr):
	self.PR[ (tc, journal) ] = pr
	self.OverallPR[tc].incAll( pr)

    def getJournals(self):
	return self.journals

    def getJournalResults(self, tc, journal):
	return self.PR[ (tc, journal) ]

    def getTcOverallResults(self, tc):
	return self.OverallPR[ tc]
# end class PRresults ---------------------------------

class DisplayDataRangler (object):
    ''' A DisplayDataRangler is an object that know how to package up the data
        to be displayed on various generated outputs.
	It puts those data into a Python dictionary that, typically, will be
	passed to Jinja2 Template to be rendered.
	- So the variables referred to on the Template are coupled to the 
	  dict returned.
	So likely, there will be a method in this class for each webpage
	    template we have.
    '''
    def __init__(self, results	# PRresults object
		):
	self.results = results
	self.datetime = 'jim figure this out'

    def getRunSummaryData(self):
	rows = []
	for tc in self.results.triageCategories:
	    pr = self.results.getTcOverallResults(tc)
	    r = dict( \
		name           = tc.getDisplayName(),
		nGoldPos       = pr.getNumGoldPositives(),
		nSciDirResults = pr.getNumResults(),
		nTruePos       = pr.getNumTruePositives(),
		nFalsePos      = '-', #r.nSciDirResults - r.nTruePos,
		nFalseNeg      = '-',
		precision      = '-',
		recall         = '-',
		)
	    # JIM need to round precision and recall
	    if pr.precisionIsDefined(): r['precision'] = pr.getPrecision()
	    if pr.recallIsDefined(): r['recall'] = pr.getRecall()

	    rows.append(r)

	d = {   'nJournals' : len( self.results.getJournals() ),
		'rows'	: rows
	    }
	return d

    def getTcSummaryData(self):
	d = {}
	return d
# end class DisplayDataRangler ---------------------------------

class IndexHtmlPage (HtmlPage):

    def addTc(self,
		tc,		# TriageCategory obj
		pr,		# PrecisionRecallStats obj
		journals	# list of SciDirectJournals
	    ):
	''' Add summary info for the TriageCategory and PRstats to the
	    results Index page
	'''
	lines = ["<hr>"]
	linkText = '<a href="category_%s.html">details</a>' % tc.getName()
	t = time.ctime(time.time())
	lines.append("<p>Category: %s (%d journals) %s --- %s" % \
		    (tc.getDisplayName(),len(journals), linkText, t) )
	lines.append( \
"<p>MGI Pubs (Gold positives): %d;  SciDirect Results: %d;  TruePositives: %d" \
	    % (pr.getNumGoldPositives(),
	       pr.getNumResults(),
	       pr.getNumTruePositives()) )
	lines.append("<br>")
	if pr.precisionIsDefined():
	    lines.append( "Precision:  %4.2f; " % ( pr.getPrecision()) ) 
	if pr.recallIsDefined():
	    lines.append( "Recall: %4.2f" % (pr.getRecall()) )

	lines.append("<p>Query:\n<pre>%s</pre>" % tc.getSdQueryString() )

	self.appendToBody( lines)

# end class IndexHtmlPage -------------------------- ]

class TcHtmlPage (HtmlPage):

    def __init__(self, title=''):
	super(self.__class__, self).__init__(title=title)
	self.journalsInfo = []	# list of (Journal, PrecisionRecallStats)

    def addTcSummary(self,
		tc,		# TriageCategory obj
		pr,		# PrecisionRecallStats obj
		journals	# list of SciDirectJournals
	    ):
	''' Add summary info for the TriageCategory and PRstats to the
	    results Index page
	'''
	lines = []
	linkText = '<a href="index.html">back to index</a>'
	t = time.ctime(time.time())
	lines.append("<p>Category: %s (%d journals) %s --- %s" % \
		    (tc.getDisplayName(),len(journals), linkText, t) )
	lines.append( \
"<p>MGI Pubs (Gold positives): %d;  SciDirect Results: %d;  TruePositives: %d" \
	    % (pr.getNumGoldPositives(),
	       pr.getNumResults(),
	       pr.getNumTruePositives()) )
	lines.append("<br>")
	if pr.precisionIsDefined():
	    lines.append( "Precision:  %4.2f; " % ( pr.getPrecision()) ) 
	if pr.recallIsDefined():
	    lines.append( "Recall: %4.2f" % (pr.getRecall()) )

	lines.append("<p>Query:\n<pre>%s</pre>" % tc.getSdQueryString() )

	self.prependToBody( lines)
    
    def addJournal(self,
		    journal,	# SciDirectJournal obj
		    pr		# PrecisionRecallCalculator obj
		):
	self.journalsInfo.append( (journal, pr) )

    def endJournals(self):
	lines = []
	for (j,pr) in self.journalsInfo:
	    lines.append("<p><hr>")
	    lines.append("<b>%s (%s) --- SciDirect: %s</b>" % \
		(j.getMgiJname(),j.getTriagedBy(), j.getSdJname()) )
	    lines.append( \
"<p>MGI Pubs (Gold positives): %d;  SciDirect Results: %d;  TruePositives: %d" \
		% (pr.getNumGoldPositives(),
		   pr.getNumResults(),
		   pr.getNumTruePositives()) )
	    lines.append("<br>")
	    if pr.precisionIsDefined():
		lines.append( "Precision:  %4.2f; " % ( pr.getPrecision()) ) 
	    if pr.recallIsDefined():
		lines.append( "Recall: %4.2f" % (pr.getRecall()) )

	    fp = pr.getFalsePositives()
	    if len(fp) == 0:
		lines.append("<p>False Positives: none")
	    else:
		#n = 10000  #self.config.getint('HTML Output', 'numFalsePositives')
		n = ConfigHolder.getConfig().getint('HTML Output', 'numFalsePositives')
		lines.append("<p>False Positives: %d of %d" % \
				( min(n,len(fp)), len(fp) ) )
		lines.append(" (returned by SciDirect but not selected in MGI)")
		lines.append('<table border=1>')
		lines.append('<tr><th>DOI</th><th>Title</th><th>pubType</th><th>Abstract</th></tr>')

		for rcd in fp[:n]:
		    doiLink = '<a href="http://dx.doi.org/%s">%s</a>' % \
		    				(rcd['DOI'], rcd['DOI'])
		    lines.append('<tr>')
		    lines.append('<td>%s</td>' % doiLink)
		    lines.append('<td>%s</td>' % rcd['title'])
		    lines.append('<td>%s</td>' % rcd['pubType'])
		    lines.append('<td>%s</td>' % " ") #rcd['abstract'])
		    lines.append('</tr>')
		lines.append('</table>')

	    fp = pr.getFalseNegatives()
	    if len(fp) == 0:
		lines.append("<p>False Negatives: none")
	    else:
		#n = 3 #self.config.getint('HTML Output', 'numFalseNegatives')
		n = ConfigHolder.getConfig().getint('HTML Output', 'numFalseNegatives')
		lines.append("<p>False Negatives: %d of %d" % \
				( min(n,len(fp)), len(fp) ) )
		lines.append(" (not returned by SciDirect but selected in MGI)")
		lines.append('<table border=1>')

		for rcd in fp[:n]:

		    MGIurl = 'http://informatics.jax.org/accession'
		    jnumLink = '<a href="%s/%s">%s</a>' % \
		    		(MGIurl, rcd['Jnum'], rcd['Jnum'])
		    doiLink = '<a href="http://dx.doi.org/%s">%s</a>' % \
		    				(rcd['DOI'], rcd['DOI'])
		    lines.append('<tr>')
		    lines.append('<td>%s</td>' % jnumLink)
		    lines.append('<td>%s</td>' % doiLink)
		    lines.append('<td>%s</td>' % rcd['title'])
		    lines.append('<td>%s</td>' % rcd['authors'])
		    lines.append('</tr>')
		lines.append('</table>')

	self.appendToBody( lines)

# end class TcHtmlPage -------------------------- ]

class JournalCompError (Exception):
    ''' Exception class for odd things that shouldn't happen.
    '''
    def __init__(self, msg):
	self.msg = msg
    def __str__(self):
	return repr(self.msg)

# end class JournalCompError --------------------------

if __name__ == "__main__":
    p = Processor( )
