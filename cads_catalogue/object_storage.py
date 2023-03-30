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
import urllib.parse
import urllib.request

import minio  # type: ignore
import structlog
from minio import commonconfig, versioningconfig

from cads_catalogue import config

THIS_PATH = os.path.abspath(os.path.dirname(__file__))
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
            "Action": ["s3:GetObject",
                       "s3:GetObjectVersion"],
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
) -> tuple[str, str]:
    """Store a file in the object storage.

    Store a file at `file_path` in the object storage, in the bucket `bucket_name`.
    If subpath is supplied, the file is stored in subpath/file_name.
    If force is True, a bucket `bucket_name` is created if not existing. Note that in such case
    the bucket is versioned and with 'download' access policy for anonymous.
    Return the tuple (download_url, version), where:
    * download_url is the download URL of the stored file, relative to the object storage
    * version is the version stored in the object storage (None if not versioned)

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
            set_bucket_policy(client, bucket_name, "download")
        else:
            raise ValueError(
                "the bucket %r does not exist in the object storage" % bucket_name
            )
    file_name = os.path.basename(file_path)
    object_name = os.path.join(subpath, file_name)
    logger.debug(
        "BEGIN process to save file %s on object storage with name %s"
        % (file_name, object_name)
    )
    with open(file_path, "rb") as fp:
        text = fp.read()
        source_sha256 = hashlib.sha256(text).hexdigest()
        logger.debug(f"source_sha256: {source_sha256}")
    # check if destination already exists under some version
    # NOTE: 'include_user_meta' does not work, so use stat_object for the results
    existing_objects = client.list_objects(
        bucket_name, object_name, include_user_meta=True, include_version=True
    )
    for existing_object in existing_objects:
        version_id = existing_object.version_id
        logger.debug(f"found stored with version id: {version_id}")
        obj_with_metadata = client.stat_object(
            bucket_name, object_name, version_id=version_id
        )
        # NOTE: when writing, metadata keys are prefixed by "x-amz-meta-"
        destination_sha256 = obj_with_metadata.metadata.get("x-amz-meta-sha256")
        logger.debug(f"destination_sha256: {destination_sha256}")
        if destination_sha256 and destination_sha256 == source_sha256:
            # already on the object storage: do not upload
            logger.debug(
                f"NOT SAVING file: already found on object storage, version_id:{version_id}"
            )
            break
    else:  # never gone on break: effective upload
        logger.debug("confirm SAVING file: not found on object storage")
        res = client.fput_object(
            bucket_name, object_name, file_path, metadata={"sha256": source_sha256}
        )
        version_id = res.version_id
        logger.debug(f"new version_id: {version_id}")
    download_url = "%s/%s?versionId=%s" % (bucket_name, object_name, version_id)
    ret_value = (download_url, version_id)
    return ret_value


def test_bucket(
    storage_settings: config.ObjectStorageSettings,
    bucket_name: str = "cads-catalogue",
) -> None:
    logger.info("testing object storage capabilities")
    client = minio.Minio(
        urllib.parse.urlparse(storage_settings.object_storage_url).netloc,
        **storage_settings.storage_kws,
    )

    logger.info("test 1: prepare a versioning download bucket")
    if client.bucket_exists(bucket_name):
        logger.warning(f"the bucket {bucket_name} already exists")
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)
        set_bucket_policy(client, bucket_name, "download")
        client.set_bucket_versioning(
            bucket_name, versioningconfig.VersioningConfig(commonconfig.ENABLED)
        )
        logger.info(f"bucket {bucket_name} created")
    if not client.bucket_exists(bucket_name):
        logger.error(f"test 1 failed: bucket {bucket_name} not found")
        return
    logger.info("test 1 passed")

    logger.info("test 2: upload a file")
    file_path = os.path.abspath(
        os.path.join(
            THIS_PATH,
            "..",
            "tests",
            "data",
            "cads-forms-json",
            "cams-global-reanalysis-eac4",
            "overview.png",
        )
    )
    subpath = "testfiles"
    file_name = os.path.basename(file_path)
    object_name = file_name  # os.path.join(subpath, file_name)
    existing_objects = list(client.list_objects(
        bucket_name, object_name, include_user_meta=True, include_version=True
    ))
    if existing_objects:
        for existing_object in existing_objects:
            version_id = existing_object.version_id
            logger.warning(
                f"found {object_name} stored with version id: {version_id}. Try removing."
            )
            client.remove_object(bucket_name, object_name, version_id)
    existing_objects = list(client.list_objects(
            bucket_name, object_name, include_user_meta=True, include_version=True
        ))
    if existing_objects:
        logger.error(f"test 2 failed: object removal unsuccessful")
        return
    with open(file_path, "rb") as fp:
        text = fp.read()
        source_sha256 = hashlib.sha256(text).hexdigest()
        fp.seek(0)
        text = fp.read()
    res = client.fput_object(
        bucket_name, object_name, file_path, metadata={"sha256": source_sha256}
    )
    version_id = res.version_id
    existing_objects = list(client.list_objects(
        bucket_name, object_name, include_user_meta=True, include_version=True
    ))
    if not existing_objects:
        logger.error(
            f"test 2 failed: object {object_name} with version {version_id} not uploaded/found"
        )
        return
    how_many_found = 0
    found_right = 0
    for existing_object in existing_objects:
        how_many_found += 1
        obj_with_metadata = client.stat_object(
            bucket_name, object_name, version_id=existing_object.version_id
        )
        destination_sha256 = obj_with_metadata.metadata.get("x-amz-meta-sha256")
        if existing_object.version_id != version_id:
            logger.error(f"found object {object_name} with wrong version {version_id}")
        if destination_sha256 != source_sha256:
            logger.error(
                f"object {object_name} with version {version_id} "
                f"not uploaded with right sha256 {source_sha256}. Found sha256 {destination_sha256}"
            )
        if (
            existing_object.version_id == version_id
            and destination_sha256 == source_sha256
        ):
            found_right += 1
            logger.info(
                f"object {object_name} with version {version_id} found with right sha256 {source_sha256}"
            )
    if found_right == 1 and how_many_found == 1:
        logger.info("test 2 passed")
    else:
        logger.info(
            f"test 2 failed: found {found_right} right results, on total of {how_many_found} (expected: 1, 1)"
        )
        return

    logger.info("test 3: retrieving a version of a file")
    file_path2 = os.path.abspath(
        os.path.join(
            THIS_PATH,
            "..",
            "tests",
            "data",
            "cads-forms-json",
            "reanalysis-era5-land-monthly-means",
            "overview.png",
        )
    )
    with open(file_path2, "rb") as fp:
        text2 = fp.read()
        source_sha256_2 = hashlib.sha256(text2).hexdigest()
    assert source_sha256_2 != source_sha256
    res2 = client.fput_object(
        bucket_name, object_name, file_path2, metadata={"sha256": source_sha256_2}
    )
    version_id2 = res2.version_id
    if version_id2 == version_id:
        logger.error(
            f"test 3 failed: different object {object_name} generated with the same version {version_id2}"
        )
        return
    existing_objects = list(client.list_objects(
        bucket_name, object_name, include_user_meta=True, include_version=True
    ))
    if not existing_objects:
        logger.error(
            f"test 3 failed: no more found {object_name} with version {version_id2}"
        )
        return
    how_many_found = 0
    found_right = 0
    for existing_object in existing_objects:
        how_many_found += 1
        obj_with_metadata = client.stat_object(
            bucket_name, object_name, version_id=existing_object.version_id
        )
        destination_sha256 = obj_with_metadata.metadata.get("x-amz-meta-sha256")
        if (existing_object.version_id, destination_sha256) not in [
            (version_id, source_sha256),
            (version_id2, source_sha256_2),
        ]:
            logger.error(
                f"found object {object_name} with mismatch version/sha256 "
                f"{existing_object.version_id} / {destination_sha256}"
            )
        else:
            logger.info(f"found expected {object_name} with version {existing_object.version_id} and sha256 {destination_sha256}")
            found_right += 1
    if found_right == 2 and how_many_found == 2:
        logger.info("test 3 passed")
    else:
        logger.error(
            f"test 3 failed: found {found_right} right results, on total of {how_many_found}"
        )
    # # cleanup
    # existing_objects = client.list_objects(
    #     bucket_name, object_name, include_user_meta=True, include_version=True
    # )
    # for existing_object in existing_objects:
    #     client.remove_object(bucket_name, object_name, existing_object.version_id)
    # client.remove_bucket(bucket_name)
    # return

    logger.info(f"test 4: get specific version of an uploaded file")
    image_rel_url = "%s/%s?versionId=%s" % (bucket_name, object_name, version_id)
    image_url = urllib.parse.urljoin(storage_settings.document_storage_url, image_rel_url)
    resp = urllib.request.urlopen(image_url)
    if resp.status != 200:
        logger.error(f"test 4 failed: not reachable {image_url}, response status {resp.status}")
        return

    text_download = resp.read()
    if text_download != text:
        logger.error(f"test 4 failed: {image_url} at download is different from the uploaded one")
        logger.error(f"text2: {text_download[:100]}")
        logger.error(f"text1: {text[:100]}")
        logger.error(f"{image_url} has sha256: {hashlib.sha256(text_download).hexdigest()}")
    else:
        logger.info(f"test 4 passed")

    # client.get_object(bucket_name, object_name, version_id=version_id)
    # cleanup
    existing_objects = client.list_objects(
        bucket_name, object_name, include_user_meta=True, include_version=True
    )
    for existing_object in existing_objects:
        client.remove_object(bucket_name, object_name, existing_object.version_id)
    client.remove_bucket(bucket_name)
    return
