import flask
import pub

app = flask.Flask(__name__, static_url_path='')

def set_env():
    pub.set_debug(flask.request.environ.get('CSPUB_DEBUG'))
    pub.set_cache(flask.request.environ.get('CSPUB_CACHE'))
    return

@app.route('/pub.css')
def css():
    data = flask.render_template('pub.css', root=flask.request.script_root)
    return flask.Response(data, mimetype='text/css')

@app.route('/')
def index():
    set_env()
    id = flask.request.args.get('id')
    if id:
        id = id.strip().encode('ascii', 'replace')
        return flask.redirect(flask.url_for('publication', id=id))
    return flask.render_template('index.tmpl', root=flask.request.script_root)

@app.route('/pm/<id>')
def publication(id):
    set_env()
    id = id.encode('ascii', 'replace')
    error = None
    publication = None
    try:
        publication = pub.Publication.get_by_pmid(id)
    except:
        try:
            publication = pub.Publication.get_by_pmc_id(id)
        except ValueError:
            error = 'Bad ID "%s"' % id
        except pub.PublicationNotFoundError:
            error = 'Publication %s not found' % id
        else:
            url = flask.url_for('publication', id=publication.pmid)
            return flask.redirect(url)
    return flask.render_template('pub.tmpl', 
                                 root=flask.request.script_root, 
                                 error=error, 
                                 pub=publication)

@app.route('/reload/<pmid>')
def reload(pmid):
    set_env()
    pmid = pmid.encode('ascii', 'replace')
    publication = pub.Publication.get_by_pmid(pmid, True)
    url = flask.url_for('publication', id=publication.pmid)
    return flask.redirect(url)

if __name__ == '__main__':
    app.run(debug=True)

application = app
application.debug = True

# eof
