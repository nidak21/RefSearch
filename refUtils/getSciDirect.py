#!/usr/bin/python
#
# Simple Command line interface to query Elsevier SciDirect and return results
#   to stdout
usageText = \
"""
usage:  getSciDirect.py options...
	-h	   - print this help
	-v	   - verbose, print API calls to stdout as they are called
	-i num	   - index of first article record to return (0-based)
	-m num	   - max number of article records to return (default 25)
	-a date	   - articles After this date, date = yyyymmdd
	-b date	   - articles Before this date, date = yyyymmdd
	-s value   - "true" or "false": set the subscribed attribute for search.
	             Default = false (search even MGI unsubscribed journals)
	-q query   - SciDirect query string, watch the quoting in the shell
	-f file	   - file holding SciDirect query string. Can do multi-line.
	-o format  - specify output format
		 format = std	- query counts and records (default)
		 format = raw	- raw json from SciDirect
		 format = json	- pretty printed json output
		 format = count	- just result count

	If no -q or -f options, reads from stdin.
	Prints output from Elsevier SciDirect to stdout.
"""
import sys
import os
import string
import json
#sys.path.append( os.path.join(sys.path[0],'jtLib') )
import SciDirect

def usage():
    print usageText
    exit(1)
# end usage() -----------------------------

def process( argv ):
    # set defaults
    qstring = None
    begdate = None
    enddate = None
    verbose = False
    fmt     = 'std'	# output format
    starti  = 0		# start index
    maxrslts= 25	# max number of results to return
    subscribed = "false" # search MGI unsubscribed journals

    # handle command line args
    argv.pop(0)		# skip argv[0], script name
    while len(argv) > 0:
	try:
	    arg = argv.pop(0)
	    if   arg == '-q': qstring = argv.pop(0)
	    elif arg == '-f':
		fname = argv.pop(0)
		qstring = open( fname, 'r').read().strip()
		# seems to handle multi-line files fine
	    elif arg == '-a': begdate = argv.pop(0)
	    elif arg == '-b': enddate = argv.pop(0)
	    elif arg == '-o': fmt = argv.pop(0)
	    elif arg == '-i': starti = int(argv.pop(0))
	    elif arg == '-m': maxrslts = int(argv.pop(0))
	    elif arg == '-s': subscribed = argv.pop(0)
	    elif arg == '-v': verbose = True
	    else: usage()	# includes -h and --help
	except IndexError as e:
	    usage()
    # end argv loop

    if qstring == None:		# read from stdin
	qstring = sys.stdin.read().strip()

    # set up query
    ev = SciDirect.SciDirectConnection()

    if begdate != None or enddate != None:
	qstring = SciDirect.addDatesToQuery(qstring, begdate, enddate)

    ev.setQuery(qstring)

    if verbose:
	ev.setDebugWriter( sys.stdout.write)
	print 'Query: %s' % qstring

    ev.setSubscribed( subscribed)

    # do query, either json or regular
    if fmt == 'json' or fmt == 'raw':

	data = ev.doQuery_Json(None, numToGet=maxrslts,startIndex=starti)
	if fmt == 'json': print json.dumps(data, sort_keys=False, indent=2,
	    						separators=(',',':') )
	if fmt == 'raw':  print data
    else:	# non-json article output
	if fmt == 'count': print ev.doCount( )
	elif fmt == 'std': doStd( ev, maxrslts, starti)
	else: usage()	# invalid output format
# end process() --------------------------

def doStd( ev,		# ElsevierSciDirect with its query completed
	   maxrslts,	# int, max num of results to get
	   starti	# int, start index for query
    ):
    (totalNum,data) = ev.doQuery(None,  numToGet=maxrslts, startIndex=starti)
   
    i = starti
    for pub in data:
	print
	print "%d %s" % (i, SciDirect.articleFormat1( pub) ),
	i = i +1
# end doStd() ---------------------

if __name__ == "__main__":
    process( sys.argv)
