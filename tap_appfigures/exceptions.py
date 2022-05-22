from requests.exceptions import HTTPError, ConnectionError, Timeout
import singer

LOGGER = singer.get_logger()

class ReadTimeoutError(Exception):
    pass
    
class Server5xxError(Exception):
    pass

class AppfiguresError(Exception):
    pass

class AppfiguresBadRequestError(AppfiguresError):
    pass

class AppfiguresForbiddenError(AppfiguresError):
    pass

class AppfiguresNotFoundError(AppfiguresError):
    pass

class AppfiguresTooManyRequestsError(AppfiguresError):
    pass

ERROR_CODE_EXCEPTION_MAPPING = {
    400: AppfiguresBadRequestError,
    403: AppfiguresForbiddenError,
    404: AppfiguresNotFoundError,
    429: AppfiguresTooManyRequestsError
}

def get_exception_for_error_code(error_code):
    return ERROR_CODE_EXCEPTION_MAPPING.get(error_code, None)

def raise_for_error(response):
    LOGGER.error(f'{response.status_code}: {response.text}, REASON: {response.reason}')
    
    try:    
        response.raise_for_status()
    except (HTTPError, ConnectionError) as error:
        try:
            content_length = len(response.content)
            if content_length == 0:
                # There is nothing we can do here since LinkedIn has neither sent
                # us a 2xx response nor a response content.
                return
            response = response.json()
            error_code = response.get('status')
            if get_exception_for_error_code(error_code):
                message = '%s: %s' % (response.get('error', str(error)),
                        response.get('message', 'Unknown Error'))
                ex = get_exception_for_error_code(error_code)
                raise ex(message)
            else:
                raise AppfiguresError(error)
        except (ValueError, TypeError):
            raise AppfiguresError(error)
