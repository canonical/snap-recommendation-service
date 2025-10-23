import flask
import logging
import os
from django_openid_auth.teams import TeamsRequest, TeamsResponse
from flask_openid import OpenID
from snaprecommend.auth.macaroon import MacaroonRequest, MacaroonResponse
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
        logger.info("=== LOGIN ENDPOINT CALLED ===")
        logger.info(f"Request method: {flask.request.method}")
        logger.info(f"Request path: {flask.request.path}")
        logger.info(f"Request headers: {dict(flask.request.headers)}")

        if authentication.is_authenticated(flask.session):
            logger.info("User already authenticated, redirecting")
            return flask.redirect(open_id.get_next_url())

        logger.info("User not authenticated, requesting macaroon from dashboard API")
        try:
            root = authentication.request_macaroon()
            logger.info("Successfully received macaroon from dashboard API")
        except Exception as api_response_error:
            logger.error(f"Failed to request macaroon: {type(api_response_error).__name__}")
            logger.error(f"Error message: {str(api_response_error)}")
            logger.error(f"Error details: {repr(api_response_error)}", exc_info=True)

            # Check if the exception has a status_code attribute
            if hasattr(api_response_error, 'status_code'):
                logger.error(f"API response status code: {api_response_error.status_code}")
                if api_response_error.status_code == 401:
                    logger.info("Received 401, redirecting to logout")
                    return flask.redirect(flask.url_for(".logout"))
                else:
                    logger.error(f"Aborting with 502: {str(api_response_error)}")
                    return flask.abort(502, str(api_response_error))
            else:
                logger.error("Exception has no status_code attribute - likely a connection or proxy error")
                logger.error(f"Aborting with 502: {str(api_response_error)}")
                return flask.abort(502, str(api_response_error))

        logger.info("Creating OpenID macaroon request")
        try:
            openid_macaroon = MacaroonRequest(caveat_id=authentication.get_caveat_id(root))
            logger.info("Successfully created OpenID macaroon request")
        except Exception as e:
            logger.error(f"Failed to create OpenID macaroon: {type(e).__name__}: {str(e)}", exc_info=True)
            return flask.abort(500, f"Failed to create OpenID macaroon: {str(e)}")

        flask.session["macaroon_root"] = root

        teams_request = TeamsRequest(
            query_membership=[SSO_TEAM, LP_CANONICAL_TEAM, LP_ADMIN_TEAM]
        )

        logger.info(f"Initiating OpenID login flow to {SSO_LOGIN_URL}")
        try:
            return open_id.try_login(
                SSO_LOGIN_URL,
                ask_for=["email", "nickname"],
                ask_for_optional=["fullname"],
                extensions=[openid_macaroon, teams_request],
            )
        except Exception as e:
            logger.error(f"Failed in try_login: {type(e).__name__}: {str(e)}", exc_info=True)
            return flask.abort(500, f"OpenID login failed: {str(e)}")

    @open_id.after_login
    def after_login(resp):
        flask.session["macaroon_root"] = flask.session.get("macaroon_root")
        flask.session["macaroon_discharge"] = resp.extensions["macaroon"].discharge

        if SSO_TEAM not in resp.extensions["lp"].is_member:
            flask.abort(403)

        try:
            dev_token = publisher_gateway.exchange_dashboard_macaroons(flask.session)
            flask.session["developer_token"] = dev_token
            flask.session["exchanged_developer_token"] = True
        except Exception:
            authentication.empty_session(flask.session)
            flask.abort(502, "Failed to exchange macaroons")

        flask.session["publisher"] = {
            "identity_url": resp.identity_url,
            "nickname": resp.nickname,
            "fullname": resp.fullname,
            "email": resp.email,
            "is_admin": LP_ADMIN_TEAM in resp.extensions["lp"].is_member,
        }

        response = flask.make_response(
            flask.redirect(
                open_id.get_next_url(),
                302,
            ),
        )
        return response
