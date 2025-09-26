from snaprecommend.auth.session import device_gateway, api_session
from snaprecommend.utils import get_icon


def get_fetaured_snaps():
    fields = ",".join(
        [
            "package_name",
            "title",
            "summary",
            "architecture",
            "media",
            "developer_name",
            "developer_id",
            "developer_validation",
            "origin",
            "apps",
            "sections",
            "snap_id",
        ]
    )

    featured_snaps = device_gateway.get_featured_snaps(fields=fields, headers={
        "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
        "Pragma": "no-cache",
        "Expires": "0",
    })
    currently_featured_snaps =  featured_snaps.get("_embedded", {}).get("clickindex:package", [])

    for snap in currently_featured_snaps:
        snap["icon_url"] = get_icon(snap["media"])

    return currently_featured_snaps
