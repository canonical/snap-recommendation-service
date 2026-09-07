import flask
import functools

from snaprecommend.auth import authentication
from snaprecommend.auth.session import publisher_gateway


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
            return flask.make_response(
                flask.jsonify({"success": False, "error": "Unauthorized"}), 401
            )
        response = flask.make_response(func(*args, **kwargs))
        response.cache_control.private = True
        return response

    return is_user_logged_in


def admin_required(func):
    @functools.wraps(func)
    def is_admin(*args, **kwargs):
        if not flask.session["publisher"].get("is_admin", False):
            response = {
                "success": False,
                "error": "Admin permissions needed",
            }
            return flask.make_response(response, 403)
        return flask.make_response(func(*args, **kwargs))

    return is_admin


def exchange_required(func):
    @functools.wraps(func)
    def is_exchanged(*args, **kwargs):
        if "exchanged_developer_token" not in flask.session:
            try:
                result = publisher_gateway.exchange_dashboard_macaroons(
                    flask.session
                )
            except Exception:
                flask.current_app.logger.exception(
                    "Failed to exchange dashboard macaroons"
                )
                return flask.make_response(
                    {
                        "success": False,
                        "error": "Unauthorized",
                    },
                    401,
                )
            flask.session["developer_token"] = result
            flask.session["exchanged_developer_token"] = True
        return flask.make_response(func(*args, **kwargs))

    return is_exchanged
