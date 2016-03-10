import flask

app = flask.Flask(__name__)

@app.route('/')
def index():
    return '<html><body>Hello, world</body></html>\n'

if __name__ == '__main__':
    app.run(debug=True)

application = app
application.debug = True

# eof
