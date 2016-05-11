
import sys
import traceback
import json
import string
import urllib
import urllib2
from flask import Flask, url_for, render_template, request
from SciDirect import SciDirectConnection

app = Flask(__name__)
elsevierConnect = SciDirectConnection()
querystring = ''	# most recent query string

@app.route("/", methods=['POST', 'GET'])
def base():
    return render_template('main_page.html', querystring=querystring)

@app.route("/login/")
@app.route("/logout/")
def login():
    return 'no login or logout yet'

@app.route('/process_form/')
def process_form():

    global querystring
    querystring = request.args.get('query', '')
    journals = request.args.getlist('journals')
    wholeQuery = constructQueryString(querystring, journals)
    #return wholeQuery
    if False:
	datadump = "method=%s... ...query='%s'" % (request.method, wholeQuery)
	app.logger.debug(datadump)

    message    = None
    totalCount = 0
    results    = []
    jsonDump   = None
    try:
	totalCount = elsevierConnect.doCount(query=wholeQuery)
	results = elsevierConnect.doQuery(query=wholeQuery,numToGet=5)
	jsonDump = json.dumps( elsevierConnect.doQuery_Json(query=wholeQuery),
		    sort_keys=False, indent=2, separators=(',', ': ') )
    except urllib2.HTTPError as e:
	if hasattr( e, 'code') and e.code == 400:
					    # probably query syntax error
	    message =  "HTTP error: You probably have an error in your query syntax."
	    # write stack trace and exception
	    e_type, e_value, e_tb = sys.exc_info()
	    app.logger.debug( string.join(
			traceback.format_exception(e_type, e_value, e_tb)) )
	else:
	    raise

    return render_template('query_results.html', 
			    querystring=wholeQuery,
			    message=message,
			    totalCount=totalCount,
			    count=len(results),
			    results=results,
			    jsonDump=jsonDump)

def constructQueryString( base, journals):
    query = base
    if len(journals) > 0:
	if query != '': query += " AND "
	query = query + 'SRCTITLE("%s"' % journals[0]
	for j in journals[1:]:
	    query = query + ' OR "%s"' % j
	query = query + ")"
    return query


if __name__ == "__main__":
    app.debug = True
    app.run()		# app.run(host='0.0.0.0') to make webapp avail to others
