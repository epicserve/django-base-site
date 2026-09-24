"""Tests for the `ensure_s3_bucket` management command that the web container runs on boot."""

from io import StringIO
from unittest.mock import patch

from django.core.management import call_command

import pytest
from botocore.exceptions import ClientError

BOTO3_CLIENT = "apps.accounts.management.commands.ensure_s3_bucket.boto3.client"


def _client_error(code, operation):
    return ClientError({"Error": {"Code": code, "Message": code}}, operation)


def _run():
    out = StringIO()
    call_command("ensure_s3_bucket", stdout=out)
    return out.getvalue()


@pytest.fixture()
def s3_storage(settings):
    settings.STORAGES = {
        "default": {
            "BACKEND": "apps.base.storage.S3MediaStorage",
            "OPTIONS": {
                "bucket_name": "media",
                "endpoint_url": "http://silo:9000",
                "access_key": "siloadmin",
                "secret_key": "siloadmin",
            },
        },
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }


class TestEnsureS3Bucket:
    def test_skips_when_no_bucket_is_configured(self, settings):
        settings.STORAGES = {"default": {"BACKEND": "django.core.files.storage.FileSystemStorage"}}
        with patch(BOTO3_CLIENT) as client_factory:
            output = _run()
        assert "skipping" in output
        client_factory.assert_not_called()

    def test_existing_bucket_is_left_alone(self, s3_storage):
        with patch(BOTO3_CLIENT) as client_factory:
            s3 = client_factory.return_value
            output = _run()
        s3.head_bucket.assert_called_once_with(Bucket="media")
        s3.create_bucket.assert_not_called()
        assert 'Bucket "media" already exists.' in output

    def test_missing_bucket_is_created(self, s3_storage):
        with patch(BOTO3_CLIENT) as client_factory:
            s3 = client_factory.return_value
            s3.head_bucket.side_effect = _client_error("404", "HeadBucket")
            output = _run()
        s3.create_bucket.assert_called_once_with(Bucket="media")
        assert 'Created bucket "media".' in output

    def test_losing_the_create_race_counts_as_success(self, s3_storage):
        """Two processes see no bucket at once; the one whose create_bucket comes second must not crash."""
        with patch(BOTO3_CLIENT) as client_factory:
            s3 = client_factory.return_value
            s3.head_bucket.side_effect = _client_error("404", "HeadBucket")
            s3.create_bucket.side_effect = _client_error("BucketAlreadyOwnedByYou", "CreateBucket")
            output = _run()
        assert 'Bucket "media" already exists.' in output

    def test_other_create_errors_still_raise(self, s3_storage):
        with patch(BOTO3_CLIENT) as client_factory:
            s3 = client_factory.return_value
            s3.head_bucket.side_effect = _client_error("404", "HeadBucket")
            s3.create_bucket.side_effect = _client_error("AccessDenied", "CreateBucket")
            with pytest.raises(ClientError):
                _run()
