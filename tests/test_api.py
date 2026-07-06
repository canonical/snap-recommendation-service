from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from snaprecommend.api import (
    api_blueprint,
    format_response,
    get_category_top_snaps,
    trigger_featured_selection,
    update_featured_settings,
)
from snaprecommend.featuredsnaps.api import post_featured_snaps
from snaprecommend.models import EditorialSlice, RecommendationCategory, Snap
from tests.mock_data import mock_snap


@pytest.fixture
def app():
    """
    Create a Flask application for testing.
    """
    app = Flask(__name__)
    app.secret_key = "test"
    app.register_blueprint(api_blueprint)
    app.app_context().push()
    return app


@pytest.fixture
def client(app):
    """
    Provide a test client for the Flask app.
    """
    return app.test_client()


@patch("snaprecommend.db.session.query")
def test_get_category_top_snaps(mock_query):
    mock_snap_query = MagicMock()
    mock_query.return_value = mock_snap_query

    mock_snap_query.filter.return_value = mock_snap_query
    mock_snap_query.join.return_value = mock_snap_query
    mock_snap_query.order_by.return_value = mock_snap_query
    mock_snap_query.limit.return_value = mock_snap_query
    mock_snap_query.all.return_value = [Snap(snap_id=7, name="Snap7")]

    result = get_category_top_snaps("popular", limit=1)

    assert len(result) == 1
    assert result[0].snap_id == 7
    mock_query.assert_called_once()


def test_format_response():
    snap1 = mock_snap()
    snap2 = mock_snap()
    snap2.snap_id = 2
    snap2.title = "Mock Title 2"
    snap2.name = "Snap2"
    snap2.version = "2.1.0"
    mock_snaps = [snap1, snap2]
    response = format_response(mock_snaps)

    assert response == [
        {
            "snap_id": 1,
            "rank": 1,
            "details": {
                "snap_id": 1,
                "title": "Mock Title 1",
                "name": "Snap1",
                "version": "1.0.0",
                "summary": "This is a summary of Snap1.",
                "description": "Detailed description of Snap1.",
                "icon": "https://example.com/snap1/icon.png",
                "website": "https://example.com/snap1",
                "contact": "support@example.com",
                "publisher": "Mock Publisher 1",
                "revision": 42,
                "links": ["https://example.com/snap1/docs"],
                "media": ["https://example.com/snap1/media.png"],
                "developer_validation": True,
                "license": "MIT",
                "last_updated": "2024-02-17T12:00:00Z",
            },
        },
        {
            "snap_id": 2,
            "rank": 2,
            "details": {
                "snap_id": 2,
                "title": "Mock Title 2",
                "name": "Snap2",
                "version": "2.1.0",
                "summary": "This is a summary of Snap1.",
                "description": "Detailed description of Snap1.",
                "icon": "https://example.com/snap1/icon.png",
                "website": "https://example.com/snap1",
                "contact": "support@example.com",
                "publisher": "Mock Publisher 1",
                "revision": 42,
                "links": ["https://example.com/snap1/docs"],
                "media": ["https://example.com/snap1/media.png"],
                "developer_validation": True,
                "license": "MIT",
                "last_updated": "2024-02-17T12:00:00Z",
            },
        },
    ]


@patch("snaprecommend.api.RecommendationCategory.query")
@patch("snaprecommend.api.get_category_top_snaps")
def test_category_endpoint(mock_get_category_top_snaps, mock_query, client):
    mock_category = MagicMock()
    mock_category.id = "test_id"
    mock_category.name = "Test Category"
    mock_category.description = "Test Description"
    mock_query.filter_by.return_value.first.return_value = mock_category

    mock_snaps = [
        mock_snap(),
    ]
    mock_get_category_top_snaps.return_value = mock_snaps

    response = client.get("/category/popular")
    assert response.status_code == 200
    assert response.json == [
        {
            "snap_id": 1,
            "rank": 1,
            "details": {
                "snap_id": 1,
                "title": "Mock Title 1",
                "name": "Snap1",
                "version": "1.0.0",
                "summary": "This is a summary of Snap1.",
                "description": "Detailed description of Snap1.",
                "icon": "https://example.com/snap1/icon.png",
                "website": "https://example.com/snap1",
                "contact": "support@example.com",
                "publisher": "Mock Publisher 1",
                "revision": 42,
                "links": ["https://example.com/snap1/docs"],
                "media": ["https://example.com/snap1/media.png"],
                "developer_validation": True,
                "license": "MIT",
                "last_updated": "2024-02-17T12:00:00Z",
            },
        },
    ]
    mock_query.filter_by.assert_called_once_with(id="popular")
    mock_get_category_top_snaps.assert_called_once_with("popular")


