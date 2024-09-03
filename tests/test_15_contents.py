import datetime
import os.path

import pytest_mock
import sqlalchemy as sa

from cads_catalogue import config, contents, object_storage

THIS_PATH = os.path.abspath(os.path.dirname(__file__))
TESTDATA_PATH = os.path.join(THIS_PATH, "data")
TEST_CONTENT_ROOT_PATH = os.path.join(TESTDATA_PATH, "cads-contents-json")


def test_load_content_folder() -> None:
    site = "cds"
    content_type = "application"
    content_folder = os.path.join(
        TEST_CONTENT_ROOT_PATH, "contents", site, content_type, "climate-pulse"
    )
    expected_content = {
        "content_uid": "cds-application-climate-pulse",
        "creation_date": "2023-03-18T11:02:31Z",
        "description": "Climate Pulse visualises near-real-time updates of global "
        "average air- and sea-surface temperatures from ECMWF's "
        "flagship ERA5 reanalysis",
        "image": os.path.join(content_folder, "overview.png"),
        "keywords": [
            "Product type: Application",
            "Spatial coverage: Global",
            "Temporal coverage: Past",
            "Variable domain: Land (hydrology)",
            "Variable domain: Land (physics)",
            "Variable domain: Land (biosphere)",
            "Provider: Copernicus C3S",
        ],
        "layout": os.path.join(content_folder, "layout.json"),
        "last_update": "2024-07-19T11:01:31Z",
        "link": "https://pulse.climate.copernicus.eu/",
        "site": "cds",
        "title": "Climate Pulse",
        "type": "application",
    }

    effective_content = contents.load_content_folder(content_folder, site, content_type)
    assert effective_content == expected_content


def test_load_contents() -> None:
    expected_contents = [
        {
            "site": "ads",
            "type": "application",
            "content_uid": "ads-application-climate-pulse",
            "link": "https://pulse.climate.copernicus.eu/",
            "title": "Climate Pulse",
            "description": "Climate Pulse visualises near-real-time updates of global average "
            "air- and sea-surface temperatures from ECMWF's flagship ERA5 reanalysis",
            "creation_date": "2023-03-18T11:03:31Z",
            "last_update": "2024-07-19T10:02:31Z",
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
            "image": os.path.join(
                TEST_CONTENT_ROOT_PATH,
                "contents",
                "ads",
                "application",
                "climate-pulse",
                "overview.png",
            ),
        },
        {
            "site": "ads",
            "type": "page",
            "content_uid": "ads-page-how-to-api",
            "link": None,
            "title": "How to API page",
            "description": "This is the test description of the How to API page",
            "creation_date": "2024-02-08T11:02:31Z",
            "last_update": "2024-09-02T13:02:31Z",
            "keywords": [],
            "layout": os.path.join(
                TEST_CONTENT_ROOT_PATH,
                "contents",
                "ads",
                "page",
                "how-to-api",
                "layout.json",
            ),
            "image": None,
        },
        {
            "site": "cds",
            "type": "application",
            "content_uid": "cds-application-climate-pulse",
            "link": "https://pulse.climate.copernicus.eu/",
            "title": "Climate Pulse",
            "description": "Climate Pulse visualises near-real-time updates of global average "
            "air- and sea-surface temperatures from ECMWF's flagship ERA5 reanalysis",
            "creation_date": "2023-03-18T11:02:31Z",
            "last_update": "2024-07-19T11:01:31Z",
            "keywords": [
                "Product type: Application",
                "Spatial coverage: Global",
                "Temporal coverage: Past",
                "Variable domain: Land (hydrology)",
                "Variable domain: Land (physics)",
                "Variable domain: Land (biosphere)",
                "Provider: Copernicus C3S",
            ],
            "layout": os.path.join(
                TEST_CONTENT_ROOT_PATH,
                "contents",
                "cds",
                "application",
                "climate-pulse",
                "layout.json",
            ),
            "image": os.path.join(
                TEST_CONTENT_ROOT_PATH,
                "contents",
                "cds",
                "application",
                "climate-pulse",
                "overview.png",
            ),
        },
        {
            "site": "cds",
            "type": "application",
            "content_uid": "cds-application-copernicus-interactive-climate-atlas",
            "link": "https://atlas.climate.copernicus.eu/atlas",
            "title": "Copernicus Interactive Climate Atlas",
            "description": "The Copernicus Interactive Climate Atlas provides graphical information about "
            "recent past trends and future changes (for different scenarios and "
            "global warming levels)",
            "creation_date": "2023-02-17T11:02:31Z",
            "last_update": "2024-08-17T11:02:31Z",
            "keywords": [
                "Product type: Application",
                "Spatial coverage: Global",
                "Temporal coverage: Present",
                "Variable domain: Atmosphere (surface)",
                "Variable domain: Ocean (biology)",
                "Provider: Copernicus C3S",
            ],
            "layout": None,
            "image": os.path.join(
                TEST_CONTENT_ROOT_PATH,
                "contents",
                "cds",
                "application",
                "copernicus-interactive-climate-atlas",
                "image.png",
            ),
        },
    ]
    effective_contents = contents.load_contents(TEST_CONTENT_ROOT_PATH)
    assert effective_contents == expected_contents


def test_content_sync(
    session_obj: sa.orm.sessionmaker, mocker: pytest_mock.MockerFixture
) -> None:
    content_folder = os.path.join(
        TEST_CONTENT_ROOT_PATH, "cds", "application", "climate-pulse"
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
        "content_uid": "cds-application-climate-pulse",
        "creation_date": "2023-03-18T11:02:31Z",
        "description": "Climate Pulse visualises near-real-time updates of global "
        "average air- and sea-surface temperatures from ECMWF's "
        "flagship ERA5 reanalysis",
        "image": os.path.join(content_folder, "overview.png"),
        "keywords": [
            "Product type: Application",
            "Spatial coverage: Global",
            "Temporal coverage: Past",
            "Variable domain: Land (hydrology)",
            "Variable domain: Land (physics)",
            "Variable domain: Land (biosphere)",
            "Provider: Copernicus C3S",
        ],
        "layout": os.path.join(content_folder, "layout.json"),
        "last_update": "2024-07-19T11:01:31Z",
        "link": "https://pulse.climate.copernicus.eu/",
        "site": "cds",
        "title": "Climate Pulse",
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
            if key in ("creation_date", "last_update"):
                value = datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")  # type: ignore
            elif key in ("image", "layout"):
                value = "an url"
            elif key == "keywords":
                continue
            assert getattr(db_content1, key) == value

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
    content1["creation_date"] = "2021-03-18T11:02:31Z"
    content1["title"] = "new title"
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
            if key in ("creation_date", "last_update"):
                value = datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")  # type: ignore
            elif key in ("layout",):
                value = "an url"
            elif key == "keywords":
                continue
            assert getattr(db_content2, key) == value
