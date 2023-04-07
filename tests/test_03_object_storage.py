import hashlib
import json
import os
from typing import Any

import minio  # type: ignore
import pytest
import pytest_mock

from cads_catalogue import object_storage

THIS_PATH = os.path.abspath(os.path.dirname(__file__))
TESTDATA_PATH = os.path.join(THIS_PATH, "data")


@pytest.mark.filterwarnings("ignore:Exception ignored")
def test_store_file(mocker: pytest_mock.MockerFixture) -> None:
    object_storage_url = "http://myobject-storage:myport/"
    bucket_name = "cads-catalogue"
    ro_policy = json.dumps(object_storage.DOWNLOAD_POLICY_TEMPLATE) % {
        "bucket_name": bucket_name
    }
    storage_kws: dict[str, Any] = {
        "access_key": "storage_user",
        "secret_key": "storage_password",
        "secure": False,
    }
    file_path = os.path.join(
        TESTDATA_PATH, "cads-licences", "licence-to-use-copernicus-products.pdf"
    )
    with open(file_path, "rb") as fp:
        text = fp.read()
        sha256 = hashlib.sha256(text).hexdigest()
    expected_url = f"{bucket_name}/licence-to-use-copernicus-products_{sha256}.pdf"

    # patching the used Minio client APIs
    patch1 = mocker.patch.object(minio.Minio, "__init__", return_value=None)
    patch2 = mocker.patch.object(minio.Minio, "bucket_exists", return_value=False)
    patch3 = mocker.patch.object(minio.Minio, "make_bucket")
    patch6 = mocker.patch("minio.Minio.fput_object")
    patch7 = mocker.patch.object(minio.Minio, "set_bucket_policy")
    mocker.patch.object(minio.Minio, "list_objects", return_value=[])

    # run for a not existing file/not absolute path
    with pytest.raises(ValueError):
        object_storage.store_file("not/existing.png", object_storage_url, **storage_kws)

    # run without bucket_name nor subpath
    with pytest.raises(ValueError):
        # bucket name must exist if force is not used
        object_storage.store_file(file_path, object_storage_url, **storage_kws)
    patch1.reset_mock()
    patch2.reset_mock()

    res = object_storage.store_file(
        file_path, object_storage_url, force=True, **storage_kws
    )

    assert res == expected_url
    patch1.assert_called_once_with("myobject-storage:myport", **storage_kws)
    patch2.assert_called_once()
    patch3.assert_called_once_with("cads-catalogue")

    patch6.assert_called_once_with(
        bucket_name,
        f"licence-to-use-copernicus-products_{sha256}.pdf",
        file_path,
        content_type="application/pdf",
    )
    patch7.assert_called_once_with(bucket_name, ro_policy)

    # reset mocks
    for patch in [patch1, patch2, patch3, patch6, patch7]:
        patch.reset_mock()

    # calling with a subpath and a bucket
    subpath = "licences/mypath"
    bucket_name = "mybucket"
    expected_url = (
        f"{bucket_name}/licences/mypath/licence-to-use-copernicus-products_{sha256}.pdf"
    )

    ro_policy = json.dumps(object_storage.DOWNLOAD_POLICY_TEMPLATE) % {
        "bucket_name": bucket_name
    }
    res = object_storage.store_file(
        file_path, object_storage_url, bucket_name, subpath, force=True, **storage_kws
    )
    assert res == expected_url
    patch1.assert_called_once_with("myobject-storage:myport", **storage_kws)
    patch2.assert_called_once()
    patch3.assert_called_once_with("mybucket")
    patch6.assert_called_once_with(
        bucket_name,
        f"{subpath}/licence-to-use-copernicus-products_{sha256}.pdf",
        file_path,
        content_type="application/pdf",
    )
    patch7.assert_called_once_with(bucket_name, ro_policy)
