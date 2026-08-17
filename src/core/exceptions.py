from fastapi import status

class AppException(Exception):
    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class ResourceNotFoundError(AppException):
    def __init__(self, resource: str, identifier: str):
        super().__init__(f"{resource} with ID '{identifier}' was not found", status.HTTP_404_NOT_FOUND)

class ValidationError(AppException):
    def __init__(self, detail: str):
        super().__init__(f"Validation failed: {detail}", status.HTTP_422_UNPROCESSABLE_ENTITY)
