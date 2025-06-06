import json
import os.path

import pytest
import pytest_mock
import sqlalchemy as sa

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


def test_transform_licence_required_blocks(tmpdir, session_obj: sa.orm.sessionmaker):
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
        all_licences = session.scalars(sa.select(database.Licence)).all()
    # create a test layout.json
    layout_path = os.path.join(str(tmpdir), "layout.json")
    block1 = {"licence-id": all_licences[0].licence_uid, "type": "licence"}
    block2 = {
        "type": "link",
        "id": "test-link-id",
        "title": "a link",
        "href": "http://a-link.html",
    }
    block3 = {"licence-id": all_licences[1].licence_uid, "type": "licence"}
    sections = [
        {"id": "overview", "blocks": [block1, block2, block3]},
        {"id": "overview2", "blocks": [block2, block3]},
    ]
    aside = {"blocks": [block1, block2]}

    layout_data = create_layout_for_test(layout_path, sections=sections, aside=aside)

    new_layout_data = layout_manager.transform_licence_required_blocks(
        session, layout_data, storage_settings
    )
    assert new_layout_data == {
        "uid": "cams-global-reanalysis-eac4",
        "body": {
            "main": {
                "sections": [
                    {
                        "id": "overview",
                        "blocks": layout_manager.build_required_licence_blocks(
                            all_licences[0], storage_settings.document_storage_url
                        )
                        + [block2]
                        + layout_manager.build_required_licence_blocks(
                            all_licences[1], storage_settings.document_storage_url
                        ),
                    },
                    {
                        "id": "overview2",
                        "blocks": [block2]
                        + layout_manager.build_required_licence_blocks(
                            all_licences[1], storage_settings.document_storage_url
                        ),
                    },
                ]
            },
            "aside": {
                "blocks": layout_manager.build_required_licence_blocks(
                    all_licences[0], storage_settings.document_storage_url
                )
                + [block2]
            },
        },
    }

    # build a nested version
    block1 = {"licence-id": all_licences[0].licence_uid, "type": "licence"}
    block2 = {
        "type": "link",
        "id": "test-link-id",
        "title": "a link",
        "href": "http://a-link.html",
    }
    block3 = {"licence-id": all_licences[1].licence_uid, "type": "licence"}
    section1 = {"id": "overview", "blocks": [block1, block2, block3]}
    section2 = {"id": "overview2", "blocks": [block2, block3]}
    section3 = {"id": "section1", "type": "section", "blocks": [block1, block3]}
    section4 = {
        "id": "accordion1",
        "type": "accordion",
        "blocks": [section3, block1, block2],
    }
    sections = [section1, section4, section2]
    aside = {"blocks": [block1, block2, section4, block3]}
    new_block1 = layout_manager.build_required_licence_blocks(
        all_licences[0], storage_settings.document_storage_url
    )
    new_block3 = layout_manager.build_required_licence_blocks(
        all_licences[1], storage_settings.document_storage_url
    )
    layout_data = create_layout_for_test(layout_path, sections=sections, aside=aside)

    new_layout_data = layout_manager.transform_licence_required_blocks(
        session, layout_data, storage_settings
    )
    expected = {
        "uid": "cams-global-reanalysis-eac4",
        "body": {
            "main": {
                "sections": [
                    {"id": "overview", "blocks": new_block1 + [block2] + new_block3},
                    {
                        "id": "accordion1",
                        "type": "accordion",
                        "blocks": [
                            {
                                "id": "section1",
                                "type": "section",
                                "blocks": new_block1 + new_block3,
                            }
                        ]
                        + new_block1
                        + [block2],
                    },
                    {"id": "overview2", "blocks": [block2] + new_block3},
                ]
            },
            "aside": {
                "blocks": new_block1
                + [block2]
                + [
                    {
                        "id": "accordion1",
                        "type": "accordion",
                        "blocks": [
                            {
                                "id": "section1",
                                "type": "section",
                                "blocks": new_block1 + new_block3,
                            }
                        ]
                        + new_block1
                        + [block2],
                    },
                ]
                + new_block3
            },
        },
    }
    assert new_layout_data == expected
    session.close()


