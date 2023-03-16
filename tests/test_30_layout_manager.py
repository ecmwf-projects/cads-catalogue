import json
import os.path

import pytest
import pytest_mock
from sqlalchemy.orm import sessionmaker

from cads_catalogue import (
    config,
    database,
    layout_manager,
    licence_manager,
    object_storage,
)

THIS_PATH = os.path.abspath(os.path.dirname(__file__))
TESTDATA_PATH = os.path.join(THIS_PATH, "data")


def create_layout_for_test(path, sections=[], aside={}):
    """Use for testing."""
    base_data = {
        "uid": "cams-global-reanalysis-eac4",
        "body": {
            "main": {
                "sections": sections,
            },
            "aside": aside,
        },
    }
    with open(path, "w") as fp:
        json.dump(base_data, fp)
    return base_data


def test_transform_licences_blocks(tmpdir, session_obj: sessionmaker):
    my_settings_dict = {
        "object_storage_url": "object/storage/url",
        "storage_admin": "admin1",
        "storage_password": "secret1",
        "catalogue_bucket": "mycatalogue_bucket",
        "document_storage_url": "my/url",
    }
    storage_settings = config.ObjectStorageSettings(**my_settings_dict)
    # add some licences to work on
    licences_folder_path = os.path.join(TESTDATA_PATH, "cads-licences")
    licences = licence_manager.load_licences_from_folder(licences_folder_path)
    with session_obj() as session:
        for licence in licences:
            session.add(database.Licence(**licence))
        session.commit()
        session.query(database.Licence).all()
    # create a test layout.json
    layout_path = os.path.join(str(tmpdir), "layout.json")
    block1 = {"licence-id": "licence-to-use-copernicus-products", "type": "licence"}
    block2 = {
        "type": "link",
        "id": "test-link-id",
        "title": "a link",
        "href": "http://a-link.html",
    }
    block3 = {"licence-id": "eumetsat-cm-saf", "type": "licence"}
    sections = [
        {"id": "overview", "blocks": [block1, block2, block3]},
        {"id": "overview2", "blocks": [block2, block3]},
    ]
    aside = {"blocks": [block1, block2]}
    # expected blocks

    def get_blocks(licence_uid, licence_pdf_name):
        block11 = {
            "type": "button",
            "id": f"{licence_uid}-licences",
            "title": "Licence",
            "action": "modal",
            "content": "dummy md content",
        }
        block12 = {
            "type": "button",
            "id": f"{licence_uid}-licences-download",
            "parent": f"{licence_uid}-licences",
            "title": "Download PDF",
            "action": "download",
            "contents-url": os.path.join(
                licences_folder_path,
                licence_pdf_name,  # "licence-to-use-copernicus-products.pdf"
            ),
        }
        block13 = {
            "type": "button",
            "id": f"{licence_uid}-licences-clipboard",
            "parent": f"{licence_uid}-licences",
            "title": "Copy to clipboard",
            "action": "copy-clipboard",
        }
        return [block11, block12, block13]

    layout_data = create_layout_for_test(layout_path, sections=sections, aside=aside)

    new_layout_data = layout_manager.transform_licences_blocks(
        session, layout_data, storage_settings
    )
    assert new_layout_data == {
        "uid": "cams-global-reanalysis-eac4",
        "body": {
            "main": {
                "sections": [
                    {
                        "id": "overview",
                        "blocks": get_blocks(
                            "licence-to-use-copernicus-products",
                            "licence-to-use-copernicus-products.pdf",
                        )
                        + [block2]
                        + get_blocks("eumetsat-cm-saf", "eumetsat-cm-saf.pdf"),
                    },
                    {
                        "id": "overview2",
                        "blocks": [block2]
                        + get_blocks("eumetsat-cm-saf", "eumetsat-cm-saf.pdf"),
                    },
                ]
            },
            "aside": {
                "blocks": get_blocks(
                    "licence-to-use-copernicus-products",
                    "licence-to-use-copernicus-products.pdf",
                )
                + [block2]
            },
        },
    }


