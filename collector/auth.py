import pymacaroons
import base64
import json


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
