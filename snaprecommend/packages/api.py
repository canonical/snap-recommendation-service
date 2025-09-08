import flask

from snaprecommend.packages.utils import get_packages

store_packages_blueprint = flask.Blueprint("package", __name__)

FIELDS = [
    "title",
    "summary",
    "media",
    "publisher",
    "categories",
]


@store_packages_blueprint.route("store.json")
def get_store_packages():
    args = dict(flask.request.args)

    res = flask.make_response(get_packages(FIELDS, 15, args))
    return res
