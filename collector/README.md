# To get a new macaroon

`snapcraft export-login exchange.creds --expires 2025-09-14 --acls package_metrics`

then run `python3 scripts/auth.py /path/to/exchange.creds` and add the returned token to .env as `FLASK_SNAPSTORE_MACAROON_KEY`.