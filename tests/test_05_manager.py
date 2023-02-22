import json
import operator
import os.path
from typing import Any

import pytest
import pytest_mock
from sqlalchemy.orm import sessionmaker

from cads_catalogue import config, database, manager, object_storage, utils

THIS_PATH = os.path.abspath(os.path.dirname(__file__))
TESTDATA_PATH = os.path.join(THIS_PATH, "data")


def dummy_get_last_commit_hash1(folder):
    """Use for testing is_db_to_update."""
    if "cads-forms-json" in folder:
        return "5f662d202e4084dd569567bab0957c8a56f79c0f"
    else:
        return "f0591ec408b59d32a46a5d08b9786641dffe5c7e"


def dummy_get_last_commit_hash2(folder):
    """Use for testing is_db_to_update."""
    if "cads-forms-json" in folder:
        return "5f662d202e4084dd569567bab0957c8a56f79aaa"
    else:
        return "f0591ec408b59d32a46a5d08b9786641dffe5bbb"


def test_is_db_to_update(
    session_obj: sessionmaker, mocker: pytest_mock.MockerFixture
) -> None:
    mocker.patch.object(utils, "get_last_commit_hash", new=dummy_get_last_commit_hash1)
    resource_folder_path = os.path.join(TESTDATA_PATH, "cads-forms-json")
    licences_folder_path = os.path.join(TESTDATA_PATH, "cds-licences")
    last_c1 = "5f662d202e4084dd569567bab0957c8a56f79c0f"
    last_l1 = "f0591ec408b59d32a46a5d08b9786641dffe5c7e"
    c2 = "5f662d202e4084dd569567bab0957c8a56f79aaa"
    l2 = "f0591ec408b59d32a46a5d08b9786641dffe5bbb"
    with session_obj() as session:
        # begin with empty table
        assert manager.is_db_to_update(
            session, resource_folder_path, licences_folder_path
        ) == (True, last_c1, last_l1)
        # insert a catalogue update
        new_record = database.CatalogueUpdate(
            catalogue_repo_commit=last_c1, licence_repo_commit=last_l1
        )
        session.add(new_record)
        session.commit()
        assert manager.is_db_to_update(
            session, resource_folder_path, licences_folder_path
        ) == (False, last_c1, last_l1)
        # simulate a new repo update
        mocker.patch.object(
            utils, "get_last_commit_hash", new=dummy_get_last_commit_hash2
        )
        assert manager.is_db_to_update(
            session, resource_folder_path, licences_folder_path
        ) == (True, c2, l2)
        # update the db with only one right repo commit
        new_record = database.CatalogueUpdate(
            catalogue_repo_commit=c2,
            licence_repo_commit=last_l1,
        )
        session.add(new_record)
        session.commit()
        assert manager.is_db_to_update(
            session, resource_folder_path, licences_folder_path
        ) == (True, c2, l2)
        # update the db with both two right repo commit
        new_record = database.CatalogueUpdate(
            catalogue_repo_commit=c2,
            licence_repo_commit=l2,
        )
        session.add(new_record)
        session.commit()
        assert manager.is_db_to_update(
            session, resource_folder_path, licences_folder_path
        ) == (False, c2, l2)


def test_load_licences_from_folder() -> None:
    # test data taken from repository "https://git.ecmwf.int/projects/CDS/repos/cds-licences"
    licences_folder_path = os.path.join(TESTDATA_PATH, "cds-licences")
    expected_licences = [
        {
            "download_filename": os.path.join(
                licences_folder_path,
                "CCI-data-policy-for-satellite-surface-radiation-budget.pdf",
            ),
            "licence_uid": "CCI-data-policy-for-satellite-surface-radiation-budget",
            "revision": 4,
            "title": "CCI product licence",
        },
        {
            "download_filename": os.path.join(
                licences_folder_path, "eumetsat-cm-saf.pdf"
            ),
            "licence_uid": "eumetsat-cm-saf",
            "revision": 1,
            "title": "EUMETSAT CM SAF products licence",
        },
        {
            "download_filename": os.path.join(
                licences_folder_path, "licence-to-use-copernicus-products.pdf"
            ),
            "licence_uid": "licence-to-use-copernicus-products",
            "revision": 12,
            "title": "Licence to use Copernicus Products",
        },
    ]
    licences = sorted(
        manager.load_licences_from_folder(licences_folder_path),
        key=operator.itemgetter("licence_uid"),
    )

    assert licences == expected_licences


