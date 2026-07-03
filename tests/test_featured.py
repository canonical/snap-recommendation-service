import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
from sqlalchemy.pool import StaticPool

from snaprecommend import db
from snaprecommend.models import FeaturedHistory
from snaprecommend.logic import record_featured_history, get_featured_history
from snaprecommend.featuredsnaps.api import featured_blueprint
from snaprecommend.featuredsnaps.utils import get_featured_snaps


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite://"
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "poolclass": StaticPool,
        "connect_args": {"check_same_thread": False},
    }
    app.config["TESTING"] = True
    app.secret_key = "test"
    db.init_app(app)
    app.register_blueprint(featured_blueprint, url_prefix="/featured")

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def admin_client(client):
    with client.session_transaction() as sess:
        sess["exchanged_developer_token"] = True
        sess["developer_token"] = "token"
        sess["publisher"] = {
            "is_admin": True,
            "email": "jane@canonical.com",
            "nickname": "jane",
        }
    return client


def test_record_featured_history_manual(app):
    """A manual pick is stored with is_manual=True and the acting user."""
    events = [
        {
            "snap_id": "snap1",
            "selection_reason": {
                "actor": "jane@canonical.com",
                "nickname": "jane",
            },
        }
    ]
    rows = record_featured_history(events, is_manual=True)

    assert len(rows) == 1
    stored = db.session.query(FeaturedHistory).all()
    assert len(stored) == 1
    assert stored[0].snap_id == "snap1"
    assert stored[0].is_manual is True
    assert stored[0].selection_reason["actor"] == "jane@canonical.com"
    assert stored[0].featured_at is not None


def test_record_featured_history_automated(app):
    events = [
        {
            "snap_id": "snap1",
            "selection_reason": {
                "ranking_key": "active_devices",
                "ranking_value": 184213,
            },
        }
    ]
    record_featured_history(events, is_manual=False)

    stored = db.session.query(FeaturedHistory).one()
    assert stored.is_manual is False
    assert stored.selection_reason["ranking_key"] == "active_devices"


def test_manual_and_automated_share_one_shape(app):
    record_featured_history(
        [{"snap_id": "snap1", "selection_reason": {"actor": "a@b.com"}}],
        is_manual=True,
    )
    record_featured_history(
        [{"snap_id": "snap2", "selection_reason": {"ranking_key": "rating"}}],
        is_manual=False,
    )

    rows = db.session.query(FeaturedHistory).all()
    assert len(rows) == 2
    for row in rows:
        assert row.featured_at is not None
        assert isinstance(row.is_manual, bool)
        assert row.selection_reason is not None


def test_get_featured_history_groups_newest_first(app):
    record_featured_history(
        [{"snap_id": "snap1", "selection_reason": {"n": 1}}], is_manual=False
    )
    record_featured_history(
        [
            {"snap_id": "snap1", "selection_reason": {"n": 2}},
            {"snap_id": "snap2", "selection_reason": {"n": 3}},
        ],
        is_manual=True,
    )

    history = get_featured_history(["snap1", "snap2"])

    assert set(history.keys()) == {"snap1", "snap2"}
    assert len(history["snap1"]) == 2
    assert history["snap1"][0]["selection_reason"]["n"] == 2
    assert history["snap1"][0]["is_manual"] is True
    assert history["snap1"][1]["selection_reason"]["n"] == 1
    assert history["snap2"][0]["selection_reason"]["n"] == 3


def test_get_featured_history_empty(app):
    assert get_featured_history([]) == {}


@patch("snaprecommend.featuredsnaps.utils.device_gateway")
def test_get_featured_snaps_attaches_reason_and_history(mock_gateway, app):
    record_featured_history(
        [
            {
                "snap_id": "snap1",
                "selection_reason": {"actor": "jane@canonical.com"},
            }
        ],
        is_manual=True,
    )
    mock_gateway.get_featured_snaps.return_value = {
        "_embedded": {
            "clickindex:package": [
                {
                    "snap_id": "snap1",
                    "media": [
                        {"type": "icon", "url": "http://example.com/i.png"}
                    ],
                },
                {"snap_id": "snap2", "media": []},
            ]
        }
    }

    result = get_featured_snaps()
    by_id = {snap["snap_id"]: snap for snap in result}

    assert by_id["snap1"]["is_manual"] is True
    assert by_id["snap1"]["selection_reason"]["actor"] == "jane@canonical.com"
    assert len(by_id["snap1"]["featured_history"]) == 1
    assert by_id["snap1"]["icon_url"] == "http://example.com/i.png"

    assert by_id["snap2"]["selection_reason"] is None
    assert by_id["snap2"]["is_manual"] is None
    assert by_id["snap2"]["featured_history"] == []


@patch("snaprecommend.auth.authentication.is_authenticated", return_value=True)
@patch("snaprecommend.featuredsnaps.api.publisher_gateway")
@patch("snaprecommend.featuredsnaps.api.device_gateway")
def test_post_featured_records_manual_history(
    mock_device, mock_publisher, _mock_auth, admin_client
):
    mock_device.get_featured_snaps.return_value = {
        "_embedded": {"clickindex:package": []},
        "_links": {},
    }
    update_response = MagicMock()
    update_response.status_code = 201
    mock_publisher.update_featured_snaps.return_value = update_response

    response = admin_client.post("/featured/", data={"snaps": "snap1,snap2"})

    assert response.status_code == 200
    assert response.get_json()["success"] is True
    mock_publisher.update_featured_snaps.assert_called_once()

    rows = db.session.query(FeaturedHistory).all()
    assert len(rows) == 2
    assert {r.snap_id for r in rows} == {"snap1", "snap2"}
    assert all(r.is_manual is True for r in rows)
    assert all(
        r.selection_reason["actor"] == "jane@canonical.com" for r in rows
    )
    assert all(r.selection_reason["nickname"] == "jane" for r in rows)


@patch("snaprecommend.featuredsnaps.api.record_featured_history")
@patch("snaprecommend.auth.authentication.is_authenticated", return_value=True)
@patch("snaprecommend.featuredsnaps.api.publisher_gateway")
@patch("snaprecommend.featuredsnaps.api.device_gateway")
def test_post_featured_reverts_store_when_history_fails(
    mock_device, mock_publisher, _mock_auth, mock_record, admin_client
):
    mock_device.get_featured_snaps.return_value = {
        "_embedded": {"clickindex:package": [{"snap_id": "old1"}]},
        "_links": {},
    }
    delete_response = MagicMock()
    delete_response.status_code = 201
    mock_publisher.delete_featured_snaps.return_value = delete_response
    update_response = MagicMock()
    update_response.status_code = 201
    mock_publisher.update_featured_snaps.return_value = update_response

    mock_record.side_effect = Exception("db down")

    response = admin_client.post("/featured/", data={"snaps": "snap1,snap2"})

    assert response.status_code == 500
    assert response.get_json()["success"] is False

    assert mock_publisher.update_featured_snaps.call_count == 2
    revert_call = mock_publisher.update_featured_snaps.call_args_list[-1]
    assert revert_call.args[1] == {"packages": ["old1"]}

    assert db.session.query(FeaturedHistory).count() == 0
