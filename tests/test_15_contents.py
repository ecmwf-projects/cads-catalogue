import datetime
import os.path
import unittest.mock
from operator import itemgetter
from typing import Any

import pytest_mock
import sqlalchemy as sa

from cads_catalogue import config, contents, layout_manager, object_storage

THIS_PATH = os.path.abspath(os.path.dirname(__file__))
TESTDATA_PATH = os.path.join(THIS_PATH, "data")
TEST_CONTENT_ROOT_PATH = os.path.join(TESTDATA_PATH, "cads-contents-json")


def test_yaml2context() -> None:
    yaml_path = os.path.join(TEST_CONTENT_ROOT_PATH, "template_config.yaml")
    effective_context = contents.yaml2context(yaml_path)
    expected_context = {
        "default": {
            "apiSnippet": "import something\nthis_is_a_default_snippet\n",
            "global_prop": "33",
        },
        "cds": {
            "siteSlug": "CDS",
            "siteName": "Climate Data Store",
            "apiSnippet": "import cds_stuff\nthis_is_cds_snippet\n",
        },
        "ads": {
            "siteSlug": "ADS",
            "siteName": "ADS Data Store",
            "apiSnippet": "import ads_stuff\nthis_is_ads_snippet",
        },
    }
    assert effective_context == expected_context


def test_load_content_folder() -> None:
    # no templated content
    content_folder = os.path.join(
        TEST_CONTENT_ROOT_PATH,
        "copernicus-interactive-climates-atlas",
    )
    expected_contents = [
        {
            "slug": "copernicus-interactive-climates-atlas",
            "publication_date": "2024-09-13T00:00:00Z",
            "hidden": False,
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
            "related_datasets": [
                "reanalysis-era5-land",
                "foo",
                "satellite-sea-ice-concentration",
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
                "copernicus_programme": [
                    {
                        "id": "climate-change-service",
                        "title": "Copernicus Climate Change Service",
                        "link": "https://climate.copernicus.eu/",
                    },
                    {
                        "id": "atmosphere-monitoring-service",
                        "title": "Copernicus Atmosphere Monitoring Service",
                        "link": "https://atmosphere.copernicus.eu/",
                    },
                ],
            },
        }
    ]

    effective_contents = contents.load_content_folder(content_folder)
    assert effective_contents == expected_contents

    # templated content
    content_folder = os.path.join(TEST_CONTENT_ROOT_PATH, "how-to-api-templated")
    yaml_config = os.path.join(TEST_CONTENT_ROOT_PATH, "template_config.yaml")
    expected_contents = [
        {
            "slug": "how-to-api-templated",
            "publication_date": "2024-09-13T10:01:50Z",
            "hidden": False,
            "description": "Access 33 items of ADS Data Store catalogue, "
            "with search and availability features",
            "image": None,
            "keywords": [],
            "layout": os.path.join(
                TEST_CONTENT_ROOT_PATH, "how-to-api-templated", "layout.json"
            ),
            "related_datasets": [],
            "content_update": "2024-09-16T02:10:22Z",
            "link": None,
            "site": "ads",
            "title": "ADS API setup",
            "type": "page",
            "data": None,
        },
    ]
    global_context = contents.yaml2context(yaml_config)
    effective_contents = contents.load_content_folder(content_folder, global_context)
    assert effective_contents == expected_contents


