import requests
from requests.exceptions import ConnectionError, Timeout
from tap_appfigures.exceptions import raise_for_error, AppfiguresError, ReadTimeoutError, Server5xxError, AppfiguresTooManyRequestsError

import backoff
import json
import singer

LOGGER = singer.get_logger()

REQUEST_TIMEOUT = 3000
BACKOFF_MAX_TRIES_REQUEST = 5

class AppfiguresClient():

    BASE_URL = "https://appfigures.com/market/explorer/_u/data"
    APPLICATION_API = "explorer_search"
    COMPANY_API = "profiles/developer"

    def __init__(self, config):
        self.__cookie = config.get("cookie")
        self.__x_rt = config.get("x-rt")
        self.__verified = False
        self.__session = requests.Session()


    def __enter__(self):
        self.__verified = self.check_access()
        
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        
        self.__session.close()
    
    def __headers(self):
        
        headers = {}
        headers["accept"] = "*/*"
        headers["accept-language"] = "en-US,en;q=0.9"
        headers["connection"] = "keep-alive"
        headers["cookie"] = self.__cookie
        headers["origin"] = "https://appfigures.com"
        headers["referer"] = "https://appfigures.com/market/explorer"
        headers["referrer-policy"] = "strict-origin-when-cross-origin"
        headers["sec-fest-dest"] = "empty"
        headers["sec-fest-mode"] = "cors"
        headers["sec-fest-site"] = "same-origin"
        headers["user-agent"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"
        headers["dpr"] = "1"
        headers["sec-ch-ua"] = '"Google Chrome";v="107", "Chromium";v="107", "Not=A?Brand";v="24"'
        headers["sec-ch-ua-mobile"] = "70"
        headers["sec-ch-ua-platform"] = '"macOS"'
        headers["viewport-width"] = "546"
        headers["x-rt"] = self.__x_rt
        headers["x-requested-with"] = "XMLHttpRequest"

        return headers

    def __data(self):

        data = {}
        data["q"] = '["and",["and",["or",["nested","all_sdks",["and",["match","all_sdks.id",["and","apollo"]],["match","all_sdks.active",true]]]]]]' 
        
        return data
    
    def get_company_url(self, company_id):
        
        url = f"{self.BASE_URL}/{self.COMPANY_API}/{company_id}"
        
        return url

    def get_application_search_url(self):

        url = f"{self.BASE_URL}/{self.APPLICATION_API}"

        return url
        
    
    @backoff.on_exception(
        backoff.expo,
        (Server5xxError, ReadTimeoutError, ConnectionError, Timeout),
        max_tries=3,
        factor=2)
    def check_access(self):

        if self.__cookie is None:
            raise Exception('Error: Missing cookie in tap config.json.')
        
        url = f"{self.BASE_URL}"

        try:
            response = self.__session.get(url=url, timeout=REQUEST_TIMEOUT, headers=self.__headers())
        except requests.exceptions.Timeout as err:
            LOGGER.error(f'TIMEOUT ERROR: {err}')
            raise ReadTimeoutError

        if response.status_code != 200:
            LOGGER.error(f'Error status_code = {response.status_code}')
            raise_for_error(response)
        else:
            return True

    @backoff.on_exception(
        backoff.expo,
        (Server5xxError, ReadTimeoutError, ConnectionError, Timeout, AppfiguresTooManyRequestsError),
        max_tries=BACKOFF_MAX_TRIES_REQUEST,
        factor=10,
        logger=LOGGER)
    def perform_request(self,
                        method,
                        url=None,
                        params=None,
                        json=None,
                        stream=False,
                        **kwargs):
        
        try:
            response = self.__session.request(method=method,
                                              url=url,
                                              params=params,
                                              json=json,
                                              stream=stream,
                                              timeout=REQUEST_TIMEOUT,
                                              **kwargs)

            if response.status_code >= 500:
                LOGGER.error(f'Error status_code = {response.status_code}')
                raise Server5xxError()

            if response.status_code != 200:
                LOGGER.error(f'Error status_code = {response.status_code}')
                raise_for_error(response)
            return response

        except requests.exceptions.Timeout as err:
            LOGGER.error(f'TIMEOUT ERROR: {err}')
            raise ReadTimeoutError(err)

    def post_request(self, url, params=None, data=None, **kwargs):
        
        if not self.__verified:
            self.__verified = self.check_access()

        response = self.perform_request(method="post",
                                            url=url,
                                            params=params,
                                            data=self.__data(),
                                            headers=self.__headers(),
                                            **kwargs)

        response_json = response.json()

        return response_json

    def get_request(self, url, params=None, json=None, **kwargs):
        
        if not self.__verified:
            self.__verified = self.check_access()

        response = self.perform_request(method="get",
                                            url=url,
                                            params=params,
                                            json=json,
                                            headers=self.__headers(),
                                            **kwargs)

        response_json = response.json()

        return response_json