def test_load_resource_for_object_storage() -> None:
    folder_path = os.path.join(TESTDATA_PATH, "cads-forms-json", "reanalysis-era5-land")
    res = manager.load_resource_for_object_storage(folder_path)
    assert res == {
        "constraints": os.path.join(folder_path, "constraints.json"),
        "form": os.path.join(folder_path, "form.json"),
        "layout": os.path.join(folder_path, "layout.json"),
        "previewimage": os.path.join(folder_path, "overview.png"),
    }


def test_load_resource_from_folder() -> None:
    resource_folder_path = os.path.join(
        TESTDATA_PATH, "cads-forms-json", "reanalysis-era5-land"
    )
    constraints_fp = open(os.path.join(resource_folder_path, "constraints.json"))
    form_fp = open(os.path.join(resource_folder_path, "form.json"))
    mapping_fp = open(os.path.join(resource_folder_path, "mapping.json"))
    resource = manager.load_resource_from_folder(resource_folder_path)
    expected_resource = {
        "abstract": "ERA5-Land is a reanalysis dataset providing a consistent view "
        "of the evolution of land variables over several decades at an "
        "enhanced resolution compared to ERA5. ERA5-Land has been produced "
        "by replaying the land component of the ECMWF ERA5 climate reanalysis. "
        "Reanalysis combines model data with observations from across the world "
        "into a globally complete and consistent dataset using the laws of physics. "
        "Reanalysis produces data that goes several decades back in time, "
        "providing an accurate description of the climate of the past. \n\n"
        "ERA5-Land uses as input to control the simulated land fields ERA5 "
        "atmospheric variables, such as air temperature and air humidity. "
        "This is called the atmospheric forcing. Without the constraint of "
        "the atmospheric forcing, the model-based estimates can rapidly deviate "
        "from reality. Therefore, while observations are not directly used in "
        "the production of ERA5-Land, they have an indirect influence through "
        "the atmospheric forcing used to run the simulation. In addition, the "
        "input air temperature, air humidity and pressure used to run ERA5-Land"
        " are corrected to account for the altitude difference between the grid"
        " of the forcing and the higher resolution grid of ERA5-Land. This "
        "correction is called 'lapse rate correction'.    \n\n"
        "The ERA5-Land dataset, as any other simulation, provides estimates"
        " which have some degree of uncertainty. Numerical models can only "
        "provide a more or less accurate representation of the real physical "
        "processes governing different components of the Earth System. In general, "
        "the uncertainty of model estimates grows as we go back in time, "
        "because the number of observations available to create a good "
        "quality atmospheric forcing is lower. ERA5-land parameter fields "
        "can currently be used in combination with the uncertainty of the "
        "equivalent ERA5 fields. \n\nThe temporal and spatial resolutions "
        "of ERA5-Land makes this dataset very useful for all kind of land "
        "surface applications such as flood or drought forecasting. The "
        "temporal and spatial resolution of this dataset, the period covered"
        " in time, as well as the fixed grid used for the data distribution "
        "at any period enables decisions makers, businesses and individuals"
        " to access and use more accurate information on land states.",
        "begin_date": "1950-01-01",
        "citation": [
            "Muñoz Sabater, J., (2019): ERA5-Land hourly data from 1981 to present. "
            "Copernicus Climate Change Service (C3S) Climate Data Store (CDS). "
            "(Accessed on < DD-MMM-YYYY >), 10.24381/cds.e2161bac",
            "Muñoz Sabater, J., (2021): ERA5-Land hourly data from 1950 to 1980. "
            "Copernicus Climate Change Service (C3S) Climate Data Store (CDS). "
            "(Accessed on < DD-MMM-YYYY >), 10.24381/cds.e2161bac",
        ],
        "constraints": os.path.join(resource_folder_path, "constraints.json"),
        "constraints_data": json.load(constraints_fp),
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
                "value": "4 levels of the ECMWF surface model: Layer 1: 0 -7cm, Layer 2: 7 -28cm, "
                "Layer 3: 28-100cm, Layer 4: 100-289cm\nSome parameters are defined at "
                "2 m over the surface.\n",
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
                "value": "Monthly with a delay of about three months relatively to actual date.",
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
        "ds_contactemail": "https://support.ecmwf.int",
        "ds_responsible_organisation": "ECMWF",
        "ds_responsible_organisation_role": "publisher",
        "end_date": "2022-10-01",
        "file_format": ["grib", "netcdf"],
        "form": os.path.join(resource_folder_path, "form.json"),
        "form_data": json.load(form_fp),
        "format_version": None,
        "geo_extent": {"bboxE": 360, "bboxN": 89, "bboxS": -89, "bboxW": 0},
        "hidden": False,
        "keywords": [
            "Product type: Reanalysis",
            "Spatial coverage: Global",
            "Temporal coverage: Past",
            "Variable domain: Land (hydrology)",
            "Variable domain: Land (physics)",
            "Variable domain: Land (biosphere)",
            "Provider: Copernicus C3S",
        ],
        "layout": os.path.join(resource_folder_path, "layout.json"),
        "layout_images_info": [
            (os.path.join(resource_folder_path, "overview.png"), "sections", 0, 0)
        ],
        "licence_uids": ["licence-to-use-copernicus-products"],
        "lineage": "EC Copernicus program",
        "mapping": json.load(mapping_fp),
        "previewimage": os.path.join(resource_folder_path, "overview.png"),
        "publication_date": "2019-07-12",
        "related_resources_keywords": [],
        "representative_fraction": 0.25,
        "resource_uid": "reanalysis-era5-land",
        "resource_update": "2022-12-02",
        "responsible_organisation": "ECMWF",
        "responsible_organisation_role": "pointOfContact",
        "responsible_organisation_website": "https://www.ecmwf.int/",
        "title": "ERA5-Land hourly data from 1950 to present",
        "topic": "climatologyMeteorologyAtmosphere",
        "type": "dataset",
        "unit_measure": "dd",
        "use_limitation": "Content accessible through the CDS may only be used under "
        "the terms of the licenses attributed to each particular "
        "resource.",
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
                "label": "2m temperature",
                "units": "K",
            },
            {
                "description": "The amount of evaporation from bare soil at "
                "the top of the land surface. This variable is "
                "accumulated from the beginning of the forecast "
                "time to the end of the forecast step.",
                "label": "Evaporation from bare soil",
                "units": "m of water equivalent",
            },
            {
                "description": "Amount of evaporation from surface water "
                "storage like lakes and inundated areas but "
                "excluding oceans. This variable is accumulated "
                "from the beginning of the forecast time to the "
                "end of the forecast step.",
                "label": "Evaporation from open water surfaces excluding " "oceans",
                "units": "m of water equivalent",
            },
            {
                "description": "The amount of evaporation from the canopy "
                "interception reservoir at the top of the "
                "canopy. This variable is accumulated from the "
                "beginning of the forecast time to the end of "
                "the forecast step.",
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
                "label": "Lake total layer temperature",
                "units": "K",
            },
            {
                "description": "One-half of the total green leaf area per unit "
                "horizontal ground surface area for high "
                "vegetation type.",
                "label": "Leaf area index, high vegetation",
                "units": "m^2 m^-2",
            },
            {
                "description": "One-half of the total green leaf area per unit "
                "horizontal ground surface area for low "
                "vegetation type.",
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
                "label": "Snow albedo",
                "units": "dimensionless",
            },
            {
                "description": "It represents the fraction (0-1) of the cell / "
                "grid-box occupied by snow (similar to the "
                "cloud cover fields of ERA5).",
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
                "label": "Snow density",
                "units": "kg m^-3",
            },
            {
                "description": "Instantaneous grib-box average of the snow "
                "thickness on the ground (excluding snow on "
                "canopy).",
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
                "label": "Snow depth water equivalent",
                "units": "m of water equivalent",
            },
            {
                "description": "Evaporation from snow averaged over the grid "
                "box (to find flux over snow, divide by snow "
                "fraction). This variable is accumulated from "
                "the beginning of the forecast time to the end "
                "of the forecast step.",
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
                "label": "Snowfall",
                "units": "m of water equivalent",
            },
            {
                "description": "Melting of snow averaged over the grid box (to "
                "find melt over snow, divide by snow fraction). "
                "This variable is accumulated from the "
                "beginning of the forecast time to the end of "
                "the forecast step.",
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
                "label": "Soil temperature level 1",
                "units": "K",
            },
            {
                "description": "Temperature of the soil in layer 2 (7 -28cm) "
                "of the ECMWF Integrated Forecasting System.",
                "label": "Soil temperature level 2",
                "units": "K",
            },
            {
                "description": "Temperature of the soil in layer 3 (28-100cm) "
                "of the ECMWF Integrated Forecasting System.",
                "label": "Soil temperature level 3",
                "units": "K",
            },
            {
                "description": "Temperature of the soil in layer 4 (100-289 "
                "cm) of the ECMWF Integrated Forecasting "
                "System.",
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
                "label": "Sub-surface runoff",
                "units": "m",
            },
            {
                "description": "Exchange of latent heat with the surface "
                "through turbulent diffusion. This variables is "
                "accumulated from the beginning of the forecast "
                "time to the end of the forecast step. By model "
                "convention, downward fluxes are positive.",
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
                "label": "Surface net solar radiation",
                "units": "J m^-2",
            },
            {
                "description": "Net thermal radiation at the surface. "
                "Accumulated field from the beginning of the "
                "forecast time to the end of the forecast step. "
                "By model convention downward fluxes are "
                "positive.",
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
                "label": "Volumetric soil water layer 1",
                "units": "m^3 m^-3",
            },
            {
                "description": "Volume of water in soil layer 2 (7 -28 cm) of "
                "the ECMWF Integrated Forecasting System.",
                "label": "Volumetric soil water layer 2",
                "units": "m^3 m^-3",
            },
            {
                "description": "Volume of water in soil layer 3 (28-100 cm) of "
                "the ECMWF Integrated Forecasting System.",
                "label": "Volumetric soil water layer 3",
                "units": "m^3 m^-3",
            },
            {
                "description": "Volume of water in soil layer 4 (100-289 cm) "
                "of the ECMWF Integrated Forecasting System.",
                "label": "Volumetric soil water layer 4",
                "units": "m^3 m^-3",
            },
        ],
    }
    assert resource == expected_resource

    constraints_fp.close()
    form_fp.close()
    mapping_fp.close()


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