def test_load_contents() -> None:
    yaml_config = os.path.join(TEST_CONTENT_ROOT_PATH, "template_config.yaml")
    global_context = contents.yaml2context(yaml_config)
    expected_contents = [
        {
            "slug": "copernicus-interactive-climates-atlas",
            "publication_date": "2024-09-13T00:00:00Z",
            "hidden": False,
            "description": "The Copernicus Interactive Climate Atlas provides graphical "
            "information about recent past trends and future changes "
            "(for different scenarios and global warming levels)",
            "image": os.path.join(
                TEST_CONTENT_ROOT_PATH,
                "copernicus-interactive-climates-atlas",
                "cica-overview.png",
            ),
            "related_datasets": [
                "reanalysis-era5-land",
                "foo",
                "satellite-sea-ice-concentration",
            ],
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
                "copernicus_programme": [
                    {
                        "id": "climate-change-service",
                        "title": "Copernicus Climate Change Service",
                        "link": "https://climate.copernicus.eu/",
                    },
                    {
                        "id": "atmosphere-monitoring-service",
                        "title": "Copernicus Atmosphere Monitoring Service",
                        "link": "https://atmosphere.copernicus.eu/",
                    },
                ],
            },
        },
        {
            "slug": "how-to-api",
            "publication_date": "2024-09-13T10:01:50Z",
            "hidden": True,
            "description": "Access the full data store catalogue, "
            "with search and availability features",
            "image": None,
            "related_datasets": [],
            "keywords": [],
            "layout": os.path.join(TEST_CONTENT_ROOT_PATH, "how-to-api", "layout.json"),
            "content_update": "2024-09-16T02:10:22Z",
            "link": None,
            "site": "ads",
            "title": "CDSAPI setup",
            "type": "page",
            "data": None,
        },
        {
            "slug": "how-to-api",
            "publication_date": "2024-09-13T10:01:50Z",
            "hidden": True,
            "description": "Access the full data store catalogue, "
            "with search and availability features",
            "image": None,
            "related_datasets": [],
            "keywords": [],
            "layout": os.path.join(TEST_CONTENT_ROOT_PATH, "how-to-api", "layout.json"),
            "content_update": "2024-09-16T02:10:22Z",
            "link": None,
            "site": "cds",
            "title": "CDSAPI setup",
            "type": "page",
            "data": None,
        },
        {
            "slug": "how-to-api-templated",
            "publication_date": "2024-09-13T10:01:50Z",
            "hidden": False,
            "description": "Access 33 items of ADS Data Store catalogue, "
            "with search and availability features",
            "image": None,
            "related_datasets": [],
            "keywords": [],
            "layout": os.path.join(
                TEST_CONTENT_ROOT_PATH, "how-to-api-templated", "layout.json"
            ),
            "content_update": "2024-09-16T02:10:22Z",
            "link": None,
            "site": "ads",
            "title": "ADS API setup",
            "type": "page",
            "data": None,
        },
    ]
    effective_contents = sorted(
        contents.load_contents(TEST_CONTENT_ROOT_PATH, global_context),
        key=itemgetter("slug", "site"),
    )
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
        "slug": "copernicus-interactive-climates-atlas",
        "publication_date": "2024-09-13T00:00:00Z",
        "hidden": True,
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
            elif key == "keywords":
                continue
            assert getattr(db_content2, key) == value


def test_transform_layout(mocker: pytest_mock.MockerFixture):
    mocker.patch.object(object_storage, "store_file", return_value="an url")
    _store_layout_by_data = mocker.spy(layout_manager, "store_layout_by_data")
    my_settings_dict = {
        "object_storage_url": "https://object/storage/url/",
        "storage_admin": "admin1",
        "storage_password": "secret1",
        "catalogue_bucket": "mycatalogue_bucket",
        "document_storage_url": "https://document/storage/url/",
    }
    storage_settings = config.ObjectStorageSettings(**my_settings_dict)
    content_folder = os.path.join(TEST_CONTENT_ROOT_PATH, "how-to-api")
    initial_md_content: dict[str, Any] = {
        "site": "cds",
        "type": "page",
        "slug": "how-to-api",
        "title": "CDSAPI setup",
        "description": "Access the full data store catalogue, with search and availability features",
        "publication_date": "2024-09-13T10:01:50Z",
        "content_update": "2024-09-16T02:10:22Z",
        "link": None,
        "keywords": [],
        "data": None,
        "layout": os.path.join(content_folder, "layout.json"),
        "image": None,
    }
    expected_layout_data = {
        "title": "CDSAPI setup",
        "description": "Access the full data store catalogue, with search and availability features",
        "body": {
            "main": {
                "sections": [
                    {
                        "id": "main",
                        "blocks": [
                            {
                                "id": "page-content",
                                "type": "html",
                                "content": "<p>this is a content of a html block</p>\n<p>${apiSnippet}</p>",
                            }
                        ],
                    }
                ]
            }
        },
    }

    effective_md_content = contents.transform_layout(
        initial_md_content, storage_settings
    )
    expected_md_content = initial_md_content.copy()
    expected_md_content["layout"] = "an url"

    assert effective_md_content == expected_md_content
    assert _store_layout_by_data.mock_calls == [
        unittest.mock.call(
            expected_layout_data,
            expected_md_content,
            storage_settings,
            subpath="contents/cds/page/how-to-api",
        )
    ]


# def test_update_catalogue_contents(session_obj: sa.orm.sessionmaker, mocker: pytest_mock.MockerFixture):
#     my_settings_dict = {
#         "object_storage_url": "object/storage/url",
#         "storage_admin": "admin1",
#         "storage_password": "secret1",
#         "catalogue_bucket": "mycatalogue_bucket",
#         "document_storage_url": "my/url",
#     }
#     storage_settings = config.ObjectStorageSettings(**my_settings_dict)
#     patch = mocker.patch.object(object_storage, "store_file", return_value="an url")
#     contents_package_path = os.path.join(TESTDATA_PATH, "cads-contents-json")
#     yaml_config = os.path.join(TEST_CONTENT_ROOT_PATH, 'template_config.yaml')
#     with session_obj() as session:
#         contents.update_catalogue_contents(
#         session, contents_package_path, storage_settings, yaml_path=yaml_config
#         )