def test_manage_image_section(tmpdir, mocker: pytest_mock.MockerFixture) -> None:
    oss = config.ObjectStorageSettings(
        object_storage_url="http://myobject-storage:myport/",
        storage_admin="storage_user",
        storage_password="storage_password",
        catalogue_bucket="abucket",
        document_storage_url="http://public-storage/",
    )
    mocker.patch.object(object_storage, "store_file", return_value="an url")
    resource = {"resource_uid": "a-dataset"}
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
    multi_images_block = {
        "id": "abstract",
        "type": "thumb-markdown",
        "content": "a content",
        "image": [
            {
                "url": "overview/overview.png",
                "alt": "alternative text1",
            },
            {
                "url": "overview/overview2.png",
                "alt": "alternative text2",
            },
        ],
    }
    modified_image_block = {
        "id": "abstract",
        "type": "thumb-markdown",
        "content": "a content",
        "image": {
            "url": "http://public-storage/an url",
            "alt": "alternative text",
        },
    }
    multi_images_block_uploaded = {
        "id": "abstract",
        "type": "thumb-markdown",
        "content": "a content",
        "image": [
            {
                "url": "http://public-storage/an url",
                "alt": "alternative text1",
            },
            {
                "url": "http://public-storage/an url",
                "alt": "alternative text2",
            },
        ],
    }
    section = {"id": "overview", "blocks": [no_image_block, image_block]}
    images_stored: dict[str, str] = dict()
    image_storage_subpath = f"resources/{resource['resource_uid']}"
    # not found overview/overview.png
    with pytest.raises(ValueError):
        layout_manager.manage_image_section(
            str(tmpdir), section, images_stored, image_storage_subpath, oss
        )
    # url is already uploaded: no change
    image_block_already_url = {
        "id": "abstract",
        "type": "thumb-markdown",
        "content": "a content",
        "image": {
            "url": "http://anurl.com/overview/overview.png",
            "alt": "alternative text",
        },
    }
    section = {"id": "overview", "blocks": [no_image_block, image_block_already_url]}
    new_section = layout_manager.manage_image_section(
        str(tmpdir), section, images_stored, image_storage_subpath, oss
    )
    assert new_section == section

    # create image overview/overview.png and repeat the test
    overview_path = os.path.join(str(tmpdir), "overview")
    os.mkdir(overview_path)
    overview_file_path = os.path.join(overview_path, "overview.png")
    with open(overview_file_path, "w") as fp:
        fp.write("hello! I am an image")
    overview2_file_path = os.path.join(overview_path, "overview2.png")
    with open(overview2_file_path, "w") as fp:
        fp.write("hello! I am an image2")
    # 1 image block
    section = {"id": "overview", "blocks": [no_image_block, image_block]}
    new_section = layout_manager.manage_image_section(
        str(tmpdir), section, images_stored, image_storage_subpath, oss
    )
    assert new_section == {
        "id": "overview",
        "blocks": [no_image_block, modified_image_block],
    }
    assert section == {
        "id": "overview",
        "blocks": [no_image_block, image_block],
    }  # function never changes input

    # case section without replace to do
    section = {"id": "overview", "blocks": [no_image_block, no_image_block]}
    new_section = layout_manager.manage_image_section(
        str(tmpdir), section, images_stored, image_storage_subpath, oss
    )
    assert new_section == section

    # case section with more separeted image blocks
    section = {"id": "overview", "blocks": [image_block, no_image_block, image_block]}
    new_section = layout_manager.manage_image_section(
        str(tmpdir), section, images_stored, image_storage_subpath, oss
    )
    assert new_section == {
        "id": "overview",
        "blocks": [modified_image_block, no_image_block, modified_image_block],
    }

    # case section with nested image_blocks
    inside_section1 = {
        "id": "overview2",
        "type": "section",
        "blocks": [image_block, no_image_block, image_block],
    }
    inside_section2 = {
        "id": "overview3",
        "type": "accordion",
        "blocks": [no_image_block, inside_section1],
    }
    section = {
        "id": "overview",
        "blocks": [
            image_block,
            image_block,
            no_image_block,
            inside_section2,
            no_image_block,
        ],
    }
    new_section = layout_manager.manage_image_section(
        str(tmpdir), section, images_stored, image_storage_subpath, oss
    )
    assert new_section == {
        "id": "overview",
        "blocks": [
            modified_image_block,
            modified_image_block,
            no_image_block,
            {
                "id": "overview3",
                "type": "accordion",
                "blocks": [
                    no_image_block,
                    {
                        "id": "overview2",
                        "type": "section",
                        "blocks": [
                            modified_image_block,
                            no_image_block,
                            modified_image_block,
                        ],
                    },
                ],
            },
            no_image_block,
        ],
    }
    # case section with a block with multiple images
    section = {"id": "overview", "blocks": [no_image_block, multi_images_block]}
    new_section = layout_manager.manage_image_section(
        str(tmpdir), section, images_stored, image_storage_subpath, oss
    )
    assert new_section == {
        "id": "overview",
        "blocks": [no_image_block, multi_images_block_uploaded],
    }


