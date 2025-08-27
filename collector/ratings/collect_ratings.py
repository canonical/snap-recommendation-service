import logging
import grpc
from hashlib import sha256
from collector.ratings.generated import (
    ratings_features_user_pb2 as ratings_features_user,
    ratings_features_user_pb2_grpc as ratings_features_user_grpc,
    ratings_features_app_pb2 as ratings_features_app,
    ratings_features_app_pb2_grpc as ratings_features_app_grpc,
)

logger = logging.getLogger("ratings_collector")

RATINGS_ADDRESS = "ratings.staging.ubuntu.com"

USER_ID = sha256(b"snaprecommend").hexdigest()


def ratings_login():
    creds = grpc.ssl_channel_credentials()
    with grpc.secure_channel(RATINGS_ADDRESS, creds) as channel:
        stub = ratings_features_user_grpc.UserStub(channel)

        try:
            auth_request = ratings_features_user.AuthenticateRequest(
                id=USER_ID
            )

            auth_response = stub.Authenticate(auth_request)
            token = auth_response.token

            if not token:
                logger.error("Authentication failed: Did not receive a token.")
                return
            logger.info("Successfully authenticated with ratings service.")
            return token
        except grpc.RpcError as e:
            logger.error(
                f"gRPC error during authentication: {e.code()} - {e.details()}"
            )
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {e}")


def get_ratings(snap_ids: list[str], token: str) -> dict[str, dict]:
    """
    Fetches ratings for a list of snap IDs from the ratings service.
    Returns a dictionary mapping snap IDs to rating data containing
    raw_rating and total_votes.
    """
    if not snap_ids:
        return {}

    # First authenticate to get the token
    if not token:
        logger.error("Failed to authenticate with ratings service")
        raise ValueError("Authentication token is required")

    creds = grpc.ssl_channel_credentials()
    with grpc.secure_channel(RATINGS_ADDRESS, creds) as channel:
        stub = ratings_features_app_grpc.AppStub(channel)

        try:
            # Create metadata with the authentication token
            metadata = [("authorization", f"Bearer {token}")]

            # Create the bulk ratings request
            bulk_request = ratings_features_app.GetBulkRatingsRequest(
                snap_ids=snap_ids
            )

            # Make the gRPC call
            bulk_response = stub.GetBulkRatings(
                bulk_request, metadata=metadata
            )

            # Process the response into the expected format
            ratings_dict = {}
            for chart_data in bulk_response.ratings:
                if chart_data.rating and chart_data.rating.snap_id:
                    snap_id = chart_data.rating.snap_id
                    ratings_dict[snap_id] = {
                        "raw_rating": chart_data.raw_rating,
                        "total_votes": chart_data.rating.total_votes,
                    }

            logger.info(
                f"Successfully fetched ratings for {len(ratings_dict)} snaps"
            )
            return ratings_dict

        except grpc.RpcError as e:
            logger.error(
                f"gRPC error during bulk ratings fetch: "
                f"{e.code()} - {e.details()}"
            )
            return {}
        except Exception as e:
            logger.error(f"Unexpected error during bulk ratings fetch: {e}")
            return {}
