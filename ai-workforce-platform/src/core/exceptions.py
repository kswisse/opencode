class AppError(Exception):
    def __init__(self, message: str, code: str = "INTERNAL_ERROR", status_code: int = 500):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppError):
    def __init__(self, resource: str, resource_id: str):
        super().__init__(f"{resource} {resource_id} not found", "NOT_FOUND", 404)


class ValidationError(AppError):
    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR", 422)


class QuotaExceededError(AppError):
    def __init__(self, resource: str):
        super().__init__(f"Quota exceeded for {resource}", "QUOTA_EXCEEDED", 429)


class LLMError(AppError):
    def __init__(self, message: str):
        super().__init__(message, "LLM_ERROR", 502)
