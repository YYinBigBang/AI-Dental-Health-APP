import time
import logging
from functools import wraps
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger()


def standard_response(returncode=0, message="Success", data=True, status_code=status.HTTP_200_OK):
    """
    Generates a standardized API response.

    Args:
        returncode (int): HTTP status code equivalent (0 for success, non-zero for errors).
        message (str): Descriptive message.
        data (optional or bool): Data payload. Use `True` if there's no data to return.
        status_code (int): HTTP status code for the response.

    Returns:
        Response: DRF Response object with standardized format.
    """
    return Response({
        "returnCode": returncode,
        "message": message,
        "data": data
    }, status=status_code)


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        status_code = response.status_code

        return standard_response(
            returncode=1,
            message='Error: ' + str(response.data.get('detail', '')),
            data=response.data,
            status_code=status_code
        )
    else:
        return standard_response(
            returncode=1,
            message='Internal Server Error!!',
            data=True,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def timelog(func):
    """Decorator for recording function execution time."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            logger.info(f'[Phase: {func.__name__}] ------------- START')
            print(f'[Phase: {func.__name__}] ------------- START')
            return func(*args, **kwargs)
        finally:
            elapsed_time = time.time() - start_time
            logger.info(f"[Phase: {func.__name__}] ------------- END in {elapsed_time:.3f}(s)")
            print(f"[Phase: {func.__name__}] ------------- END in {elapsed_time:.3f}(s)")
    return wrapper