def test_transform_image_blocks(tmpdir, mocker: pytest_mock.MockerFixture) -> None:
    oss = config.ObjectStorageSettings(
        object_storage_url="http://myobject-storage:myport/",
        storage_admin="storage_user",
        storage_password="storage_password",
        catalogue_bucket="abucket",
        document_storage_url="http://public-storage/",
    )
    mocker.patch.object(object_storage, "store_file", return_value="an url")
    layout_path = os.path.join(str(tmpdir), "layout.json")
    resource = {"resource_uid": "a-dataset"}
    image_storage_subpath = f"resources/{resource['resource_uid']}"
    # missing blocks with images
    layout_data = create_layout_for_test(layout_path)
    new_layout_data = layout_manager.transform_image_blocks(
        layout_data, str(tmpdir), image_storage_subpath, oss
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
        layout_manager.transform_image_blocks(
            layout_data, str(tmpdir), image_storage_subpath, oss
        )

    # create image overview/overview.png and repeat the test
    overview_path = os.path.join(str(tmpdir), "overview")
    os.mkdir(overview_path)
    overview_file_path = os.path.join(overview_path, "overview.png")
    with open(overview_file_path, "w") as fp:
        fp.write("hello! I am an image")
    new_layout_data = layout_manager.transform_image_blocks(
        layout_data, str(tmpdir), image_storage_subpath, oss
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
        layout_data, str(tmpdir), image_storage_subpath, oss
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
        layout_data, str(tmpdir), image_storage_subpath, oss
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
    assert layout_data != new_layout_data  # function doesn't change input

    # only on aside, position 1 and 3
    aside = {"blocks": [no_image_block, image_block, no_image_block, image_block]}
    layout_data = create_layout_for_test(layout_path, aside=aside)
    new_layout_data = layout_manager.transform_image_blocks(
        layout_data, str(tmpdir), image_storage_subpath, oss
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
        layout_data, str(tmpdir), image_storage_subpath, oss
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


def test_transform_cim_blocks(tmpdir):
    layout_path = os.path.join(str(tmpdir), "layout.json")
    cim_layout_path = os.path.join(str(tmpdir), "quality_assurance.layout.json")
    test_sections_1 = [
        {
            "id": "overview",
            "title": "an overview",
            "blocks": [
                {"id": "abstract1", "type": "a type", "content": "a content"},
                {"id": "abstract2", "type": "a type", "content": "a content"},
            ],
        },
        {
            "id": "overview2",
            "title": "an overview 2",
            "blocks": [
                {"id": "abstract3", "type": "a type", "content": "a content"},
                {
                    "id": "abstract4",
                    "type": "thumb-markdown",
                    "content": "a content",
                    "image": {
                        "url": "http://public-storage/an url",
                        "alt": "alternative text",
                    },
                },
                {"id": "abstract5", "type": "a type", "content": "a content"},
            ],
        },
    ]
    test_aside_1 = {
        "id": "an id",
        "title": "a title",
        "type": "a type",
        "blocks": [
            {"id": "abstract1", "type": "a type", "content": "a content"},
            {"id": "abstract2", "type": "a type", "content": "a content"},
            {
                "id": "abstract3",
                "type": "thumb-markdown",
                "content": "a content",
                "image": {
                    "url": "http://public-storage/an url",
                    "alt": "alternative text",
                },
            },
            {"id": "abstract4", "type": "a type", "content": "a content"},
        ],
    }
    # test case 1: not existing cim layout, not existing QA sections -> no change of input layout_data
    layout_data = create_layout_for_test(
        layout_path, sections=test_sections_1, aside=test_aside_1
    )
    new_layout_data = layout_manager.transform_cim_blocks(
        layout_data, cim_layout_path=cim_layout_path
    )
    assert new_layout_data == layout_data

    # test case 2: not existing cim layout, existing only QA_tab section -> remove placeholder
    qa_tab_section = {
        "title": "Quality assurance, or whatever",
        "id": "quality_assurance_tab",
        "type": "a_section_type",
        "blocks": [],
    }
    test_sections_2 = [test_sections_1[0], qa_tab_section, test_sections_1[1]]
    layout_data = create_layout_for_test(
        layout_path, sections=test_sections_2, aside=test_aside_1
    )
    new_layout_data = layout_manager.transform_cim_blocks(
        layout_data, cim_layout_path=cim_layout_path
    )
    assert new_layout_data == create_layout_for_test(
        layout_path, sections=test_sections_1, aside=test_aside_1
    )
    # test case 3: not existing cim layout, existing only QA_aside block -> remove placeholder
    new_aside_block = {
        "title": "QA or whatever",
        "id": "quality_assurance_aside",
        "type": "section",
    }
    test_aside_2 = {
        "blocks": test_aside_1["blocks"][:2]
        + [new_aside_block]
        + test_aside_1["blocks"][2:],
        "title": "a new title",
        "type": "a new type",
    }
    expected_aside_2 = {
        "blocks": test_aside_1["blocks"],
        "title": "a new title",
        "type": "a new type",
    }
    layout_data = create_layout_for_test(
        layout_path, sections=test_sections_1, aside=test_aside_2
    )
    new_layout_data = layout_manager.transform_cim_blocks(
        layout_data, cim_layout_path=cim_layout_path
    )
    assert new_layout_data == create_layout_for_test(
        layout_path, sections=test_sections_1, aside=expected_aside_2
    )

    # test case 4: existing cim layout, not existing QA section/aside on layout
    # -> no change of input layout_data
    layout_data = create_layout_for_test(
        layout_path, sections=test_sections_1, aside=test_aside_1
    )
    cim_layout_path = os.path.join(
        TESTDATA_PATH,
        "cads-forms-cim-json",
        "reanalysis-era5-land",
        "quality_assurance.layout.json",
    )
    with open(cim_layout_path) as fp:
        cim_layout_data = json.load(fp)
        quality_assurance_tab = cim_layout_data["quality_assurance_tab"]
        quality_assurance_tab["id"] = "quality_assurance_tab"
        quality_assurance_aside = cim_layout_data["quality_assurance_aside"]
        quality_assurance_aside["id"] = "quality_assurance_aside"
    new_layout_data = layout_manager.transform_cim_blocks(
        layout_data, cim_layout_path=cim_layout_path
    )
    assert new_layout_data == layout_data

    # test case 5: existing cim layout, existing only QA section on layout
    # -> layout_data with QA section replaced
    layout_data = create_layout_for_test(
        layout_path, sections=test_sections_2, aside=test_aside_1
    )
    new_layout_data = layout_manager.transform_cim_blocks(
        layout_data, cim_layout_path=cim_layout_path
    )
    assert new_layout_data == {
        "uid": "cams-global-reanalysis-eac4",
        "body": {
            "main": {
                "sections": [
                    test_sections_1[0],
                    quality_assurance_tab,
                    test_sections_1[1],
                ]
            },
            "aside": test_aside_1,
        },
    }

    # test case 6: existing cim layout, existing only QA aside block -> layout_data with QA aside replaced
    layout_data = create_layout_for_test(
        layout_path, sections=test_sections_1, aside=test_aside_2
    )
    new_layout_data = layout_manager.transform_cim_blocks(
        layout_data, cim_layout_path=cim_layout_path
    )

    assert new_layout_data == {
        "uid": "cams-global-reanalysis-eac4",
        "body": {
            "main": {
                "sections": test_sections_1,
            },
            "aside": {
                "blocks": test_aside_1["blocks"][:2]
                + [quality_assurance_aside]
                + test_aside_1["blocks"][2:],
                "title": "a new title",
                "type": "a new type",
            },
        },
    }

    # test case 7: existing cim layout, existing both section and aside blocks
    layout_data = create_layout_for_test(
        layout_path, sections=test_sections_2, aside=test_aside_2
    )
    new_layout_data = layout_manager.transform_cim_blocks(
        layout_data, cim_layout_path=cim_layout_path
    )
    assert new_layout_data == {
        "uid": "cams-global-reanalysis-eac4",
        "body": {
            "main": {
                "sections": [
                    test_sections_1[0],
                    quality_assurance_tab,
                    test_sections_1[1],
                ]
            },
            "aside": {
                "blocks": test_aside_1["blocks"][:2]
                + [quality_assurance_aside]
                + test_aside_1["blocks"][2:],
                "title": "a new title",
                "type": "a new type",
            },
        },
    }

    # test case 8: existing cim layout, existing both section and aside blocks, but qa_flag is False
    # -> layout_data with placeholders removed
    layout_data = create_layout_for_test(
        layout_path, sections=test_sections_2, aside=test_aside_2
    )
    new_layout_data = layout_manager.transform_cim_blocks(
        layout_data, cim_layout_path=cim_layout_path, qa_flag=False
    )
    assert new_layout_data == {
        "uid": "cams-global-reanalysis-eac4",
        "body": {
            "main": {
                "sections": [
                    test_sections_1[0],
                    test_sections_1[1],
                ]
            },
            "aside": {
                "blocks": test_aside_1["blocks"][:2] + test_aside_1["blocks"][2:],
                "title": "a new title",
                "type": "a new type",
            },
        },
    }


def test_has_section_id(tmpdir):
    layout_path = os.path.join(str(tmpdir), "layout.json")
    test_sections_1 = [
        {
            "id": "overview",
            "blocks": [
                {"id": "abstract1", "type": "a type", "content": "a content"},
            ],
        },
        {
            "id": "overview2",
            "blocks": [
                {"id": "abstract2", "type": "a type", "content": "a content"},
            ],
        },
        {
            "id": "overview3",
            "blocks": [
                {"id": "abstract3", "type": "a type", "content": "a content"},
            ],
        },
    ]
    # test case 1: not existing cim layout, not existing layout sections
    layout_data = create_layout_for_test(layout_path, sections=test_sections_1)
    assert layout_manager.has_section_id(layout_data, "overview2") is True
    assert layout_manager.has_section_id(layout_data, "overview4") is False


def test_transform_licence_acceptance_blocks(session_obj: sa.orm.sessionmaker):
    my_settings_dict = {
        "object_storage_url": "https://object/storage/url/",
        "storage_admin": "admin1",
        "storage_password": "secret1",
        "catalogue_bucket": "mycatalogue_bucket",
        "document_storage_url": "https://document/storage/url/",
    }
    storage_settings = config.ObjectStorageSettings(**my_settings_dict)
    # add some licences to work on
    licences_folder_path = os.path.join(TESTDATA_PATH, "cads-licences")
    licences = licence_manager.load_licences_from_folder(licences_folder_path)
    with session_obj() as session:
        for licence in licences:
            # simulate upload to storage
            licence["download_filename"] = os.path.join(
                storage_settings.catalogue_bucket,
                "licences",
                licence["licence_uid"],
                "test_storage_path.pdf",
            )
            licence["md_filename"] = os.path.join(
                storage_settings.catalogue_bucket,
                "licences",
                licence["licence_uid"],
                "test_storage_path.md",
            )
            session.add(database.Licence(**licence))
        session.commit()
        # all_licences = session.scalars(sa.select(database.Licence)).all()

    input_layout_path = os.path.join(TESTDATA_PATH, "layout1.json")
    with open(input_layout_path) as fp:
        input_layout_data = json.load(fp)
    out_layout_data = layout_manager.transform_licence_acceptance_blocks(
        session, input_layout_data, storage_settings
    )
    expected_layout_path = os.path.join(TESTDATA_PATH, "layout2.json")
    # with open(expected_layout_path, "w") as fp:
    #     json.dump(out_layout_data, fp, indent=2)
    with open(expected_layout_path) as fp:
        expected_layout_data = json.load(fp)
    assert out_layout_data == expected_layout_data
    session.close()


def build_layout_data(blocks):
    """For testing transform_html_blocks."""
    layout_data = {
        "title": "CDSAPI setup",
        "description": "Access the full data store catalogue, with search and availability features",
        "body": {
            "main": {
                "sections": [
                    {
                        "id": "main",
                        "blocks": blocks,
                    }
                ]
            }
        },
    }
    return layout_data


def test_transform_html_blocks():
    # note: layout_folder_path is the reference for relative path of the html content source
    layout_folder_path = os.path.join(TESTDATA_PATH, "cads-contents-json", "how-to-api")
    with open(
        os.path.join(TESTDATA_PATH, "cads-contents-json", "html_block.html")
    ) as fp:
        html_block_content = fp.read()
    thumb_block = {
        "id": "test_block",
        "type": "thumb-markdown",
        "content": "EAC4",
    }
    html_block_no_change = {
        "id": "test_block",
        "type": "html",
        "content": "<p>this must be static</p>",
    }
    html_block_replace = {
        "id": "test_block",
        "type": "html",
        "content_source": "../html_block.html",
    }
    html_block_overwrite = {
        "id": "test_block",
        "type": "html",
        "content_source": "../html_block.html",
        "content": "<div>to be overriden</div>",
    }
    html_block_default = {
        "id": "test_block",
        "type": "html",
        "content_source": "../not_exist.html",
        "content": "<div>to be overriden</div>",
    }
    html_block_broken = {
        "id": "test_block",
        "type": "html",
        "content_source": "../not_exist.html",
    }
    exp_html_block_replaced = {
        "id": "test_block",
        "type": "html",
        "content": html_block_content,
    }
    exp_html_block_default = {
        "id": "test_block",
        "type": "html",
        "content": "<div>to be overriden</div>",
    }
    # no change
    in_layout_data = build_layout_data([thumb_block, html_block_no_change, thumb_block])
    out_layout_data = layout_manager.transform_html_blocks(
        in_layout_data, layout_folder_path
    )
    assert out_layout_data == in_layout_data
    # replace
    in_layout_data = build_layout_data([thumb_block, html_block_replace, thumb_block])
    out_layout_data = layout_manager.transform_html_blocks(
        in_layout_data, layout_folder_path
    )
    assert out_layout_data == build_layout_data(
        [thumb_block, exp_html_block_replaced, thumb_block]
    )
    # overwrite
    in_layout_data = build_layout_data([thumb_block, html_block_overwrite, thumb_block])
    out_layout_data = layout_manager.transform_html_blocks(
        in_layout_data, layout_folder_path
    )
    assert out_layout_data == build_layout_data(
        [thumb_block, exp_html_block_replaced, thumb_block]
    )
    # default
    in_layout_data = build_layout_data([thumb_block, html_block_default, thumb_block])
    out_layout_data = layout_manager.transform_html_blocks(
        in_layout_data, layout_folder_path
    )
    assert out_layout_data == build_layout_data(
        [thumb_block, exp_html_block_default, thumb_block]
    )
    # broken
    in_layout_data = build_layout_data([thumb_block, html_block_broken, thumb_block])
    with pytest.raises(ValueError):
        layout_manager.transform_html_blocks(in_layout_data, layout_folder_path)
