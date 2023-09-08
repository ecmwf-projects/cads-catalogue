import hashlib
import os
from typing import Any

import botocore
import pytest
import pytest_mock

from cads_catalogue import object_storage, utils

THIS_PATH = os.path.abspath(os.path.dirname(__file__))
TESTDATA_PATH = os.path.join(THIS_PATH, "data")


class DummyStorageObject:
    """Simulate an object stored."""

    def __init__(self, name, extra_args=None):
        self.name = name
        if extra_args is None:
            extra_args = dict()
        new_extra_args = extra_args.copy()
        acl = new_extra_args.pop("ACL", None)
        if acl and acl != "public-read":
            raise NotImplementedError
        self.acl = {
            "ResponseMetadata": {
                "RequestId": "a-request-id",
                "HTTPStatusCode": 200,
            },
            "Grants": [
                {
                    "Grantee": {
                        "Type": "Group",
                        "URI": "http://acs.amazonaws.com/groups/global/AllUsers",
                    },
                    "Permission": "READ",
                },
            ],
        }
        for key, value in new_extra_args.items():
            setattr(self, key, value)


class DummyBucket:
    """Simulate a bucket."""

    def __init__(self, name, cors=None, acl=None):
        self.name = name
        self.cors = cors
        self.acl = acl
        self.objects = []

    def __contains__(self, item):
        names_contained = [r.name for r in self.objects]
        return item in names_contained

    def __getitem__(self, item):
        objs_contained = {r.name: r for r in self.objects}
        return objs_contained[item]

    def __setitem__(self, key, value):
        new_object = DummyStorageObject(name=key)
        if key in self:
            names_contained = [r.name for r in self.objects]
            index = names_contained.index(key)
            self.objects[index] = new_object
        else:
            self.objects.append(new_object)


class DummyBotoClient:
    """Simulate a boto client."""

    def __init__(self, resource, endpoint_url=None, **storage_kws):
        self.resource = resource
        self.endpoint_url = endpoint_url
        self.storage_kws = storage_kws
        self.buckets = dict()

    def create_bucket(self, Bucket):
        if Bucket in self.buckets:
            return
        bucket_obj = DummyBucket(name=Bucket)
        self.buckets[Bucket] = bucket_obj

    def head_bucket(self, Bucket):
        if Bucket not in self.buckets:
            error_response = {"Error": {"Code": "404"}}
            error = botocore.exceptions.ClientError(error_response, "head bucket")
            raise error

    def get_bucket_cors(self, Bucket):
        if Bucket not in self.buckets:
            raise ValueError("No such bucket")
        bucket_obj = self.buckets[Bucket]
        if not bucket_obj.cors:
            error_response = {"Error": {"Code": "NoSuchCORSConfiguration"}}
            error = botocore.exceptions.ClientError(error_response, "get bucket CORS")
            raise error
        return bucket_obj.cors

    def put_bucket_cors(self, Bucket, CORSConfiguration):
        if Bucket not in self.buckets:
            raise ValueError("bucket doesn't exists")
        bucket_obj = self.buckets[Bucket]
        bucket_obj.cors = CORSConfiguration

    def get_bucket_acl(self, Bucket):
        if Bucket not in self.buckets:
            raise ValueError("No such bucket")
        bucket_obj = self.buckets[Bucket]
        if not bucket_obj.acl:
            raise ValueError("bucket doesn't have ACL")
        return bucket_obj.acl

    def put_bucket_acl(self, Bucket, ACL):
        if Bucket not in self.buckets:
            raise ValueError("bucket doesn't exists")
        bucket_obj = self.buckets[Bucket]
        if ACL != "public-read":
            raise NotImplementedError
        bucket_obj.acl = {
            "ResponseMetadata": {
                "RequestId": "a-request-id",
                "HTTPStatusCode": 200,
            },
            "Grants": [
                {
                    "Grantee": {
                        "Type": "Group",
                        "URI": "http://acs.amazonaws.com/groups/global/AllUsers",
                    },
                    "Permission": "READ",
                },
            ],
        }

    def head_object(self, Bucket, Key):
        if Bucket not in self.buckets:
            raise ValueError("bucket doesn't exists")
        bucket_obj = self.buckets[Bucket]
        if Key not in bucket_obj:
            error_response = {"Error": {"Code": "404"}}
            error = botocore.exceptions.ClientError(error_response, "head object")
            raise error

    def upload_file(self, Filename, Bucket, Key, ExtraArgs):
        if Bucket not in self.buckets:
            raise ValueError("bucket doesn't exists")
        bucket_object = self.buckets[Bucket]
        if Key in bucket_object:
            raise ValueError("file already present")
        new_object = DummyStorageObject(name=Key, extra_args=ExtraArgs)
        new_object.Filename = Filename
        bucket_object[Key] = new_object

    def get_object_acl(self, Bucket, Key):
        if Bucket not in self.buckets:
            raise ValueError("bucket doesn't exists")
        bucket_object = self.buckets[Bucket]
        if Key not in bucket_object:
            raise ValueError("file doesn't found")
        the_object = bucket_object[Key]
        return the_object.acl

    def put_object_acl(self, Bucket, Key, ACL=None):
        if Bucket not in self.buckets:
            raise ValueError("bucket doesn't exists")
        bucket_object = self.buckets[Bucket]
        if Key not in bucket_object:
            raise ValueError("file doesn't found")
        the_object = bucket_object[Key]
        if ACL != "public-read":
            raise NotImplementedError
        the_object.acl = {
            "ResponseMetadata": {
                "RequestId": "a-request-id",
                "HTTPStatusCode": 200,
            },
            "Grants": [
                {
                    "Grantee": {
                        "Type": "Group",
                        "URI": "http://acs.amazonaws.com/groups/global/AllUsers",
                    },
                    "Permission": "READ",
                },
            ],
        }