def test_load_layout_images_info(tmpdir) -> None:
    layout_path = os.path.join(str(tmpdir), "layout.json")
    # missing blocks with images
    create_layout_for_test(layout_path)
    effective = manager.load_layout_images_info(str(tmpdir))
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
        manager.load_layout_images_info(str(tmpdir))
    # create dummy image
    overview_path = os.path.join(str(tmpdir), "overview")
    os.mkdir(overview_path)
    overview_file_path = os.path.join(overview_path, "overview.png")
    with open(overview_file_path, "w") as fp:
        fp.write("hello! I am an image")
    # on sections position [0, 1]
    effective = manager.load_layout_images_info(str(tmpdir))
    assert effective == {"layout_images_info": [(overview_file_path, "sections", 0, 1)]}
    # on section position [0, 1] and [1, 0]
    sections = [
        {"id": "overview", "blocks": [no_image_block, image_block]},
        {"id": "overview2", "blocks": [image_block, no_image_block]},
    ]
    create_layout_for_test(layout_path, sections)
    effective = manager.load_layout_images_info(str(tmpdir))
    assert effective == {
        "layout_images_info": [
            (overview_file_path, "sections", 0, 1),
            (overview_file_path, "sections", 1, 0),
        ]
    }
    # only on aside, position 0
    aside = {"blocks": [image_block, no_image_block, no_image_block]}
    create_layout_for_test(layout_path, aside=aside)
    effective = manager.load_layout_images_info(str(tmpdir))
    assert effective == {
        "layout_images_info": [
            (overview_file_path, "aside", 0),
        ]
    }
    # only on aside, position 1 and 3
    aside = {"blocks": [no_image_block, image_block, no_image_block, image_block]}
    create_layout_for_test(layout_path, aside=aside)
    effective = manager.load_layout_images_info(str(tmpdir))
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
    effective = manager.load_layout_images_info(str(tmpdir))
    assert effective == {
        "layout_images_info": [
            (overview_file_path, "sections", 1, 1),
            (overview_file_path, "sections", 1, 2),
            (overview_file_path, "aside", 2),
            (overview_file_path, "aside", 4),
        ]
    }


