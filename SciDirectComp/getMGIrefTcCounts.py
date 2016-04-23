#!/usr/local/bin/python

#  runsql.py
###########################################################################
#
#  Purpose:
#	   run one or more sql commands from stdin (separated by "||"),
#		and send the output in tab-delimited form to stdout
#
#  Usage:  
USAGETEXT = """Usage: runsql.py [-s server] [-d database] [-sep string] [-delim string] [-q]
	Run one or more sql commands from stdin,
	and send output in tab-delimited form to stdout.
	-s (or -S) server   defaults to ADHOC_MGI.
	-d (or -D) database defaults to mgd.
	Everything runs as MGD_PUBLIC.
	-sep string defines the sql command separator string, default is "||"
	-delim string defines the output field separator, default is tab
	-q means quiet - don't write diagnositic msgs to stderr
"""
#
#  Env Vars:  None
#
#  Inputs:	SQL commands from stdin
#
#  Outputs:     SQL output to stdout	
#
#  Exit Codes:
#
#      0:  Successful completion
#      1:  An exception occurred
#
#  Assumes:  Nothing
#
###########################################################################
import ignoreDeprecation
import sys
import os
import string
import time
import db

SQL = '''
-- SQL to create a table of journals by Triage categories (A, G, E, T)
--   with the cells being the number of papers from each journal selected
--   for that category.

-- first get tmp table w/ journal, triage category (dataset), count
select r.journal, ds._dataset_key, ds.abbreviation, count( *) as "refcount"
into #refTcount
from bib_refs r join bib_dataset_assoc dsa on (r._refs_key = dsa._refs_key )
join bib_dataset ds on (dsa._dataset_key = ds._dataset_key)
where r.year = %(year)s
and r.journal is not null
group by r.journal, ds._dataset_key, ds.abbreviation
||
select count(distinct journal) from #refTcount
||
-- now build the output table w/ columns for each triage category
select  distinct rc.journal, rcA.refcount as "A&P", rcG.refcount as "GO", rcE.refcount as "Expr", rcT.refcount as Tumor
from #refTcount rc 
left outer join #refTcount rcA on (rc.journal = rcA.journal and rcA._dataset_key = 1002)
left outer join #refTcount rcG on (rc.journal = rcG.journal and rcG._dataset_key = 1005)
left outer join #refTcount rcE on (rc.journal = rcE.journal and rcE._dataset_key = 1004)
left outer join #refTcount rcT on (rc.journal = rcT.journal and rcT._dataset_key = 1007)
order by rc.journal
'''

COLUMNS = [ 'journal', 'A&P', 'GO', 'Expr', 'Tumor' ]

#
#  CONSTANTS
#
DEBUG = 0

def usage():
# Purpose: print usage message and exit
    sys.stderr.write( USAGETEXT)
    sys.exit(1)
# end usage() --------------------------------------------------------

def getArgs():
# Purpose: parse command line args
# Returns: a dict mapping arg names to values
#	   "script" -> "$0" - the name of this script
# Effects: dies with usage if invalid args are passed

    argDict = {}	# dict mapping argument "names" to their values
    myArgs = sys.argv	# local copy of args

    argDict[ "script"] = myArgs[0]	# always the name of the invoked script
    del myArgs[0]

    # Set defaults:
    argDict[ "DBSERVER"]     = "DEV_MGI"
    argDict[ "DBNAME"]       = "mgd"
    argDict[ "SQLSEPARATOR"] = "||"
    argDict[ "DELIMITER"]    = "\t"
    argDict[ "QUIET"]        = False

    # Process "-" flag arguments
    while len(myArgs) > 0 and myArgs[0][0] == "-": # while next arg start w/ -
	arg = myArgs[0]
	del myArgs[0]		# throw arg away, i.e., "shift"
	if arg == "-d" or arg == "-D":
	    getRequredFlagValue( myArgs, argDict, "DBNAME")
	elif arg == "-s" or arg == "-S":
	    getRequredFlagValue( myArgs, argDict, "DBSERVER")
	elif arg == "-sep":
	    getRequredFlagValue( myArgs, argDict, "SQLSEPARATOR")
	elif arg == "-delim":
	    getRequredFlagValue( myArgs, argDict, "DELIMITER")
	elif arg == "-q":
	    argDict[ "QUIET"] = True
	else:
	    usage()

    # Process non-flag (non "-") args
    if len(myArgs) != 0:
	usage()

    # Apply any cleanups and error checks

    return argDict

# end getArgs() ----------------------------------------------------------

def getRequredFlagValue( args,	# arg list (like sys.argv)
		  argDict,	# dictionary to hold labels mapping to arg vals
		  label		# dict label (key) to use for this arg
		  ):
# Purpose: check that args has at least one more arg in it and assign
#	   argDict[ label] = arg[0]
# 	   Invoke usage() (and die) if args is empty
# Effects: Remove the arg from args.

    if len(args) == 0:
	usage()
    else:
	argDict[ label] = args[0]
	del args[0]

# end getRequredFlagValue()-------------------------------------------------

def process ():
# Purpose: Main routine of this script
# Returns: nothing

    args = getArgs()

    notQuiet = not args[ "QUIET"]

    db.set_sqlServer  ( args["DBSERVER"])
    db.set_sqlDatabase( args["DBNAME"])
    db.set_sqlUser    ("MGD_PUBLIC")
    db.set_sqlPassword("mgdpub")

    query = SQL % {'year' : '2013'}
    queries = string.split(query, args[ "SQLSEPARATOR"])

    if notQuiet:
	sys.stderr.write("Running %d SQL command(s) on %s..%s\n" % \
			( len( queries), args[ "DBSERVER"], args[ "DBNAME"]) )
	sys.stderr.flush()

    startTime = time.time()
    results = db.sql( queries, 'auto')
    endTime = time.time()
    if notQuiet:
	sys.stderr.write( "Total SQL time: %8.3f seconds\n" % \
							(endTime-startTime))
	sys.stderr.flush()

    delim = args[ "DELIMITER"]

    result = results[2]

    # print column headers
    sys.stdout.write( string.join( COLUMNS, delim) )
    sys.stdout.write( "\n")

    # print results, one line per row (result), tab-delimited
    for r in result:
	vals =  [ r[col] for col in COLUMNS ]
	vals = map( cleanVal, vals)
	sys.stdout.write( string.join(vals, delim ) )
	sys.stdout.write( "\n")
    
# end process() ----------------------------------

def cleanVal( val):
    if val == None:
	val = ""
    return str(val)

#
#  MAIN
#
process()
sys.exit(0)
