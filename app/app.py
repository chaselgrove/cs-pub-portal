import flask
import pub

app = flask.Flask(__name__, static_url_path='')

@app.route('/')
def index():
    pmid = flask.request.args.get('pmid')
    if pmid:
        return flask.redirect(flask.url_for('publication', pmid=pmid))
    return flask.render_template('index.tmpl', root=flask.request.script_root)

@app.route('/pm/<pmid>')
def publication(pmid):
    error = None
    publication = None
    try:
        publication = pub.Publication(pmid)
    except ValueError:
        error = 'Bad PMID'
    except pub.PublicationNotFoundError:
        error = 'Publication not found'
    return flask.render_template('pub.tmpl', 
                                 root=flask.request.script_root, 
                                 error=error, 
                                 pub=publication)

if __name__ == '__main__':
    app.run(debug=True)

application = app
application.debug = True

# eof
