from unittest.mock import patch

from collector.ratings.collect_ratings import get_ratings, ratings_login


@patch("collector.ratings.collect_ratings.grpc.secure_channel")
def test_ratings_login_sets_deadline(mock_channel):
    channel = mock_channel.return_value.__enter__.return_value
    authenticate = channel.unary_unary.return_value
    authenticate.return_value.token = "test-token"

    assert ratings_login() == "test-token"
    authenticate.assert_called_once()
    assert authenticate.call_args.kwargs["timeout"] == 15


@patch("collector.ratings.collect_ratings.grpc.secure_channel")
def test_get_ratings_sets_deadline(mock_channel):
    channel = mock_channel.return_value.__enter__.return_value
    get_bulk_ratings = channel.unary_unary.return_value
    get_bulk_ratings.return_value.ratings = []

    assert get_ratings(["snap-id"], "test-token") == {}
    get_bulk_ratings.assert_called_once()
    assert get_bulk_ratings.call_args.kwargs["timeout"] == 15
