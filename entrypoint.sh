#!/bin/sh
set -e

python3 migrate.py

exec "$@"