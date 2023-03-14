
import json
import os.path
from typing import Any

import pytest
import pytest_mock

from cads_catalogue import layout_manager, object_storage

THIS_PATH = os.path.abspath(os.path.dirname(__file__))
TESTDATA_PATH = os.path.join(THIS_PATH, "data")


def create_layout_for_test(path, sections=[], aside={}):
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


def test_manage_upload_layout_images(tmpdir, mocker: pytest_mock.MockerFixture) -> None:
    # create dummy image
    overview_path = os.path.join(str(tmpdir), "overview")
    os.mkdir(overview_path)
    overview_file_path = os.path.join(overview_path, "overview.png")
    with open(overview_file_path, "w") as fp:
        fp.write("hello! I am an image")
    layout_path = os.path.join(str(tmpdir), "layout.json")
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
    create_layout_for_test(layout_path, sections=sections, aside=aside)
    object_storage_url = "http://myobject-storage:myport/"
    doc_storage_url = "http://public-storage/"
    storage_kws: dict[str, Any] = {
        "access_key": "storage_user",
        "secret_key": "storage_password",
        "secure": False,
    }
    mocker.patch.object(
        object_storage, "store_file", return_value=("an url", "a version")
    )
    dataset_md = layout_manager.load_layout_images_info(str(tmpdir))
    dataset_md["layout"] = layout_path
    dataset_md["resource_uid"] = "a_dataset"
    new_image_block: dict[str, Any] = {
        "id": "abstract",
        "type": "thumb-markdown",
        "content": "a content",
        "image": {
            "alt": "alternative text",
            "url": "http://public-storage/an url",
        },
    }
    sections = [
        {"id": "overview", "blocks": [no_image_block, no_image_block]},
        {
            "id": "overview2",
            "blocks": [no_image_block, new_image_block, new_image_block],
        },
    ]
    aside = {
        "blocks": [
            no_image_block,
            no_image_block,
            new_image_block,
            no_image_block,
            new_image_block,
        ]
    }
    expected_layout = {
        "uid": "cams-global-reanalysis-eac4",
        "body": {
            "main": {
                "sections": sections,
            },
            "aside": aside,
        },
    }
    layout_data = layout_manager.manage_upload_layout_images(
        dataset_md,
        object_storage_url,
        doc_storage_url=doc_storage_url,
        ret_layout_data=True,
        **storage_kws
    )

    assert layout_data == expected_layout


def test_load_layout_images_info(tmpdir) -> None:
    layout_path = os.path.join(str(tmpdir), "layout.json")
    # missing blocks with images
    create_layout_for_test(layout_path)
    effective = layout_manager.load_layout_images_info(str(tmpdir))
    assert effective == {"layout_images_info": []}
    # image not found
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
    create_layout_for_test(layout_path, sections)
    with pytest.raises(ValueError):
        layout_manager.load_layout_images_info(str(tmpdir))
    # create dummy image
    overview_path = os.path.join(str(tmpdir), "overview")
    os.mkdir(overview_path)
    overview_file_path = os.path.join(overview_path, "overview.png")
    with open(overview_file_path, "w") as fp:
        fp.write("hello! I am an image")
    # on sections position [0, 1]
    effective = layout_manager.load_layout_images_info(str(tmpdir))
    assert effective == {"layout_images_info": [(overview_file_path, "sections", 0, 1)]}
    # on section position [0, 1] and [1, 0]
    sections = [
        {"id": "overview", "blocks": [no_image_block, image_block]},
        {"id": "overview2", "blocks": [image_block, no_image_block]},
    ]
    create_layout_for_test(layout_path, sections)
    effective = layout_manager.load_layout_images_info(str(tmpdir))
    assert effective == {
        "layout_images_info": [
            (overview_file_path, "sections", 0, 1),
            (overview_file_path, "sections", 1, 0),
        ]
    }
    # only on aside, position 0
    aside = {"blocks": [image_block, no_image_block, no_image_block]}
    create_layout_for_test(layout_path, aside=aside)
    effective = layout_manager.load_layout_images_info(str(tmpdir))
    assert effective == {
        "layout_images_info": [
            (overview_file_path, "aside", 0),
        ]
    }
    # only on aside, position 1 and 3
    aside = {"blocks": [no_image_block, image_block, no_image_block, image_block]}
    create_layout_for_test(layout_path, aside=aside)
    effective = layout_manager.load_layout_images_info(str(tmpdir))
    assert effective == {
        "layout_images_info": [
            (overview_file_path, "aside", 1),
            (overview_file_path, "aside", 3),
        ]
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
    create_layout_for_test(layout_path, sections=sections, aside=aside)
    effective = layout_manager.load_layout_images_info(str(tmpdir))
    assert effective == {
        "layout_images_info": [
            (overview_file_path, "sections", 1, 1),
            (overview_file_path, "sections", 1, 2),
            (overview_file_path, "aside", 2),
            (overview_file_path, "aside", 4),
        ]
    }
