import flask
from django_openid_auth.teams import TeamsRequest, TeamsResponse
from flask_openid import OpenID
from snaprecommend.auth.macaroon import MacaroonRequest, MacaroonResponse
from snaprecommend.auth import authentication
from snaprecommend.auth.session import dashboard
from snaprecommend.auth.constants import DEFAULT_SSO_TEAM, LP_CANONICAL_TEAM, LP_ADMIN_TEAM, SSO_LOGIN_URL
from snaprecommend.auth.utils import get_stores


def init_sso(app: flask.Flask):
    open_id = OpenID(
        store_factory=lambda: None,
        safe_roots=[],
        extension_responses=[MacaroonResponse, TeamsResponse],
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
            return flask.redirect(open_id.get_next_url())
        try:
            root = authentication.request_macaroon()
        except Exception as api_response_error:
            if api_response_error.status_code == 401:
                return flask.redirect(flask.url_for(".logout"))
            else:
                return flask.abort(502, str(api_response_error))
        openid_macaroon = MacaroonRequest(
            caveat_id=authentication.get_caveat_id(root)
        )
        flask.session["macaroon_root"] = root

        teams_request = TeamsRequest(query_membership=[SSO_TEAM, LP_CANONICAL_TEAM, LP_ADMIN_TEAM])

        return open_id.try_login(
            SSO_LOGIN_URL,
            ask_for=["email", "nickname"],
            ask_for_optional=["fullname"],
            extensions=[openid_macaroon, teams_request],
        )

    @open_id.after_login
    def after_login(resp):
        flask.session["macaroon_discharge"] = resp.extensions["macaroon"].discharge

        if SSO_TEAM not in resp.extensions["lp"].is_member:
            flask.abort(403)

        account = dashboard.get_account(flask.session)
        validation_sets = dashboard.get_validation_sets(flask.session)

        if account:
            is_canonical = LP_CANONICAL_TEAM in resp.extensions["lp"].is_member

            flask.session["publisher"] = {
                "identity_url": resp.identity_url,
                "nickname": account["username"],
                "fullname": account["displayname"],
                "email": account["email"],
                "is_canonical": is_canonical,
                "is_admin": LP_ADMIN_TEAM in resp.extensions["lp"].is_member,
            }

            if get_stores(
                account["stores"], roles=["admin", "review", "view"]
            ):
                flask.session["publisher"]["has_stores"] = (
                    len(dashboard.get_stores(flask.session)) > 0
                )

            flask.session["publisher"]["has_validation_sets"] = (
                validation_sets is not None
                and len(validation_sets["assertions"]) > 0
            )
        else:
            flask.session["publisher"] = {
                "identity_url": resp.identity_url,
                "nickname": resp.nickname,
                "fullname": resp.fullname,
                "image": resp.image,
                "email": resp.email,
            }

        response = flask.make_response(
            flask.redirect(
                open_id.get_next_url(),
                302,
            ),
        )
        return response

