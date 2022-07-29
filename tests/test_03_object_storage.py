
import datetime
import json
import os
from typing import Any

import minio  # type: ignore
from minio import commonconfig, versioningconfig
import pytest

from cads_catalogue import object_storage

THIS_PATH = os.path.abspath(os.path.dirname(__file__))
TESTDATA_PATH = os.path.join(THIS_PATH, "data")


def get_ro_policy_dict(bucket_name, version):
    """Get the read-only policy dictionary for a bucket"""
    policy = {
        'Version': version,
        'Statement': [
            {
                'Action': ['s3:GetBucketLocation', 's3:ListBucket'],
                'Effect': 'Allow',
                'Principal': {'AWS': '*'},
                'Resource': ['arn:aws:s3:::%s' % bucket_name]
            },
            {
                'Action': ['s3:GetObject'],
                'Effect': 'Allow',
                'Principal': {'AWS': '*'},
                'Resource': ['arn:aws:s3:::%s/*' % bucket_name]
            }
        ],
    }
    return policy


@pytest.mark.filterwarnings("ignore:Exception ignored")
def test_store_file(mocker) -> None:
    expected_url = "a/relative/path/to/a/file"
    expected_version_id = "dfbd25b3-abec-4184-a4e8-5a35a5c1174d"
    object_storage_url = "http://myobject-storage:myport/"
    bucket_name = "cads-catalogue-bucket"
    ro_policy = get_ro_policy_dict(bucket_name, datetime.date.today().isoformat())
    storage_kws: dict[str, Any] = {
        "access_key": "storage_user",
        "secret_key": "storage_password",
        "secure": False,
    }
    file_path = os.path.join(
        TESTDATA_PATH, "cds-licences", "licence-to-use-copernicus-products.pdf")
    # patching the used Minio client APIs
    patch1 = mocker.patch.object(minio.Minio, "__init__", return_value=None)
    patch2 = mocker.patch.object(minio.Minio, "bucket_exists", return_value=False)
    patch3 = mocker.patch.object(minio.Minio, "make_bucket")
    patch5 = mocker.patch.object(minio.Minio, "set_bucket_versioning")
    patch6 = mocker.patch("minio.Minio.fput_object")
    patch6.return_value.version_id = expected_version_id
    patch7 = mocker.patch.object(
        minio.Minio, "presigned_get_object", return_value=f"{object_storage_url}{expected_url}")
    patch8 = mocker.patch.object(minio.Minio, "set_bucket_policy")

    # run for a not existing file/not absolute path
    with pytest.raises(ValueError):
        object_storage.store_file("not/existing.png", object_storage_url, **storage_kws)

    # run without bucket_name nor subpath
    with pytest.raises(ValueError):
        # bucket name must exist if force is not used
        object_storage.store_file(file_path, object_storage_url, **storage_kws)
    patch1.reset_mock()
    patch2.reset_mock()

    res = object_storage.store_file(file_path, object_storage_url, force=True, **storage_kws)

    assert res == (expected_url, expected_version_id)
    patch1.assert_called_once_with("myobject-storage:myport", **storage_kws)
    patch2.assert_called_once()
    patch3.assert_called_once_with("cads-catalogue-bucket")
    assert patch5.call_args_list[0][0][0] == "cads-catalogue-bucket"
    assert isinstance(patch5.call_args_list[0][0][1], versioningconfig.VersioningConfig)
    assert patch5.call_args_list[0][0][1].status == commonconfig.ENABLED
    patch6.assert_called_once_with(
        bucket_name, "licence-to-use-copernicus-products.pdf", file_path)
    patch7.assert_called_once_with(bucket_name, "licence-to-use-copernicus-products.pdf")
    patch8.assert_called_once_with(bucket_name, json.dumps(ro_policy))

    # reset mocks
    for patch in [patch1, patch2, patch3, patch5, patch6, patch7, patch8]:
        patch.reset_mock()

    # calling with a subpath and a bucket
    subpath = "licences/mypath"
    bucket_name = "mybucket"
    ro_policy = get_ro_policy_dict(bucket_name, datetime.date.today().isoformat())
    res = object_storage.store_file(
        file_path, object_storage_url, bucket_name, subpath, force=True, **storage_kws
    )

    assert res == (expected_url, expected_version_id)
    patch1.assert_called_once_with("myobject-storage:myport", **storage_kws)
    patch2.assert_called_once()
    patch3.assert_called_once_with("mybucket")
    assert patch5.call_args_list[0][0][0] == "mybucket"
    assert isinstance(patch5.call_args_list[0][0][1], versioningconfig.VersioningConfig)
    assert patch5.call_args_list[0][0][1].status == commonconfig.ENABLED
    patch6.assert_called_once_with(
        bucket_name, "licences/mypath/licence-to-use-copernicus-products.pdf", file_path)
    patch7.assert_called_once_with(
        bucket_name, "licences/mypath/licence-to-use-copernicus-products.pdf")
    patch8.assert_called_once_with(bucket_name, json.dumps(ro_policy))
