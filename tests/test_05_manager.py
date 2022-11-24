import json
import os.path
from datetime import date
from typing import Any

from sqlalchemy.orm import sessionmaker

from cads_catalogue import DATA_PATH, config, database, manager, object_storage

THIS_PATH = os.path.abspath(os.path.dirname(__file__))
TESTDATA_PATH = os.path.join(THIS_PATH, "data")


def test_recursive_search():
    obj1 = {
        "a": 1,
        "b": [
            {"a": 2, "b": {"a": 3, "b": 4}},
            [1, 2, 3],
            [{}, {"b": 4}, {"a": 4, "b": 4}],
        ],
        "c": {"a": 5, "b": {"a": 6, "b": 4}},
    }
    res1 = manager.recursive_key_search(obj1, key="a")
    assert res1 == [1, 2, 3, 4, 5, 6]
    form_json_path = os.path.join(
        TESTDATA_PATH, "satellite-surface-radiation-budget", "json-config", "form.json"
    )
    with open(form_json_path) as fp:
        form_data = json.load(fp)
    search_results = manager.recursive_key_search(form_data, key="labels")
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


def test_load_metadata_licences() -> None:
    # test data taken from repository "https://git.ecmwf.int/projects/CDS/repos/cds-licences"
    licences_folder_path = os.path.join(TESTDATA_PATH, "cds-licences")
    expected_licences = [
        {
            "download_filename": os.path.join(
                licences_folder_path, "licence-to-use-copernicus-products.pdf"
            ),
            "licence_uid": "licence-to-use-copernicus-products",
            "revision": 12,
            "title": "Licence to use Copernicus Products",
        }
    ]

    licences = manager.load_licences_from_folder(licences_folder_path)

    assert licences == expected_licences


def test_load_resource_for_object_storage() -> None:
    folder_path = os.path.join(TESTDATA_PATH, "reanalysis-era5-land")
    res = manager.load_resource_for_object_storage(folder_path)
    assert res == {
        "constraints": os.path.join(folder_path, "json-config", "constraints.json"),
        "form": os.path.join(folder_path, "json-config", "form.json"),
        "layout": os.path.join(folder_path, "json-config", "layout.json"),
        "mapping": os.path.join(folder_path, "json-config", "mapping.json"),
        "previewimage": os.path.join(
            folder_path, "content", "overview", "overview.png"
        ),
    }


def test_load_variable_id_map() -> None:
    form_json_path = os.path.join(
        TESTDATA_PATH, "reanalysis-era5-land", "json-config", "form.json"
    )
    mapping_json_path = os.path.join(
        TESTDATA_PATH, "reanalysis-era5-land", "json-config", "mapping.json"
    )
    res = manager.load_variable_id_map(form_json_path, mapping_json_path)
    assert res == {
        "10m u-component of wind": "10m_u_component_of_wind",
        "10m v-component of wind": "10m_v_component_of_wind",
        "2m dewpoint temperature": "2m_dewpoint_temperature",
        "2m temperature": "2m_temperature",
        "Evaporation from bare soil": "evaporation_from_bare_soil",
        "Evaporation from open water surfaces excluding oceans": "evaporation_from_"
        "open_water_surfaces_"
        "excluding_oceans",
        "Evaporation from the top of canopy": "evaporation_from_the_top_of_canopy",
        "Evaporation from vegetation transpiration": "evaporation_from_vegetation_transpiration",
        "Forecast albedo": "forecast_albedo",
        "Lake bottom temperature": "lake_bottom_temperature",
        "Lake ice depth": "lake_ice_depth",
        "Lake ice temperature": "lake_ice_temperature",
        "Lake mix-layer depth": "lake_mix_layer_depth",
        "Lake mix-layer temperature": "lake_mix_layer_temperature",
        "Lake shape factor": "lake_shape_factor",
        "Lake total layer temperature": "lake_total_layer_temperature",
        "Leaf area index, high vegetation": "leaf_area_index_high_vegetation",
        "Leaf area index, low vegetation": "leaf_area_index_low_vegetation",
        "Potential evaporation": "potential_evaporation",
        "Runoff": "runoff",
        "Skin reservoir content": "skin_reservoir_content",
        "Skin temperature": "skin_temperature",
        "Snow albedo": "snow_albedo",
        "Snow cover": "snow_cover",
        "Snow density": "snow_density",
        "Snow depth": "snow_depth",
        "Snow depth water equivalent": "snow_depth_water_equivalent",
        "Snow evaporation": "snow_evaporation",
        "Snowfall": "snowfall",
        "Snowmelt": "snowmelt",
        "Soil temperature level 1": "soil_temperature_level_1",
        "Soil temperature level 2": "soil_temperature_level_2",
        "Soil temperature level 3": "soil_temperature_level_3",
        "Soil temperature level 4": "soil_temperature_level_4",
        "Sub-surface runoff": "sub_surface_runoff",
        "Surface latent heat flux": "surface_latent_heat_flux",
        "Surface net solar radiation": "surface_net_solar_radiation",
        "Surface net thermal radiation": "surface_net_thermal_radiation",
        "Surface pressure": "surface_pressure",
        "Surface runoff": "surface_runoff",
        "Surface sensible heat flux": "surface_sensible_heat_flux",
        "Surface solar radiation downwards": "surface_solar_radiation_downwards",
        "Surface thermal radiation downwards": "surface_thermal_radiation_downwards",
        "Temperature of snow layer": "temperature_of_snow_layer",
        "Total evaporation": "total_evaporation",
        "Total precipitation": "total_precipitation",
        "Volumetric soil water layer 1": "volumetric_soil_water_layer_1",
        "Volumetric soil water layer 2": "volumetric_soil_water_layer_2",
        "Volumetric soil water layer 3": "volumetric_soil_water_layer_3",
        "Volumetric soil water layer 4": "volumetric_soil_water_layer_4",
    }


