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

import json
import os
import pathlib
import urllib.parse
from typing import Any

import minio  # type: ignore
from minio import commonconfig, versioningconfig


def set_readwrite_bucket_policy(client: minio.api.Minio, bucket_name: str) -> None:
    """Set anonymous read-write policy to a bucket.

    Parameters
    ----------
    client: minio client object
    bucket_name: name of the bucket
    """
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"AWS": "*"},
                "Action": [
                    "s3:GetBucketLocation",
                    "s3:ListBucket",
                    "s3:ListBucketMultipartUploads",
                ],
                "Resource": "arn:aws:s3:::%s" % bucket_name,
            },
            {
                "Effect": "Allow",
                "Principal": {"AWS": "*"},
                "Action": [
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:DeleteObject",
                    "s3:ListMultipartUploadParts",
                    "s3:AbortMultipartUpload",
                ],
                "Resource": "arn:aws:s3:::%s/*" % bucket_name,
            },
        ],
    }
    client.set_bucket_policy(bucket_name, json.dumps(policy))


def set_readonly_bucket_policy(client, bucket_name):
    """Set anonymous read-only policy to a bucket.

    Parameters
    ----------
    client: minio client object
    bucket_name: name of the bucket
    """
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Action": ["s3:GetBucketLocation", "s3:ListBucket"],
                "Effect": "Allow",
                "Principal": {"AWS": "*"},
                "Resource": ["arn:aws:s3:::%s" % bucket_name],
            },
            {
                "Action": ["s3:GetObject"],
                "Effect": "Allow",
                "Principal": {"AWS": "*"},
                "Resource": ["arn:aws:s3:::%s/*" % bucket_name],
            },
        ],
    }
    client.set_bucket_policy(bucket_name, json.dumps(policy))


def store_file(
    file_path: str | pathlib.Path,
    object_storage_url: str,
    bucket_name: str = "cads-catalogue-bucket",
    subpath: str = "",
    force: bool = False,
    **storage_kws: Any,
) -> tuple[str, str]:
    """Store a file in the object storage.

    Store a file at `file_path` in the object storage, in the bucket `bucket_name`.
    If subpath is supplied, the file is stored in subpath/file_name.
    If force is True, a (versioned and read-only) bucket `bucket_name` is created
    if not exists.
    Return the tuple (download_url, version), where:
    * download_url is the download URL of the stored file relative to the object storage
    * version is the version stored in the object storage ('unversioned' if not versioned)

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
    if not client.bucket_exists(bucket_name):
        if force:
            client.make_bucket(bucket_name)
            client.set_bucket_versioning(
                bucket_name, versioningconfig.VersioningConfig(commonconfig.ENABLED)
            )
            set_readonly_bucket_policy(client, bucket_name)
        else:
            raise ValueError(
                "the bucket %r does not exist in the object storage" % bucket_name
            )
    file_name = os.path.basename(file_path)
    object_name = os.path.join(subpath, file_name)
    res = client.fput_object(bucket_name, object_name, file_path)
    version_id = res.version_id
    download_url = "%s/%s?versionId=%s" % (bucket_name, object_name, version_id)
    ret_value = (download_url, version_id)
    return ret_value
