
from requests import Session as RequestsSession
from requests.exceptions import Timeout, ConnectionError
from canonicalwebteam.store_api.devicegw import DeviceGW
from canonicalwebteam.store_api.publishergw import PublisherGW
from canonicalwebteam.store_api.dashboard import Dashboard

class BaseSession:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def requests(self, method, url, timeout=12, **kwargs):
        try:
            return super().request(
                method=method, url=url, timeout=timeout, **kwargs
            )
        except Timeout:
            raise Exception(
                "The request to {} took too long".format(url)
            )
        except ConnectionError:
            raise Exception(
                "Failed to establish connection to {}.".format(url)
            )
        
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
