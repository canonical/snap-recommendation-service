import functools
import flask

from snaprecommend.auth import authentication


def dashboard_login(func):
    @functools.wraps(func)
    def is_user_logged_in(*args, **kwargs):
        if not authentication.is_authenticated(flask.session):
            authentication.empty_session(flask.session)
            return flask.redirect(f"/login?next={flask.request.path}")
        response = flask.make_response(func(*args, **kwargs))
        response.cache_control.private = True
        return response

    return is_user_logged_in


def login_required(func):
    @functools.wraps(func)
    def is_user_logged_in(*args, **kwargs):
        if not authentication.is_authenticated(flask.session):
            authentication.empty_session(flask.session)
            return flask.make_response(flask.jsonify({"status": "failed", "error": "Unauthorized"}), 401)
        response = flask.make_response(func(*args, **kwargs))
        response.cache_control.private = True
        return response
    return is_user_logged_in
