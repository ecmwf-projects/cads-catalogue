"""utility module to interface to the object storage."""

# Copyright 2022, European Union.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import hashlib
import json
import os
import pathlib
from typing import Any

import boto3
import botocore
import structlog

from cads_catalogue import utils

logger = structlog.get_logger(__name__)

DOWNLOAD_POLICY_TEMPLATE: dict[str, Any] = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": ["s3:GetBucketLocation", "s3:ListBucket"],
            "Effect": "Allow",
            "Principal": {"AWS": ["*"]},
            "Resource": ["arn:aws:s3:::%(bucket_name)s"],
        },
        {
            "Action": ["s3:GetObject", "s3:GetObjectVersion"],
            "Effect": "Allow",
            "Principal": {"AWS": ["*"]},
            "Resource": ["arn:aws:s3:::%(bucket_name)s/*"],
        },
    ],
}
PRIVATE_POLICY_TEMPLATE: dict[str, Any] = {}
PUBLIC_POLICY_TEMPLATE: dict[str, Any] = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": [
                "s3:GetBucketLocation",
                "s3:ListBucket",
                "s3:ListBucketMultipartUploads",
            ],
            "Effect": "Allow",
            "Principal": {"AWS": ["*"]},
            "Resource": ["arn:aws:s3:::%(bucket_name)s"],
        },
        {
            "Action": [
                "s3:PutObject",
                "s3:AbortMultipartUpload",
                "s3:DeleteObject",
                "s3:GetObject",
                "s3:GetObjectVersion",
                "s3:ListMultipartUploadParts",
            ],
            "Effect": "Allow",
            "Principal": {"AWS": ["*"]},
            "Resource": ["arn:aws:s3:::%(bucket_name)s/*"],
        },
    ],
}
UPLOAD_POLICY_TEMPLATE: dict[str, Any] = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": ["s3:GetBucketLocation", "s3:ListBucketMultipartUploads"],
            "Effect": "Allow",
            "Principal": {"AWS": ["*"]},
            "Resource": ["arn:aws:s3:::%(bucket_name)s"],
        },
        {
            "Action": [
                "s3:AbortMultipartUpload",
                "s3:DeleteObject",
                "s3:ListMultipartUploadParts",
                "s3:PutObject",
            ],
            "Effect": "Allow",
            "Principal": {"AWS": ["*"]},
            "Resource": ["arn:aws:s3:::%(bucket_name)s/*"],
        },
    ],
}

CORS_CONFIG: dict[str, Any] = {
    "CORSRules": [
        {
            "AllowedHeaders": ["Accept", "Content-Type"],
            "AllowedMethods": ["GET", "HEAD"],
            "AllowedOrigins": ["*"],
        }
    ]
}


def set_bucket_policy(
    client: boto3.session.Session.client, bucket_name: str, policy: str  # type: ignore
) -> None:
    """Set anonymous policy to a bucket.

    Parameters
    ----------
    client: boto3 client object
    bucket_name: name of the bucket
    policy: one of 'private', 'public', 'upload', 'download'
    """
    policy_map = {
        "download": DOWNLOAD_POLICY_TEMPLATE,
        "private": PRIVATE_POLICY_TEMPLATE,
        "public": PUBLIC_POLICY_TEMPLATE,
        "upload": UPLOAD_POLICY_TEMPLATE,
    }
    policy_json = json.dumps(policy_map[policy]) % {"bucket_name": bucket_name}
    client.put_bucket_policy(Bucket=bucket_name, Policy=policy_json)  # type: ignore


def set_bucket_cors(
    client: boto3.session.Session.client,  # type: ignore
    bucket_name: str,
    config: dict[str, Any] | None = None,
) -> None:
    """Configure CORS for the bucket.

    Parameters
    ----------
    client: boto3 client object
    bucket_name: name of the bucket
    config: CORS configuration to use (default is CORS_CONFIG)
    """
    if config is None:
        config = CORS_CONFIG
    client.put_bucket_cors(Bucket=bucket_name, CORSConfiguration=config)  # type: ignore


