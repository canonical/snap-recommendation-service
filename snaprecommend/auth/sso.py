import flask
from django_openid_auth.teams import TeamsRequest, TeamsResponse
from flask_openid import OpenID
from snaprecommend.auth import authentication
from snaprecommend.auth.constants import DEFAULT_SSO_TEAM, SSO_LOGIN_URL


def init_sso(app: flask.Flask):
    open_id = OpenID(
        store_factory=lambda: None,
        safe_roots=[],
        extension_responses=[TeamsResponse],
    )

    SSO_TEAM = app.config.get("OPENID_LAUNCHPAD_TEAM", DEFAULT_SSO_TEAM)

    @app.route("/logout")
    def logout():
        authentication.empty_session(flask.session)
        return flask.redirect("/")

    @app.route("/login", methods=["GET", "POST"])
    @open_id.loginhandler
    def login():
        if authentication.is_authenticated(flask.session):
            if flask.request.is_secure:
                return flask.redirect(
                    open_id.get_next_url().replace("http://", "https://")
                )
            return flask.redirect(open_id.get_next_url())

        teams_request = TeamsRequest(query_membership=[SSO_TEAM])
        return open_id.try_login(
            SSO_LOGIN_URL, ask_for=["email", "nickname"], ask_for_optional=["fullname"], extensions=[teams_request]
        )

    @open_id.after_login
    def after_login(resp):
        if SSO_TEAM not in resp.extensions["lp"].is_member:
            flask.abort(403)

        flask.session["openid"] = {
            "identity_url": resp.identity_url,
            "email": resp.email,
        }

        response = flask.make_response(
            flask.redirect(
                open_id.get_next_url(),
                302,
            ),
        )
        return response
