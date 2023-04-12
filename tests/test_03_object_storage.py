import hashlib
import json
import os
from typing import Any

import botocore
import pytest
import pytest_mock

from cads_catalogue import object_storage

THIS_PATH = os.path.abspath(os.path.dirname(__file__))
TESTDATA_PATH = os.path.join(THIS_PATH, "data")


class DummyBotoClient:
    def __init__(self, resource, endpoint_url=None, **storage_kws):
        self.resource = resource
        self.endpoint_url = endpoint_url
        self.storage_kws = storage_kws

    def head_bucket(self, Bucket):
        error_response = {"Error": {"Code": "404"}}
        error = botocore.exceptions.ClientError(error_response, "head bucket")
        raise error

    def create_bucket(self, Bucket):
        pass

    def put_bucket_policy(self, Bucket, Policy):
        pass

    def head_object(self, Bucket, Key):
        error_response = {"Error": {"Code": "404"}}
        error = botocore.exceptions.ClientError(error_response, "head object")
        raise error

    def get_bucket_cors(self, Bucket):
        error_response = {"Error": {"Code": "NoSuchCORSConfiguration"}}
        error = botocore.exceptions.ClientError(error_response, "get bucket cors")
        raise error

    def put_bucket_cors(self, Bucket, CORSConfiguration):
        pass

    def upload_file(self, Filename, Bucket, Key, ExtraArgs):
        pass


def new_dummy_boto_client(*args, **kwargs):
    return DummyBotoClient(*args, **kwargs)


@pytest.mark.filterwarnings("ignore:Exception ignored")
def test_store_file(mocker: pytest_mock.MockerFixture) -> None:
    object_storage_url = "http://myobject-storage:myport/"
    bucket_name = "cads-catalogue"
    json.dumps(object_storage.DOWNLOAD_POLICY_TEMPLATE) % {"bucket_name": bucket_name}
    storage_kws: dict[str, Any] = {
        "aws_access_key_id": "storage_user",
        "aws_secret_access_key": "storage_password",
    }
    file_path = os.path.join(
        TESTDATA_PATH, "cads-licences", "licence-to-use-copernicus-products.pdf"
    )
    with open(file_path, "rb") as fp:
        text = fp.read()
        sha256 = hashlib.sha256(text).hexdigest()
    expected_url = f"{bucket_name}/licence-to-use-copernicus-products_{sha256}.pdf"

    # run for a not existing file/not absolute path
    use_client = DummyBotoClient("S3", endpoint_url=object_storage_url, **storage_kws)
    with pytest.raises(ValueError):
        object_storage.store_file(
            "not/existing.png", object_storage_url, use_client=use_client, **storage_kws
        )

    # run without bucket_name nor subpath
    with pytest.raises(ValueError):
        # bucket name must exist if force is not used
        object_storage.store_file(
            file_path, object_storage_url, use_client=use_client, **storage_kws
        )

    # spies
    head_bucket = mocker.spy(DummyBotoClient, "head_bucket")
    create_bucket = mocker.spy(DummyBotoClient, "create_bucket")
    put_bucket_policy = mocker.spy(DummyBotoClient, "put_bucket_policy")
    head_object = mocker.spy(DummyBotoClient, "head_object")
    upload_file = mocker.spy(DummyBotoClient, "upload_file")
    get_bucket_cors = mocker.spy(DummyBotoClient, "get_bucket_cors")
    put_bucket_cors = mocker.spy(DummyBotoClient, "put_bucket_cors")

    res = object_storage.store_file(
        file_path, object_storage_url, force=True, use_client=use_client, **storage_kws
    )

    assert res == expected_url

    # check spies
    head_bucket.assert_called_once()
    create_bucket.assert_called_once_with(use_client, Bucket="cads-catalogue")
    put_bucket_policy.assert_called_once_with(
        use_client,
        Bucket="cads-catalogue",
        Policy='{"Version": "2012-10-17", "Statement": '
        '[{"Action": ["s3:GetBucketLocation", "s3:ListBucket"], '
        '"Effect": "Allow", "Principal": {"AWS": ["*"]}, "Resource": '
        '["arn:aws:s3:::cads-catalogue"]}, '
        '{"Action": ["s3:GetObject", "s3:GetObjectVersion"], '
        '"Effect": "Allow", "Principal": '
        '{"AWS": ["*"]}, "Resource": ["arn:aws:s3:::cads-catalogue/*"]}]}',
    )
    head_object.assert_called_once_with(
        use_client,
        Bucket=bucket_name,
        Key=f"licence-to-use-copernicus-products_{sha256}.pdf",
    )
    upload_file.assert_called_once_with(
        use_client,
        Filename=file_path,
        Bucket=bucket_name,
        Key=f"licence-to-use-copernicus-products_{sha256}.pdf",
        ExtraArgs={"ContentType": "application/pdf"},
    )
    get_bucket_cors.assert_called_once_with(use_client, Bucket=bucket_name)
    put_bucket_cors.assert_called_once_with(
        use_client,
        Bucket=bucket_name,
        CORSConfiguration=object_storage.CORS_CONFIG,
    )

    for spy in [
        head_bucket,
        create_bucket,
        put_bucket_policy,
        head_object,
        upload_file,
        get_bucket_cors,
        put_bucket_cors,
    ]:
        spy.reset_mock()

    # calling with a subpath and a bucket
    subpath = "licences/mypath"
    bucket_name = "mybucket"
    expected_url = (
        f"{bucket_name}/licences/mypath/licence-to-use-copernicus-products_{sha256}.pdf"
    )

    json.dumps(object_storage.DOWNLOAD_POLICY_TEMPLATE) % {"bucket_name": bucket_name}
    res = object_storage.store_file(
        file_path,
        object_storage_url,
        bucket_name,
        subpath,
        use_client=use_client,
        force=True,
        **storage_kws,
    )
    assert res == expected_url

    # check spies
    head_bucket.assert_called_once()
    create_bucket.assert_called_once_with(use_client, Bucket=bucket_name)
    put_bucket_policy.assert_called_once_with(
        use_client,
        Bucket=bucket_name,
        Policy='{"Version": "2012-10-17", "Statement": '
        '[{"Action": ["s3:GetBucketLocation", "s3:ListBucket"], '
        '"Effect": "Allow", "Principal": {"AWS": ["*"]}, '
        '"Resource": ["arn:aws:s3:::mybucket"]}, '
        '{"Action": ["s3:GetObject", "s3:GetObjectVersion"], '
        '"Effect": "Allow", "Principal": '
        '{"AWS": ["*"]}, "Resource": ["arn:aws:s3:::mybucket/*"]}]}',
    )
    head_object.assert_called_once_with(
        use_client,
        Bucket=bucket_name,
        Key=f"licences/mypath/licence-to-use-copernicus-products_{sha256}.pdf",
    )
    upload_file.assert_called_once_with(
        use_client,
        Bucket=bucket_name,
        Key=f"licences/mypath/licence-to-use-copernicus-products_{sha256}.pdf",
        Filename=file_path,
        ExtraArgs={"ContentType": "application/pdf"},
    )
    get_bucket_cors.assert_called_once_with(use_client, Bucket=bucket_name)
    put_bucket_cors.assert_called_once_with(
        use_client,
        Bucket=bucket_name,
        CORSConfiguration=object_storage.CORS_CONFIG,
    )
