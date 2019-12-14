from django.contrib.staticfiles.storage import ManifestFilesMixin

from storages.backends.s3boto3 import S3Boto3Storage


class StaticS3Storage(ManifestFilesMixin, S3Boto3Storage):
    location = "static"


class MediaS3Storage(ManifestFilesMixin, S3Boto3Storage):
    location = "media"
