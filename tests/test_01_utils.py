import os.path
import subprocess

import pytest
import pytest_mock

from cads_catalogue import utils

THIS_PATH = os.path.abspath(os.path.dirname(__file__))
TEST_RESOURCES_DATA_PATH = os.path.abspath(
    os.path.join(THIS_PATH, "..", "tests", "data", "cads-forms-json")
)


def test_get_last_commit_hash(mocker: pytest_mock.MockerFixture) -> None:
    spy1 = mocker.spy(subprocess, "Popen")
    ret_value = utils.get_last_commit_hash(THIS_PATH)
    assert isinstance(ret_value, str)
    assert len(ret_value) == 40
    assert spy1.mock_calls[0].args == ('git log -n 1 --pretty=format:"%H"',)
    with pytest.raises(FileNotFoundError):
        utils.get_last_commit_hash("/not/exists")


def test_normalize_abstract():
    replacer_map = {'sup': utils.superscript_text, 'sub': utils.subscript_text}
    text = "This dataset provides <sup>observations</sup> of atmospheric methane (CH<SUB>4</SUB>) " \
           "more he <b>C</b>opernicus <b>E</b>uropean <b>R</b>egional <b>R</b>e<b>A</b>n"
    parser = utils.TagReplacer(replacer_map)
    parser.feed(text)

    assert parser.output_text == 'This dataset provides ᵒᵇˢᵉʳᵛᵃᵗᶦᵒⁿˢ of atmospheric methane (CH₄) ' \
                                 'more he Copernicus European Regional ReAn'


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