def store_file(
    file_path: str | pathlib.Path,
    object_storage_url: str,  # type: ignore
    bucket_name: str = "cads-catalogue",  # type: ignore
    subpath: str = "",
    force: bool = False,
    use_client: Any = None,
    **storage_kws: Any,
) -> str:
    """Store a file in the object storage.

    Store a file at `file_path` in the object storage, in the bucket `bucket_name`.
    If subpath is supplied, the file is stored in subpath/file_name.
    If force is True, a bucket `bucket_name` is created if not existing. Note that in such case
    the bucket has 'download' access policy for anonymous.
    Return the download URL of the stored file, relative to the object storage.

    Parameters
    ----------
    file_path: absolute path to the file to store
    object_storage_url: endpoint URL of the object storage
    bucket_name: name of the bucket to use inside the object storage
    subpath: optional folder path inside the bucket (created if not existing)
    force: if True, force to create the bucket if not existing (default to False)
    use_client: if specified, use this client instead of a new boto3 client (used in tests)
    storage_kws: dictionary of parameters used to pass to the storage client

    Returns
    -------
    tuple[str, str]: the tuple (download url, version)
    """
    if not file_path or not os.path.isabs(file_path) or not os.path.exists(file_path):
        raise ValueError(
            "file not found or not provided as absolute path: %r" % file_path
        )
    if use_client:
        client = use_client
    else:
        client = boto3.client("s3", endpoint_url=object_storage_url, **storage_kws)
    # NOTE: version retrieval is not supported in the public endpoint of the storage,
    # so the file is stored using a prefix including the SHA256 hash of the file content
    try:
        client.head_bucket(Bucket=bucket_name)
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "404":  # bucket does not exist
            if force:
                client.create_bucket(Bucket=bucket_name)
                set_bucket_policy(client, bucket_name, "download")
            else:
                raise ValueError(
                    "the bucket %r does not exist in the object storage" % bucket_name
                )
    try:
        client.get_bucket_cors(Bucket=bucket_name)
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchCORSConfiguration":
            set_bucket_cors(client, bucket_name)
    with open(file_path, "rb") as fp:
        data = fp.read()
        source_sha256 = hashlib.sha256(data).hexdigest()
    file_name = os.path.basename(file_path)
    file_prefix, file_ext = os.path.splitext(file_name)
    object_name = os.path.join(subpath, f"{file_prefix}_{source_sha256}{file_ext}")
    try:
        client.head_object(Bucket=bucket_name, Key=object_name)
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "404":  # file does not exist
            client.upload_file(
                Filename=file_path,
                Bucket=bucket_name,
                Key=object_name,
                ExtraArgs={"ContentType": utils.guess_type(file_name)},
            )

    download_rel_url = "%s/%s" % (bucket_name, object_name)
    return download_rel_url


def delete_bucket(
    bucket_name: str, object_storage_url: str, force: bool = False, **storage_kws: Any
) -> None:
    """
    Delete a bucket.

    Parameters
    ----------
    bucket_name: name of the bucket to use inside the object storage
    object_storage_url: endpoint URL of the object storage
    force: if True, remove also a not empty bucket (default False)
    storage_kws: dictionary of parameters used to pass to the storage client
    """
    client = boto3.client("s3", endpoint_url=object_storage_url, **storage_kws)
    try:
        client.head_bucket(Bucket=bucket_name)
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "404":  # bucket does not exist
            logger.warning(f"bucket {bucket_name} does not exist")
        return
    try:
        client.delete_bucket(Bucket=bucket_name)
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "BucketNotEmpty":
            if force:
                for i, obj in enumerate(
                    client.list_objects_v2(Bucket=bucket_name)["Contents"]
                ):
                    client.delete_object(Bucket=bucket_name, Key=obj["Key"])
                    if i % 1000 == 0:
                        logger.info(
                            f"removed %i files from the bucket {bucket_name}..."
                        )
            else:
                logger.error(f"bucket {bucket_name} is not empty")
    logger.info(f"bucket {bucket_name} successfully removed")
