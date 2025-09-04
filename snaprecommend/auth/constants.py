import os

PERMISSIONS = [
    "edit_account",
    "package_access",
    "package_manage",
    "package_metrics",
    "package_register",
    "package_release",
    "package_update",
    "package_upload_request",
    "store_admin",
]


SSO_LOGIN_URL =  os.getenv("LOGIN_URL", "https://login.ubuntu.com")
DEFAULT_SSO_TEAM = "canonical-webmonkeys"

LP_CANONICAL_TEAM = "canonical"
LP_ADMIN_TEAM = "featured-packages-editors"

SNAPSTORE_DASHBOARD_API_URL = os.getenv(
    "SNAPSTORE_DASHBOARD_API_URL", "https://dashboard.snapcraft.io/"
)

HEADERS = {
    "Accept": "application/json, application/hal+json",
    "Content-Type": "application/json",
    "Cache-Control": "no-cache",
}