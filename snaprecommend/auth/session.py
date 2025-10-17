import logging
from requests import Session as RequestsSession
from requests.exceptions import Timeout, ConnectionError, ProxyError
from canonicalwebteam.store_api.devicegw import DeviceGW
from canonicalwebteam.store_api.publishergw import PublisherGW
from canonicalwebteam.store_api.dashboard import Dashboard

logger = logging.getLogger(__name__)


class BaseSession:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Disable automatic proxy configuration from environment variables
        # This prevents the "403 Forbidden" proxy errors when accessing Snapcraft services
        self.trust_env = False
        logger.info(f"Initialized {self.__class__.__name__} with trust_env=False (proxy disabled)")

    def requests(self, method, url, timeout=12, **kwargs):
        try:
            return super().request(method=method, url=url, timeout=timeout, **kwargs)
        except Timeout:
            raise Exception("The request to {} took too long".format(url))
        except ConnectionError:
            raise Exception("Failed to establish connection to {}.".format(url))
        except ProxyError as e:
            logger.error(f"Proxy error when connecting to {url}: {str(e)}")
            raise Exception("Proxy error when connecting to {}: {}".format(url, str(e)))


class Session(BaseSession, RequestsSession):
    pass


class PublisherSession(BaseSession, RequestsSession):
    def request(self, method, url, timeout=None, **kwargs):
        return super().request(method, url, timeout, **kwargs)


api_session = Session()
api_publisher_session = PublisherSession()

dashboard = Dashboard(api_session)
device_gateway = DeviceGW("snap", api_session)
publisher_gateway = PublisherGW("snap", api_publisher_session)
