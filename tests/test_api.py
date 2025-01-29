import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
from snaprecommend.api import (
    api_blueprint,
    get_category_top_snaps,
    format_response,
)
from snaprecommend.models import Snap


@pytest.fixture
def app():
    """
    Create a Flask application for testing.
    """
    app = Flask(__name__)
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
    mock_snaps = [
        Snap(snap_id=1, name="Snap1"),
        Snap(snap_id=2, name="Snap2"),
    ]
    response = format_response(mock_snaps)

    assert response == [
        {"snap_id": 1, "name": "Snap1", "rank": 1},
        {"snap_id": 2, "name": "Snap2", "rank": 2},
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
        Snap(snap_id=1, name="Snap1"),
        Snap(snap_id=2, name="Snap2"),
    ]
    mock_get_category_top_snaps.return_value = mock_snaps

    response = client.get("/category/popular")
    assert response.status_code == 200
    assert response.json == [
        {"snap_id": 1, "name": "Snap1", "rank": 1},
        {"snap_id": 2, "name": "Snap2", "rank": 2},
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
