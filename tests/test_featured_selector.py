"""
Tests for collector/featured_selector.py

All tests use an in-memory SQLite database so no external services are needed.
Store API calls (device_gateway, publisher_gateway) are mocked throughout.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from flask import Flask
from sqlalchemy.pool import StaticPool

from snaprecommend import db
from snaprecommend.models import FeaturedHistory, PipelineStepLog, PipelineSteps, Snap
from collector.featured_selector import (
    _apply_hard_gates,
    _enforce_canonical_mix,
    _fill_slots,
    _get_recently_auto_featured_ids,
    _has_any_category,
    _minmax_normalise,
    _rank_candidates,
    _reserve_category_slots,
    _snap_category_slugs,
    run_selection,
    select_featured_snaps,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

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

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def _make_snap(
    snap_id,
    name=None,
    publisher="third-party",
    validation="verified",
    active_devices=1000,
    raw_rating=4.5,
    last_updated=None,
    categories=None,
    reaches_threshold=True,
    excluded=False,
):
    """Helper: build and persist a Snap row."""
    snap = Snap(
        snap_id=snap_id,
        name=name or snap_id,
        title=f"Title {snap_id}",
        version="1.0",
        summary="summary",
        description="desc",
        icon="https://example.com/icon.png",
        website="https://example.com",
        contact="contact@example.com",
        publisher=publisher,
        revision=1,
        links={},
        media=[],
        developer_validation=validation,
        license="MIT",
        last_updated=last_updated or datetime.utcnow(),
        active_devices=active_devices,
        raw_rating=raw_rating,
        reaches_min_threshold=reaches_threshold,
        excluded=excluded,
        categories=categories or [{"slug": "utilities"}],
    )
    db.session.add(snap)
    db.session.commit()
    return snap


# ---------------------------------------------------------------------------
# Unit tests: helpers
# ---------------------------------------------------------------------------

def test_snap_category_slugs_dict_format():
    from types import SimpleNamespace
    snap = SimpleNamespace(categories=[{"slug": "development"}, {"slug": "games"}])
    assert _snap_category_slugs(snap) == {"development", "games"}


def test_snap_category_slugs_string_format():
    from types import SimpleNamespace
    snap = SimpleNamespace(categories=["development", "games"])
    assert _snap_category_slugs(snap) == {"development", "games"}


def test_snap_category_slugs_none():
    from types import SimpleNamespace
    snap = SimpleNamespace(categories=None)
    assert _snap_category_slugs(snap) == set()


def test_has_any_category_true():
    from types import SimpleNamespace
    snap = SimpleNamespace(categories=[{"slug": "development"}])
    assert _has_any_category(snap, {"development", "games"}) is True


def test_has_any_category_false():
    from types import SimpleNamespace
    snap = SimpleNamespace(categories=[{"slug": "utilities"}])
    assert _has_any_category(snap, {"development", "games"}) is False


def test_minmax_normalise_normal():
    result = _minmax_normalise({"a": 0, "b": 50, "c": 100})
    assert result["a"] == pytest.approx(0.0)
    assert result["b"] == pytest.approx(0.5)
    assert result["c"] == pytest.approx(1.0)


def test_minmax_normalise_all_same():
    result = _minmax_normalise({"a": 5, "b": 5})
    assert result["a"] == pytest.approx(1.0)


def test_minmax_normalise_none_values():
    result = _minmax_normalise({"a": None, "b": 100})
    assert result["a"] == pytest.approx(0.0)
    assert result["b"] == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Unit tests: Stage 1 — hard gates
# ---------------------------------------------------------------------------

def test_hard_gates_excludes_old_snap(app):
    _make_snap("old", last_updated=datetime.utcnow() - timedelta(days=200))
    result = _apply_hard_gates(
        recency_days=180, history_window_days=365, min_rating=4.0, exclusion_names=[]
    )
    assert not any(s.snap_id == "old" for s in result)


def test_hard_gates_excludes_low_rating(app):
    _make_snap("bad-rating", raw_rating=2.0)
    result = _apply_hard_gates(
        recency_days=180, history_window_days=365, min_rating=4.0, exclusion_names=[]
    )
    assert not any(s.snap_id == "bad-rating" for s in result)


def test_hard_gates_allows_null_rating(app):
    _make_snap("no-rating", raw_rating=None)
    result = _apply_hard_gates(
        recency_days=180, history_window_days=365, min_rating=4.0, exclusion_names=[]
    )
    assert any(s.snap_id == "no-rating" for s in result)


def test_hard_gates_excludes_unverified(app):
    _make_snap("unverified", validation="unproven")
    result = _apply_hard_gates(
        recency_days=180, history_window_days=365, min_rating=4.0, exclusion_names=[]
    )
    assert not any(s.snap_id == "unverified" for s in result)


def test_hard_gates_allows_starred(app):
    _make_snap("starred", validation="starred")
    result = _apply_hard_gates(
        recency_days=180, history_window_days=365, min_rating=4.0, exclusion_names=[]
    )
    assert any(s.snap_id == "starred" for s in result)


def test_hard_gates_excludes_server_cloud_category(app):
    _make_snap("lxd-snap", categories=[{"slug": "server-and-cloud"}])
    result = _apply_hard_gates(
        recency_days=180, history_window_days=365, min_rating=4.0, exclusion_names=[]
    )
    assert not any(s.snap_id == "lxd-snap" for s in result)


def test_hard_gates_excludes_by_name(app):
    _make_snap("lxd", name="lxd")
    result = _apply_hard_gates(
        recency_days=180,
        history_window_days=365,
        min_rating=4.0,
        exclusion_names=["lxd"],
    )
    assert not any(s.snap_id == "lxd" for s in result)


def test_hard_gates_excludes_excluded_flag(app):
    _make_snap("ex", excluded=True)
    result = _apply_hard_gates(
        recency_days=180, history_window_days=365, min_rating=4.0, exclusion_names=[]
    )
    assert not any(s.snap_id == "ex" for s in result)


def test_hard_gates_excludes_recently_featured(app):
    _make_snap("recent-feat")
    # Record an automated featuring within the window
    db.session.add(
        FeaturedHistory(
            snap_id="recent-feat",
            featured_at=datetime.utcnow() - timedelta(days=30),
            is_manual=False,
        )
    )
    db.session.commit()

    result = _apply_hard_gates(
        recency_days=180, history_window_days=365, min_rating=4.0, exclusion_names=[]
    )
    assert not any(s.snap_id == "recent-feat" for s in result)


def test_hard_gates_allows_manually_featured_recently(app):
    """Manual pins bypass the 12-month gate."""
    _make_snap("manual-pin")
    db.session.add(
        FeaturedHistory(
            snap_id="manual-pin",
            featured_at=datetime.utcnow() - timedelta(days=30),
            is_manual=True,  # manual — should NOT be excluded
        )
    )
    db.session.commit()

    result = _apply_hard_gates(
        recency_days=180, history_window_days=365, min_rating=4.0, exclusion_names=[]
    )
    assert any(s.snap_id == "manual-pin" for s in result)


# ---------------------------------------------------------------------------
# Unit tests: Stage 2 — ranking
# ---------------------------------------------------------------------------

def test_ranking_orders_by_composite_score(app):
    low = _make_snap("low", active_devices=100, raw_rating=4.0)
    high = _make_snap("high", active_devices=100_000, raw_rating=5.0)
    mid = _make_snap("mid", active_devices=10_000, raw_rating=4.5)

    ranked, _ = _rank_candidates([low, high, mid], recency_days=180)
    ids = [s.snap_id for s in ranked]
    assert ids.index("high") < ids.index("mid") < ids.index("low")


# ---------------------------------------------------------------------------
# Unit tests: Stage 3 — Canonical mix
# ---------------------------------------------------------------------------

def _snap_obj(snap_id, publisher="third-party", categories=None):
    """Build a plain object with the Snap attributes the selector needs."""
    from types import SimpleNamespace
    return SimpleNamespace(
        snap_id=snap_id,
        publisher=publisher,
        categories=categories or [{"slug": "utilities"}],
    )


def test_canonical_mix_inserts_one_when_zero(app):
    top3 = [_snap_obj("a"), _snap_obj("b"), _snap_obj("c")]
    canonical = _snap_obj("canon", publisher="canonical")
    remaining = [canonical, _snap_obj("d")]

    new_top3, new_remaining = _enforce_canonical_mix(top3, remaining)
    assert any(s.publisher == "canonical" for s in new_top3)
    assert canonical not in new_remaining


def test_canonical_mix_removes_one_when_three(app):
    top3 = [
        _snap_obj("a", publisher="canonical"),
        _snap_obj("b", publisher="canonical"),
        _snap_obj("c", publisher="canonical"),
    ]
    non_canon = _snap_obj("nc")
    remaining = [non_canon]

    new_top3, _ = _enforce_canonical_mix(top3, remaining)
    canonical_count = sum(1 for s in new_top3 if s.publisher == "canonical")
    assert canonical_count == 2


def test_canonical_mix_one_or_two_unchanged(app):
    top3 = [
        _snap_obj("a", publisher="canonical"),
        _snap_obj("b"),
        _snap_obj("c"),
    ]
    remaining = [_snap_obj("d")]
    new_top3, _ = _enforce_canonical_mix(top3, remaining)
    assert [s.snap_id for s in new_top3] == ["a", "b", "c"]


def test_canonical_mix_raises_when_no_canonical_available(app):
    top3 = [_snap_obj("a"), _snap_obj("b"), _snap_obj("c")]
    remaining = [_snap_obj("d")]  # no Canonical at all
    with pytest.raises(ValueError, match="No Canonical snap"):
        _enforce_canonical_mix(top3, remaining)


# ---------------------------------------------------------------------------
# Unit tests: Stage 4 — category spread
# ---------------------------------------------------------------------------

def _dev_snap(snap_id):
    return _snap_obj(snap_id, categories=[{"slug": "development"}])


def _game_snap(snap_id):
    return _snap_obj(snap_id, categories=[{"slug": "games"}])


def _dev_game_snap(snap_id):
    return _snap_obj(snap_id, categories=[{"slug": "development"}, {"slug": "games"}])


def test_category_reserve_fills_dev_and_game(app):
    top3 = [_snap_obj("a"), _snap_obj("b"), _snap_obj("c")]
    remaining = [_dev_snap("dev1"), _dev_snap("dev2"), _game_snap("game1"), _snap_obj("x")]

    reserved, leftover = _reserve_category_slots(top3, remaining)
    reserved_ids = {s.snap_id for s, _ in reserved}
    assert "dev1" in reserved_ids
    assert "dev2" in reserved_ids
    assert "game1" in reserved_ids


def test_category_reserve_dual_category_counts_for_both(app):
    top3 = [_snap_obj("a"), _snap_obj("b"), _snap_obj("c")]
    remaining = [_dev_snap("dev1"), _dev_game_snap("dg")]

    # dev1 + dg covers dev×2 and dg covers games×1
    reserved, _ = _reserve_category_slots(top3, remaining)
    assert len(reserved) == 2


def test_category_reserve_raises_when_no_game(app):
    top3 = [_snap_obj("a"), _snap_obj("b"), _snap_obj("c")]
    remaining = [_dev_snap("d1"), _dev_snap("d2"), _snap_obj("x")]
    with pytest.raises(ValueError, match="game snaps"):
        _reserve_category_slots(top3, remaining)


def test_category_reserve_no_extra_slots_needed_when_top3_satisfies(app):
    top3 = [
        _dev_snap("d1"),
        _dev_game_snap("dg"),
        _snap_obj("x"),
    ]
    remaining = [_snap_obj("y")]
    reserved, _ = _reserve_category_slots(top3, remaining)
    assert reserved == []


# ---------------------------------------------------------------------------
# Unit tests: Stage 5 — fill
# ---------------------------------------------------------------------------

def test_fill_respects_cap(app):
    top3 = [_snap_obj(f"t{i}", categories=[{"slug": "dev"}]) for i in range(3)]
    # cap=4: 3 dev already in top3 → only 1 more dev allowed in fill.
    # Give each "other" snap a unique category so the cap never blocks them.
    dev_snaps = [_snap_obj(f"d{i}", categories=[{"slug": "dev"}]) for i in range(5)]
    other_snaps = [_snap_obj(f"o{i}", categories=[{"slug": f"cat{i}"}]) for i in range(10)]
    remaining = dev_snaps + other_snaps
    filled = _fill_slots(top3, [], remaining, target_count=10, category_cap=4)
    dev_count = sum(
        1 for s in filled if any(c.get("slug") == "dev" for c in (s.categories or []))
    )
    assert dev_count <= 1  # cap=4, 3 already in top3 → max 1 more dev in fill


def test_fill_relaxes_cap_when_short(app):
    top3 = [_snap_obj(f"t{i}", categories=[{"slug": "dev"}]) for i in range(3)]
    # Only dev snaps available and cap is already reached; relaxation must kick in.
    snaps = [_snap_obj(f"d{i}", categories=[{"slug": "dev"}]) for i in range(5)]
    filled = _fill_slots(top3, [], snaps, target_count=6, category_cap=3)
    assert len(filled) > 0


# ---------------------------------------------------------------------------
# Integration tests: run_selection end-to-end
# ---------------------------------------------------------------------------

def _seed_full_candidate_pool(app, count=20):
    """
    Seed enough snaps to satisfy all selection rules:
    - 1+ Canonical
    - 2+ development
    - 1+ games
    - rest utilities
    """
    snaps = []
    snaps.append(_make_snap(
        "canon-1", publisher="canonical", validation="starred",
        active_devices=90_000, raw_rating=4.8,
        categories=[{"slug": "utilities"}],
    ))
    snaps.append(_make_snap(
        "canon-2", publisher="canonical", validation="verified",
        active_devices=80_000, raw_rating=4.7,
        categories=[{"slug": "utilities"}],
    ))
    snaps.append(_make_snap(
        "dev-1", validation="verified", active_devices=70_000, raw_rating=4.6,
        categories=[{"slug": "development"}],
    ))
    snaps.append(_make_snap(
        "dev-2", validation="verified", active_devices=60_000, raw_rating=4.5,
        categories=[{"slug": "development"}],
    ))
    snaps.append(_make_snap(
        "game-1", validation="starred", active_devices=50_000, raw_rating=4.7,
        categories=[{"slug": "games"}],
    ))
    for i in range(count - 5):
        snaps.append(_make_snap(
            f"util-{i}", validation="verified",
            active_devices=10_000 + i * 100, raw_rating=4.2,
            categories=[{"slug": "utilities"}],
        ))
    return snaps


def test_run_selection_returns_events_and_ids(app):
    _seed_full_candidate_pool(app)
    events, snap_ids = run_selection()

    assert 3 <= len(snap_ids) <= 15
    assert len(events) == len(snap_ids)
    for event in events:
        assert "snap_id" in event
        assert "selection_reason" in event
        reason = event["selection_reason"]
        assert "role" in reason
        assert "canonical" in reason
        assert "ranking_key" in reason
        assert "random_seed" in reason


def test_run_selection_enforces_canonical_in_top3(app):
    _seed_full_candidate_pool(app)
    events, snap_ids = run_selection()

    # At least one of the top-3 snap_ids is a Canonical snap
    top3_ids = snap_ids[:3]
    top3_snaps = db.session.query(Snap).filter(Snap.snap_id.in_(top3_ids)).all()
    canonical_count = sum(1 for s in top3_snaps if s.publisher == "canonical")
    assert 1 <= canonical_count <= 2


def test_run_selection_includes_dev_and_game(app):
    _seed_full_candidate_pool(app)
    _, snap_ids = run_selection()

    selected = db.session.query(Snap).filter(Snap.snap_id.in_(snap_ids)).all()
    dev_count = sum(
        1 for s in selected
        if any(
            (c.get("slug") if isinstance(c, dict) else c) == "development"
            for c in (s.categories or [])
        )
    )
    game_count = sum(
        1 for s in selected
        if any(
            (c.get("slug") if isinstance(c, dict) else c) == "games"
            for c in (s.categories or [])
        )
    )
    assert dev_count >= 2
    assert game_count >= 1


def test_run_selection_excludes_server_cloud(app):
    _seed_full_candidate_pool(app)
    _make_snap("cloud-snap", categories=[{"slug": "server-and-cloud"}])
    _, snap_ids = run_selection()
    assert "cloud-snap" not in snap_ids


def test_run_selection_excludes_recently_auto_featured(app):
    _seed_full_candidate_pool(app)
    # Mark canon-1 as recently auto-featured
    db.session.add(FeaturedHistory(
        snap_id="canon-1",
        featured_at=datetime.utcnow() - timedelta(days=10),
        is_manual=False,
    ))
    db.session.commit()
    _, snap_ids = run_selection()
    assert "canon-1" not in snap_ids


def test_run_selection_raises_when_no_canonical(app):
    """If no Canonical snap exists, selection must fail rather than ship a bad list."""
    _make_snap("dev-1", validation="verified", categories=[{"slug": "development"}])
    _make_snap("dev-2", validation="verified", categories=[{"slug": "development"}])
    _make_snap("game-1", validation="starred", categories=[{"slug": "games"}])
    for i in range(15):
        _make_snap(f"u{i}", validation="verified", categories=[{"slug": "utilities"}])

    with pytest.raises(ValueError, match="Canonical"):
        run_selection()


def test_run_selection_raises_when_empty_pool(app):
    with pytest.raises(ValueError, match="No eligible candidates"):
        run_selection()


def test_run_selection_produces_valid_list_on_repeated_calls(app):
    """
    Multiple consecutive runs must each return a valid list satisfying the size
    constraint. This also exercises the random-seed path without relying on
    timing or mocking.
    """
    _seed_full_candidate_pool(app, count=30)
    for _ in range(3):
        _, snap_ids = run_selection()
        assert 3 <= len(snap_ids) <= 15
        assert len(snap_ids) == len(set(snap_ids)), "Duplicate snap IDs in selection"


# ---------------------------------------------------------------------------
# Integration tests: select_featured_snaps (with mocked store)
# ---------------------------------------------------------------------------

@patch("collector.featured_selector.publisher_gateway")
@patch("collector.featured_selector.device_gateway")
def test_select_records_history_and_updates_setting(
    mock_device, mock_publisher, app
):
    _seed_full_candidate_pool(app)

    mock_device.get_featured_snaps.return_value = {
        "_embedded": {"clickindex:package": []},
        "_links": {},
    }
    update_resp = MagicMock()
    update_resp.status_code = 201
    mock_publisher.update_featured_snaps.return_value = update_resp

    select_featured_snaps(token="fake-token")

    rows = db.session.query(FeaturedHistory).filter_by(is_manual=False).all()
    assert len(rows) >= 3
    assert all(r.selection_reason is not None for r in rows)

    from snaprecommend.settings import get_setting
    assert get_setting("featured_last_updated") is not None


@patch("collector.featured_selector.publisher_gateway")
@patch("collector.featured_selector.device_gateway")
def test_select_without_token_skips_store_publish(
    mock_device, mock_publisher, app
):
    _seed_full_candidate_pool(app)

    select_featured_snaps(token=None)

    # History is still recorded
    rows = db.session.query(FeaturedHistory).filter_by(is_manual=False).all()
    assert len(rows) >= 3
    # But the store was NOT touched
    mock_publisher.update_featured_snaps.assert_not_called()
    mock_publisher.delete_featured_snaps.assert_not_called()


@patch("collector.featured_selector.notify_mattermost")
@patch("collector.featured_selector.publisher_gateway")
@patch("collector.featured_selector.device_gateway")
def test_select_notifies_mattermost_on_failure(
    mock_device, mock_publisher, mock_notify, app
):
    # Empty DB → selection must fail
    with pytest.raises(ValueError):
        select_featured_snaps()

    mock_notify.assert_called_once()
    msg = mock_notify.call_args[0][0]
    assert "failed" in msg.lower()


@patch("collector.featured_selector.publisher_gateway")
@patch("collector.featured_selector.device_gateway")
def test_select_logs_pipeline_step(mock_device, mock_publisher, app):
    _seed_full_candidate_pool(app)

    mock_device.get_featured_snaps.return_value = {
        "_embedded": {"clickindex:package": []},
        "_links": {},
    }
    update_resp = MagicMock()
    update_resp.status_code = 201
    mock_publisher.update_featured_snaps.return_value = update_resp

    select_featured_snaps(token="fake-token")

    log = (
        db.session.query(PipelineStepLog)
        .filter_by(step=PipelineSteps.FEATURED)
        .first()
    )
    assert log is not None
    assert log.success is True


@patch("collector.featured_selector.notify_mattermost")
def test_select_logs_failed_pipeline_step_on_error(mock_notify, app):
    with pytest.raises(ValueError):
        select_featured_snaps()

    log = (
        db.session.query(PipelineStepLog)
        .filter_by(step=PipelineSteps.FEATURED)
        .first()
    )
    assert log is not None
    assert log.success is False
