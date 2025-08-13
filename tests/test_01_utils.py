import os.path
import time
from typing import Any, Dict

import pytest

from cads_catalogue import utils

THIS_PATH = os.path.abspath(os.path.dirname(__file__))
TEST_RESOURCES_DATA_PATH = os.path.abspath(
    os.path.join(THIS_PATH, "..", "tests", "data", "cads-forms-json")
)
TEST_CIM_RESOURCES_DATA_PATH = os.path.abspath(
    os.path.join(THIS_PATH, "..", "tests", "data", "cads-forms-cim-json")
)


def test_cadstemplate() -> None:
    # case no use brackets -> no replacing, no raise
    t = utils.CADSTemplate("x is $x")
    assert t.substitute({"x": 1}) == "x is $x"
    assert t.substitute({"y": 1}) == "x is $x"

    # case use brackets -> do replace, raise in case
    t = utils.CADSTemplate("x is ${x}")
    assert t.substitute({"x": 1}) == "x is 1"
    with pytest.raises(utils.CADSTemplateKeyError):
        t.substitute({"y": 1})

    # case escaped without brackets -> no replacing, no raise
    t = utils.CADSTemplate("x is $$x")
    assert t.substitute({"x": 1}) == "x is $$x"
    assert t.substitute({"y": 1}) == "x is $$x"  # and no raise

    # case escaped with brackets -> no replacing, no raise
    t = utils.CADSTemplate("x is $${x}")
    assert t.substitute({"x": 1}) == "x is $${x}"
    assert t.substitute({"y": 1}) == "x is $${x}"  # and no raise


def test_dict_render() -> None:
    input_dict = {
        "replacing_x": "x is ${x}",
        "no_brackets": "x is $x",
        "escape_no_brackets": "x is $$x",
        "escape_with_brackets": "x is $${x}",
    }
    input_list = ["x is ${x}", "x is $x", "x is $$x", "x is $${x}"]
    out_dict = {
        "replacing_x": "x is 1",
        "no_brackets": "x is $x",
        "escape_no_brackets": "x is $$x",
        "escape_with_brackets": "x is $${x}",
    }
    out_list = ["x is 1", "x is $x", "x is $$x", "x is $${x}"]
    assert utils.dict_render(input_dict, {"x": 1, "y": 2}) == out_dict
    assert utils.list_render(input_list, {"x": 1, "y": 2}) == out_list
    # complex dict
    input_dict2: Dict[str, Any] = input_dict.copy()
    input_dict2["dict_inside"] = input_dict
    input_dict2["list_inside"] = input_list
    out_dict2: Dict[str, Any] = out_dict.copy()
    out_dict2["dict_inside"] = out_dict
    out_dict2["list_inside"] = out_list
    assert utils.dict_render(input_dict2, {"x": 1, "y": 2}) == out_dict2


def test_file2hash() -> None:
    test_file_path = os.path.join(
        TEST_RESOURCES_DATA_PATH, "cams-global-reanalysis-eac4", "constraints.json"
    )
    assert (
        utils.file2hash(test_file_path).hexdigest()
        == "1ef896811caf39dd7b3fb7093f8862c6"
    )


def test_folder2hash() -> None:
    test_file_path = os.path.join(
        TEST_RESOURCES_DATA_PATH, "cams-global-reanalysis-eac4"
    )
    assert (
        utils.folder2hash(test_file_path).hexdigest()
        == "48a771d06e98670e3aa8fff982c05d8a"
    )


def test_folders2hash() -> None:
    test_file_path_1 = os.path.join(TEST_RESOURCES_DATA_PATH, "reanalysis-era5-land")
    test_file_path_2 = os.path.join(
        TEST_CIM_RESOURCES_DATA_PATH, "reanalysis-era5-land"
    )
    assert (
        utils.folders2hash([test_file_path_1]).hexdigest()
        == "0a7c7acc72d31fbaeccf72e7de440f09"
    )
    assert (
        utils.folders2hash([test_file_path_1, test_file_path_2]).hexdigest()
        == "1effb88b78313d5147ae7c25ab578968"
    )


def test_normalize_abstract():
    replacer_map = {"sup": utils.superscript_text, "sub": utils.subscript_text}
    text = (
        "This dataset provides <sup>observations</sup> of atmospheric methane (CH<SUB>4</SUB>) "
        "more he <b>C</b>opernicus <b>E</b>uropean <b>R</b>egional <b>R</b>e<b>A</b>n"
    )
    parser = utils.TagReplacer(replacer_map)
    parser.feed(text)

    assert (
        parser.output_text
        == "This dataset provides ᵒᵇˢᵉʳᵛᵃᵗᶦᵒⁿˢ of atmospheric methane (CH₄) "
        "more he Copernicus European Regional ReAn"
    )


def test_str2bool() -> None:
    true_values = ["true", "1", "t", "True", "TRUE", "Y", "yes"]
    for value in true_values:
        assert utils.str2bool(value) is True
    false_values = ["false", "0", "f", "False", "FALSE", "N", "no"]
    for value in false_values:
        assert utils.str2bool(value) is False
    strange_values = ["null", "", "tbd", "U"]
    for value in strange_values:
        with pytest.raises(ValueError):
            assert utils.str2bool(value)
    default = True
    for value in strange_values:
        assert utils.str2bool(value, raise_if_unknown=False, default=default) == default
    for value in strange_values:
        assert utils.str2bool(value, raise_if_unknown=False) is False


def sleep_function(secs, ret_value=None, raises=False):
    # used to test run_function_with_timeout
    time.sleep(secs)
    if raises:
        raise ValueError("this is a value error")
    return ret_value


def test_run_function_with_timeout() -> None:
    # run without any problem
    utils.run_function_with_timeout(
        2,
        "timeout message",
        sleep_function,
        (
            1,
            1,
        ),
    )
    # run with timeout error
    with pytest.raises(TimeoutError):
        utils.run_function_with_timeout(1, "timeout message", sleep_function, (2, 1))
    # run with a raise
    with pytest.raises(ValueError):
        utils.run_function_with_timeout(
            2,
            "timeout message",
            sleep_function,
            (
                1,
                1,
            ),
            {"raises": True},
        )
