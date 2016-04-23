#!/usr/bin/python

# Jim's handy Python utilities

import string
import json

def stringIt(u,  		# string or Unicode to return as string
	     encoding='utf-8'	# encoding to use.
    ):
    '''Return 'u' as a string.
	If it's Unicode, convert it to utf-8 encoded string
    '''
    if type(u) == type(u'x'):
        return u.encode( encoding)
    else:
        return str(u)
# end strintIt() ---------------------

def jsonCurse( x, indent=''):
    ''' Simple, recursive, json printer so you can see the structure of
        a json data structure.
        Return a string, pretty printed verson of x, a json dict structure
    '''
    print "here is x: !%s!" % str(x) 
    lines = []
    newIndent = indent + '  '           # indent for recursive calls
    if type(x) == type( {} ):   # dictionary
        lines.append( indent + '{dict' + str(len(x)) + ' keys')
        for k in x.keys():
            lines.append( indent + 'key: ' + k )
            lines = lines + jsonCurse(x[k], indent=newIndent)
        lines.append( indent + '}' )
    elif type(x) == type( [] ): # list
        lines.append( indent + '[list' + str(len(x)) + ' items' )
        for li in x:
            lines.append( indent + 'list item' )
            lines = lines + jsonCurse(li, indent=newIndent)
        lines.append( indent + ']' )
    else:
        if type(x) == type(u'x'):       # type unicode
            x = x.encode('utf-8', 'backslashreplace')
        lines.append( indent + str(x) )

    print "here are lines: |%s|" % lines
    return string.join( lines, '\n')
# end jsonCurse() ----------------------------------

def jsonCurse_old( x, indent=''):
    ''' Simple, recursive, json printer so you can see the structure of
        a json data structure.
	JIM: should convert to just construct the string rather than printing
	Return a string, pretty printed verson of x, a json dict structure
    '''
    newIndent = indent + '  '           # indent for recursive calls
    if type(x) == type( {} ):   # dictionary
        print indent, '{dict', len(x), ' keys'
        for k in x.keys():
            print indent, 'key: ', k
            jsonCurse(x[k], indent=newIndent)
        print indent, '}'
    elif type(x) == type( [] ): # list
        print indent, '[list', len(x), ' items'
        for li in x:
            print indent, 'list item'
            jsonCurse(li, indent=newIndent)
        print indent, ']'
    else:
        if type(x) == type(u'x'):       # type unicode
            x = x.encode('utf-8')
        print indent, x
# end jsonCurse() ----------------------------------

class ConfigHolder (object):
    ''' lets you set/get a config option that any module can grab as needed '''
    curConfig = None

    @classmethod
    def getConfig( cls):
	return cls.curConfig

    @classmethod
    def setConfig( cls, config):
	cls.curConfig = config
# end class ConfigHolder ----------------------------------

PAGE_HEADER = \
'''
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">

<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
<title>%s</title>
</head>
<body>
'''
PAGE_FOOTER = \
'''
</body>
</html>
'''

class HtmlPage (object):
    ''' Simple Base class for creating HTML page content
    '''
    def __init__(self, title=''):
	# JIM: probably add args for title, css, js, etc.
	# JIM: maybe keep as an array of strings?
	#      How to support different headers?
	self.header = (PAGE_HEADER % title).strip().split('\n')
	self.body = []			# a list of strings
	self.footer = PAGE_FOOTER.strip().split('\n')

    def appendToBody(self, text):
	''' text is a string or a list of strings to add to the page
	'''
	if type(text) == type( '' ):	# is a string
	    text = [text]
	self.body += text

    def prependToBody(self, text):
	''' text is a string or a list of strings to prepend to the page
	'''
	if type(text) == type( '' ):	# is a string
	    text = [text]
	self.body = text + self.body

    def getPageText(self):
	return string.join(self.getPageLines(), '\n')

    def getPageLines(self):
	return self.header + self.body + self.footer

    def write(self, filename):
	fp = open( filename, 'w')
	fp.write( self.getPageText() )
	fp.close()
# end class HtmlPage -------------------------------

if __name__ == "__main__":
    if False:
	p = HtmlPage(title='my title')
	p.appendToBody('some text that should be 3rd')
	p.prependToBody(['some text that should be first', 'and 2nd'])
	p.appendToBody(['some text that should be 4th'])
	print p.getPageText()
	for line in p.getPageLines():
	    print line
    # test jsonCurse()
    jsonstr = '''{"foo1" : [ "xx", "yy", "zz" ], "foo2" : {"k1" : "tom"}, "foo3": "harry"}'''
    print jsonstr
    myjson = json.loads(jsonstr)
    print jsonCurse(myjson)