def test_load_resource_from_folder() -> None:
    resource_folder_path = os.path.join(TESTDATA_PATH, "reanalysis-era5-land")
    resource = manager.load_resource_from_folder(resource_folder_path)
    expected_resource = {
        "abstract": "",
        "adaptor": (
            '{\n'
            '  "format_conversion": {\n'
            '    "netcdf_cdm": {\n'
            '      "split_on": [\n'
            '        "origin",\n'
            '        "type",\n'
            '        "dataset"\n'
            '      ],\n'
            '      "system_call": [\n'
            '        "cdscdm-translate",\n'
            '        "-o",\n'
            '        "{{outfile}}",\n'
            '        "--product",\n'
            '        "{{product}}",\n'
            '        "--merge_datasets",\n'
            '        "true",\n'
            '        "{{infile}}"\n'
            '      ]\n'
            '    }\n'
            '  }\n'
            '}'
        ),
        "begin_date": "1982-01-01",
        "constraints": os.path.join(
            resource_folder_path, "json-config", "constraints.json"
        ),
        "contactemail": "https://support.ecmwf.int",
        "description": [
            {"id": "file-format", "label": "File format", "value": "GRIB"},
            {"id": "data-type", "label": "Data type", "value": "Gridded"},
            {
                "id": "projection",
                "label": "Projection",
                "value": "Regular latitude-longitude grid",
            },
            {
                "id": "horizontal-coverage",
                "label": "Horizontal coverage",
                "value": "Global",
            },
            {
                "id": "horizontal-resolution",
                "label": "Horizontal resolution",
                "value": "0.1° x 0.1°; Native resolution is 9 km.",
            },
            {
                "id": "vertical-coverage",
                "label": "Vertical coverage",
                "value": "From 2 m above the surface level, to a soil depth of 289 cm.\n",
            },
            {
                "id": "vertical-resolution",
                "label": "Vertical resolution",
                "value": "4 levels of the ECMWF surface model: Layer 1: 0 "
                "-7cm, Layer 2: 7 -28cm, Layer 3: 28-100cm, Layer "
                "4: 100-289cm\n"
                "Some parameters are defined at 2 m over the "
                "surface.\n",
            },
            {
                "id": "temporal-coverage",
                "label": "Temporal coverage",
                "value": "January 1950 to present",
            },
            {
                "id": "temporal-resolution",
                "label": "Temporal resolution",
                "value": "Hourly",
            },
            {
                "id": "update-frequency",
                "label": "Update frequency",
                "value": "Monthly with a delay of about three months "
                "relatively to actual date.",
            },
        ],
        "documentation": [
            {
                "description": "Further and more detailed information "
                "relating to the ERA5-Land dataset can be "
                "found in the Copernicus Knowledge Base web "
                "link above.",
                "title": "ERA5-Land online documentation",
                "url": "https://confluence.ecmwf.int/display/CKB/ERA5-Land%3A+data+documentation",
            }
        ],
        "doi": "10.24381/cds.e2161bac",
        'ds_contactemail': 'https://support.ecmwf.int',
        'ds_responsible_organisation': 'ECMWF',
        'ds_responsible_organisation_role': 'publisher',
        "end_date": "2022-06-01",
        'file_format': 'grib',
        "form": os.path.join(resource_folder_path, "json-config", "form.json"),
        'format_version': None,
        "geo_extent": {"bboxE": 360, "bboxN": 89, "bboxS": -89, "bboxW": 0},
        "keywords": [
            "Product type: Reanalysis",
            "Spatial coverage: Global",
            "Temporal coverage: Past",
            "Variable domain: Land (hydrology)",
            "Variable domain: Land (physics)",
            "Variable domain: Land (biosphere)",
            "Provider: Copernicus C3S",
        ],
        "layout": os.path.join(resource_folder_path, "json-config", "layout.json"),
        "licence_uids": ["licence-to-use-copernicus-products"],
        'lineage': 'EC Copernicus program',
        "mapping": os.path.join(resource_folder_path, "json-config", "mapping.json"),
        "previewimage": os.path.join(
            resource_folder_path, "content", "overview", "overview.png"
        ),
        "publication_date": "2019-07-12",
        'representative_fraction': 0.25,
        "resource_uid": "reanalysis-era5-land",
        'resource_update': '2022-11-24',
        'responsible_organisation': 'ECMWF',
        'responsible_organisation_role': 'pointOfContact',
        'responsible_organisation_website': 'https://www.ecmwf.int/',
        "title": None,
        'topic': 'climatologyMeteorologyAtmosphere',
        "type": "dataset",
        'unit_measure': 'dd',
        'use_limitation': 'Content accessible through the CDS may only be used under '
                          'the terms of the licenses attributed to each particular '
                          'resource.',
        "variables": [
            {
                "description": "Eastward component of the 10m wind. It is the "
                "horizontal speed of air moving towards the "
                "east, at a height of ten metres above the "
                "surface of the Earth, in metres per second. "
                "Care should be taken when comparing this "
                "variable with observations, because wind "
                "observations vary on small space and time "
                "scales and are affected by the local terrain, "
                "vegetation and buildings that are represented "
                "only on average in the ECMWF Integrated "
                "Forecasting System. This variable can be "
                "combined with the V component of 10m wind to "
                "give the speed and direction of the horizontal "
                "10m wind.",
                "id": "10m_u_component_of_wind",
                "label": "10m u-component of wind",
                "units": "m s^-1",
            },
            {
                "description": "Northward component of the 10m wind. It is the "
                "horizontal speed of air moving towards the "
                "north, at a height of ten metres above the "
                "surface of the Earth, in metres per second. "
                "Care should be taken when comparing this "
                "variable with observations, because wind "
                "observations vary on small space and time "
                "scales and are affected by the local terrain, "
                "vegetation and buildings that are represented "
                "only on average in the ECMWF Integrated "
                "Forecasting System. This variable can be "
                "combined with the U component of 10m wind to "
                "give the speed and direction of the horizontal "
                "10m wind.",
                "id": "10m_v_component_of_wind",
                "label": "10m v-component of wind",
                "units": "m s^-1",
            },
            {
                "description": "Temperature to which the air, at 2 metres "
                "above the surface of the Earth, would have to "
                "be cooled for saturation to occur.It is a "
                "measure of the humidity of the air. Combined "
                "with temperature and pressure, it can be used "
                "to calculate the relative humidity. 2m dew "
                "point temperature is calculated by "
                "interpolating between the lowest model level "
                "and the Earth's surface, taking account of the "
                "atmospheric conditions. Temperature measured "
                "in kelvin can be converted to degrees Celsius "
                "(°C) by subtracting 273.15.",
                "id": "2m_dewpoint_temperature",
                "label": "2m dewpoint temperature",
                "units": "K",
            },
            {
                "description": "Temperature of air at 2m above the surface of "
                "land, sea or in-land waters. 2m temperature is "
                "calculated by interpolating between the lowest "
                "model level and the Earth's surface, taking "
                "account of the atmospheric conditions. "
                "Temperature measured in kelvin can be "
                "converted to degrees Celsius (°C) by "
                "subtracting 273.15.",
                "id": "2m_temperature",
                "label": "2m temperature",
                "units": "K",
            },
            {
                "description": "The amount of evaporation from bare soil at "
                "the top of the land surface. This variable is "
                "accumulated from the beginning of the forecast "
                "time to the end of the forecast step.",
                "id": "evaporation_from_bare_soil",
                "label": "Evaporation from bare soil",
                "units": "m of water equivalent",
            },
            {
                "description": "Amount of evaporation from surface water "
                "storage like lakes and inundated areas but "
                "excluding oceans. This variable is accumulated "
                "from the beginning of the forecast time to the "
                "end of the forecast step.",
                "id": "evaporation_from_open_water_surfaces_excluding_oceans",
                "label": "Evaporation from open water surfaces excluding " "oceans",
                "units": "m of water equivalent",
            },
            {
                "description": "The amount of evaporation from the canopy "
                "interception reservoir at the top of the "
                "canopy. This variable is accumulated from the "
                "beginning of the forecast time to the end of "
                "the forecast step.",
                "id": "evaporation_from_the_top_of_canopy",
                "label": "Evaporation from the top of canopy",
                "units": "m of water equivalent",
            },
            {
                "description": "Amount of evaporation from vegetation "
                "transpiration. This has the same meaning as "
                "root extraction i.e. the amount of water "
                "extracted from the different soil layers. This "
                "variable is accumulated from the beginning of "
                "the forecast time to the end of the forecast "
                "step.",
                "id": "evaporation_from_vegetation_transpiration",
                "label": "Evaporation from vegetation transpiration",
                "units": "m of water equivalent",
            },
            {
                "description": "Is a measure of the reflectivity of the "
                "Earth's surface. It is the fraction of solar "
                "(shortwave) radiation reflected by Earth's "
                "surface, across the solar spectrum, for both "
                "direct and diffuse radiation. Values are "
                "between 0 and 1. Typically, snow and ice have "
                "high reflectivity with albedo values of 0.8 "
                "and above, land has intermediate values "
                "between about 0.1 and 0.4 and the ocean has "
                "low values of 0.1 or less. Radiation from the "
                "Sun (solar, or shortwave, radiation) is partly "
                "reflected back to space by clouds and "
                "particles in the atmosphere (aerosols) and "
                "some of it is absorbed. The rest is incident "
                "on the Earth's surface, where some of it is "
                "reflected. The portion that is reflected by "
                "the Earth's surface depends on the albedo. In "
                "the ECMWF Integrated Forecasting System (IFS), "
                "a climatological background albedo (observed "
                "values averaged over a period of several "
                "years) is used, modified by the model over "
                "water, ice and snow. Albedo is often shown as "
                "a percentage (%).",
                "id": "forecast_albedo",
                "label": "Forecast albedo",
                "units": "dimensionless",
            },
            {
                "description": "Temperature of water at the bottom of inland "
                "water bodies (lakes, reservoirs, rivers) and "
                "coastal waters. ECMWF implemented a lake model "
                "in May 2015 to represent the water temperature "
                "and lake ice of all the world’s major inland "
                "water bodies in the Integrated Forecasting "
                "System. The model keeps lake depth and surface "
                "area (or fractional cover) constant in time.",
                "id": "lake_bottom_temperature",
                "label": "Lake bottom temperature",
                "units": "K",
            },
            {
                "description": "The thickness of ice on inland water bodies "
                "(lakes, reservoirs and rivers) and coastal "
                "waters. The ECMWF Integrated Forecasting "
                "System (IFS) represents the formation and "
                "melting of ice on inland water bodies (lakes, "
                "reservoirs and rivers) and coastal water. A "
                "single ice layer is represented. This "
                "parameter is the thickness of that ice layer.",
                "id": "lake_ice_depth",
                "label": "Lake ice depth",
                "units": "m",
            },
            {
                "description": "The temperature of the uppermost surface of "
                "ice on inland water bodies (lakes, reservoirs, "
                "rivers) and coastal waters. The ECMWF "
                "Integrated Forecasting System represents the "
                "formation and melting of ice on lakes. A "
                "single ice layer is represented. The "
                "temperature measured in kelvin can be "
                "converted to degrees Celsius (°C) by "
                "subtracting 273.15.",
                "id": "lake_ice_temperature",
                "label": "Lake ice temperature",
                "units": "K",
            },
            {
                "description": "The thickness of the upper most layer of an "
                "inland water body (lake, reservoirs, and "
                "rivers) or coastal waters that is well mixed "
                "and has a near constant temperature with depth "
                "(uniform distribution of temperature). The "
                "ECMWF Integrated Forecasting System represents "
                "inland water bodies with two layers in the "
                "vertical, the mixed layer above and the "
                "thermocline below. Thermoclines upper boundary "
                "is located at the mixed layer bottom, and the "
                "lower boundary at the lake bottom. Mixing "
                "within the mixed layer can occur when the "
                "density of the surface (and near-surface) "
                "water is greater than that of the water below. "
                "Mixing can also occur through the action of "
                "wind on the surface of the lake.",
                "id": "lake_mix_layer_depth",
                "label": "Lake mix-layer depth",
                "units": "m",
            },
            {
                "description": "The temperature of the upper most layer of "
                "inland water bodies (lakes, reservoirs and "
                "rivers) or coastal waters) that is well mixed. "
                "The ECMWF Integrated Forecasting System "
                "represents inland water bodies with two layers "
                "in the vertical, the mixed layer above and the "
                "thermocline below. Thermoclines upper boundary "
                "is located at the mixed layer bottom, and the "
                "lower boundary at the lake bottom. Mixing "
                "within the mixed layer can occur when the "
                "density of the surface (and near-surface) "
                "water is greater than that of the water below. "
                "Mixing can also occur through the action of "
                "wind on the surface of the lake. Temperature "
                "measured in kelvin can be converted to degrees "
                "Celsius (°C) by subtracting 273.15.",
                "id": "lake_mix_layer_temperature",
                "label": "Lake mix-layer temperature",
                "units": "K",
            },
            {
                "description": "This parameter describes the way that "
                "temperature changes with depth in the "
                "thermocline layer of inland water bodies "
                "(lakes, reservoirs and rivers) and coastal "
                "waters. It is used to calculate the lake "
                "bottom temperature and other lake-related "
                "parameters. The ECMWF Integrated Forecasting "
                "System represents inland and coastal water "
                "bodies with two layers in the vertical, the "
                "mixed layer above and the thermocline below "
                "where temperature changes with depth.",
                "id": "lake_shape_factor",
                "label": "Lake shape factor",
                "units": "dimensionless",
            },
            {
                "description": "The mean temperature of total water column in "
                "inland water bodies (lakes, reservoirs and "
                "rivers) and coastal waters. The ECMWF "
                "Integrated Forecasting System represents "
                "inland water bodies with two layers in the "
                "vertical, the mixed layer above and the "
                "thermocline below where temperature changes "
                "with depth. This parameter is the mean over "
                "the two layers. Temperature measured in kelvin "
                "can be converted to degrees Celsius (°C) by "
                "subtracting 273.15.",
                "id": "lake_total_layer_temperature",
                "label": "Lake total layer temperature",
                "units": "K",
            },
            {
                "description": "One-half of the total green leaf area per unit "
                "horizontal ground surface area for high "
                "vegetation type.",
                "id": "leaf_area_index_high_vegetation",
                "label": "Leaf area index, high vegetation",
                "units": "m^2 m^-2",
            },
            {
                "description": "One-half of the total green leaf area per unit "
                "horizontal ground surface area for low "
                "vegetation type.",
                "id": "leaf_area_index_low_vegetation",
                "label": "Leaf area index, low vegetation",
                "units": "m^2 m^-2",
            },
            {
                "description": "Potential evaporation (pev) in the current "
                "ECMWF model is computed, by making a second "
                "call to the surface energy balance routine "
                "with the vegetation variables set to "
                '"crops/mixed farming" and assuming no stress '
                "from soil moisture. In other words, "
                "evaporation is computed for agricultural land "
                "as if it is well watered and assuming that the "
                "atmosphere is not affected by this artificial "
                "surface condition. The latter may not always "
                "be realistic. Although pev is meant to provide "
                "an estimate of irrigation requirements, the "
                "method can give unrealistic results in arid "
                "conditions due to too strong evaporation "
                "forced by dry air. Note that in ERA5-Land pev "
                "is computed as an open water evaporation (Pan "
                "evaporation) and assuming that the atmosphere "
                "is not affected by this artificial surface "
                "condition. The latter is different  from the "
                "way pev is computed in ERA5. This variable is "
                "accumulated from the beginning of the forecast "
                "time to the end of the forecast step.",
                "id": "potential_evaporation",
                "label": "Potential evaporation",
                "units": "m",
            },
            {
                "description": "Some water from rainfall, melting snow, or "
                "deep in the soil, stays stored in the soil. "
                "Otherwise, the water drains away, either over "
                "the surface (surface runoff), or under the "
                "ground (sub-surface runoff) and the sum of "
                "these two is simply called 'runoff'. This "
                "variable is the total amount of water "
                "accumulated from the beginning of the forecast "
                "time to the end of the forecast step. The "
                "units of runoff are depth in metres. This is "
                "the depth the water would have if it were "
                "spread evenly over the grid box. Care should "
                "be taken when comparing model variables with "
                "observations, because observations are often "
                "local to a particular point rather than "
                "averaged over a grid square area.  "
                "Observations are also often taken in different "
                "units, such as mm/day, rather than the "
                "accumulated metres produced here. Runoff is a "
                "measure of the availability of water in the "
                "soil, and can, for example, be used as an "
                "indicator of drought or flood. More "
                "information about how runoff is calculated is "
                "given in the IFS Physical Processes "
                "documentation.",
                "id": "runoff",
                "label": "Runoff",
                "units": "m",
            },
            {
                "description": "Amount of water in the vegetation canopy "
                "and/or in a thin layer on the soil. It "
                "represents the amount of rain intercepted by "
                "foliage, and water from dew. The maximum "
                "amount of 'skin reservoir content' a grid box "
                "can hold depends on the type of vegetation, "
                "and may be zero.  Water leaves the 'skin "
                "reservoir' by evaporation.",
                "id": "skin_reservoir_content",
                "label": "Skin reservoir content",
                "units": "m of water equivalent",
            },
            {
                "description": "Temperature of the surface of the Earth. The "
                "skin temperature is the theoretical "
                "temperature that is required to satisfy the "
                "surface energy balance. It represents the "
                "temperature of the uppermost surface layer, "
                "which has no heat capacity and so can respond "
                "instantaneously to changes in surface fluxes. "
                "Skin temperature is calculated differently "
                "over land and sea. Temperature measured in "
                "kelvin can be converted to degrees Celsius "
                "(°C) by subtracting 273.15.",
                "id": "skin_temperature",
                "label": "Skin temperature",
                "units": "K",
            },
            {
                "description": "It is defined as the fraction of solar "
                "(shortwave) radiation reflected by the snow, "
                "across the solar spectrum, for both direct and "
                "diffuse radiation. It is a measure of the "
                "reflectivity of the snow covered grid cells. "
                "Values vary between 0 and 1. Typically, snow "
                "and ice have high reflectivity with albedo "
                "values of 0.8 and above.",
                "id": "snow_albedo",
                "label": "Snow albedo",
                "units": "dimensionless",
            },
            {
                "description": "It represents the fraction (0-1) of the cell / "
                "grid-box occupied by snow (similar to the "
                "cloud cover fields of ERA5).",
                "id": "snow_cover",
                "label": "Snow cover",
                "units": "%",
            },
            {
                "description": "Mass of snow per cubic metre in the snow "
                "layer. The ECMWF Integrated Forecast System "
                "(IFS) model represents snow as a single "
                "additional layer over the uppermost soil "
                "level. The snow may cover all or part of the "
                "grid box.",
                "id": "snow_density",
                "label": "Snow density",
                "units": "kg m^-3",
            },
            {
                "description": "Instantaneous grib-box average of the snow "
                "thickness on the ground (excluding snow on "
                "canopy).",
                "id": "snow_depth",
                "label": "Snow depth",
                "units": "m",
            },
            {
                "description": "Depth of snow from the snow-covered area of a "
                "grid box. Its units are metres of water "
                "equivalent, so it is the depth the water would "
                "have if the snow melted and was spread evenly "
                "over the whole grid box. The ECMWF Integrated "
                "Forecast System represents snow as a single "
                "additional layer over the uppermost soil "
                "level. The snow may cover all or part of the "
                "grid box.",
                "id": "snow_depth_water_equivalent",
                "label": "Snow depth water equivalent",
                "units": "m of water equivalent",
            },
            {
                "description": "Evaporation from snow averaged over the grid "
                "box (to find flux over snow, divide by snow "
                "fraction). This variable is accumulated from "
                "the beginning of the forecast time to the end "
                "of the forecast step.",
                "id": "snow_evaporation",
                "label": "Snow evaporation",
                "units": "m of water equivalent",
            },
            {
                "description": "Accumulated total snow that has fallen to the "
                "Earth's surface. It consists of snow due to "
                "the large-scale atmospheric flow (horizontal "
                "scales greater than around a few hundred "
                "metres) and convection where smaller scale "
                "areas (around 5km to a few hundred kilometres) "
                "of warm air rise. If snow has melted during "
                "the period over which this variable was "
                "accumulated, then it will be higher than the "
                "snow depth. This variable is the total amount "
                "of water accumulated from the beginning of the "
                "forecast time to the end of the forecast step. "
                "The units given measure the depth the water "
                "would have if the snow melted and was spread "
                "evenly over the grid box. Care should be taken "
                "when comparing model variables with "
                "observations, because observations are often "
                "local to a particular point in space and time, "
                "rather than representing averages over a model "
                "grid box and model time step.",
                "id": "snowfall",
                "label": "Snowfall",
                "units": "m of water equivalent",
            },
            {
                "description": "Melting of snow averaged over the grid box (to "
                "find melt over snow, divide by snow fraction). "
                "This variable is accumulated from the "
                "beginning of the forecast time to the end of "
                "the forecast step.",
                "id": "snowmelt",
                "label": "Snowmelt",
                "units": "m of water equivalent",
            },
            {
                "description": "Temperature of the soil in layer 1 (0 - 7 cm) "
                "of the ECMWF Integrated Forecasting System. "
                "The surface is at 0 cm. Soil temperature is "
                "set at the middle of each layer, and heat "
                "transfer is calculated at the interfaces "
                "between them. It is assumed that there is no "
                "heat transfer out of the bottom of the lowest "
                "layer. Temperature measured in kelvin can be "
                "converted to degrees Celsius (°C) by "
                "subtracting 273.15.",
                "id": "soil_temperature_level_1",
                "label": "Soil temperature level 1",
                "units": "K",
            },
            {
                "description": "Temperature of the soil in layer 2 (7 -28cm) "
                "of the ECMWF Integrated Forecasting System.",
                "id": "soil_temperature_level_2",
                "label": "Soil temperature level 2",
                "units": "K",
            },
            {
                "description": "Temperature of the soil in layer 3 (28-100cm) "
                "of the ECMWF Integrated Forecasting System.",
                "id": "soil_temperature_level_3",
                "label": "Soil temperature level 3",
                "units": "K",
            },
            {
                "description": "Temperature of the soil in layer 4 (100-289 "
                "cm) of the ECMWF Integrated Forecasting "
                "System.",
                "id": "soil_temperature_level_4",
                "label": "Soil temperature level 4",
                "units": "K",
            },
            {
                "description": "Some water from rainfall, melting snow, or "
                "deep in the soil, stays stored in the soil. "
                "Otherwise, the water drains away, either over "
                "the surface (surface runoff), or under the "
                "ground (sub-surface runoff) and the sum of "
                "these two is simply called 'runoff'. This "
                "variable is accumulated from the beginning of "
                "the forecast time to the end of the forecast "
                "step. The units of runoff are depth in metres. "
                "This is the depth the water would have if it "
                "were spread evenly over the grid box. Care "
                "should be taken when comparing model variables "
                "with observations, because observations are "
                "often local to a particular point rather than "
                "averaged over a grid square area.  "
                "Observations are also often taken in different "
                "units, such as mm/day, rather than the "
                "accumulated metres produced here. Runoff is a "
                "measure of the availability of water in the "
                "soil, and can, for example, be used as an "
                "indicator of drought or flood. More "
                "information about how runoff is calculated is "
                "given in the IFS Physical Processes "
                "documentation.",
                "id": "sub_surface_runoff",
                "label": "Sub-surface runoff",
                "units": "m",
            },
            {
                "description": "Exchange of latent heat with the surface "
                "through turbulent diffusion. This variables is "
                "accumulated from the beginning of the forecast "
                "time to the end of the forecast step. By model "
                "convention, downward fluxes are positive.",
                "id": "surface_latent_heat_flux",
                "label": "Surface latent heat flux",
                "units": "J m^-2",
            },
            {
                "description": "Amount of solar radiation (also known as "
                "shortwave radiation) reaching the surface of "
                "the Earth (both direct and diffuse) minus the "
                "amount reflected by the Earth's surface (which "
                "is governed by the albedo).Radiation from the "
                "Sun (solar, or shortwave, radiation) is partly "
                "reflected back to space by clouds and "
                "particles in the atmosphere (aerosols) and "
                "some of it is absorbed. The rest is incident "
                "on the Earth's surface, where some of it is "
                "reflected. The difference between downward and "
                "reflected solar radiation is the surface net "
                "solar radiation. This variable is accumulated "
                "from the beginning of the forecast time to the "
                "end of the forecast step. The units are joules "
                "per square metre (J m^-2). To convert to watts "
                "per square metre (W m^-2), the accumulated "
                "values should be divided by the accumulation "
                "period expressed in seconds. The ECMWF "
                "convention for vertical fluxes is positive "
                "downwards.",
                "id": "surface_net_solar_radiation",
                "label": "Surface net solar radiation",
                "units": "J m^-2",
            },
            {
                "description": "Net thermal radiation at the surface. "
                "Accumulated field from the beginning of the "
                "forecast time to the end of the forecast step. "
                "By model convention downward fluxes are "
                "positive.",
                "id": "surface_net_thermal_radiation",
                "label": "Surface net thermal radiation",
                "units": "J m^-2",
            },
            {
                "description": "Pressure (force per unit area) of the "
                "atmosphere on the surface of land, sea and "
                "in-land water. It is a measure of the weight "
                "of all the air in a column vertically above "
                "the area of the Earth's surface represented at "
                "a fixed point. Surface pressure is often used "
                "in combination with temperature to calculate "
                "air density. The strong variation of pressure "
                "with altitude makes it difficult to see the "
                "low and high pressure systems over mountainous "
                "areas, so mean sea level pressure, rather than "
                "surface pressure, is normally used for this "
                "purpose. The units of this variable are "
                "Pascals (Pa). Surface pressure is often "
                "measured in hPa and sometimes is presented in "
                "the old units of millibars, mb (1 hPa = 1 mb = "
                "100 Pa).",
                "id": "surface_pressure",
                "label": "Surface pressure",
                "units": "Pa",
            },
            {
                "description": "Some water from rainfall, melting snow, or "
                "deep in the soil, stays stored in the soil. "
                "Otherwise, the water drains away, either over "
                "the surface (surface runoff), or under the "
                "ground (sub-surface runoff) and the sum of "
                "these two is simply called 'runoff'. This "
                "variable is the total amount of water "
                "accumulated from the beginning of the forecast "
                "time to the end of the forecast step. The "
                "units of runoff are depth in metres. This is "
                "the depth the water would have if it were "
                "spread evenly over the grid box. Care should "
                "be taken when comparing model variables with "
                "observations, because observations are often "
                "local to a particular point rather than "
                "averaged over a grid square area. Observations "
                "are also often taken in different units, such "
                "as mm/day, rather than the accumulated metres "
                "produced here. Runoff is a measure of the "
                "availability of water in the soil, and can, "
                "for example, be used as an indicator of "
                "drought or flood. More information about how "
                "runoff is calculated is given in the IFS "
                "Physical Processes documentation.",
                "id": "surface_runoff",
                "label": "Surface runoff",
                "units": "m",
            },
            {
                "description": "Transfer of heat between the Earth's surface "
                "and the atmosphere through the effects of "
                "turbulent air motion (but excluding any heat "
                "transfer resulting from condensation or "
                "evaporation). The magnitude of the sensible "
                "heat flux is governed by the difference in "
                "temperature between the surface and the "
                "overlying atmosphere, wind speed and the "
                "surface roughness. For example, cold air "
                "overlying a warm surface would produce a "
                "sensible heat flux from the land (or ocean) "
                "into the atmosphere. This is a single level "
                "variable and it is accumulated from the "
                "beginning of the forecast time to the end of "
                "the forecast step. The units are joules per "
                "square metre (J m^-2). To convert to watts per "
                "square metre (W m^-2), the accumulated values "
                "should be divided by the accumulation period "
                "expressed in seconds. The ECMWF convention for "
                "vertical fluxes is positive downwards.",
                "id": "surface_sensible_heat_flux",
                "label": "Surface sensible heat flux",
                "units": "J m^-2",
            },
            {
                "description": "Amount of solar radiation (also known as "
                "shortwave radiation) reaching the surface of "
                "the Earth. This variable comprises both direct "
                "and diffuse solar radiation. Radiation from "
                "the Sun (solar, or shortwave, radiation) is "
                "partly reflected back to space by clouds and "
                "particles in the atmosphere (aerosols) and "
                "some of it is absorbed.  The rest is incident "
                "on the Earth's surface (represented by this "
                "variable). To a reasonably good approximation, "
                "this variable is the model equivalent of what "
                "would be measured by a pyranometer (an "
                "instrument used for measuring solar radiation) "
                "at the surface. However, care should be taken "
                "when comparing model variables with "
                "observations, because observations are often "
                "local to a particular point in space and time, "
                "rather than representing averages over a  "
                "model grid box and model time step. This "
                "variable is accumulated from the beginning of "
                "the forecast time to the end of the forecast "
                "step. The units are joules per square metre (J "
                "m^-2). To convert to watts per square metre (W "
                "m^-2), the accumulated values should be "
                "divided by the accumulation period expressed "
                "in seconds. The ECMWF convention for vertical "
                "fluxes is positive downwards.",
                "id": "surface_solar_radiation_downwards",
                "label": "Surface solar radiation downwards",
                "units": "J m-2",
            },
            {
                "description": "Amount of thermal (also known as longwave or "
                "terrestrial) radiation emitted by the "
                "atmosphere and clouds that reaches the Earth's "
                "surface. The surface of the Earth emits "
                "thermal radiation, some of which is absorbed "
                "by the atmosphere and clouds. The atmosphere "
                "and clouds likewise emit thermal radiation in "
                "all directions, some of which reaches the "
                "surface (represented by this variable). This "
                "variable is accumulated from the beginning of "
                "the forecast time to the end of the forecast "
                "step. The units are joules per square metre (J "
                "m^-2). To convert to watts per square metre (W "
                "m^-2), the accumulated values should be "
                "divided by the accumulation period expressed "
                "in seconds. The ECMWF convention for vertical "
                "fluxes is positive downwards.",
                "id": "surface_thermal_radiation_downwards",
                "label": "Surface thermal radiation downwards",
                "units": "J m-2",
            },
            {
                "description": "This variable gives the temperature of the "
                "snow layer from the ground to the snow-air "
                "interface. The ECMWF Integrated Forecast "
                "System (IFS) model represents snow as a single "
                "additional layer over the uppermost soil "
                "level. The snow may cover all or part of the  "
                "grid box. Temperature measured in kelvin can "
                "be converted to degrees Celsius (°C) by "
                "subtracting 273.15.",
                "id": "temperature_of_snow_layer",
                "label": "Temperature of snow layer",
                "units": "K",
            },
            {
                "description": "Accumulated amount of water that has "
                "evaporated from the Earth's surface, including "
                "a simplified representation of transpiration "
                "(from vegetation), into vapour in the air "
                "above. This variable is accumulated from the "
                "beginning of the forecast to the end of the "
                "forecast step. The ECMWF Integrated "
                "Forecasting System convention is that downward "
                "fluxes are positive. Therefore, negative "
                "values indicate evaporation and positive "
                "values indicate condensation.",
                "id": "total_evaporation",
                "label": "Total evaporation",
                "units": "m of water equivalent",
            },
            {
                "description": "Accumulated liquid and frozen water, including "
                "rain and snow, that falls to the Earth's "
                "surface. It is the sum of large-scale "
                "precipitation (that precipitation which is "
                "generated by large-scale weather patterns, "
                "such as troughs and cold fronts) and "
                "convective precipitation (generated by "
                "convection which occurs when air at lower "
                "levels in the atmosphere is warmer and less "
                "dense than the air above, so it rises). "
                "Precipitation variables do not include fog, "
                "dew or the precipitation that evaporates in "
                "the atmosphere before it lands at the surface "
                "of the Earth. This variable is accumulated "
                "from the beginning of the forecast time to the "
                "end of the forecast step. The units of "
                "precipitation are depth in metres. It is the "
                "depth the water would have if it were spread "
                "evenly over the grid box. Care should be taken "
                "when comparing model variables with "
                "observations, because observations are often "
                "local to a particular point in space and time, "
                "rather than representing averages over a model "
                "grid box and  model time step.",
                "id": "total_precipitation",
                "label": "Total precipitation",
                "units": "m",
            },
            {
                "description": "Volume of water in soil layer 1 (0 - 7 cm) of "
                "the ECMWF Integrated Forecasting System. The "
                "surface is at 0 cm. The volumetric soil water "
                "is associated with the soil texture (or "
                "classification), soil depth, and the "
                "underlying groundwater level.",
                "id": "volumetric_soil_water_layer_1",
                "label": "Volumetric soil water layer 1",
                "units": "m^3 m^-3",
            },
            {
                "description": "Volume of water in soil layer 2 (7 -28 cm) of "
                "the ECMWF Integrated Forecasting System.",
                "id": "volumetric_soil_water_layer_2",
                "label": "Volumetric soil water layer 2",
                "units": "m^3 m^-3",
            },
            {
                "description": "Volume of water in soil layer 3 (28-100 cm) of "
                "the ECMWF Integrated Forecasting System.",
                "id": "volumetric_soil_water_layer_3",
                "label": "Volumetric soil water layer 3",
                "units": "m^3 m^-3",
            },
            {
                "description": "Volume of water in soil layer 4 (100-289 cm) "
                "of the ECMWF Integrated Forecasting System.",
                "id": "volumetric_soil_water_layer_4",
                "label": "Volumetric soil water layer 4",
                "units": "m^3 m^-3",
            },
        ],
    }
    assert resource == expected_resource


