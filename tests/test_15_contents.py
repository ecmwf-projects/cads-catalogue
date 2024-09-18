import datetime
import os.path

import pytest_mock
import sqlalchemy as sa

from cads_catalogue import config, contents, object_storage

THIS_PATH = os.path.abspath(os.path.dirname(__file__))
TESTDATA_PATH = os.path.join(THIS_PATH, "data")
TEST_CONTENT_ROOT_PATH = os.path.join(TESTDATA_PATH, "cads-contents-json")


def test_load_content_folder() -> None:
    content_folder = os.path.join(
        TEST_CONTENT_ROOT_PATH, "copernicus-interactive-climates-atlas"
    )
    expected_content = {
        "content_uid": "copernicus-interactive-climates-atlas",
        "publication_date": "2024-09-13T00:00:00Z",
        "description": "The Copernicus Interactive Climate Atlas provides graphical "
        "information about recent past trends and future changes "
        "(for different scenarios and global warming levels)",
        "image": os.path.join(content_folder, "cica-overview.png"),
        "keywords": [
            "Product type: Application",
            "Spatial coverage: Global",
            "Temporal coverage: Past",
            "Variable domain: Land (hydrology)",
            "Variable domain: Land (physics)",
            "Variable domain: Land (biosphere)",
            "Provider: Copernicus C3S",
        ],
        "layout": None,
        "link": "https://atlas.climate.copernicus.eu/atlas",
        "content_update": "2024-09-16T00:00:00Z",
        "site": "cds",
        "title": "Copernicus Interactive Climate Atlas",
        "type": "application",
        "data": {
            "file-format": "GRIB (optional conversion to netCDF)",
            "data-type": "Gridded",
            "horizontal-coverage": "Global",
        },
    }

    effective_content = contents.load_content_folder(content_folder)
    assert effective_content == expected_content


def test_load_contents() -> None:
    expected_contents = [
        {
            "content_uid": "copernicus-interactive-climates-atlas",
            "publication_date": "2024-09-13T00:00:00Z",
            "description": "The Copernicus Interactive Climate Atlas provides graphical "
            "information about recent past trends and future changes "
            "(for different scenarios and global warming levels)",
            "image": os.path.join(
                TEST_CONTENT_ROOT_PATH,
                "copernicus-interactive-climates-atlas",
                "cica-overview.png",
            ),
            "keywords": [
                "Product type: Application",
                "Spatial coverage: Global",
                "Temporal coverage: Past",
                "Variable domain: Land (hydrology)",
                "Variable domain: Land (physics)",
                "Variable domain: Land (biosphere)",
                "Provider: Copernicus C3S",
            ],
            "layout": None,
            "link": "https://atlas.climate.copernicus.eu/atlas",
            "content_update": "2024-09-16T00:00:00Z",
            "site": "cds",
            "title": "Copernicus Interactive Climate Atlas",
            "type": "application",
            "data": {
                "file-format": "GRIB (optional conversion to netCDF)",
                "data-type": "Gridded",
                "horizontal-coverage": "Global",
            },
        },
        {
            "content_uid": "how-to-api",
            "publication_date": "2024-09-13T10:01:50Z",
            "description": "Access the full data store catalogue, with search and availability features",
            "image": None,
            "keywords": [],
            "layout": os.path.join(TEST_CONTENT_ROOT_PATH, "how-to-api", "layout.json"),
            "content_update": "2024-09-16T02:10:22Z",
            "link": None,
            "site": "cds,ads",
            "title": "CDSAPI setup",
            "type": "page",
            "data": None,
        },
    ]
    effective_contents = contents.load_contents(TEST_CONTENT_ROOT_PATH)
    assert effective_contents == expected_contents


