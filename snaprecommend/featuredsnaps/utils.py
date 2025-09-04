from snaprecommend.auth.session import device_gateway 


def get_icon(media):
    icons = [m["url"] for m in media if m["type"] == "icon"]
    if len(icons) > 0:
        return icons[0]
    return ""


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

    for snap in featured_snaps:
        snap["icon_url"] = get_icon(snap["media"])
    return featured_snaps