def test_store_licences(session_obj: sessionmaker, mocker) -> None:
    object_storage_url = "http://myobject-storage:myport/"
    storage_kws: dict[str, Any] = {
        "access_key": "storage_user",
        "secret_key": "storage_password",
        "secure": False,
    }
    licences_folder_path = os.path.join(TESTDATA_PATH, "cds-licences")
    licences = manager.load_licences_from_folder(licences_folder_path)
    session = session_obj()
    res = session.query(database.Licence).all()
    assert res == []
    patch = mocker.patch(
        "cads_catalogue.object_storage.store_file",
        return_value=("an url", "a version"),
    )

    manager.store_licences(session, licences, object_storage_url, **storage_kws)
    session.commit()
    assert patch.call_count == len(licences)
    assert patch.mock_calls[0].args == (
        os.path.join(licences_folder_path, "licence-to-use-copernicus-products.pdf"),
        object_storage_url,
    )
    assert patch.mock_calls[0].kwargs == {
        "force": True,
        "subpath": "licences/licence-to-use-copernicus-products",
        "access_key": "storage_user",
        "secret_key": "storage_password",
        "secure": False,
    }
    res = session.query(database.Licence).all()
    assert len(res) == len(licences)
    db_obj_as_dict = manager.object_as_dict(res[0])
    assert 1 == db_obj_as_dict.pop("licence_id")
    assert db_obj_as_dict == licences[0]
    assert db_obj_as_dict["download_filename"] == "an url"
    session.close()
    # reset globals for tests following
    config.dbsettings = None