@patch("snaprecommend.api.RecommendationCategory.query")
def test_category_not_found(mock_query, client, app):
    with app.app_context():
        mock_query.filter_by.return_value.first.return_value = None

        response = client.get("/category/nonexistent_id")
        assert response.status_code == 404
        assert response.json == {"error": "Category not found"}
        mock_query.filter_by.assert_called_once_with(id="nonexistent_id")


@patch("snaprecommend.api.get_all_categories")
def test_categories_endpoint(mock_get_all_categories, client):
    mock_categories = [
        RecommendationCategory(
            id="mock-category",
            name="Category 1",
            description="Description 1",
        ),
        RecommendationCategory(
            id="mock2",
            name="Category 2",
            description="Description 2",
        ),
    ]
    mock_get_all_categories.return_value = mock_categories

    response = client.get("/categories")
    assert response.status_code == 200
    assert response.json == [
        {
            "id": "mock-category",
            "name": "Category 1",
            "description": "Description 1",
        },
        {"id": "mock2", "name": "Category 2", "description": "Description 2"},
    ]
    mock_get_all_categories.assert_called_once()


@patch("snaprecommend.api.get_all_slices")
def test_slices_endpoint(mock_get_all_slices, client):
    mock_slices = [
        EditorialSlice(
            id="slice1",
            name="Slice 1",
            description="Description 1",
        ),
        EditorialSlice(
            id="slice2", name="Slice 2", description="Description 2"
        ),
    ]
    mock_get_all_slices.return_value = mock_slices

    response = client.get("/slices")
    assert response.status_code == 200
    assert response.json == [
        {
            "id": "slice1",
            "name": "Slice 1",
            "description": "Description 1",
        },
        {
            "id": "slice2",
            "name": "Slice 2",
            "description": "Description 2",
        },
    ]
    mock_get_all_slices.assert_called_once()


@patch("snaprecommend.api.EditorialSlice.query")
@patch("snaprecommend.api.get_slice_snaps")
def test_slice_endpoint(mock_get_slice_snaps, mock_query, client):
    mock_slice = EditorialSlice(
        id="slice1", name="Slice 1", description="Description 1"
    )
    mock_query.filter_by.return_value.first.return_value = mock_slice

    mock_snaps = [mock_snap()]
    mock_get_slice_snaps.return_value = mock_snaps

    response = client.get("/slice/slice1")
    assert response.status_code == 200
    assert response.json == {
        "slice": {
            "id": "slice1",
            "name": "Slice 1",
            "description": "Description 1",
        },
        "snaps": [
            {
                "snap_id": 1,
                "title": "Mock Title 1",
                "name": "Snap1",
                "version": "1.0.0",
                "summary": "This is a summary of Snap1.",
                "description": "Detailed description of Snap1.",
                "icon": "https://example.com/snap1/icon.png",
                "website": "https://example.com/snap1",
                "contact": "support@example.com",
                "publisher": "Mock Publisher 1",
                "revision": 42,
                "links": ["https://example.com/snap1/docs"],
                "media": ["https://example.com/snap1/media.png"],
                "developer_validation": True,
                "license": "MIT",
                "last_updated": "2024-02-17T12:00:00Z",
            }
        ],
    }
    mock_query.filter_by.assert_called_once_with(id="slice1")
    mock_get_slice_snaps.assert_called_once_with("slice1")


@patch("snaprecommend.api.EditorialSlice.query")
def test_slice_not_found(mock_query, client):
    mock_query.filter_by.return_value.first.return_value = None

    response = client.get("/slice/nonexistent_id")
    assert response.status_code == 404
    assert response.json == {"error": "Slice not found"}
    mock_query.filter_by.assert_called_once_with(id="nonexistent_id")


@patch("snaprecommend.api.Snap.query")
def test_stats_endpoint(mock_query, client):
    mock_query.count.return_value = 100

    mock_filter = MagicMock()
    mock_filter.count.side_effect = [5, 20]  # new_today, updated_today
    mock_query.filter.return_value = mock_filter

    response = client.get("/stats")
    assert response.status_code == 200
    assert response.json == {
        "total_tracked": 100,
        "new_today": 5,
        "updated_today": 20,
    }