def test_content_sync(
    session_obj: sa.orm.sessionmaker, mocker: pytest_mock.MockerFixture
) -> None:
    content_folder = os.path.join(
        TEST_CONTENT_ROOT_PATH, "copernicus-interactive-climates-atlas"
    )
    # patching object storage upload
    my_settings_dict = {
        "object_storage_url": "object/storage/url",
        "storage_admin": "admin1",
        "storage_password": "secret1",
        "catalogue_bucket": "mycatalogue_bucket",
        "document_storage_url": "my/url",
    }
    storage_settings = config.ObjectStorageSettings(**my_settings_dict)
    mocker.patch.object(object_storage, "store_file", return_value="an url")
    # load testing content
    content1 = {
        "content_uid": "copernicus-interactive-climates-atlas",
        "publication_date": "2024-09-13T00:00:00Z",
        "description": "The Copernicus Interactive Climate Atlas provides graphical "
        "information about recent past trends and future changes "
        "(for different scenarios and global warming levels)",
        "image": os.path.join(content_folder, "cica-overview.png"),
        "keywords": [
            "Product type: Application",
            "Spatial coverage: Global",
            "Temporal coverage: Past",
            "Variable domain: Land (hydrology)",
            "Variable domain: Land (physics)",
            "Variable domain: Land (biosphere)",
            "Provider: Copernicus C3S",
        ],
        "layout": None,
        "content_update": "2024-09-16T00:00:00Z",
        "link": "https://pulse.climate.copernicus.eu/",
        "site": "cds,ads",
        "title": "Copernicus Interactive Climate Atlas",
        "type": "application",
    }

    with session_obj() as session:
        # db is empty: adding a content
        db_content1 = contents.content_sync(session, content1, storage_settings)
        session.commit()
        # check keywords
        assert set(
            [
                (k.category_name, k.category_value, k.keyword_name)
                for k in db_content1.keywords
            ]
        ) == set(
            [
                ("Temporal coverage", "Past", "Temporal coverage: Past"),
                (
                    "Variable domain",
                    "Land (biosphere)",
                    "Variable domain: Land (biosphere)",
                ),
                ("Product type", "Application", "Product type: Application"),
                (
                    "Variable domain",
                    "Land (hydrology)",
                    "Variable domain: Land (hydrology)",
                ),
                ("Spatial coverage", "Global", "Spatial coverage: Global"),
                (
                    "Variable domain",
                    "Land (physics)",
                    "Variable domain: Land (physics)",
                ),
                ("Provider", "Copernicus C3S", "Provider: Copernicus C3S"),
            ]
        )
        # check db fields
        for key, value in content1.items():
            if key in ("publication_date", "content_update"):
                value = datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")  # type: ignore
            elif key in ("image",):
                value = "an url"
            elif key == "keywords":
                continue
            assert getattr(db_content1, key) == value, key

    # changing content1, so do an update
    content1["image"] = None  # type: ignore
    content1["keywords"] = [
        "Spatial coverage: Europe",
        "Temporal coverage: Past",
        "Variable domain: Land (hydrology)",
        "Variable domain: Land (physics)",
        "Variable domain: Land (biosphere)",
        "Provider: Copernicus C3S",
    ]
    content1["publication_date"] = "2021-03-18T11:02:31Z"
    content1["title"] = "new title"
    content1["layout"] = os.path.join(content_folder, "cica-overview.png")
    with session_obj() as session:
        # db is not empty: update a content
        db_content2 = contents.content_sync(session, content1, storage_settings)
        session.commit()
        # check keywords
        assert set(
            [
                (k.category_name, k.category_value, k.keyword_name)
                for k in db_content2.keywords
            ]
        ) == set(
            [
                ("Temporal coverage", "Past", "Temporal coverage: Past"),
                (
                    "Variable domain",
                    "Land (biosphere)",
                    "Variable domain: Land (biosphere)",
                ),
                (
                    "Variable domain",
                    "Land (hydrology)",
                    "Variable domain: Land (hydrology)",
                ),
                ("Spatial coverage", "Europe", "Spatial coverage: Europe"),
                (
                    "Variable domain",
                    "Land (physics)",
                    "Variable domain: Land (physics)",
                ),
                ("Provider", "Copernicus C3S", "Provider: Copernicus C3S"),
            ]
        )
        # check db fields
        for key, value in content1.items():
            if key in ("publication_date", "content_update"):
                value = datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")  # type: ignore
            elif key in ("layout",):
                value = "an url"
            elif key == "keywords":
                continue
            assert getattr(db_content2, key) == value
