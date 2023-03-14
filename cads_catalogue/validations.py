"""utility module to validated input files for the catalogue manager."""

# Copyright 2023, European Union.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import glob
import json
import logging
import os

from cads_catalogue import utils

logger = logging.getLogger(__name__)


def validate_base_json(folder, file_name, required=True):
    """Do a base validation of a json file inside a folder."""
    logger.info(f"-starting validation of {file_name}-")
    file_path = os.path.join(folder, file_name)
    if not os.path.isfile(file_path):
        if required:
            logger.error(f"{file_name} not found")
        return

    with open(file_path) as fp:
        try:
            data = json.load(fp)
        except Exception:  # noqa
            logger.exception(f"{file_name} is not a valid json")
            return
    return data


def validate_adaptors(dataset_folder):
    """Validate adaptor information of a dataset."""
    logger.info("-starting validation of adaptors-")
    adaptor_conf_file_path = os.path.join(dataset_folder, "adaptor.json")
    adaptor_code_file_path = os.path.join(dataset_folder, "adaptor.py")
    if not os.path.isfile(adaptor_conf_file_path):
        if os.path.isfile(adaptor_code_file_path):
            logger.error("found adaptor.py without adaptor.json")
        return

    with open(adaptor_conf_file_path) as fp:
        try:
            data = json.load(fp)
        except Exception:  # noqa
            logger.exception("adaptor.json is not a valid json")
            return

    entry_point = data.get("entry_point")
    if not entry_point:
        return

    adaptor_code_file_path = os.path.join(dataset_folder, "adaptor.py")
    if ":" in entry_point:
        if os.path.isfile(adaptor_code_file_path):
            logger.error(
                f"found adaptor.py: remove it or change inconsistent entry_point '{entry_point}'"
            )
    else:
        if not os.path.isfile(adaptor_code_file_path):
            logger.error(
                f"adaptor.py not found: add it or change inconsistent entry_point '{entry_point}'"
            )
        else:
            with open(adaptor_code_file_path) as fp:
                code = fp.read()
            if entry_point not in code:
                logger.error(f"class name '{entry_point}' not found in adaptor.py")


def validate_constraints(dataset_folder):
    """Validate constraints.json of a dataset."""
    file_name = "constraints.json"
    validate_base_json(dataset_folder, file_name)


def validate_form(dataset_folder):
    """Validate form.json of a dataset."""
    file_name = "form.json"
    validate_base_json(dataset_folder, file_name)


def validate_layout(dataset_folder):
    """Validate layout.json of a dataset."""
    file_name = "layout.json"
    layout_data = validate_base_json(dataset_folder, file_name)

    found_image = False
    # search all the images inside body/main/sections:
    sections = layout_data.get("body", {}).get("main", {}).get("sections", [])
    for i, section in enumerate(sections):
        blocks = section.get("blocks", [])
        for j, block in enumerate(blocks):
            image_rel_path = block.get("image", {}).get("url")
            if block.get("type") == "thumb-markdown" and image_rel_path:
                image_abs_path = os.path.join(dataset_folder, block["image"]["url"])
                if not os.path.isfile(image_abs_path):
                    logger.error(
                        f"image {image_rel_path} referenced on {file_name} not found"
                    )
                else:
                    found_image = True
    # search all the images inside body/aside:
    aside_blocks = layout_data.get("body", {}).get("aside", {}).get("blocks", [])
    for i, block in enumerate(aside_blocks):
        image_rel_path = block.get("image", {}).get("url")
        if block.get("type") == "thumb-markdown" and image_rel_path:
            image_abs_path = os.path.join(dataset_folder, block["image"]["url"])
            if not os.path.isfile(image_abs_path):
                logger.error(
                    f"image {image_rel_path} referenced on {file_name} not found"
                )
            else:
                found_image = True

    if not found_image:
        logger.warning(f"image of the dataset not found in {file_name}")


def validate_mapping(dataset_folder):
    """Validate mapping.json of a dataset."""
    file_name = "mapping.json"
    validate_base_json(dataset_folder, file_name, required=False)


