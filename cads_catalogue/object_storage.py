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
import os
import pathlib
from typing import Any

import boto3
import botocore
import structlog

from cads_catalogue import utils

logger = structlog.get_logger(__name__)


DEFAULT_CORS_CONFIG: dict[str, Any] = {
    "CORSRules": [
        {
            "AllowedHeaders": ["Accept", "Content-Type"],
            "AllowedMethods": ["GET", "HEAD"],
            "AllowedOrigins": ["*"],
        }
    ]
}


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
        config = DEFAULT_CORS_CONFIG
    client.put_bucket_cors(Bucket=bucket_name, CORSConfiguration=config)  # type: ignore


def is_bucket_read_only(client, bucket_name) -> bool:
    """Return True if the bucket is read-only for all users."""
    response = client.get_bucket_acl(Bucket=bucket_name)
    try:
        for grant in response["Grants"]:
            grantee = grant["Grantee"]
            if (
                grantee["Type"] == "Group"
                and grantee["URI"] == "http://acs.amazonaws.com/groups/global/AllUsers"
            ):
                return grant["Permission"] == "READ"
    except KeyError:
        logger.error(f"ACL of bucket {bucket_name} not parsable")
    return False


def is_bucket_existing(client, bucket_name) -> bool | None:
    """Return True if the bucket exists."""
    try:
        client.head_bucket(Bucket=bucket_name)
        return True
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return False
    return None


def is_bucket_cors_set(client, bucket_name) -> bool | None:
    """Return True if the bucket has CORS already set."""
    ret_value = None
    try:
        client.get_bucket_cors(Bucket=bucket_name)
        ret_value = True
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchCORSConfiguration":
            ret_value = False
    return ret_value


def is_object_read_only(client, bucket, object_name):
    """Return True if the object is stored with ACL read-only."""
    response = client.get_object_acl(Bucket=bucket, Key=object_name)
    try:
        for grant in response["Grants"]:
            grantee = grant["Grantee"]
            if (
                grantee["Type"] == "Group"
                and grantee["URI"] == "http://acs.amazonaws.com/groups/global/AllUsers"
            ):
                return grant["Permission"] == "READ"
    except KeyError:
        logger.error(f"ACL of object {bucket}/{object_name} not parsable")
    return False


def setup_bucket(client, bucket_name) -> None:
    """Create a public-read bucket (if not existing) and setup CORS."""
    if not is_bucket_existing(client, bucket_name):
        logger.info(f"creation of bucket {bucket_name}")
        client.create_bucket(Bucket=bucket_name)
        logger.info(f"setup ACL public-read on bucket {bucket_name}")
        client.put_bucket_acl(ACL="public-read", Bucket=bucket_name)
    else:
        if not is_bucket_read_only(client, bucket_name):
            logger.warning(f"setting ACL public-read on bucket {bucket_name}")
            client.put_bucket_acl(ACL="public-read", Bucket=bucket_name)

    if not is_bucket_cors_set(client, bucket_name):
        logger.warning(f"setting CORS policy on bucket {bucket_name}")
        try:
            client.put_bucket_cors(
                Bucket=bucket_name, CORSConfiguration=DEFAULT_CORS_CONFIG
            )
        except Exception:
            logger.warning(f"unable to set CORS policy on bucket {bucket_name}")


def store_file(
    file_path: str | pathlib.Path,
    object_storage_url: str,  # type: ignore
    bucket_name: str = "cads-catalogue",  # type: ignore
    subpath: str = "",
    use_client: Any = None,
    **storage_kws: Any,
) -> str:
    """Store a file in the object storage.

    Store a file at `file_path` in the object storage, in the bucket `bucket_name`.
    If subpath is supplied, the file is stored in subpath/file_name.
    Return the download URL of the stored file, relative to the object storage.

    Parameters
    ----------
    file_path: absolute path to the file to store
    object_storage_url: endpoint URL of the object storage
    bucket_name: name of the bucket to use inside the object storage
    subpath: optional folder path inside the bucket (created if not existing)
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
    setup_bucket(client, bucket_name)
    # NOTE: version retrieval is not supported in the public endpoint of the storage,
    # so the file is stored using a prefix including the SHA256 hash of the file content
    with open(file_path, "rb") as fp:
        data = fp.read()
        source_sha256 = hashlib.sha256(data).hexdigest()
    file_name = os.path.basename(file_path)
    file_prefix, file_ext = os.path.splitext(file_name)
    object_name = os.path.join(subpath, f"{file_prefix}_{source_sha256}{file_ext}")
    try:
        client.head_object(Bucket=bucket_name, Key=object_name)
        logger.debug(f"file {object_name} already existing on bucket {bucket_name}")
    except botocore.exceptions.ClientError as e:
        logger.info(f"uploading file {object_name} on bucket {bucket_name}")
        if e.response["Error"]["Code"] == "404":  # file does not exist
            client.upload_file(
                Filename=file_path,
                Bucket=bucket_name,
                Key=object_name,
                ExtraArgs={
                    "ContentType": utils.guess_type(file_name),
                    "ACL": "public-read",
                },
            )
    else:
        if not is_object_read_only(client, bucket_name, object_name):
            logger.info(
                f"setting ACL read-only on object {object_name} on bucket {bucket_name}"
            )
            client.put_object_acl(
                Bucket=bucket_name, Key=object_name, ACL="public-read"
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
                s3 = boto3.resource(
                    "s3", endpoint_url=object_storage_url, **storage_kws
                )
                bucket = s3.Bucket(bucket_name)
                bucket_versioning = s3.BucketVersioning(bucket_name)
                if bucket_versioning.status == "Enabled":
                    bucket.object_versions.delete()
                else:
                    bucket.objects.all().delete()
                client.delete_bucket(Bucket=bucket_name)
            else:
                logger.error(f"bucket {bucket_name} is not empty")
    logger.info(f"bucket {bucket_name} successfully removed")
