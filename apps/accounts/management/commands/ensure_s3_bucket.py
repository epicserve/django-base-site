from django.conf import settings
from django.core.management.base import BaseCommand

import boto3
from botocore.exceptions import ClientError


class Command(BaseCommand):
    help = "Ensure the S3/MinIO media bucket exists."

    def handle(self, *args, **options):
        storage_opts = settings.STORAGES.get("default", {}).get("OPTIONS", {})
        bucket_name = storage_opts.get("bucket_name")
        if not bucket_name:
            self.stdout.write("No S3 bucket configured, skipping.")
            return

        endpoint_url = storage_opts.get("endpoint_url")
        s3 = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=storage_opts.get("access_key"),
            aws_secret_access_key=storage_opts.get("secret_key"),
        )
        try:
            s3.head_bucket(Bucket=bucket_name)
            self.stdout.write(f'Bucket "{bucket_name}" already exists.')
        except ClientError:
            s3.create_bucket(Bucket=bucket_name)
            self.stdout.write(f'Created bucket "{bucket_name}".')
