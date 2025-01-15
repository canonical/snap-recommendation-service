import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
from snaprecommend.api import api_blueprint, get_top_snaps_by_field, format_response
from snaprecommend.models import Snap


@pytest.fixture
def app():
    """
    Create a Flask application for testing.
    """
    app = Flask(__name__)
    app.register_blueprint(api_blueprint)
    return app


@pytest.fixture
def client(app):
    """
    Provide a test client for the Flask app.
    """
    return app.test_client()


@patch("snaprecommend.api.get_top_snaps_by_field")
def test_popular_endpoint(mock_get_top_snaps_by_field, client):
    mock_snaps = [
        Snap(snap_id=3, name="Snap3"),
        Snap(snap_id=4, name="Snap4"),
    ]
    mock_get_top_snaps_by_field.return_value = mock_snaps

    response = client.get("/popular")
    assert response.status_code == 200
    assert response.json == [
        {"snap_id": 3, "name": "Snap3", "rank": 1},
        {"snap_id": 4, "name": "Snap4", "rank": 2},
    ]
    mock_get_top_snaps_by_field.assert_called_once_with("popularity_score")


@patch("snaprecommend.api.get_top_snaps_by_field")
def test_recent_endpoint(mock_get_top_snaps_by_field, client):
    mock_snaps = [
        Snap(snap_id=3, name="Snap3"),
        Snap(snap_id=4, name="Snap4"),
    ]
    mock_get_top_snaps_by_field.return_value = mock_snaps

    response = client.get("/recent")
    assert response.status_code == 200
    assert response.json == [
        {"snap_id": 3, "name": "Snap3", "rank": 1},
        {"snap_id": 4, "name": "Snap4", "rank": 2},
    ]
    mock_get_top_snaps_by_field.assert_called_once_with("recency_score")


@patch("snaprecommend.api.get_top_snaps_by_field")
def test_trending_endpoint(mock_get_top_snaps_by_field, client):
    mock_snaps = [
        Snap(snap_id=5, name="Snap5"),
        Snap(snap_id=6, name="Snap6"),
    ]
    mock_get_top_snaps_by_field.return_value = mock_snaps

    response = client.get("/trending")
    assert response.status_code == 200
    assert response.json == [
        {"snap_id": 5, "name": "Snap5", "rank": 1},
        {"snap_id": 6, "name": "Snap6", "rank": 2},
    ]
    mock_get_top_snaps_by_field.assert_called_once_with("trending_score")


@patch("snaprecommend.db.session.query")
def test_get_top_snaps_by_field(mock_query):
    mock_snap_query = MagicMock()
    mock_query.return_value = mock_snap_query

    mock_snap_query.filter.return_value = mock_snap_query
    mock_snap_query.join.return_value = mock_snap_query
    mock_snap_query.order_by.return_value = mock_snap_query
    mock_snap_query.limit.return_value = [Snap(snap_id=7, name="Snap7")]

    result = get_top_snaps_by_field("popularity_score", limit=1)

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