def test_store_dataset(session_obj: sessionmaker, mocker) -> None:
    object_storage_url = "http://myobject-storage:myport/"
    storage_kws: dict[str, Any] = {
        "access_key": "storage_user",
        "secret_key": "storage_password",
        "secure": False,
    }

    mocker.patch.object(
        object_storage, "store_file", return_value=("an url", "a version")
    )
    licences_folder_path = os.path.join(TESTDATA_PATH, "cds-licences")
    licences = manager.load_licences_from_folder(licences_folder_path)
    session = session_obj()
    manager.store_licences(session, licences, object_storage_url, **storage_kws)
    resource_folder_path = os.path.join(TESTDATA_PATH, "reanalysis-era5-land")
    resource = manager.load_resource_from_folder(resource_folder_path)
    assert resource["licence_uids"] == [licences[0]["licence_uid"]]
    res = session.query(database.Resource).all()
    assert res == []

    patch = mocker.patch(
        "cads_catalogue.object_storage.store_file",
        return_value=("an url", "a version"),
    )
    stored_record = manager.store_dataset(
        session, resource, object_storage_url, **storage_kws
    )
    session.commit()
    assert patch.call_count == len(
        set(dict(manager.OBJECT_STORAGE_UPLOAD_FILES).values())
    )
    kwargs = storage_kws.copy()
    kwargs["subpath"] = "resources/reanalysis-era5-land"
    kwargs["force"] = True
    effective_calls_pars = [(c.args, c.kwargs) for c in patch.mock_calls]
    for file_name, db_field in manager.OBJECT_STORAGE_UPLOAD_FILES:
        expected_call_pars = (
            (resource[db_field], object_storage_url),
            kwargs,
        )
        assert expected_call_pars in effective_calls_pars
    # assert (
    #     (os.path.join(DATA_PATH, "layout.json"), object_storage_url),
    #     kwargs,
    # ) in effective_calls_pars

    assert 1 == stored_record.pop("resource_id")
    for column, value in stored_record.items():
        if column not in [
            "adaptor",
            "record_update",
            "form",
            "constraints",
            "previewimage",
            "mapping",
            "layout",
        ]:
            assert resource.get(column) == value
    assert stored_record["form"] == "an url"
    assert stored_record["constraints"] == "an url"
    assert stored_record["previewimage"] == "an url"
    assert stored_record["mapping"] == "an url"
    assert stored_record["layout"] == "an url"
    expected_many2many_record = {
        "resource_id": 1,
        "licence_id": 1,
    }
    assert (
        manager.object_as_dict(session.query(database.ResourceLicence).first())
        == expected_many2many_record
    )

    session.close()
    # reset globals for tests following
    config.dbsettings = None
