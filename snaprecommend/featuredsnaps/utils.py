from snaprecommend.auth.session import device_gateway
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

    currently_featured_snaps = []

    next = True
    while next:
        featured_snaps = device_gateway.get_featured_snaps(fields=fields)
        currently_featured_snaps.extend(
            featured_snaps.get("_embedded", {}).get("clickindex:package", [])
        )
        next = featured_snaps.get("_links", {}).get("next", False)

    for snap in currently_featured_snaps:
        snap["icon_url"] = get_icon(snap["media"])

    return currently_featured_snaps
