from jinja2 import Environment, FileSystemLoader, Template

env = Environment( loader=FileSystemLoader('.'), trim_blocks=True)

template = env.get_template('justPlaying.html')

rows = [{'col1': 'chicken', 'col2': 'beef'},
	{'col1': 'popcorn', 'col2': "pizza"},
	{'col1': 'juice', 'col2': "pepsi"},
	]
rows = []
d = dict(name="Fred Rat", rows='None' )

print template.render(d)

