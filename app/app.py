import flask
import pub

app = flask.Flask(__name__, static_url_path='')

@app.route('/')
def index():
    return flask.render_template('index.tmpl', root=flask.request.script_root)

@app.route('/pmc')
@app.route('/pmc/')
def pmc_redir():
    pmc_id = flask.request.args.get('pmc_id')
    if not pmc_id:
        return flask.redirect(flask.url_for('index'))
    return flask.redirect(flask.url_for('publication', pmc_id=pmc_id))

@app.route('/pmc/<pmc_id>')
def publication(pmc_id):
    publication = pub.Publication(pmc_id)
    return flask.render_template('pub.tmpl', 
                                 root=flask.request.script_root, 
                                 pub=publication)

if __name__ == '__main__':
    app.run(debug=True)

application = app
application.debug = True

# eof
