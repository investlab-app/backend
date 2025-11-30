import os

from storages.backends.s3boto3 import S3Boto3Storage


class S3MediaStorage(S3Boto3Storage):
    bucket_name = os.environ.get("MINIO_MEDIA_BUCKET_NAME", "media")
    file_overwrite = False
    default_acl = None
    querystring_auth = False


class S3StaticStorage(S3Boto3Storage):
    bucket_name = os.environ.get("MINIO_STATIC_BUCKET_NAME", "static")
    file_overwrite = True
    default_acl = None
    querystring_auth = False

    # Cache static files for 1 year (they're versioned via collectstatic)
    object_parameters = {
        "CacheControl": "max-age=31536000, public, immutable",
    }
