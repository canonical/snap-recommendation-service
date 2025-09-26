import flask
from snaprecommend.featuredsnaps.utils import get_fetaured_snaps

featured_blueprint = flask.Blueprint("featured", __name__)


@featured_blueprint.route("/")
def featured_snaps():
    featured = get_fetaured_snaps()
    return flask.jsonify(featured), 200
