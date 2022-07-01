import os.path
from datetime import date
from typing import Any

from sqlalchemy import inspect
from sqlalchemy.orm import sessionmaker

from cads_catalogue import database, manager

THIS_PATH = os.path.abspath(os.path.dirname(__file__))
TESTDATA_PATH = os.path.join(THIS_PATH, "data")


def object_as_dict(obj: Any) -> dict[str, Any]:
    """convert a sqlalchemy object in a python dictionary"""
    return {c.key: getattr(obj, c.key) for c in inspect(obj).mapper.column_attrs}


def test_load_metadata_licences() -> None:
    # test data taken from repository "https://git.ecmwf.int/projects/CDS/repos/cds-licences"
    licences_folder_path = os.path.join(TESTDATA_PATH, "cds-licences")
    expected_licences = [
        {
            "download_filename": "licence-to-use-copernicus-products.pdf",
            "licence_id": "licence-to-use-copernicus-products",
            "revision": 12,
            "title": "Licence to use Copernicus Products",
        }
    ]

    licences = manager.load_licences_from_folder(licences_folder_path)

    assert licences == expected_licences


def test_load_resource_from_folder() -> None:
    resource_folder_path = os.path.join(
        TESTDATA_PATH, "reanalysis-era5-land-monthly-means"
    )
    expected_resource = {
        "abstract": "ERA5-Land is a reanalysis dataset providing a consistent view of the "
        "evolution of land variables over several decades at an enhanced resolution "
        "compared to ERA5. ERA5-Land has been produced by replaying the land "
        "component of the ECMWF ERA5 climate reanalysis. Reanalysis combines model "
        "data with observations from across the world into a globally complete and "
        "consistent dataset using the laws of physics. Reanalysis produces data "
        "that goes several decades back in time, providing an accurate description "
        "of the climate of the past.\n"
        "\n"
        "ERA5-Land provides a consistent view of the water and energy cycles at "
        "surface level during several decades.\n"
        "It contains a detailed record from 1950 onwards, with a temporal "
        "resolution of 1 hour. The native spatial resolution of the ERA5-Land "
        "reanalysis dataset is 9km on a reduced Gaussian grid (TCo1279). The data "
        "in the CDS has been regridded to a regular lat-lon grid of 0.1x0.1 "
        "degrees.\n"
        "\n"
        "The data presented here is a post-processed subset of the full ERA5-Land "
        "dataset. Monthly-mean averages have been pre-calculated to facilitate many "
        "applications requiring easy and fast access to the data, when sub-monthly "
        "fields are not required.\n"
        "\n"
        "Hourly fields can be found in the [ERA5-Land hourly fields CDS "
        "page](https://cds-dev.copernicus-climate.eu/cdsapp#!/dataset/"
        "reanalysis-era5-land?tab=overview "
        '"ERA5-Land hourly data"). Documentation can be found in the [online '
        "ERA5-Land "
        "documentation](https://confluence.ecmwf.int/display/CKB/ERA5-Land+data+documentation "
        '"ERA5-Land data documentation").\n',
        "description": '{"file-format": "GRIB", "data-type": "Gridded", "projection": "Regular '
        'latitude-longitude grid", "horizontal-coverage": "Global", '
        '"horizontal-resolution": "0.1\\u00b0 x 0.1\\u00b0; Native resolution is '
        '9 km.", "vertical-coverage": "From 2 m above the surface level, to a '
        'soil depth of 289 cm.\\n", "vertical-resolution": "4 levels of the '
        "ECMWF surface model: Layer 1: 0 -7cm, Layer 2: 7 -28cm, Layer 3: "
        "28-100cm, Layer 4: 100-289cm\\nSome parameters are defined at 2 m over "
        'the surface.\\n", "temporal-coverage": "January 1950 to present", '
        '"temporal-resolution": "Monthly", "update-frequency": "Monthly with a '
        'delay of 2-3 months relatively to the actual date."}',
        "documentation": '[{"url": '
        '"https://confluence.ecmwf.int/display/CKB/ERA5-Land%3A+data+documentation", '
        '"title": "ERA5-Land online documentation", "description": "Further '
        "and more detailed information relating to the ERA5-Land dataset can "
        'be found in the Copernicus Knowledge Base web link above."}]',
        "form": "[\n"
        "    {\n"
        '        "css": "todo",\n'
        '        "details": {\n'
        '            "columns": 2,\n'
        '            "id": 0,\n'
        '            "labels": {\n'
        '                "monthly_averaged_reanalysis": "Monthly averaged reanalysis",\n'
        '                "monthly_averaged_reanalysis_by_hour_of_day": "Monthly '
        'averaged reanalysis by hour of day"\n'
        "            },\n"
        '            "values": [\n'
        '                "monthly_averaged_reanalysis",\n'
        '                "monthly_averaged_reanalysis_by_hour_of_day"\n'
        "            ]\n"
        "        },\n"
        '        "help": "Monthly averaged reanalysis data are produced by averaging '
        "all daily data. Monthly averages by hour of day constitute the average over "
        'all data within the calendar month for every hour (UTC) of the day.",\n'
        '        "label": "Product type",\n'
        '        "name": "product_type",\n'
        '        "required": true,\n'
        '        "type": "StringListWidget"\n'
        "    },\n"
        "    {\n"
        '        "css": "todo",\n'
        '        "details": {\n'
        '            "accordionGroups": true,\n'
        '            "accordionOptions": {\n'
        '                "openGroups": [\n'
        '                    "Temperature",\n'
        '                    "Lakes",\n'
        '                    "Snow",\n'
        '                    "Soil Water",\n'
        '                    "Radiation and Heat",\n'
        '                    "Evaporation and Runoff",\n'
        '                    "Wind, Pressure and Precipitation",\n'
        '                    "Vegetation",\n'
        '                    "Blacklisted"\n'
        "                ],\n"
        '                "searchable": false\n'
        "            },\n"
        '            "displayaslist": false,\n'
        '            "groups": [\n'
        "                {\n"
        '                    "columns": 2,\n'
        '                    "label": "Temperature",\n'
        '                    "labels": {\n'
        '                        "2m_dewpoint_temperature": "2m dewpoint temperature",\n'
        '                        "2m_temperature": "2m temperature",\n'
        '                        "skin_temperature": "Skin temperature",\n'
        '                        "soil_temperature_level_1": "Soil temperature level '
        '1",\n'
        '                        "soil_temperature_level_2": "Soil temperature level '
        '2",\n'
        '                        "soil_temperature_level_3": "Soil temperature level '
        '3",\n'
        '                        "soil_temperature_level_4": "Soil temperature level '
        '4"\n'
        "                    },\n"
        '                    "values": [\n'
        '                        "2m_dewpoint_temperature",\n'
        '                        "2m_temperature",\n'
        '                        "skin_temperature",\n'
        '                        "soil_temperature_level_1",\n'
        '                        "soil_temperature_level_2",\n'
        '                        "soil_temperature_level_3",\n'
        '                        "soil_temperature_level_4"\n'
        "                    ]\n"
        "                },\n"
        "                {\n"
        '                    "columns": 2,\n'
        '                    "label": "Lakes",\n'
        '                    "labels": {\n'
        '                        "lake_bottom_temperature": "Lake bottom temperature",\n'
        '                        "lake_ice_depth": "Lake ice depth",\n'
        '                        "lake_ice_temperature": "Lake ice temperature",\n'
        '                        "lake_mix_layer_depth": "Lake mix-layer depth",\n'
        '                        "lake_mix_layer_temperature": "Lake mix-layer '
        'temperature",\n'
        '                        "lake_shape_factor": "Lake shape factor",\n'
        '                        "lake_total_layer_temperature": "Lake total layer '
        'temperature"\n'
        "                    },\n"
        '                    "values": [\n'
        '                        "lake_bottom_temperature",\n'
        '                        "lake_ice_depth",\n'
        '                        "lake_ice_temperature",\n'
        '                        "lake_mix_layer_depth",\n'
        '                        "lake_mix_layer_temperature",\n'
        '                        "lake_shape_factor",\n'
        '                        "lake_total_layer_temperature"\n'
        "                    ]\n"
        "                },\n"
        "                {\n"
        '                    "columns": 2,\n'
        '                    "label": "Snow",\n'
        '                    "labels": {\n'
        '                        "snow_albedo": "Snow albedo",\n'
        '                        "snow_cover": "Snow cover",\n'
        '                        "snow_density": "Snow density",\n'
        '                        "snow_depth": "Snow depth",\n'
        '                        "snow_depth_water_equivalent": "Snow depth water '
        'equivalent",\n'
        '                        "snowfall": "Snowfall",\n'
        '                        "snowmelt": "Snowmelt",\n'
        '                        "temperature_of_snow_layer": "Temperature of snow '
        'layer"\n'
        "                    },\n"
        '                    "values": [\n'
        '                        "snow_albedo",\n'
        '                        "snow_cover",\n'
        '                        "snow_density",\n'
        '                        "snow_depth",\n'
        '                        "snow_depth_water_equivalent",\n'
        '                        "snowfall",\n'
        '                        "snowmelt",\n'
        '                        "temperature_of_snow_layer"\n'
        "                    ]\n"
        "                },\n"
        "                {\n"
        '                    "columns": 2,\n'
        '                    "label": "Soil Water",\n'
        '                    "labels": {\n'
        '                        "skin_reservoir_content": "Skin reservoir content",\n'
        '                        "volumetric_soil_water_layer_1": "Volumetric soil '
        'water layer 1",\n'
        '                        "volumetric_soil_water_layer_2": "Volumetric soil '
        'water layer 2",\n'
        '                        "volumetric_soil_water_layer_3": "Volumetric soil '
        'water layer 3",\n'
        '                        "volumetric_soil_water_layer_4": "Volumetric soil '
        'water layer 4"\n'
        "                    },\n"
        '                    "values": [\n'
        '                        "skin_reservoir_content",\n'
        '                        "volumetric_soil_water_layer_1",\n'
        '                        "volumetric_soil_water_layer_2",\n'
        '                        "volumetric_soil_water_layer_3",\n'
        '                        "volumetric_soil_water_layer_4"\n'
        "                    ]\n"
        "                },\n"
        "                {\n"
        '                    "columns": 2,\n'
        '                    "label": "Radiation and Heat",\n'
        '                    "labels": {\n'
        '                        "forecast_albedo": "Forecast albedo",\n'
        '                        "surface_latent_heat_flux": "Surface latent heat '
        'flux",\n'
        '                        "surface_net_solar_radiation": "Surface net solar '
        'radiation",\n'
        '                        "surface_net_thermal_radiation": "Surface net thermal '
        'radiation",\n'
        '                        "surface_sensible_heat_flux": "Surface sensible heat '
        'flux",\n'
        '                        "surface_solar_radiation_downwards": "Surface solar '
        'radiation downwards",\n'
        '                        "surface_thermal_radiation_downwards": "Surface '
        'thermal radiation downwards"\n'
        "                    },\n"
        '                    "values": [\n'
        '                        "forecast_albedo",\n'
        '                        "surface_latent_heat_flux",\n'
        '                        "surface_net_solar_radiation",\n'
        '                        "surface_net_thermal_radiation",\n'
        '                        "surface_sensible_heat_flux",\n'
        '                        "surface_solar_radiation_downwards",\n'
        '                        "surface_thermal_radiation_downwards"\n'
        "                    ]\n"
        "                },\n"
        "                {\n"
        '                    "columns": 2,\n'
        '                    "label": "Evaporation and Runoff",\n'
        '                    "labels": {\n'
        '                        "evaporation_from_bare_soil": "Evaporation from bare '
        'soil",\n'
        "                        "
        '"evaporation_from_open_water_surfaces_excluding_oceans": "Evaporation from '
        'open water surfaces excluding oceans",\n'
        '                        "evaporation_from_the_top_of_canopy": "Evaporation '
        'from the top of canopy",\n'
        '                        "evaporation_from_vegetation_transpiration": '
        '"Evaporation from vegetation transpiration",\n'
        '                        "potential_evaporation": "Potential evaporation",\n'
        '                        "runoff": "Runoff",\n'
        '                        "snow_evaporation": "Snow evaporation",\n'
        '                        "sub_surface_runoff": "Sub-surface runoff",\n'
        '                        "surface_runoff": "Surface runoff",\n'
        '                        "total_evaporation": "Total evaporation"\n'
        "                    },\n"
        '                    "values": [\n'
        '                        "evaporation_from_bare_soil",\n'
        "                        "
        '"evaporation_from_open_water_surfaces_excluding_oceans",\n'
        '                        "evaporation_from_the_top_of_canopy",\n'
        '                        "evaporation_from_vegetation_transpiration",\n'
        '                        "potential_evaporation",\n'
        '                        "runoff",\n'
        '                        "snow_evaporation",\n'
        '                        "sub_surface_runoff",\n'
        '                        "surface_runoff",\n'
        '                        "total_evaporation"\n'
        "                    ]\n"
        "                },\n"
        "                {\n"
        '                    "columns": 2,\n'
        '                    "label": "Wind, Pressure and Precipitation",\n'
        '                    "labels": {\n'
        '                        "10m_u_component_of_wind": "10m u-component of wind",\n'
        '                        "10m_v_component_of_wind": "10m v-component of wind",\n'
        '                        "surface_pressure": "Surface pressure",\n'
        '                        "total_precipitation": "Total precipitation"\n'
        "                    },\n"
        '                    "values": [\n'
        '                        "10m_u_component_of_wind",\n'
        '                        "10m_v_component_of_wind",\n'
        '                        "surface_pressure",\n'
        '                        "total_precipitation"\n'
        "                    ]\n"
        "                },\n"
        "                {\n"
        '                    "columns": 2,\n'
        '                    "label": "Vegetation",\n'
        '                    "labels": {\n'
        '                        "leaf_area_index_high_vegetation": "Leaf area index, '
        'high vegetation",\n'
        '                        "leaf_area_index_low_vegetation": "Leaf area index, '
        'low vegetation"\n'
        "                    },\n"
        '                    "values": [\n'
        '                        "leaf_area_index_high_vegetation",\n'
        '                        "leaf_area_index_low_vegetation"\n'
        "                    ]\n"
        "                },\n"
        "                {\n"
        '                    "columns": 2,\n'
        '                    "label": "Blacklisted",\n'
        '                    "labels": {},\n'
        '                    "values": []\n'
        "                }\n"
        "            ],\n"
        '            "id": 1\n'
        "        },\n"
        '        "help": "Please, consult the product user guide in the documentation '
        'section for more information on these variables.",\n'
        '        "label": "Variable",\n'
        '        "name": "variable",\n'
        '        "required": true,\n'
        '        "type": "StringListArrayWidget"\n'
        "    },\n"
        "    {\n"
        '        "css": "todo",\n'
        '        "details": {\n'
        '            "columns": 8,\n'
        '            "id": 2,\n'
        '            "labels": {\n'
        '                "1950": "1950",\n'
        '                "1951": "1951",\n'
        '                "1952": "1952",\n'
        '                "1953": "1953",\n'
        '                "1954": "1954",\n'
        '                "1955": "1955",\n'
        '                "1956": "1956",\n'
        '                "1957": "1957",\n'
        '                "1958": "1958",\n'
        '                "1959": "1959",\n'
        '                "1960": "1960",\n'
        '                "1961": "1961",\n'
        '                "1962": "1962",\n'
        '                "1963": "1963",\n'
        '                "1964": "1964",\n'
        '                "1965": "1965",\n'
        '                "1966": "1966",\n'
        '                "1967": "1967",\n'
        '                "1968": "1968",\n'
        '                "1969": "1969",\n'
        '                "1970": "1970",\n'
        '                "1971": "1971",\n'
        '                "1972": "1972",\n'
        '                "1973": "1973",\n'
        '                "1974": "1974",\n'
        '                "1975": "1975",\n'
        '                "1976": "1976",\n'
        '                "1977": "1977",\n'
        '                "1978": "1978",\n'
        '                "1979": "1979",\n'
        '                "1980": "1980",\n'
        '                "1981": "1981",\n'
        '                "1982": "1982",\n'
        '                "1983": "1983",\n'
        '                "1984": "1984",\n'
        '                "1985": "1985",\n'
        '                "1986": "1986",\n'
        '                "1987": "1987",\n'
        '                "1988": "1988",\n'
        '                "1989": "1989",\n'
        '                "1990": "1990",\n'
        '                "1991": "1991",\n'
        '                "1992": "1992",\n'
        '                "1993": "1993",\n'
        '                "1994": "1994",\n'
        '                "1995": "1995",\n'
        '                "1996": "1996",\n'
        '                "1997": "1997",\n'
        '                "1998": "1998",\n'
        '                "1999": "1999",\n'
        '                "2000": "2000",\n'
        '                "2001": "2001",\n'
        '                "2002": "2002",\n'
        '                "2003": "2003",\n'
        '                "2004": "2004",\n'
        '                "2005": "2005",\n'
        '                "2006": "2006",\n'
        '                "2007": "2007",\n'
        '                "2008": "2008",\n'
        '                "2009": "2009",\n'
        '                "2010": "2010",\n'
        '                "2011": "2011",\n'
        '                "2012": "2012",\n'
        '                "2013": "2013",\n'
        '                "2014": "2014",\n'
        '                "2015": "2015",\n'
        '                "2016": "2016",\n'
        '                "2017": "2017",\n'
        '                "2018": "2018",\n'
        '                "2019": "2019",\n'
        '                "2020": "2020",\n'
        '                "2021": "2021",\n'
        '                "2022": "2022"\n'
        "            },\n"
        '            "values": [\n'
        '                "1950",\n'
        '                "1951",\n'
        '                "1952",\n'
        '                "1953",\n'
        '                "1954",\n'
        '                "1955",\n'
        '                "1956",\n'
        '                "1957",\n'
        '                "1958",\n'
        '                "1959",\n'
        '                "1960",\n'
        '                "1961",\n'
        '                "1962",\n'
        '                "1963",\n'
        '                "1964",\n'
        '                "1965",\n'
        '                "1966",\n'
        '                "1967",\n'
        '                "1968",\n'
        '                "1969",\n'
        '                "1970",\n'
        '                "1971",\n'
        '                "1972",\n'
        '                "1973",\n'
        '                "1974",\n'
        '                "1975",\n'
        '                "1976",\n'
        '                "1977",\n'
        '                "1978",\n'
        '                "1979",\n'
        '                "1980",\n'
        '                "1981",\n'
        '                "1982",\n'
        '                "1983",\n'
        '                "1984",\n'
        '                "1985",\n'
        '                "1986",\n'
        '                "1987",\n'
        '                "1988",\n'
        '                "1989",\n'
        '                "1990",\n'
        '                "1991",\n'
        '                "1992",\n'
        '                "1993",\n'
        '                "1994",\n'
        '                "1995",\n'
        '                "1996",\n'
        '                "1997",\n'
        '                "1998",\n'
        '                "1999",\n'
        '                "2000",\n'
        '                "2001",\n'
        '                "2002",\n'
        '                "2003",\n'
        '                "2004",\n'
        '                "2005",\n'
        '                "2006",\n'
        '                "2007",\n'
        '                "2008",\n'
        '                "2009",\n'
        '                "2010",\n'
        '                "2011",\n'
        '                "2012",\n'
        '                "2013",\n'
        '                "2014",\n'
        '                "2015",\n'
        '                "2016",\n'
        '                "2017",\n'
        '                "2018",\n'
        '                "2019",\n'
        '                "2020",\n'
        '                "2021",\n'
        '                "2022"\n'
        "            ]\n"
        "        },\n"
        '        "help": null,\n'
        '        "label": "Year",\n'
        '        "name": "year",\n'
        '        "required": true,\n'
        '        "type": "StringListWidget"\n'
        "    },\n"
        "    {\n"
        '        "css": "todo",\n'
        '        "details": {\n'
        '            "columns": 6,\n'
        '            "id": 3,\n'
        '            "labels": {\n'
        '                "01": "January",\n'
        '                "02": "February",\n'
        '                "03": "March",\n'
        '                "04": "April",\n'
        '                "05": "May",\n'
        '                "06": "June",\n'
        '                "07": "July",\n'
        '                "08": "August",\n'
        '                "09": "September",\n'
        '                "10": "October",\n'
        '                "11": "November",\n'
        '                "12": "December"\n'
        "            },\n"
        '            "values": [\n'
        '                "01",\n'
        '                "02",\n'
        '                "03",\n'
        '                "04",\n'
        '                "05",\n'
        '                "06",\n'
        '                "07",\n'
        '                "08",\n'
        '                "09",\n'
        '                "10",\n'
        '                "11",\n'
        '                "12"\n'
        "            ]\n"
        "        },\n"
        '        "help": null,\n'
        '        "label": "Month",\n'
        '        "name": "month",\n'
        '        "required": true,\n'
        '        "type": "StringListWidget"\n'
        "    },\n"
        "    {\n"
        '        "css": "todo",\n'
        '        "details": {\n'
        '            "columns": 6,\n'
        '            "id": 4,\n'
        '            "labels": {\n'
        '                "00:00": "00:00",\n'
        '                "01:00": "01:00",\n'
        '                "02:00": "02:00",\n'
        '                "03:00": "03:00",\n'
        '                "04:00": "04:00",\n'
        '                "05:00": "05:00",\n'
        '                "06:00": "06:00",\n'
        '                "07:00": "07:00",\n'
        '                "08:00": "08:00",\n'
        '                "09:00": "09:00",\n'
        '                "10:00": "10:00",\n'
        '                "11:00": "11:00",\n'
        '                "12:00": "12:00",\n'
        '                "13:00": "13:00",\n'
        '                "14:00": "14:00",\n'
        '                "15:00": "15:00",\n'
        '                "16:00": "16:00",\n'
        '                "17:00": "17:00",\n'
        '                "18:00": "18:00",\n'
        '                "19:00": "19:00",\n'
        '                "20:00": "20:00",\n'
        '                "21:00": "21:00",\n'
        '                "22:00": "22:00",\n'
        '                "23:00": "23:00"\n'
        "            },\n"
        '            "values": [\n'
        '                "00:00",\n'
        '                "01:00",\n'
        '                "02:00",\n'
        '                "03:00",\n'
        '                "04:00",\n'
        '                "05:00",\n'
        '                "06:00",\n'
        '                "07:00",\n'
        '                "08:00",\n'
        '                "09:00",\n'
        '                "10:00",\n'
        '                "11:00",\n'
        '                "12:00",\n'
        '                "13:00",\n'
        '                "14:00",\n'
        '                "15:00",\n'
        '                "16:00",\n'
        '                "17:00",\n'
        '                "18:00",\n'
        '                "19:00",\n'
        '                "20:00",\n'
        '                "21:00",\n'
        '                "22:00",\n'
        '                "23:00"\n'
        "            ]\n"
        "        },\n"
        '        "help": "UTC time standard. UTC stands for Universal Time Coordinated '
        'as well as for Coordinated Universal Time.",\n'
        '        "label": "Time",\n'
        '        "name": "time",\n'
        '        "required": true,\n'
        '        "type": "StringListWidget"\n'
        "    },\n"
        "    {\n"
        '        "css": "variable",\n'
        '        "details": {\n'
        '            "id": 5\n'
        "        },\n"
        '        "help": "Select one widget from the choice below",\n'
        '        "label": "Geographical area",\n'
        '        "name": "area_group",\n'
        '        "required": true,\n'
        '        "type": "ExclusiveFrameWidget",\n'
        '        "widgets": [\n'
        '            "global",\n'
        '            "area"\n'
        "        ]\n"
        "    },\n"
        "    {\n"
        '        "details": {\n'
        '            "accordion": false,\n'
        '            "id": 6,\n'
        '            "information": "With this option selected the entire available '
        'area will be provided"\n'
        "        },\n"
        '        "label": "Whole available region",\n'
        '        "name": "global",\n'
        '        "required": true,\n'
        '        "type": "LabelWidget"\n'
        "    },\n"
        "    {\n"
        '        "details": {\n'
        '            "accordion": true,\n'
        '            "default": [\n'
        "                90,\n"
        "                -180,\n"
        "                -90,\n"
        "                180\n"
        "            ],\n"
        '            "extentlabels": [\n'
        '                "North",\n'
        '                "West",\n'
        '                "South",\n'
        '                "East"\n'
        "            ],\n"
        '            "fullheight": true,\n'
        '            "id": 7,\n'
        '            "precision": 2,\n'
        '            "range": {\n'
        '                "e": 180,\n'
        '                "n": 90,\n'
        '                "s": -90,\n'
        '                "w": -180\n'
        "            },\n"
        '            "withmap": false,\n'
        '            "wrapping": true\n'
        "        },\n"
        '        "help": "Select a sub-region of the available area by providing its '
        'limits on latitude and longitude",\n'
        '        "label": "Sub-region extraction",\n'
        '        "name": "area",\n'
        '        "type": "GeographicExtentMapWidget"\n'
        "    },\n"
        "    {\n"
        '        "css": "todo",\n'
        '        "details": {\n'
        '            "columns": 2,\n'
        '            "default": [\n'
        '                "grib"\n'
        "            ],\n"
        '            "id": 8,\n'
        '            "labels": {\n'
        '                "grib": "GRIB",\n'
        '                "netcdf": "NetCDF (experimental)"\n'
        "            },\n"
        '            "values": [\n'
        '                "grib",\n'
        '                "netcdf"\n'
        "            ]\n"
        "        },\n"
        '        "help": null,\n'
        '        "label": "Format",\n'
        '        "name": "format",\n'
        '        "required": true,\n'
        '        "type": "StringChoiceWidget"\n'
        "    }\n"
        "]\n",
        "keywords": [
            "Product type: Reanalysis",
            "Spatial coverage: Global",
            "Temporal coverage: Past",
            "Variable domain: Land (hydrology)",
            "Variable domain: Land (physics)",
            "Variable domain: Land (biosphere)",
            "Provider: Copernicus C3S",
        ],
        "licence_ids": ["licence-to-use-copernicus-products"],
        "previewimage": "overview.png",
        "publication_date": date(2019, 6, 23),
        "resource_id": "reanalysis-era5-land-monthly-means",
        "resource_update": date(2022, 3, 2),
        "title": "ERA5-Land monthly averaged data from 1950 to present",
        "type": "dataset",
        "variables": '{"10m u-component of wind": {"description": "Eastward component of the '
        "10m wind. It is the horizontal speed of air moving towards the east, at a "
        "height of ten metres above the surface of the Earth, in metres per "
        "second. Care should be taken when comparing this variable with "
        "observations, because wind observations vary on small space and time "
        "scales and are affected by the local terrain, vegetation and buildings "
        "that are represented only on average in the ECMWF Integrated Forecasting "
        "System. This variable can be combined with the V component of 10m wind to "
        'give the speed and direction of the horizontal 10m wind.", "units": "m '
        's^-1"}, "10m v-component of wind": {"description": "Northward component '
        "of the 10m wind. It is the horizontal speed of air moving towards the "
        "north, at a height of ten metres above the surface of the Earth, in "
        "metres per second. Care should be taken when comparing this variable with "
        "observations, because wind observations vary on small space and time "
        "scales and are affected by the local terrain, vegetation and buildings "
        "that are represented only on average in the ECMWF Integrated Forecasting "
        "System. This variable can be combined with the U component of 10m wind to "
        'give the speed and direction of the horizontal 10m wind.", "units": "m '
        's^-1"}, "2m dewpoint temperature": {"description": "Temperature to which '
        "the air, at 2 metres above the surface of the Earth, would have to be "
        "cooled for saturation to occur.It is a measure of the humidity of the "
        "air. Combined with temperature and pressure, it can be used to calculate "
        "the relative humidity. 2m dew point temperature is calculated by "
        "interpolating between the lowest model level and the Earth's surface, "
        "taking account of the atmospheric conditions. Temperature measured in "
        "kelvin can be converted to degrees Celsius (\\u00b0C) by subtracting "
        '273.15.", "units": "K"}, "2m temperature": {"description": "Temperature '
        "of air at 2m above the surface of land, sea or in-land waters. 2m "
        "temperature is calculated by interpolating between the lowest model level "
        "and the Earth's surface, taking account of the atmospheric conditions. "
        "Temperature measured in kelvin can be converted to degrees Celsius "
        '(\\u00b0C) by subtracting 273.15.", "units": "K"}, "Evaporation from bare '
        'soil": {"description": "The amount of evaporation from bare soil at the '
        "top of the land surface. This variable is accumulated from the beginning "
        'of the forecast time to the end of the forecast step.", "units": "m of '
        'water equivalent"}, "Evaporation from open water surfaces excluding '
        'oceans": {"description": "Amount of evaporation from surface water '
        "storage like lakes and inundated areas but excluding oceans. This "
        "variable is accumulated from the beginning of the forecast time to the "
        'end of the forecast step.", "units": "m of water equivalent"}, '
        '"Evaporation from the top of canopy": {"description": "The amount of '
        "evaporation from the canopy interception reservoir at the top of the "
        "canopy. This variable is accumulated from the beginning of the forecast "
        'time to the end of the forecast step.", "units": "m of water '
        'equivalent"}, "Evaporation from vegetation transpiration": '
        '{"description": "Amount of evaporation from vegetation transpiration. '
        "This has the same meaning as root extraction i.e. the amount of water "
        "extracted from the different soil layers. This variable is accumulated "
        "from the beginning of the forecast time to the end of the forecast "
        'step.", "units": "m of water equivalent"}, "Forecast albedo": '
        '{"description": "Is a measure of the reflectivity of the Earth\'s '
        "surface. It is the fraction of solar (shortwave) radiation reflected by "
        "Earth's surface, across the solar spectrum, for both direct and diffuse "
        "radiation. Values are between 0 and 1. Typically, snow and ice have high "
        "reflectivity with albedo values of 0.8 and above, land has intermediate "
        "values between about 0.1 and 0.4 and the ocean has low values of 0.1 or "
        "less. Radiation from the Sun (solar, or shortwave, radiation) is partly "
        "reflected back to space by clouds and particles in the atmosphere "
        "(aerosols) and some of it is absorbed. The rest is incident on the "
        "Earth's surface, where some of it is reflected. The portion that is "
        "reflected by the Earth's surface depends on the albedo. In the ECMWF "
        "Integrated Forecasting System (IFS), a climatological background albedo "
        "(observed values averaged over a period of several years) is used, "
        "modified by the model over water, ice and snow. Albedo is often shown as "
        'a percentage (%).", "units": "dimensionless"}, "Lake bottom temperature": '
        '{"description": "Temperature of water at the bottom of inland water '
        "bodies (lakes, reservoirs, rivers) and coastal waters. ECMWF implemented "
        "a lake model in May 2015 to represent the water temperature and lake ice "
        "of all the world\\u2019s major inland water bodies in the Integrated "
        "Forecasting System. The model keeps lake depth and surface area (or "
        'fractional cover) constant in time.", "units": "K"}, "Lake ice depth": '
        '{"description": "The thickness of ice on inland water bodies (lakes, '
        "reservoirs and rivers) and coastal waters. The ECMWF Integrated "
        "Forecasting System (IFS) represents the formation and melting of ice on "
        "inland water bodies (lakes, reservoirs and rivers) and coastal water. A "
        "single ice layer is represented. This parameter is the thickness of that "
        'ice layer.", "units": "m"}, "Lake ice temperature": {"description": "The '
        "temperature of the uppermost surface of ice on inland water bodies "
        "(lakes, reservoirs, rivers) and coastal waters. The ECMWF Integrated "
        "Forecasting System represents the formation and melting of ice on lakes. "
        "A single ice layer is represented. The temperature measured in kelvin can "
        'be converted to degrees Celsius (\\u00b0C) by subtracting 273.15.", '
        '"units": "K"}, "Lake mix-layer depth": {"description": "The thickness of '
        "the upper most layer of an inland water body (lake, reservoirs, and "
        "rivers) or coastal waters that is well mixed and has a near constant "
        "temperature with depth (uniform distribution of temperature). The ECMWF "
        "Integrated Forecasting System represents inland water bodies with two "
        "layers in the vertical, the mixed layer above and the thermocline below. "
        "Thermoclines upper boundary is located at the mixed layer bottom, and the "
        "lower boundary at the lake bottom. Mixing within the mixed layer can "
        "occur when the density of the surface (and near-surface) water is greater "
        "than that of the water below. Mixing can also occur through the action of "
        'wind on the surface of the lake.", "units": "m"}, "Lake mix-layer '
        'temperature": {"description": "The temperature of the upper most layer of '
        "inland water bodies (lakes, reservoirs and rivers) or coastal waters) "
        "that is well mixed. The ECMWF Integrated Forecasting System represents "
        "inland water bodies with two layers in the vertical, the mixed layer "
        "above and the thermocline below. Thermoclines upper boundary is located "
        "at the mixed layer bottom, and the lower boundary at the lake bottom. "
        "Mixing within the mixed layer can occur when the density of the surface "
        "(and near-surface) water is greater than that of the water below. Mixing "
        "can also occur through the action of wind on the surface of the lake. "
        "Temperature measured in kelvin can be converted to degrees Celsius "
        '(\\u00b0C) by subtracting 273.15.", "units": "K"}, "Lake shape factor": '
        '{"description": "This parameter describes the way that temperature '
        "changes with depth in the thermocline layer of inland water bodies "
        "(lakes, reservoirs and rivers) and coastal waters. It is used to "
        "calculate the lake bottom temperature and other lake-related parameters. "
        "The ECMWF Integrated Forecasting System represents inland and coastal "
        "water bodies with two layers in the vertical, the mixed layer above and "
        'the thermocline below where temperature changes with depth.", "units": '
        '"dimensionless"}, "Lake total layer temperature": {"description": "The '
        "mean temperature of total water column in inland water bodies (lakes, "
        "reservoirs and rivers) and coastal waters. The ECMWF Integrated "
        "Forecasting System represents inland water bodies with two layers in the "
        "vertical, the mixed layer above and the thermocline below where "
        "temperature changes with depth. This parameter is the mean over the two "
        "layers. Temperature measured in kelvin can be converted to degrees "
        'Celsius (\\u00b0C) by subtracting 273.15.", "units": "K"}, "Leaf area '
        'index, high vegetation": {"description": "One-half of the total green '
        "leaf area per unit horizontal ground surface area for high vegetation "
        'type.", "units": "m^2 m^-2"}, "Leaf area index, low vegetation": '
        '{"description": "One-half of the total green leaf area per unit '
        'horizontal ground surface area for low vegetation type.", "units": "m^2 '
        'm^-2"}, "Potential evaporation": {"description": "Potential evaporation '
        "(pev) in the current ECMWF model is computed, by making a second call to "
        "the surface energy balance routine with the vegetation variables set to "
        '\\"crops/mixed farming\\" and assuming no stress from soil moisture. In '
        "other words, evaporation is computed for agricultural land as if it is "
        "well watered and assuming that the atmosphere is not affected by this "
        "artificial surface condition. The latter may not always be realistic. "
        "Although pev is meant to provide an estimate of irrigation requirements, "
        "the method can give unrealistic results in arid conditions due to too "
        "strong evaporation forced by dry air. Note that in ERA5-Land pev is "
        "computed as an open water evaporation (Pan evaporation) and assuming that "
        "the atmosphere is not affected by this artificial surface condition. The "
        "latter is different from the way pev is computed in ERA5. This variable "
        "is accumulated from the beginning of the forecast time to the end of the "
        'forecast step.", "units": "m"}, "Runoff": {"description": "Some water '
        "from rainfall, melting snow, or deep in the soil, stays stored in the "
        "soil. Otherwise, the water drains away, either over the surface (surface "
        "runoff), or under the ground (sub-surface runoff) and the sum of these "
        "two is simply called 'runoff'. This variable is the total amount of water "
        "accumulated from the beginning of the forecast time to the end of the "
        "forecast step. The units of runoff are depth in metres. This is the depth "
        "the water would have if it were spread evenly over the grid box. Care "
        "should be taken when comparing model variables with observations, because "
        "observations are often local to a particular point rather than averaged "
        "over a grid square area.  Observations are also often taken in different "
        "units, such as mm/day, rather than the accumulated metres produced here. "
        "Runoff is a measure of the availability of water in the soil, and can, "
        "for example, be used as an indicator of drought or flood. More "
        "information about how runoff is calculated is given in the IFS Physical "
        'Processes documentation.", "units": "m"}, "Skin reservoir content": '
        '{"description": "Amount of water in the vegetation canopy and/or in a '
        "thin layer on the soil. It represents the amount of rain intercepted by "
        "foliage, and water from dew. The maximum amount of 'skin reservoir "
        "content' a grid box can hold depends on the type of vegetation, and may "
        'be zero.  Water leaves the \'skin reservoir\' by evaporation.", "units": '
        '"m of water equivalent"}, "Skin temperature": {"description": '
        '"Temperature of the surface of the Earth. The skin temperature is the '
        "theoretical temperature that is required to satisfy the surface energy "
        "balance. It represents the temperature of the uppermost surface layer, "
        "which has no heat capacity and so can respond instantaneously to changes "
        "in surface fluxes. Skin temperature is calculated differently over land "
        "and sea. Temperature measured in kelvin can be converted to degrees "
        'Celsius (\\u00b0C) by subtracting 273.15.", "units": "K"}, "Snow albedo": '
        '{"description": "It is defined as the fraction of solar (shortwave) '
        "radiation reflected by the snow, across the solar spectrum, for both "
        "direct and diffuse radiation. It is a measure of the reflectivity of the "
        "snow covered grid cells. Values vary between 0 and 1. Typically, snow and "
        'ice have high reflectivity with albedo values of 0.8 and above.", '
        '"units": "dimensionless"}, "Snow cover": {"description": "It represents '
        "the fraction (0-1) of the cell / grid-box occupied by snow (similar to "
        'the cloud cover fields of ERA5).", "units": "%"}, "Snow density": '
        '{"description": "Mass of snow per cubic metre in the snow layer. The '
        "ECMWF Integrated Forecast System (IFS) model represents snow as a single "
        "additional layer over the uppermost soil level. The snow may cover all or "
        'part of the grid box.", "units": "kg m^-3"}, "Snow depth": '
        '{"description": "Instantaneous grib-box average of the snow thickness on '
        'the ground (excluding snow on canopy).", "units": "m"}, "Snow depth water '
        'equivalent": {"description": "Depth of snow from the snow-covered area of '
        "a grid box. Its units are metres of water equivalent, so it is the depth "
        "the water would have if the snow melted and was spread evenly over the "
        "whole grid box. The ECMWF Integrated Forecast System represents snow as a "
        "single additional layer over the uppermost soil level. The snow may cover "
        'all or part of the grid box.", "units": "m of water equivalent"}, "Snow '
        'evaporation": {"description": "Evaporation from snow averaged over the '
        "grid box (to find flux over snow, divide by snow fraction). This variable "
        "is accumulated from the beginning of the forecast time to the end of the "
        'forecast step.", "units": "m of water equivalent"}, "Snowfall": '
        '{"description": "Accumulated total snow that has fallen to the Earth\'s '
        "surface. It consists of snow due to the large-scale atmospheric flow "
        "(horizontal scales greater than around a few hundred metres) and "
        "convection where smaller scale areas (around 5km to a few hundred "
        "kilometres) of warm air rise. If snow has melted during the period over "
        "which this variable was accumulated, then it will be higher than the snow "
        "depth. This variable is the total amount of water accumulated from the "
        "beginning of the forecast time to the end of the forecast step. The units "
        "given measure the depth the water would have if the snow melted and was "
        "spread evenly over the grid box. Care should be taken when comparing "
        "model variables with observations, because observations are often local "
        "to a particular point in space and time, rather than representing "
        'averages over a model grid box and model time step.", "units": "m of '
        'water equivalent"}, "Snowmelt": {"description": "Melting of snow averaged '
        "over the grid box (to find melt over snow, divide by snow fraction). This "
        "variable is accumulated from the beginning of the forecast time to the "
        'end of the forecast step.", "units": "m of water equivalent"}, "Soil '
        'temperature level 1": {"description": "Temperature of the soil in layer 1 '
        "(0 - 7 cm) of the ECMWF Integrated Forecasting System. The surface is at "
        "0 cm. Soil temperature is set at the middle of each layer, and heat "
        "transfer is calculated at the interfaces between them. It is assumed that "
        "there is no heat transfer out of the bottom of the lowest layer. "
        "Temperature measured in kelvin can be converted to degrees Celsius "
        '(\\u00b0C) by subtracting 273.15.", "units": "K"}, "Soil temperature '
        'level 2": {"description": "Temperature of the soil in layer 2 (7 -28cm) '
        'of the ECMWF Integrated Forecasting System.", "units": "K"}, "Soil '
        'temperature level 3": {"description": "Temperature of the soil in layer 3 '
        '(28-100cm) of the ECMWF Integrated Forecasting System.", "units": "K"}, '
        '"Soil temperature level 4": {"description": "Temperature of the soil in '
        'layer 4 (100-289 cm) of the ECMWF Integrated Forecasting System.", '
        '"units": "K"}, "Sub-surface runoff": {"description": "Some water from '
        "rainfall, melting snow, or deep in the soil, stays stored in the soil. "
        "Otherwise, the water drains away, either over the surface (surface "
        "runoff), or under the ground (sub-surface runoff) and the sum of these "
        "two is simply called 'runoff'. This variable is accumulated from the "
        "beginning of the forecast time to the end of the forecast step. The units "
        "of runoff are depth in metres. This is the depth the water would have if "
        "it were spread evenly over the grid box. Care should be taken when "
        "comparing model variables with observations, because observations are "
        "often local to a particular point rather than averaged over a grid square "
        "area.  Observations are also often taken in different units, such as "
        "mm/day, rather than the accumulated metres produced here. Runoff is a "
        "measure of the availability of water in the soil, and can, for example, "
        "be used as an indicator of drought or flood. More information about how "
        "runoff is calculated is given in the IFS Physical Processes "
        'documentation.", "units": "m"}, "Surface latent heat flux": '
        '{"description": "Exchange of latent heat with the surface through '
        "turbulent diffusion. This variables is accumulated from the beginning of "
        "the forecast time to the end of the forecast step. By model convention, "
        'downward fluxes are positive.", "units": "J m^-2"}, "Surface net solar '
        'radiation": {"description": "Amount of solar radiation (also known as '
        "shortwave radiation) reaching the surface of the Earth (both direct and "
        "diffuse) minus the amount reflected by the Earth's surface (which is "
        "governed by the albedo).Radiation from the Sun (solar, or shortwave, "
        "radiation) is partly reflected back to space by clouds and particles in "
        "the atmosphere (aerosols) and some of it is absorbed. The rest is "
        "incident on the Earth's surface, where some of it is reflected. The "
        "difference between downward and reflected solar radiation is the surface "
        "net solar radiation. This variable is accumulated from the beginning of "
        "the forecast time to the end of the forecast step. The units are joules "
        "per square metre (J m^-2). To convert to watts per square metre (W m^-2), "
        "the accumulated values should be divided by the accumulation period "
        "expressed in seconds. The ECMWF convention for vertical fluxes is "
        'positive downwards.", "units": "J m^-2"}, "Surface net thermal '
        'radiation": {"description": "Net thermal radiation at the surface. '
        "Accumulated field from the beginning of the forecast time to the end of "
        'the forecast step. By model convention downward fluxes are positive.", '
        '"units": "J m^-2"}, "Surface pressure": {"description": "Pressure (force '
        "per unit area) of the atmosphere on the surface of land, sea and in-land "
        "water. It is a measure of the weight of all the air in a column "
        "vertically above the area of the Earth's surface represented at a fixed "
        "point. Surface pressure is often used in combination with temperature to "
        "calculate air density. The strong variation of pressure with altitude "
        "makes it difficult to see the low and high pressure systems over "
        "mountainous areas, so mean sea level pressure, rather than surface "
        "pressure, is normally used for this purpose. The units of this variable "
        "are Pascals (Pa). Surface pressure is often measured in hPa and sometimes "
        'is presented in the old units of millibars, mb (1 hPa = 1 mb = 100 Pa).", '
        '"units": "Pa"}, "Surface runoff": {"description": "Some water from '
        "rainfall, melting snow, or deep in the soil, stays stored in the soil. "
        "Otherwise, the water drains away, either over the surface (surface "
        "runoff), or under the ground (sub-surface runoff) and the sum of these "
        "two is simply called 'runoff'. This variable is the total amount of water "
        "accumulated from the beginning of the forecast time to the end of the "
        "forecast step. The units of runoff are depth in metres. This is the depth "
        "the water would have if it were spread evenly over the grid box. Care "
        "should be taken when comparing model variables with observations, because "
        "observations are often local to a particular point rather than averaged "
        "over a grid square area. Observations are also often taken in different "
        "units, such as mm/day, rather than the accumulated metres produced here. "
        "Runoff is a measure of the availability of water in the soil, and can, "
        "for example, be used as an indicator of drought or flood. More "
        "information about how runoff is calculated is given in the IFS Physical "
        'Processes documentation.", "units": "m"}, "Surface sensible heat flux": '
        '{"description": "Transfer of heat between the Earth\'s surface and the '
        "atmosphere through the effects of turbulent air motion (but excluding any "
        "heat transfer resulting from condensation or evaporation). The magnitude "
        "of the sensible heat flux is governed by the difference in temperature "
        "between the surface and the overlying atmosphere, wind speed and the "
        "surface roughness. For example, cold air overlying a warm surface would "
        "produce a sensible heat flux from the land (or ocean) into the "
        "atmosphere. This is a single level variable and it is accumulated from "
        "the beginning of the forecast time to the end of the forecast step. The "
        "units are joules per square metre (J m^-2). To convert to watts per "
        "square metre (W m^-2), the accumulated values should be divided by the "
        "accumulation period expressed in seconds. The ECMWF convention for "
        'vertical fluxes is positive downwards.", "units": "J m^-2"}, "Surface '
        'solar radiation downwards": {"description": "Amount of solar radiation '
        "(also known as shortwave radiation) reaching the surface of the Earth. "
        "This variable comprises both direct and diffuse solar radiation. "
        "Radiation from the Sun (solar, or shortwave, radiation) is partly "
        "reflected back to space by clouds and particles in the atmosphere "
        "(aerosols) and some of it is absorbed.  The rest is incident on the "
        "Earth's surface (represented by this variable). To a reasonably good "
        "approximation, this variable is the model equivalent of what would be "
        "measured by a pyranometer (an instrument used for measuring solar "
        "radiation) at the surface. However, care should be taken when comparing "
        "model variables with observations, because observations are often local "
        "to a particular point in space and time, rather than representing "
        "averages over a  model grid box and model time step. This variable is "
        "accumulated from the beginning of the forecast time to the end of the "
        "forecast step. The units are joules per square metre (J m^-2). To convert "
        "to watts per square metre (W m^-2), the accumulated values should be "
        "divided by the accumulation period expressed in seconds. The ECMWF "
        'convention for vertical fluxes is positive downwards.", "units": "J '
        'm-2"}, "Surface thermal radiation downwards": {"description": "Amount of '
        "thermal (also known as longwave or terrestrial) radiation emitted by the "
        "atmosphere and clouds that reaches the Earth's surface. The surface of "
        "the Earth emits thermal radiation, some of which is absorbed by the "
        "atmosphere and clouds. The atmosphere and clouds likewise emit thermal "
        "radiation in all directions, some of which reaches the surface "
        "(represented by this variable). This variable is accumulated from the "
        "beginning of the forecast time to the end of the forecast step. The units "
        "are joules per square metre (J m^-2). To convert to watts per square "
        "metre (W m^-2), the accumulated values should be divided by the "
        "accumulation period expressed in seconds. The ECMWF convention for "
        'vertical fluxes is positive downwards.", "units": "J m-2"}, "Temperature '
        'of snow layer": {"description": "This variable gives the temperature of '
        "the snow layer from the ground to the snow-air interface. The ECMWF "
        "Integrated Forecast System (IFS) model represents snow as a single "
        "additional layer over the uppermost soil level. The snow may cover all or "
        "part of the  grid box. Temperature measured in kelvin can be converted to "
        'degrees Celsius (\\u00b0C) by subtracting 273.15.", "units": "K"}, "Total '
        'evaporation": {"description": "Accumulated amount of water that has '
        "evaporated from the Earth's surface, including a simplified "
        "representation of transpiration (from vegetation), into vapour in the air "
        "above. This variable is accumulated from the beginning of the forecast to "
        "the end of the forecast step. The ECMWF Integrated Forecasting System "
        "convention is that downward fluxes are positive. Therefore, negative "
        'values indicate evaporation and positive values indicate condensation.", '
        '"units": "m of water equivalent"}, "Total precipitation": {"description": '
        '"Accumulated liquid and frozen water, including rain and snow, that falls '
        "to the Earth's surface. It is the sum of large-scale precipitation (that "
        "precipitation which is generated by large-scale weather patterns, such as "
        "troughs and cold fronts) and convective precipitation (generated by "
        "convection which occurs when air at lower levels in the atmosphere is "
        "warmer and less dense than the air above, so it rises). Precipitation "
        "variables do not include fog, dew or the precipitation that evaporates in "
        "the atmosphere before it lands at the surface of the Earth. This variable "
        "is accumulated from the beginning of the forecast time to the end of the "
        "forecast step. The units of precipitation are depth in metres. It is the "
        "depth the water would have if it were spread evenly over the grid box. "
        "Care should be taken when comparing model variables with observations, "
        "because observations are often local to a particular point in space and "
        "time, rather than representing averages over a model grid box and  model "
        'time step.", "units": "m"}, "Volumetric soil water layer 1": '
        '{"description": "Volume of water in soil layer 1 (0 - 7 cm) of the ECMWF '
        "Integrated Forecasting System. The surface is at 0 cm. The volumetric "
        "soil water is associated with the soil texture (or classification), soil "
        'depth, and the underlying groundwater level.", "units": "m^3 m^-3"}, '
        '"Volumetric soil water layer 2": {"description": "Volume of water in soil '
        'layer 2 (7 -28 cm) of the ECMWF Integrated Forecasting System.", "units": '
        '"m^3 m^-3"}, "Volumetric soil water layer 3": {"description": "Volume of '
        "water in soil layer 3 (28-100 cm) of the ECMWF Integrated Forecasting "
        'System.", "units": "m^3 m^-3"}, "Volumetric soil water layer 4": '
        '{"description": "Volume of water in soil layer 4 (100-289 cm) of the '
        'ECMWF Integrated Forecasting System.", "units": "m^3 m^-3"}}',
    }
    resource = manager.load_resource_from_folder(resource_folder_path)

    assert resource == expected_resource


