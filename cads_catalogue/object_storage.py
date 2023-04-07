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
import urllib.parse
from typing import Any

import minio  # type: ignore
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


def set_bucket_policy(client: minio.api.Minio, bucket_name: str, policy: str) -> None:
    """Set anonymous policy to a bucket.

    Parameters
    ----------
    client: minio client object
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
    client.set_bucket_policy(bucket_name, policy_json)


def store_file(
    file_path: str | pathlib.Path,
    object_storage_url: str,  # type: ignore
    bucket_name: str = "cads-catalogue",  # type: ignore
    subpath: str = "",
    force: bool = False,
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
    storage_kws: dictionary of parameters used to pass to the storage client

    Returns
    -------
    tuple[str, str]: the tuple (download url, version)
    """
    if not file_path or not os.path.isabs(file_path) or not os.path.exists(file_path):
        raise ValueError(
            "file not found or not provided as absolute path: %r" % file_path
        )
    client = minio.Minio(
        urllib.parse.urlparse(object_storage_url).netloc, **storage_kws
    )
    # NOTE: version retrieval is not supported in the public endpoint of the storage,
    # so the file is stored using a prefix including the SHA256 hash of the file content
    if not client.bucket_exists(bucket_name):
        if force:
            client.make_bucket(bucket_name)
            set_bucket_policy(client, bucket_name, "download")
        else:
            raise ValueError(
                "the bucket %r does not exist in the object storage" % bucket_name
            )
    with open(file_path, "rb") as fp:
        data = fp.read()
        source_sha256 = hashlib.sha256(data).hexdigest()
    file_name = os.path.basename(file_path)
    file_prefix, file_ext = os.path.splitext(file_name)
    object_name = os.path.join(subpath, f"{file_prefix}_{source_sha256}{file_ext}")

    existing_objects = list(client.list_objects(bucket_name, object_name))
    if not existing_objects:
        client.fput_object(
            bucket_name,
            object_name,
            file_path,
            content_type=utils.guess_type(file_name),
        )
    download_rel_url = "%s/%s" % (bucket_name, object_name)
    return download_rel_url
