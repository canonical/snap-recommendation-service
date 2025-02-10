import pytest
import requests
from datetime import datetime
from unittest.mock import MagicMock, patch
from collector.collect import (
    get_snap_page,
    upsert_snap,
    bulk_upsert_snaps,
    collect_initial_snap_data,
)
from sqlalchemy.orm import Session


@pytest.fixture
def mock_session():
    """Fixture to create a mocked SQLAlchemy session."""
    return MagicMock(spec=Session)


@pytest.fixture
def sample_snap():
    """Fixture to provide a sample snap."""
    return {
        "snap_id": "snap1",
        "package_name": "test-snap",
        "last_updated": "2024-12-16 09:32:04.767",
        "summary": "Test summary",
        "description": "Test description",
        "title": "Test Snap",
        "version": "1.0",
        "publisher": "Canonical",
        "revision": 1,
        "links": {
            "website": ["https://example.com"],
            "contact": ["contact@example.com"],
        },
        "media": [{"type": "icon", "url": "https://example.com/icon.png"}],
        "developer_validation": True,
        "license": "MIT",
    }


@patch("collector.collect.requests.get")
def test_get_snap_page(mock_get):
    """Test fetching a page of snaps."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "_embedded": {
            "clickindex:package": [
                {"snap_id": "snap1", "links": {}, "media": []},
                {"snap_id": "snap2", "links": {}, "media": []},
            ]
        },
        "_links": {"next": {"href": "next_page"}},
    }
    mock_get.return_value = mock_response

    snaps, has_next = get_snap_page(1)

    assert len(snaps) == 2
    assert has_next is True
    mock_get.assert_called_once_with(
        "http://api.snapcraft.io/api/v1/snaps/search?fields=snap_id,package_name,last_updated,summary,description,title,version,publisher,revision,links,media,developer_validation,license&confinement=strict,classic&page=1"
    )


@patch("collector.collect.requests.get")
def test_no_next_page(mock_get):
    mock_response = {"_embedded": {"clickindex:package": []}, "_links": {}}
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = mock_response

    snaps, has_next = get_snap_page(1)

    assert snaps == []
    assert has_next is False


@patch("collector.collect.requests.get")
def test_api_error(mock_get):
    mock_get.return_value.status_code = 500
    mock_get.side_effect = requests.exceptions.HTTPError(
        "Internal Server Error"
    )

    with pytest.raises(requests.exceptions.HTTPError):
        get_snap_page(1)


def test_upsert_snap(mock_session, sample_snap):
    """Test upserting a single snap."""
    upsert_snap(mock_session, sample_snap)

    mock_session.merge.assert_called_once()
    snap_instance = mock_session.merge.call_args[0][0]
    assert snap_instance.snap_id == sample_snap["snap_id"]
    assert snap_instance.name == sample_snap["package_name"]
    assert snap_instance.website == sample_snap["links"]["website"][0]
    assert snap_instance.contact == sample_snap["links"]["contact"][0]


@patch("collector.collect.insert")
def test_bulk_upsert_snaps(mock_insert, mock_session, sample_snap):
    """Test bulk upsert of snaps."""
    mock_stmt = MagicMock()
    mock_insert.return_value.values.return_value.on_conflict_do_update.return_value = (
        mock_stmt
    )

    bulk_upsert_snaps(mock_session, [sample_snap])

    mock_insert.assert_called_once()
    mock_insert.return_value.values.assert_called_once_with(
        [
            {
                "snap_id": sample_snap["snap_id"],
                "name": sample_snap["package_name"],
                "icon": "https://example.com/icon.png",
                "summary": sample_snap["summary"],
                "description": sample_snap["description"],
                "title": sample_snap["title"],
                "website": "https://example.com",
                "version": sample_snap["version"],
                "publisher": sample_snap["publisher"],
                "revision": sample_snap["revision"],
                "contact": "contact@example.com",
                "links": sample_snap["links"],
                "media": sample_snap["media"],
                "developer_validation": sample_snap["developer_validation"],
                "license": sample_snap["license"],
                "last_updated": datetime.fromisoformat(
                    sample_snap["last_updated"]
                ),
            }
        ]
    )
    mock_session.execute.assert_called_once_with(mock_stmt)


@patch("collector.collect.insert_snaps", return_value=5)
@patch("collector.collect.logger")
def test_collect_initial_snap_data(mock_logger, mock_insert_snaps):
    """Test the entire snap collection process."""
    collect_initial_snap_data()

    mock_insert_snaps.assert_called_once()
    mock_logger.info.assert_any_call(
        "Starting the snap data ingestion process."
    )
    mock_logger.info.assert_any_call(
        "Snap data ingestion process completed. 5 snaps inserted."
    )
