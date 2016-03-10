import flask
import pub

app = flask.Flask(__name__)

@app.route('/')
def index():
    pmc_id = flask.request.args.get('pmc_id')
    if not pmc_id:
        return flask.render_template('index.tmpl')
    return flask.redirect(flask.url_for('publication', pmc_id=pmc_id))

@app.route('/<pmc_id>')
def publication(pmc_id):
    publication = pub.Publication(pmc_id)
    return flask.render_template('pub.tmpl', pub=publication)

if __name__ == '__main__':
    app.run(debug=True)

application = app
application.debug = True

# eof