def test_store_licences(session_obj: sessionmaker) -> None:
    licences_folder_path = os.path.join(TESTDATA_PATH, "cds-licences")
    licences = manager.load_licences_from_folder(licences_folder_path)
    session = session_obj()

    res = session.query(database.Licence).all()
    assert res == []

    manager.store_licences(session_obj, licences)
    res = session.query(database.Licence).all()
    assert len(res) == len(licences)
    assert object_as_dict(res[0]) == licences[0]

    session.close()


def test_store_dataset(session_obj: sessionmaker) -> None:
    licences_folder_path = os.path.join(TESTDATA_PATH, "cds-licences")
    licences = manager.load_licences_from_folder(licences_folder_path)
    manager.store_licences(session_obj, licences)
    resource_folder_path = os.path.join(
        TESTDATA_PATH, "reanalysis-era5-land-monthly-means"
    )
    resource = manager.load_resource_from_folder(resource_folder_path)
    session = session_obj()
    assert resource["licence_ids"] == [licences[0]["licence_id"]]

    res = session.query(database.Resource).all()
    assert res == []

    manager.store_dataset(session_obj, resource)
    res = session.query(database.Resource).all()
    assert len(res) == 1
    for column, value in object_as_dict(res[0]).items():
        if column not in ["record_update"]:
            assert resource.get(column) == value

    expected_many2many_record = {
        "resource_id": "reanalysis-era5-land-monthly-means",
        "licence_id": "licence-to-use-copernicus-products",
        "revision": 12,
    }
    assert (
        object_as_dict(session.query(database.ResourceLicence).first())
        == expected_many2many_record
    )

    session.close()


# def test_load_test_data(session_obj):
#     licences_folder_path = os.path.join(TESTDATA_PATH, "cds-licences")
#     licences = manager.load_licences_from_folder(licences_folder_path)
#     manager.store_licences(session_obj, licences)
#     datasets = [
#         "reanalysis-era5-land-monthly-means",
#         "reanalysis-era5-pressure-levels",
#     ]
#     session = session_obj()
#     for dataset in datasets:
#         resource_folder_path = os.path.join(TESTDATA_PATH, dataset)
#         resource = manager.load_resource_from_folder(resource_folder_path)
#         manager.store_dataset(session_obj, resource)
#
#     session.close()