@patch("snaprecommend.api.Snap.query")
def test_stats_endpoint_empty(mock_query, client):
    mock_query.count.return_value = 0

    mock_filter = MagicMock()
    mock_filter.count.side_effect = [0, 0]
    mock_query.filter.return_value = mock_filter

    response = client.get("/stats")
    assert response.status_code == 200
    assert response.json == {
        "total_tracked": 0,
        "new_today": 0,
        "updated_today": 0,
    }


def test_trigger_featured_selection_rejects_non_object_payload(app):
    raw_view = trigger_featured_selection.__wrapped__.__wrapped__
    with app.test_request_context(
        "/featured/select",
        method="POST",
        json=["not", "an", "object"],
    ):
        response, status = raw_view()

    assert status == 400
    assert response.get_json()["message"] == "Request body must be a JSON object."


def test_trigger_featured_selection_rejects_non_boolean_force(app):
    raw_view = trigger_featured_selection.__wrapped__.__wrapped__
    with app.test_request_context(
        "/featured/select",
        method="POST",
        json={"force": "false"},
    ):
        response, status = raw_view()

    assert status == 400
    assert response.get_json()["message"] == "'force' must be a JSON boolean."


def test_update_featured_settings_rejects_non_object_payload(app):
    raw_view = update_featured_settings.__wrapped__.__wrapped__
    with app.test_request_context(
        "/featured/settings",
        method="PATCH",
        json=[{"featured_update_interval_days": 30}],
    ):
        response, status = raw_view()

    assert status == 400
    assert response.get_json()["message"] == "Request body must be a JSON object."


def test_update_featured_settings_rejects_invalid_range(app):
    raw_view = update_featured_settings.__wrapped__.__wrapped__
    with app.test_request_context(
        "/featured/settings",
        method="PATCH",
        json={"featured_update_interval_days": 0},
    ):
        response, status = raw_view()

    assert status == 400
    assert "between 1 and 3650" in response.get_json()["message"]


@patch("snaprecommend.featuredsnaps.api.acquire_featured_selection_lock")
def test_post_featured_snaps_rejects_when_lock_busy(mock_acquire_lock, app):
    mock_acquire_lock.return_value = False
    raw_view = post_featured_snaps.__wrapped__.__wrapped__.__wrapped__

    with app.test_request_context(
        "/",
        method="POST",
        data={"snaps": "snap-a,snap-b"},
    ):
        response = raw_view()

    assert response.status_code == 409
    assert response.get_json()["message"] == "Featured update already in progress. Please retry."


@patch("snaprecommend.featuredsnaps.api.release_featured_selection_lock")
@patch("snaprecommend.featuredsnaps.api.record_featured_history")
@patch("snaprecommend.featuredsnaps.api.publisher_gateway")
@patch("snaprecommend.featuredsnaps.api.device_gateway")
@patch("snaprecommend.featuredsnaps.api.acquire_featured_selection_lock")
def test_post_featured_snaps_uses_shared_lock_for_store_and_history(
    mock_acquire_lock,
    mock_device_gateway,
    mock_publisher_gateway,
    mock_record_featured_history,
    mock_release_lock,
    app,
):
    mock_acquire_lock.return_value = True
    mock_device_gateway.get_featured_snaps.return_value = {
        "_embedded": {"clickindex:package": [{"snap_id": "existing"}]},
        "_links": {},
    }

    delete_response = MagicMock()
    delete_response.status_code = 201
    update_response = MagicMock()
    update_response.status_code = 201
    mock_publisher_gateway.delete_featured_snaps.return_value = delete_response
    mock_publisher_gateway.update_featured_snaps.return_value = update_response

    raw_view = post_featured_snaps.__wrapped__.__wrapped__.__wrapped__
    with app.test_request_context(
        "/",
        method="POST",
        data={"snaps": "snap-a,snap-b"},
    ):
        from flask import session
        session["developer_token"] = "token"
        session["publisher"] = {
            "email": "admin@example.com",
            "nickname": "admin",
        }
        response = raw_view()

    assert response.status_code == 200
    mock_acquire_lock.assert_called_once_with()
    mock_release_lock.assert_called_once_with()
    mock_record_featured_history.assert_called_once()
