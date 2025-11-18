from rest_framework.exceptions import APIException


class PayloadTooLarge(APIException):
    status_code = 413
    default_detail = "Payload too large."
    default_code = "payload_too_large"
