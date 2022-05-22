import requests
from requests.exceptions import ConnectionError, Timeout
from tap_appfigures.exceptions import raise_for_error, LinkedInError, ReadTimeoutError, Server5xxError, LinkedInTooManyRequestsError

import backoff
import json
import singer

LOGGER = singer.get_logger()

REQUEST_TIMEOUT = 3000
BACKOFF_MAX_TRIES_REQUEST = 5

class AppfiguresClient():

    BASE_URL = "https://explorer.appfigures.com"
    APPLICATION_API = "api/appbase/products"
    COMPANY_API = "data/profiles/developer"

    def __init__(self, config):
        self.__cookie = "_ga=GA1.2.2114205037.1645753240; G_ENABLED_IDPS=google; G_AUTHUSER_H=0; _gid=GA1.2.665749090.1648483113; KSERVERID=a2b28ce56085a1d062fd4e99a4c33b8fe1042060; G_ENABLED_IDPS=google; G_AUTHUSER_H=0; _afm_session=cgdyLJZyLyJbwfwlXdCWaA.5jT4KVbHVtRXFY_3yXu1uQaBHAh_MnuHj2hvKTmXU-hEjUPjjy8IuC7GaHVJc9EhqzEE3svA_4ldvG9CGhHnHT3c4gRokoXnpwBjQJagNhR3hh6Lead58RHoMESme_42ea3_ypHjWSr0XXGs8HRz3vZgIkQJoKmEGO1EmsoxJPBM5FNpW0nvMb3JhzK1-_KBz8RJ7jtdaH4cpkIhsLnI8pIcZWRxvrsgieiIJf1ZFyCvx8hP4iL0fGf7ON7wQr_dzszN0YmLCJarqLBkbloCig.1648510556893.2592000000.hpXx9sV9nD-Wo9kZK520I1SCGDZLfPWB2Eu-hAS6BMM; crisp-client/session/8be82478-7316-42dc-b8d4-fb27fbdf055d=session_aabbf73e-ea0e-48e6-852e-5037cbf6d623; _gat=1"
        self.__verified = False
        self.__session = requests.Session()


    def __enter__(self):
        self.__verified = self.check_access()
        
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        
        self.__session.close()
    
    def __headers(self):
        
        headers = {}
        # headers["accept"] = "*/*"
        # headers["accept-language"] = "en-US,en;q=0.9"
        # headers["content-type"] = "application/x-www-form-urlencoded"
        # headers["connection"] = "keep-alive"
        # headers["origin"] = "https://explorer.appfigures.com"
        # headers["referer"] = "https://explorer.appfigures.com/search"
        headers["cookie"] = self.__cookie

        return headers

    def __data(self):

        data = {}
        data["q"] = '["and",["and",["or",["nested","all_sdks",["and",["match","all_sdks.id",["and","apollo"]],["match","all_sdks.active",true]]]]]]' 

        # '["and",["and",["match","updated_date",["range","2022-05-05T00:00:00",null]],["or",["nested","all_sdks",["and",["match","all_sdks.id",["and","apollo"]],["match","all_sdks.active",true]]]]]]'
        
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
        (Server5xxError, ReadTimeoutError, ConnectionError, Timeout, LinkedInTooManyRequestsError),
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
            LOGGER.error(f'TIMEOUT ERROR: {error}')
            raise ReadTimeoutError(err)

    def post_request(self, url, params=None, data=None, **kwargs):
        
        if not self.__verified:
            self.__verified = self.check_access()

        response = self.perform_request(method="post",
                                            url=url,
                                            params=params,
                                            data=self.__data(),
                                            # headers=self.__headers(),
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
