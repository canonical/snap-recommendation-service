from unittest.mock import Mock, call

import requests

from collector import main


def test_collector_retries_ingestion_after_timeout(monkeypatch):
    monkeypatch.setenv(main.MACAROON_ENV_PATH, "test")
    collect = Mock(side_effect=[requests.ReadTimeout("search timed out"), None])
    pipeline_ran_recently = Mock(return_value=True)
    sleep = Mock(side_effect=[None, KeyboardInterrupt()])
    monkeypatch.setattr(main, "collect_initial_snap_data", collect)
    monkeypatch.setattr(main, "_pipeline_ran_recently", pipeline_ran_recently)
    monkeypatch.setattr(main, "sleep", sleep)

    main.collector_service()

    assert collect.call_count == 2
    pipeline_ran_recently.assert_called_once_with()
    assert sleep.call_args_list == [call(main.INITIAL_STEP_INTERVAL)] * 2
