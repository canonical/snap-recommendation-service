from snaprecommend.auth.session import device_gateway
from snaprecommend.logic import get_featured_history
from snaprecommend.utils import get_icon


def get_featured_snaps():
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
    currently_featured_snaps = featured_snaps.get("_embedded", {}).get("clickindex:package", [])

    # Attach the recorded selection reason and featured history for each snap.
    snap_ids = [snap["snap_id"] for snap in currently_featured_snaps]
    history_by_snap = get_featured_history(snap_ids)

    for snap in currently_featured_snaps:
        snap["icon_url"] = get_icon(snap["media"])
        events = history_by_snap.get(snap["snap_id"], [])
        snap["featured_history"] = events
        latest = events[0] if events else None
        snap["selection_reason"] = latest["selection_reason"] if latest else None
        snap["is_manual"] = latest["is_manual"] if latest else None

    return currently_featured_snaps