def test_manage_upload_images_and_layout(
    tmpdir, mocker: pytest_mock.MockerFixture
) -> None:
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
    dataset_md = manager.load_layout_images_info(str(tmpdir))
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
    layout_data = manager.manage_upload_images_and_layout(
        dataset_md,
        object_storage_url,
        doc_storage_url=doc_storage_url,
        ret_layout_data=True,
        **storage_kws
    )

    assert layout_data == expected_layout


def test_licence_sync(
    session_obj: sessionmaker, mocker: pytest_mock.MockerFixture
) -> None:
    my_settings_dict = {
        "object_storage_url": "object/storage/url",
        "storage_admin": "admin1",
        "storage_password": "secret1",
        "catalogue_bucket": "mycatalogue_bucket",
        "document_storage_url": "my/url",
    }
    licences_folder_path = os.path.join(TESTDATA_PATH, "cds-licences")
    licences = manager.load_licences_from_folder(licences_folder_path)
    licence_uid = "CCI-data-policy-for-satellite-surface-radiation-budget"
    licence_md = {
        "licence_id": 1,
        "licence_uid": "CCI-data-policy-for-satellite-surface-radiation-budget",
        "revision": 4,
        "title": "CCI product licence",
        "download_filename": "an url",
    }
    storage_settings = config.ObjectStorageSettings(**my_settings_dict)
    patch = mocker.patch(
        "cads_catalogue.object_storage.store_file",
        return_value=("an url", "a version"),
    )
    # start without any licence in the db
    with session_obj() as session:
        manager.licence_sync(session, licence_uid, licences, storage_settings)
        session.commit()
        db_licences = session.query(database.Licence).all()
        assert len(db_licences) == 1
        assert utils.object_as_dict(db_licences[0]) == licence_md

    assert patch.call_count == 1
    assert (
        os.path.join(
            licences_folder_path,
            "CCI-data-policy-for-satellite-surface-radiation-budget.pdf",
        ),
        storage_settings.object_storage_url,
    ) in [pm.args for pm in patch.mock_calls]

    assert {
        "bucket_name": "mycatalogue_bucket",
        "subpath": "licences/CCI-data-policy-for-satellite-surface-radiation-budget",
        "force": True,
        "access_key": "admin1",
        "secret_key": "secret1",
        "secure": False,
    } in [pm.kwargs for pm in patch.mock_calls]
    patch.reset_mock()

    # update an existing licence
    updated_licence = [r for r in licences if r["licence_uid"] == licence_uid][0]
    updated_licence["title"] = "CCI product licence UPDATED"
    licence_md2 = {
        "licence_id": 1,
        "licence_uid": "CCI-data-policy-for-satellite-surface-radiation-budget",
        "revision": 4,
        "title": "CCI product licence UPDATED",
        "download_filename": "an url",
    }
    licences = [updated_licence]
    with session_obj() as session:
        manager.licence_sync(session, licence_uid, licences, storage_settings)
        session.commit()
        db_licences = session.query(database.Licence).all()
        assert len(db_licences) == 1
        assert utils.object_as_dict(db_licences[0]) == licence_md2

    # reset globals for tests following
    config.dbsettings = None
    config.storagesettings = None


