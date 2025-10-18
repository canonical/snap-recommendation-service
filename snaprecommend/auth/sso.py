import flask
import logging
import os
from django_openid_auth.teams import TeamsRequest, TeamsResponse
from flask_openid import OpenID
from snaprecommend.auth.macroon import MacaroonRequest, MacaroonResponse
from snaprecommend.auth import authentication
from snaprecommend.auth.session import publisher_gateway
from snaprecommend.auth.constants import (
    DEFAULT_SSO_TEAM,
    LP_CANONICAL_TEAM,
    LP_ADMIN_TEAM,
    SSO_LOGIN_URL,
)

logger = logging.getLogger(__name__)


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
        logger.info(f"Login request started - Method: {flask.request.method}, Remote IP: {flask.request.remote_addr}")

        if authentication.is_authenticated(flask.session):
            next_url = open_id.get_next_url()
            logger.info(f"User already authenticated, redirecting to: {next_url}")
            return flask.redirect(next_url)

        logger.info("User not authenticated, requesting macaroon from dashboard API")
        try:
            root = authentication.request_macaroon()
            logger.info("Successfully obtained macaroon from dashboard API")
        except Exception as api_response_error:
            logger.error(f"Failed to request macaroon: {str(api_response_error)}")
            if hasattr(api_response_error, 'status_code'):
                if api_response_error.status_code == 401:
                    logger.warning("Received 401 from dashboard API, redirecting to logout")
                    return flask.redirect(flask.url_for(".logout"))
                else:
                    logger.error(f"Dashboard API error with status {api_response_error.status_code}")
                    return flask.abort(502, str(api_response_error))
            else:
                logger.error(f"Dashboard API error without status code: {str(api_response_error)}")
                return flask.abort(502, str(api_response_error))

        logger.info("Creating OpenID macaroon request with caveat ID")
        openid_macaroon = MacaroonRequest(caveat_id=authentication.get_caveat_id(root))
        flask.session["macaroon_root"] = root

        teams_request = TeamsRequest(
            query_membership=[SSO_TEAM, LP_CANONICAL_TEAM, LP_ADMIN_TEAM]
        )

        logger.info(f"Initiating OpenID login flow to {SSO_LOGIN_URL}")
        return open_id.try_login(
            SSO_LOGIN_URL,
            ask_for=["email", "nickname"],
            ask_for_optional=["fullname"],
            extensions=[openid_macaroon, teams_request],
        )

    @open_id.after_login
    def after_login(resp):
        logger.info(f"OpenID callback received - Identity: {resp.identity_url}")

        flask.session["macaroon_root"] = flask.session.get("macaroon_root")

        if "macaroon" not in resp.extensions:
            logger.error("No macaroon extension in OpenID response")
            flask.abort(502, "Missing macaroon in OpenID response")

        flask.session["macaroon_discharge"] = resp.extensions["macaroon"].discharge
        logger.info("Macaroon discharge stored in session")

        # Check team membership
        user_teams = resp.extensions.get("lp", {}).is_member if "lp" in resp.extensions else []
        logger.info(f"User teams: {user_teams}")

        if SSO_TEAM not in user_teams:
            logger.warning(f"User {resp.identity_url} is not member of required team: {SSO_TEAM}")
            flask.abort(403)

        logger.info(f"User is member of required team: {SSO_TEAM}")

        # Exchange macaroons for developer token
        logger.info("Exchanging macaroons for developer token")
        try:
            dev_token = publisher_gateway.exchange_dashboard_macaroons(flask.session)
            flask.session["developer_token"] = dev_token
            flask.session["exchanged_developer_token"] = True
            logger.info("Successfully exchanged macaroons for developer token")
        except Exception as exchange_error:
            logger.error(f"Failed to exchange macaroons: {str(exchange_error)}")
            authentication.empty_session(flask.session)
            flask.abort(502, "Failed to exchange macaroons")

        is_admin = LP_ADMIN_TEAM in user_teams
        flask.session["publisher"] = {
            "identity_url": resp.identity_url,
            "nickname": resp.nickname,
            "fullname": resp.fullname,
            "email": resp.email,
            "is_admin": is_admin,
        }

        logger.info(f"Login successful for {resp.email} (admin: {is_admin})")

        next_url = open_id.get_next_url()
        logger.info(f"Redirecting authenticated user to: {next_url}")

        response = flask.make_response(
            flask.redirect(next_url, 302),
        )
        return response
