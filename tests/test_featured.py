import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from flask import Flask
from sqlalchemy.pool import StaticPool

from snaprecommend import db
from snaprecommend.models import FeaturedHistory, Snap
from snaprecommend.logic import (
    record_featured_history,
    get_latest_featured_events,
    get_featured_history,
)
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


def test_get_latest_featured_events_returns_newest(app):
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

    latest = get_latest_featured_events(["snap1", "snap2"])

    assert set(latest.keys()) == {"snap1", "snap2"}
    assert latest["snap1"]["selection_reason"]["n"] == 2
    assert latest["snap1"]["is_manual"] is True
    assert latest["snap2"]["selection_reason"]["n"] == 3


def test_get_latest_featured_events_empty(app):
    assert get_latest_featured_events([]) == {}


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
    assert by_id["snap1"]["featured_at"] is not None
    assert by_id["snap1"]["icon_url"] == "http://example.com/i.png"

    assert by_id["snap2"]["selection_reason"] is None
    assert by_id["snap2"]["is_manual"] is None
    assert by_id["snap2"]["featured_at"] is None


@patch("snaprecommend.auth.authentication.is_authenticated", return_value=True)
@patch("snaprecommend.logic.publisher_gateway")
@patch("snaprecommend.logic.device_gateway")
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
@patch("snaprecommend.logic.publisher_gateway")
@patch("snaprecommend.logic.device_gateway")
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


def _make_snap(snap_id: str, **overrides) -> Snap:
    fields = {
        "snap_id": snap_id,
        "title": "Multipass",
        "name": "multipass",
        "version": "1.0",
        "summary": "Ubuntu VMs on demand.",
        "description": "Ubuntu VMs on demand for any workstation.",
        "icon": "https://example.com/multipass.png",
        "publisher": "Canonical",
        "revision": 1,
        "links": {},
        "media": [],
        "developer_validation": "starred",
        "license": "GPL-3.0",
        "last_updated": datetime(2026, 8, 1),
    }
    fields.update(overrides)
    return Snap(**fields)


def test_history_records_snap_details(app):
    """Snap details are copied onto the row at write time."""
    db.session.add(_make_snap("snap1"))
    db.session.commit()

    record_featured_history([{"snap_id": "snap1"}], is_manual=False)

    row = db.session.query(FeaturedHistory).one()
    assert row.title == "Multipass"
    assert row.name == "multipass"
    assert row.publisher == "Canonical"
    assert row.icon == "https://example.com/multipass.png"


def test_history_survives_snap_deletion(app):
    """A deleted snap keeps its name, timestamp and reason in the history."""
    db.session.add(_make_snap("snap1"))
    db.session.commit()

    record_featured_history(
        [{"snap_id": "snap1", "selection_reason": {"role": "top-3"}}],
        is_manual=False,
    )

    db.session.delete(db.session.query(Snap).filter_by(snap_id="snap1").one())
    db.session.commit()

    history = get_featured_history(["snap1"])
    assert len(history["snap1"]) == 1

    event = history["snap1"][0]
    assert event["title"] == "Multipass"
    assert event["name"] == "multipass"
    assert event["selection_reason"] == {"role": "top-3"}
    assert event["featured_at"]


def test_history_written_for_snap_missing_from_snap_table(app):
    """A snap we never collected still records, with details left empty."""
    record_featured_history([{"snap_id": "unknown"}], is_manual=True)

    event = get_featured_history(["unknown"])["unknown"][0]
    assert event["title"] is None
    assert event["is_manual"] is True


@patch("snaprecommend.auth.authentication.is_authenticated", return_value=True)
def test_history_endpoint_includes_deleted_snaps(_mock_auth, app, admin_client):
    """The endpoint returns events for snaps no longer featured or present."""
    db.session.add(_make_snap("snap1"))
    db.session.commit()
    record_featured_history(
        [{"snap_id": "snap1", "selection_reason": {"role": "fill"}}],
        is_manual=False,
    )
    db.session.delete(db.session.query(Snap).filter_by(snap_id="snap1").one())
    db.session.commit()

    response = admin_client.get("/featured/history")

    assert response.status_code == 200
    events = response.get_json()
    assert len(events) == 1
    assert events[0]["snap_id"] == "snap1"
    assert events[0]["title"] == "Multipass"
    assert events[0]["selection_reason"] == {"role": "fill"}


