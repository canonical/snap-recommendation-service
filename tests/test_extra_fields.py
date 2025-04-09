import pytest
from unittest.mock import MagicMock, patch
from collector.extra_fields import (
    calculate_latest_active_devices,
    fetch_metrics_from_api,
    process_and_update_snap_metrics,
    fetch_and_update_metrics_for_snaps,
    get_metrics_time_range,
    fetch_eligible_snaps,
    update_snap_metrics,
    fetch_extra_fields,
)
from snaprecommend.models import Snap
from sqlalchemy.orm import Session
from datetime import datetime, timedelta


@pytest.fixture
def mock_session():
    return MagicMock(spec=Session)


@pytest.fixture
def sample_snap():
    return Snap(
        snap_id="snap1",
        name="test-snap",
        active_devices=0,
        reaches_min_threshold=True,
    )


def test_calculate_latest_active_devices():
    metrics_data = {
        "buckets": ["2025-01-26", "2025-01-27"],
        "metric_name": "weekly_installed_base_by_version",
        "series": [{"name": "1.0.1", "values": [23, 22]}],
        "snap_id": "bv9Q2i9CNAvTjt9wTx1cFC6SAT9YrEfG",
        "status": "OK",
    }

    result = calculate_latest_active_devices(metrics_data)
    assert result == 22


@patch("collector.extra_fields.requests.post")
@patch("collector.extra_fields.get_auth_header")
def test_fetch_metrics_from_api(mock_get_auth_header, mock_post, sample_snap):
    mock_get_auth_header.return_value = "Bearer token"
    mock_response = MagicMock()
    mock_response.json.return_value = {"metrics": []}
    mock_post.return_value = mock_response

    result = fetch_metrics_from_api([sample_snap], "2023-01-01", "2023-01-31")
    assert result == {"metrics": []}
    mock_post.assert_called_once()


def test_process_and_update_snap_metrics(mock_session, sample_snap):
    metrics_data = {
        "metrics": [
            {
                "buckets": ["2025-01-26", "2025-01-27"],
                "metric_name": "weekly_installed_base_by_version",
                "series": [{"name": "1.0.1", "values": [23, 22]}],
                "snap_id": "bv9Q2i9CNAvTjt9wTx1cFC6SAT9YrEfG",
                "status": "OK",
            }
        ]
    }

    process_and_update_snap_metrics([sample_snap], metrics_data, mock_session)
    assert sample_snap.active_devices == 22
    mock_session.commit.assert_called_once()


@patch("collector.extra_fields.fetch_metrics_from_api")
@patch("collector.extra_fields.process_and_update_snap_metrics")
@patch("collector.extra_fields.get_metrics_time_range")
def test_fetch_and_update_metrics_for_snaps(
    mock_get_metrics_time_range,
    mock_process_and_update_snap_metrics,
    mock_fetch_metrics_from_api,
    mock_session,
    sample_snap,
):
    mock_get_metrics_time_range.return_value = ("2023-01-01", "2023-01-31")
    mock_fetch_metrics_from_api.return_value = {"metrics": []}

    fetch_and_update_metrics_for_snaps([sample_snap], mock_session)
    mock_fetch_metrics_from_api.assert_called_once()
    mock_process_and_update_snap_metrics.assert_called_once()


def test_get_metrics_time_range():
    start_date, end_date = get_metrics_time_range()
    assert end_date == (datetime.now() - timedelta(days=1)).strftime(
        "%Y-%m-%d"
    )
    assert start_date == (datetime.now() - timedelta(days=2)).strftime(
        "%Y-%m-%d"
    )


def test_fetch_eligible_snaps(mock_session):
    mock_session.query().filter().all.return_value = [sample_snap]
    result = fetch_eligible_snaps(mock_session)
    assert result == [sample_snap]
    mock_session.query().filter().all.assert_called_once()


@patch("collector.extra_fields.fetch_eligible_snaps")
@patch("collector.extra_fields.fetch_and_update_metrics_for_snaps")
def test_update_snap_metrics(
    mock_fetch_and_update_metrics_for_snaps,
    mock_fetch_eligible_snaps,
):
    mock_fetch_eligible_snaps.return_value = [sample_snap]

    update_snap_metrics()
    mock_fetch_eligible_snaps.assert_called_once()
    mock_fetch_and_update_metrics_for_snaps.assert_called_once()


@patch("collector.extra_fields.update_snap_metrics")
@patch("collector.extra_fields.add_pipeline_step_log")
def test_fetch_extra_fields(
    mock_add_pipeline_step_log, mock_update_snap_metrics
):
    fetch_extra_fields()
    mock_update_snap_metrics.assert_called_once()
    mock_add_pipeline_step_log.assert_called_once()
