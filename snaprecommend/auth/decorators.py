import functools
import flask

from snaprecommend.auth import authentication
from snaprecommend.auth.session import publisher_gateway


def login_required(func):
    @functools.wraps(func)
    def is_user_logged_in(*args, **kwargs):
        if not authentication.is_authenticated(flask.session):
            authentication.empty_session(flask.session)
            return flask.redirect(f"/login?next={flask.request.path}")

        return func(*args, **kwargs)

    return is_user_logged_in


def exchange_required(func):
    @functools.wraps(func)
    def is_exchanged(*args, **kwargs):
        try:
            if "exchanged_developer_token" not in flask.session:
                result = publisher_gateway.exchange_dashboard_macaroons(
                    flask.session
                )
                flask.session["developer_token"] = result
                flask.session["exchanged_developer_token"] = True
            return func(*args, **kwargs)
        except Exception as e:
            print(e)
    return is_exchanged

def admin_required(func):
    @functools.wraps(func)
    def is_admin(*args, **kwargs):
        if not flask.session["publisher"]["is_admin"]:
            # flask.abort(403)
            response = {
                "success": False,
                "message": "Admin permissions needed",
            }
            return flask.make_response(response, 403)
        return func(*args, **kwargs)

    return is_admin
