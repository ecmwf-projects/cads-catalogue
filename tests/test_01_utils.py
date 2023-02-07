import json
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
        utils.get_last_commit_hash('/not/exists')


def test_recursive_search() -> None:
    obj1 = {
        "a": 1,
        "b": [
            {"a": 2, "b": {"a": 3, "b": 4}},
            [1, 2, 3],
            [{}, {"b": 4}, {"a": 4, "b": 4}],
        ],
        "c": {"a": 5, "b": {"a": 6, "b": 4}},
    }
    res1 = utils.recursive_key_search(obj1, key="a")
    assert res1 == [1, 2, 3, 4, 5, 6]
    form_json_path = os.path.join(
        TEST_RESOURCES_DATA_PATH,
        "satellite-surface-radiation-budget",
        "form.json",
    )
    with open(form_json_path) as fp:
        form_data = json.load(fp)
    search_results = utils.recursive_key_search(form_data, key="labels")
    assert search_results == [
        {
            "cci": "CCI (Climate Change Initiative)",
            "clara": "CLARA (CLoud, Albedo and Radiation)",
        },
        {
            "c3s": "C3S (Copernicus Climate Change Service)",
            "esa": "ESA (European Space Agency)",
            "eumetsat": "EUMETSAT (European Organisation for the Exploitation of "
            "Meteorological Satellites)",
        },
        {
            "all_variables": "All variables (CCI product family)",
            "surface_downwelling_longwave_flux": "Surface downwelling longwave  flux",
            "surface_downwelling_shortwave_flux": "Surface downwelling shortwave  flux",
            "surface_net_downward_longwave_flux": "Surface net downward longwave  flux",
            "surface_net_downward_radiative_flux": "Surface net downward radiative flux",
            "surface_net_downward_shortwave_flux": "Surface net downward shortwave  flux",
            "surface_upwelling_longwave_flux": "Surface upwelling longwave  flux",
            "surface_upwelling_shortwave_flux": "Surface upwelling shortwave  flux",
        },
        {
            "interim_climate_data_record": "Interim Climate Data Record (ICDR)",
            "thematic_climate_data_record": "Thematic Climate Data Record (TCDR)",
        },
        {
            "aatsr_on_envisat": "AATSR on ENVISAT",
            "atsr2_on_ers2": "ATSR2 on ERS2",
            "avhrr_on_multiple_satellites": "AVHRR on multiple satellites",
            "slstr_on_sentinel_3a_is_under_investigation": "SLSTR on Sentinel-3A is "
            "under investigation",
            "slstr_on_sentinel_3b_is_under_investigation": "SLSTR on Sentinel-3B is "
            "under investigation",
        },
        {"daily_mean": "Daily mean", "monthly_mean": "Monthly mean"},
        {
            "1982": "1982",
            "1983": "1983",
            "1984": "1984",
            "1985": "1985",
            "1986": "1986",
            "1987": "1987",
            "1988": "1988",
            "1989": "1989",
            "1990": "1990",
            "1991": "1991",
            "1992": "1992",
            "1993": "1993",
            "1994": "1994",
            "1995": "1995",
            "1996": "1996",
            "1997": "1997",
            "1998": "1998",
            "1999": "1999",
            "2000": "2000",
            "2001": "2001",
            "2002": "2002",
            "2003": "2003",
            "2004": "2004",
            "2005": "2005",
            "2006": "2006",
            "2007": "2007",
            "2008": "2008",
            "2009": "2009",
            "2010": "2010",
            "2011": "2011",
            "2012": "2012",
            "2013": "2013",
            "2014": "2014",
            "2015": "2015",
            "2016": "2016",
            "2017": "2017",
            "2018": "2018",
            "2019": "2019",
            "2020": "2020",
            "2021": "2021",
        },
        {
            "01": "January",
            "02": "February",
            "03": "March",
            "04": "April",
            "05": "May",
            "06": "June",
            "07": "July",
            "08": "August",
            "09": "September",
            "10": "October",
            "11": "November",
            "12": "December",
        },
        {
            "01": "01",
            "02": "02",
            "03": "03",
            "04": "04",
            "05": "05",
            "06": "06",
            "07": "07",
            "08": "08",
            "09": "09",
            "10": "10",
            "11": "11",
            "12": "12",
            "13": "13",
            "14": "14",
            "15": "15",
            "16": "16",
            "17": "17",
            "18": "18",
            "19": "19",
            "20": "20",
            "21": "21",
            "22": "22",
            "23": "23",
            "24": "24",
            "25": "25",
            "26": "26",
            "27": "27",
            "28": "28",
            "29": "29",
            "30": "30",
            "31": "31",
        },
        {"v1_0": "v1.0"},
        {"tgz": "Compressed tar file (.tar.gz)", "zip": "Zip file (.zip)"},
    ]


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
