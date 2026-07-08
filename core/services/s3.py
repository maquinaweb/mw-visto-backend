from io import BytesIO
from os.path import join
from uuid import uuid4

import boto3
from django.conf import settings


class S3Utils:
    def __init__(self) -> None:
        if settings.AWS_PROFILE:
            session = boto3.Session(profile_name=settings.AWS_PROFILE)
        else:
            session = boto3.Session()

        self.s3_client = session.client(
            "s3",
            region_name=settings.AWS_S3_REGION_NAME,
            endpoint_url=f"https://s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com",
        )

    def presign_url(self, path: str, file: dict):
        data = self.generate_presigned_url(
            join(
                settings.PUBLIC_MEDIA_LOCATION,
                path,
                f"{uuid4()}.{file.get('name').split('.')[-1].lower()}",
            ),
            file,
        )
        return data

    def presign_urls(self, path: str, files: list):
        return [
            self.presign_url(
                path,
                file,
            )
            for file in files
        ]

    def generate_presigned_url(self, key: str, file: dict):
        response = self.s3_client.generate_presigned_post(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=key,
            Fields={"Content-Type": file.get("type", ""), "key": key},
            Conditions=[
                ["starts-with", "$Content-Type", ""],
                ["content-length-range", 0, settings.MAX_UPLOAD_SIZE],
            ],
            ExpiresIn=3600,
        )
        return {"url": response["url"], "fields": response["fields"]}

    def upload_file(self, file_obj: BytesIO, key: str, content_type: str):
        self.s3_client.upload_fileobj(
            file_obj,
            settings.AWS_STORAGE_BUCKET_NAME,
            join(settings.PUBLIC_MEDIA_LOCATION, key),
            ExtraArgs={"ContentType": content_type},
        )
