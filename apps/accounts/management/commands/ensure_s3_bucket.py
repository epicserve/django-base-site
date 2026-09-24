from django.conf import settings
from django.core.management.base import BaseCommand

import boto3
from botocore.exceptions import ClientError


class Command(BaseCommand):
    help = "Ensure the S3 (Silo locally) media bucket exists."

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
        except ClientError:
            pass
        else:
            self.stdout.write(f'Bucket "{bucket_name}" already exists.')
            return

        try:
            s3.create_bucket(Bucket=bucket_name)
        except ClientError as exc:
            # Another process (e.g. a second container booting at the same time) won the race
            # between head_bucket and create_bucket. The bucket exists, which is all this
            # command guarantees, so report it as such. Any other failure still raises.
            if exc.response.get("Error", {}).get("Code") != "BucketAlreadyOwnedByYou":
                raise
            self.stdout.write(f'Bucket "{bucket_name}" already exists.')
            return
        self.stdout.write(f'Created bucket "{bucket_name}".')
