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

    # TODO add pagination
    featured_snaps_response = device_gateway.get_featured_snaps(fields=fields)
    featured_snaps = featured_snaps_response.get("_embedded", {}).get("clickindex:package", [])
    print("featured snapcount:", len(featured_snaps))
    for snap in featured_snaps:
        snap["icon_url"] = get_icon(snap["media"])
    return featured_snaps
