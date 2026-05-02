from django.contrib.staticfiles.storage import ManifestFilesMixin

from storages.backends.s3boto3 import S3Boto3Storage


class StaticS3Storage(ManifestFilesMixin, S3Boto3Storage):
    location = "static"


class MediaS3Storage(ManifestFilesMixin, S3Boto3Storage):
    """Legacy AWS S3 media storage with manifest hashing (kept for backwards-compat with the AWS path)."""

    location = "media"


class S3MediaStorage(S3Boto3Storage):
    """
    S3-compatible storage that uses a separate endpoint for browser-facing URLs.

    In local dev, the S3 API endpoint is http://minio:9000 (Docker-internal),
    but browser-accessible URLs must use http://localhost:9000. Setting
    ``url_endpoint_url`` replaces the internal endpoint in generated URLs
    while keeping the internal endpoint for actual file operations.
    """

    def __init__(self, **kwargs):
        self._url_endpoint_url = kwargs.pop("url_endpoint_url", None)
        super().__init__(**kwargs)

    def url(self, name, parameters=None, expire=None, http_method=None):
        result = super().url(name, parameters=parameters, expire=expire, http_method=http_method)
        if self._url_endpoint_url and self.endpoint_url:
            result = result.replace(self.endpoint_url, self._url_endpoint_url, 1)
        return result
