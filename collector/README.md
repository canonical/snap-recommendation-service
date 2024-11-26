# To get a new macaroon

`snapcraft export-login exchange.creds --expires 2025-09-14 --acls package_metrics`

then add the token to .env as MACAROON="<token>", you can do

`sed -i "/^MACAROON=/s/=.*/=\"$(cat exchange.creds)\"/" .env`
