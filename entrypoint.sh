#!/bin/sh
set -e

if [ -n "$POSTGRESQL_DB_CONNECT_STRING" ]; then
	python3 migrate.py
fi

exec "$@"