@patch("snaprecommend.auth.authentication.is_authenticated", return_value=True)
def test_history_endpoint_limit_is_capped(_mock_auth, app, admin_client):
    """A caller cannot ask for more than the maximum."""
    record_featured_history([{"snap_id": "snap1"}], is_manual=False)

    assert admin_client.get("/featured/history?limit=99999").status_code == 200
    assert admin_client.get("/featured/history?limit=0").status_code == 200


@patch("snaprecommend.auth.authentication.is_authenticated", return_value=True)
def test_history_endpoint_keeps_position_order_within_a_run(
    _mock_auth, app, admin_client
):
    published = ["snap1", "snap2", "snap3"]
    record_featured_history(
        [{"snap_id": snap_id} for snap_id in published], is_manual=False
    )

    events = admin_client.get("/featured/history").get_json()

    assert [event["snap_id"] for event in events] == published


@patch("snaprecommend.auth.authentication.is_authenticated", return_value=True)
def test_history_timestamps_are_utc_aware(_mock_auth, app, admin_client):
    record_featured_history([{"snap_id": "snap1"}], is_manual=False)

    event = admin_client.get("/featured/history").get_json()[0]

    parsed = datetime.fromisoformat(event["featured_at"])
    assert parsed.tzinfo is not None
    assert parsed.utcoffset() == timedelta(0)


@patch("snaprecommend.auth.authentication.is_authenticated", return_value=True)
def test_snap_history_endpoint_returns_only_that_snap(
    _mock_auth, app, admin_client
):
    """The drawer endpoint scopes history to the snap it was asked about."""
    record_featured_history(
        [{"snap_id": "snap1"}, {"snap_id": "snap2"}], is_manual=False
    )

    response = admin_client.get("/featured/history/snap1")

    assert response.status_code == 200
    events = response.get_json()
    assert [event["snap_id"] for event in events] == ["snap1"]


@patch("snaprecommend.auth.authentication.is_authenticated", return_value=True)
def test_snap_history_endpoint_is_newest_first(_mock_auth, app, admin_client):
    record_featured_history(
        [{"snap_id": "snap1", "selection_reason": {"role": "fill"}}],
        is_manual=False,
    )
    record_featured_history(
        [{"snap_id": "snap1", "selection_reason": {"role": "top-3"}}],
        is_manual=True,
    )

    events = admin_client.get("/featured/history/snap1").get_json()

    assert len(events) == 2
    assert events[0]["selection_reason"]["role"] == "top-3"
    assert events[0]["is_manual"] is True
    assert events[1]["selection_reason"]["role"] == "fill"


@patch("snaprecommend.auth.authentication.is_authenticated", return_value=True)
def test_snap_history_endpoint_unknown_snap_is_empty(
    _mock_auth, app, admin_client
):
    assert admin_client.get("/featured/history/nope").get_json() == []


def test_history_attaches_current_categories(app):
    """Events carry the snap's categories so the drawer can label them."""
    db.session.add(
        _make_snap(
            "snap1",
            categories=[
                {"name": "development", "featured": False},
                {"name": "utilities", "featured": False},
            ],
        )
    )
    db.session.commit()
    record_featured_history([{"snap_id": "snap1"}], is_manual=True)

    event = get_featured_history(["snap1"])["snap1"][0]

    assert event["categories"] == ["development", "utilities"]


def test_history_categories_none_when_snap_is_gone(app):
    """A history row outlives its snap; categories are simply absent."""
    record_featured_history([{"snap_id": "vanished"}], is_manual=False)

    event = get_featured_history(["vanished"])["vanished"][0]

    assert event["categories"] is None