def test_resource_sync(
    session_obj: sessionmaker, mocker: pytest_mock.MockerFixture
) -> None:
    my_settings_dict = {
        "object_storage_url": "object/storage/url",
        "storage_admin": "admin1",
        "storage_password": "secret1",
        "catalogue_bucket": "mycatalogue_bucket",
        "document_storage_url": "my/url",
    }
    storage_settings = config.ObjectStorageSettings(**my_settings_dict)
    patch = mocker.patch.object(
        object_storage, "store_file", return_value=("an url", "a version")
    )
    spy1 = mocker.spy(manager, "manage_upload_images_and_layout")
    resource_folder_path = os.path.join(
        TESTDATA_PATH, "cads-forms-json", "reanalysis-era5-land"
    )
    resource = manager.load_resource_from_folder(resource_folder_path)
    # start without any licence in the db
    with session_obj() as session:
        with pytest.raises(ValueError):
            manager.resource_sync(session, resource, storage_settings)
    assert patch.call_count == 0
    patch.reset_mock()

    # store licences
    licences_folder_path = os.path.join(TESTDATA_PATH, "cds-licences")
    licences = manager.load_licences_from_folder(licences_folder_path)
    with session_obj() as session:
        for licence in licences:
            licence_uid = licence["licence_uid"]
            manager.licence_sync(session, licence_uid, licences, storage_settings)
        session.commit()
        db_licences = session.execute(
            "select licence_uid, licence_id from licences order by licence_uid"
        ).all()
        uid_id_licence_map = dict(db_licences)
    patch.reset_mock()

    # create first dataset
    with session_obj() as session:
        manager.resource_sync(session, resource, storage_settings)
        session.commit()

    assert patch.call_count == 5
    expected_args_object_storage_calls = [
        (
            os.path.join(resource_folder_path, "overview.png"),
            storage_settings.object_storage_url,
        ),
        (mocker.ANY, storage_settings.object_storage_url),
        (
            os.path.join(resource_folder_path, "constraints.json"),
            storage_settings.object_storage_url,
        ),
        (
            os.path.join(resource_folder_path, "form.json"),
            storage_settings.object_storage_url,
        ),
        (
            os.path.join(resource_folder_path, "overview.png"),
            storage_settings.object_storage_url,
        ),
    ]
    effective_args_object_storage_calls = [pm.args for pm in patch.mock_calls]
    for expected_args_object_storage_call in expected_args_object_storage_calls:
        assert expected_args_object_storage_call in effective_args_object_storage_calls
    assert effective_args_object_storage_calls[1][0].endswith("layout.json")
    assert {
        "bucket_name": "mycatalogue_bucket",
        "subpath": "resources/reanalysis-era5-land",
        "force": True,
        "access_key": "admin1",
        "secret_key": "secret1",
        "secure": False,
    } in [pm.kwargs for pm in patch.mock_calls]
    spy1.assert_called_once()
    patch.reset_mock()

    # create second dataset
    resource_folder_path2 = os.path.join(
        TESTDATA_PATH, "cads-forms-json", "reanalysis-era5-land-monthly-means"
    )
    resource2 = manager.load_resource_from_folder(resource_folder_path2)
    with session_obj() as session:
        manager.resource_sync(session, resource2, storage_settings)
        session.commit()

    with session_obj() as session:
        all_db_resources = session.query(database.Resource).all()
        utils.compare_resources_with_dumped_file(
            all_db_resources,
            os.path.join(TESTDATA_PATH, "dumped_resources2.txt"),
        )
        assert session.execute(
            "select resource_id, licence_id "
            "from resources_licences "
            "order by resource_id, licence_id"
        ).all() == [
            (1, uid_id_licence_map["licence-to-use-copernicus-products"]),
            (2, uid_id_licence_map["licence-to-use-copernicus-products"]),
        ]
        assert session.execute(
            "select parent_resource_id, child_resource_id "
            "from related_resources "
            "order by parent_resource_id"
        ).all() == [(1, 2), (2, 1)]

    # modify second dataset
    resource2["keywords"] = [
        #  "Product type: Reanalysis",   # removed
        "Spatial coverage: Global",
        "Temporal coverage: Past",
        "Variable domain: Land (hydrology)",
        "Variable domain: Land (physics)",
        "Variable domain: Land (biosphere)",
        "Provider: Copernicus C3S",
    ]
    resource2["licence_uids"] = [
        "licence-to-use-copernicus-products",
        "eumetsat-cm-saf",  # added
    ]
    resource2["ds_contactemail"] = "a_new_test@email"
    with session_obj() as session:
        manager.resource_sync(session, resource2, storage_settings)
        session.commit()

    with session_obj() as session:
        all_db_resources = session.query(database.Resource).all()
        utils.compare_resources_with_dumped_file(
            all_db_resources,
            os.path.join(TESTDATA_PATH, "dumped_resources3.txt"),
        )
        assert session.execute(
            "select resource_id, licence_id "
            "from resources_licences "
            "order by resource_id, licence_id"
        ).all() == [
            (1, uid_id_licence_map["licence-to-use-copernicus-products"]),
            (2, uid_id_licence_map["eumetsat-cm-saf"]),
            (2, uid_id_licence_map["licence-to-use-copernicus-products"]),
        ]
        assert session.execute(
            "select parent_resource_id, child_resource_id "
            "from related_resources "
            "order by parent_resource_id"
        ).all() == [(1, 2)]

    # reset globals for tests following
    config.dbsettings = None
    config.storagesettings = None
