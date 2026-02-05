#!/usr/bin/env python3
# Copyright 2025 Ubuntu
# See LICENSE file for licensing details.

"""Flask Charm entrypoint."""

import logging
import typing

import ops

import paas_charm.flask

logger = logging.getLogger(__name__)


class SnaprecommendCharm(paas_charm.flask.Charm):
    """Flask Charm service."""
    # Ensure the Pebble service is named 'flask' as expected by the framework.
    # Prevents KeyError('flask') during flask-app-pebble-ready.
    workload_service_name = "flask"

    def __init__(self, *args: typing.Any) -> None:
        """Initialize the instance.

        Args:
            args: passthrough to CharmBase.
        """
        super().__init__(*args)


if __name__ == "__main__":
    ops.main(SnaprecommendCharm)
