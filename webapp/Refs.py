
import json
from SciDirect import ElsevierSciDirect
from flask import Flask, url_for, render_template, request

app = Flask(__name__)
elsevierConnect = ElsevierSciDirect()

@app.route("/", methods=['POST', 'GET'])
def base():
    return render_template('query_form.html')

@app.route("/login/")
@app.route("/logout/")
def login():
    return 'no login or logout yet'

@app.route('/process_form/')
def process_form():
    query = request.args.get('query', '')
    if True:
	datadump = "method=%s... ...query='%s'" % (request.method, query)
	app.logger.debug(datadump)

    totalCount = elsevierConnect.doCount(query=query)
    results = elsevierConnect.doQuery(query=query,maxrslts=5)
    if type(results) == type("x"):	# connect error
	app.logger.debug(results)
	return results

    jsonDump = json.dumps( elsevierConnect.doQuery_json(query=query),
		    sort_keys=True, indent=2, separators=(',', ': ') )

    return render_template('query_results.html', 
			    querystring=query,
			    totalCount=totalCount,
			    count=len(results),
			    results=results,
			    jsonDump=jsonDump)

if __name__ == "__main__":
    app.debug = True
    app.run()		# app.run(host='0.0.0.0') to make webapp avail to others