def test_transform_image_blocks(tmpdir, mocker: pytest_mock.MockerFixture) -> None:
    oss = config.ObjectStorageSettings(
        object_storage_url="http://myobject-storage:myport/",
        storage_admin="storage_user",
        storage_password="storage_password",
        catalogue_bucket="abucket",
        document_storage_url="http://public-storage/",
    )
    mocker.patch.object(
        object_storage, "store_file", return_value=("an url", "a version")
    )
    layout_path = os.path.join(str(tmpdir), "layout.json")
    resource = {"resource_uid": "a-dataset"}

    # missing blocks with images
    layout_data = create_layout_for_test(layout_path)
    new_layout_data = layout_manager.transform_image_blocks(
        layout_data, str(tmpdir), resource, oss
    )
    assert new_layout_data == layout_data

    # image overview/overview.png not found
    no_image_block = {"id": "abstract", "type": "a type", "content": "a content"}
    image_block = {
        "id": "abstract",
        "type": "thumb-markdown",
        "content": "a content",
        "image": {
            "url": "overview/overview.png",
            "alt": "alternative text",
        },
    }
    sections = [{"id": "overview", "blocks": [no_image_block, image_block]}]
    layout_data = create_layout_for_test(layout_path, sections)
    with pytest.raises(ValueError):
        layout_manager.transform_image_blocks(layout_data, str(tmpdir), resource, oss)

    # create image overview/overview.png and repeat the test
    overview_path = os.path.join(str(tmpdir), "overview")
    os.mkdir(overview_path)
    overview_file_path = os.path.join(overview_path, "overview.png")
    with open(overview_file_path, "w") as fp:
        fp.write("hello! I am an image")
    new_layout_data = layout_manager.transform_image_blocks(
        layout_data, str(tmpdir), resource, oss
    )
    assert new_layout_data == {
        "uid": "cams-global-reanalysis-eac4",
        "body": {
            "main": {
                "sections": [
                    {
                        "id": "overview",
                        "blocks": [
                            {
                                "id": "abstract",
                                "type": "a type",
                                "content": "a content",
                            },
                            {
                                "id": "abstract",
                                "type": "thumb-markdown",
                                "content": "a content",
                                "image": {
                                    "url": "http://public-storage/an url",
                                    "alt": "alternative text",
                                },
                            },
                        ],
                    }
                ]
            },
            "aside": {},
        },
    }

    # on section position [0, 1] and [1, 0]
    sections = [
        {"id": "overview", "blocks": [no_image_block, image_block]},
        {"id": "overview2", "blocks": [image_block, no_image_block]},
    ]
    layout_data = create_layout_for_test(layout_path, sections)
    new_layout_data = layout_manager.transform_image_blocks(
        layout_data, str(tmpdir), resource, oss
    )
    assert new_layout_data == {
        "uid": "cams-global-reanalysis-eac4",
        "body": {
            "main": {
                "sections": [
                    {
                        "id": "overview",
                        "blocks": [
                            {
                                "id": "abstract",
                                "type": "a type",
                                "content": "a content",
                            },
                            {
                                "id": "abstract",
                                "type": "thumb-markdown",
                                "content": "a content",
                                "image": {
                                    "url": "http://public-storage/an url",
                                    "alt": "alternative text",
                                },
                            },
                        ],
                    },
                    {
                        "id": "overview2",
                        "blocks": [
                            {
                                "id": "abstract",
                                "type": "thumb-markdown",
                                "content": "a content",
                                "image": {
                                    "url": "http://public-storage/an url",
                                    "alt": "alternative text",
                                },
                            },
                            {
                                "id": "abstract",
                                "type": "a type",
                                "content": "a content",
                            },
                        ],
                    },
                ]
            },
            "aside": {},
        },
    }

    # only on aside, position 0
    aside = {"blocks": [image_block, no_image_block, no_image_block]}
    layout_data = create_layout_for_test(layout_path, aside=aside)
    new_layout_data = layout_manager.transform_image_blocks(
        layout_data, str(tmpdir), resource, oss
    )
    assert new_layout_data == {
        "uid": "cams-global-reanalysis-eac4",
        "body": {
            "main": {"sections": []},
            "aside": {
                "blocks": [
                    {
                        "id": "abstract",
                        "type": "thumb-markdown",
                        "content": "a content",
                        "image": {
                            "url": "http://public-storage/an url",
                            "alt": "alternative text",
                        },
                    },
                    {"id": "abstract", "type": "a type", "content": "a content"},
                    {"id": "abstract", "type": "a type", "content": "a content"},
                ]
            },
        },
    }

    # only on aside, position 1 and 3
    aside = {"blocks": [no_image_block, image_block, no_image_block, image_block]}
    layout_data = create_layout_for_test(layout_path, aside=aside)
    new_layout_data = layout_manager.transform_image_blocks(
        layout_data, str(tmpdir), resource, oss
    )
    assert new_layout_data == {
        "uid": "cams-global-reanalysis-eac4",
        "body": {
            "main": {"sections": []},
            "aside": {
                "blocks": [
                    {"id": "abstract", "type": "a type", "content": "a content"},
                    {
                        "id": "abstract",
                        "type": "thumb-markdown",
                        "content": "a content",
                        "image": {
                            "url": "http://public-storage/an url",
                            "alt": "alternative text",
                        },
                    },
                    {"id": "abstract", "type": "a type", "content": "a content"},
                    {
                        "id": "abstract",
                        "type": "thumb-markdown",
                        "content": "a content",
                        "image": {
                            "url": "http://public-storage/an url",
                            "alt": "alternative text",
                        },
                    },
                ]
            },
        },
    }

    # on both layout (1, 1) (1, 2) and aside 2, 4
    sections = [
        {"id": "overview", "blocks": [no_image_block, no_image_block]},
        {"id": "overview2", "blocks": [no_image_block, image_block, image_block]},
    ]
    aside = {
        "blocks": [
            no_image_block,
            no_image_block,
            image_block,
            no_image_block,
            image_block,
        ]
    }
    layout_data = create_layout_for_test(layout_path, sections=sections, aside=aside)
    new_layout_data = layout_manager.transform_image_blocks(
        layout_data, str(tmpdir), resource, oss
    )
    assert new_layout_data == {
        "uid": "cams-global-reanalysis-eac4",
        "body": {
            "main": {
                "sections": [
                    {
                        "id": "overview",
                        "blocks": [
                            {
                                "id": "abstract",
                                "type": "a type",
                                "content": "a content",
                            },
                            {
                                "id": "abstract",
                                "type": "a type",
                                "content": "a content",
                            },
                        ],
                    },
                    {
                        "id": "overview2",
                        "blocks": [
                            {
                                "id": "abstract",
                                "type": "a type",
                                "content": "a content",
                            },
                            {
                                "id": "abstract",
                                "type": "thumb-markdown",
                                "content": "a content",
                                "image": {
                                    "url": "http://public-storage/an url",
                                    "alt": "alternative text",
                                },
                            },
                            {
                                "id": "abstract",
                                "type": "thumb-markdown",
                                "content": "a content",
                                "image": {
                                    "url": "http://public-storage/an url",
                                    "alt": "alternative text",
                                },
                            },
                        ],
                    },
                ]
            },
            "aside": {
                "blocks": [
                    {"id": "abstract", "type": "a type", "content": "a content"},
                    {"id": "abstract", "type": "a type", "content": "a content"},
                    {
                        "id": "abstract",
                        "type": "thumb-markdown",
                        "content": "a content",
                        "image": {
                            "url": "http://public-storage/an url",
                            "alt": "alternative text",
                        },
                    },
                    {"id": "abstract", "type": "a type", "content": "a content"},
                    {
                        "id": "abstract",
                        "type": "thumb-markdown",
                        "content": "a content",
                        "image": {
                            "url": "http://public-storage/an url",
                            "alt": "alternative text",
                        },
                    },
                ]
            },
        },
    }
