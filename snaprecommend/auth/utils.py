from snaprecommend.auth.session import api_session
from snaprecommend.auth.constants import SNAPSTORE_DASHBOARD_API_URL, HEADERS, SSO_LOGIN_URL


def process_response(response):
    if not response.ok:
        raise Exception("Unknown error from api", response.status_code)

    try:
        body = response.json()
    except Exception as error:
        api_error_exception = Exception(
            "JSON decoding failed: {}".format(error)
        )
        raise api_error_exception

    return body


def post_macaroon(json):
    url = "".join([SNAPSTORE_DASHBOARD_API_URL, "dev/api/acl/"])
    response = api_session.post(url=url, headers=HEADERS, json=json)

    return process_response(response)


def get_refreshed_discharge(json):
    url = "".join([SSO_LOGIN_URL, "/api/v2/tokens/refresh"])
    response = api_session.post(url=url, headers=HEADERS, json=json)

    return process_response(response)


def get_stores(stores, roles):
    """Get list of stores where the user has the specified roles
    :param stores: The account stores
    :param roles: The requested roles to filter
    :return: A list of stores
    """
    user_stores = []

    for store in stores:
        if not set(roles).isdisjoint(store["roles"]):
            user_stores.append(store)

    return user_stores
