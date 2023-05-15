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
from typing import Any

from cads_catalogue import layout_manager, utils

logger = logging.getLogger(__name__)


def check_values(input_obj, values_to_exclude=[]):
    """Check recursively if input list/dict has forbidden values."""
    if type(input_obj) is dict:
        for key, value in input_obj.items():
            if values_to_exclude and value in values_to_exclude:
                value_repr = value is None and "'null'" or repr(value)
                logger.error(f"found key {key} with a forbidden value: {value_repr}")
                continue
            check_values(value, values_to_exclude=values_to_exclude)
    elif type(input_obj) is list:
        for item in input_obj:
            if values_to_exclude and item in values_to_exclude:
                item_repr = item is None and "'null'" or repr(item)
                logger.error(f"found unexpected item {item_repr}")
                continue
            check_values(item, values_to_exclude=values_to_exclude)
    return


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


def validate_stringchoicewidget(widget_data: dict[str, Any]):
    """Do a validation of StringChoiceWidget."""
    w_type = widget_data.get("type", "StringChoiceWidget")
    w_name = widget_data.get("name")
    if not w_name:
        logger.error(f"found {w_type} without required key 'name'")
        return
    if "details" not in widget_data:
        logger.error(f"found {w_type} named '{w_name}' without required key 'details'")
        return
    details = widget_data["details"]
    try:
        assert details
        assert isinstance(details, dict)
    except AssertionError:
        logger.error(
            f"key 'details' of {w_type} named '{w_name}' must be a not empty dictionary"
        )
        return
    if "default" not in details:
        logger.error(f"found {w_type} named '{w_name}' without a default value")
        return
    default = details["default"]
    try:
        assert default
        assert isinstance(default, list)
        assert len(default) == 1
    except AssertionError:
        logger.error(
            f"default of {w_type} named '{w_name}' must be defined as a list of one element"
        )
        return

    if "values" not in details:
        logger.error(f"found {w_type} named '{w_name}' without a list of values")
        return
    values = details["values"]
    try:
        assert values
        assert isinstance(values, list)
        assert len(values)
    except AssertionError:
        logger.error(
            f"key 'values' of {w_type} named '{w_name}' must be a not empty list"
        )
        return

    if default[0] not in values:
        logger.error(
            f"default of {w_type} named '{w_name}' is not included in the allowed list of values"
        )
        return


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
    data = validate_base_json(dataset_folder, file_name)
    if not data:
        return
    check_values(data, values_to_exclude=[None])


def validate_form(dataset_folder):
    """Validate form.json of a dataset."""
    file_name = "form.json"
    data = validate_base_json(dataset_folder, file_name)
    if not data:
        return
    # validators_map = {
    #     # widget type: validator function,
    #     "StringChoiceWidget": validate_stringchoicewidget,
    # }
    # for widget_data in data:
    #     w_type = widget_data.get("type")
    #     if w_type in validators_map:
    #         validators_map[w_type](widget_data)


def validate_layout(dataset_folder):
    """Validate layout.json of a dataset."""
    file_name = "layout.json"
    layout_data = validate_base_json(dataset_folder, file_name)
    if not os.path.isfile(os.path.join(dataset_folder, file_name)):
        return
    # validate for images
    try:
        layout_manager.transform_image_blocks(
            layout_data,
            dataset_folder,
            {"resource_uid": "validation"},
            None,
            disable_upload=True,
        )
    except Exception:  # noqa
        logger.exception(f"Image parsing of {file_name} not compliant. Error follows.")


def validate_mapping(dataset_folder):
    """Validate mapping.json of a dataset."""
    file_name = "mapping.json"
    validate_base_json(dataset_folder, file_name, required=False)


def validate_metadata_json(dataset_folder):
    """Validate metadata.json of a dataset."""
    file_name = "metadata.json"
    data = validate_base_json(dataset_folder, file_name)
    if not os.path.isfile(os.path.join(dataset_folder, file_name)):
        return
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
        if optional_field not in data or data.get(optional_field) is None:
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
                if date_field == "end_date" and value == "now":
                    continue
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
        print()
    logger.info("----end of validations----")
