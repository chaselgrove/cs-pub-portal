import flask
import pub

app = flask.Flask(__name__, static_url_path='')

@app.route('/pub.css')
def css():
    data = flask.render_template('pub.css', root=flask.request.script_root)
    return flask.Response(data, mimetype='text/css')

@app.route('/')
def index():
    pmid = flask.request.args.get('pmid')
    if pmid:
        pmid = pmid.strip()
        return flask.redirect(flask.url_for('publication', pmid=pmid))
    return flask.render_template('index.tmpl', root=flask.request.script_root)

@app.route('/pm/<pmid>')
def publication(pmid):
    error = None
    publication = None
    try:
        publication = pub.Publication.get_by_pmid(pmid)
    except:
        try:
            publication = pub.Publication.get_by_pmc_id(pmid)
        except ValueError:
            error = 'Bad ID "%s"' % pmid
        except pub.PublicationNotFoundError:
            error = 'Publication %s not found' % pmid
        else:
            url = flask.url_for('publication', pmid=publication.pmid)
            return flask.redirect(url)
    return flask.render_template('pub.tmpl', 
                                 root=flask.request.script_root, 
                                 error=error, 
                                 pub=publication)

if __name__ == '__main__':
    app.run(debug=True)

application = app
application.debug = True

# eof
