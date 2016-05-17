
import sys
import traceback
import json
import string
import urllib
import urllib2
from flask import Flask, url_for, render_template, request, redirect
import SciDirect
import RefQuery

DEFAULT_PER_PAGE = 50		# default number of results to show per page

app = Flask(__name__)
elsevierConnect = SciDirect.SciDirectConnection()
refQuery = None		# most recent query object

@app.route("/", methods=['POST', 'GET'])
def base():
    return render_template('main_page.html', querystring='')

@app.route("/login/")
@app.route("/logout/")
def login():
    return 'no login or logout yet'

@app.route('/process_form/')
def process_form():

    global refQuery
    querystring = request.args.get('query', '')
    journals = request.args.getlist('journals')
    startIndex = int( request.args.get('startIndex', 0) )
    refQuery = RefQuery.RefQuery(elsevierConnect, app.logger.debug, querystring,
			    journals, DEFAULT_PER_PAGE, startIndex=startIndex)
    message    = None
    totalCount = 0
    results    = []
    jsonDump   = None
    try:
	(totalCount,results) = refQuery.doQuery()
    except urllib2.HTTPError as e:
	if hasattr( e, 'code') and e.code == 400:
			    # probably query syntax error
	    message = \
		"HTTP error: You probably have an error in your query syntax."
	    # write stack trace and exception
	    e_type, e_value, e_tb = sys.exc_info()
	    app.logger.debug( string.join(
			traceback.format_exception(e_type, e_value, e_tb)) )
	else:
	    raise
    return render_template('query_results.html', 
			    querystring=querystring,
			    journals=journals,
			    message=message,
			    #totalCount=totalCount,
			    totalCount=refQuery.getTotalNumResults(),
			    count=len(results),
			    results=results,
			    jsonDump=jsonDump)

@app.route('/paging/')
def page_up_down():

    #return str(request.values.items())

    n_p = request.args.get('page', 'next')
    if n_p == 'next':
	startIndex = min( refQuery.getTotalNumResults() -1,
			    refQuery.getStartIndex() + refQuery.getPerPage() )
    elif n_p == 'prev':
	startIndex = max( 0, refQuery.getStartIndex() - refQuery.getPerPage() )

    refQuery.setStartIndex( startIndex)

    return redirect( url_for('process_form', query = refQuery.getQuery(),
		    journals = refQuery.getJournals(), startIndex=startIndex) )

if __name__ == "__main__":
    app.debug = True
    app.run()		# app.run(host='0.0.0.0') to make webapp avail to others