def validate_metadata_json(dataset_folder):
    """Validate metadata.json of a dataset."""
    file_name = "metadata.json"
    data = validate_base_json(dataset_folder, file_name)

    metadata = dict()
    required_fields = ["abstract", "resource_type", "title"]
    for required_field in required_fields:
        if required_field not in data or not data.get(required_field):
            logger.error(f"required field not found or empty: '{required_field}'")
    optional_fields = [
        "bboxE",
        "bboxN",
        "bboxS",
        "bboxW",
        "begin_date",
        "citation",
        "contactemail",
        "data_type",
        "description",
        "doi",
        "ds_contactemail",
        "ds_responsible_individual",
        "ds_responsible_organisation",
        "ds_responsible_organisation_role",
        "end_date",
        "file_format",
        "hidden",
        "inspire_theme",
        "keywords",
        "licences",
        "lineage",
        "publication_date",
        "related_resources_keywords",
        "representative_fraction",
        "responsible_individual",
        "responsible_organisation",
        "responsible_organisation_role",
        "responsible_organisation_website",
        "topic",
        "unit_measure",
        "update_date",
        "use_limitation",
    ]
    for optional_field in optional_fields:
        if optional_field not in data or not data.get(optional_field):
            logger.info(
                f"optional field not found or empty: '{optional_field}', "
                f"consider to include a value"
            )

    extra_fields = sorted(
        set(data.keys()) - set(required_fields).union(set(optional_fields))
    )
    for extra_field in extra_fields:
        logger.warning(f"field currently ignored: '{extra_field}'")

    date_fields = ["begin_date", "end_date", "publication_date"]
    for date_field in date_fields:
        value = data.get(date_field)
        if value:
            try:
                datetime.datetime.strptime(value, "%Y-%m-%d")
            except:  # noqa
                logger.error(
                    f"value '{value}' not parsable as a valid date: use format YYYY-MM-DD"
                )

    try:
        for key, value in data.get("description", dict()).items():
            _ = {
                "id": key,
                "label": key.replace("-", " ").capitalize(),
                "value": value,
            }
    except:  # noqa
        logger.exception("field description not compliant")

    bboxes = ("bboxN", "bboxS", "bboxE", "bboxW")
    if not [data.get(box) for box in bboxes] == [None] * 4:
        try:
            int(data.get("bboxN"))
            int(data.get("bboxS"))
            int(data.get("bboxE"))
            int(data.get("bboxW"))
        except (TypeError, ValueError):
            logger.exception("bbox not compliant")

    if "hidden" in data:
        if not isinstance(data["hidden"], bool):
            try:
                utils.str2bool(data["hidden"])
            except:  # noqa
                logger.exception("field 'hidden' not compliant")

    keywords = data.get("keywords")
    if keywords:
        for keyword in keywords:
            if len(keyword.split(":")) != 2:
                logger.error(f"keyword {keyword} not compliant")

    return metadata


def validate_variables(dataset_folder):
    """Validate variables.json of a dataset."""
    file_name = "variables.json"
    validate_base_json(dataset_folder, file_name, required=False)


def validate_dataset(dataset_folder: str) -> None:
    """
    Validate a dataset folder for the catalogue manager.

    Parameters
    ----------
    dataset_folder: dataset folder path
    """
    resource_uid = os.path.basename(dataset_folder.rstrip(os.sep))
    logger.info(f"---starting validation of resource {resource_uid}---")
    validators = [
        validate_metadata_json,
        validate_adaptors,
        validate_constraints,
        validate_form,
        validate_layout,
        validate_mapping,
        validate_variables,
    ]
    for validator in validators:
        try:
            validator(dataset_folder)
        except Exception:
            logger.exception(
                f"unexpected error running {validator.__name__}. Error follows."
            )
    logger.info(f"---end validation of folder {dataset_folder}---")


def validate_datasets(datasets_folder: str) -> None:
    """
    Explore and report subfolders to validate contents as valid datasets for the catalogue manager.

    Parameters
    ----------
    datasets_folder: the root folder where to search dataset subfolders in
    """
    exclude_folders = (".git",)
    logger.info(f"----starting validations of root folder {datasets_folder}----")
    # load metadata of each resource from files and sync each resource in the db
    for dataset_folder in glob.glob(os.path.join(datasets_folder, "*/")):
        resource_uid = os.path.basename(dataset_folder.rstrip(os.sep))
        if resource_uid in exclude_folders:
            logger.debug(f"excluding folder {resource_uid}")
            continue
        validate_dataset(dataset_folder)
    logger.info("----end of validations----")
