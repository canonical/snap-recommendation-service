import pymacaroons
import base64
import json
import requests

EXCHANGE_DASHBOARD_ENDPOINT = (
    "https://api.charmhub.io/v1/tokens/dashboard/exchange"
)


def get_auth_header(token):

    exchange_value = json.loads(base64.b64decode(token).decode("utf-8"))

    root_val = exchange_value["v"]["r"]
    discharge_val = exchange_value["v"]["d"]

    root = pymacaroons.Macaroon.deserialize(root_val)
    discharge = pymacaroons.Macaroon.deserialize(discharge_val)
    bound = root.prepare_for_request(discharge)
    return "Macaroon root={}, discharge={}".format(
        root.serialize(), bound.serialize()
    )


def get_auth_token_from_file(file):
    with open(file, "r") as f:
        token = f.read()
    return token


def exchange_dashboard_macaroons(token):
    headers = {
        "Authorization": get_auth_header(token),
        "Content-Type": "application/json",
    }

    response = requests.post(
        EXCHANGE_DASHBOARD_ENDPOINT,
        headers=headers,
        json={"client-description": "snaprecommend"},
    )

    if response.status_code != 200:
        raise Exception(
            "Failed to exchange macaroons: {}".format(response.text)
        )

    return response.json()["macaroon"]


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python auth.py <file>")
        sys.exit(1)
    file = sys.argv[1]

    with open(file, "r") as f:
        token = f.read()

    if not token:
        print("Invalid token, check collector/README.md for more info")
        sys.exit(1)

    exchanged_macaroons = exchange_dashboard_macaroons(token)
    print("Token: {}".format(exchanged_macaroons))
