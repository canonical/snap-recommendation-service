from snaprecommend.models import Snap


def mock_snap() -> Snap:
    return Snap(
        snap_id=1,
        name="Snap1",
        title="Mock Title 1",
        version="1.0.0",
        summary="This is a summary of Snap1.",
        description="Detailed description of Snap1.",
        icon="https://example.com/snap1/icon.png",
        website="https://example.com/snap1",
        contact="support@example.com",
        publisher="Mock Publisher 1",
        revision=42,
        links=["https://example.com/snap1/docs"],
        media=["https://example.com/snap1/media.png"],
        developer_validation=True,
        license="MIT",
        last_updated="2024-02-17T12:00:00Z",
        active_devices=1000,
        reaches_min_threshold=True,
    )