@pytest.mark.filterwarnings("ignore:Exception ignored")
def test_store_file(mocker: pytest_mock.MockerFixture) -> None:
    object_storage_url = "http://myobject-storage:myport/"
    bucket_name = "cads-catalogue"
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

    # FIRST TEST: run for a not existing file/not absolute path
    use_client = DummyBotoClient("S3", endpoint_url=object_storage_url, **storage_kws)
    with pytest.raises(ValueError):
        object_storage.store_file(
            "not/existing.png", object_storage_url, use_client=use_client, **storage_kws
        )

    # define spies
    head_bucket = mocker.spy(DummyBotoClient, "head_bucket")
    create_bucket = mocker.spy(DummyBotoClient, "create_bucket")
    put_bucket_acl = mocker.spy(DummyBotoClient, "put_bucket_acl")
    get_bucket_acl = mocker.spy(DummyBotoClient, "get_bucket_acl")
    get_bucket_cors = mocker.spy(DummyBotoClient, "get_bucket_cors")
    put_bucket_cors = mocker.spy(DummyBotoClient, "put_bucket_cors")
    head_object = mocker.spy(DummyBotoClient, "head_object")
    upload_file = mocker.spy(DummyBotoClient, "upload_file")
    put_object_acl = mocker.spy(DummyBotoClient, "put_object_acl")
    get_object_acl = mocker.spy(DummyBotoClient, "get_object_acl")

    # SECOND TEST: upload first time on the default (not existing) bucket
    res = object_storage.store_file(
        file_path, object_storage_url, use_client=use_client, **storage_kws
    )
    assert res == expected_url
    # check if the bucket exists
    head_bucket.assert_called_once_with(use_client, Bucket="cads-catalogue")
    # create the bucket
    create_bucket.assert_called_once_with(use_client, Bucket="cads-catalogue")
    # check bucket ACL
    get_bucket_acl.assert_not_called()
    # put bucket ACL
    put_bucket_acl.assert_called_once_with(
        use_client, ACL="public-read", Bucket="cads-catalogue"
    )
    # check bucket CORS
    get_bucket_cors.assert_called_once_with(use_client, Bucket="cads-catalogue")
    # put bucket CORS
    put_bucket_cors.assert_called_once_with(
        use_client,
        Bucket="cads-catalogue",
        CORSConfiguration=object_storage.DEFAULT_CORS_CONFIG,
    )
    # check if the object exists
    head_object.assert_called_once_with(
        use_client,
        Bucket="cads-catalogue",
        Key=f"licence-to-use-copernicus-products_{sha256}.pdf",
    )
    # upload file
    upload_file.assert_called_once_with(
        use_client,
        Filename=file_path,
        Bucket="cads-catalogue",
        Key=f"licence-to-use-copernicus-products_{sha256}.pdf",
        ExtraArgs={
            "ContentType": utils.guess_type(file_path),
            "ACL": "public-read",
        },
    )
    # check object ACL
    get_object_acl.assert_not_called()
    # set object ACL
    put_object_acl.assert_not_called()

    for spy in [
        head_bucket,
        create_bucket,
        get_bucket_acl,
        put_bucket_acl,
        head_object,
        upload_file,
        get_bucket_cors,
        put_bucket_cors,
        get_object_acl,
        put_object_acl,
    ]:
        spy.reset_mock()

    # import pdb; pdb.set_trace()
    # THIRD TEST: calling with a subpath and a (not existing) bucket
    subpath = "licences/mypath"
    bucket_name = "mybucket"
    expected_url = (
        f"{bucket_name}/licences/mypath/licence-to-use-copernicus-products_{sha256}.pdf"
    )

    res = object_storage.store_file(
        file_path,
        object_storage_url,
        bucket_name,
        subpath,
        use_client=use_client,
        **storage_kws,
    )
    assert res == expected_url
    head_bucket.assert_called_once_with(use_client, Bucket=bucket_name)
    create_bucket.assert_called_once_with(use_client, Bucket=bucket_name)
    get_bucket_acl.assert_not_called()
    put_bucket_acl.assert_called_once_with(
        use_client, ACL="public-read", Bucket=bucket_name
    )
    get_bucket_cors.assert_called_once_with(use_client, Bucket=bucket_name)
    put_bucket_cors.assert_called_once_with(
        use_client,
        Bucket=bucket_name,
        CORSConfiguration=object_storage.DEFAULT_CORS_CONFIG,
    )
    head_object.assert_called_once_with(
        use_client,
        Bucket=bucket_name,
        Key=f"{subpath}/licence-to-use-copernicus-products_{sha256}.pdf",
    )
    upload_file.assert_called_once_with(
        use_client,
        Filename=file_path,
        Bucket=bucket_name,
        Key=f"{subpath}/licence-to-use-copernicus-products_{sha256}.pdf",
        ExtraArgs={
            "ContentType": utils.guess_type(file_path),
            "ACL": "public-read",
        },
    )
    get_object_acl.assert_not_called()
    put_object_acl.assert_not_called()

    for spy in [
        head_bucket,
        create_bucket,
        get_bucket_acl,
        put_bucket_acl,
        head_object,
        upload_file,
        get_bucket_cors,
        put_bucket_cors,
        get_object_acl,
        put_object_acl,
    ]:
        spy.reset_mock()

    # FOURTH TEST: calling again the same upload (so bucket and file both exist)
    res = object_storage.store_file(
        file_path,
        object_storage_url,
        bucket_name,
        subpath,
        use_client=use_client,
        **storage_kws,
    )
    assert res == expected_url
    head_bucket.assert_called_once_with(use_client, Bucket=bucket_name)
    create_bucket.assert_not_called()
    get_bucket_acl.assert_called_once_with(use_client, Bucket=bucket_name)
    put_bucket_acl.assert_not_called()
    get_bucket_cors.assert_called_once_with(use_client, Bucket=bucket_name)
    put_bucket_cors.assert_not_called()
    head_object.assert_called_once_with(
        use_client,
        Bucket=bucket_name,
        Key=f"{subpath}/licence-to-use-copernicus-products_{sha256}.pdf",
    )
    upload_file.assert_not_called()
    get_object_acl.assert_called_once_with(
        use_client,
        Bucket=bucket_name,
        Key=f"{subpath}/licence-to-use-copernicus-products_{sha256}.pdf",
    )
    put_object_acl.assert_not_called()
