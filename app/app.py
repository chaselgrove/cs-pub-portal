import flask

app = flask.Flask(__name__)

@app.route('/')
def index():
    return flask.render_template('index.tmpl')

if __name__ == '__main__':
    app.run(debug=True)

application = app
application.debug = True

# eof
