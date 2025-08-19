from starlette import status
from starlette.exceptions import HTTPException


class AppBaseException(HTTPException):
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)


class AppBadRequestException(AppBaseException):
    def __init__(self, msg: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg
        )


class AppForbiddenException(AppBaseException):
    def __init__(self, msg: str):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=msg
        )


class AppNotFoundException(AppBaseException):
    def __init__(self, msg: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=msg
        )


class AppAuthorizationException(AppBaseException):
    def __init__(self, msg: str):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=msg
        )