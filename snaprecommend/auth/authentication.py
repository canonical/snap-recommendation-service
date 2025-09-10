from urllib.parse import urlparse
from pymacaroons import Macaroon
from snaprecommend.auth import utils
from snaprecommend.auth.constants import SSO_LOGIN_URL, PERMISSIONS


def is_authenticated(session):
    return (
        "openid" in session
        and "macaroon_discharge" in session
        and "macaroon_root" in session
    ) or ("openid" in session and "macaroons" in session)


def empty_session(session):
    session.pop("macaroons", None)
    session.pop("macaroon_root", None)
    session.pop("macaroon_discharge", None)
    session.pop("openid", None)


def request_macaroon():
    response = utils.post_macaroon({"permissions": PERMISSIONS})
    return response["macaroon"]


def get_caveat_id(root):
    location = urlparse(SSO_LOGIN_URL).hostname
    (caveat,) = [
        c
        for c in Macaroon.deserialize(root).third_party_caveats()
        if c.location == location
    ]

    return caveat.caveat_id
