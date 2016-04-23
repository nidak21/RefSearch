#!/usr/bin/python

# Jim's handy Python utilities

import string

def stringIt(u,  		# string or Unicode to return as string
	     encoding='ascii'	# encoding to use.
    ):
    '''Return 'u' as a string.
	If it's Unicode, convert it to utf-8 encoded string
    '''
    if type(u) == type(u'x'):
        return u.encode( encoding,errors='backslashreplace')
    else:
        return str(u)
# end strintIt() ---------------------

def jsonCurse( x, indent=''):
    ''' Simple, recursive, json printer so you can see the structure of
        a json data structure.
	Return a string, pretty printed verson of x, a json dict structure
    '''
    lines = []
    newIndent = indent + '  '           # indent for recursive calls
    if type(x) == type( {} ):   # dictionary
        lines.append( indent + '{dict' + str(len(x)) + ' keys')
        for k in x.keys():
            lines.append( indent + 'key: ' + k )
            lines += jsonCurse(str(x[k]), indent=newIndent)
        lines.append( indent + '}' )
    elif type(x) == type( [] ): # list
        lines.append( indent + '[list' + str(len(x)) + ' items' )
        for li in x:
            lines.append( indent + 'list item' )
            lines += jsonCurse(str(li), indent=newIndent)
        lines.append( indent + ']' )
    else:
        if type(x) == type(u'x'):       # type unicode
            x = x.encode('utf-8', 'backslashreplace')
        lines.append( indent + str(x) )

    return string.join( lines, '\n')
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

if __name__ == "__main__":
    pass
