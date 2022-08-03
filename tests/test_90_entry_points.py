import datetime
import os.path
from pathlib import Path
from typing import Any

import sqlalchemy as sa
from psycopg import Connection
from sqlalchemy.orm import sessionmaker
from typer.testing import CliRunner

from cads_catalogue import database, entry_points, manager

THIS_PATH = os.path.abspath(os.path.dirname(__file__))
TESTDATA_PATH = os.path.join(THIS_PATH, "data")
runner = CliRunner()


def test_init_db(postgresql: Connection[str]) -> None:
    connection_string = (
        f"postgresql://{postgresql.info.user}:"
        f"@{postgresql.info.host}:{postgresql.info.port}/{postgresql.info.dbname}"
    )
    engine = sa.create_engine(connection_string)
    conn = engine.connect()
    query = (
        "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
    )
    result = runner.invoke(
        entry_points.app, ["init-db", "--connection-string", connection_string]
    )

    assert result.exit_code == 0
    assert set(conn.execute(query).scalars()) == set(database.metadata.tables)  # type: ignore


def test_setup_test_database(postgresql: Connection[str], tmp_path: Path) -> None:
    connection_string = (
        f"postgresql://{postgresql.info.user}:"
        f"@{postgresql.info.host}:{postgresql.info.port}/{postgresql.info.dbname}"
    )
    engine = sa.create_engine(connection_string)
    session_obj = sessionmaker(engine)
    expected_licences = [
        {
            "download_filename": (
                "licences/licence-to-use-copernicus-products/"
                "licence-to-use-copernicus-products.pdf"
            ),
            "licence_id": 1,
            "licence_uid": "licence-to-use-copernicus-products",
            "revision": 12,
            "title": "Licence to use Copernicus Products",
        }
    ]
    expected_resources: list[dict[str, Any]] = [
        {
            "abstract": "ERA5-Land is a reanalysis dataset providing a consistent view of "
            "the evolution of land variables over several decades at an "
            "enhanced resolution compared to ERA5. ERA5-Land has been "
            "produced by replaying the land component of the ECMWF ERA5 "
            "climate reanalysis. Reanalysis combines model data with "
            "observations from across the world into a globally complete and "
            "consistent dataset using the laws of physics. Reanalysis "
            "produces data that goes several decades back in time, providing "
            "an accurate description of the climate of the past. \n"
            "\n"
            "ERA5-Land uses as input to control the simulated land fields "
            "ERA5 atmospheric variables, such as air temperature and air "
            "humidity. This is called the atmospheric forcing. Without the "
            "constraint of the atmospheric forcing, the model-based estimates "
            "can rapidly deviate from reality. Therefore, while observations "
            "are not directly used in the production of ERA5-Land, they have "
            "an indirect influence through the atmospheric forcing used to "
            "run the simulation. In addition, the input air temperature, air "
            "humidity and pressure used to run ERA5-Land are corrected to "
            "account for the altitude difference between the grid of the "
            "forcing and the higher resolution grid of ERA5-Land. This "
            "correction is called 'lapse rate correction'.    \n"
            "\n"
            "The ERA5-Land dataset, as any other simulation, provides "
            "estimates which have some degree of uncertainty. Numerical "
            "models can only provide a more or less accurate representation "
            "of the real physical processes governing different components of "
            "the Earth System. In general, the uncertainty of model estimates "
            "grows as we go back in time, because the number of observations "
            "available to create a good quality atmospheric forcing is lower. "
            "ERA5-land parameter fields can currently be used in combination "
            "with the uncertainty of the equivalent ERA5 fields. \n"
            "\n"
            "The temporal and spatial resolutions of ERA5-Land makes this "
            "dataset very useful for all kind of land surface applications "
            "such as flood or drought forecasting. The temporal and spatial "
            "resolution of this dataset, the period covered in time, as well "
            "as the fixed grid used for the data distribution at any period "
            "enables decisions makers, businesses and individuals to access "
            "and use more accurate information on land states.\n"
            "\n"
            "\n",
            "constraints": "resources/reanalysis-era5-land/constraints.json",
            "contact": None,
            "description": {
                "data-type": "Gridded",
                "file-format": "GRIB",
                "horizontal-coverage": "Global",
                "horizontal-resolution": "0.1° x 0.1°; Native resolution is 9 " "km.",
                "projection": "Regular latitude-longitude grid",
                "temporal-coverage": "January 1950 to present",
                "temporal-resolution": "Hourly",
                "update-frequency": "Monthly with a delay of about three "
                "months relatively to actual date.",
                "vertical-coverage": "From 2 m above the surface level, to a "
                "soil depth of 289 cm.\n",
                "vertical-resolution": "4 levels of the ECMWF surface model: "
                "Layer 1: 0 -7cm, Layer 2: 7 -28cm, "
                "Layer 3: 28-100cm, Layer 4: "
                "100-289cm\n"
                "Some parameters are defined at 2 m "
                "over the surface.\n",
            },
            "documentation": [
                {
                    "description": "Further and more detailed information "
                    "relating to the ERA5-Land dataset can be "
                    "found in the Copernicus Knowledge Base web "
                    "link above.",
                    "title": "ERA5-Land online documentation",
                    "url": "https://confluence.ecmwf.int/display/CKB/ERA5-Land%"
                    "3A+data+documentation",
                }
            ],
            "doi": "10.24381/cds.e2161bac",
            "extent": None,
            "form": "resources/reanalysis-era5-land/form.json",
            "keywords": [
                "Product type: Reanalysis",
                "Spatial coverage: Global",
                "Temporal coverage: Past",
                "Variable domain: Land (hydrology)",
                "Variable domain: Land (physics)",
                "Variable domain: Land (biosphere)",
                "Provider: Copernicus C3S",
            ],
            "previewimage": "resources/reanalysis-era5-land/overview.png",
            "providers": None,
            "publication_date": datetime.date(2019, 7, 12),
            "record_update": datetime.datetime(
                2022,
                7,
                13,
                9,
                11,
                30,
                50535,
                tzinfo=datetime.timezone(datetime.timedelta(seconds=7200)),
            ),
            "references": [
                {
                    "content": "resources/reanalysis-era5-land/citation.html",
                    "copy": True,
                    "download_file": None,
                    "title": "Citation",
                    "url": None,
                },
            ],
            "resource_id": 3,
            "resource_uid": "reanalysis-era5-land",
            "resource_update": datetime.date(2022, 3, 14),
            "summaries": None,
            "title": "ERA5-Land hourly data from 1950 to present",
            "type": "dataset",
            "use_eqc": True,
            "version": None,
            "variables": {
                "10m u-component of wind": {
                    "description": "Eastward component "
                    "of the 10m wind. It "
                    "is the horizontal "
                    "speed of air moving "
                    "towards the east, "
                    "at a height of ten "
                    "metres above the "
                    "surface of the "
                    "Earth, in metres "
                    "per second. Care "
                    "should be taken "
                    "when comparing this "
                    "variable with "
                    "observations, "
                    "because wind "
                    "observations vary "
                    "on small space and "
                    "time scales and are "
                    "affected by the "
                    "local terrain, "
                    "vegetation and "
                    "buildings that are "
                    "represented only on "
                    "average in the "
                    "ECMWF Integrated "
                    "Forecasting System. "
                    "This variable can "
                    "be combined with "
                    "the V component of "
                    "10m wind to give "
                    "the speed and "
                    "direction of the "
                    "horizontal 10m "
                    "wind.",
                    "units": "m s^-1",
                },
                "10m v-component of wind": {
                    "description": "Northward component "
                    "of the 10m wind. It "
                    "is the horizontal "
                    "speed of air moving "
                    "towards the north, "
                    "at a height of ten "
                    "metres above the "
                    "surface of the "
                    "Earth, in metres "
                    "per second. Care "
                    "should be taken "
                    "when comparing this "
                    "variable with "
                    "observations, "
                    "because wind "
                    "observations vary "
                    "on small space and "
                    "time scales and are "
                    "affected by the "
                    "local terrain, "
                    "vegetation and "
                    "buildings that are "
                    "represented only on "
                    "average in the "
                    "ECMWF Integrated "
                    "Forecasting System. "
                    "This variable can "
                    "be combined with "
                    "the U component of "
                    "10m wind to give "
                    "the speed and "
                    "direction of the "
                    "horizontal 10m "
                    "wind.",
                    "units": "m s^-1",
                },
                "2m dewpoint temperature": {
                    "description": "Temperature to "
                    "which the air, at 2 "
                    "metres above the "
                    "surface of the "
                    "Earth, would have "
                    "to be cooled for "
                    "saturation to "
                    "occur.It is a "
                    "measure of the "
                    "humidity of the "
                    "air. Combined with "
                    "temperature and "
                    "pressure, it can be "
                    "used to calculate "
                    "the relative "
                    "humidity. 2m dew "
                    "point temperature "
                    "is calculated by "
                    "interpolating "
                    "between the lowest "
                    "model level and the "
                    "Earth's surface, "
                    "taking account of "
                    "the atmospheric "
                    "conditions. "
                    "Temperature "
                    "measured in kelvin "
                    "can be converted to "
                    "degrees Celsius "
                    "(°C) by subtracting "
                    "273.15.",
                    "units": "K",
                },
                "2m temperature": {
                    "description": "Temperature of air at 2m "
                    "above the surface of land, "
                    "sea or in-land waters. 2m "
                    "temperature is calculated by "
                    "interpolating between the "
                    "lowest model level and the "
                    "Earth's surface, taking "
                    "account of the atmospheric "
                    "conditions. Temperature "
                    "measured in kelvin can be "
                    "converted to degrees Celsius "
                    "(°C) by subtracting 273.15.",
                    "units": "K",
                },
                "Evaporation from bare soil": {
                    "description": "The amount of "
                    "evaporation from "
                    "bare soil at the "
                    "top of the land "
                    "surface. This "
                    "variable is "
                    "accumulated from "
                    "the beginning of "
                    "the forecast "
                    "time to the end "
                    "of the forecast "
                    "step.",
                    "units": "m of water equivalent",
                },
                "Evaporation from open water surfaces excluding oceans": {
                    "description": "Amount "
                    "of "
                    "evaporation "
                    "from "
                    "surface "
                    "water "
                    "storage "
                    "like "
                    "lakes "
                    "and "
                    "inundated "
                    "areas "
                    "but "
                    "excluding "
                    "oceans. "
                    "This "
                    "variable "
                    "is "
                    "accumulated "
                    "from "
                    "the "
                    "beginning "
                    "of "
                    "the "
                    "forecast "
                    "time "
                    "to "
                    "the "
                    "end "
                    "of "
                    "the "
                    "forecast "
                    "step.",
                    "units": "m " "of " "water " "equivalent",
                },
                "Evaporation from the top of canopy": {
                    "description": "The "
                    "amount "
                    "of "
                    "evaporation "
                    "from the "
                    "canopy "
                    "interception "
                    "reservoir "
                    "at the "
                    "top of "
                    "the "
                    "canopy. "
                    "This "
                    "variable "
                    "is "
                    "accumulated "
                    "from the "
                    "beginning "
                    "of the "
                    "forecast "
                    "time to "
                    "the end "
                    "of the "
                    "forecast "
                    "step.",
                    "units": "m of water " "equivalent",
                },
                "Evaporation from vegetation transpiration": {
                    "description": "Amount "
                    "of "
                    "evaporation "
                    "from "
                    "vegetation "
                    "transpiration. "
                    "This "
                    "has "
                    "the "
                    "same "
                    "meaning "
                    "as "
                    "root "
                    "extraction "
                    "i.e. "
                    "the "
                    "amount "
                    "of "
                    "water "
                    "extracted "
                    "from "
                    "the "
                    "different "
                    "soil "
                    "layers. "
                    "This "
                    "variable "
                    "is "
                    "accumulated "
                    "from "
                    "the "
                    "beginning "
                    "of "
                    "the "
                    "forecast "
                    "time "
                    "to "
                    "the "
                    "end "
                    "of "
                    "the "
                    "forecast "
                    "step.",
                    "units": "m of " "water " "equivalent",
                },
                "Forecast albedo": {
                    "description": "Is a measure of the "
                    "reflectivity of the Earth's "
                    "surface. It is the fraction "
                    "of solar (shortwave) "
                    "radiation reflected by "
                    "Earth's surface, across the "
                    "solar spectrum, for both "
                    "direct and diffuse "
                    "radiation. Values are "
                    "between 0 and 1. Typically, "
                    "snow and ice have high "
                    "reflectivity with albedo "
                    "values of 0.8 and above, "
                    "land has intermediate "
                    "values between about 0.1 "
                    "and 0.4 and the ocean has "
                    "low values of 0.1 or less. "
                    "Radiation from the Sun "
                    "(solar, or shortwave, "
                    "radiation) is partly "
                    "reflected back to space by "
                    "clouds and particles in the "
                    "atmosphere (aerosols) and "
                    "some of it is absorbed. The "
                    "rest is incident on the "
                    "Earth's surface, where some "
                    "of it is reflected. The "
                    "portion that is reflected "
                    "by the Earth's surface "
                    "depends on the albedo. In "
                    "the ECMWF Integrated "
                    "Forecasting System (IFS), a "
                    "climatological background "
                    "albedo (observed values "
                    "averaged over a period of "
                    "several years) is used, "
                    "modified by the model over "
                    "water, ice and snow. Albedo "
                    "is often shown as a "
                    "percentage (%).",
                    "units": "dimensionless",
                },
                "Lake bottom temperature": {
                    "description": "Temperature of "
                    "water at the bottom "
                    "of inland water "
                    "bodies (lakes, "
                    "reservoirs, rivers) "
                    "and coastal waters. "
                    "ECMWF implemented a "
                    "lake model in May "
                    "2015 to represent "
                    "the water "
                    "temperature and "
                    "lake ice of all the "
                    "world’s major "
                    "inland water bodies "
                    "in the Integrated "
                    "Forecasting System. "
                    "The model keeps "
                    "lake depth and "
                    "surface area (or "
                    "fractional cover) "
                    "constant in time.",
                    "units": "K",
                },
                "Lake ice depth": {
                    "description": "The thickness of ice on "
                    "inland water bodies (lakes, "
                    "reservoirs and rivers) and "
                    "coastal waters. The ECMWF "
                    "Integrated Forecasting "
                    "System (IFS) represents the "
                    "formation and melting of ice "
                    "on inland water bodies "
                    "(lakes, reservoirs and "
                    "rivers) and coastal water. A "
                    "single ice layer is "
                    "represented. This parameter "
                    "is the thickness of that ice "
                    "layer.",
                    "units": "m",
                },
                "Lake ice temperature": {
                    "description": "The temperature of the "
                    "uppermost surface of "
                    "ice on inland water "
                    "bodies (lakes, "
                    "reservoirs, rivers) "
                    "and coastal waters. "
                    "The ECMWF Integrated "
                    "Forecasting System "
                    "represents the "
                    "formation and melting "
                    "of ice on lakes. A "
                    "single ice layer is "
                    "represented. The "
                    "temperature measured "
                    "in kelvin can be "
                    "converted to degrees "
                    "Celsius (°C) by "
                    "subtracting 273.15.",
                    "units": "K",
                },
                "Lake mix-layer depth": {
                    "description": "The thickness of the "
                    "upper most layer of an "
                    "inland water body "
                    "(lake, reservoirs, and "
                    "rivers) or coastal "
                    "waters that is well "
                    "mixed and has a near "
                    "constant temperature "
                    "with depth (uniform "
                    "distribution of "
                    "temperature). The "
                    "ECMWF Integrated "
                    "Forecasting System "
                    "represents inland "
                    "water bodies with two "
                    "layers in the "
                    "vertical, the mixed "
                    "layer above and the "
                    "thermocline below. "
                    "Thermoclines upper "
                    "boundary is located at "
                    "the mixed layer "
                    "bottom, and the lower "
                    "boundary at the lake "
                    "bottom. Mixing within "
                    "the mixed layer can "
                    "occur when the density "
                    "of the surface (and "
                    "near-surface) water is "
                    "greater than that of "
                    "the water below. "
                    "Mixing can also occur "
                    "through the action of "
                    "wind on the surface of "
                    "the lake.",
                    "units": "m",
                },
                "Lake mix-layer temperature": {
                    "description": "The temperature "
                    "of the upper "
                    "most layer of "
                    "inland water "
                    "bodies (lakes, "
                    "reservoirs and "
                    "rivers) or "
                    "coastal waters) "
                    "that is well "
                    "mixed. The ECMWF "
                    "Integrated "
                    "Forecasting "
                    "System "
                    "represents "
                    "inland water "
                    "bodies with two "
                    "layers in the "
                    "vertical, the "
                    "mixed layer "
                    "above and the "
                    "thermocline "
                    "below. "
                    "Thermoclines "
                    "upper boundary "
                    "is located at "
                    "the mixed layer "
                    "bottom, and the "
                    "lower boundary "
                    "at the lake "
                    "bottom. Mixing "
                    "within the mixed "
                    "layer can occur "
                    "when the density "
                    "of the surface "
                    "(and "
                    "near-surface) "
                    "water is greater "
                    "than that of the "
                    "water below. "
                    "Mixing can also "
                    "occur through "
                    "the action of "
                    "wind on the "
                    "surface of the "
                    "lake. "
                    "Temperature "
                    "measured in "
                    "kelvin can be "
                    "converted to "
                    "degrees Celsius "
                    "(°C) by "
                    "subtracting "
                    "273.15.",
                    "units": "K",
                },
                "Lake shape factor": {
                    "description": "This parameter describes "
                    "the way that temperature "
                    "changes with depth in the "
                    "thermocline layer of "
                    "inland water bodies "
                    "(lakes, reservoirs and "
                    "rivers) and coastal "
                    "waters. It is used to "
                    "calculate the lake bottom "
                    "temperature and other "
                    "lake-related parameters. "
                    "The ECMWF Integrated "
                    "Forecasting System "
                    "represents inland and "
                    "coastal water bodies with "
                    "two layers in the "
                    "vertical, the mixed layer "
                    "above and the thermocline "
                    "below where temperature "
                    "changes with depth.",
                    "units": "dimensionless",
                },
                "Lake total layer temperature": {
                    "description": "The mean "
                    "temperature of "
                    "total water "
                    "column in "
                    "inland water "
                    "bodies (lakes, "
                    "reservoirs and "
                    "rivers) and "
                    "coastal "
                    "waters. The "
                    "ECMWF "
                    "Integrated "
                    "Forecasting "
                    "System "
                    "represents "
                    "inland water "
                    "bodies with "
                    "two layers in "
                    "the vertical, "
                    "the mixed "
                    "layer above "
                    "and the "
                    "thermocline "
                    "below where "
                    "temperature "
                    "changes with "
                    "depth. This "
                    "parameter is "
                    "the mean over "
                    "the two "
                    "layers. "
                    "Temperature "
                    "measured in "
                    "kelvin can be "
                    "converted to "
                    "degrees "
                    "Celsius (°C) "
                    "by subtracting "
                    "273.15.",
                    "units": "K",
                },
                "Leaf area index, high vegetation": {
                    "description": "One-half "
                    "of the "
                    "total "
                    "green leaf "
                    "area per "
                    "unit "
                    "horizontal "
                    "ground "
                    "surface "
                    "area for "
                    "high "
                    "vegetation "
                    "type.",
                    "units": "m^2 m^-2",
                },
                "Leaf area index, low vegetation": {
                    "description": "One-half of "
                    "the total "
                    "green leaf "
                    "area per "
                    "unit "
                    "horizontal "
                    "ground "
                    "surface "
                    "area for "
                    "low "
                    "vegetation "
                    "type.",
                    "units": "m^2 m^-2",
                },
                "Potential evaporation": {
                    "description": "Potential evaporation "
                    "(pev) in the current "
                    "ECMWF model is "
                    "computed, by making a "
                    "second call to the "
                    "surface energy "
                    "balance routine with "
                    "the vegetation "
                    "variables set to "
                    '"crops/mixed farming" '
                    "and assuming no "
                    "stress from soil "
                    "moisture. In other "
                    "words, evaporation is "
                    "computed for "
                    "agricultural land as "
                    "if it is well watered "
                    "and assuming that the "
                    "atmosphere is not "
                    "affected by this "
                    "artificial surface "
                    "condition. The latter "
                    "may not always be "
                    "realistic. Although "
                    "pev is meant to "
                    "provide an estimate "
                    "of irrigation "
                    "requirements, the "
                    "method can give "
                    "unrealistic results "
                    "in arid conditions "
                    "due to too strong "
                    "evaporation forced by "
                    "dry air. Note that in "
                    "ERA5-Land pev is "
                    "computed as an open "
                    "water evaporation "
                    "(Pan evaporation) and "
                    "assuming that the "
                    "atmosphere is not "
                    "affected by this "
                    "artificial surface "
                    "condition. The latter "
                    "is different  from "
                    "the way pev is "
                    "computed in ERA5. "
                    "This variable is "
                    "accumulated from the "
                    "beginning of the "
                    "forecast time to the "
                    "end of the forecast "
                    "step.",
                    "units": "m",
                },
                "Runoff": {
                    "description": "Some water from rainfall, melting "
                    "snow, or deep in the soil, stays "
                    "stored in the soil. Otherwise, the "
                    "water drains away, either over the "
                    "surface (surface runoff), or under "
                    "the ground (sub-surface runoff) and "
                    "the sum of these two is simply "
                    "called 'runoff'. This variable is "
                    "the total amount of water "
                    "accumulated from the beginning of "
                    "the forecast time to the end of the "
                    "forecast step. The units of runoff "
                    "are depth in metres. This is the "
                    "depth the water would have if it "
                    "were spread evenly over the grid "
                    "box. Care should be taken when "
                    "comparing model variables with "
                    "observations, because observations "
                    "are often local to a particular "
                    "point rather than averaged over a "
                    "grid square area.  Observations are "
                    "also often taken in different units, "
                    "such as mm/day, rather than the "
                    "accumulated metres produced here. "
                    "Runoff is a measure of the "
                    "availability of water in the soil, "
                    "and can, for example, be used as an "
                    "indicator of drought or flood. More "
                    "information about how runoff is "
                    "calculated is given in the IFS "
                    "Physical Processes documentation.",
                    "units": "m",
                },
                "Skin reservoir content": {
                    "description": "Amount of water in "
                    "the vegetation "
                    "canopy and/or in a "
                    "thin layer on the "
                    "soil. It represents "
                    "the amount of rain "
                    "intercepted by "
                    "foliage, and water "
                    "from dew. The "
                    "maximum amount of "
                    "'skin reservoir "
                    "content' a grid box "
                    "can hold depends on "
                    "the type of "
                    "vegetation, and may "
                    "be zero.  Water "
                    "leaves the 'skin "
                    "reservoir' by "
                    "evaporation.",
                    "units": "m of water equivalent",
                },
                "Skin temperature": {
                    "description": "Temperature of the surface "
                    "of the Earth. The skin "
                    "temperature is the "
                    "theoretical temperature "
                    "that is required to "
                    "satisfy the surface energy "
                    "balance. It represents the "
                    "temperature of the "
                    "uppermost surface layer, "
                    "which has no heat capacity "
                    "and so can respond "
                    "instantaneously to changes "
                    "in surface fluxes. Skin "
                    "temperature is calculated "
                    "differently over land and "
                    "sea. Temperature measured "
                    "in kelvin can be converted "
                    "to degrees Celsius (°C) by "
                    "subtracting 273.15.",
                    "units": "K",
                },
                "Snow albedo": {
                    "description": "It is defined as the fraction "
                    "of solar (shortwave) radiation "
                    "reflected by the snow, across "
                    "the solar spectrum, for both "
                    "direct and diffuse radiation. "
                    "It is a measure of the "
                    "reflectivity of the snow "
                    "covered grid cells. Values vary "
                    "between 0 and 1. Typically, "
                    "snow and ice have high "
                    "reflectivity with albedo values "
                    "of 0.8 and above.",
                    "units": "dimensionless",
                },
                "Snow cover": {
                    "description": "It represents the fraction (0-1) "
                    "of the cell / grid-box occupied "
                    "by snow (similar to the cloud "
                    "cover fields of ERA5).",
                    "units": "%",
                },
                "Snow density": {
                    "description": "Mass of snow per cubic metre "
                    "in the snow layer. The ECMWF "
                    "Integrated Forecast System "
                    "(IFS) model represents snow as "
                    "a single additional layer over "
                    "the uppermost soil level. The "
                    "snow may cover all or part of "
                    "the grid box.",
                    "units": "kg m^-3",
                },
                "Snow depth": {
                    "description": "Instantaneous grib-box average "
                    "of the snow thickness on the "
                    "ground (excluding snow on "
                    "canopy).",
                    "units": "m",
                },
                "Snow depth water equivalent": {
                    "description": "Depth of snow "
                    "from the "
                    "snow-covered "
                    "area of a grid "
                    "box. Its units "
                    "are metres of "
                    "water "
                    "equivalent, so "
                    "it is the depth "
                    "the water would "
                    "have if the "
                    "snow melted and "
                    "was spread "
                    "evenly over the "
                    "whole grid box. "
                    "The ECMWF "
                    "Integrated "
                    "Forecast System "
                    "represents snow "
                    "as a single "
                    "additional "
                    "layer over the "
                    "uppermost soil "
                    "level. The snow "
                    "may cover all "
                    "or part of the "
                    "grid box.",
                    "units": "m of water " "equivalent",
                },
                "Snow evaporation": {
                    "description": "Evaporation from snow "
                    "averaged over the grid box "
                    "(to find flux over snow, "
                    "divide by snow fraction). "
                    "This variable is "
                    "accumulated from the "
                    "beginning of the forecast "
                    "time to the end of the "
                    "forecast step.",
                    "units": "m of water equivalent",
                },
                "Snowfall": {
                    "description": "Accumulated total snow that has "
                    "fallen to the Earth's surface. It "
                    "consists of snow due to the "
                    "large-scale atmospheric flow "
                    "(horizontal scales greater than "
                    "around a few hundred metres) and "
                    "convection where smaller scale "
                    "areas (around 5km to a few hundred "
                    "kilometres) of warm air rise. If "
                    "snow has melted during the period "
                    "over which this variable was "
                    "accumulated, then it will be "
                    "higher than the snow depth. This "
                    "variable is the total amount of "
                    "water accumulated from the "
                    "beginning of the forecast time to "
                    "the end of the forecast step. The "
                    "units given measure the depth the "
                    "water would have if the snow "
                    "melted and was spread evenly over "
                    "the grid box. Care should be taken "
                    "when comparing model variables "
                    "with observations, because "
                    "observations are often local to a "
                    "particular point in space and "
                    "time, rather than representing "
                    "averages over a model grid box and "
                    "model time step.",
                    "units": "m of water equivalent",
                },
                "Snowmelt": {
                    "description": "Melting of snow averaged over the "
                    "grid box (to find melt over snow, "
                    "divide by snow fraction). This "
                    "variable is accumulated from the "
                    "beginning of the forecast time to "
                    "the end of the forecast step.",
                    "units": "m of water equivalent",
                },
                "Soil temperature level 1": {
                    "description": "Temperature of the "
                    "soil in layer 1 (0 "
                    "- 7 cm) of the "
                    "ECMWF Integrated "
                    "Forecasting "
                    "System. The "
                    "surface is at 0 "
                    "cm. Soil "
                    "temperature is set "
                    "at the middle of "
                    "each layer, and "
                    "heat transfer is "
                    "calculated at the "
                    "interfaces between "
                    "them. It is "
                    "assumed that there "
                    "is no heat "
                    "transfer out of "
                    "the bottom of the "
                    "lowest layer. "
                    "Temperature "
                    "measured in kelvin "
                    "can be converted "
                    "to degrees Celsius "
                    "(°C) by "
                    "subtracting "
                    "273.15.",
                    "units": "K",
                },
                "Soil temperature level 2": {
                    "description": "Temperature of the "
                    "soil in layer 2 (7 "
                    "-28cm) of the "
                    "ECMWF Integrated "
                    "Forecasting "
                    "System.",
                    "units": "K",
                },
                "Soil temperature level 3": {
                    "description": "Temperature of the "
                    "soil in layer 3 "
                    "(28-100cm) of the "
                    "ECMWF Integrated "
                    "Forecasting "
                    "System.",
                    "units": "K",
                },
                "Soil temperature level 4": {
                    "description": "Temperature of the "
                    "soil in layer 4 "
                    "(100-289 cm) of "
                    "the ECMWF "
                    "Integrated "
                    "Forecasting "
                    "System.",
                    "units": "K",
                },
                "Sub-surface runoff": {
                    "description": "Some water from "
                    "rainfall, melting snow, "
                    "or deep in the soil, "
                    "stays stored in the "
                    "soil. Otherwise, the "
                    "water drains away, "
                    "either over the surface "
                    "(surface runoff), or "
                    "under the ground "
                    "(sub-surface runoff) and "
                    "the sum of these two is "
                    "simply called 'runoff'. "
                    "This variable is "
                    "accumulated from the "
                    "beginning of the "
                    "forecast time to the end "
                    "of the forecast step. "
                    "The units of runoff are "
                    "depth in metres. This is "
                    "the depth the water "
                    "would have if it were "
                    "spread evenly over the "
                    "grid box. Care should be "
                    "taken when comparing "
                    "model variables with "
                    "observations, because "
                    "observations are often "
                    "local to a particular "
                    "point rather than "
                    "averaged over a grid "
                    "square area.  "
                    "Observations are also "
                    "often taken in different "
                    "units, such as mm/day, "
                    "rather than the "
                    "accumulated metres "
                    "produced here. Runoff is "
                    "a measure of the "
                    "availability of water in "
                    "the soil, and can, for "
                    "example, be used as an "
                    "indicator of drought or "
                    "flood. More information "
                    "about how runoff is "
                    "calculated is given in "
                    "the IFS Physical "
                    "Processes documentation.",
                    "units": "m",
                },
                "Surface latent heat flux": {
                    "description": "Exchange of latent "
                    "heat with the "
                    "surface through "
                    "turbulent "
                    "diffusion. This "
                    "variables is "
                    "accumulated from "
                    "the beginning of "
                    "the forecast time "
                    "to the end of the "
                    "forecast step. By "
                    "model convention, "
                    "downward fluxes "
                    "are positive.",
                    "units": "J m^-2",
                },
                "Surface net solar radiation": {
                    "description": "Amount of solar "
                    "radiation (also "
                    "known as "
                    "shortwave "
                    "radiation) "
                    "reaching the "
                    "surface of the "
                    "Earth (both "
                    "direct and "
                    "diffuse) minus "
                    "the amount "
                    "reflected by "
                    "the Earth's "
                    "surface (which "
                    "is governed by "
                    "the "
                    "albedo).Radiation "
                    "from the Sun "
                    "(solar, or "
                    "shortwave, "
                    "radiation) is "
                    "partly "
                    "reflected back "
                    "to space by "
                    "clouds and "
                    "particles in "
                    "the atmosphere "
                    "(aerosols) and "
                    "some of it is "
                    "absorbed. The "
                    "rest is "
                    "incident on the "
                    "Earth's "
                    "surface, where "
                    "some of it is "
                    "reflected. The "
                    "difference "
                    "between "
                    "downward and "
                    "reflected solar "
                    "radiation is "
                    "the surface net "
                    "solar "
                    "radiation. This "
                    "variable is "
                    "accumulated "
                    "from the "
                    "beginning of "
                    "the forecast "
                    "time to the end "
                    "of the forecast "
                    "step. The units "
                    "are joules per "
                    "square metre (J "
                    "m^-2). To "
                    "convert to "
                    "watts per "
                    "square metre (W "
                    "m^-2), the "
                    "accumulated "
                    "values should "
                    "be divided by "
                    "the "
                    "accumulation "
                    "period "
                    "expressed in "
                    "seconds. The "
                    "ECMWF "
                    "convention for "
                    "vertical fluxes "
                    "is positive "
                    "downwards.",
                    "units": "J m^-2",
                },
                "Surface net thermal radiation": {
                    "description": "Net thermal "
                    "radiation at "
                    "the surface. "
                    "Accumulated "
                    "field from "
                    "the beginning "
                    "of the "
                    "forecast time "
                    "to the end of "
                    "the forecast "
                    "step. By "
                    "model "
                    "convention "
                    "downward "
                    "fluxes are "
                    "positive.",
                    "units": "J m^-2",
                },
                "Surface pressure": {
                    "description": "Pressure (force per unit "
                    "area) of the atmosphere on "
                    "the surface of land, sea "
                    "and in-land water. It is a "
                    "measure of the weight of "
                    "all the air in a column "
                    "vertically above the area "
                    "of the Earth's surface "
                    "represented at a fixed "
                    "point. Surface pressure is "
                    "often used in combination "
                    "with temperature to "
                    "calculate air density. The "
                    "strong variation of "
                    "pressure with altitude "
                    "makes it difficult to see "
                    "the low and high pressure "
                    "systems over mountainous "
                    "areas, so mean sea level "
                    "pressure, rather than "
                    "surface pressure, is "
                    "normally used for this "
                    "purpose. The units of this "
                    "variable are Pascals (Pa). "
                    "Surface pressure is often "
                    "measured in hPa and "
                    "sometimes is presented in "
                    "the old units of "
                    "millibars, mb (1 hPa = 1 "
                    "mb = 100 Pa).",
                    "units": "Pa",
                },
                "Surface runoff": {
                    "description": "Some water from rainfall, "
                    "melting snow, or deep in the "
                    "soil, stays stored in the "
                    "soil. Otherwise, the water "
                    "drains away, either over the "
                    "surface (surface runoff), or "
                    "under the ground "
                    "(sub-surface runoff) and the "
                    "sum of these two is simply "
                    "called 'runoff'. This "
                    "variable is the total amount "
                    "of water accumulated from "
                    "the beginning of the "
                    "forecast time to the end of "
                    "the forecast step. The units "
                    "of runoff are depth in "
                    "metres. This is the depth "
                    "the water would have if it "
                    "were spread evenly over the "
                    "grid box. Care should be "
                    "taken when comparing model "
                    "variables with observations, "
                    "because observations are "
                    "often local to a particular "
                    "point rather than averaged "
                    "over a grid square area. "
                    "Observations are also often "
                    "taken in different units, "
                    "such as mm/day, rather than "
                    "the accumulated metres "
                    "produced here. Runoff is a "
                    "measure of the availability "
                    "of water in the soil, and "
                    "can, for example, be used as "
                    "an indicator of drought or "
                    "flood. More information "
                    "about how runoff is "
                    "calculated is given in the "
                    "IFS Physical Processes "
                    "documentation.",
                    "units": "m",
                },
                "Surface sensible heat flux": {
                    "description": "Transfer of heat "
                    "between the "
                    "Earth's surface "
                    "and the "
                    "atmosphere "
                    "through the "
                    "effects of "
                    "turbulent air "
                    "motion (but "
                    "excluding any "
                    "heat transfer "
                    "resulting from "
                    "condensation or "
                    "evaporation). "
                    "The magnitude of "
                    "the sensible "
                    "heat flux is "
                    "governed by the "
                    "difference in "
                    "temperature "
                    "between the "
                    "surface and the "
                    "overlying "
                    "atmosphere, wind "
                    "speed and the "
                    "surface "
                    "roughness. For "
                    "example, cold "
                    "air overlying a "
                    "warm surface "
                    "would produce a "
                    "sensible heat "
                    "flux from the "
                    "land (or ocean) "
                    "into the "
                    "atmosphere. This "
                    "is a single "
                    "level variable "
                    "and it is "
                    "accumulated from "
                    "the beginning of "
                    "the forecast "
                    "time to the end "
                    "of the forecast "
                    "step. The units "
                    "are joules per "
                    "square metre (J "
                    "m^-2). To "
                    "convert to watts "
                    "per square metre "
                    "(W m^-2), the "
                    "accumulated "
                    "values should be "
                    "divided by the "
                    "accumulation "
                    "period expressed "
                    "in seconds. The "
                    "ECMWF convention "
                    "for vertical "
                    "fluxes is "
                    "positive "
                    "downwards.",
                    "units": "J m^-2",
                },
                "Surface solar radiation downwards": {
                    "description": "Amount of "
                    "solar "
                    "radiation "
                    "(also "
                    "known as "
                    "shortwave "
                    "radiation) "
                    "reaching "
                    "the "
                    "surface "
                    "of the "
                    "Earth. "
                    "This "
                    "variable "
                    "comprises "
                    "both "
                    "direct "
                    "and "
                    "diffuse "
                    "solar "
                    "radiation. "
                    "Radiation "
                    "from the "
                    "Sun "
                    "(solar, "
                    "or "
                    "shortwave, "
                    "radiation) "
                    "is partly "
                    "reflected "
                    "back to "
                    "space by "
                    "clouds "
                    "and "
                    "particles "
                    "in the "
                    "atmosphere "
                    "(aerosols) "
                    "and some "
                    "of it is "
                    "absorbed.  "
                    "The rest "
                    "is "
                    "incident "
                    "on the "
                    "Earth's "
                    "surface "
                    "(represented "
                    "by this "
                    "variable). "
                    "To a "
                    "reasonably "
                    "good "
                    "approximation, "
                    "this "
                    "variable "
                    "is the "
                    "model "
                    "equivalent "
                    "of what "
                    "would be "
                    "measured "
                    "by a "
                    "pyranometer "
                    "(an "
                    "instrument "
                    "used for "
                    "measuring "
                    "solar "
                    "radiation) "
                    "at the "
                    "surface. "
                    "However, "
                    "care "
                    "should be "
                    "taken "
                    "when "
                    "comparing "
                    "model "
                    "variables "
                    "with "
                    "observations, "
                    "because "
                    "observations "
                    "are often "
                    "local to "
                    "a "
                    "particular "
                    "point in "
                    "space and "
                    "time, "
                    "rather "
                    "than "
                    "representing "
                    "averages "
                    "over a  "
                    "model "
                    "grid box "
                    "and model "
                    "time "
                    "step. "
                    "This "
                    "variable "
                    "is "
                    "accumulated "
                    "from the "
                    "beginning "
                    "of the "
                    "forecast "
                    "time to "
                    "the end "
                    "of the "
                    "forecast "
                    "step. The "
                    "units are "
                    "joules "
                    "per "
                    "square "
                    "metre (J "
                    "m^-2). To "
                    "convert "
                    "to watts "
                    "per "
                    "square "
                    "metre (W "
                    "m^-2), "
                    "the "
                    "accumulated "
                    "values "
                    "should be "
                    "divided "
                    "by the "
                    "accumulation "
                    "period "
                    "expressed "
                    "in "
                    "seconds. "
                    "The ECMWF "
                    "convention "
                    "for "
                    "vertical "
                    "fluxes is "
                    "positive "
                    "downwards.",
                    "units": "J m-2",
                },
                "Surface thermal radiation downwards": {
                    "description": "Amount "
                    "of "
                    "thermal "
                    "(also "
                    "known "
                    "as "
                    "longwave "
                    "or "
                    "terrestrial) "
                    "radiation "
                    "emitted "
                    "by the "
                    "atmosphere "
                    "and "
                    "clouds "
                    "that "
                    "reaches "
                    "the "
                    "Earth's "
                    "surface. "
                    "The "
                    "surface "
                    "of the "
                    "Earth "
                    "emits "
                    "thermal "
                    "radiation, "
                    "some of "
                    "which "
                    "is "
                    "absorbed "
                    "by the "
                    "atmosphere "
                    "and "
                    "clouds. "
                    "The "
                    "atmosphere "
                    "and "
                    "clouds "
                    "likewise "
                    "emit "
                    "thermal "
                    "radiation "
                    "in all "
                    "directions, "
                    "some of "
                    "which "
                    "reaches "
                    "the "
                    "surface "
                    "(represented "
                    "by this "
                    "variable). "
                    "This "
                    "variable "
                    "is "
                    "accumulated "
                    "from "
                    "the "
                    "beginning "
                    "of the "
                    "forecast "
                    "time to "
                    "the end "
                    "of the "
                    "forecast "
                    "step. "
                    "The "
                    "units "
                    "are "
                    "joules "
                    "per "
                    "square "
                    "metre "
                    "(J "
                    "m^-2). "
                    "To "
                    "convert "
                    "to "
                    "watts "
                    "per "
                    "square "
                    "metre "
                    "(W "
                    "m^-2), "
                    "the "
                    "accumulated "
                    "values "
                    "should "
                    "be "
                    "divided "
                    "by the "
                    "accumulation "
                    "period "
                    "expressed "
                    "in "
                    "seconds. "
                    "The "
                    "ECMWF "
                    "convention "
                    "for "
                    "vertical "
                    "fluxes "
                    "is "
                    "positive "
                    "downwards.",
                    "units": "J m-2",
                },
                "Temperature of snow layer": {
                    "description": "This variable "
                    "gives the "
                    "temperature of "
                    "the snow layer "
                    "from the ground "
                    "to the snow-air "
                    "interface. The "
                    "ECMWF Integrated "
                    "Forecast System "
                    "(IFS) model "
                    "represents snow "
                    "as a single "
                    "additional layer "
                    "over the "
                    "uppermost soil "
                    "level. The snow "
                    "may cover all or "
                    "part of the  grid "
                    "box. Temperature "
                    "measured in "
                    "kelvin can be "
                    "converted to "
                    "degrees Celsius "
                    "(°C) by "
                    "subtracting "
                    "273.15.",
                    "units": "K",
                },
                "Total evaporation": {
                    "description": "Accumulated amount of "
                    "water that has evaporated "
                    "from the Earth's surface, "
                    "including a simplified "
                    "representation of "
                    "transpiration (from "
                    "vegetation), into vapour "
                    "in the air above. This "
                    "variable is accumulated "
                    "from the beginning of the "
                    "forecast to the end of "
                    "the forecast step. The "
                    "ECMWF Integrated "
                    "Forecasting System "
                    "convention is that "
                    "downward fluxes are "
                    "positive. Therefore, "
                    "negative values indicate "
                    "evaporation and positive "
                    "values indicate "
                    "condensation.",
                    "units": "m of water equivalent",
                },
                "Total precipitation": {
                    "description": "Accumulated liquid and "
                    "frozen water, including "
                    "rain and snow, that "
                    "falls to the Earth's "
                    "surface. It is the sum "
                    "of large-scale "
                    "precipitation (that "
                    "precipitation which is "
                    "generated by "
                    "large-scale weather "
                    "patterns, such as "
                    "troughs and cold "
                    "fronts) and convective "
                    "precipitation "
                    "(generated by "
                    "convection which occurs "
                    "when air at lower "
                    "levels in the "
                    "atmosphere is warmer "
                    "and less dense than the "
                    "air above, so it "
                    "rises). Precipitation "
                    "variables do not "
                    "include fog, dew or the "
                    "precipitation that "
                    "evaporates in the "
                    "atmosphere before it "
                    "lands at the surface of "
                    "the Earth. This "
                    "variable is accumulated "
                    "from the beginning of "
                    "the forecast time to "
                    "the end of the forecast "
                    "step. The units of "
                    "precipitation are depth "
                    "in metres. It is the "
                    "depth the water would "
                    "have if it were spread "
                    "evenly over the grid "
                    "box. Care should be "
                    "taken when comparing "
                    "model variables with "
                    "observations, because "
                    "observations are often "
                    "local to a particular "
                    "point in space and "
                    "time, rather than "
                    "representing averages "
                    "over a model grid box "
                    "and  model time step.",
                    "units": "m",
                },
                "Volumetric soil water layer 1": {
                    "description": "Volume of "
                    "water in soil "
                    "layer 1 (0 - "
                    "7 cm) of the "
                    "ECMWF "
                    "Integrated "
                    "Forecasting "
                    "System. The "
                    "surface is at "
                    "0 cm. The "
                    "volumetric "
                    "soil water is "
                    "associated "
                    "with the soil "
                    "texture (or "
                    "classification), "
                    "soil depth, "
                    "and the "
                    "underlying "
                    "groundwater "
                    "level.",
                    "units": "m^3 m^-3",
                },
                "Volumetric soil water layer 2": {
                    "description": "Volume of "
                    "water in soil "
                    "layer 2 (7 "
                    "-28 cm) of "
                    "the ECMWF "
                    "Integrated "
                    "Forecasting "
                    "System.",
                    "units": "m^3 m^-3",
                },
                "Volumetric soil water layer 3": {
                    "description": "Volume of "
                    "water in soil "
                    "layer 3 "
                    "(28-100 cm) "
                    "of the ECMWF "
                    "Integrated "
                    "Forecasting "
                    "System.",
                    "units": "m^3 m^-3",
                },
                "Volumetric soil water layer 4": {
                    "description": "Volume of "
                    "water in soil "
                    "layer 4 "
                    "(100-289 cm) "
                    "of the ECMWF "
                    "Integrated "
                    "Forecasting "
                    "System.",
                    "units": "m^3 m^-3",
                },
            },
        },
        {
            "abstract": (
                "ERA5-Land is a reanalysis dataset providing a consistent view of the"
                " evolution of land variables over several decades at an enhanced"
                " resolution compared to ERA5. ERA5-Land has been produced by replaying"
                " the land component of the ECMWF ERA5 climate reanalysis. Reanalysis"
                " combines model data with observations from across the world into a"
                " globally complete and consistent dataset using the laws of physics."
                " Reanalysis produces data that goes several decades back in time,"
                " providing an accurate description of the climate of the"
                " past.\n\nERA5-Land provides a consistent view of the water and energy"
                " cycles at surface level during several decades.\nIt contains a"
                " detailed record from 1950 onwards, with a temporal resolution of 1"
                " hour. The native spatial resolution of the ERA5-Land reanalysis"
                " dataset is 9km on a reduced Gaussian grid (TCo1279). The data in the"
                " CDS has been regridded to a regular lat-lon grid of 0.1x0.1"
                " degrees.\n\nThe data presented here is a post-processed subset of the"
                " full ERA5-Land dataset. Monthly-mean averages have been"
                " pre-calculated to facilitate many applications requiring easy and"
                " fast access to the data, when sub-monthly fields are not"
                " required.\n\nHourly fields can be found in the [ERA5-Land hourly"
                " fields CDS"
                " page](https://cds-dev.copernicus-climate.eu/cdsapp#!/dataset/"
                "reanalysis-era5-land?tab=overview"
                ' "ERA5-Land hourly data"). Documentation can be found in the [online'
                " ERA5-Land"
                " documentation](https://confluence.ecmwf.int/display/CKB/"
                "ERA5-Land+data+documentation"
                ' "ERA5-Land data documentation").\n'
            ),
            "constraints": (
                "resources/reanalysis-era5-land-monthly-means/constraints.json"
            ),
            "contact": None,
            "description": {
                "data-type": "Gridded",
                "projection": "Regular latitude-longitude grid",
                "file-format": "GRIB",
                "update-frequency": (
                    "Monthly with a delay of 2-3 months relatively to the actual date."
                ),
                "temporal-coverage": "January 1950 to present",
                "vertical-coverage": (
                    "From 2 m above the surface level, to a soil depth of 289 cm.\n"
                ),
                "horizontal-coverage": "Global",
                "temporal-resolution": "Monthly",
                "vertical-resolution": (
                    "4 levels of the ECMWF surface model: Layer 1: 0 -7cm, Layer 2: 7"
                    " -28cm, Layer 3: 28-100cm, Layer 4: 100-289cm\nSome parameters are"
                    " defined at 2 m over the surface.\n"
                ),
                "horizontal-resolution": "0.1° x 0.1°; Native resolution is 9 km.",
            },
            "documentation": [
                {
                    "url": "https://confluence.ecmwf.int/display/"
                    "CKB/ERA5-Land%3A+data+documentation",
                    "title": "ERA5-Land online documentation",
                    "description": (
                        "Further and more detailed information relating to the"
                        " ERA5-Land dataset can be found in the Copernicus Knowledge"
                        " Base web link above."
                    ),
                }
            ],
            "doi": "10.24381/cds.68d2bb30",
            "extent": None,
            "form": "resources/reanalysis-era5-land-monthly-means/form.json",
            "keywords": [
                "Product type: Reanalysis",
                "Spatial coverage: Global",
                "Temporal coverage: Past",
                "Variable domain: Land (hydrology)",
                "Variable domain: Land (physics)",
                "Variable domain: Land (biosphere)",
                "Provider: Copernicus C3S",
            ],
            "previewimage": "resources/reanalysis-era5-land-monthly-means/overview.png",
            "providers": None,
            "publication_date": datetime.date(2019, 6, 23),
            "record_update": datetime.datetime(
                2022,
                7,
                6,
                12,
                22,
                8,
                307930,
                tzinfo=datetime.timezone(datetime.timedelta(seconds=7200)),
            ),
            "references": [
                {
                    "title": "Citation",
                    "content": "resources/reanalysis-era5-land-monthly-means/citation.html",
                    "copy": True,
                    "url": None,
                    "download_file": None,
                },
            ],
            "resource_id": 1,
            "resource_uid": "reanalysis-era5-land-monthly-means",
            "resource_update": datetime.date(2022, 3, 2),
            "summaries": None,
            "title": "ERA5-Land monthly averaged data from 1950 to present",
            "type": "dataset",
            "use_eqc": True,
            "variables": {
                "Runoff": {
                    "units": "m",
                    "description": (
                        "Some water from rainfall, melting snow, or deep in the soil,"
                        " stays stored in the soil. Otherwise, the water drains away,"
                        " either over the surface (surface runoff), or under the ground"
                        " (sub-surface runoff) and the sum of these two is simply"
                        " called 'runoff'. This variable is the total amount of water"
                        " accumulated from the beginning of the forecast time to the"
                        " end of the forecast step. The units of runoff are depth in"
                        " metres. This is the depth the water would have if it were"
                        " spread evenly over the grid box. Care should be taken when"
                        " comparing model variables with observations, because"
                        " observations are often local to a particular point rather"
                        " than averaged over a grid square area.  Observations are also"
                        " often taken in different units, such as mm/day, rather than"
                        " the accumulated metres produced here. Runoff is a measure of"
                        " the availability of water in the soil, and can, for example,"
                        " be used as an indicator of drought or flood. More information"
                        " about how runoff is calculated is given in the IFS Physical"
                        " Processes documentation."
                    ),
                },
                "Snowfall": {
                    "units": "m of water equivalent",
                    "description": (
                        "Accumulated total snow that has fallen to the Earth's surface."
                        " It consists of snow due to the large-scale atmospheric flow"
                        " (horizontal scales greater than around a few hundred metres)"
                        " and convection where smaller scale areas (around 5km to a few"
                        " hundred kilometres) of warm air rise. If snow has melted"
                        " during the period over which this variable was accumulated,"
                        " then it will be higher than the snow depth. This variable is"
                        " the total amount of water accumulated from the beginning of"
                        " the forecast time to the end of the forecast step. The units"
                        " given measure the depth the water would have if the snow"
                        " melted and was spread evenly over the grid box. Care should"
                        " be taken when comparing model variables with observations,"
                        " because observations are often local to a particular point in"
                        " space and time, rather than representing averages over a"
                        " model grid box and model time step."
                    ),
                },
                "Snowmelt": {
                    "units": "m of water equivalent",
                    "description": (
                        "Melting of snow averaged over the grid box (to find melt over"
                        " snow, divide by snow fraction). This variable is accumulated"
                        " from the beginning of the forecast time to the end of the"
                        " forecast step."
                    ),
                },
                "Snow cover": {
                    "units": "%",
                    "description": (
                        "It represents the fraction (0-1) of the cell / grid-box"
                        " occupied by snow (similar to the cloud cover fields of ERA5)."
                    ),
                },
                "Snow depth": {
                    "units": "m",
                    "description": (
                        "Instantaneous grib-box average of the snow thickness on the"
                        " ground (excluding snow on canopy)."
                    ),
                },
                "Snow albedo": {
                    "units": "dimensionless",
                    "description": (
                        "It is defined as the fraction of solar (shortwave) radiation"
                        " reflected by the snow, across the solar spectrum, for both"
                        " direct and diffuse radiation. It is a measure of the"
                        " reflectivity of the snow covered grid cells. Values vary"
                        " between 0 and 1. Typically, snow and ice have high"
                        " reflectivity with albedo values of 0.8 and above."
                    ),
                },
                "Snow density": {
                    "units": "kg m^-3",
                    "description": (
                        "Mass of snow per cubic metre in the snow layer. The ECMWF"
                        " Integrated Forecast System (IFS) model represents snow as a"
                        " single additional layer over the uppermost soil level. The"
                        " snow may cover all or part of the grid box."
                    ),
                },
                "2m temperature": {
                    "units": "K",
                    "description": (
                        "Temperature of air at 2m above the surface of land, sea or"
                        " in-land waters. 2m temperature is calculated by interpolating"
                        " between the lowest model level and the Earth's surface,"
                        " taking account of the atmospheric conditions. Temperature"
                        " measured in kelvin can be converted to degrees Celsius (°C)"
                        " by subtracting 273.15."
                    ),
                },
                "Lake ice depth": {
                    "units": "m",
                    "description": (
                        "The thickness of ice on inland water bodies (lakes, reservoirs"
                        " and rivers) and coastal waters. The ECMWF Integrated"
                        " Forecasting System (IFS) represents the formation and melting"
                        " of ice on inland water bodies (lakes, reservoirs and rivers)"
                        " and coastal water. A single ice layer is represented. This"
                        " parameter is the thickness of that ice layer."
                    ),
                },
                "Surface runoff": {
                    "units": "m",
                    "description": (
                        "Some water from rainfall, melting snow, or deep in the soil,"
                        " stays stored in the soil. Otherwise, the water drains away,"
                        " either over the surface (surface runoff), or under the ground"
                        " (sub-surface runoff) and the sum of these two is simply"
                        " called 'runoff'. This variable is the total amount of water"
                        " accumulated from the beginning of the forecast time to the"
                        " end of the forecast step. The units of runoff are depth in"
                        " metres. This is the depth the water would have if it were"
                        " spread evenly over the grid box. Care should be taken when"
                        " comparing model variables with observations, because"
                        " observations are often local to a particular point rather"
                        " than averaged over a grid square area. Observations are also"
                        " often taken in different units, such as mm/day, rather than"
                        " the accumulated metres produced here. Runoff is a measure of"
                        " the availability of water in the soil, and can, for example,"
                        " be used as an indicator of drought or flood. More information"
                        " about how runoff is calculated is given in the IFS Physical"
                        " Processes documentation."
                    ),
                },
                "Forecast albedo": {
                    "units": "dimensionless",
                    "description": (
                        "Is a measure of the reflectivity of the Earth's surface. It is"
                        " the fraction of solar (shortwave) radiation reflected by"
                        " Earth's surface, across the solar spectrum, for both direct"
                        " and diffuse radiation. Values are between 0 and 1. Typically,"
                        " snow and ice have high reflectivity with albedo values of 0.8"
                        " and above, land has intermediate values between about 0.1 and"
                        " 0.4 and the ocean has low values of 0.1 or less. Radiation"
                        " from the Sun (solar, or shortwave, radiation) is partly"
                        " reflected back to space by clouds and particles in the"
                        " atmosphere (aerosols) and some of it is absorbed. The rest is"
                        " incident on the Earth's surface, where some of it is"
                        " reflected. The portion that is reflected by the Earth's"
                        " surface depends on the albedo. In the ECMWF Integrated"
                        " Forecasting System (IFS), a climatological background albedo"
                        " (observed values averaged over a period of several years) is"
                        " used, modified by the model over water, ice and snow. Albedo"
                        " is often shown as a percentage (%)."
                    ),
                },
                "Skin temperature": {
                    "units": "K",
                    "description": (
                        "Temperature of the surface of the Earth. The skin temperature"
                        " is the theoretical temperature that is required to satisfy"
                        " the surface energy balance. It represents the temperature of"
                        " the uppermost surface layer, which has no heat capacity and"
                        " so can respond instantaneously to changes in surface fluxes."
                        " Skin temperature is calculated differently over land and sea."
                        " Temperature measured in kelvin can be converted to degrees"
                        " Celsius (°C) by subtracting 273.15."
                    ),
                },
                "Snow evaporation": {
                    "units": "m of water equivalent",
                    "description": (
                        "Evaporation from snow averaged over the grid box (to find flux"
                        " over snow, divide by snow fraction). This variable is"
                        " accumulated from the beginning of the forecast time to the"
                        " end of the forecast step."
                    ),
                },
                "Surface pressure": {
                    "units": "Pa",
                    "description": (
                        "Pressure (force per unit area) of the atmosphere on the"
                        " surface of land, sea and in-land water. It is a measure of"
                        " the weight of all the air in a column vertically above the"
                        " area of the Earth's surface represented at a fixed point."
                        " Surface pressure is often used in combination with"
                        " temperature to calculate air density. The strong variation of"
                        " pressure with altitude makes it difficult to see the low and"
                        " high pressure systems over mountainous areas, so mean sea"
                        " level pressure, rather than surface pressure, is normally"
                        " used for this purpose. The units of this variable are Pascals"
                        " (Pa). Surface pressure is often measured in hPa and sometimes"
                        " is presented in the old units of millibars, mb (1 hPa = 1 mb"
                        " = 100 Pa)."
                    ),
                },
                "Lake shape factor": {
                    "units": "dimensionless",
                    "description": (
                        "This parameter describes the way that temperature changes with"
                        " depth in the thermocline layer of inland water bodies (lakes,"
                        " reservoirs and rivers) and coastal waters. It is used to"
                        " calculate the lake bottom temperature and other lake-related"
                        " parameters. The ECMWF Integrated Forecasting System"
                        " represents inland and coastal water bodies with two layers in"
                        " the vertical, the mixed layer above and the thermocline below"
                        " where temperature changes with depth."
                    ),
                },
                "Total evaporation": {
                    "units": "m of water equivalent",
                    "description": (
                        "Accumulated amount of water that has evaporated from the"
                        " Earth's surface, including a simplified representation of"
                        " transpiration (from vegetation), into vapour in the air"
                        " above. This variable is accumulated from the beginning of the"
                        " forecast to the end of the forecast step. The ECMWF"
                        " Integrated Forecasting System convention is that downward"
                        " fluxes are positive. Therefore, negative values indicate"
                        " evaporation and positive values indicate condensation."
                    ),
                },
                "Sub-surface runoff": {
                    "units": "m",
                    "description": (
                        "Some water from rainfall, melting snow, or deep in the soil,"
                        " stays stored in the soil. Otherwise, the water drains away,"
                        " either over the surface (surface runoff), or under the ground"
                        " (sub-surface runoff) and the sum of these two is simply"
                        " called 'runoff'. This variable is accumulated from the"
                        " beginning of the forecast time to the end of the forecast"
                        " step. The units of runoff are depth in metres. This is the"
                        " depth the water would have if it were spread evenly over the"
                        " grid box. Care should be taken when comparing model variables"
                        " with observations, because observations are often local to a"
                        " particular point rather than averaged over a grid square"
                        " area.  Observations are also often taken in different units,"
                        " such as mm/day, rather than the accumulated metres produced"
                        " here. Runoff is a measure of the availability of water in the"
                        " soil, and can, for example, be used as an indicator of"
                        " drought or flood. More information about how runoff is"
                        " calculated is given in the IFS Physical Processes"
                        " documentation."
                    ),
                },
                "Total precipitation": {
                    "units": "m",
                    "description": (
                        "Accumulated liquid and frozen water, including rain and snow,"
                        " that falls to the Earth's surface. It is the sum of"
                        " large-scale precipitation (that precipitation which is"
                        " generated by large-scale weather patterns, such as troughs"
                        " and cold fronts) and convective precipitation (generated by"
                        " convection which occurs when air at lower levels in the"
                        " atmosphere is warmer and less dense than the air above, so it"
                        " rises). Precipitation variables do not include fog, dew or"
                        " the precipitation that evaporates in the atmosphere before it"
                        " lands at the surface of the Earth. This variable is"
                        " accumulated from the beginning of the forecast time to the"
                        " end of the forecast step. The units of precipitation are"
                        " depth in metres. It is the depth the water would have if it"
                        " were spread evenly over the grid box. Care should be taken"
                        " when comparing model variables with observations, because"
                        " observations are often local to a particular point in space"
                        " and time, rather than representing averages over a model grid"
                        " box and  model time step."
                    ),
                },
                "Lake ice temperature": {
                    "units": "K",
                    "description": (
                        "The temperature of the uppermost surface of ice on inland"
                        " water bodies (lakes, reservoirs, rivers) and coastal waters."
                        " The ECMWF Integrated Forecasting System represents the"
                        " formation and melting of ice on lakes. A single ice layer is"
                        " represented. The temperature measured in kelvin can be"
                        " converted to degrees Celsius (°C) by subtracting 273.15."
                    ),
                },
                "Lake mix-layer depth": {
                    "units": "m",
                    "description": (
                        "The thickness of the upper most layer of an inland water body"
                        " (lake, reservoirs, and rivers) or coastal waters that is well"
                        " mixed and has a near constant temperature with depth (uniform"
                        " distribution of temperature). The ECMWF Integrated"
                        " Forecasting System represents inland water bodies with two"
                        " layers in the vertical, the mixed layer above and the"
                        " thermocline below. Thermoclines upper boundary is located at"
                        " the mixed layer bottom, and the lower boundary at the lake"
                        " bottom. Mixing within the mixed layer can occur when the"
                        " density of the surface (and near-surface) water is greater"
                        " than that of the water below. Mixing can also occur through"
                        " the action of wind on the surface of the lake."
                    ),
                },
                "Potential evaporation": {
                    "units": "m",
                    "description": (
                        "Potential evaporation (pev) in the current ECMWF model is"
                        " computed, by making a second call to the surface energy"
                        " balance routine with the vegetation variables set to"
                        ' "crops/mixed farming" and assuming no stress from soil'
                        " moisture. In other words, evaporation is computed for"
                        " agricultural land as if it is well watered and assuming that"
                        " the atmosphere is not affected by this artificial surface"
                        " condition. The latter may not always be realistic. Although"
                        " pev is meant to provide an estimate of irrigation"
                        " requirements, the method can give unrealistic results in arid"
                        " conditions due to too strong evaporation forced by dry air."
                        " Note that in ERA5-Land pev is computed as an open water"
                        " evaporation (Pan evaporation) and assuming that the"
                        " atmosphere is not affected by this artificial surface"
                        " condition. The latter is different from the way pev is"
                        " computed in ERA5. This variable is accumulated from the"
                        " beginning of the forecast time to the end of the forecast"
                        " step."
                    ),
                },
                "Skin reservoir content": {
                    "units": "m of water equivalent",
                    "description": (
                        "Amount of water in the vegetation canopy and/or in a thin"
                        " layer on the soil. It represents the amount of rain"
                        " intercepted by foliage, and water from dew. The maximum"
                        " amount of 'skin reservoir content' a grid box can hold"
                        " depends on the type of vegetation, and may be zero.  Water"
                        " leaves the 'skin reservoir' by evaporation."
                    ),
                },
                "10m u-component of wind": {
                    "units": "m s^-1",
                    "description": (
                        "Eastward component of the 10m wind. It is the horizontal speed"
                        " of air moving towards the east, at a height of ten metres"
                        " above the surface of the Earth, in metres per second. Care"
                        " should be taken when comparing this variable with"
                        " observations, because wind observations vary on small space"
                        " and time scales and are affected by the local terrain,"
                        " vegetation and buildings that are represented only on average"
                        " in the ECMWF Integrated Forecasting System. This variable can"
                        " be combined with the V component of 10m wind to give the"
                        " speed and direction of the horizontal 10m wind."
                    ),
                },
                "10m v-component of wind": {
                    "units": "m s^-1",
                    "description": (
                        "Northward component of the 10m wind. It is the horizontal"
                        " speed of air moving towards the north, at a height of ten"
                        " metres above the surface of the Earth, in metres per second."
                        " Care should be taken when comparing this variable with"
                        " observations, because wind observations vary on small space"
                        " and time scales and are affected by the local terrain,"
                        " vegetation and buildings that are represented only on average"
                        " in the ECMWF Integrated Forecasting System. This variable can"
                        " be combined with the U component of 10m wind to give the"
                        " speed and direction of the horizontal 10m wind."
                    ),
                },
                "2m dewpoint temperature": {
                    "units": "K",
                    "description": (
                        "Temperature to which the air, at 2 metres above the surface of"
                        " the Earth, would have to be cooled for saturation to occur.It"
                        " is a measure of the humidity of the air. Combined with"
                        " temperature and pressure, it can be used to calculate the"
                        " relative humidity. 2m dew point temperature is calculated by"
                        " interpolating between the lowest model level and the Earth's"
                        " surface, taking account of the atmospheric conditions."
                        " Temperature measured in kelvin can be converted to degrees"
                        " Celsius (°C) by subtracting 273.15."
                    ),
                },
                "Lake bottom temperature": {
                    "units": "K",
                    "description": (
                        "Temperature of water at the bottom of inland water bodies"
                        " (lakes, reservoirs, rivers) and coastal waters. ECMWF"
                        " implemented a lake model in May 2015 to represent the water"
                        " temperature and lake ice of all the world’s major inland"
                        " water bodies in the Integrated Forecasting System. The model"
                        " keeps lake depth and surface area (or fractional cover)"
                        " constant in time."
                    ),
                },
                "Soil temperature level 1": {
                    "units": "K",
                    "description": (
                        "Temperature of the soil in layer 1 (0 - 7 cm) of the ECMWF"
                        " Integrated Forecasting System. The surface is at 0 cm. Soil"
                        " temperature is set at the middle of each layer, and heat"
                        " transfer is calculated at the interfaces between them. It is"
                        " assumed that there is no heat transfer out of the bottom of"
                        " the lowest layer. Temperature measured in kelvin can be"
                        " converted to degrees Celsius (°C) by subtracting 273.15."
                    ),
                },
                "Soil temperature level 2": {
                    "units": "K",
                    "description": (
                        "Temperature of the soil in layer 2 (7 -28cm) of the ECMWF"
                        " Integrated Forecasting System."
                    ),
                },
                "Soil temperature level 3": {
                    "units": "K",
                    "description": (
                        "Temperature of the soil in layer 3 (28-100cm) of the ECMWF"
                        " Integrated Forecasting System."
                    ),
                },
                "Soil temperature level 4": {
                    "units": "K",
                    "description": (
                        "Temperature of the soil in layer 4 (100-289 cm) of the ECMWF"
                        " Integrated Forecasting System."
                    ),
                },
                "Surface latent heat flux": {
                    "units": "J m^-2",
                    "description": (
                        "Exchange of latent heat with the surface through turbulent"
                        " diffusion. This variables is accumulated from the beginning"
                        " of the forecast time to the end of the forecast step. By"
                        " model convention, downward fluxes are positive."
                    ),
                },
                "Temperature of snow layer": {
                    "units": "K",
                    "description": (
                        "This variable gives the temperature of the snow layer from the"
                        " ground to the snow-air interface. The ECMWF Integrated"
                        " Forecast System (IFS) model represents snow as a single"
                        " additional layer over the uppermost soil level. The snow may"
                        " cover all or part of the  grid box. Temperature measured in"
                        " kelvin can be converted to degrees Celsius (°C) by"
                        " subtracting 273.15."
                    ),
                },
                "Evaporation from bare soil": {
                    "units": "m of water equivalent",
                    "description": (
                        "The amount of evaporation from bare soil at the top of the"
                        " land surface. This variable is accumulated from the beginning"
                        " of the forecast time to the end of the forecast step."
                    ),
                },
                "Lake mix-layer temperature": {
                    "units": "K",
                    "description": (
                        "The temperature of the upper most layer of inland water bodies"
                        " (lakes, reservoirs and rivers) or coastal waters) that is"
                        " well mixed. The ECMWF Integrated Forecasting System"
                        " represents inland water bodies with two layers in the"
                        " vertical, the mixed layer above and the thermocline below."
                        " Thermoclines upper boundary is located at the mixed layer"
                        " bottom, and the lower boundary at the lake bottom. Mixing"
                        " within the mixed layer can occur when the density of the"
                        " surface (and near-surface) water is greater than that of the"
                        " water below. Mixing can also occur through the action of wind"
                        " on the surface of the lake. Temperature measured in kelvin"
                        " can be converted to degrees Celsius (°C) by subtracting"
                        " 273.15."
                    ),
                },
                "Surface sensible heat flux": {
                    "units": "J m^-2",
                    "description": (
                        "Transfer of heat between the Earth's surface and the"
                        " atmosphere through the effects of turbulent air motion (but"
                        " excluding any heat transfer resulting from condensation or"
                        " evaporation). The magnitude of the sensible heat flux is"
                        " governed by the difference in temperature between the surface"
                        " and the overlying atmosphere, wind speed and the surface"
                        " roughness. For example, cold air overlying a warm surface"
                        " would produce a sensible heat flux from the land (or ocean)"
                        " into the atmosphere. This is a single level variable and it"
                        " is accumulated from the beginning of the forecast time to the"
                        " end of the forecast step. The units are joules per square"
                        " metre (J m^-2). To convert to watts per square metre (W"
                        " m^-2), the accumulated values should be divided by the"
                        " accumulation period expressed in seconds. The ECMWF"
                        " convention for vertical fluxes is positive downwards."
                    ),
                },
                "Snow depth water equivalent": {
                    "units": "m of water equivalent",
                    "description": (
                        "Depth of snow from the snow-covered area of a grid box. Its"
                        " units are metres of water equivalent, so it is the depth the"
                        " water would have if the snow melted and was spread evenly"
                        " over the whole grid box. The ECMWF Integrated Forecast System"
                        " represents snow as a single additional layer over the"
                        " uppermost soil level. The snow may cover all or part of the"
                        " grid box."
                    ),
                },
                "Surface net solar radiation": {
                    "units": "J m^-2",
                    "description": (
                        "Amount of solar radiation (also known as shortwave radiation)"
                        " reaching the surface of the Earth (both direct and diffuse)"
                        " minus the amount reflected by the Earth's surface (which is"
                        " governed by the albedo).Radiation from the Sun (solar, or"
                        " shortwave, radiation) is partly reflected back to space by"
                        " clouds and particles in the atmosphere (aerosols) and some of"
                        " it is absorbed. The rest is incident on the Earth's surface,"
                        " where some of it is reflected. The difference between"
                        " downward and reflected solar radiation is the surface net"
                        " solar radiation. This variable is accumulated from the"
                        " beginning of the forecast time to the end of the forecast"
                        " step. The units are joules per square metre (J m^-2). To"
                        " convert to watts per square metre (W m^-2), the accumulated"
                        " values should be divided by the accumulation period expressed"
                        " in seconds. The ECMWF convention for vertical fluxes is"
                        " positive downwards."
                    ),
                },
                "Lake total layer temperature": {
                    "units": "K",
                    "description": (
                        "The mean temperature of total water column in inland water"
                        " bodies (lakes, reservoirs and rivers) and coastal waters. The"
                        " ECMWF Integrated Forecasting System represents inland water"
                        " bodies with two layers in the vertical, the mixed layer above"
                        " and the thermocline below where temperature changes with"
                        " depth. This parameter is the mean over the two layers."
                        " Temperature measured in kelvin can be converted to degrees"
                        " Celsius (°C) by subtracting 273.15."
                    ),
                },
                "Surface net thermal radiation": {
                    "units": "J m^-2",
                    "description": (
                        "Net thermal radiation at the surface. Accumulated field from"
                        " the beginning of the forecast time to the end of the forecast"
                        " step. By model convention downward fluxes are positive."
                    ),
                },
                "Volumetric soil water layer 1": {
                    "units": "m^3 m^-3",
                    "description": (
                        "Volume of water in soil layer 1 (0 - 7 cm) of the ECMWF"
                        " Integrated Forecasting System. The surface is at 0 cm. The"
                        " volumetric soil water is associated with the soil texture (or"
                        " classification), soil depth, and the underlying groundwater"
                        " level."
                    ),
                },
                "Volumetric soil water layer 2": {
                    "units": "m^3 m^-3",
                    "description": (
                        "Volume of water in soil layer 2 (7 -28 cm) of the ECMWF"
                        " Integrated Forecasting System."
                    ),
                },
                "Volumetric soil water layer 3": {
                    "units": "m^3 m^-3",
                    "description": (
                        "Volume of water in soil layer 3 (28-100 cm) of the ECMWF"
                        " Integrated Forecasting System."
                    ),
                },
                "Volumetric soil water layer 4": {
                    "units": "m^3 m^-3",
                    "description": (
                        "Volume of water in soil layer 4 (100-289 cm) of the ECMWF"
                        " Integrated Forecasting System."
                    ),
                },
                "Leaf area index, low vegetation": {
                    "units": "m^2 m^-2",
                    "description": (
                        "One-half of the total green leaf area per unit horizontal"
                        " ground surface area for low vegetation type."
                    ),
                },
                "Leaf area index, high vegetation": {
                    "units": "m^2 m^-2",
                    "description": (
                        "One-half of the total green leaf area per unit horizontal"
                        " ground surface area for high vegetation type."
                    ),
                },
                "Surface solar radiation downwards": {
                    "units": "J m-2",
                    "description": (
                        "Amount of solar radiation (also known as shortwave radiation)"
                        " reaching the surface of the Earth. This variable comprises"
                        " both direct and diffuse solar radiation. Radiation from the"
                        " Sun (solar, or shortwave, radiation) is partly reflected back"
                        " to space by clouds and particles in the atmosphere (aerosols)"
                        " and some of it is absorbed.  The rest is incident on the"
                        " Earth's surface (represented by this variable). To a"
                        " reasonably good approximation, this variable is the model"
                        " equivalent of what would be measured by a pyranometer (an"
                        " instrument used for measuring solar radiation) at the"
                        " surface. However, care should be taken when comparing model"
                        " variables with observations, because observations are often"
                        " local to a particular point in space and time, rather than"
                        " representing averages over a  model grid box and model time"
                        " step. This variable is accumulated from the beginning of the"
                        " forecast time to the end of the forecast step. The units are"
                        " joules per square metre (J m^-2). To convert to watts per"
                        " square metre (W m^-2), the accumulated values should be"
                        " divided by the accumulation period expressed in seconds. The"
                        " ECMWF convention for vertical fluxes is positive downwards."
                    ),
                },
                "Evaporation from the top of canopy": {
                    "units": "m of water equivalent",
                    "description": (
                        "The amount of evaporation from the canopy interception"
                        " reservoir at the top of the canopy. This variable is"
                        " accumulated from the beginning of the forecast time to the"
                        " end of the forecast step."
                    ),
                },
                "Surface thermal radiation downwards": {
                    "units": "J m-2",
                    "description": (
                        "Amount of thermal (also known as longwave or terrestrial)"
                        " radiation emitted by the atmosphere and clouds that reaches"
                        " the Earth's surface. The surface of the Earth emits thermal"
                        " radiation, some of which is absorbed by the atmosphere and"
                        " clouds. The atmosphere and clouds likewise emit thermal"
                        " radiation in all directions, some of which reaches the"
                        " surface (represented by this variable). This variable is"
                        " accumulated from the beginning of the forecast time to the"
                        " end of the forecast step. The units are joules per square"
                        " metre (J m^-2). To convert to watts per square metre (W"
                        " m^-2), the accumulated values should be divided by the"
                        " accumulation period expressed in seconds. The ECMWF"
                        " convention for vertical fluxes is positive downwards."
                    ),
                },
                "Evaporation from vegetation transpiration": {
                    "units": "m of water equivalent",
                    "description": (
                        "Amount of evaporation from vegetation transpiration. This has"
                        " the same meaning as root extraction i.e. the amount of water"
                        " extracted from the different soil layers. This variable is"
                        " accumulated from the beginning of the forecast time to the"
                        " end of the forecast step."
                    ),
                },
                "Evaporation from open water surfaces excluding oceans": {
                    "units": "m of water equivalent",
                    "description": (
                        "Amount of evaporation from surface water storage like lakes"
                        " and inundated areas but excluding oceans. This variable is"
                        " accumulated from the beginning of the forecast time to the"
                        " end of the forecast step."
                    ),
                },
            },
            "version": None,
        },
        {
            "abstract": (
                "**ERA5** is the fifth generation ECMWF reanalysis for the global"
                " climate and weather for the past 4 to 7 decades.\nCurrently data is"
                " available from 1950, with Climate Data Store entries for 1950-1978"
                " (preliminary back extension) and from 1959 onwards (final release"
                " plus timely updates, this page).\nERA5 replaces the ERA-Interim"
                " reanalysis.\n\nReanalysis combines model data with observations from"
                " across the world into a globally complete and consistent dataset"
                " using the laws of physics. This principle, called data assimilation,"
                " is based on the method used by numerical weather prediction centres,"
                " where every so many hours (12 hours at ECMWF) a previous forecast is"
                " combined with newly available observations in an optimal way to"
                " produce a new best estimate of the state of the atmosphere, called"
                " analysis, from which an updated, improved forecast is issued."
                " Reanalysis works in the same way, but at reduced resolution to allow"
                " for the provision of a dataset spanning back several decades."
                " Reanalysis does not have the constraint of issuing timely forecasts,"
                " so there is more time to collect observations, and when going further"
                " back in time, to allow for the ingestion of improved versions of the"
                " original observations, which all benefit the quality of the"
                " reanalysis product.\n\nERA5 provides hourly estimates for a large"
                " number of atmospheric, ocean-wave and land-surface quantities.\nAn"
                " uncertainty estimate is sampled by an underlying 10-member"
                " ensemble\nat three-hourly intervals. Ensemble mean and spread have"
                " been pre-computed for convenience.\nSuch uncertainty estimates are"
                " closely related to the information content of the available observing"
                " system which\nhas evolved considerably over time. They also indicate"
                " flow-dependent sensitive areas.\nTo facilitate many climate"
                " applications, monthly-mean averages have been pre-calculated"
                " too,\nthough monthly means are not available for the ensemble mean"
                " and spread.\n\nERA5 is updated daily with a latency of about 5 days."
                " In case that serious flaws are detected in this early release (called"
                " ERA5T), this data could be different from the final release 2 to 3"
                " months later. In case that this occurs users are notified.\n\nThe"
                " data set presented here is a regridded subset of the full ERA5 data"
                " set on native resolution.\nIt is online on spinning disk, which"
                " should ensure fast and easy access.\nIt should satisfy the"
                " requirements for most common applications.\n\nAn overview of all ERA5"
                " datasets can be found in [this"
                " article](https://confluence.ecmwf.int/display/CKB/The+family+of+ERA5+datasets"
                ' "The family of ERA5 datasets").\nInformation on access to ERA5 data'
                " on native resolution is provided in [these"
                " guidelines](https://confluence.ecmwf.int/display/CKB/How+to+download+ERA5"
                ' "How to download ERA5").\n\nData has been regridded to a regular'
                " lat-lon grid of 0.25 degrees for the reanalysis and 0.5 degrees"
                " for\nthe uncertainty estimate (0.5 and 1 degree respectively for"
                " ocean waves).\nThere are four main sub sets: hourly and monthly"
                " products, both on pressure levels (upper air fields) and single"
                " levels (atmospheric, ocean-wave and land surface quantities).\n\nThe"
                ' present entry is "ERA5 hourly data on pressure levels from 1959 to'
                ' present".\n'
            ),
            "constraints": "resources/reanalysis-era5-pressure-levels/constraints.json",
            "contact": None,
            "description": {
                "data-type": "Gridded",
                "projection": "Regular latitude-longitude grid.",
                "file-format": "GRIB",
                "temporal-coverage": "1959 to present",
                "vertical-coverage": "1000 hPa to 1 hPa",
                "horizontal-coverage": "Global",
                "temporal-resolution": "Hourly",
                "vertical-resolution": "37 pressure levels",
                "horizontal-resolution": (
                    "\nReanalysis: 0.25° x 0.25°\n\nMean, spread and members: 0.5° x"
                    " 0.5°"
                ),
            },
            "documentation": [
                {
                    "url": "https://confluence.ecmwf.int/display/CKB/ERA5%3A+data+documentation",
                    "title": "ERA5 data documentation",
                    "description": (
                        "Detailed information relating to the ERA5 data archive can "
                        "be found in the web link above."
                    ),
                },
                {
                    "url": "https://rmets.onlinelibrary.wiley.com/doi/10.1002/qj.4174",
                    "kind": "",
                    "title": (
                        "The ERA5 global reanalysis: Preliminary extension to 1950"
                    ),
                    "description": (
                        "Journal article describing the ERA5 preliminary extension."
                    ),
                },
                {
                    "url": "https://rmets.onlinelibrary.wiley.com/doi/10.1002/qj.3803",
                    "kind": "",
                    "title": "The ERA5 global reanalysis",
                    "description": "Journal article describing ERA5.",
                },
            ],
            "doi": "10.24381/cds.bd0915c6",
            "extent": None,
            "form": "resources/reanalysis-era5-pressure-levels/form.json",
            "keywords": [
                "Variable domain: Atmosphere (surface)",
                "Variable domain: Atmosphere (upper air)",
                "Temporal coverage: Past",
                "Spatial coverage: Global",
                "Product type: Reanalysis",
                "Provider: Copernicus C3S",
            ],
            "previewimage": "resources/reanalysis-era5-pressure-levels/overview.jpg",
            "providers": None,
            "publication_date": None,
            "record_update": datetime.datetime(
                2022,
                7,
                6,
                12,
                22,
                8,
                330625,
                tzinfo=datetime.timezone(datetime.timedelta(seconds=7200)),
            ),
            "references": [
                {
                    "title": "Citation",
                    "content": "resources/reanalysis-era5-pressure-levels/citation.html",
                    "copy": True,
                    "url": None,
                    "download_file": None,
                },
                {
                    "title": "Acknowledgement",
                    "content": "resources/reanalysis-era5-pressure-levels/acknowledgement.html",
                    "copy": None,
                    "url": None,
                    "download_file": None,
                },
            ],
            "resource_id": 2,
            "resource_uid": "reanalysis-era5-pressure-levels",
            "resource_update": datetime.date(2022, 6, 9),
            "summaries": None,
            "title": "ERA5 hourly data on pressure levels from 1959 to present",
            "type": "dataset",
            "use_eqc": True,
            "variables": {
                "Divergence": {
                    "units": "s^-1",
                    "description": (
                        "This parameter is the horizontal divergence of velocity. It is"
                        " the rate at which  air is spreading out horizontally from a"
                        " point, per square metre. This parameter  is positive for air"
                        " that is spreading out, or diverging, and negative for the "
                        " opposite, for air that is concentrating, or converging"
                        " (convergence)."
                    ),
                },
                "Temperature": {
                    "units": "K",
                    "description": (
                        "This parameter is the temperature in the atmosphere.\nIt has"
                        " units of kelvin (K). Temperature measured in kelvin can be"
                        " converted to degrees  Celsius (°C) by subtracting"
                        " 273.15.\nThis parameter is available on multiple levels"
                        " through the atmosphere."
                    ),
                },
                "Geopotential": {
                    "units": "m^2 s^-2",
                    "description": (
                        "This parameter is the gravitational potential energy of a unit"
                        " mass, at a  particular location, relative to mean sea level."
                        " It is also the amount of work  that would have to be done,"
                        " against the force of gravity, to lift a unit mass to  that"
                        " location from mean sea level.\nThe geopotential height can be"
                        " calculated by dividing the geopotential by the  Earth's"
                        " gravitational acceleration, g (=9.80665 m s-2). The"
                        " geopotential height  plays an important role in synoptic"
                        " meteorology (analysis of weather patterns).  Charts of"
                        " geopotential height plotted at constant pressure levels"
                        " (e.g., 300,  500 or 850 hPa) can be used to identify weather"
                        " systems such as cyclones,  anticyclones, troughs and"
                        " ridges.\nAt the surface of the Earth, this parameter shows"
                        " the variations in geopotential  (height) of the surface, and"
                        " is often referred to as the orography."
                    ),
                },
                "Relative humidity": {
                    "units": "%",
                    "description": (
                        "This parameter is the water vapour pressure as a percentage of"
                        " the value at which  the air becomes saturated (the point at"
                        " which water vapour begins to condense into  liquid water or"
                        " deposition into ice).\nFor temperatures over 0°C (273.15 K)"
                        " it is calculated for saturation over water. At  temperatures"
                        " below -23°C it is calculated for saturation over ice. Between"
                        " -23°C  and 0°C this parameter is calculated by interpolating"
                        " between the ice and water  values using a quadratic"
                        " function. "
                    ),
                },
                "Specific humidity": {
                    "units": "kg kg^-1",
                    "description": (
                        "This parameter is the mass of water vapour per kilogram of"
                        " moist air.\nThe total mass of moist air is the sum of the dry"
                        " air, water vapour, cloud liquid,  cloud ice, rain and falling"
                        " snow."
                    ),
                },
                "Vertical velocity": {
                    "units": "Pa s^-1",
                    "description": (
                        "This parameter is the speed of air motion in the upward or"
                        " downward direction. The ECMWF  Integrated Forecasting System"
                        " (IFS) uses a pressure based vertical co-ordinate system and "
                        " pressure decreases with height, therefore negative values of"
                        " vertical velocity indicate  upward motion.\nVertical velocity"
                        " can be useful to understand the large-scale dynamics of the"
                        " atmosphere,  including areas of upward motion/ascent"
                        " (negative values) and downward motion/subsidence  (positive"
                        " values)."
                    ),
                },
                "Potential vorticity": {
                    "units": "K m^2 kg^-1 s^-1",
                    "description": (
                        "Potential vorticity is a measure of the capacity for air to"
                        " rotate in the  atmosphere. If we ignore the effects of"
                        " heating and friction, potential vorticity  is conserved"
                        " following an air parcel. It is used to look for places where"
                        " large  wind storms are likely to originate and develop."
                        " Potential vorticity increases  strongly above the tropopause"
                        " and therefore, it can also be used in studies related  to the"
                        " stratosphere and stratosphere-troposphere exchanges.\nLarge"
                        " wind storms develop when a column of air in the atmosphere"
                        " starts to rotate.  Potential vorticity is calculated from the"
                        " wind, temperature and pressure across a  column of air in the"
                        " atmosphere. "
                    ),
                },
                "U-component of wind": {
                    "units": "m s^-1",
                    "description": (
                        "This parameter is the eastward component of the wind. It is"
                        " the horizontal speed of air  moving towards the east. A"
                        " negative sign indicates air moving towards the west.\nThis"
                        " parameter can be combined with the V component of wind to"
                        " give the speed and  direction of the horizontal wind."
                    ),
                },
                "V-component of wind": {
                    "units": "m s^-1",
                    "description": (
                        "This parameter is the northward component of the wind. It is"
                        " the horizontal speed of air  moving towards the north. A"
                        " negative sign indicates air moving towards the south.\nThis"
                        " parameter can be combined with the U component of wind to"
                        " give the speed and  direction of the horizontal wind."
                    ),
                },
                "Vorticity (relative)": {
                    "units": "s^-1",
                    "description": (
                        "This parameter is a measure of the rotation of air in the"
                        " horizontal, around a vertical  axis, relative to a fixed"
                        " point on the surface of the Earth.\nOn the scale of weather"
                        " systems, troughs (weather features that can include rain) are"
                        "  associated with anticlockwise rotation (in the northern"
                        " hemisphere), and ridges (weather  features that bring light"
                        " or still winds) are associated with clockwise"
                        " rotation.\nAdding the effect of rotation of the Earth, the"
                        " Coriolis parameter, to the relative  vorticity produces the"
                        " absolute vorticity."
                    ),
                },
                "Fraction of cloud cover": {
                    "units": "Dimensionless",
                    "description": (
                        "This parameter is the proportion of a grid box covered by"
                        " cloud (liquid or ice)  and varies between zero and one. This"
                        " parameter is available on multiple levels through the"
                        " atmosphere."
                    ),
                },
                "Ozone mass mixing ratio": {
                    "units": "kg kg^-1",
                    "description": (
                        "This parameter is the mass of ozone per kilogram of air.\nIn"
                        " the ECMWF Integrated Forecasting System (IFS), there is a"
                        " simplified  representation of ozone chemistry (including"
                        " representation of the chemistry  which has caused the ozone"
                        " hole). Ozone is also transported around in the  atmosphere"
                        " through the motion of air.\nNaturally occurring ozone in the"
                        " stratosphere helps protect organisms at the  surface of the"
                        " Earth from the harmful effects of ultraviolet (UV) radiation"
                        " from  the Sun. Ozone near the surface, often produced because"
                        " of pollution, is harmful  to organisms.\nMost of the IFS"
                        " chemical species are archived as mass mixing ratios [kg"
                        " kg-1]."
                    ),
                },
                "Specific rain water content": {
                    "units": "kg kg^-1",
                    "description": (
                        "The mass of water produced from large-scale clouds that is of"
                        " raindrop size and so  can fall to the surface as"
                        " precipitation.\nLarge-scale clouds are generated by the cloud"
                        " scheme in the ECMWF Integrated  Forecasting System (IFS). The"
                        " cloud scheme represents the formation and dissipation  of"
                        " clouds and large-scale precipitation due to changes in"
                        " atmospheric quantities  (such as pressure, temperature and"
                        " moisture) predicted directly by the IFS at spatial  scales of"
                        " a grid box or larger.\nThe quantity is expressed in kilograms"
                        " per kilogram of the total mass of moist air.  The 'total mass"
                        " of moist air' is the sum of the dry air, water vapour, cloud"
                        " liquid,  cloud ice, rain and falling snow. This parameter"
                        " represents the average value for a  grid box.\nClouds contain"
                        " a continuum of different sized water droplets and ice"
                        " particles. The  IFS cloud scheme simplifies this to represent"
                        " a number of discrete cloud  droplets/particles including"
                        " cloud water droplets, raindrops, ice crystals and snow "
                        " (aggregated ice crystals). The processes of droplet"
                        " formation, phase transition and  aggregation are also highly"
                        " simplified in the IFS."
                    ),
                },
                "Specific snow water content": {
                    "units": "kg kg^-1",
                    "description": (
                        "The mass of snow (aggregated ice crystals) produced from"
                        " large-scale clouds that can  fall to the surface as"
                        " precipitation.\nLarge-scale clouds are generated by the cloud"
                        " scheme in the ECMWF Integrated  Forecasting System (IFS). The"
                        " cloud scheme represents the formation and dissipation  of"
                        " clouds and large-scale precipitation due to changes in"
                        " atmospheric quantities (such  as pressure, temperature and"
                        " moisture) predicted directly by the IFS at spatial scales  of"
                        " a grid box or larger.\nThe mass is expressed in kilograms per"
                        " kilogram of the total mass of moist air. The  'total mass of"
                        " moist air' is the sum of the dry air, water vapour, cloud"
                        " liquid, cloud  ice, rain and falling snow. This parameter"
                        " represents the average value for a grid box.\nClouds contain"
                        " a continuum of different sized water droplets and ice"
                        " particles. The IFS  cloud scheme simplifies this to represent"
                        " a number of discrete cloud droplets/particles  including"
                        " cloud water droplets, raindrops, ice crystals and snow"
                        " (aggregated ice  crystals). The processes of droplet"
                        " formation, phase transition and aggregation are also  highly"
                        " simplified in the IFS."
                    ),
                },
                "Specific cloud ice water content": {
                    "units": "kg kg^-1",
                    "description": (
                        "This parameter is the mass of cloud ice particles per kilogram"
                        " of the total mass of  moist air. The 'total mass of moist"
                        " air' is the sum of the dry air, water vapour,  cloud liquid,"
                        " cloud ice, rain and falling snow. This parameter represents"
                        " the  average value for a grid box.\nWater within clouds can"
                        " be liquid or ice, or a combination of the two. Note that "
                        " 'cloud frozen water' is the same as 'cloud ice water'."
                    ),
                },
                "Specific cloud liquid water content": {
                    "units": "kg kg^-1",
                    "description": (
                        "This parameter is the mass of cloud liquid water droplets per"
                        " kilogram of the total  mass of moist air. The 'total mass of"
                        " moist air' is the sum of the dry air, water  vapour, cloud"
                        " liquid, cloud ice, rain and falling snow. This parameter"
                        " represents  the average value for a grid box.\nWater within"
                        " clouds can be liquid or ice, or a combination of the two. "
                    ),
                },
            },
            "version": None,
        },
        {
            "resource_id": 4,
            "resource_uid": "reanalysis-era5-single-levels",
            "title": "ERA5 hourly data on single levels from 1959 to present",
            "description": {
                "file-format": "GRIB",
                "data-type": "Gridded",
                "projection": "Regular latitude-longitude grid",
                "horizontal-coverage": "Global",
                "horizontal-resolution": "\nReanalysis: 0.25° x 0.25° (atmosphere), 0.5° x 0.5° "
                "(ocean waves)\n\nMean, spread and members: 0.5° x 0.5° "
                "(atmosphere), 1° x 1° (ocean waves)",
                "temporal-coverage": "1959 to present",
                "temporal-resolution": "Hourly",
                "update-frequency": "Daily",
            },
            "abstract": "**ERA5** is the fifth generation ECMWF reanalysis for the global climate"
            " and weather for the past 4 to 7 decades.\nCurrently data is available "
            "from 1950, with Climate Data Store entries for 1950-1978 (preliminary "
            "back extension) and from 1959 onwards (final release plus timely "
            "updates, this page).\nERA5 replaces the ERA-Interim "
            "reanalysis.\n\nReanalysis combines model data with observations "
            "from across the world into a globally complete and consistent dataset "
            "using the laws of physics. This principle, called data assimilation, is"
            " based on the method used by numerical weather prediction centres, where"
            " every so many hours (12 hours at ECMWF) a previous forecast is combined"
            " with newly available observations in an optimal way to produce a new"
            " best estimate of the state of the atmosphere, called analysis, from"
            " which an updated, improved forecast is issued. Reanalysis works in the"
            " same way, but at reduced resolution to allow for the provision of a "
            "dataset spanning back several decades. Reanalysis does not have the"
            " constraint of issuing timely forecasts, so there is more time to "
            "collect observations, and when going further back in time, to allow"
            " for the ingestion of improved versions of the original observations, "
            "which all benefit the quality of the reanalysis product.\n\nERA5 "
            "provides hourly estimates for a large number of atmospheric, "
            "ocean-wave and land-surface quantities.\nAn uncertainty estimate "
            "is sampled by an underlying 10-member ensemble\nat three-hourly "
            "intervals. Ensemble mean and spread have been pre-computed for "
            "convenience.\nSuch uncertainty estimates are closely related to the"
            " information content of the available observing system which\nhas"
            " evolved considerably over time. They also indicate flow-dependent "
            "sensitive areas.\nTo facilitate many climate applications, "
            "monthly-mean averages have been pre-calculated too,\nthough monthly "
            "means are not available for the ensemble mean and spread.\n\nERA5 "
            "is updated daily with a latency of about 5 days. In case that "
            "serious flaws are detected in this early release (called ERA5T), "
            "this data could be different from the final release 2 to 3 months"
            " later. In case that this occurs users are notified.\n\n"
            "The data set presented here is a regridded subset of the full ERA5 "
            "data set on native resolution.\nIt is online on spinning disk, which "
            "should ensure fast and easy access.\nIt should satisfy the "
            "requirements for most common applications.\n\nAn overview of all "
            "ERA5 datasets can be found in [this article]("
            "https://confluence.ecmwf.int/display/CKB/The+family+of+ERA5+datasets "
            '"The family of ERA5 datasets").\nInformation on access to ERA5 data '
            "on native resolution is provided in [these guidelines]"
            "(https://confluence.ecmwf.int/display/CKB/How+to+download+ERA5 "
            '"How to download ERA5").\n\nData has been regridded to a regular '
            "lat-lon grid of 0.25 degrees for the reanalysis and 0.5 degrees "
            "for\nthe uncertainty estimate (0.5 and 1 degree respectively for "
            "ocean waves).\nThere are four main sub sets: hourly and monthly "
            "products, both on pressure levels (upper air fields) and single "
            "levels (atmospheric, ocean-wave and land surface quantities).\n\nThe"
            ' present entry is "ERA5 hourly data on single levels from 1959 to '
            'present".\n',
            "contact": None,
            "doi": "10.24381/cds.adbb2d47",
            "form": "resources/reanalysis-era5-single-levels/form.json",
            "constraints": "resources/reanalysis-era5-single-levels/constraints.json",
            "keywords": [
                "Variable domain: Atmosphere (surface)",
                "Variable domain: Atmosphere (upper air)",
                "Temporal coverage: Past",
                "Spatial coverage: Global",
                "Product type: Reanalysis",
                "Provider: Copernicus C3S",
            ],
            "version": None,
            "variables": {
                "100m u-component of wind": {
                    "description": "This parameter is the eastward component of the 100 m wind. "
                    "It is the horizontal  speed of air moving towards the east, "
                    "at a height of 100 metres above the surface  of the Earth, "
                    "in metres per second.\nCare should be taken when comparing "
                    "model parameters with observations, because  observations are"
                    " often local to a particular point in space and time, rather"
                    " than  representing averages over a model grid box.\nThis"
                    " parameter can be combined with the northward component to "
                    "give the speed and  direction of the horizontal 100 m wind.",
                    "units": "m s^-1",
                },
                "100m v-component of wind": {
                    "description": "This parameter is the northward component of the 100 m wind."
                    " It is the horizontal  speed of air moving towards the north, "
                    "at a height of 100 metres above the surface  of the Earth, "
                    "in metres per second.\nCare should be taken when comparing "
                    "model parameters with observations, because  observations "
                    "are often local to a particular point in space and time, "
                    "rather than  representing averages over a model grid box.\n"
                    "This parameter can be combined with the eastward component "
                    "to give the speed and  direction of the horizontal 100 m"
                    " wind.",
                    "units": "m s^-1",
                },
                "10m u-component of neutral wind": {
                    "description": 'This parameter is the eastward component of the "neutral wind", at a height of 10  metres above the surface of the Earth.\nThe neutral wind is calculated from the surface stress and the corresponding  roughness length by assuming that the air is neutrally stratified. The neutral wind  is slower than the actual wind in stable conditions, and faster in unstable  conditions. The neutral wind is, by definition, in the direction of the surface  stress. The size of the roughness length depends on land surface properties or the  sea state. ',
                    "units": "m s^-1",
                },
                "10m u-component of wind": {
                    "description": "This parameter is the eastward component of the 10m wind. It is the horizontal speed  of air moving towards the east, at a height of ten metres above the surface of the  Earth, in metres per second.\nCare should be taken when comparing this parameter with observations, because wind  observations vary on small space and time scales and are affected by the local  terrain, vegetation and buildings that are represented only on average in the ECMWF  Integrated Forecasting System (IFS).\nThis parameter can be combined with the V component of 10m wind to give the speed  and direction of the horizontal 10m wind.",
                    "units": "m s^-1",
                },
                "10m v-component of neutral wind": {
                    "description": 'This parameter is the northward component of the "neutral wind", at a height of 10  metres above the surface of the Earth.\nThe neutral wind is calculated from the surface stress and the corresponding  roughness length by assuming that the air is neutrally stratified. The neutral wind  is slower than the actual wind in stable conditions, and faster in unstable  conditions. The neutral wind is, by definition, in the direction of the surface  stress. The size of the roughness length depends on land surface properties or the  sea state. ',
                    "units": "m s^-1",
                },
                "10m v-component of wind": {
                    "description": "This parameter is the northward component of the 10m wind. It is the horizontal speed  of air moving towards the north, at a height of ten metres above the surface of the  Earth, in metres per second.\nCare should be taken when comparing this parameter with observations, because wind  observations vary on small space and time scales and are affected by the local  terrain, vegetation and buildings that are represented only on average in the ECMWF  Integrated Forecasting System (IFS).\nThis parameter can be combined with the U component of 10m wind to give the speed  and direction of the horizontal 10m wind.",
                    "units": "m s^-1",
                },
                "10m wind gust since previous post-processing": {
                    "description": "Maximum 3 second wind at 10 m height as defined by WMO.\nParametrization represents turbulence only before 01102008; thereafter effects of  convection are included. The 3 s gust is computed every time step and and the maximum  is kept since the last postprocessing.",
                    "units": "m s^-1",
                },
                "2m dewpoint temperature": {
                    "description": "This parameter is the temperature to which the air, at 2 metres above the surface of  the Earth, would have to be cooled for saturation to occur.\nIt is a measure of the humidity of the air. Combined with temperature and pressure,  it can be used to calculate the relative humidity.\n2m dew point temperature is calculated by interpolating between the lowest model level  and the Earth's surface, taking account of the atmospheric conditions. This parameter  has units of kelvin (K). Temperature measured in kelvin can be converted to degrees  Celsius (°C) by subtracting 273.15.",
                    "units": "K",
                },
                "2m temperature": {
                    "description": "This parameter is the temperature of air at 2m above the surface of land, sea or  inland waters.\n2m temperature is calculated by interpolating between the lowest model level and the  Earth's surface, taking account of the atmospheric conditions. This parameter has  units of kelvin (K). Temperature measured in kelvin can be converted to degrees  Celsius (°C) by subtracting 273.15.",
                    "units": "K",
                },
                "Air density over the oceans": {
                    "description": "This parameter is the mass of air per cubic metre over the oceans, derived from the  temperature, specific humidity and pressure at the lowest model level in the atmospheric  model.\nThis parameter is one of the parameters used to force the wave model, therefore it is  only calculated over water bodies represented in the ocean wave model. It is interpolated  from the atmospheric model horizontal grid onto the horizontal grid used by the ocean  wave model.",
                    "units": "kg m^-3",
                },
                "Angle of sub-gridscale orography": {
                    "description": "This parameter is one of four parameters (the others being standard deviation, slope and  anisotropy) that describe the features of the orography that are too small to be  resolved by the model grid. These four parameters are calculated for orographic features  with horizontal scales comprised between 5 km and the model grid resolution, being  derived from the height of valleys, hills and mountains at about 1 km resolution. They  are used as input for the sub-grid orography scheme which represents low-level blocking  and orographic gravity wave effects.\nThe angle of the sub-grid scale orography characterises the geographical orientation of  the terrain in the horizontal plane (from a bird's-eye view) relative to an eastwards  axis.\nThis parameter does not vary in time.",
                    "units": "radians",
                },
                "Anisotropy of sub-gridscale orography": {
                    "description": "This parameter is one of four parameters (the others being standard deviation, slope and  angle of sub-gridscale orography) that describe the features of the orography that are  too small to be resolved by the model grid. These four parameters are calculated for  orographic features with horizontal scales comprised between 5 km and the model grid  resolution, being derived from the height of valleys, hills and mountains at about 1 km  resolution. They are used as input for the sub-grid orography scheme which represents  low-level blocking and orographic gravity wave effects.\nThis parameter is a measure of how much the shape of the terrain in the horizontal plane  (from a bird's-eye view) is distorted from a circle.\nA value of one is a circle, less than one an ellipse, and 0 is a ridge. In the case of a  ridge, wind blowing parallel to it does not exert any drag on the flow, but wind blowing  perpendicular to it exerts the maximum drag.\nThis parameter does not vary in time.",
                    "units": "Dimensionless",
                },
                "Benjamin-feir index": {
                    "description": "This parameter is used to calculate the likelihood of freak ocean waves, which are waves  that are higher than twice the mean height of the highest third of waves. Large values  of this parameter (in practice of the order 1) indicate increased probability of the  occurrence of freak waves.\nThe ocean/sea surface wave field consists of a combination of waves with different heights,  lengths and directions (known as the two-dimensional wave spectrum). This parameter is  derived from the statistics of the two-dimensional wave spectrum. More precisely, it is  the square of the ratio of the integral ocean wave steepness and the relative width of the  frequency spectrum of the waves.\nFurther information on the calculation of this parameter is given in Section 10.6 of the  ECMWF Wave Model documentation.",
                    "units": "Dimensionless",
                },
                "Boundary layer dissipation": {
                    "description": "This parameter is the accumulated conversion of kinetic energy in the mean flow into heat, over the whole atmospheric column, per unit area, that is due to the effects of stress associated with turbulent eddies near the surface and turbulent orographic form drag. It is calculated by the ECMWF Integrated Forecasting System's turbulent diffusion and turbulent orographic form drag schemes. The turbulent eddies near the surface are related to the roughness of the surface. The turbulent orographic form drag is the stress due to the valleys, hills and mountains on horizontal scales below 5km, which are specified from land surface data at about 1 km resolution. (The dissipation associated with orographic features with horizontal scales between 5 km and the model grid-scale is accounted for by the sub-grid orographic scheme.)\nThis parameter is accumulated over a particular time period which depends on the data extracted.  For the reanalysis, the accumulation period is over the 1 hour ending at the validity date and time.  For the ensemble members, ensemble mean and ensemble spread, the accumulation period is over the  3 hours ending at the validity date and time.",
                    "units": "J m^-2",
                },
                "Boundary layer height": {
                    "description": "This parameter is the depth of air next to the Earth's surface which is most affected by  the resistance to the transfer of momentum, heat or moisture across the surface.\nThe boundary layer height can be as low as a few tens of metres, such as in cooling air at  night, or as high as several kilometres over the desert in the middle of a hot sunny day.  When the boundary layer height is low, higher concentrations of pollutants (emitted from  the Earth's surface) can develop.\nThe boundary layer height calculation is based on the bulk Richardson number (a measure  of the atmospheric conditions) following the conclusions of a 2012 review.",
                    "units": "m",
                },
                "Charnock": {
                    "description": "This parameter accounts for increased aerodynamic roughness as wave heights grow due to  increasing surface stress. It depends on the wind speed, wave age and other aspects of  the sea state and is used to calculate how much the waves slow down the wind.\nWhen the atmospheric model is run without the ocean model, this parameter has a constant  value of 0.018. When the atmospheric model is coupled to the ocean model, this parameter  is calculated by the ECMWF Wave Model.",
                    "units": "Dimensionless",
                },
                "Clear-sky direct solar radiation at surface": {
                    "description": "This parameter is the amount of direct radiation from the Sun (also known as solar or  shortwave radiation) reaching the surface of the Earth, assuming clear-sky (cloudless)  conditions. It is the amount of radiation passing through a horizontal plane.\nSolar radiation at the surface can be direct or diffuse. Solar radiation can be  scattered in all directions by particles in the atmosphere, some of which reaches the  surface (diffuse solar radiation). Some solar radiation reaches the surface without  being scattered (direct solar radiation).\nClear-sky radiation quantities are computed for exactly the same atmospheric conditions  of temperature, humidity, ozone, trace gases and aerosol as the corresponding total-sky  quantities (clouds included), but assuming that the clouds are not there.\nThis parameter is accumulated over a particular time period which depends on the data extracted.  For the reanalysis, the accumulation period is over the 1 hour ending at the validity date and time.  For the ensemble members, ensemble mean and ensemble spread, the accumulation period is over the  3 hours ending at the validity date and time.\nThe units are joules per square metre (J m^-2 ). To convert to watts per square  metre (W m^-2 ), the accumulated values should be divided by the accumulation period  expressed in seconds.\nThe ECMWF convention for vertical fluxes is positive downwards.",
                    "units": "J m^-2",
                },
                "Cloud base height": {
                    "description": "The height above the Earth's surface of the base of the lowest cloud layer, at the  specified time.\nThis parameter is calculated by searching from the second lowest model level upwards,  to the height of the level where cloud fraction becomes greater than 1% and condensate  content greater than 1.E-6 kg kg^-1. Fog (i.e., cloud in the lowest model layer) is not  considered when defining cloud base height.",
                    "units": "m",
                },
                "Coefficient of drag with waves": {
                    "description": 'This parameter is the resistance that ocean waves exert on the atmosphere. It is  sometimes also called a "friction coefficient".\nIt is calculated by the wave model as the ratio of the square of the friction velocity,  to the square of the neutral wind speed at a height of 10 metres above the surface of  the Earth.\nThe neutral wind is calculated from the surface stress and the corresponding roughness  length by assuming that the air is neutrally stratified. The neutral wind is, by  definition, in the direction of the surface stress. The size of the roughness length  depends on the sea state.',
                    "units": "Dimensionless",
                },
                "Convective available potential energy": {
                    "description": "This is an indication of the instability (or stability) of the atmosphere and can be  used to assess the potential for the development of convection, which can lead to heavy  rainfall, thunderstorms and other severe weather.\nIn the ECMWF Integrated Forecasting System (IFS), CAPE is calculated by considering  parcels of air departing at different model levels below the 350 hPa level. If a parcel  of air is more buoyant (warmer and/or with more moisture) than its surrounding  environment, it will continue to rise (cooling as it rises) until it reaches a point  where it no longer has positive buoyancy. CAPE is the potential energy represented by  the total excess buoyancy. The maximum CAPE produced by the different parcels is the  value retained.\nLarge positive values of CAPE indicate that an air parcel would be much warmer than its  surrounding environment and therefore, very buoyant. CAPE is related to the maximum  potential vertical velocity of air within an updraft; thus, higher values indicate  greater potential for severe weather. Observed values in thunderstorm environments  often may exceed 1000 joules per kilogram (J kg^-1), and in extreme cases may exceed  5000 J kg^-1.\nThe calculation of this parameter assumes: (i) the parcel of air does not mix with  surrounding air; (ii) ascent is pseudo-adiabatic (all condensed water falls out) and  (iii) other simplifications related to the mixed-phase condensational heating.",
                    "units": "J kg^-1",
                },
                "Convective inhibition": {
                    "description": "This parameter is a measure of the amount of energy required for convection to  commence. If the value of this parameter is too high, then deep, moist convection is  unlikely to occur even if the convective available potential energy or convective  available potential energy shear are large. CIN values greater than 200 J kg^-1 would  be considered high.\nAn atmospheric layer where temperature increases with height (known as a temperature  inversion) would inhibit convective uplift and is a situation in which convective  inhibition would be large.",
                    "units": "J kg^-1",
                },
                "Convective precipitation": {
                    "description": "This parameter is the accumulated precipitation that falls to the Earth's surface,  which is generated by the convection scheme in the ECMWF Integrated Forecasting System  (IFS). The convection scheme represents convection at spatial scales smaller than the  grid box. Precipitation can also be generated by the cloud scheme in the IFS, which  represents the formation and dissipation of clouds and large-scale precipitation due  to changes in atmospheric quantities (such as pressure, temperature and moisture)  predicted directly at spatial scales of the grid box or larger. In the IFS,  precipitation is comprised of rain and snow.\nIn the IFS, precipitation is comprised of rain and snow.\nThis parameter is accumulated over a particular time period which depends on the data extracted.  For the reanalysis, the accumulation period is over the 1 hour ending at the validity date and time.  For the ensemble members, ensemble mean and ensemble spread, the accumulation period is over the  3 hours ending at the validity date and time.\nThe units of this parameter are depth in metres of water equivalent. It is the depth  the water would have if it were spread evenly over the grid box.\nCare should be taken when comparing model parameters with observations, because  observations are often local to a particular point in space and time, rather than  representing averages over a model grid box.",
                    "units": "m",
                },
                "Convective rain rate": {
                    "description": "This parameter is the rate of rainfall (rainfall intensity), at the Earth's surface and  at the specified time, which is generated by the convection scheme in the ECMWF Integrated  Forecasting System (IFS). The convection scheme represents convection at spatial scales  smaller than the grid box. Rainfall can also be generated by the cloud scheme in the IFS,  which represents the formation and dissipation of clouds and large-scale precipitation due  to changes in atmospheric quantities (such as pressure, temperature and moisture) predicted  directly at spatial scales of the grid box or larger. In the IFS, precipitation is comprised  of rain and snow.\nThis parameter is the rate the rainfall would have if it were spread evenly over the grid box. 1 kg of water spread over 1 square metre of surface is 1 mm deep (neglecting the  effects of temperature on the density of water), therefore the units are equivalent to  mm per second.\nCare should be taken when comparing model parameters with observations, because  observations are often local to a particular point in space and time, rather than  representing averages over a model grid box.",
                    "units": "kg m^-2 s^-1",
                },
                "Convective snowfall": {
                    "description": "This parameter is the accumulated snow that falls to the Earth's surface, which is generated by the  convection scheme in the ECMWF Integrated Forecasting System (IFS). The convection scheme represents  convection at spatial scales smaller than the grid box. Snowfall can also be generated by the cloud  scheme in the IFS, which represents the formation and dissipation of clouds and large-scale  precipitation due to changes in atmospheric quantities (such as pressure, temperature and moisture)  predicted directly at spatial scales of the grid box or larger. In the IFS, precipitation is comprised  of rain and snow.\nThis parameter is accumulated over a particular time period which depends on the data extracted.  For the reanalysis, the accumulation period is over the 1 hour ending at the validity date and time.  For the ensemble members, ensemble mean and ensemble spread, the accumulation period is over the  3 hours ending at the validity date and time.\nThe units of this parameter are depth in metres of water equivalent. It is the depth  the water would have if it were spread evenly over the grid box.\nCare should be taken when comparing model parameters with observations, because observations are often  local to a particular point in space and time, rather than representing averages over a model grid box.",
                    "units": "m of water equivalent",
                },
                "Convective snowfall rate water equivalent": {
                    "description": "This parameter is the rate of snowfall (snowfall intensity), at the Earth's surface and at the  specified time, which is generated by the convection scheme in the ECMWF Integrated Forecasting  System (IFS). The convection scheme represents convection at spatial scales smaller than the  grid box. Snowfall can also be generated by the cloud scheme in the IFS, which represents the  formation and dissipation of clouds and large-scale precipitation due to changes in atmospheric  quantities (such as pressure, temperature and moisture) predicted directly at spatial scales of  the grid box or larger. In the IFS, precipitation is comprised of rain and snow.\nThis parameter is the rate the snowfall would have if it were spread evenly over the grid box. Since 1 kg of water spread over 1 square metre of surface is 1 mm thick (neglecting  the effects of temperature on the density of water), the units are equivalent to mm  (of liquid water) per second.\nCare should be taken when comparing model parameters with observations, because  observations are often local to a particular point in space and time, rather than  representing averages over a model grid box.",
                    "units": "kg m^-2 s^-1",
                },
                "Downward UV radiation at the surface": {
                    "description": "This parameter is the amount of ultraviolet (UV) radiation reaching the surface. It  is the amount of radiation passing through a horizontal plane.\nUV radiation is part of the electromagnetic spectrum emitted by the Sun that has  wavelengths shorter than visible light. In the ECMWF Integrated Forecasting system  (IFS) it is defined as radiation with a wavelength of 0.20-0.44 µm (microns, 1  millionth of a metre).\nSmall amounts of UV are essential for living organisms, but overexposure may result  in cell damage; in humans this includes acute and chronic health effects on the skin,  eyes and immune system. UV radiation is absorbed by the ozone layer, but some reaches  the surface. The depletion of the ozone layer is causing concern over an increase in  the damaging effects of UV.\nThis parameter is accumulated over a particular time period which depends on the data extracted.  For the reanalysis, the accumulation period is over the 1 hour ending at the validity date and time.  For the ensemble members, ensemble mean and ensemble spread, the accumulation period is over the  3 hours ending at the validity date and time.\nThe units are joules per square metre (J m^-2 ). To convert to watts per square metre  (W m^-2 ), the accumulated values should be divided by the accumulation period expressed in seconds.\nThe ECMWF convention for vertical fluxes is positive downwards.",
                    "units": "J m^-2",
                },
                "Duct base height": {
                    "description": "Duct base height as diagnosed from the vertical gradient of atmospheric refractivity.",
                    "units": "m",
                },
                "Eastward gravity wave surface stress": {
                    "description": "Air flowing over a surface exerts a stress (drag) that transfers momentum to the surface and slows the wind. This parameter is the component of the accumulated surface stress in an eastward direction, associated with low-level, orographic blocking and orographic gravity waves. It is calculated by the ECMWF Integrated Forecasting System's sub-grid orography scheme, which represents stress due to unresolved valleys, hills and mountains with horizontal scales between 5 km and the model grid-scale. (The stress associated  with orographic features with horizontal scales smaller than 5 km is accounted for by  the turbulent orographic form drag scheme).\nOrographic gravity waves are oscillations in the flow maintained by the buoyancy of  displaced air parcels, produced when air is deflected upwards by hills and  mountains. This process can create stress on the atmosphere at the Earth's  surface and at other levels in the atmosphere.\nPositive (negative) values indicate stress on the surface of the Earth in an eastward (westward) direction.\nThis parameter is accumulated over a particular time period which depends on the data extracted.  For the reanalysis, the accumulation period is over the 1 hour ending at the validity date and time.  For the ensemble members, ensemble mean and ensemble spread, the accumulation period is over the  3 hours ending at the validity date and time.",
                    "units": "N m^-2 s",
                },
                "Eastward turbulent surface stress": {
                    "description": "Air flowing over a surface exerts a stress (drag) that transfers momentum to the surface and slows the wind. This parameter is the component of the accumulated surface stress in an eastward direction, associated with turbulent eddies near the surface and turbulent orographic form drag. It is calculated by the ECMWF Integrated Forecasting System's turbulent diffusion and turbulent orographic form drag schemes. The turbulent eddies near the surface are related to the roughness of the surface. The turbulent orographic form drag is the stress due to the valleys, hills and mountains on horizontal scales below 5km, which are specified from land surface data at about 1 km resolution. (The stress associated with orographic features with horizontal scales between 5 km and the model grid-scale is accounted for by the sub-grid orographic scheme.)\nPositive (negative) values indicate stress on the surface of the Earth in an eastward (westward) direction.\nThis parameter is accumulated over a particular time period which depends on the data extracted.  For the reanalysis, the accumulation period is over the 1 hour ending at the validity date and time.  For the ensemble members, ensemble mean and ensemble spread, the accumulation period is over the  3 hours ending at the validity date and time.",
                    "units": "N m^-2 s",
                },
                "Evaporation": {
                    "description": "This parameter is the accumulated amount of water that has evaporated from the  Earth's surface, including a simplified representation of transpiration (from  vegetation), into vapour in the air above.\nThis parameter is accumulated over a particular time period which depends on the data extracted.  For the reanalysis, the accumulation period is over the 1 hour ending at the validity date and time.  For the ensemble members, ensemble mean and ensemble spread, the accumulation period is over the  3 hours ending at the validity date and time.\nThe ECMWF Integrated Forecasting System (IFS) convention is that downward fluxes are  positive. Therefore, negative values indicate evaporation and positive values indicate  condensation.",
                    "units": "m of water equivalent",
                },
                "Forecast albedo": {
                    "description": "This parameter is a measure of the reflectivity of the Earth's surface. It is the  fraction of short-wave (solar) radiation reflected by the Earth's surface, for diffuse radiation, assuming a fixed spectrum of downward short-wave radiation at the surface.\nThe values of this parameter vary between zero and one. Typically, snow and ice have high reflectivity with albedo values of 0.8 and above, land has intermediate values between about 0.1 and 0.4 and the ocean has low values of 0.1 or less.\nShort-wave radiation from the Sun is partly reflected back to  space by clouds and particles in the atmosphere (aerosols) and some of it is absorbed.  The remainder is incident on the Earth's surface, where some of it is reflected. The  portion that is reflected by the Earth's surface depends on the albedo.\nIn the ECMWF Integrated Forecasting System (IFS), a climatological background albedo  (observed values averaged over a period of several years) is used, modified by the  model over water, ice and snow.\nAlbedo is often shown as a percentage (%).",
                    "units": "Dimensionless",
                },
                "Forecast logarithm of surface roughness for heat": {
                    "description": "This parameter is the natural logarithm of the roughness length for heat.\nThe surface roughness for heat is a measure of the surface resistance to heat transfer.  This parameter is used to determine the air to surface transfer of heat. For given  atmospheric conditions, a higher surface roughness for heat means that it is more  difficult for the air to exchange heat with the surface. A lower surface roughness for  heat means that it is easier for the air to exchange heat with the surface.\nOver the ocean, surface roughness for heat depends on the waves. Over sea-ice, it has  a constant value of 0.001 m. Over land, it is derived from the vegetation type and  snow cover.",
                    "units": "Dimensionless",
                },
                "Forecast surface roughness": {
                    "description": "This parameter is the aerodynamic roughness length in metres.\nIt is a measure of the surface resistance. This parameter is used to determine the air  to surface transfer of momentum. For given atmospheric conditions, a higher surface  roughness causes a slower near-surface wind speed.\nOver ocean, surface roughness depends on the waves. Over land, surface roughness is  derived from the vegetation type and snow cover.",
                    "units": "m",
                },
                "Free convective velocity over the oceans": {
                    "description": "This parameter is an estimate of the vertical velocity of updraughts generated by free  convection. Free convection is fluid motion induced by buoyancy forces, which are  driven by density gradients. The free convective velocity is used to estimate the  impact of wind gusts on ocean wave growth.\nIt is calculated at the height of the lowest temperature inversion (the height above  the surface of the Earth where the temperature increases with height).\nThis parameter is one of the parameters used to force the wave model, therefore it is  only calculated over water bodies represented in the ocean wave model. It is  interpolated from the atmospheric model horizontal grid onto the horizontal grid used  by the ocean wave model.",
                    "units": "m s^-1",
                },
                "Friction velocity": {
                    "description": "Air flowing over a surface exerts a stress that transfers momentum to the surface and  slows the wind. This parameter is a theoretical wind speed at the Earth's surface that  expresses the magnitude of stress. It is calculated by dividing the surface stress by  air density and taking its square root. For turbulent flow, the friction velocity is  approximately constant in the lowest few metres of the atmosphere.\nThis parameter increases with the roughness of the surface. It is used to calculate  the way wind changes with height in the lowest levels of the atmosphere.",
                    "units": "m s^-1",
                },
                "Gravity wave dissipation": {
                    "description": "This parameter is the accumulated conversion of kinetic energy in the mean flow into heat, over the whole atmospheric column, per unit area, that is due to the effects of stress associated with low-level, orographic blocking and orographic gravity waves. It is calculated by the ECMWF Integrated Forecasting System's sub-grid orography scheme, which represents stress due to unresolved valleys, hills and mountains with horizontal scales between 5 km and the model grid-scale. (The dissipation associated  with orographic features with horizontal scales smaller than 5 km is accounted for by  the turbulent orographic form drag scheme).\nOrographic gravity waves are oscillations in the flow maintained by the buoyancy of  displaced air parcels, produced when air is deflected upwards by hills and  mountains. This process can create stress on the atmosphere at the Earth's  surface and at other levels in the atmosphere.\nThis parameter is accumulated over a particular time period which depends on the data extracted.  For the reanalysis, the accumulation period is over the 1 hour ending at the validity date and time.  For the ensemble members, ensemble mean and ensemble spread, the accumulation period is over the  3 hours ending at the validity date and time.",
                    "units": "J m^-2",
                },
                "High cloud cover": {
                    "description": 'The proportion of a grid box covered by cloud occurring in the high levels of the  troposphere. High cloud is a single level field calculated from cloud occurring on  model levels with a pressure less than 0.45 times the surface pressure. So, if the  surface pressure is 1000 hPa (hectopascal), high cloud would be calculated using  levels with a pressure of less than 450 hPa (approximately 6km and above (assuming a "standard atmosphere")).\nThe high cloud cover parameter is calculated from cloud for the appropriate model  levels as described above. Assumptions are made about the degree of overlap/randomness  between clouds in different model levels.\nCloud fractions vary from 0 to 1.',
                    "units": "Dimensionless",
                },
                "High vegetation cover": {
                    "description": 'This parameter is the fraction of the grid box that is covered with vegetation that  is classified as "high". The values vary between 0 and 1 but do not vary in time.\nThis is one of the parameters in the model that describes land surface vegetation.  "High vegetation" consists of evergreen trees, deciduous trees, mixed forest/woodland,  and interrupted forest.',
                    "units": "Dimensionless",
                },
                "Ice temperature layer 1": {
                    "description": "This parameter is the sea-ice temperature in layer 1 (0 to 7cm).\nThe ECMWF Integrated Forecasting System (IFS) has a four-layer sea-ice slab: Layer 1: 0-7cm, Layer 2: 7-28cm, Layer 3: 28-100cm, Layer 4: 100-150cm.\nThe temperature of the sea-ice in each layer changes as heat is transferred between the  sea-ice layers and the atmosphere above and ocean below.\nThis parameter is defined over the whole globe, even where there is no ocean or sea ice. Regions without sea ice can be masked out by only considering grid points where the sea-ice cover does not have a missing value and is greater than 0.0.",
                    "units": "K",
                },
                "Ice temperature layer 2": {
                    "description": "This parameter is the sea-ice temperature in layer 2 (7 to 28cm).\nThe ECMWF Integrated Forecasting System (IFS) has a four-layer sea-ice slab: Layer 1: 0-7cm, Layer 2: 7-28cm, Layer 3: 28-100cm, Layer 4: 100-150cm.\nThe temperature of the sea-ice in each layer changes as heat is transferred between the  sea-ice layers and the atmosphere above and ocean below.\nThis parameter is defined over the whole globe, even where there is no ocean or sea ice. Regions without sea ice can be masked out by only considering grid points where the sea-ice cover does not have a missing value and is greater than 0.0.",
                    "units": "K",
                },
                "Ice temperature layer 3": {
                    "description": "This parameter is the sea-ice temperature in layer 3 (28 to 100cm).\nThe ECMWF Integrated Forecasting System (IFS) has a four-layer sea-ice slab: Layer 1: 0-7cm, Layer 2: 7-28cm, Layer 3: 28-100cm, Layer 4: 100-150cm.\nThe temperature of the sea-ice in each layer changes as heat is transferred between the  sea-ice layers and the atmosphere above and ocean below.\nThis parameter is defined over the whole globe, even where there is no ocean or sea ice. Regions without sea ice can be masked out by only considering grid points where the sea-ice cover does not have a missing value and is greater than 0.0.",
                    "units": "K",
                },
                "Ice temperature layer 4": {
                    "description": "This parameter is the sea-ice temperature in layer 4 (100 to 150cm).\nThe ECMWF Integrated Forecasting System (IFS) has a four-layer sea-ice slab: Layer 1: 0-7cm, Layer 2: 7-28cm, Layer 3: 28-100cm, Layer 4: 100-150cm.\nThe temperature of the sea-ice in each layer changes as heat is transferred between the  sea-ice layers and the atmosphere above and ocean below.\nThis parameter is defined over the whole globe, even where there is no ocean or sea ice. Regions without sea ice can be masked out by only considering grid points where the sea-ice cover does not have a missing value and is greater than 0.0.",
                    "units": "K",
                },
                "Instantaneous 10m wind gust": {
                    "description": "This parameter is the maximum wind gust at the specified time, at a height of ten metres  above the surface of the Earth.\nThe WMO defines a wind gust as the maximum of the wind averaged over 3 second intervals.  This duration is shorter than a model time step, and so the ECMWF Integrated Forecasting  System (IFS) deduces the magnitude of a gust within each time step from the  time-step-averaged surface stress, surface friction, wind shear and stability.\nCare should be taken when comparing model parameters with observations, because  observations are often local to a particular point in space and time, rather than  representing averages over a model grid box.",
                    "units": "m s^-1",
                },
                "Instantaneous eastward turbulent surface stress": {
                    "description": "Air flowing over a surface exerts a stress (drag) that transfers momentum to the surface and slows the wind. This parameter is the component of the surface stress at the specified time, in an eastward direction, associated with turbulent eddies near the surface and turbulent orographic form drag. It is calculated by the ECMWF Integrated Forecasting System's turbulent diffusion and turbulent orographic form drag schemes. The turbulent eddies near the surface are related to the roughness of the surface. The turbulent orographic form drag is the stress due to the valleys, hills and mountains on horizontal scales below 5km, which are specified from land surface data at about 1 km resolution. (The stress associated with orographic features with horizontal scales between 5 km and the model grid-scale is accounted for by the sub-grid orographic scheme.)\nPositive (negative) values indicate stress on the surface of the Earth in an eastward (westward) direction.",
                    "units": "N m^-2",
                },
                "Instantaneous large-scale surface precipitation fraction": {
                    "description": "This parameter is the fraction of the grid box (0-1) covered by large-scale  precipitation at the specified time.\nLarge-scale precipitation is rain and snow that falls to the Earth's surface, and is  generated by the cloud scheme in the ECMWF Integrated Forecasting System (IFS). The  cloud scheme represents the formation and dissipation of clouds and large-scale  precipitation due to changes in atmospheric quantities (such as pressure, temperature  and moisture) predicted directly by the IFS at spatial scales of a grid box or larger.  Precipitation can also be due to convection generated by the convection scheme in the  IFS. The convection scheme represents convection at spatial scales smaller than the grid  box.",
                    "units": "Dimensionless",
                },
                "Instantaneous moisture flux": {
                    "description": "This parameter is the net rate of moisture exchange between the land/ocean surface and  the atmosphere, due to the processes of evaporation (including evapotranspiration) and  condensation, at the specified time. By convention, downward fluxes are positive, which  means that evaporation is represented by negative values and condensation by positive  values.",
                    "units": "kg m^-2 s^-1",
                },
                "Instantaneous northward turbulent surface stress": {
                    "description": "Air flowing over a surface exerts a stress (drag) that transfers momentum to the surface and slows the wind. This parameter is the component of the surface stress at the specified time, in a northward direction, associated with turbulent eddies near the surface and turbulent orographic form drag. It is calculated by the ECMWF Integrated Forecasting System's turbulent diffusion and turbulent orographic form drag schemes. The turbulent eddies near the surface are related to the roughness of the surface. The turbulent orographic form drag is the stress due to the valleys, hills and mountains on horizontal scales below 5km, which are specified from land surface data at about 1 km resolution. (The stress associated with orographic features with horizontal scales between 5 km and the model grid-scale is accounted for by the sub-grid orographic scheme.)\nPositive (negative) values indicate stress on the surface of the Earth in a northward (southward) direction.",
                    "units": "N m^-2",
                },
                "Instantaneous surface sensible heat flux": {
                    "description": "This parameter is the transfer of heat between the Earth's surface and the atmosphere,  at the specified time, through the effects of turbulent air motion (but excluding any  heat transfer resulting from condensation or evaporation).\nThe magnitude of the sensible heat flux is governed by the difference in temperature  between the surface and the overlying atmosphere, wind speed and the surface roughness.  For example, cold air overlying a warm surface would produce a sensible heat flux from  the land (or ocean) into the atmosphere. The ECMWF convention for vertical fluxes is  positive downwards.",
                    "units": "W m^-2",
                },
                "K index": {
                    "description": "This parameter is a measure of the potential for a thunderstorm to develop, calculated  from the temperature and dew point temperature in the lower part of the atmosphere.  The calculation uses the temperature at 850, 700 and 500 hPa and dewpoint temperature  at 850 and 700 hPa. Higher values of K indicate a higher potential for the development  of thunderstorms.\nThis parameter is related to the probability of occurrence of a thunderstorm: <20 K No thunderstorm, 20-25 K Isolated thunderstorms, 26-30 K Widely scattered thunderstorms, 31-35 K Scattered thunderstorms, >35 K Numerous thunderstorms.",
                    "units": "K",
                },
                "Lake bottom temperature": {
                    "description": "This parameter is the temperature of water at the bottom of inland water bodies (lakes,  reservoirs, rivers and coastal waters).\nThis parameter is defined over the whole globe, even where there is no inland water. Regions without inland water can be masked out by only considering grid points where the lake cover is greater than 0.0.\nIn May 2015, a lake model was implemented in the ECMWF Integrated Forecasting System  (IFS) to represent the water temperature and lake ice of all the world's major inland  water bodies. Lake depth and area fraction (cover) are kept constant in time.\nThis parameter has units of kelvin (K). Temperature measured in kelvin can be converted  to degrees Celsius (°C) by subtracting 273.15.",
                    "units": "K",
                },
                "Lake cover": {
                    "description": "This parameter is the proportion of a grid box covered by inland water bodies (lakes,  reservoirs, rivers and coastal waters). Values vary between 0: no inland water, and  1: grid box is fully covered with inland water. This parameter is specified from  observations and does not vary in time.\nIn May 2015, a lake model was implemented in the ECMWF Integrated Forecasting System  (IFS) to represent the water temperature and lake ice of all the world's major inland  water bodies.",
                    "units": "Dimensionless",
                },
                "Lake depth": {
                    "description": "This parameter is the mean depth of inland water bodies (lakes, reservoirs, rivers  and coastal waters). This parameter is specified from in-situ measurements and indirect  estimates and does not vary in time.\nThis parameter is defined over the whole globe, even where there is no inland water. Regions without inland water can be masked out by only considering grid points where the lake cover is greater than 0.0.\nIn May 2015, a lake model was implemented in the ECMWF Integrated Forecasting System  (IFS) to represent the water temperature and lake ice of all the world's major inland  water bodies.",
                    "units": "m",
                },
                "Lake ice depth": {
                    "description": "This parameter is the thickness of ice on inland water bodies (lakes, reservoirs,  rivers and coastal waters).\nThis parameter is defined over the whole globe, even where there is no inland water. Regions without inland water can be masked out by only considering grid points where the lake cover is greater than 0.0.\nIn May 2015, a lake model was implemented in the ECMWF Integrated Forecasting System  (IFS) to represent the water temperature and lake ice of all the world's major inland  water bodies. Lake depth and area fraction (cover) are kept constant in time. A  single ice layer is used to represent the formation and melting of ice on inland  water bodies. This parameter is the thickness of that ice layer.",
                    "units": "m",
                },
                "Lake ice temperature": {
                    "description": "This parameter is the temperature of the uppermost surface of ice on inland water  bodies (lakes, reservoirs, rivers and coastal waters). It is the temperature at the  ice/atmosphere or ice/snow interface.\nThis parameter is defined over the whole globe, even where there is no inland water. Regions without inland water can be masked out by only considering grid points where the lake cover is greater than 0.0.\nIn May 2015, a lake model was implemented in the ECMWF Integrated Forecasting System  (IFS) to represent the water temperature and lake ice of all the world's major inland  water bodies. Lake depth and area fraction (cover) are kept constant in time. A  single ice layer is used to represent the formation and melting of ice on inland  water bodies.\nThis parameter has units of kelvin (K). Temperature measured in kelvin can be converted  to degrees Celsius (°C) by subtracting 273.15.",
                    "units": "K",
                },
                "Lake mix-layer depth": {
                    "description": "This parameter is the thickness of the uppermost layer of inland water bodies (lakes,  reservoirs, rivers and coastal waters) that is well mixed and has a near constant  temperature with depth (i.e., a uniform distribution of temperature with depth).\nMixing can occur when the density of the surface (and near-surface) water is greater  than that of the water below. Mixing can also occur through the action of wind on the  surface of the water.\nThis parameter is defined over the whole globe, even where there is no inland water. Regions without inland water can be masked out by only considering grid points where the lake cover is greater than 0.0.\nIn May 2015, a lake model was implemented in the ECMWF Integrated Forecasting System  (IFS) to represent the water temperature and lake ice of all the world's major inland  water bodies. Lake depth and area fraction (cover) are kept constant in time. Inland  water bodies are represented with two layers in the vertical, the mixed layer above  and the thermocline below, where temperature changes with depth. The upper boundary  of the thermocline is located at the mixed layer bottom, and the lower boundary of  the thermocline at the lake bottom. A single ice layer is used to represent the  formation and melting of ice on inland water bodies.",
                    "units": "m",
                },
                "Lake mix-layer temperature": {
                    "description": "This parameter is the temperature of the uppermost layer of inland water bodies (lakes,  reservoirs, rivers and coastal waters) that is well mixed and has a near constant  temperature with depth (i.e., a uniform distribution of temperature with depth).\nMixing can occur when the density of the surface (and near-surface) water is greater  than that of the water below. Mixing can also occur through the action of wind on the  surface of the water.\nThis parameter is defined over the whole globe, even where there is no inland water. Regions without inland water can be masked out by only considering grid points where the lake cover is greater than 0.0.\nIn May 2015, a lake model was implemented in the ECMWF Integrated Forecasting System  (IFS) to represent the water temperature and lake ice of all the world's major inland  water bodies. Lake depth and area fraction (cover) are kept constant in time. Inland  water bodies are represented with two layers in the vertical, the mixed layer above  and the thermocline below, where temperature changes with depth. The upper boundary  of the thermocline is located at the mixed layer bottom, and the lower boundary of  the thermocline at the lake bottom. A single ice layer is used to represent the  formation and melting of ice on inland water bodies.\nThis parameter has units of kelvin (K). Temperature measured in kelvin can be  converted to degrees Celsius (°C) by subtracting 273.15.",
                    "units": "K",
                },
                "Lake shape factor": {
                    "description": "This parameter describes the way that temperature changes with depth in the  thermocline layer of inland water bodies (lakes, reservoirs, rivers and coastal waters)  i.e., it describes the shape of the vertical temperature profile. It is used to  calculate the lake bottom temperature and other lake-related parameters.\nThis parameter is defined over the whole globe, even where there is no inland water. Regions without inland water can be masked out by only considering grid points where the lake cover is greater than 0.0.\nIn May 2015, a lake model was implemented in the ECMWF Integrated Forecasting System  (IFS) to represent the water temperature and lake ice of all the world's major inland  water bodies. Lake depth and area fraction (cover) are kept constant in time. Inland  water bodies are represented with two layers in the vertical, the mixed layer above  and the thermocline below, where temperature changes with depth. The upper boundary  of the thermocline is located at the mixed layer bottom, and the lower boundary of  the thermocline at the lake bottom. A single ice layer is used to represent the  formation and melting of ice on inland water bodies.",
                    "units": "Dimensionless",
                },
                "Lake total layer temperature": {
                    "description": "This parameter is the mean temperature of the total water column in inland water  bodies (lakes, reservoirs, rivers and coastal waters).\nThis parameter is defined over the whole globe, even where there is no inland water. Regions without inland water can be masked out by only considering grid points where the lake cover is greater than 0.0.\nIn May 2015, a lake model was implemented in the ECMWF Integrated Forecasting System  (IFS) to represent the water temperature and lake ice of all the world's major inland  water bodies. Lake depth and area fraction (cover) are kept constant in time. Inland  water bodies are represented with two layers in the vertical, the mixed layer above  and the thermocline below, where temperature changes with depth. This parameter is  the mean temperature over the two layers. The upper boundary of the thermocline is  located at the mixed layer bottom, and the lower boundary of the thermocline at the  lake bottom. A single ice layer is used to represent the formation and melting of ice  on inland water bodies.\nThis parameter has units of kelvin (K). Temperature measured in kelvin can be converted  to degrees Celsius (°C) by subtracting 273.15.",
                    "units": "K",
                },
                "Land-sea mask": {
                    "description": "This parameter is the proportion of land, as opposed to ocean or inland waters (lakes,  reservoirs, rivers and coastal waters), in a grid box.\nThis parameter has values ranging between zero and one and is dimensionless.\nIn cycles of the ECMWF Integrated Forecasting System (IFS) from CY41R1 (introduced in  May 2015) onwards, grid boxes where this parameter has a value above 0.5 can be  comprised of a mixture of land and inland water but not ocean. Grid boxes with a value  of 0.5 and below can only be comprised of a water surface. In the latter case, the  lake cover is used to determine how much of the water surface is ocean or inland water.\nIn cycles of the IFS before CY41R1, grid boxes where this parameter has a value above  0.5 can only be comprised of land and those grid boxes with a value of 0.5 and below  can only be comprised of ocean. In these older model cycles, there is no  differentiation between ocean and inland water.\nThis parameter does not vary in time.",
                    "units": "Dimensionless",
                },
                "Large scale rain rate": {
                    "description": "This parameter is the rate of rainfall (rainfall intensity), at the Earth's surface and  at the specified time, which is generated by the cloud scheme in the ECMWF Integrated  Forecasting System (IFS). The cloud scheme represents the formation and dissipation of  clouds and large-scale precipitation due to changes in atmospheric quantities (such as  pressure, temperature and moisture) predicted directly at spatial scales of the grid box  or larger. Rainfall can also be generated by the convection scheme in the IFS, which  represents convection at spatial scales smaller than the grid box. In the IFS,  precipitation is comprised of rain and snow.\nThis parameter is the rate the rainfall would have if it were spread evenly over the grid box. Since 1 kg of water spread over 1 square metre of surface is 1 mm deep (neglecting  the effects of temperature on the density of water), the units are equivalent to mm  per second.\nCare should be taken when comparing model parameters with observations, because  observations are often local to a particular point in space and time, rather than  representing averages over a model grid box.",
                    "units": "kg m^-2 s^-1",
                },
                "Large scale snowfall rate water equivalent": {
                    "description": "This parameter is the rate of snowfall (snowfall intensity), at the Earth's surface and  at the specified time, which is generated by the cloud scheme in the ECMWF Integrated  Forecasting System (IFS). The cloud scheme represents the formation and dissipation of  clouds and large-scale precipitation due to changes in atmospheric quantities (such as  pressure, temperature and moisture) predicted directly at spatial scales of the grid box  or larger. Snowfall can also be generated by the convection scheme in the IFS, which  represents convection at spatial scales smaller than the grid box. In the IFS,  precipitation is comprised of rain and snow.\nThis parameter is the rate the snowfall would have if it were spread evenly over the grid box. Since 1 kg of water spread over 1 square metre of surface is 1 mm deep (neglecting  the effects of temperature on the density of water), the units are equivalent to mm  (of liquid water) per second.\nCare should be taken when comparing model parameters with observations, because  observations are often local to a particular point in space and time, rather than  representing averages over a model grid box.",
                    "units": "kg m^-2 s^-1",
                },
                "Large-scale precipitation": {
                    "description": "This parameter is the accumulated precipitation that falls to the Earth's surface,  which is generated by the cloud scheme in the ECMWF Integrated Forecasting System (IFS).  The cloud scheme represents the formation and dissipation of clouds and large-scale  precipitation due to changes in atmospheric quantities (such as pressure, temperature  and moisture) predicted directly at spatial scales of the grid box or larger.  Precipitation can also be generated by the convection scheme in the IFS, which represents  convection at spatial scales smaller than the grid box. In the IFS, precipitation is  comprised of rain and snow.\nThis parameter is accumulated over a particular time period which depends on the data extracted.  For the reanalysis, the accumulation period is over the 1 hour ending at the validity date and time.  For the ensemble members, ensemble mean and ensemble spread, the accumulation period is over the  3 hours ending at the validity date and time.\nThe units of this parameter are depth in metres of water equivalent. It is the depth  the water would have if it were spread evenly over the grid box. \nCare should be taken when comparing model parameters with observations, because  observations are often local to a particular point in space and time, rather than  representing averages over a model grid box.",
                    "units": "m",
                },
                "Large-scale precipitation fraction": {
                    "description": "This parameter is the accumulation of the fraction of the grid box (0-1) that is  covered by large-scale precipitation.\nThis parameter is accumulated over a particular time period which depends on the data extracted.  For the reanalysis, the accumulation period is over the 1 hour ending at the validity date and time.  For the ensemble members, ensemble mean and ensemble spread, the accumulation period is over the  3 hours ending at the validity date and time.",
                    "units": "s",
                },
                "Large-scale snowfall": {
                    "description": "This parameter is the accumulated snow that falls to the Earth's surface, which is generated by  the cloud scheme in the ECMWF Integrated Forecasting System (IFS). The cloud scheme represents the  formation and dissipation of clouds and large-scale precipitation due to changes in atmospheric  quantities (such as pressure, temperature and moisture) predicted directly at spatial scales of the  grid box or larger. Snowfall can also be generated by the convection scheme in the IFS, which  represents convection at spatial scales smaller than the grid box. In the IFS, precipitation is  comprised of rain and snow.\nThis parameter is accumulated over a particular time period which depends on the data extracted.  For the reanalysis, the accumulation period is over the 1 hour ending at the validity date and time.  For the ensemble members, ensemble mean and ensemble spread, the accumulation period is over the  3 hours ending at the validity date and time.\nThe units of this parameter are depth in metres of water equivalent. It is the depth  the water would have if it were spread evenly over the grid box.\nCare should be taken when comparing model parameters with observations, because observations are often  local to a particular point in space and time, rather than representing averages over a model grid box.",
                    "units": "m of water equivalent",
                },
                "Leaf area index, high vegetation": {
                    "description": 'This parameter is the surface area of one side of all the leaves found over an area  of land for vegetation classified as "high". This parameter has a value of 0 over  bare ground or where there are no leaves. It can be calculated daily from satellite  data. It is important for forecasting, for example, how much rainwater will be  intercepted by the vegetative canopy, rather than falling to the ground.\nThis is one of the parameters in the model that describes land surface vegetation.  "High vegetation" consists of evergreen trees, deciduous trees, mixed  forest/woodland, and interrupted forest.',
                    "units": "m^2 m^-2",
                },
                "Leaf area index, low vegetation": {
                    "description": 'This parameter is the surface area of one side of all the leaves found over an area  of land for vegetation classified as "low". This parameter has a value of 0 over  bare ground or where there are no leaves. It can be calculated daily from satellite  data. It is important for forecasting, for example, how much rainwater will be  intercepted by the vegetative canopy, rather than falling to the ground.\nThis is one of the parameters in the model that describes land surface vegetation.  "Low vegetation" consists of crops and mixed farming, irrigated crops, short grass,  tall grass, tundra, semidesert, bogs and marshes, evergreen shrubs, deciduous shrubs,  and water and land mixtures.',
                    "units": "m^2 m^-2",
                },
                "Low cloud cover": {
                    "description": 'This parameter is the proportion of a grid box covered by cloud occurring in the  lower levels of the troposphere. Low cloud is a single level field calculated from  cloud occurring on model levels with a pressure greater than 0.8 times the surface  pressure. So, if the surface pressure is 1000 hPa (hectopascal), low cloud would be  calculated using levels with a pressure greater than 800 hPa (below approximately 2km (assuming a "standard atmosphere")).\nAssumptions are made about the degree of overlap/randomness between clouds in  different model levels.\nThis parameter has values from 0 to 1.',
                    "units": "Dimensionless",
                },
                "Low vegetation cover": {
                    "description": 'This parameter is the fraction of the grid box that is covered with vegetation that  is classified as "low". The values vary between 0 and 1 but do not vary in time.\nThis is one of the parameters in the model that describes land surface vegetation.  "Low vegetation" consists of crops and mixed farming, irrigated crops, short grass,  tall grass, tundra, semidesert, bogs and marshes, evergreen shrubs, deciduous shrubs,  and water and land mixtures.',
                    "units": "Dimensionless",
                },
                "Maximum 2m temperature since previous post-processing": {
                    "description": "This parameter is the highest temperature of air at 2m above the surface of land,  sea or inland water since the parameter was last archived in a particular forecast.\n2m temperature is calculated by interpolating between the lowest model level and the  Earth's surface, taking account of the atmospheric conditions.\nThis parameter has units of kelvin (K). Temperature measured in kelvin can be  converted to degrees Celsius (°C) by subtracting 273.15.",
                    "units": "K",
                },
                "Maximum individual wave height": {
                    "description": "This parameter is an estimate of the height of the expected highest individual wave  within a 20 minute time window. It can be used as a guide to the likelihood of  extreme or freak waves.\nThe interactions between waves are non-linear and occasionally concentrate wave  energy giving a wave height considerably larger than the significant wave height.  If the maximum individual wave height is more than twice the significant wave height,  then the wave is considered as a freak wave. The significant wave height represents  the average height of the highest third of surface ocean/sea waves, generated by local winds and associated with swell.\nThe ocean/sea surface wave field consists of a combination of waves with different  heights, lengths and directions (known as the two-dimensional wave spectrum). This  parameter is derived statistically from the two-dimensional wave spectrum.\nThe wave spectrum can be decomposed into wind-sea waves, which are directly affected  by local winds, and swell, the waves that were generated by the wind at a different  location and time. This parameter takes account of both.",
                    "units": "m",
                },
                "Maximum total precipitation rate since previous post-processing": {
                    "description": "The total precipitation is calculated from the combined large-scale and convective  rainfall and snowfall rates every time step and the maximum is kept since the last  postprocessing.",
                    "units": "kg m^-2 s^-1",
                },
                "Mean boundary layer dissipation": {
                    "description": "This parameter is the mean rate of conversion of kinetic energy in the mean flow into heat, over the whole atmospheric column, per unit area, that is due to the effects of stress associated with turbulent eddies near the surface and turbulent orographic form drag. It is calculated by the ECMWF Integrated Forecasting System's turbulent diffusion and turbulent orographic form drag schemes. The turbulent eddies near the surface are related to the roughness of the surface. The turbulent orographic form drag is the stress due to the valleys, hills and mountains on horizontal scales below 5km, which are specified from land surface data at about 1 km resolution. (The dissipation associated with orographic features with horizontal scales between 5 km and the model grid-scale is accounted for by the sub-grid orographic scheme.)\nThis parameter is a mean over a particular time period (the processing period) which depends on the data extracted. For the reanalysis, the processing period is over the 1 hour ending at the validity date and time. For the ensemble members, ensemble mean and ensemble spread, the processing period is over the 3 hours ending at the validity date and time.",
                    "units": "W m^-2",
                },
                "Mean convective precipitation rate": {
                    "description": "This parameter is the rate of precipitation at the Earth's surface, which is  generated by the convection scheme in the ECMWF Integrated Forecasting System (IFS). The  convection scheme represents convection at spatial scales smaller than the grid box.  Precipitation can also be generated by the cloud scheme in the IFS, which represents the  formation and dissipation of clouds and large-scale precipitation due to changes in  atmospheric quantities (such as pressure, temperature and moisture) predicted directly at  spatial scales of the grid box or larger. In the IFS, precipitation is comprised of rain and  snow.\nThis parameter is a mean over a particular time period (the processing period) which depends on the data extracted. For the reanalysis, the processing period is over the 1 hour ending at the validity date and time. For the ensemble members, ensemble mean and ensemble spread, the processing period is over the 3 hours ending at the validity date and time.\nIt is the rate the precipitation would have if it were spread evenly over the grid box. 1 kg of water spread over 1 square metre of surface is 1 mm deep (neglecting the  effects of temperature on the density of water), therefore the units are equivalent to  mm (of liquid water) per second.\nCare should be taken when comparing model parameters with observations, because  observations are often local to a particular point in space and time, rather than  representing averages over a model grid box.",
                    "units": "kg m^-2 s^-1",
                },
                "Mean convective snowfall rate": {
                    "description": "This parameter is the rate of snowfall (snowfall intensity) at the Earth's surface, which is generated by the convection scheme in the ECMWF Integrated Forecasting System (IFS). The  convection scheme represents convection at spatial scales smaller than the grid box. Snowfall can also be generated by the cloud scheme in the IFS, which represents the formation  and dissipation of clouds and large-scale precipitation due to changes in atmospheric quantities  (such as pressure, temperature and moisture) predicted directly at spatial scales of the grid  box or larger. In the IFS, precipitation is comprised of rain and snow.\nThis parameter is a mean over a particular time period (the processing period) which depends on the data extracted. For the reanalysis, the processing period is over the 1 hour ending at the validity date and time. For the ensemble members, ensemble mean and ensemble spread, the processing period is over the 3 hours ending at the validity date and time.\nIt is the rate the snowfall would have if it were spread evenly over the grid box. Since 1 kg of water spread over 1 square metre of surface is 1 mm thick (neglecting  the effects of temperature on the density of water), the units are equivalent to mm  (of liquid water) per second.\nCare should be taken when comparing model parameters with observations, because  observations are often local to a particular point in space and time, rather than  representing averages over a model grid box.",
                    "units": "kg m^-2 s^-1",
                },
                "Mean direction of total swell": {
                    "description": 'This parameter is the mean direction of waves associated with swell.\nThe ocean/sea surface wave field consists of a combination of waves with different  heights, lengths and directions (known as the two-dimensional wave spectrum). The  wave spectrum can be decomposed into wind-sea waves, which are directly affected by  local winds, and swell, the waves that were generated by the wind at a different  location and time. This parameter takes account of all swell only. It is the mean over all frequencies and directions of the total swell spectrum.\nThe units are degrees true, which means the direction relative to the geographic  location of the north pole. It is the direction that waves are coming from, so  0 degrees means "coming from the north" and 90 degrees means "coming from the east".',
                    "units": "degrees",
                },
                "Mean direction of wind waves": {
                    "description": 'The mean direction of waves generated by local winds.\nThe ocean/sea surface wave field consists of a combination of waves with different  heights, lengths and directions (known as the two-dimensional wave spectrum). The  wave spectrum can be decomposed into wind-sea waves, which are directly affected  by local winds, and swell, the waves that were generated by the wind at a different  location and time. This parameter takes account of wind-sea waves only. It is the mean over all frequencies and directions of the total wind-sea wave spectrum.\nThe units are degrees true, which means the direction relative to the geographic  location of the north pole. It is the direction that waves are coming from, so  0 degrees means "coming from the north" and 90 degrees means "coming from the east".',
                    "units": "degrees",
                },
                "Mean eastward gravity wave surface stress": {
                    "description": "Air flowing over a surface exerts a stress (drag) that transfers momentum to the surface and slows the wind. This parameter is the component of the mean surface stress in an eastward direction, associated with low-level, orographic blocking and orographic gravity waves. It is calculated by the ECMWF Integrated Forecasting System's sub-grid orography scheme, which represents stress due to unresolved valleys, hills and mountains with horizontal scales between 5 km and the model grid-scale. (The stress associated  with orographic features with horizontal scales smaller than 5 km is accounted for by  the turbulent orographic form drag scheme).\nOrographic gravity waves are oscillations in the flow maintained by the buoyancy of  displaced air parcels, produced when air is deflected upwards by hills and  mountains. This process can create stress on the atmosphere at the Earth's  surface and at other levels in the atmosphere.\nPositive (negative) values indicate stress on the surface of the Earth in an eastward (westward) direction.\nThis parameter is a mean over a particular time period (the processing period) which depends on the data extracted. For the reanalysis, the processing period is over the 1 hour ending at the validity date and time. For the ensemble members, ensemble mean and ensemble spread, the processing period is over the 3 hours ending at the validity date and time.",
                    "units": "N m^-2",
                },
                "Mean eastward turbulent surface stress": {
                    "description": "Air flowing over a surface exerts a stress (drag) that transfers momentum to the surface and slows the wind. This parameter is the component of the mean surface stress in an eastward direction, associated with turbulent eddies near the surface and turbulent orographic form drag. It is calculated by the ECMWF Integrated Forecasting System's turbulent diffusion and turbulent orographic form drag schemes. The turbulent eddies near the surface are related to the roughness of the surface. The turbulent orographic form drag is the stress due to the valleys, hills and mountains on horizontal scales below 5km, which are specified from land surface data at about 1 km resolution. (The stress associated with orographic features with horizontal scales between 5 km and the model grid-scale is accounted for by the sub-grid orographic scheme.)\nPositive (negative) values indicate stress on the surface of the Earth in an eastward (westward) direction.\nThis parameter is a mean over a particular time period (the processing period) which depends on the data extracted. For the reanalysis, the processing period is over the 1 hour ending at the validity date and time. For the ensemble members, ensemble mean and ensemble spread, the processing period is over the 3 hours ending at the validity date and time.",
                    "units": "N m^-2",
                },
                "Mean evaporation rate": {
                    "description": "This parameter is the amount of water that has evaporated from the  Earth's surface, including a simplified representation of transpiration (from  vegetation), into vapour in the air above.\nThis parameter is a mean over a particular time period (the processing period) which depends on the data extracted. For the reanalysis, the processing period is over the 1 hour ending at the validity date and time. For the ensemble members, ensemble mean and ensemble spread, the processing period is over the 3 hours ending at the validity date and time.\nThe ECMWF Integrated Forecasting System (IFS) convention is that downward fluxes are  positive. Therefore, negative values indicate evaporation and positive values indicate  condensation.",
                    "units": "kg m^-2 s^-1",
                },
                "Mean gravity wave dissipation": {
                    "description": "This parameter is the mean rate of conversion of kinetic energy in the mean flow into heat, over the whole atmospheric column, per unit area, that is due to the effects of stress associated with low-level, orographic blocking and orographic gravity waves. It is calculated by the ECMWF Integrated Forecasting System's sub-grid orography scheme, which represents stress due to unresolved valleys, hills and mountains with horizontal scales between 5 km and the model grid-scale. (The dissipation associated  with orographic features with horizontal scales smaller than 5 km is accounted for by  the turbulent orographic form drag scheme).\nOrographic gravity waves are oscillations in the flow maintained by the buoyancy of  displaced air parcels, produced when air is deflected upwards by hills and  mountains. This process can create stress on the atmosphere at the Earth's  surface and at other levels in the atmosphere.\nThis parameter is a mean over a particular time period (the processing period) which depends on the data extracted. For the reanalysis, the processing period is over the 1 hour ending at the validity date and time. For the ensemble members, ensemble mean and ensemble spread, the processing period is over the 3 hours ending at the validity date and time.",
                    "units": "W m^-2",
                },
                "Mean large-scale precipitation fraction": {
                    "description": "This parameter is the mean of the fraction of the grid box (0-1) that is  covered by large-scale precipitation.\nThis parameter is a mean over a particular time period (the processing period) which depends on the data extracted. For the reanalysis, the processing period is over the 1 hour ending at the validity date and time. For the ensemble members, ensemble mean and ensemble spread, the processing period is over the 3 hours ending at the validity date and time.",
                    "units": "Dimensionless",
                },
                "Mean large-scale precipitation rate": {
                    "description": "This parameter is the rate of precipitation at the Earth's surface, which is generated by the  cloud scheme in the ECMWF Integrated Forecasting System (IFS). The cloud scheme represents the  formation and dissipation of clouds and large-scale precipitation due to changes in atmospheric  quantities (such as pressure, temperature and moisture) predicted directly at spatial scales  of the grid box or larger. Precipitation can also be generated by the convection scheme in the  IFS, which represents convection at spatial scales smaller than the grid box. In the IFS,  precipitation is comprised of rain and snow.\nThis parameter is a mean over a particular time period (the processing period) which depends on the data extracted. For the reanalysis, the processing period is over the 1 hour ending at the validity date and time. For the ensemble members, ensemble mean and ensemble spread, the processing period is over the 3 hours ending at the validity date and time.\nIt is the rate the precipitation would have if it were spread evenly over the grid box. Since 1 kg of water spread over 1 square metre of surface is 1 mm deep (neglecting  the effects of temperature on the density of water), the units are equivalent to mm  (of liquid water) per second.\nCare should be taken when comparing model parameters with observations, because  observations are often local to a particular point in space and time, rather than  representing averages over a model grid box.",
                    "units": "kg m^-2 s^-1",
                },
                "Mean large-scale snowfall rate": {
                    "description": "This parameter is the rate of snowfall (snowfall intensity) at the Earth's surface, which is  generated by the cloud scheme in the ECMWF Integrated Forecasting System (IFS). The cloud  scheme represents the formation and dissipation of clouds and large-scale precipitation due  to changes in atmospheric quantities (such as pressure, temperature and moisture) predicted  directly at spatial scales of the grid box or larger. Snowfall can also be generated by the  convection scheme in the IFS, which represents convection at spatial scales smaller than the  grid box. In the IFS, precipitation is comprised of rain and snow.\nThis parameter is a mean over a particular time period (the processing period) which depends on the data extracted. For the reanalysis, the processing period is over the 1 hour ending at the validity date and time. For the ensemble members, ensemble mean and ensemble spread, the processing period is over the 3 hours ending at the validity date and time.\nIt is the rate the snowfall would have if it were spread evenly over the grid box. Since 1 kg of water spread over 1 square metre of surface is 1 mm deep (neglecting  the effects of temperature on the density of water), the units are equivalent to mm  (of liquid water) per second.\nCare should be taken when comparing model parameters with observations, because  observations are often local to a particular point in space and time, rather than  representing averages over a model grid box.",
                    "units": "kg m^-2 s^-1",
                },
                "Mean northward gravity wave surface stress": {
                    "description": "Air flowing over a surface exerts a stress (drag) that transfers momentum to the surface and slows the wind. This parameter is the component of the mean surface stress in a northward direction, associated with low-level, orographic blocking and orographic gravity waves. It is calculated by the ECMWF Integrated Forecasting System's sub-grid orography scheme, which represents stress due to unresolved valleys, hills and mountains with horizontal scales between 5 km and the model grid-scale. (The stress associated  with orographic features with horizontal scales smaller than 5 km is accounted for by  the turbulent orographic form drag scheme).\nOrographic gravity waves are oscillations in the flow maintained by the buoyancy of  displaced air parcels, produced when air is deflected upwards by hills and  mountains. This process can create stress on the atmosphere at the Earth's  surface and at other levels in the atmosphere.\nPositive (negative) values indicate stress on the surface of the Earth in a northward (southward) direction.\nThis parameter is a mean over a particular time period (the processing period) which depends on the data extracted. For the reanalysis, the processing period is over the 1 hour ending at the validity date and time. For the ensemble members, ensemble mean and ensemble spread, the processing period is over the 3 hours ending at the validity date and time.",
                    "units": "N m^-2",
                },
                "Mean northward turbulent surface stress": {
                    "description": "Air flowing over a surface exerts a stress (drag) that transfers momentum to the surface and slows the wind. This parameter is the component of the mean surface stress in a northward direction, associated with turbulent eddies near the surface and turbulent orographic form drag. It is calculated by the ECMWF Integrated Forecasting System's turbulent diffusion and turbulent orographic form drag schemes. The turbulent eddies near the surface are related to the roughness of the surface. The turbulent orographic form drag is the stress due to the valleys, hills and mountains on horizontal scales below 5km, which are specified from land surface data at about 1 km resolution. (The stress associated with orographic features with horizontal scales between 5 km and the model grid-scale is accounted for by the sub-grid orographic scheme.)\nPositive (negative) values indicate stress on the surface of the Earth in a northward (southward) direction.\nThis parameter is a mean over a particular time period (the processing period) which depends on the data extracted. For the reanalysis, the processing period is over the 1 hour ending at the validity date and time. For the ensemble members, ensemble mean and ensemble spread, the processing period is over the 3 hours ending at the validity date and time.",
                    "units": "N m^-2",
                },
                "Mean period of total swell": {
                    "description": "This parameter is the average time it takes for two consecutive wave crests, on  the surface of the ocean/sea associated with swell, to pass through a fixed  point.\nThe ocean/sea surface wave field consists of a combination of waves with  different heights, lengths and directions (known as the two-dimensional wave  spectrum). The wave spectrum can be decomposed into wind-sea waves, which are  directly affected by local winds, and swell, the waves that were generated by  the wind at a different location and time. This parameter takes account of all  swell only. It is the mean over all frequencies and directions of the total  swell spectrum.",
                    "units": "s",
                },
                "Mean period of wind waves": {
                    "description": "This parameter is the average time it takes for two consecutive wave crests, on  the surface of the ocean/sea generated by local winds, to pass through a fixed  point.\nThe ocean/sea surface wave field consists of a combination of waves with  different heights, lengths and directions (known as the two-dimensional wave  spectrum). The wave spectrum can be decomposed into wind-sea waves, which are  directly affected by local winds, and swell, the waves that were generated by  the wind at a different location and time. This parameter takes account of  wind-sea waves only. It is the mean over all frequencies and directions of the  total wind-sea spectrum.",
                    "units": "s",
                },
                "Mean potential evaporation rate": {
                    "description": 'This parameter is a measure of the extent to which near-surface atmospheric conditions are  conducive to the process of evaporation. It is usually considered to be the amount of  evaporation, under existing atmospheric conditions, from a surface of pure water which has the  temperature of the lowest layer of the atmosphere and gives an indication of the maximum  possible evaporation.\nPotential evaporation in the current ECMWF Integrated Forecasting System (IFS) is based on  surface energy balance calculations with the vegetation parameters set to "crops/mixed farming"  and assuming "no stress from soil moisture". In other words, evaporation is computed for  agricultural land as if it is well watered and assuming that the atmosphere is not affected by  this artificial surface condition. The latter may not always be realistic. Although potential  evaporation is meant to provide an estimate of irrigation requirements, the method can give  unrealistic results in arid conditions due to too strong evaporation forced by dry air.\nThis parameter is a mean over a particular time period (the processing period) which depends on the data extracted. For the reanalysis, the processing period is over the 1 hour ending at the validity date and time. For the ensemble members, ensemble mean and ensemble spread, the processing period is over the 3 hours ending at the validity date and time.',
                    "units": "kg m^-2 s^-1",
                },
                "Mean runoff rate": {
                    "description": "Some water from rainfall, melting snow, or deep in the soil, stays stored in the soil. Otherwise,  the water drains away, either over the surface (surface runoff), or under the ground (sub-surface  runoff) and the sum of these two is called runoff.\nThis parameter is a mean over a particular time period (the processing period) which depends on the data extracted. For the reanalysis, the processing period is over the 1 hour ending at the validity date and time. For the ensemble members, ensemble mean and ensemble spread, the processing period is over the 3 hours ending at the validity date and time.\nIt is the rate the runoff would have if it were spread evenly over the grid box. Care should be  taken when comparing model parameters with observations, because observations are often local to  a particular point rather than averaged over a grid box. \nRunoff is a measure of the availability of water in the soil, and can, for example, be used as an  indicator of drought or flood.",
                    "units": "kg m^-2 s^-1",
                },
                "Mean sea level pressure": {
                    "description": "This parameter is the pressure (force per unit area) of the atmosphere at the surface of the Earth, adjusted to the height of mean sea level.\nIt is a measure of the weight that all the air in a column vertically above a point on the Earth's  surface would have, if the point were located at mean sea level. It is  calculated over all surfaces - land, sea and inland water.\nMaps of mean sea level pressure are used to identify the locations of low and high pressure weather  systems, often referred to as cyclones and anticyclones. Contours of mean sea level pressure also  indicate the strength of the wind. Tightly packed contours show stronger winds.\nThe units of this parameter are pascals (Pa). Mean sea level pressure is often measured in hPa and  sometimes is presented in the old units of millibars, mb (1 hPa = 1 mb = 100 Pa).",
                    "units": "Pa",
                },
                "Mean snow evaporation rate": {
                    "description": "This parameter is the average rate of snow evaporation from the snow-covered area of a grid box  into vapour in the air above.\nThe ECMWF Integrated Forecasting System (IFS) represents snow as a single additional layer over the  uppermost soil level. The snow may cover all or part of the grid box.\nThis parameter is a mean over a particular time period (the processing period) which depends on the data extracted. For the reanalysis, the processing period is over the 1 hour ending at the validity date and time. For the ensemble members, ensemble mean and ensemble spread, the processing period is over the 3 hours ending at the validity date and time.\nIt is the rate the snow evaporation would have if it were spread evenly over the grid box. 1 kg of water spread over 1 square metre of surface is 1 mm deep (neglecting the  effects of temperature on the density of water), therefore the units are equivalent to  mm (of liquid water) per second.\nThe IFS convention is that downward fluxes are positive. Therefore, negative values indicate  evaporation and positive values indicate deposition.",
                    "units": "kg m^-2 s^-1",
                },
                "Mean snowfall rate": {
                    "description": "This parameter is the rate of snowfall at the Earth's surface. It is the sum of large-scale  and convective snowfall. Large-scale snowfall is generated by the cloud scheme in the ECMWF Integrated Forecasting System (IFS). The cloud scheme represents the formation and dissipation of  clouds and large-scale precipitation due to changes in atmospheric quantities (such as pressure,  temperature and moisture) predicted directly at spatial scales of the grid box or larger.  Convective snowfall is generated by the convection scheme in the IFS, which represents convection at  spatial scales smaller than the grid box. In the IFS, precipitation is comprised of rain and snow.\nThis parameter is a mean over a particular time period (the processing period) which depends on the data extracted. For the reanalysis, the processing period is over the 1 hour ending at the validity date and time. For the ensemble members, ensemble mean and ensemble spread, the processing period is over the 3 hours ending at the validity date and time.\nIt is the rate the snowfall would have if it were spread evenly over the grid box. 1 kg of water spread over 1 square metre of surface is 1 mm deep (neglecting the  effects of temperature on the density of water), therefore the units are equivalent to  mm (of liquid water) per second.\nCare should be taken when comparing model parameters with observations, because observations are often  local to a particular point in space and time, rather than representing averages over a model grid box.",
                    "units": "kg m^-2 s^-1",
                },
                "Mean snowmelt rate": {
                    "description": "This parameter is the rate of snow melt in the snow-covered area of a grid box.\nThe ECMWF Integrated Forecasting System (IFS) represents snow as a single additional layer over the  uppermost soil level. The snow may cover all or part of the grid box.\nThis parameter is a mean over a particular time period (the processing period) which depends on the data extracted. For the reanalysis, the processing period is over the 1 hour ending at the validity date and time. For the ensemble members, ensemble mean and ensemble spread, the processing period is over the 3 hours ending at the validity date and time.\nIt is the rate the melting would have if it were spread evenly over the grid box. 1 kg of water spread over 1 square metre of surface is 1 mm deep (neglecting the  effects of temperature on the density of water), therefore the units are equivalent to  mm (of liquid water) per second.",
                    "units": "kg m^-2 s^-1",
                },
                "Mean square slope of waves": {
                    "description": "This parameter can be related analytically to the average slope of combined  wind-sea and swell waves. It can also be expressed as a function of wind speed  under some statistical assumptions. The higher the slope, the steeper the  waves. This parameter indicates the roughness of the sea/ocean surface which  affects the interaction between ocean and atmosphere.\nThe ocean/sea surface wave field consists of a combination of waves with  different heights, lengths and directions (known as the two-dimensional wave  spectrum). This parameter is derived statistically from the two-dimensional  wave spectrum.",
                    "units": "Dimensionless",
                },
                "Mean sub-surface runoff rate": {
                    "description": "Some water from rainfall, melting snow, or deep in the soil, stays stored in the soil. Otherwise,  the water drains away, either over the surface (surface runoff), or under the ground (sub-surface  runoff) and the sum of these two is called runoff.\nThis parameter is a mean over a particular time period (the processing period) which depends on the data extracted. For the reanalysis, the processing period is over the 1 hour ending at the validity date and time. For the ensemble members, ensemble mean and ensemble spread, the processing period is over the 3 hours ending at the validity date and time.\nIt is the rate the runoff would have if it were spread evenly over the grid box. Care should be  taken when comparing model parameters with observations, because observations are often local to  a particular point rather than averaged over a grid box. \nRunoff is a measure of the availability of water in the soil, and can, for example, be used as an  indicator of drought or flood.",
                    "units": "kg m^-2 s^-1",
                },
                "Mean surface direct short-wave radiation flux": {
                    "description": "This parameter is the amount of direct solar radiation (also known as shortwave radiation) reaching  the surface of the Earth. It is the amount of radiation passing through a horizontal plane.\nSolar radiation at the surface can be direct or diffuse. Solar radiation can be scattered in all  directions by particles in the atmosphere, some of which reaches the surface (diffuse solar  radiation). Some solar radiation reaches the surface without being scattered (direct solar radiation).\nThis parameter is a mean over a particular time period (the processing period) which depends on the data extracted. For the reanalysis, the processing period is over the 1 hour ending at the validity date and time. For the ensemble members, ensemble mean and ensemble spread, the processing period is over the 3 hours ending at the validity date and time.\nThe ECMWF convention for vertical fluxes is positive downwards.",
                    "units": "W m^-2",
                },
                "Mean surface direct short-wave radiation flux, clear sky": {
                    "description": "This parameter is the amount of direct radiation from the Sun (also known as solar or  shortwave radiation) reaching the surface of the Earth, assuming clear-sky (cloudless)  conditions. It is the amount of radiation passing through a horizontal plane.\nSolar radiation at the surface can be direct or diffuse. Solar radiation can be  scattered in all directions by particles in the atmosphere, some of which reaches the  surface (diffuse solar radiation). Some solar radiation reaches the surface without  being scattered (direct solar radiation).\nClear-sky radiation quantities are computed for exactly the same atmospheric conditions  of temperature, humidity, ozone, trace gases and aerosol as the corresponding total-sky  quantities (clouds included), but assuming that the clouds are not there.\nThis parameter is a mean over a particular time period (the processing period) which depends on the data extracted. For the reanalysis, the processing period is over the 1 hour ending at the validity date and time. For the ensemble members, ensemble mean and ensemble spread, the processing period is over the 3 hours ending at the validity date and time.\nThe ECMWF convention for vertical fluxes is positive downwards.",
                    "units": "W m^-2",
                },
                "Mean surface downward UV radiation flux": {
                    "description": "This parameter is the amount of ultraviolet (UV) radiation reaching the surface. It  is the amount of radiation passing through a horizontal plane.\nUV radiation is part of the electromagnetic spectrum emitted by the Sun that has  wavelengths shorter than visible light. In the ECMWF Integrated Forecasting system  (IFS) it is defined as radiation with a wavelength of 0.20-0.44 µm (microns, 1  millionth of a metre).\nSmall amounts of UV are essential for living organisms, but overexposure may result  in cell damage; in humans this includes acute and chronic health effects on the skin,  eyes and immune system. UV radiation is absorbed by the ozone layer, but some reaches  the surface. The depletion of the ozone layer is causing concern over an increase in  the damaging effects of UV.\nThis parameter is a mean over a particular time period (the processing period) which depends on the data extracted. For the reanalysis, the processing period is over the 1 hour ending at the validity date and time. For the ensemble members, ensemble mean and ensemble spread, the processing period is over the 3 hours ending at the validity date and time.\nThe ECMWF convention for vertical fluxes is positive downwards.",
                    "units": "W m^-2",
                },
                "Mean surface downward long-wave radiation flux": {
                    "description": "This parameter is the amount of thermal (also known as longwave or terrestrial) radiation emitted by the  atmosphere and clouds that reaches a horizontal plane at the surface of the Earth.\nThe surface of the Earth emits thermal radiation, some of which is absorbed by the atmosphere and clouds. The  atmosphere and clouds likewise emit thermal radiation in all directions, some of which reaches the surface (represented by this parameter).\nThis parameter is a mean over a particular time period (the processing period) which depends on the data extracted. For the reanalysis, the processing period is over the 1 hour ending at the validity date and time. For the ensemble members, ensemble mean and ensemble spread, the processing period is over the 3 hours ending at the validity date and time.\nThe ECMWF convention for vertical fluxes is positive downwards.",
                    "units": "W m^-2",
                },
                "Mean surface downward long-wave radiation flux, clear sky": {
                    "description": "This parameter is the amount of thermal (also known as longwave or terrestrial) radiation emitted by the  atmosphere that reaches a horizontal plane at the surface of the Earth, assuming clear-sky (cloudless) conditions.\nThe surface of the Earth emits thermal radiation, some of which is absorbed by the atmosphere and clouds. The  atmosphere and clouds likewise emit thermal radiation in all directions, some of which reaches the surface.\nClear-sky radiation quantities are computed for exactly the same atmospheric conditions of temperature,  humidity, ozone, trace gases and aerosol as the corresponding total-sky quantities (clouds included),  but assuming that the clouds are not there.\nThis parameter is a mean over a particular time period (the processing period) which depends on the data extracted. For the reanalysis, the processing period is over the 1 hour ending at the validity date and time. For the ensemble members, ensemble mean and ensemble spread, the processing period is over the 3 hours ending at the validity date and time.\nThe ECMWF convention for vertical fluxes is positive downwards.",
                    "units": "W m^-2",
                },
                "Mean surface downward short-wave radiation flux": {
                    "description": "This parameter is the amount of solar radiation (also known as shortwave radiation) that reaches a horizontal  plane at the surface of the Earth. This parameter comprises both direct and diffuse solar radiation.\nRadiation from the Sun (solar, or shortwave, radiation) is partly reflected back to space by clouds and  particles in the atmosphere (aerosols) and some of it is absorbed. The rest is incident on the Earth's surface  (represented by this parameter).\nTo a reasonably good approximation, this parameter is the model equivalent of what would be measured by a  pyranometer (an instrument used for measuring solar radiation) at the surface. However, care should be taken  when comparing model parameters with observations, because observations are often local to a particular point  in space and time, rather than representing averages over a model grid box.\nThis parameter is a mean over a particular time period (the processing period) which depends on the data extracted. For the reanalysis, the processing period is over the 1 hour ending at the validity date and time. For the ensemble members, ensemble mean and ensemble spread, the processing period is over the 3 hours ending at the validity date and time.\nThe ECMWF convention for vertical fluxes is positive downwards.",
                    "units": "W m^-2",
                },
                "Mean surface downward short-wave radiation flux, clear sky": {
                    "description": "This parameter is the amount of solar radiation (also known as shortwave radiation) that reaches a horizontal  plane at the surface of the Earth, assuming clear-sky (cloudless) conditions. This parameter comprises both direct and diffuse solar radiation.\nRadiation from the Sun (solar, or shortwave, radiation) is partly reflected back to space by clouds and  particles in the atmosphere (aerosols) and some of it is absorbed. The rest is incident on the Earth's surface.\nClear-sky radiation quantities are computed for exactly the same atmospheric conditions of temperature,  humidity, ozone, trace gases and aerosol as the corresponding total-sky quantities (clouds included),  but assuming that the clouds are not there.\nThis parameter is a mean over a particular time period (the processing period) which depends on the data extracted. For the reanalysis, the processing period is over the 1 hour ending at the validity date and time. For the ensemble members, ensemble mean and ensemble spread, the processing period is over the 3 hours ending at the validity date and time.\nThe ECMWF convention for vertical fluxes is positive downwards.",
                    "units": "W m^-2",
                },
                "Mean surface latent heat flux": {
                    "description": "This parameter is the transfer of latent heat (resulting from water phase changes, such as  evaporation or condensation) between the Earth's surface and the atmosphere through the effects of  turbulent air motion. Evaporation from the Earth's surface represents a transfer of energy from  the surface to the atmosphere.\nThis parameter is a mean over a particular time period (the processing period) which depends on the data extracted. For the reanalysis, the processing period is over the 1 hour ending at the validity date and time. For the ensemble members, ensemble mean and ensemble spread, the processing period is over the 3 hours ending at the validity date and time.\nThe ECMWF convention for vertical fluxes is positive downwards.",
                    "units": "W m^-2",
                },
                "Mean surface net long-wave radiation flux": {
                    "description": "Thermal radiation (also known as longwave or terrestrial radiation) refers to radiation emitted by the  atmosphere, clouds and the surface of the Earth. This parameter is the difference between downward and upward thermal radiation at the surface of the Earth. It is the amount of radiation passing through a  horizontal plane.\nThe atmosphere and clouds emit thermal radiation in all directions, some of which reaches the surface as  downward thermal radiation. The upward thermal radiation at the surface consists of thermal radiation emitted by the surface plus the fraction of downwards thermal radiation reflected upward by the surface.\nThis parameter is a mean over a particular time period (the processing period) which depends on the data extracted. For the reanalysis, the processing period is over the 1 hour ending at the validity date and time. For the ensemble members, ensemble mean and ensemble spread, the processing period is over the 3 hours ending at the validity date and time.\nThe ECMWF convention for vertical fluxes is positive downwards.",
                    "units": "W m^-2",
                },
                "Mean surface net long-wave radiation flux, clear sky": {
                    "description": "Thermal radiation (also known as longwave or terrestrial radiation) refers to radiation emitted by the  atmosphere, clouds and the surface of the Earth. This parameter is the difference between downward and upward thermal radiation at the surface of the Earth, assuming clear-sky (cloudless) conditions. It is  the amount of radiation passing through a horizontal plane.\nClear-sky radiation quantities are computed for exactly the same atmospheric conditions of temperature,  humidity, ozone, trace gases and aerosol as the corresponding total-sky quantities (clouds included),  but assuming that the clouds are not there.\nThe atmosphere and clouds emit thermal radiation in all directions, some of which reaches the surface  as downward thermal radiation. The upward thermal radiation at the surface consists of thermal radiation emitted by the surface plus the fraction of downwards thermal radiation reflected upward by the surface.\nThis parameter is a mean over a particular time period (the processing period) which depends on the data extracted. For the reanalysis, the processing period is over the 1 hour ending at the validity date and time. For the ensemble members, ensemble mean and ensemble spread, the processing period is over the 3 hours ending at the validity date and time.\nThe ECMWF convention for vertical fluxes is positive downwards.",
                    "units": "W m^-2",
                },
                "Mean surface net short-wave radiation flux": {
                    "description": "This parameter is the amount of solar radiation (also known as shortwave radiation) that reaches a  horizontal plane at the surface of the Earth (both direct and diffuse) minus the amount reflected by the Earth's surface (which is governed by the albedo).\nRadiation from the Sun (solar, or shortwave, radiation) is partly reflected back to space by clouds and  particles in the atmosphere (aerosols) and some of it is absorbed. The remainder is incident on the  Earth's surface, where some of it is reflected.\nThis parameter is a mean over a particular time period (the processing period) which depends on the data extracted. For the reanalysis, the processing period is over the 1 hour ending at the validity date and time. For the ensemble members, ensemble mean and ensemble spread, the processing period is over the 3 hours ending at the validity date and time.\nThe ECMWF convention for vertical fluxes is positive downwards.",
                    "units": "W m^-2",
                },
                "Mean surface net short-wave radiation flux, clear sky": {
                    "description": "This parameter is the amount of solar (shortwave) radiation reaching the surface of the Earth (both direct  and diffuse) minus the amount reflected by the Earth's surface (which is governed by the albedo), assuming  clear-sky (cloudless) conditions. It is the amount of radiation passing through a horizontal plane.\nClear-sky radiation quantities are computed for exactly the same atmospheric conditions of temperature,  humidity, ozone, trace gases and aerosol as the corresponding total-sky quantities (clouds included), but assuming that the clouds are not there.\nRadiation from the Sun (solar, or shortwave, radiation) is partly reflected back to space by clouds and  particles in the atmosphere (aerosols) and some of it is absorbed. The rest is incident on the Earth's surface, where some of it is reflected. The difference between downward and reflected solar radiation is  the surface net solar radiation.\nThis parameter is a mean over a particular time period (the processing period) which depends on the data extracted. For the reanalysis, the processing period is over the 1 hour ending at the validity date and time. For the ensemble members, ensemble mean and ensemble spread, the processing period is over the 3 hours ending at the validity date and time.\nThe ECMWF convention for vertical fluxes is positive downwards.",
                    "units": "W m^-2",
                },
                "Mean surface runoff rate": {
                    "description": "Some water from rainfall, melting snow, or deep in the soil, stays stored in the soil. Otherwise, the  water drains away, either over the surface (surface runoff), or under the ground (sub-surface runoff) and the sum of these two is called runoff.\nThis parameter is a mean over a particular time period (the processing period) which depends on the data extracted. For the reanalysis, the processing period is over the 1 hour ending at the validity date and time. For the ensemble members, ensemble mean and ensemble spread, the processing period is over the 3 hours ending at the validity date and time.\nIt is the rate the runoff would have if it were spread evenly over the grid box. Care should be  taken when comparing model parameters with observations, because observations are often local to a  particular point rather than averaged over a grid box. \nRunoff is a measure of the availability of water in the soil, and can, for example, be used as an  indicator of drought or flood.",
                    "units": "kg m^-2 s^-1",
                },
                "Mean surface sensible heat flux": {
                    "description": "This parameter is the transfer of heat between the Earth's surface and the atmosphere through the effects  of turbulent air motion (but excluding any heat transfer resulting from condensation or evaporation).\nThe magnitude of the sensible heat flux is governed by the difference in temperature between the surface  and the overlying atmosphere, wind speed and the surface roughness. For example, cold air overlying a warm surface would produce a sensible heat flux from the land (or ocean) into the atmosphere.\nThis parameter is a mean over a particular time period (the processing period) which depends on the data extracted. For the reanalysis, the processing period is over the 1 hour ending at the validity date and time. For the ensemble members, ensemble mean and ensemble spread, the processing period is over the 3 hours ending at the validity date and time.\nThe ECMWF convention for vertical fluxes is positive downwards.",
                    "units": "W m^-2",
                },
                "Mean top downward short-wave radiation flux": {
                    "description": "This parameter is the incoming solar radiation (also known as shortwave radiation), received from the Sun,  at the top of the atmosphere. It is the amount of radiation passing through a horizontal plane. \nThis parameter is a mean over a particular time period (the processing period) which depends on the data extracted. For the reanalysis, the processing period is over the 1 hour ending at the validity date and time. For the ensemble members, ensemble mean and ensemble spread, the processing period is over the 3 hours ending at the validity date and time.\nThe ECMWF convention for vertical fluxes is positive downwards.",
                    "units": "W m^-2",
                },
                "Mean top net long-wave radiation flux": {
                    "description": "The thermal (also known as terrestrial or longwave) radiation emitted to space at the top of the atmosphere is  commonly known as the Outgoing Longwave Radiation (OLR). The top net thermal radiation (this parameter) is equal  to the negative of OLR.\nThis parameter is a mean over a particular time period (the processing period) which depends on the data extracted. For the reanalysis, the processing period is over the 1 hour ending at the validity date and time. For the ensemble members, ensemble mean and ensemble spread, the processing period is over the 3 hours ending at the validity date and time.\nThe ECMWF convention for vertical fluxes is positive downwards.",
                    "units": "W m^-2",
                },
                "Mean top net long-wave radiation flux, clear sky": {
                    "description": "This parameter is the thermal (also known as terrestrial or longwave) radiation emitted to space at the top of the  atmosphere, assuming clear-sky (cloudless) conditions. It is the amount passing through a horizontal plane. Note  that the ECMWF convention for vertical fluxes is positive downwards, so a flux from the atmosphere to space will  be negative.\nClear-sky radiation quantities are computed for exactly the same atmospheric conditions of temperature, humidity,  ozone, trace gases and aerosol as total-sky quantities (clouds included), but assuming that the clouds are not  there.\nThe thermal radiation emitted to space at the top of the atmosphere is commonly known as the Outgoing Longwave  Radiation (OLR) (i.e., taking a flux from the atmosphere to space as positive).\nThis parameter is a mean over a particular time period (the processing period) which depends on the data extracted. For the reanalysis, the processing period is over the 1 hour ending at the validity date and time. For the ensemble members, ensemble mean and ensemble spread, the processing period is over the 3 hours ending at the validity date and time.",
                    "units": "W m^-2",
                },
                "Mean top net short-wave radiation flux": {
                    "description": "This parameter is the incoming solar radiation (also known as shortwave radiation) minus the outgoing solar  radiation at the top of the atmosphere. It is the amount of radiation passing through a horizontal plane. The  incoming solar radiation is the amount received from the Sun. The outgoing solar radiation is the amount  reflected and scattered by the Earth's atmosphere and surface.\nThis parameter is a mean over a particular time period (the processing period) which depends on the data extracted. For the reanalysis, the processing period is over the 1 hour ending at the validity date and time. For the ensemble members, ensemble mean and ensemble spread, the processing period is over the 3 hours ending at the validity date and time.\nThe ECMWF convention for vertical fluxes is positive downwards.",
                    "units": "W m^-2",
                },
                "Mean top net short-wave radiation flux, clear sky": {
                    "description": "This parameter is the incoming solar radiation (also known as shortwave radiation) minus the outgoing solar  radiation at the top of the atmosphere, assuming clear-sky (cloudless) conditions. It is the amount of  radiation passing through a horizontal plane. The incoming solar radiation is the amount received from the Sun.  The outgoing solar radiation is the amount reflected and scattered by the Earth's atmosphere and surface,  assuming clear-sky (cloudless) conditions.\nClear-sky radiation quantities are computed for exactly the same atmospheric conditions of temperature, humidity,  ozone, trace gases and aerosol as the total-sky (clouds included) quantities, but assuming that the clouds are  not there.\nThis parameter is a mean over a particular time period (the processing period) which depends on the data extracted. For the reanalysis, the processing period is over the 1 hour ending at the validity date and time. For the ensemble members, ensemble mean and ensemble spread, the processing period is over the 3 hours ending at the validity date and time.\nThe ECMWF convention for vertical fluxes is positive downwards.",
                    "units": "W m^-2",
                },
                "Mean total precipitation rate": {
                    "description": "This parameter is the rate of precipitation at the Earth's surface. It is the sum of the rates due to  large-scale precipitation and convective precipitation. Large-scale precipitation is generated by the  cloud scheme in the ECMWF Integrated Forecasting System (IFS). The cloud scheme represents the formation  and dissipation of clouds and large-scale precipitation due to changes in atmospheric quantities (such  as pressure, temperature and moisture) predicted directly at spatial scales of the grid box or larger.  Convective precipitation is generated by the convection scheme in the IFS, which represents convection  at spatial scales smaller than the grid box. In the IFS, precipitation is comprised of rain and snow.\nThis parameter is a mean over a particular time period (the processing period) which depends on the data extracted. For the reanalysis, the processing period is over the 1 hour ending at the validity date and time. For the ensemble members, ensemble mean and ensemble spread, the processing period is over the 3 hours ending at the validity date and time.\nIt is the rate the precipitation would have if it were spread evenly over the grid box. 1 kg of water spread over 1 square metre of surface is 1 mm deep (neglecting the  effects of temperature on the density of water), therefore the units are equivalent to  mm (of liquid water) per second.\nCare should be taken when comparing model parameters with observations, because observations are  often local to a particular point in space and time, rather than representing averages over a model  grid box.",
                    "units": "kg m^-2 s^-1",
                },
                "Mean vertical gradient of refractivity inside trapping layer": {
                    "description": "Mean vertical gradient of atmospheric refractivity inside the trapping layer.",
                    "units": "m^-1",
                },
                "Mean vertically integrated moisture divergence": {
                    "description": "The vertical integral of the moisture flux is the horizontal rate of flow of moisture  (water vapour, cloud liquid and cloud ice), per metre across the flow, for a column of  air extending from the surface of the Earth to the top of the atmosphere. Its horizontal  divergence is the rate of moisture spreading outward from a point, per square metre.\nThis parameter is a mean over a particular time period (the processing period) which depends on the data extracted. For the reanalysis, the processing period is over the 1 hour ending at the validity date and time. For the ensemble members, ensemble mean and ensemble spread, the processing period is over the 3 hours ending at the validity date and time.\nThis parameter is positive for moisture that is spreading out, or diverging, and negative  for the opposite, for moisture that is concentrating, or converging (convergence). This  parameter thus indicates whether atmospheric motions act to decrease (for divergence) or  increase (for convergence) the vertical integral of moisture, over the time period. High  negative values of this parameter (i.e. large moisture convergence) can be related to  precipitation intensification and floods.\n1 kg of water spread over 1 square metre of surface is 1 mm deep (neglecting the effects  of temperature on the density of water), therefore the units are equivalent to mm (of  liquid water) per second.",
                    "units": "kg m^-2 s^-1",
                },
                "Mean wave direction": {
                    "description": 'This parameter is the mean direction of ocean/sea surface waves. The ocean/sea surface  wave field consists of a combination of waves with different heights, lengths and  directions (known as the two-dimensional wave spectrum). This parameter is a mean over  all frequencies and directions of the two-dimensional wave spectrum.\nThe wave spectrum can be decomposed into wind-sea waves, which are directly affected  by local winds, and swell, the waves that were generated by the wind at a different  location and time. This parameter takes account of both.\nThis parameter can be used to assess sea state and swell. For example, engineers use  this type of wave information when designing structures in the open ocean, such as oil  platforms, or in coastal applications.\nThe units are degrees true, which means the direction relative to the geographic  location of the north pole. It is the direction that waves are coming from, so  0 degrees means "coming from the north" and 90 degrees means "coming from the east".',
                    "units": "degree true",
                },
                "Mean wave direction of first swell partition": {
                    "description": 'This parameter is the mean direction of waves in the first swell partition.\nThe ocean/sea surface wave field consists of a combination of waves with different  heights, lengths and directions (known as the two-dimensional wave spectrum). The wave  spectrum can be decomposed into wind-sea waves, which are directly affected by local  winds, and swell, the waves that were generated by the wind at a different location and  time.\nIn many situations, swell can be made up of different swell systems, for example, from  two distant and separate storms. To account for this, the swell spectrum is partitioned  into up to three parts. The swell partitions are labelled first, second and third based  on their respective wave height. Therefore, there is no guarantee of spatial coherence  (the first swell partition might be from one system at one location and a different  system at the neighbouring location).\nThe units are degrees true, which means the direction relative to the geographic  location of the north pole. It is the direction that waves are coming from, so  0 degrees means "coming from the north" and 90 degrees means "coming from the east".',
                    "units": "degrees",
                },
                "Mean wave direction of second swell partition": {
                    "description": 'This parameter is the mean direction of waves in the second swell partition.\nThe ocean/sea surface wave field consists of a combination of waves with different  heights, lengths and directions (known as the two-dimensional wave spectrum). The wave  spectrum can be decomposed into wind-sea waves, which are directly affected by local  winds, and swell, the waves that were generated by the wind at a different location and  time.\nIn many situations, swell can be made up of different swell systems, for example, from  two distant and separate storms. To account for this, the swell spectrum is partitioned  into up to three parts. The swell partitions are labelled first, second and third based  on their respective wave height. Therefore, there is no guarantee of spatial coherence  (the first swell partition might be from one system at one location and a different  system at the neighbouring location).\nThe units are degrees true, which means the direction relative to the geographic  location of the north pole. It is the direction that waves are coming from, so  0 degrees means "coming from the north" and 90 degrees means "coming from the east".',
                    "units": "degrees",
                },
                "Mean wave direction of third swell partition": {
                    "description": 'This parameter is the mean direction of waves in the third swell partition.\nThe ocean/sea surface wave field consists of a combination of waves with different  heights, lengths and directions (known as the two-dimensional wave spectrum). The wave  spectrum can be decomposed into wind-sea waves, which are directly affected by local  winds, and swell, the waves that were generated by the wind at a different location and  time.\nIn many situations, swell can be made up of different swell systems, for example, from  two distant and separate storms. To account for this, the swell spectrum is partitioned  into up to three parts. The swell partitions are labelled first, second and third based  on their respective wave height. Therefore, there is no guarantee of spatial coherence  (the first swell partition might be from one system at one location and a different  system at the neighbouring location).\nThe units are degrees true, which means the direction relative to the geographic  location of the north pole. It is the direction that waves are coming from, so  0 degrees means "coming from the north" and 90 degrees means "coming from the east".',
                    "units": "degrees",
                },
                "Mean wave period": {
                    "description": "This parameter is the average time it takes for two consecutive wave crests, on the  surface of the ocean/sea, to pass through a fixed point. The ocean/sea surface wave  field consists of a combination of waves with different heights, lengths and directions  (known as the two-dimensional wave spectrum). This parameter is a mean over all  frequencies and directions of the two-dimensional wave spectrum.\nThe wave spectrum can be decomposed into wind-sea waves, which are directly affected by  local winds, and swell, the waves that were generated by the wind at a different location  and time. This parameter takes account of both.\nThis parameter can be used to assess sea state and swell. For example, engineers use such  wave information when designing structures in the open ocean, such as oil platforms, or  in coastal applications.",
                    "units": "s",
                },
                "Mean wave period based on first moment": {
                    "description": "This parameter is the reciprocal of the mean frequency of the wave components that  represent the sea state. All wave components have been averaged proportionally to their  respective amplitude. This parameter can be used to estimate the magnitude of Stokes  drift transport in deep water.\nThe ocean/sea surface wave field consists of a combination of waves with different heights,  lengths and directions (known as the two-dimensional wave spectrum). Moments are  statistical quantities derived from the two-dimensional wave spectrum.",
                    "units": "s",
                },
                "Mean wave period based on first moment for swell": {
                    "description": "This parameter is the reciprocal of the mean frequency of the wave components associated  with swell. All wave components have been averaged proportionally to their respective  amplitude. This parameter can be used to estimate the magnitude of Stokes drift transport  in deep water associated with swell.\nThe ocean/sea surface wave field consists of a combination of waves with different heights,  lengths and directions (known as the two-dimensional wave spectrum). The wave spectrum can  be decomposed into wind-sea waves, which are directly affected by local winds, and swell,  the waves that were generated by the wind at a different location and time. This parameter  takes account of all swell only. Moments are statistical quantities derived from the  two-dimensional wave spectrum.",
                    "units": "s",
                },
                "Mean wave period based on first moment for wind waves": {
                    "description": "This parameter is the reciprocal of the mean frequency of the wave components generated by  local winds. All wave components have been averaged proportionally to their respective  amplitude. This parameter can be used to estimate the magnitude of Stokes drift transport  in deep water associated with wind waves.\nThe ocean/sea surface wave field consists of a combination of waves with different heights,  lengths and directions (known as the two-dimensional wave spectrum). The wave spectrum can  be decomposed into wind-sea waves, which are directly affected by local winds, and swell,  the waves that were generated by the wind at a different location and time. This parameter  takes account of wind-sea waves only. Moments are statistical quantities derived from the  two-dimensional wave spectrum.",
                    "units": "s",
                },
                "Mean wave period based on second moment for swell": {
                    "description": "This parameter is equivalent to the zero-crossing mean wave period for swell. The  zero-crossing mean wave period represents the mean length of time between occasions where  the sea/ocean surface crosses a defined zeroth level (such as mean sea level).\nThe ocean/sea surface wave field consists of a combination of waves with different heights,  lengths and directions (known as the two-dimensional wave spectrum). The wave spectrum can  be decomposed into wind-sea waves, which are directly affected by local winds, and swell,  the waves that were generated by the wind at a different location and time. Moments are  statistical quantities derived from the two-dimensional wave spectrum.",
                    "units": "s",
                },
                "Mean wave period based on second moment for wind waves": {
                    "description": "This parameter is equivalent to the zero-crossing mean wave period for waves generated by  local winds. The zero-crossing mean wave period represents the mean length of time between  occasions where the sea/ocean surface crosses a defined zeroth level (such as mean sea  level).\nThe ocean/sea surface wave field consists of a combination of waves with different heights,  lengths and directions (known as the two-dimensional wave spectrum). The wave spectrum can  be decomposed into wind-sea waves, which are directly affected by local winds, and swell,  the waves that were generated by the wind at a different location and time. Moments are  statistical quantities derived from the two-dimensional wave spectrum.",
                    "units": "s",
                },
                "Mean wave period of first swell partition": {
                    "description": "This parameter is the mean period of waves in the first swell partition. The wave period  is the average time it takes for two consecutive wave crests, on the surface of the  ocean/sea, to pass through a fixed point.\nThe ocean/sea surface wave field consists of a combination of waves with different heights,  lengths and directions (known as the two-dimensional wave spectrum). The wave spectrum can  be decomposed into wind-sea waves, which are directly affected by local winds, and swell,  the waves that were generated by the wind at a different location and time.\nIn many situations, swell can be made up of different swell systems, for example, from two  distant and separate storms. To account for this, the swell spectrum is partitioned into  up to three parts. The swell partitions are labelled first, second and third based on their  respective wave height. Therefore, there is no guarantee of spatial coherence (the first  swell partition might be from one system at one location and a different system at the  neighbouring location).",
                    "units": "s",
                },
                "Mean wave period of second swell partition": {
                    "description": "This parameter is the mean period of waves in the second swell partition. The wave period  is the average time it takes for two consecutive wave crests, on the surface of the  ocean/sea, to pass through a fixed point.\nThe ocean/sea surface wave field consists of a combination of waves with different heights,  lengths and directions (known as the two-dimensional wave spectrum). The wave spectrum can  be decomposed into wind-sea waves, which are directly affected by local winds, and swell,  the waves that were generated by the wind at a different location and time.\nIn many situations, swell can be made up of different swell systems, for example, from two  distant and separate storms. To account for this, the swell spectrum is partitioned into up  to three parts. The swell partitions are labelled first, second and third based on their  respective wave height. Therefore, there is no guarantee of spatial coherence (the second  swell partition might be from one system at one location and a different system at the  neighbouring location).",
                    "units": "s",
                },
                "Mean wave period of third swell partition": {
                    "description": "This parameter is the mean period of waves in the third swell partition. The wave period is  the average time it takes for two consecutive wave crests, on the surface of the ocean/sea,  to pass through a fixed point.\nThe ocean/sea surface wave field consists of a combination of waves with different heights,  lengths and directions (known as the two-dimensional wave spectrum). The wave spectrum can  be decomposed into wind-sea waves, which are directly affected by local winds, and swell,  the waves that were generated by the wind at a different location and time.\nIn many situations, swell can be made up of different swell systems, for example, from two  distant and separate storms. To account for this, the swell spectrum is partitioned into up  to three parts. The swell partitions are labelled first, second and third based on their  respective wave height. Therefore, there is no guarantee of spatial coherence (the third  swell partition might be from one system at one location and a different system at the  neighbouring location).",
                    "units": "s",
                },
                "Mean zero-crossing wave period": {
                    "description": "This parameter represents the mean length of time between occasions where the sea/ocean  surface crosses mean sea level. In combination with wave height information, it could be  used to assess the length of time that a coastal structure might be under water, for  example.\nThe ocean/sea surface wave field consists of a combination of waves with different heights,  lengths and directions (known as the two-dimensional wave spectrum). In the ECMWF  Integrated Forecasting System (IFS) this parameter is calculated from the characteristics  of the two-dimensional wave spectrum.",
                    "units": "s",
                },
                "Medium cloud cover": {
                    "description": 'This parameter is the proportion of a grid box covered by cloud occurring in the middle  levels of the troposphere. Medium cloud is a single level field calculated from cloud  occurring on model levels with a pressure between 0.45 and 0.8 times the surface  pressure. So, if the surface pressure is 1000 hPa (hectopascal), medium cloud would be  calculated using levels with a pressure of less than or equal to 800 hPa and greater  than or equal to 450 hPa (between approximately 2km and 6km (assuming a "standard  atmosphere")).\nThe medium cloud parameter is calculated from cloud cover for the appropriate model  levels as described above. Assumptions are made about the degree of overlap/randomness  between clouds in different model levels.\nCloud fractions vary from 0 to 1.',
                    "units": "Dimensionless",
                },
                "Minimum 2m temperature since previous post-processing": {
                    "description": "This parameter is the lowest temperature of air at 2m above the surface of land, sea  or inland waters since the parameter was last archived in a particular forecast.\n2m temperature is calculated by interpolating between the lowest model level and the  Earth's surface, taking account of the atmospheric conditions. See further information.\nThis parameter has units of kelvin (K). Temperature measured in kelvin can be converted  to degrees Celsius (°C) by subtracting 273.15.",
                    "units": "K",
                },
                "Minimum total precipitation rate since previous post-processing": {
                    "description": "The total precipitation is calculated from the combined large-scale and convective  rainfall and snowfall rates every time step and the minimum is kept since the last  postprocessing.",
                    "units": "kg m^-2 s^-1",
                },
                "Minimum vertical gradient of refractivity inside trapping layer": {
                    "description": "Minimum vertical gradient of atmospheric refractivity inside the trapping layer.",
                    "units": "m^-1",
                },
                "Model bathymetry": {
                    "description": "This parameter is the depth of water from the surface to the bottom of the ocean. It is  used by the ocean wave model to specify the propagation properties of the different  waves that could be present.\nNote that the ocean wave model grid is too coarse to resolve some small islands and  mountains on the bottom of the ocean, but they can have an impact on surface ocean  waves. The ocean wave model has been modified to reduce the wave energy flowing around  or over features at spatial scales smaller than the grid box.",
                    "units": "m",
                },
                "Near IR albedo for diffuse radiation": {
                    "description": "Albedo is a measure of the reflectivity of the Earth's surface. This parameter is the  fraction of diffuse solar (shortwave) radiation with wavelengths between 0.7 and 4 µm  (microns, 1 millionth of a metre) reflected by the Earth's surface (for snow-free land  surfaces only). Values of this parameter vary between 0 and 1.\nIn the ECMWF Integrated Forecasting System (IFS) albedo is dealt with separately for  solar radiation with wavelengths greater/less than 0.7µm and for direct and diffuse  solar radiation (giving 4 components to albedo).\nSolar radiation at the surface can be direct or diffuse. Solar radiation can be  scattered in all directions by particles in the atmosphere, some of which reaches the  surface (diffuse solar radiation). Some solar radiation reaches the surface without  being scattered (direct solar radiation).\nIn the IFS, a climatological (observed values averaged over a period of several years)  background albedo is used which varies from month to month through the year, modified  by the model over water, ice and snow.",
                    "units": "Dimensionless",
                },
                "Near IR albedo for direct radiation": {
                    "description": "Albedo is a measure of the reflectivity of the Earth's surface. This parameter is the  fraction of direct solar (shortwave) radiation with wavelengths between 0.7 and 4 µm  (microns, 1 millionth of a metre) reflected by the Earth's surface (for snow-free land  surfaces only). Values of this parameter vary between 0 and 1.\nIn the ECMWF Integrated Forecasting System (IFS) albedo is dealt with separately for  solar radiation with wavelengths greater/less than 0.7µm and for direct and diffuse  solar radiation (giving 4 components to albedo).\nSolar radiation at the surface can be direct or diffuse. Solar radiation can be  scattered in all directions by particles in the atmosphere, some of which reaches the  surface (diffuse solar radiation). Some solar radiation reaches the surface without  being scattered (direct solar radiation).\nIn the IFS, a climatological (observed values averaged over a period of several years)  background albedo is used which varies from month to month through the year, modified  by the model over water, ice and snow.",
                    "units": "Dimensionless",
                },
                "Normalized energy flux into ocean": {
                    "description": "This parameter is the normalised vertical flux of turbulent kinetic energy from ocean  waves into the ocean. The energy flux is calculated from an estimation of the loss of  wave energy due to white capping waves. A white capping wave is one that appears white  at its crest as it breaks, due to air being mixed into the water. When waves break in  this way, there is a transfer of energy from the waves to the ocean. Such a flux is  defined to be negative.\nThe energy flux has units of Watts per metre squared, and this is normalised by being  divided by the product of air density and the cube of the friction velocity.",
                    "units": "Dimensionless",
                },
                "Normalized energy flux into waves": {
                    "description": "This parameter is the normalised vertical flux of energy from wind into the ocean waves.  A positive flux implies a flux into the waves.\nThe energy flux has units of Watts per metre squared, and this is normalised by being  divided by the product of air density and the cube of the friction velocity.",
                    "units": "Dimensionless",
                },
                "Normalized stress into ocean": {
                    "description": "This parameter is the normalised surface stress, or momentum flux, from the air into the  ocean due to turbulence at the air-sea interface and breaking waves. It does not include  the flux used to generate waves. The ECMWF convention for vertical fluxes is positive  downwards.\nThe stress has units of Newtons per metre squared, and this is normalised by being divided  by the product of air density and the square of the friction velocity.",
                    "units": "Dimensionless",
                },
                "Northward gravity wave surface stress": {
                    "description": "Air flowing over a surface exerts a stress (drag) that transfers momentum to the surface and slows the wind. This parameter is the component of the accumulated surface stress in a northward direction, associated with low-level, orographic blocking and orographic gravity waves. It is calculated by the ECMWF Integrated Forecasting System's sub-grid orography scheme, which represents stress due to unresolved valleys, hills and mountains with horizontal scales between 5 km and the model grid-scale. (The stress associated  with orographic features with horizontal scales smaller than 5 km is accounted for by  the turbulent orographic form drag scheme).\nOrographic gravity waves are oscillations in the flow maintained by the buoyancy of  displaced air parcels, produced when air is deflected upwards by hills and  mountains. This process can create stress on the atmosphere at the Earth's  surface and at other levels in the atmosphere.\nPositive (negative) values indicate stress on the surface of the Earth in a northward (southward) direction.\nThis parameter is accumulated over a particular time period which depends on the data extracted.  For the reanalysis, the accumulation period is over the 1 hour ending at the validity date and time.  For the ensemble members, ensemble mean and ensemble spread, the accumulation period is over the  3 hours ending at the validity date and time.",
                    "units": "N m^-2 s",
                },
                "Northward turbulent surface stress": {
                    "description": "Air flowing over a surface exerts a stress (drag) that transfers momentum to the surface and slows the wind. This parameter is the component of the accumulated surface stress in a northward direction, associated with turbulent eddies near the surface and turbulent orographic form drag. It is calculated by the ECMWF Integrated Forecasting System's turbulent diffusion and turbulent orographic form drag schemes. The turbulent eddies near the surface are related to the roughness of the surface. The turbulent orographic form drag is the stress due to the valleys, hills and mountains on horizontal scales below 5km, which are specified from land surface data at about 1 km resolution. (The stress associated with orographic features with horizontal scales between 5 km and the model grid-scale is accounted for by the sub-grid orographic scheme.)\nPositive (negative) values indicate stress on the surface of the Earth in a northward (southward) direction.\nThis parameter is accumulated over a particular time period which depends on the data extracted.  For the reanalysis, the accumulation period is over the 1 hour ending at the validity date and time.  For the ensemble members, ensemble mean and ensemble spread, the accumulation period is over the  3 hours ending at the validity date and time.",
                    "units": "N m^-2 s",
                },
                "Ocean surface stress equivalent 10m neutral wind direction": {
                    "description": 'This parameter is the direction from which the "neutral wind" blows, in degrees clockwise  from true north, at a height of ten metres above the surface of the Earth.\nThe neutral wind is calculated from the surface stress and roughness length by assuming  that the air is neutrally stratified. The neutral wind is, by definition, in the direction  of the surface stress. The size of the roughness length depends on the sea state.\nThis parameter is the wind direction used to force the wave model, therefore it is only  calculated over water bodies represented in the ocean wave model. It is interpolated from  the atmospheric model\'s horizontal grid onto the horizontal grid used by the ocean wave model.',
                    "units": "degrees",
                },
                "Ocean surface stress equivalent 10m neutral wind speed": {
                    "description": 'This parameter is the horizontal speed of the "neutral wind", at a height of ten metres  above the surface of the Earth. The units of this parameter are metres per second.\nThe neutral wind is calculated from the surface stress and roughness length by assuming  that the air is neutrally stratified. The neutral wind is, by definition, in the direction  of the surface stress. The size of the roughness length depends on the sea state.\nThis parameter is the wind speed used to force the wave model, therefore it is only  calculated over water bodies represented in the ocean wave model. It is interpolated from  the atmospheric model\'s horizontal grid onto the horizontal grid used by the ocean wave model.',
                    "units": "m s^-1",
                },
                "Geopotential": {
                    "description": "This parameter is the gravitational potential energy of a unit mass, at a particular location at the surface of the Earth, relative to mean sea level. It is also the amount of work that would have to be done, against the force of gravity, to lift a unit mass to that location from mean sea level.\nThe (surface) geopotential height (orography) can be calculated by dividing the (surface) geopotential by the Earth's gravitational acceleration, g (=9.80665 m s^-2 ).\nThis parameter does not vary in time.",
                    "units": "m^2 s^-2",
                },
                "Peak wave period": {
                    "description": "This parameter represents the period of the most energetic ocean waves generated by local winds  and associated with swell. The wave period is the average time it takes for two consecutive wave  crests, on the surface of the ocean/sea, to pass through a fixed point.\nThe ocean/sea surface wave field consists of a combination of waves with different heights,  lengths and directions (known as the two-dimensional wave spectrum). This parameter is  calculated from the reciprocal of the frequency corresponding to the largest value (peak) of the  frequency wave spectrum. The frequency wave spectrum is obtained by integrating the  two-dimensional wave spectrum over all directions.\nThe wave spectrum can be decomposed into wind-sea waves, which are directly affected by local  winds, and swell, the waves that were generated by the wind at a different location and time.  This parameter takes account of both.",
                    "units": "s",
                },
                "Period corresponding to maximum individual wave height": {
                    "description": "This parameter is the period of the expected highest individual wave within a 20-minute time  window. It can be used as a guide to the characteristics of extreme or freak waves. Wave period  is the average time it takes for two consecutive wave crests, on the surface of the ocean/sea,  to pass through a fixed point.\nOccasionally waves of different periods reinforce and interact non-linearly giving a wave height  considerably larger than the significant wave height. If the maximum individual wave height is  more than twice the significant wave height, then the wave is considered to be a freak wave. The  significant wave height represents the average height of the highest third of surface ocean/sea  waves, generated by local winds and associated with swell.\nThe ocean/sea surface wave field consists of a combination of waves with different heights,  lengths and directions (known as the two-dimensional wave spectrum). This parameter is derived  statistically from the two-dimensional wave spectrum.\nThe wave spectrum can be decomposed into wind-sea waves, which are directly affected by local  winds, and swell, the waves that were generated by the wind at a different location and time.  This parameter takes account of both.",
                    "units": "s",
                },
                "Potential evaporation": {
                    "description": 'This parameter is a measure of the extent to which near-surface atmospheric conditions are  conducive to the process of evaporation. It is usually considered to be the amount of  evaporation, under existing atmospheric conditions, from a surface of pure water which has the  temperature of the lowest layer of the atmosphere and gives an indication of the maximum  possible evaporation.\nPotential evaporation in the current ECMWF Integrated Forecasting System (IFS) is based on  surface energy balance calculations with the vegetation parameters set to "crops/mixed farming"  and assuming "no stress from soil moisture". In other words, evaporation is computed for  agricultural land as if it is well watered and assuming that the atmosphere is not affected by  this artificial surface condition. The latter may not always be realistic. Although potential  evaporation is meant to provide an estimate of irrigation requirements, the method can give  unrealistic results in arid conditions due to too strong evaporation forced by dry air.\nThis parameter is accumulated over a particular time period which depends on the data extracted.  For the reanalysis, the accumulation period is over the 1 hour ending at the validity date and time.  For the ensemble members, ensemble mean and ensemble spread, the accumulation period is over the  3 hours ending at the validity date and time.',
                    "units": "m",
                },
                "Precipitation type": {
                    "description": "This parameter describes the type of precipitation at the surface, at the specified time.\nA precipitation type is assigned wherever there is a non-zero value of precipitation. \nIn the ECMWF Integrated Forecasting System (IFS) there are only two predicted precipitation variables:  rain and snow. Precipitation type is derived from these two predicted variables in combination  with atmospheric conditions, such as temperature.\nValues of precipitation type defined in the IFS:\n0: No precipitation, 1: Rain, 3: Freezing rain (i.e. supercooled raindrops which freeze on contact with the ground and other surfaces), 5: Snow, 6: Wet snow (i.e. snow particles which are starting to melt); 7: Mixture of rain and snow, 8: Ice pellets.\nThese precipitation types are consistent with WMO Code Table 4.201. Other types in this WMO table are not defined in the IFS.",
                    "units": "Dimensionless",
                },
                "Runoff": {
                    "description": "Some water from rainfall, melting snow, or deep in the soil, stays stored in the soil. Otherwise,  the water drains away, either over the surface (surface runoff), or under the ground (sub-surface  runoff) and the sum of these two is called runoff.\nThis parameter is accumulated over a particular time period which depends on the data extracted.  For the reanalysis, the accumulation period is over the 1 hour ending at the validity date and time.  For the ensemble members, ensemble mean and ensemble spread, the accumulation period is over the  3 hours ending at the validity date and time.\nThe units of runoff are depth in metres of water. This is the depth the water would  have if it were spread evenly over the grid box. Care should be taken when comparing model  parameters with observations, because observations are often local to a particular point rather than  averaged over a grid box. Observations are also often taken in different units, such as mm/day,  rather than the accumulated metres produced here.\nRunoff is a measure of the availability of water in the soil, and can, for example, be used as an  indicator of drought or flood.",
                    "units": "m",
                },
                "Sea surface temperature": {
                    "description": "This parameter (SST) is the temperature of sea water near the surface. In ERA5, this parameter is a foundation SST, which means there are no variations due to the daily cycle of the sun (diurnal variations). SST, in ERA5, is given by two external providers. Before September 2007, SST from the HadISST2 dataset is used and from September 2007 onwards, the OSTIA dataset is used. This parameter has units of kelvin (K). Temperature measured in kelvin can be converted to degrees Celsius (°C) by subtracting 273.15.",
                    "units": "K",
                },
                "Sea-ice cover": {
                    "description": "This parameter is the fraction of a grid box which is covered by sea ice. Sea ice can only occur in a  grid box which includes ocean or inland water according to the land-sea mask and lake cover, at the  resolution being used. This parameter can be known as sea-ice (area) fraction, sea-ice concentration  and more generally as sea-ice cover.\nIn ERA5, sea-ice cover is given by two external providers. Before 1979 the HadISST2 dataset is used. From 1979 to August 2007 the OSI SAF (409a) dataset is used and from September 2007 the OSI SAF oper dataset is used.\nSea ice is frozen sea water which floats on the surface of the ocean. Sea ice does not include ice  which forms on land such as glaciers, icebergs and ice-sheets. It also excludes ice shelves which are  anchored on land, but protrude out over the surface of the ocean. These phenomena are not modelled by  the IFS.\nLong-term monitoring of sea ice is important for understanding climate change. Sea ice also affects  shipping routes through the polar regions.",
                    "units": "Dimensionless",
                },
                "Significant height of combined wind waves and swell": {
                    "description": "This parameter represents the average height of the highest third of surface ocean/sea waves generated  by wind and swell. It represents the vertical distance between the wave crest and the wave trough.\nThe ocean/sea surface wave field consists of a combination of waves with different heights, lengths and  directions (known as the two-dimensional wave spectrum).\nThe wave spectrum can be decomposed into wind-sea waves, which are directly affected by local winds,  and swell, the waves that were generated by the wind at a different location and time. This parameter  takes account of both.\nMore strictly, this parameter is four times the square root of the integral over all directions and all  frequencies of the two-dimensional wave spectrum.\nThis parameter can be used to assess sea state and swell. For example, engineers use significant wave  height to calculate the load on structures in the open ocean, such as oil platforms, or in coastal  applications.",
                    "units": "m",
                },
                "Significant height of total swell": {
                    "description": "This parameter represents the average height of the highest third of surface ocean/sea waves associated  with swell. It represents the vertical distance between the wave crest and the wave trough.\nThe ocean/sea surface wave field consists of a combination of waves with different heights, lengths and  directions (known as the two-dimensional wave spectrum). The wave spectrum can be decomposed into wind-sea waves, which are directly affected by local winds, and swell, the waves that were generated by  the wind at a different location and time. This parameter takes account of total swell only.\nMore strictly, this parameter is four times the square root of the integral over all directions and all  frequencies of the two-dimensional total swell spectrum. The total swell spectrum is obtained by only considering the components of the two-dimensional wave spectrum that are not under the influence of the  local wind.\nThis parameter can be used to assess swell. For example, engineers use significant wave height to  calculate the load on structures in the open ocean, such as oil platforms, or in coastal applications.",
                    "units": "m",
                },
                "Significant height of wind waves": {
                    "description": "This parameter represents the average height of the highest third of surface ocean/sea waves generated  by the local wind. It represents the vertical distance between the wave crest and the wave trough.\nThe ocean/sea surface wave field consists of a combination of waves with different heights, lengths and  directions (known as the two-dimensional wave spectrum). The wave spectrum can be decomposed into wind-sea waves, which are directly affected by local winds, and swell, the waves that were generated by  the wind at a different location and time. This parameter takes account of wind-sea waves only.\nMore strictly, this parameter is four times the square root of the integral over all directions and all  frequencies of the two-dimensional wind-sea wave spectrum. The wind-sea wave spectrum is obtained by only considering the components of the two-dimensional wave spectrum that are still under the influence of the  local wind.\nThis parameter can be used to assess wind-sea waves. For example, engineers use significant wave height  to calculate the load on structures in the open ocean, such as oil platforms, or in coastal applications.",
                    "units": "m",
                },
                "Significant wave height of first swell partition": {
                    "description": "This parameter represents the average height of the highest third of surface ocean/sea waves associated  with the first swell partition. Wave height represents the vertical distance between the wave crest and the wave trough.\nThe ocean/sea surface wave field consists of a combination of waves with different heights, lengths and  directions (known as the two-dimensional wave spectrum). The wave spectrum can be decomposed into wind-sea waves, which are directly affected by local winds, and swell, the waves that were generated by  the wind at a different location and time.\nIn many situations, swell can be made up of different swell systems, for example, from two distant and  separate storms. To account for this, the swell spectrum is partitioned into up to three parts. The swell partitions are labelled first, second and third based on their respective wave height. Therefore, there  is no guarantee of spatial coherence (the first might be from one system at one location and another system at the neighbouring location).\nMore strictly, this parameter is four times the square root of the integral over all directions and all  frequencies of the first swell partition of the two-dimensional swell spectrum. The swell spectrum is obtained by only considering the components of the two-dimensional wave spectrum that are not under the  influence of the local wind.\nThis parameter can be used to assess swell. For example, engineers use significant wave height to  calculate the load on structures in the open ocean, such as oil platforms, or in coastal applications.",
                    "units": "m",
                },
                "Significant wave height of second swell partition": {
                    "description": "This parameter represents the average height of the highest third of surface ocean/sea waves associated  with the second swell partition. Wave height represents the vertical distance between the wave crest and the wave trough.\nThe ocean/sea surface wave field consists of a combination of waves with different heights, lengths and  directions (known as the two-dimensional wave spectrum). The wave spectrum can be decomposed into wind-sea waves, which are directly affected by local winds, and swell, the waves that were generated by  the wind at a different location and time.\nIn many situations, swell can be made up of different swell systems, for example, from two distant and  separate storms. To account for this, the swell spectrum is partitioned into up to three parts. The swell partitions are labelled first, second and third based on their respective wave height. Therefore, there  is no guarantee of spatial coherence (the second might be from one system at one location and another system at the neighbouring location).\nMore strictly, this parameter is four times the square root of the integral over all directions and all  frequencies of the first swell partition of the two-dimensional swell spectrum. The swell spectrum is obtained by only considering the components of the two-dimensional wave spectrum that are not under the  influence of the local wind.\nThis parameter can be used to assess swell. For example, engineers use significant wave height to  calculate the load on structures in the open ocean, such as oil platforms, or in coastal applications.",
                    "units": "m",
                },
                "Significant wave height of third swell partition": {
                    "description": "This parameter represents the average height of the highest third of surface ocean/sea waves associated  with the third swell partition. Wave height represents the vertical distance between the wave crest and the wave trough.\nThe ocean/sea surface wave field consists of a combination of waves with different heights, lengths and  directions (known as the two-dimensional wave spectrum). The wave spectrum can be decomposed into wind-sea waves, which are directly affected by local winds, and swell, the waves that were generated by  the wind at a different location and time.\nIn many situations, swell can be made up of different swell systems, for example, from two distant and  separate storms. To account for this, the swell spectrum is partitioned into up to three parts. The  swell partitions are labelled first, second and third based on their respective wave height. Therefore,  there is no guarantee of spatial coherence (the third might be from one system at one location and  another system at the neighbouring location).\nMore strictly, this parameter is four times the square root of the integral over all directions and all  frequencies of the first swell partition of the two-dimensional swell spectrum. The swell spectrum is obtained by only considering the components of the two-dimensional wave spectrum that are not under the  influence of the local wind.\nThis parameter can be used to assess swell. For example, engineers use significant wave height to  calculate the load on structures in the open ocean, such as oil platforms, or in coastal applications.",
                    "units": "m",
                },
                "Skin reservoir content": {
                    "description": 'This parameter is the amount of water in the vegetation canopy and/or in a thin layer on the soil.\nIt represents the amount of rain intercepted by foliage, and water from dew. The maximum amount of  "skin reservoir content" a grid box can hold depends on the type of vegetation, and may be zero. Water  leaves the "skin reservoir" by evaporation.',
                    "units": "m of water equivalent",
                },
                "Skin temperature": {
                    "description": "This parameter is the temperature of the surface of the Earth.\nThe skin temperature is the theoretical temperature that is required to satisfy the surface energy  balance. It represents the temperature of the uppermost surface layer, which has no heat capacity and  so can respond instantaneously to changes in surface fluxes. Skin temperature is calculated differently  over land and sea.\nThis parameter has units of kelvin (K). Temperature measured in kelvin can be converted to degrees  Celsius (°C) by subtracting 273.15.",
                    "units": "K",
                },
                "Slope of sub-gridscale orography": {
                    "description": "This parameter is one of four parameters (the others being standard deviation, angle and anisotropy)  that describe the features of the orography that are too small to be resolved by the model grid. These  four parameters are calculated for orographic features with horizontal scales comprised between 5 km  and the model grid resolution, being derived from the height of valleys, hills and mountains at about  1 km resolution. They are used as input for the sub-grid orography scheme which represents low-level  blocking and orographic gravity wave effects.\nThis parameter represents the slope of the sub-grid valleys, hills and mountains. A flat surface has  a value of 0, and a 45 degree slope has a value of 0.5.\nThis parameter does not vary in time.",
                    "units": "Dimensionless",
                },
                "Snow albedo": {
                    "description": "This parameter is a measure of the reflectivity of the snow-covered part of the grid box. It is the  fraction of solar (shortwave) radiation reflected by snow across the solar spectrum.\nThe ECMWF Integrated Forecasting System (IFS) represents snow as a single additional layer over the  uppermost soil level. The snow may cover all or part of the grid box.\nThis parameter changes with snow age and also depends on vegetation height. It has a range of values between 0 and 1. For low vegetation, it ranges between 0.52 for old snow and 0.88 for fresh snow.  For high vegetation with snow underneath, it depends on vegetation type and has values between 0.27  and 0.38.\nThis parameter is defined over the whole globe, even where there is no snow. Regions without snow can be masked out by only considering grid points where the snow depth (m of water equivalent) is greater than 0.0.",
                    "units": "Dimensionless",
                },
                "Snow density": {
                    "description": "This parameter is the mass of snow per cubic metre in the snow layer.\nThe ECMWF Integrated Forecasting System (IFS) represents snow as a single additional layer over the  uppermost soil level. The snow may cover all or part of the grid box.\nThis parameter is defined over the whole globe, even where there is no snow. Regions without snow can be masked out by only considering grid points where the snow depth (m of water equivalent) is greater than 0.0.",
                    "units": "kg m^-3",
                },
                "Snow depth": {
                    "description": "This parameter is the amount of snow from the snow-covered area of a grid box.\nIts units are metres of water equivalent, so it is the depth the water would have if the snow melted  and was spread evenly over the whole grid box. The ECMWF Integrated Forecasting System (IFS)  represents snow as a single additional layer over the uppermost soil level. The snow may cover all  or part of the grid box.",
                    "units": "m of water equivalent",
                },
                "Snow evaporation": {
                    "description": "This parameter is the accumulated amount of water that has evaporated from snow from the snow-covered  area of a grid box into vapour in the air above.\nThe ECMWF Integrated Forecasting System (IFS) represents snow as a single additional layer over the  uppermost soil level. The snow may cover all or part of the grid box. This parameter is the depth of  water there would be if the evaporated snow (from the snow-covered area of a grid box) were liquid  and were spread evenly over the whole grid box.\nThis parameter is accumulated over a particular time period which depends on the data extracted.  For the reanalysis, the accumulation period is over the 1 hour ending at the validity date and time.  For the ensemble members, ensemble mean and ensemble spread, the accumulation period is over the  3 hours ending at the validity date and time.\nThe IFS convention is that downward fluxes are positive. Therefore, negative values indicate  evaporation and positive values indicate deposition.",
                    "units": "m of water equivalent",
                },
                "Snowfall": {
                    "description": "This parameter is the accumulated snow that falls to the Earth's surface. It is the sum of large-scale  snowfall and convective snowfall. Large-scale snowfall is generated by the cloud scheme in the ECMWF Integrated Forecasting System (IFS). The cloud scheme represents the formation and dissipation of  clouds and large-scale precipitation due to changes in atmospheric quantities (such as pressure,  temperature and moisture) predicted directly at spatial scales of the grid box or larger. Convective  snowfall is generated by the convection scheme in the IFS, which represents convection at spatial  scales smaller than the grid box. In the IFS, precipitation is comprised of rain and snow.\nThis parameter is accumulated over a particular time period which depends on the data extracted.  For the reanalysis, the accumulation period is over the 1 hour ending at the validity date and time.  For the ensemble members, ensemble mean and ensemble spread, the accumulation period is over the  3 hours ending at the validity date and time.\nThe units of this parameter are depth in metres of water equivalent. It is the depth  the water would have if it were spread evenly over the grid box.\nCare should be taken when comparing model parameters with observations, because observations are often  local to a particular point in space and time, rather than representing averages over a model grid box.",
                    "units": "m of water equivalent",
                },
                "Snowmelt": {
                    "description": "This parameter is the accumulated amount of water that has melted from snow in the snow-covered area of  a grid box.\nThe ECMWF Integrated Forecasting System (IFS) represents snow as a single additional layer over the  uppermost soil level. The snow may cover all or part of the grid box. This parameter is the depth of  water there would be if the melted snow (from the snow-covered area of a grid box) were spread evenly  over the whole grid box. For example, if half the grid box were covered in snow with a water equivalent  depth of 0.02m, this parameter would have a value of 0.01m.\nThis parameter is accumulated over a particular time period which depends on the data extracted.  For the reanalysis, the accumulation period is over the 1 hour ending at the validity date and time.  For the ensemble members, ensemble mean and ensemble spread, the accumulation period is over the  3 hours ending at the validity date and time.",
                    "units": "m of water equivalent",
                },
                "Soil temperature level 1": {
                    "description": "This parameter is the temperature of the soil at level 1 (in the middle of layer 1).\nThe ECMWF Integrated Forecasting System (IFS) has a four-layer representation of soil, where the surface  is at 0cm:\nLayer 1: 0 - 7cm, Layer 2: 7 - 28cm, Layer 3: 28 - 100cm, Layer 4: 100 - 289cm.\nSoil temperature is set at the middle of each layer, and heat transfer is calculated at the interfaces  between them. It is assumed that there is no heat transfer out of the bottom of the lowest layer.\nSoil temperature is defined over the whole globe, even over ocean. Regions with a water surface can be masked out by only considering grid points where the land-sea mask has a value greater than 0.5.\nThis parameter has units of kelvin (K). Temperature measured in kelvin can be converted to degrees  Celsius (°C) by subtracting 273.15.",
                    "units": "K",
                },
                "Soil temperature level 2": {
                    "description": "This parameter is the temperature of the soil at level 2 (in the middle of layer 2).\nThe ECMWF Integrated Forecasting System (IFS) has a four-layer representation of soil, where the surface  is at 0cm:\nLayer 1: 0 - 7cm, Layer 2: 7 - 28cm, Layer 3: 28 - 100cm, Layer 4: 100 - 289cm.\nSoil temperature is set at the middle of each layer, and heat transfer is calculated at the interfaces  between them. It is assumed that there is no heat transfer out of the bottom of the lowest layer.\nSoil temperature is defined over the whole globe, even over ocean. Regions with a water surface can be masked out by only considering grid points where the land-sea mask has a value greater than 0.5.\nThis parameter has units of kelvin (K). Temperature measured in kelvin can be converted to degrees  Celsius (°C) by subtracting 273.15.",
                    "units": "K",
                },
                "Soil temperature level 3": {
                    "description": "This parameter is the temperature of the soil at level 3 (in the middle of layer 3).\nThe ECMWF Integrated Forecasting System (IFS) has a four-layer representation of soil, where the surface  is at 0cm:\nLayer 1: 0 - 7cm, Layer 2: 7 - 28cm, Layer 3: 28 - 100cm, Layer 4: 100 - 289cm.\nSoil temperature is set at the middle of each layer, and heat transfer is calculated at the interfaces  between them. It is assumed that there is no heat transfer out of the bottom of the lowest layer.\nSoil temperature is defined over the whole globe, even over ocean. Regions with a water surface can be masked out by only considering grid points where the land-sea mask has a value greater than 0.5.\nThis parameter has units of kelvin (K). Temperature measured in kelvin can be converted to degrees  Celsius (°C) by subtracting 273.15.",
                    "units": "K",
                },
                "Soil temperature level 4": {
                    "description": "This parameter is the temperature of the soil at level 4 (in the middle of layer 4).\nThe ECMWF Integrated Forecasting System (IFS) has a four-layer representation of soil, where the surface  is at 0cm:\nLayer 1: 0 - 7cm, Layer 2: 7 - 28cm, Layer 3: 28 - 100cm, Layer 4: 100 - 289cm.\nSoil temperature is set at the middle of each layer, and heat transfer is calculated at the interfaces  between them. It is assumed that there is no heat transfer out of the bottom of the lowest layer.\nSoil temperature is defined over the whole globe, even over ocean. Regions with a water surface can be masked out by only considering grid points where the land-sea mask has a value greater than 0.5.\nThis parameter has units of kelvin (K). Temperature measured in kelvin can be converted to degrees  Celsius (°C) by subtracting 273.15.",
                    "units": "K",
                },
                "Soil type": {
                    "description": "This parameter is the texture (or classification) of soil used by the land surface scheme of the  ECMWF Integrated Forecasting System (IFS) to predict the water holding capacity of soil in soil  moisture and runoff calculations. It is derived from the root zone data (30-100 cm below the surface)  of the FAO/UNESCO Digital Soil Map of the World, DSMW (FAO, 2003), which exists at a resolution of  5' X 5' (about 10 km).\nThe seven soil types are: 1: Coarse, 2: Medium, 3: Medium fine, 4: Fine, 5: Very fine, 6: Organic, 7: Tropical organic. A value of 0 indicates a non-land point.\nThis parameter does not vary in time.",
                    "units": "Dimensionless",
                },
                "Standard deviation of filtered subgrid orography": {
                    "description": "Climatological parameter (scales between approximately 3 and 22 km are included).\nThis parameter does not vary in time.",
                    "units": "m",
                },
                "Standard deviation of orography": {
                    "description": "This parameter is one of four parameters (the others being angle of sub-gridscale orography, slope  and anisotropy) that describe the features of the orography that are too small to be resolved by the  model grid. These four parameters are calculated for orographic features with horizontal scales  comprised between 5 km and the model grid resolution, being derived from the height of valleys,  hills and mountains at about 1 km resolution. They are used as input for the sub-grid orography  scheme which represents low-level blocking and orographic gravity wave effects.\nThis parameter represents the standard deviation of the height of the sub-grid valleys, hills and  mountains within a grid box.\nThis parameter does not vary in time.",
                    "units": "Dimensionless",
                },
                "Sub-surface runoff": {
                    "description": "Some water from rainfall, melting snow, or deep in the soil, stays stored in the soil. Otherwise,  the water drains away, either over the surface (surface runoff), or under the ground (sub-surface  runoff) and the sum of these two is called runoff.\nThis parameter is accumulated over a particular time period which depends on the data extracted.  For the reanalysis, the accumulation period is over the 1 hour ending at the validity date and time.  For the ensemble members, ensemble mean and ensemble spread, the accumulation period is over the  3 hours ending at the validity date and time.\nThe units of runoff are depth in metres of water. This is the depth the water would  have if it were spread evenly over the grid box. Care should be taken when comparing model parameters  with observations, because observations are often local to a particular point rather than averaged  over a grid box. Observations are also often taken in different units, such as mm/day, rather than  the accumulated metres produced here.\nRunoff is a measure of the availability of water in the soil, and can, for example, be used as an  indicator of drought or flood.",
                    "units": "m",
                },
                "Surface latent heat flux": {
                    "description": "This parameter is the transfer of latent heat (resulting from water phase changes, such as  evaporation or condensation) between the Earth's surface and the atmosphere through the effects of  turbulent air motion. Evaporation from the Earth's surface represents a transfer of energy from  the surface to the atmosphere.\nThis parameter is accumulated over a particular time period which depends on the data extracted.  For the reanalysis, the accumulation period is over the 1 hour ending at the validity date and time.  For the ensemble members, ensemble mean and ensemble spread, the accumulation period is over the  3 hours ending at the validity date and time.\nThe units are joules per square metre (J m^-2 ). To convert to watts per square metre (W m^-2 ), the  accumulated values should be divided by the accumulation period expressed in seconds.\nThe ECMWF convention for vertical fluxes is positive downwards.",
                    "units": "J m^-2",
                },
                "Surface net solar radiation": {
                    "description": "This parameter is the amount of solar radiation (also known as shortwave radiation) that reaches a  horizontal plane at the surface of the Earth (both direct and diffuse) minus the amount reflected by the Earth's surface (which is governed by the albedo).\nRadiation from the Sun (solar, or shortwave, radiation) is partly reflected back to space by clouds and  particles in the atmosphere (aerosols) and some of it is absorbed. The remainder is incident on the  Earth's surface, where some of it is reflected.\nThis parameter is accumulated over a particular time period which depends on the data extracted.  For the reanalysis, the accumulation period is over the 1 hour ending at the validity date and time.  For the ensemble members, ensemble mean and ensemble spread, the accumulation period is over the  3 hours ending at the validity date and time.\nThe units are joules per square metre (J m^-2 ). To convert to watts per square metre (W m^-2 ), the  accumulated values should be divided by the accumulation period expressed in seconds. \nThe ECMWF convention for vertical fluxes is positive downwards.",
                    "units": "J m^-2",
                },
                "Surface net solar radiation, clear sky": {
                    "description": "This parameter is the amount of solar (shortwave) radiation reaching the surface of the Earth (both direct  and diffuse) minus the amount reflected by the Earth's surface (which is governed by the albedo), assuming  clear-sky (cloudless) conditions. It is the amount of radiation passing through a horizontal plane.\nClear-sky radiation quantities are computed for exactly the same atmospheric conditions of temperature,  humidity, ozone, trace gases and aerosol as the corresponding total-sky quantities (clouds included), but assuming that the clouds are not there.\nRadiation from the Sun (solar, or shortwave, radiation) is partly reflected back to space by clouds and  particles in the atmosphere (aerosols) and some of it is absorbed. The rest is incident on the Earth's surface, where some of it is reflected. The difference between downward and reflected solar radiation is  the surface net solar radiation.\nThis parameter is accumulated over a particular time period which depends on the data extracted.  For the reanalysis, the accumulation period is over the 1 hour ending at the validity date and time.  For the ensemble members, ensemble mean and ensemble spread, the accumulation period is over the  3 hours ending at the validity date and time.\nThe units are joules per square metre (J m^-2 ). To convert to watts per square metre (W m^-2 ), the  accumulated values should be divided by the accumulation period expressed in seconds.\nThe ECMWF convention for vertical fluxes is positive downwards.",
                    "units": "J m^-2",
                },
                "Surface net thermal radiation": {
                    "description": "Thermal radiation (also known as longwave or terrestrial radiation) refers to radiation emitted by the  atmosphere, clouds and the surface of the Earth. This parameter is the difference between downward and upward thermal radiation at the surface of the Earth. It is the amount of radiation passing through a  horizontal plane.\nThe atmosphere and clouds emit thermal radiation in all directions, some of which reaches the surface as  downward thermal radiation. The upward thermal radiation at the surface consists of thermal radiation emitted by the surface plus the fraction of downwards thermal radiation reflected upward by the surface.\nThis parameter is accumulated over a particular time period which depends on the data extracted.  For the reanalysis, the accumulation period is over the 1 hour ending at the validity date and time.  For the ensemble members, ensemble mean and ensemble spread, the accumulation period is over the  3 hours ending at the validity date and time.\nThe units are joules per square metre (J m^-2 ). To convert to watts per square metre (W m^-2 ), the  accumulated values should be divided by the accumulation period expressed in seconds.\nThe ECMWF convention for vertical fluxes is positive downwards.",
                    "units": "J m^-2",
                },
                "Surface net thermal radiation, clear sky": {
                    "description": "Thermal radiation (also known as longwave or terrestrial radiation) refers to radiation emitted by the  atmosphere, clouds and the surface of the Earth. This parameter is the difference between downward and upward thermal radiation at the surface of the Earth, assuming clear-sky (cloudless) conditions. It is  the amount of radiation passing through a horizontal plane.\nClear-sky radiation quantities are computed for exactly the same atmospheric conditions of temperature,  humidity, ozone, trace gases and aerosol as the corresponding total-sky quantities (clouds included),  but assuming that the clouds are not there.\nThe atmosphere and clouds emit thermal radiation in all directions, some of which reaches the surface  as downward thermal radiation. The upward thermal radiation at the surface consists of thermal radiation emitted by the surface plus the fraction of downwards thermal radiation reflected upward by the surface.\nThis parameter is accumulated over a particular time period which depends on the data extracted.  For the reanalysis, the accumulation period is over the 1 hour ending at the validity date and time.  For the ensemble members, ensemble mean and ensemble spread, the accumulation period is over the  3 hours ending at the validity date and time.\nThe units are joules per square metre (J m^-2 ). To convert to watts per square metre (W m^-2 ), the  accumulated values should be divided by the accumulation period expressed in seconds.\nThe ECMWF convention for vertical fluxes is positive downwards.",
                    "units": "J m^-2",
                },
                "Surface pressure": {
                    "description": "This parameter is the pressure (force per unit area) of the atmosphere at the surface of land, sea and  inland water.\nIt is a measure of the weight of all the air in a column vertically above a point on the Earth's surface. \nSurface pressure is often used in combination with temperature to calculate air density.\nThe strong variation of pressure with altitude makes it difficult to see the low and high pressure weather  systems over mountainous areas, so mean sea level pressure, rather than surface pressure, is normally used  for this purpose.\nThe units of this parameter are Pascals (Pa). Surface pressure is often measured in hPa and sometimes is  presented in the old units of millibars, mb (1 hPa = 1 mb= 100 Pa).",
                    "units": "Pa",
                },
                "Surface runoff": {
                    "description": "Some water from rainfall, melting snow, or deep in the soil, stays stored in the soil. Otherwise, the  water drains away, either over the surface (surface runoff), or under the ground (sub-surface runoff) and the sum of these two is called runoff.\nThis parameter is accumulated over a particular time period which depends on the data extracted.  For the reanalysis, the accumulation period is over the 1 hour ending at the validity date and time.  For the ensemble members, ensemble mean and ensemble spread, the accumulation period is over the  3 hours ending at the validity date and time.\nThe units of runoff are depth in metres of water. This is the depth the water would have if it were  spread evenly over the grid box. Care should be taken when comparing model parameters with observations,  because observations are often local to a particular point rather than averaged over a grid box.  Observations are also often taken in different units, such as mm/day, rather than the accumulated metres  produced here.\nRunoff is a measure of the availability of water in the soil, and can, for example, be used as an  indicator of drought or flood.",
                    "units": "m",
                },
                "Surface sensible heat flux": {
                    "description": "This parameter is the transfer of heat between the Earth's surface and the atmosphere through the effects  of turbulent air motion (but excluding any heat transfer resulting from condensation or evaporation).\nThe magnitude of the sensible heat flux is governed by the difference in temperature between the surface  and the overlying atmosphere, wind speed and the surface roughness. For example, cold air overlying a warm surface would produce a sensible heat flux from the land (or ocean) into the atmosphere.\nThis parameter is accumulated over a particular time period which depends on the data extracted.  For the reanalysis, the accumulation period is over the 1 hour ending at the validity date and time.  For the ensemble members, ensemble mean and ensemble spread, the accumulation period is over the  3 hours ending at the validity date and time.\nThe units are joules per square metre (J m^-2 ). To convert to watts per square metre (W m^-2 ), the  accumulated values should be divided by the accumulation period expressed in seconds. \nThe ECMWF convention for vertical fluxes is positive downwards.",
                    "units": "J m^-2",
                },
                "Surface solar radiation downward, clear sky": {
                    "description": "This parameter is the amount of solar radiation (also known as shortwave radiation) that reaches a horizontal  plane at the surface of the Earth, assuming clear-sky (cloudless) conditions. This parameter comprises both direct and diffuse solar radiation.\nRadiation from the Sun (solar, or shortwave, radiation) is partly reflected back to space by clouds and  particles in the atmosphere (aerosols) and some of it is absorbed. The rest is incident on the Earth's surface.\nClear-sky radiation quantities are computed for exactly the same atmospheric conditions of temperature,  humidity, ozone, trace gases and aerosol as the corresponding total-sky quantities (clouds included),  but assuming that the clouds are not there.\nThis parameter is accumulated over a particular time period which depends on the data extracted.  For the reanalysis, the accumulation period is over the 1 hour ending at the validity date and time.  For the ensemble members, ensemble mean and ensemble spread, the accumulation period is over the  3 hours ending at the validity date and time.\nThe units are joules per square metre (J m^-2 ). To convert to watts per square metre (W m^-2 ), the  accumulated values should be divided by the accumulation period expressed in seconds. \nThe ECMWF convention for vertical fluxes is positive downwards.",
                    "units": "J m^-2",
                },
                "Surface solar radiation downwards": {
                    "description": "This parameter is the amount of solar radiation (also known as shortwave radiation) that reaches a horizontal  plane at the surface of the Earth. This parameter comprises both direct and diffuse solar radiation.\nRadiation from the Sun (solar, or shortwave, radiation) is partly reflected back to space by clouds and  particles in the atmosphere (aerosols) and some of it is absorbed. The rest is incident on the Earth's surface  (represented by this parameter).\nTo a reasonably good approximation, this parameter is the model equivalent of what would be measured by a  pyranometer (an instrument used for measuring solar radiation) at the surface. However, care should be taken  when comparing model parameters with observations, because observations are often local to a particular point  in space and time, rather than representing averages over a model grid box.\nThis parameter is accumulated over a particular time period which depends on the data extracted.  For the reanalysis, the accumulation period is over the 1 hour ending at the validity date and time.  For the ensemble members, ensemble mean and ensemble spread, the accumulation period is over the  3 hours ending at the validity date and time.\nThe units are joules per square metre (J m^-2 ). To convert to watts per square metre (W m^-2 ), the  accumulated values should be divided by the accumulation period expressed in seconds. \nThe ECMWF convention for vertical fluxes is positive downwards.",
                    "units": "J m^-2",
                },
                "Surface thermal radiation downward, clear sky": {
                    "description": "This parameter is the amount of thermal (also known as longwave or terrestrial) radiation emitted by the  atmosphere that reaches a horizontal plane at the surface of the Earth, assuming clear-sky (cloudless) conditions.\nThe surface of the Earth emits thermal radiation, some of which is absorbed by the atmosphere and clouds. The  atmosphere and clouds likewise emit thermal radiation in all directions, some of which reaches the surface.\nClear-sky radiation quantities are computed for exactly the same atmospheric conditions of temperature,  humidity, ozone, trace gases and aerosol as the corresponding total-sky quantities (clouds included),  but assuming that the clouds are not there.\nThis parameter is accumulated over a particular time period which depends on the data extracted.  For the reanalysis, the accumulation period is over the 1 hour ending at the validity date and time.  For the ensemble members, ensemble mean and ensemble spread, the accumulation period is over the  3 hours ending at the validity date and time.\nThe units are joules per square metre (J m^-2 ). To convert to watts per square metre (W m^-2 ), the  accumulated values should be divided by the accumulation period expressed in seconds. \nThe ECMWF convention for vertical fluxes is positive downwards.",
                    "units": "J m^-2",
                },
                "Surface thermal radiation downwards": {
                    "description": "This parameter is the amount of thermal (also known as longwave or terrestrial) radiation emitted by the  atmosphere and clouds that reaches a horizontal plane at the surface of the Earth.\nThe surface of the Earth emits thermal radiation, some of which is absorbed by the atmosphere and clouds. The  atmosphere and clouds likewise emit thermal radiation in all directions, some of which reaches the surface (represented by this parameter).\nThis parameter is accumulated over a particular time period which depends on the data extracted.  For the reanalysis, the accumulation period is over the 1 hour ending at the validity date and time.  For the ensemble members, ensemble mean and ensemble spread, the accumulation period is over the  3 hours ending at the validity date and time.\nThe units are joules per square metre (J m^-2 ). To convert to watts per square metre (W m^-2 ), the  accumulated values should be divided by the accumulation period expressed in seconds. \nThe ECMWF convention for vertical fluxes is positive downwards.",
                    "units": "J m^-2",
                },
                "TOA incident solar radiation": {
                    "description": "This parameter is the incoming solar radiation (also known as shortwave radiation), received from the Sun,  at the top of the atmosphere. It is the amount of radiation passing through a horizontal plane. \nThis parameter is accumulated over a particular time period which depends on the data extracted.  For the reanalysis, the accumulation period is over the 1 hour ending at the validity date and time.  For the ensemble members, ensemble mean and ensemble spread, the accumulation period is over the  3 hours ending at the validity date and time.\nThe units are joules per square metre (J m^-2 ). To convert to watts per square metre (W m^-2 ), the  accumulated values should be divided by the accumulation period expressed in seconds.\nThe ECMWF convention for vertical fluxes is positive downwards.",
                    "units": "J m^-2",
                },
                "Temperature of snow layer": {
                    "description": "This parameter gives the temperature of the snow layer from the ground to the snow-air interface.\nThe ECMWF Integrated Forecasting System (IFS) represents snow as a single additional layer over the uppermost  soil level. The snow may cover all or part of the grid box.\nThis parameter is defined over the whole globe, even where there is no snow. Regions without snow can be masked out by only considering grid points where the snow depth (m of water equivalent) is greater than 0.0.\nThis parameter has units of kelvin (K). Temperature measured in kelvin can be converted to degrees Celsius (°C)  by subtracting 273.15.",
                    "units": "K",
                },
                "Top net solar radiation": {
                    "description": "This parameter is the incoming solar radiation (also known as shortwave radiation) minus the outgoing solar  radiation at the top of the atmosphere. It is the amount of radiation passing through a horizontal plane. The  incoming solar radiation is the amount received from the Sun. The outgoing solar radiation is the amount  reflected and scattered by the Earth's atmosphere and surface.\nThis parameter is accumulated over a particular time period which depends on the data extracted.  For the reanalysis, the accumulation period is over the 1 hour ending at the validity date and time.  For the ensemble members, ensemble mean and ensemble spread, the accumulation period is over the  3 hours ending at the validity date and time.\nThe units are joules per square metre (J m^-2 ). To convert to watts per square metre (W m^-2 ), the  accumulated values should be divided by the accumulation period expressed in seconds.\nThe ECMWF convention for vertical fluxes is positive downwards.",
                    "units": "J m^-2",
                },
                "Top net solar radiation, clear sky": {
                    "description": "This parameter is the incoming solar radiation (also known as shortwave radiation) minus the outgoing solar  radiation at the top of the atmosphere, assuming clear-sky (cloudless) conditions. It is the amount of  radiation passing through a horizontal plane. The incoming solar radiation is the amount received from the Sun.  The outgoing solar radiation is the amount reflected and scattered by the Earth's atmosphere and surface,  assuming clear-sky (cloudless) conditions.\nClear-sky radiation quantities are computed for exactly the same atmospheric conditions of temperature, humidity,  ozone, trace gases and aerosol as the total-sky (clouds included) quantities, but assuming that the clouds are  not there.\nThis parameter is accumulated over a particular time period which depends on the data extracted.  For the reanalysis, the accumulation period is over the 1 hour ending at the validity date and time.  For the ensemble members, ensemble mean and ensemble spread, the accumulation period is over the  3 hours ending at the validity date and time.\nThe units are joules per square metre (J m^-2 ). To convert to watts per square metre (W m^-2 ), the  accumulated values should be divided by the accumulation period expressed in seconds.\nThe ECMWF convention for vertical fluxes is positive downwards.",
                    "units": "J m^-2",
                },
                "Top net thermal radiation": {
                    "description": "The thermal (also known as terrestrial or longwave) radiation emitted to space at the top of the atmosphere is  commonly known as the Outgoing Longwave Radiation (OLR). The top net thermal radiation (this parameter) is equal  to the negative of OLR.\nThis parameter is accumulated over a particular time period which depends on the data extracted.  For the reanalysis, the accumulation period is over the 1 hour ending at the validity date and time.  For the ensemble members, ensemble mean and ensemble spread, the accumulation period is over the  3 hours ending at the validity date and time.\nThe units are joules per square metre (J m^-2 ). To convert to watts per square metre (W m^-2 ), the  accumulated values should be divided by the accumulation period expressed in seconds.\nThe ECMWF convention for vertical fluxes is positive downwards.",
                    "units": "J m^-2",
                },
                "Top net thermal radiation, clear sky": {
                    "description": "This parameter is the thermal (also known as terrestrial or longwave) radiation emitted to space at the top of the  atmosphere, assuming clear-sky (cloudless) conditions. It is the amount passing through a horizontal plane. Note  that the ECMWF convention for vertical fluxes is positive downwards, so a flux from the atmosphere to space will  be negative.\nClear-sky radiation quantities are computed for exactly the same atmospheric conditions of temperature, humidity,  ozone, trace gases and aerosol as total-sky quantities (clouds included), but assuming that the clouds are not  there.\nThe thermal radiation emitted to space at the top of the atmosphere is commonly known as the Outgoing Longwave  Radiation (OLR) (i.e., taking a flux from the atmosphere to space as positive). Note that OLR is typically shown  in units of watts per square metre (W m^-2 ).\nThis parameter is accumulated over a particular time period which depends on the data extracted.  For the reanalysis, the accumulation period is over the 1 hour ending at the validity date and time.  For the ensemble members, ensemble mean and ensemble spread, the accumulation period is over the  3 hours ending at the validity date and time.\nThe units are joules per square metre (J m^-2 ). To convert to watts per square metre (W m^-2 ), the  accumulated values should be divided by the accumulation period expressed in seconds.",
                    "units": "J m^-2",
                },
                "Total cloud cover": {
                    "description": "This parameter is the proportion of a grid box covered by cloud. Total cloud cover is a single level field  calculated from the cloud occurring at different model levels through the atmosphere. Assumptions are made about  the degree of overlap/randomness between clouds at different heights.\nCloud fractions vary from 0 to 1.",
                    "units": "Dimensionless",
                },
                "Total column cloud ice water": {
                    "description": "This parameter is the amount of ice contained within clouds in a column extending from the surface of the Earth  to the top of the atmosphere. Snow (aggregated ice crystals) is not included in this parameter.\nThis parameter represents the area averaged value for a model grid box.\nClouds contain a continuum of different sized water droplets and ice particles. The ECMWF Integrated Forecasting  System (IFS) cloud scheme simplifies this to represent a number of discrete cloud droplets/particles including:  cloud water droplets, raindrops, ice crystals and snow (aggregated ice crystals). The processes of droplet  formation, phase transition and aggregation are also highly simplified in the IFS.",
                    "units": "kg m^-2",
                },
                "Total column cloud liquid water": {
                    "description": "This parameter is the amount of liquid water contained within cloud droplets in a column extending from the  surface of the Earth to the top of the atmosphere. Rain water droplets, which are much larger in size (and mass),  are not included in this parameter.\nThis parameter represents the area averaged value for a model grid box.\nClouds contain a continuum of different sized water droplets and ice particles. The ECMWF Integrated Forecasting  System (IFS) cloud scheme simplifies this to represent a number of discrete cloud droplets/particles including:  cloud water droplets, raindrops, ice crystals and snow (aggregated ice crystals). The processes of droplet  formation, phase transition and aggregation are also highly simplified in the IFS.",
                    "units": "kg m^-2",
                },
                "Total column ozone": {
                    "description": "This parameter is the total amount of ozone in a column of air extending from the surface of the Earth to the top  of the atmosphere. This parameter can also be referred to as total ozone, or vertically integrated ozone. The  values are dominated by ozone within the stratosphere.\nIn the ECMWF Integrated Forecasting System (IFS), there is a simplified representation of ozone chemistry  (including representation of the chemistry which has caused the ozone hole). Ozone is also transported around in  the atmosphere through the motion of air.\nNaturally occurring ozone in the stratosphere helps protect organisms at the surface of the Earth from the harmful  effects of ultraviolet (UV) radiation from the Sun. Ozone near the surface, often produced because of pollution,  is harmful to organisms.\nIn the IFS, the units for total ozone are kilograms per square metre, but before 12/06/2001 dobson units were used.  Dobson units (DU) are still used extensively for total column ozone. 1 DU = 2.1415E-5 kg m^-2",
                    "units": "kg m^-2",
                },
                "Total column rain water": {
                    "description": "This parameter is the total amount of water in droplets of raindrop size (which can fall to the surface as  precipitation) in a column extending from the surface of the Earth to the top of the atmosphere.\nThis parameter represents the area averaged value for a grid box.\nClouds contain a continuum of different sized water droplets and ice particles. The ECMWF Integrated Forecasting  System (IFS) cloud scheme simplifies this to represent a number of discrete cloud droplets/particles including:  cloud water droplets, raindrops, ice crystals and snow (aggregated ice crystals). The processes of droplet  formation, conversion and aggregation are also highly simplified in the IFS.",
                    "units": "kg m^-2",
                },
                "Total column snow water": {
                    "description": "This parameter is the total amount of water in the form of snow (aggregated ice crystals which can fall to the  surface as precipitation) in a column extending from the surface of the Earth to the top of the atmosphere.\nThis parameter represents the area averaged value for a grid box.\nClouds contain a continuum of different sized water droplets and ice particles. The ECMWF Integrated Forecasting  System (IFS) cloud scheme simplifies this to represent a number of discrete cloud droplets/particles including:  cloud water droplets, raindrops, ice crystals and snow (aggregated ice crystals). The processes of droplet  formation, conversion and aggregation are also highly simplified in the IFS.",
                    "units": "kg m^-2",
                },
                "Total column supercooled liquid water": {
                    "description": "This parameter is the total amount of supercooled water in a column extending from the surface of the Earth to  the top of the atmosphere. Supercooled water is water that exists in liquid form below 0oC. It is common in  cold clouds and is important in the formation of precipitation. Also, supercooled water in clouds extending to  the surface (i.e., fog) can cause icing/riming of various structures.\nThis parameter represents the area averaged value for a grid box.\nClouds contain a continuum of different sized water droplets and ice particles. The ECMWF Integrated Forecasting  System (IFS) cloud scheme simplifies this to represent a number of discrete cloud droplets/particles including:  cloud water droplets, raindrops, ice crystals and snow (aggregated ice crystals). The processes of droplet  formation, conversion and aggregation are also highly simplified in the IFS.",
                    "units": "kg m^-2",
                },
                "Total column water": {
                    "description": "This parameter is the sum of water vapour, liquid water, cloud ice, rain and snow in a column extending from the  surface of the Earth to the top of the atmosphere. In old versions of the ECMWF model (IFS), rain and snow were  not accounted for.",
                    "units": "kg m^-2",
                },
                "Total column water vapour": {
                    "description": "This parameter is the total amount of water vapour in a column extending from the surface of the Earth to the  top of the atmosphere.\nThis parameter represents the area averaged value for a grid box.",
                    "units": "kg m^-2",
                },
                "Total precipitation": {
                    "description": "This parameter is the accumulated liquid and frozen water, comprising rain and snow, that falls to  the Earth's surface. It is the sum of large-scale precipitation and convective precipitation.  Large-scale precipitation is generated by the cloud scheme in the ECMWF Integrated Forecasting  System (IFS). The cloud scheme represents the formation and dissipation of clouds and large-scale  precipitation due to changes in atmospheric quantities (such as pressure, temperature and moisture)  predicted directly by the IFS at spatial scales of the grid box or larger. Convective precipitation  is generated by the convection scheme in the IFS, which represents convection at spatial scales  smaller than the grid box. This parameter does not include fog, dew or the precipitation that  evaporates in the atmosphere before it lands at the surface of the Earth.\nThis parameter is accumulated over a particular time period which depends on the data extracted.  For the reanalysis, the accumulation period is over the 1 hour ending at the validity date and time.  For the ensemble members, ensemble mean and ensemble spread, the accumulation period is over the  3 hours ending at the validity date and time.\nThe units of this parameter are depth in metres of water equivalent. It is the depth  the water would have if it were spread evenly over the grid box.\nCare should be taken when comparing model parameters with observations, because observations are  often local to a particular point in space and time, rather than representing averages over a model  grid box.",
                    "units": "m",
                },
                "Total sky direct solar radiation at surface": {
                    "description": "This parameter is the amount of direct solar radiation (also known as shortwave radiation) reaching  the surface of the Earth. It is the amount of radiation passing through a horizontal plane.\nSolar radiation at the surface can be direct or diffuse. Solar radiation can be scattered in all  directions by particles in the atmosphere, some of which reaches the surface (diffuse solar  radiation). Some solar radiation reaches the surface without being scattered (direct solar radiation).\nThis parameter is accumulated over a particular time period which depends on the data extracted.  For the reanalysis, the accumulation period is over the 1 hour ending at the validity date and time.  For the ensemble members, ensemble mean and ensemble spread, the accumulation period is over the  3 hours ending at the validity date and time.\nThe units are joules per square metre (J m^-2 ). To convert to watts per square metre (W m^-2 ), the  accumulated values should be divided by the accumulation period expressed in seconds.\nThe ECMWF convention for vertical fluxes is positive downwards.",
                    "units": "J m^-2",
                },
                "Total totals index": {
                    "description": "This parameter gives an indication of the probability of occurrence of a thunderstorm and its severity  by using the vertical gradient of temperature and humidity.\nThe values of this index indicate the following: <44\tThunderstorms not likely, 44-50\tThunderstorms likely, 51-52\tIsolated severe thunderstorms, 53-56\tWidely scattered severe thunderstorms, 56-60\tScattered severe thunderstorms more likely.\nThe total totals index is the temperature difference between 850 hPa (near surface) and 500 hPa  (mid-troposphere) (lapse rate) plus a measure of the moisture content between 850 hPa and 500 hPa.  The probability of deep convection tends to increase with increasing lapse rate and atmospheric  moisture content.\nThere are a number of limitations to this index. Also, the interpretation of the index value varies  with season and location.",
                    "units": "K",
                },
                "Trapping layer base height": {
                    "description": "Trapping layer base height as diagnosed from the vertical gradient of atmospheric refractivity.",
                    "units": "m",
                },
                "Trapping layer top height": {
                    "description": "Trapping layer top height as diagnosed from the vertical gradient of atmospheric refractivity.",
                    "units": "m",
                },
                "Type of high vegetation": {
                    "description": "This parameter indicates the 6 types of high vegetation recognised by the ECMWF Integrated  Forecasting System:\n3 = Evergreen needleleaf trees, 4 = Deciduous needleleaf trees, 5 = Deciduous broadleaf trees, 6 = Evergreen broadleaf trees, 18 = Mixed forest/woodland, 19 = Interrupted forest. A value of 0 indicates a point without high vegetation, including an oceanic or inland water location.\nVegetation types are used to calculate the surface energy balance and snow albedo.\nThis parameter does not vary in time.",
                    "units": "Dimensionless",
                },
                "Type of low vegetation": {
                    "description": "This parameter indicates the 10 types of low vegetation recognised by the ECMWF Integrated  Forecasting System:\n1 = Crops, Mixed farming, 2 = Grass, 7 = Tall grass, 9 = Tundra, 10 = Irrigated crops, 11 = Semidesert, 13 = Bogs and marshes, 16 = Evergreen shrubs, 17 = Deciduous shrubs, 20 = Water and land mixtures. A value of 0 indicates a point without low vegetation, including an oceanic or inland water location.\nVegetation types are used to calculate the surface energy balance and snow albedo.\nThis parameter does not vary in time.",
                    "units": "Dimensionless",
                },
                "U-component stokes drift": {
                    "description": "This parameter is the eastward component of the surface Stokes drift. The Stokes drift is the  net drift velocity due to surface wind waves. It is confined to the upper few metres of the  ocean water column, with the largest value at the surface.\nFor example, a fluid particle near the surface will slowly move in the direction of wave  propagation.",
                    "units": "m s^-1",
                },
                "UV visible albedo for diffuse radiation": {
                    "description": "Albedo is a measure of the reflectivity of the Earth's surface. This parameter is the  fraction of diffuse solar (shortwave) radiation with wavelengths between 0.3 and 0.7 µm  (microns, 1 millionth of a metre) reflected by the Earth's surface (for snow-free land  surfaces only).\nIn the ECMWF Integrated Forecasting System (IFS) albedo is dealt with separately for solar  radiation with wavelengths greater/less than 0.7µm and for direct and diffuse solar  radiation (giving 4 components to albedo).\nSolar radiation at the surface can be direct or diffuse. Solar radiation can be scattered in  all directions by particles in the atmosphere, some of which reaches the surface (diffuse  solar radiation). Some solar radiation reaches the surface without being scattered (direct  solar radiation).\nIn the IFS, a climatological (observed values averaged over a period of several years)  background albedo is used which varies from month to month through the year, modified by the  model over water, ice and snow.\nThis parameter varies between 0 and 1.",
                    "units": "Dimensionless",
                },
                "UV visible albedo for direct radiation": {
                    "description": "Albedo is a measure of the reflectivity of the Earth's surface. This parameter is the  fraction of direct solar (shortwave) radiation with wavelengths between 0.3 and 0.7 µm  (microns, 1 millionth of a metre) reflected by the Earth's surface (for snow-free land  surfaces only).\nIn the ECMWF Integrated Forecasting System (IFS) albedo is dealt with separately for solar  radiation with wavelengths greater/less than 0.7µm and for direct and diffuse solar radiation  (giving 4 components to albedo).\nSolar radiation at the surface can be direct or diffuse. Solar radiation can be scattered in  all directions by particles in the atmosphere, some of which reaches the surface (diffuse solar  radiation). Some solar radiation reaches the surface without being scattered (direct solar  radiation).\nIn the IFS, a climatological (observed values averaged over a period of several years)  background albedo is used which varies from month to month through the year, modified by the  model over water, ice and snow.",
                    "units": "Dimensionless",
                },
                "V-component stokes drift": {
                    "description": "This parameter is the northward component of the surface Stokes drift. The Stokes drift is  the net drift velocity due to surface wind waves. It is confined to the upper few metres of  the ocean water column, with the largest value at the surface.\nFor example, a fluid particle near the surface will slowly move in the direction of wave  propagation.",
                    "units": "m s^-1",
                },
                "Vertical integral of divergence of cloud frozen water flux": {
                    "description": 'The vertical integral of the cloud frozen water flux is the horizontal rate of flow of cloud  frozen water, per metre across the flow, for a column of air extending from the surface of the  Earth to the top of the atmosphere. Its horizontal divergence is the rate of cloud frozen water  spreading outward from a point, per square metre. This parameter is positive for cloud frozen  water that is spreading out, or diverging, and negative for the opposite, for cloud frozen  water that is concentrating, or converging (convergence).\nThis parameter thus indicates whether atmospheric motions act to decrease (for divergence) or  increase (for convergence) the vertical integral of cloud frozen water.\nNote that "cloud frozen water" is the same as "cloud ice water".',
                    "units": "kg m^-2 s^-1",
                },
                "Vertical integral of divergence of cloud liquid water flux": {
                    "description": "The vertical integral of the cloud liquid water flux is the horizontal rate of flow of cloud  liquid water, per metre across the flow, for a column of air extending from the surface of the  Earth to the top of the atmosphere. Its horizontal divergence is the rate of cloud liquid water  spreading outward from a point, per square metre. This parameter is positive for cloud liquid  water that is spreading out, or diverging, and negative for the opposite, for cloud liquid  water that is concentrating, or converging (convergence).\nThis parameter thus indicates whether atmospheric motions act to decrease (for divergence) or  increase (for convergence) the vertical integral of cloud liquid water.",
                    "units": "kg m^-2 s^-1",
                },
                "Vertical integral of divergence of geopotential flux": {
                    "description": "The vertical integral of the geopotential flux is the horizontal rate of flow of geopotential,  per metre across the flow, for a column of air extending from the surface of the Earth to the  top of the atmosphere. Its horizontal divergence is the rate of geopotential spreading outward  from a point, per square metre.\nThis parameter is positive for geopotential that is spreading out, or diverging, and negative  for the opposite, for geopotential that is concentrating, or converging (convergence).\nThis parameter thus indicates whether atmospheric motions act to decrease (for divergence) or  increase (for convergence) the vertical integral of geopotential.\nGeopotential is the gravitational potential energy of a unit mass, at a particular location,  relative to mean sea level. It is also the amount of work that would have to be done, against  the force of gravity, to lift a unit mass to that location from mean sea level.\nThis parameter can be used to study the atmospheric energy budget.",
                    "units": "W m^-2",
                },
                "Vertical integral of divergence of kinetic energy flux": {
                    "description": "The vertical integral of the kinetic energy flux is the horizontal rate of flow of kinetic  energy, per metre across the flow, for a column of air extending from the surface of the Earth  to the top of the atmosphere. Its horizontal divergence is the rate of kinetic energy spreading  outward from a point, per square metre. This parameter is positive for kinetic energy that is  spreading out, or diverging, and negative for the opposite, for kinetic energy that is  concentrating, or converging (convergence).\nThis parameter thus indicates whether atmospheric motions act to decrease (for divergence) or  increase (for convergence) the vertical integral of kinetic energy.\nAtmospheric kinetic energy is the energy of the atmosphere due to its motion. Only horizontal  motion is considered in the calculation of this parameter.\nThis parameter can be used to study the atmospheric energy budget.",
                    "units": "W m^-2",
                },
                "Vertical integral of divergence of mass flux": {
                    "description": "The vertical integral of the mass flux is the horizontal rate of flow of mass, per metre across  the flow, for a column of air extending from the surface of the Earth to the top of the atmosphere.  Its horizontal divergence is the rate of mass spreading outward from a point, per square metre.\nThis parameter is positive for mass that is spreading out, or diverging, and negative for the  opposite, for mass that is concentrating, or converging (convergence).\nThis parameter thus indicates whether atmospheric motions act to decrease (for divergence) or  increase (for convergence) the vertical integral of mass.\nThis parameter can be used to study the atmospheric mass and energy budgets.",
                    "units": "kg m^-2 s^-1",
                },
                "Vertical integral of divergence of moisture flux": {
                    "description": "The vertical integral of the moisture flux is the horizontal rate of flow of moisture, per metre  across the flow, for a column of air extending from the surface of the Earth to the top of the  atmosphere. Its horizontal divergence is the rate of moisture spreading outward from a point, per  square metre.\nThis parameter is positive for moisture that is spreading out, or diverging, and negative for the  opposite, for moisture that is concentrating, or converging (convergence).\nThis parameter thus indicates whether atmospheric motions act to decrease (for divergence) or  increase (for convergence) the vertical integral of moisture.\n1 kg of water spread over 1 square metre of surface is 1 mm deep (neglecting the effects  of temperature on the density of water), therefore the units are equivalent to mm (of  liquid water) per second.",
                    "units": "kg m^-2 s^-1",
                },
                "Vertical integral of divergence of ozone flux": {
                    "description": "The vertical integral of the ozone flux is the horizontal rate of flow of ozone, per metre across  the flow, for a column of air extending from the surface of the Earth to the top of the  atmosphere. Its horizontal divergence is the rate of ozone spreading outward from a point, per  square metre.\nThis parameter is positive for ozone that is spreading out, or diverging, and negative for the  opposite, for ozone that is concentrating, or converging (convergence).\nThis parameter thus indicates whether atmospheric motions act to decrease (for divergence) or  increase (for convergence) the vertical integral of ozone.\nIn the ECMWF Integrated Forecasting System (IFS), there is a simplified representation of ozone  chemistry (including a representation of the chemistry which has caused the ozone hole). Ozone is  also transported around in the atmosphere through the motion of air.",
                    "units": "kg m^-2 s^-1",
                },
                "Vertical integral of divergence of thermal energy flux": {
                    "description": "The vertical integral of the thermal energy flux is the horizontal rate of flow of thermal energy,  per metre across the flow, for a column of air extending from the surface of the Earth to the top  of the atmosphere. Its horizontal divergence is the rate of thermal energy spreading outward from  a point, per square metre.\nThis parameter is positive for thermal energy that is spreading out, or diverging, and negative  for the opposite, for thermal energy that is concentrating, or converging (convergence).\nThis parameter thus indicates whether atmospheric motions act to decrease (for divergence) or  increase (for convergence) the vertical integral of thermal energy.\nThe thermal energy is equal to enthalpy, which is the sum of the internal energy and the energy  associated with the pressure of the air on its surroundings.\nInternal energy is the energy contained within a system i.e., the microscopic energy of the air  molecules, rather than the macroscopic energy associated with, for example, wind, or gravitational  potential energy. The energy associated with the pressure of the air on its surroundings is the  energy required to make room for the system by displacing its surroundings and is calculated from  the product of pressure and volume.\nThis parameter can be used to study the flow of thermal energy through the climate system and to  investigate the atmospheric energy budget.",
                    "units": "W m^-2",
                },
                "Vertical integral of divergence of total energy flux": {
                    "description": "The vertical integral of the total energy flux is the horizontal rate of flow of total energy,  per metre across the flow, for a column of air extending from the surface of the Earth to the top  of the atmosphere. Its horizontal divergence is the rate of total energy spreading outward from  a point, per square metre.\nThis parameter is positive for total energy that is spreading out, or diverging, and negative  for the opposite, for total energy that is concentrating, or converging (convergence).\nThis parameter thus indicates whether atmospheric motions act to decrease (for divergence) or  increase (for convergence) the vertical integral of total energy.\nTotal atmospheric energy is made up of internal, potential, kinetic and latent energy.\nThis parameter can be used to study the atmospheric energy budget.",
                    "units": "W m^-2",
                },
                "Vertical integral of eastward cloud frozen water flux": {
                    "description": 'This parameter is the horizontal rate of flow of cloud frozen water, in the eastward direction,  per metre across the flow, for a column of air extending from the surface of the Earth to the top  of the atmosphere. Positive values indicate a flux from west to east.\nNote that "cloud frozen water" is the same as "cloud ice water".',
                    "units": "kg m^-1 s^-1",
                },
                "Vertical integral of eastward cloud liquid water flux": {
                    "description": "This parameter is the horizontal rate of flow of cloud liquid water, in the eastward direction,  per metre across the flow, for a column of air extending from the surface of the Earth to the top  of the atmosphere. Positive values indicate a flux from west to east.",
                    "units": "kg m^-1 s^-1",
                },
                "Vertical integral of eastward geopotential flux": {
                    "description": "This parameter is the horizontal rate of flow of geopotential, in the eastward direction, per  metre across the flow, for a column of air extending from the surface of the Earth to the top of  the atmosphere. Positive values indicate a flux from west to east.\nGeopotential is the gravitational potential energy of a unit mass, at a particular location,  relative to mean sea level. It is also the amount of work that would have to be done, against  the force of gravity, to lift a unit mass to that location from mean sea level.\nThis parameter can be used to study the atmospheric energy budget.",
                    "units": "W m^-1",
                },
                "Vertical integral of eastward heat flux": {
                    "description": "This parameter is the horizontal rate of flow of heat in the eastward direction, per meter across  the flow, for a column of air extending from the surface of the Earth to the top of the  atmosphere. Positive values indicate a flux from west to east.\nHeat (or thermal energy) is equal to enthalpy, which is the sum of the internal energy and the  energy associated with the pressure of the air on its surroundings.\nInternal energy is the energy contained within a system i.e., the microscopic energy of the air  molecules, rather than the macroscopic energy associated with, for example, wind, or gravitational  potential energy. The energy associated with the pressure of the air on its surroundings is the  energy required to make room for the system by displacing its surroundings and is calculated from  the product of pressure and volume.\nThis parameter can be used to study the atmospheric energy budget.",
                    "units": "W m^-1",
                },
                "Vertical integral of eastward kinetic energy flux": {
                    "description": "This parameter is the horizontal rate of flow of kinetic energy, in the eastward direction, per  metre across the flow, for a column of air extending from the surface of the Earth to the top of  the atmosphere. Positive values indicate a flux from west to east.\nAtmospheric kinetic energy is the energy of the atmosphere due to its motion. Only horizontal  motion is considered in the calculation of this parameter.\nThis parameter can be used to study the atmospheric energy budget.",
                    "units": "W m^-1",
                },
                "Vertical integral of eastward mass flux": {
                    "description": "This parameter is the horizontal rate of flow of mass, in the eastward direction, per metre  across the flow, for a column of air extending from the surface of the Earth to the top of the  atmosphere. Positive values indicate a flux from west to east.\nThis parameter can be used to study the atmospheric mass and energy budgets.",
                    "units": "kg m^-1 s^-1",
                },
                "Vertical integral of eastward ozone flux": {
                    "description": "This parameter is the horizontal rate of flow of ozone in the eastward direction, per metre  across the flow, for a column of air extending from the surface of the Earth to the top of the  atmosphere. Positive values denote a flux from west to east.\nIn the ECMWF Integrated Forecasting System (IFS), there is a simplified representation of  ozone chemistry (including a representation of the chemistry which has caused the ozone hole).  Ozone is also transported around in the atmosphere through the motion of air.",
                    "units": "kg m^-1 s^-1",
                },
                "Vertical integral of eastward total energy flux": {
                    "description": "This parameter is the horizontal rate of flow of total energy in the eastward direction, per  metre across the flow, for a column of air extending from the surface of the Earth to the top  of the atmosphere. Positive values indicate a flux from west to east.\nTotal atmospheric energy is made up of internal, potential, kinetic and latent energy.\nThis parameter can be used to study the atmospheric energy budget.",
                    "units": "W m^-1",
                },
                "Vertical integral of eastward water vapour flux": {
                    "description": "This parameter is the horizontal rate of flow of water vapour, in the eastward direction, per  metre across the flow, for a column of air extending from the surface of the Earth to the top  of the atmosphere. Positive values indicate a flux from west to east.",
                    "units": "kg m^-1 s^-1",
                },
                "Vertical integral of energy conversion": {
                    "description": "This parameter is one contribution to the amount of energy being converted between kinetic  energy, and internal plus potential energy, for a column of air extending from the surface of  the Earth to the top of the atmosphere. Negative values indicate a conversion to kinetic  energy from potential plus internal energy.\nThis parameter can be used to study the atmospheric energy budget. The circulation of the  atmosphere can also be considered in terms of energy conversions.",
                    "units": "W m^-2",
                },
                "Vertical integral of kinetic energy": {
                    "description": "This parameter is the vertical integral of kinetic energy for a column of air extending from  the surface of the Earth to the top of the atmosphere. Atmospheric kinetic energy is the  energy of the atmosphere due to its motion. Only horizontal motion is considered in the  calculation of this parameter.\nThis parameter can be used to study the atmospheric energy budget.",
                    "units": "J m^-2",
                },
                "Vertical integral of mass of atmosphere": {
                    "description": "This parameter is the total mass of air for a column extending from the surface of the Earth  to the top of the atmosphere, per square metre.\nThis parameter is calculated by dividing surface pressure by the Earth's gravitational  acceleration, g (=9.80665 m s^-2 ), and has units of kilograms per square metre.\nThis parameter can be used to study the atmospheric mass budget.",
                    "units": "kg m^-2",
                },
                "Vertical integral of mass tendency": {
                    "description": "This parameter is the rate of change of the mass of a column of air extending from the Earth's  surface to the top of the atmosphere. An increasing mass of the column indicates rising  surface pressure. In contrast, a decrease indicates a falling surface pressure.\nThe mass of the column is calculated by dividing pressure at the Earth's surface by the  gravitational acceleration, g (=9.80665 m s^-2 ).\nThis parameter can be used to study the atmospheric mass and energy budgets.",
                    "units": "kg m^-2 s^-1",
                },
                "Vertical integral of northward cloud frozen water flux": {
                    "description": 'This parameter is the horizontal rate of flow of cloud frozen water, in the northward direction,  per metre across the flow, for a column of air extending from the surface of the Earth to the top  of the atmosphere. Positive values indicate a flux from south to north.\nNote that "cloud frozen water" is the same as "cloud ice water".',
                    "units": "kg m^-1 s^-1",
                },
                "Vertical integral of northward cloud liquid water flux": {
                    "description": "This parameter is the horizontal rate of flow of cloud liquid water, in the northward direction,  per metre across the flow, for a column of air extending from the surface of the Earth to the top  of the atmosphere. Positive values indicate a flux from south to north.",
                    "units": "kg m^-1 s^-1",
                },
                "Vertical integral of northward geopotential flux": {
                    "description": "This parameter is the horizontal rate of flow of geopotential in the northward direction, per  metre across the flow, for a column of air extending from the surface of the Earth to the top  of the atmosphere. Positive values indicate a flux from south to north.\nGeopotential is the gravitational potential energy of a unit mass, at a particular location,  relative to mean sea level. It is also the amount of work that would have to be done, against  the force of gravity, to lift a unit mass to that location from mean sea level.\nThis parameter can be used to study the atmospheric energy budget.",
                    "units": "W m^-1",
                },
                "Vertical integral of northward heat flux": {
                    "description": "This parameter is the horizontal rate of flow of heat in the northward direction, per metre  across the flow, for a column of air extending from the surface of the Earth to the top of  the atmosphere. Positive values indicate a flux from south to north.\nHeat (or thermal energy) is equal to enthalpy, which is the sum of the internal energy and  the energy associated with the pressure of the air on its surroundings.\nInternal energy is the energy contained within a system i.e., the microscopic energy of the  air molecules, rather than the macroscopic energy associated with, for example, wind, or  gravitational potential energy. The energy associated with the pressure of the air on its  surroundings is the energy required to make room for the system by displacing its  surroundings and is calculated from the product of pressure and volume.\nThis parameter can be used to study the atmospheric energy budget.",
                    "units": "W m^-1",
                },
                "Vertical integral of northward kinetic energy flux": {
                    "description": "This parameter is the horizontal rate of flow of kinetic energy, in the northward direction,  per metre across the flow, for a column of air extending from the surface of the Earth to  the top of the atmosphere. Positive values indicate a flux from south to north.\nAtmospheric kinetic energy is the energy of the atmosphere due to its motion. Only  horizontal motion is considered in the calculation of this parameter.\nThis parameter can be used to study the atmospheric energy budget.",
                    "units": "W m^-1",
                },
                "Vertical integral of northward mass flux": {
                    "description": "This parameter is the horizontal rate of flow of mass, in the northward direction, per  metre across the flow, for a column of air extending from the surface of the Earth to the  top of the atmosphere. Positive values indicate a flux from south to north.\nThis parameter can be used to study the atmospheric mass and energy budgets.",
                    "units": "kg m^-1 s^-1",
                },
                "Vertical integral of northward ozone flux": {
                    "description": "This parameter is the horizontal rate of flow of ozone in the northward direction, per  metre across the flow, for a column of air extending from the surface of the Earth to the  top of the atmosphere. Positive values denote a flux from south to north.\nIn the ECMWF Integrated Forecasting System (IFS), there is a simplified representation of  ozone chemistry (including a representation of the chemistry which has caused the ozone  hole). Ozone is also transported around in the atmosphere through the motion of air.",
                    "units": "kg m^-1 s^-1",
                },
                "Vertical integral of northward total energy flux": {
                    "description": "This parameter is the horizontal rate of flow of total energy in the northward direction,  per metre across the flow, for a column of air extending from the surface of the Earth to  the top of the atmosphere. Positive values indicate a flux from south to north.\nTotal atmospheric energy is made up of internal, potential, kinetic and latent energy.\nThis parameter can be used to study the atmospheric energy budget.",
                    "units": "W m^-1",
                },
                "Vertical integral of northward water vapour flux": {
                    "description": "This parameter is the horizontal rate of flow of water vapour, in the northward direction,  per metre across the flow, for a column of air extending from the surface of the Earth to  the top of the atmosphere. Positive values indicate a flux from south to north.",
                    "units": "kg m^-1 s^-1",
                },
                "Vertical integral of potential and internal energy": {
                    "description": "This parameter is the mass weighted vertical integral of potential and internal energy for  a column of air extending from the surface of the Earth to the top of the atmosphere.\nThe potential energy of an air parcel is the amount of work that would have to be done,  against the force of gravity, to lift the air to that location from mean sea level.  Internal energy is the energy contained within a system i.e., the microscopic energy of  the air molecules, rather than the macroscopic energy associated with, for example, wind,  or gravitational potential energy.\nThis parameter can be used to study the atmospheric energy budget.\nTotal atmospheric energy is made up of internal, potential, kinetic and latent energy.",
                    "units": "J m^-2",
                },
                "Vertical integral of potential, internal and latent energy": {
                    "description": "This parameter is the mass weighted vertical integral of potential, internal and latent  energy for a column of air extending from the surface of the Earth to the top of the  atmosphere.\nThe potential energy of an air parcel is the amount of work that would have to be done,  against the force of gravity, to lift the air to that location from mean sea level.  Internal energy is the energy contained within a system i.e., the microscopic energy of  the air molecules, rather than the macroscopic energy associated with, for example, wind,  or gravitational potential energy.\nThe latent energy refers to the energy associated with the water vapour in the atmosphere  and is equal to the energy required to convert liquid water into water vapour.\nThis parameter can be used to study the atmospheric energy budget.\nTotal atmospheric energy is made up of internal, potential, kinetic and latent energy.",
                    "units": "J m^-2",
                },
                "Vertical integral of temperature": {
                    "description": "This parameter is the mass-weighted vertical integral of temperature for a column of air  extending from the surface of the Earth to the top of the atmosphere.\nThis parameter can be used to study the atmospheric energy budget.",
                    "units": "K kg m^-2",
                },
                "Vertical integral of thermal energy": {
                    "description": "This parameter is the mass-weighted vertical integral of thermal energy for a column of  air extending from the surface of the Earth to the top of the atmosphere. Thermal energy  is calculated from the product of temperature and the specific heat capacity of air at  constant pressure.\nThe thermal energy is equal to enthalpy, which is the sum of the internal energy and the  energy associated with the pressure of the air on its surroundings.\nInternal energy is the energy contained within a system i.e., the microscopic energy of  the air molecules, rather than the macroscopic energy associated with, for example, wind,  or gravitational potential energy. The energy associated with the pressure of the air on  its surroundings is the energy required to make room for the system by displacing its  surroundings and is calculated from the product of pressure and volume.\nThis parameter can be used to study the atmospheric energy budget.\nTotal atmospheric energy is made up of internal, potential, kinetic and latent energy.",
                    "units": "J m^-2",
                },
                "Vertical integral of total energy": {
                    "description": "This parameter is the vertical integral of total energy for a column of air extending from  the surface of the Earth to the top of the atmosphere.\nTotal atmospheric energy is made up of internal, potential, kinetic and latent energy.\nThis parameter can be used to study the atmospheric energy budget.",
                    "units": "J m^-2",
                },
                "Vertically integrated moisture divergence": {
                    "description": "The vertical integral of the moisture flux is the horizontal rate of flow of moisture  (water vapour, cloud liquid and cloud ice), per metre across the flow, for a column of  air extending from the surface of the Earth to the top of the atmosphere. Its horizontal  divergence is the rate of moisture spreading outward from a point, per square metre.\nThis parameter is accumulated over a particular time period which depends on the data extracted.  For the reanalysis, the accumulation period is over the 1 hour ending at the validity date and time.  For the ensemble members, ensemble mean and ensemble spread, the accumulation period is over the  3 hours ending at the validity date and time.\nThis parameter is positive for moisture that is spreading out, or diverging, and negative  for the opposite, for moisture that is concentrating, or converging (convergence). This  parameter thus indicates whether atmospheric motions act to decrease (for divergence) or  increase (for convergence) the vertical integral of moisture, over the time period. High  negative values of this parameter (i.e. large moisture convergence) can be related to  precipitation intensification and floods.\n1 kg of water spread over 1 square metre of surface is 1 mm deep (neglecting the effects  of temperature on the density of water), therefore the units are equivalent to mm.",
                    "units": "kg m^-2",
                },
                "Volumetric soil water layer 1": {
                    "description": "This parameter is the volume of water in soil layer 1 (0 - 7cm, the surface is at 0cm).\nThe ECMWF Integrated Forecasting System (IFS) has a four-layer representation of soil: Layer 1: 0 - 7cm, Layer 2: 7 - 28cm, Layer 3: 28 - 100cm, Layer 4: 100 - 289cm.\nSoil water is defined over the whole globe, even over ocean. Regions with a water surface can be masked out by only considering grid points where the land-sea mask has a value greater than 0.5.\nThe volumetric soil water is associated with the soil texture (or classification), soil  depth, and the underlying groundwater level.",
                    "units": "m^3 m^-3",
                },
                "Volumetric soil water layer 2": {
                    "description": "This parameter is the volume of water in soil layer 2 (7 - 28cm, the surface is at 0cm).\nThe ECMWF Integrated Forecasting System (IFS) has a four-layer representation of soil: Layer 1: 0 - 7cm, Layer 2: 7 - 28cm, Layer 3: 28 - 100cm, Layer 4: 100 - 289cm.\nSoil water is defined over the whole globe, even over ocean. Regions with a water surface can be masked out by only considering grid points where the land-sea mask has a value greater than 0.5.\nThe volumetric soil water is associated with the soil texture (or classification), soil  depth, and the underlying groundwater level.",
                    "units": "m^3 m^-3",
                },
                "Volumetric soil water layer 3": {
                    "description": "This parameter is the volume of water in soil layer 3 (28 - 100cm, the surface is at 0cm).\nThe ECMWF Integrated Forecasting System (IFS) has a four-layer representation of soil: Layer 1: 0 - 7cm, Layer 2: 7 - 28cm, Layer 3: 28 - 100cm, Layer 4: 100 - 289cm.\nSoil water is defined over the whole globe, even over ocean. Regions with a water surface can be masked out by only considering grid points where the land-sea mask has a value greater than 0.5.\nThe volumetric soil water is associated with the soil texture (or classification), soil  depth, and the underlying groundwater level.",
                    "units": "m^3 m^-3",
                },
                "Volumetric soil water layer 4": {
                    "description": "This parameter is the volume of water in soil layer 4 (100 - 289cm, the surface is at 0cm).\nThe ECMWF Integrated Forecasting System (IFS) has a four-layer representation of soil: Layer 1: 0 - 7cm, Layer 2: 7 - 28cm, Layer 3: 28 - 100cm, Layer 4: 100 - 289cm.\nSoil water is defined over the whole globe, even over ocean. Regions with a water surface can be masked out by only considering grid points where the land-sea mask has a value greater than 0.5.\nThe volumetric soil water is associated with the soil texture (or classification), soil  depth, and the underlying groundwater level.",
                    "units": "m^3 m^-3",
                },
                "Wave spectral directional width": {
                    "description": "This parameter indicates whether waves (generated by local winds and associated with swell)  are coming from similar directions or from a wide range of directions.\nThe ocean/sea surface wave field consists of a combination of waves with different heights,  lengths and directions (known as the two-dimensional wave spectrum). Many ECMWF wave  parameters (such as the mean wave period) give information averaged over all wave  frequencies and directions, so do not give any information about the distribution of wave  energy across frequencies and directions. This parameter gives more information about the  nature of the two-dimensional wave spectrum. This parameter is a measure of the range of  wave directions for each frequency integrated across the two-dimensional spectrum.\nThis parameter takes values between 0 and the square root of 2. Where 0 corresponds to a  uni-directional spectrum (i.e., all wave frequencies from the same direction) and the square  root of 2 indicates a uniform spectrum (i.e., all wave frequencies from a different  direction).",
                    "units": "Dimensionless",
                },
                "Wave spectral directional width for swell": {
                    "description": "This parameter indicates whether waves associated with swell are coming from similar  directions or from a wide range of directions.\nThe ocean/sea surface wave field consists of a combination of waves with different heights,  lengths and directions (known as the two-dimensional wave spectrum). The wave spectrum can  be decomposed into wind-sea waves, which are directly affected by local winds, and swell,  the waves that were generated by the wind at a different location and time. This parameter  takes account of all swell only.\nMany ECMWF wave parameters (such as the mean wave period) give information averaged over  all wave frequencies and directions, so do not give any information about the distribution  of wave energy across frequencies and directions. This parameter gives more information  about the nature of the two-dimensional wave spectrum. This parameter is a measure of the  range of wave directions for each frequency integrated across the two-dimensional spectrum.\nThis parameter takes values between 0 and the square root of 2. Where 0 corresponds to a  uni-directional spectrum (i.e., all wave frequencies from the same direction) and the square  root of 2 indicates a uniform spectrum (i.e., all wave frequencies from a different  direction).",
                    "units": "Dimensionless",
                },
                "Wave spectral directional width for wind waves": {
                    "description": "This parameter indicates whether waves generated by the local wind are coming from similar  directions or from a wide range of directions.\nThe ocean/sea surface wave field consists of a combination of waves with different heights,  lengths and directions (known as the two-dimensional wave spectrum). The wave spectrum can  be decomposed into wind-sea waves, which are directly affected by local winds, and swell,  the waves that were generated by the wind at a different location and time. This parameter  takes account of wind-sea waves only.\nMany ECMWF wave parameters (such as the mean wave period) give information averaged over  all wave frequencies and directions, so do not give any information about the distribution  of wave energy across frequencies and directions. This parameter gives more information  about the nature of the two-dimensional wave spectrum. This parameter is a measure of the  range of wave directions for each frequency integrated across the two-dimensional spectrum.\nThis parameter takes values between 0 and the square root of 2. Where 0 corresponds to a  uni-directional spectrum (i.e., all wave frequencies from the same direction) and the square  root of 2 indicates a uniform spectrum (i.e., all wave frequencies from a different  direction).",
                    "units": "Dimensionless",
                },
                "Wave spectral kurtosis": {
                    "description": "This parameter is a statistical measure used to forecast extreme or freak ocean/sea waves.  It describes the nature of the sea surface elevation and how it is affected by waves  generated by local winds and associated with swell.\nUnder typical conditions, the sea surface elevation, as described by its probability density  function, has a near normal distribution in the statistical sense. However, under certain  wave conditions the probability density function of the sea surface elevation can deviate  considerably from normality, signalling increased probability of freak waves.\nThis parameter gives one measure of the deviation from normality. It shows how much of the  probability density function of the sea surface elevation exists in the tails of the  distribution. So, a positive kurtosis (typical range 0.0 to 0.06) means more frequent  occurrences of very extreme values (either above or below the mean), relative to a normal  distribution.",
                    "units": "Dimensionless",
                },
                "Wave spectral peakedness": {
                    "description": "This parameter is a statistical measure used to forecast extreme or freak waves. It is a  measure of the relative width of the ocean/sea wave frequency spectrum (i.e., whether the  ocean/sea wave field is made up of a narrow or broad range of frequencies).\nThe ocean/sea surface wave field consists of a combination of waves with different heights,  lengths and directions (known as the two-dimensional wave spectrum). When the wave field is  more focussed around a narrow range of frequencies, the probability of freak/extreme waves  increases.\nThis parameter is Goda's peakedness factor and is used to calculate the Benjamin-Feir Index  (BFI). The BFI is in turn used to estimate the probability and nature of extreme/freak waves.",
                    "units": "Dimensionless",
                },
                "Wave spectral skewness": {
                    "description": "This parameter is a statistical measure used to forecast extreme or freak ocean/sea waves.  It describes the nature of the sea surface elevation and how it is affected by waves  generated by local winds and associated with swell.\nUnder typical conditions, the sea surface elevation, as described by its probability density  function, has a near normal distribution in the statistical sense. However, under certain  wave conditions the probability density function of the sea surface elevation can deviate  considerably from normality, signalling increased probability of freak waves.\nThis parameter gives one measure of the deviation from normality. It is a measure of the  asymmetry of the probability density function of the sea surface elevation. So, a  positive/negative skewness (typical range -0.2 to 0.12) means more frequent occurrences of  extreme values above/below the mean, relative to a normal distribution.",
                    "units": "Dimensionless",
                },
                "Zero degree level": {
                    "description": "The height above the Earth's surface where the temperature passes from positive to negative  values, corresponding to the top of a warm layer, at the specified time. This parameter can  be used to help forecast snow.\nIf more than one warm layer is encountered, then the zero degree level corresponds to the  top of the second atmospheric layer.\nThis parameter is set to zero when the temperature in the whole atmosphere is below 0℃.",
                    "units": "m",
                },
            },
            "providers": None,
            "summaries": None,
            "extent": None,
            "documentation": [
                {
                    "url": "https://confluence.ecmwf.int/display/CKB/ERA5%3A+data+documentation",
                    "title": "ERA5 data documentation",
                    "description": "Detailed information relating to the ERA5 data archive can be found in the web link above.",
                },
                {
                    "url": "https://rmets.onlinelibrary.wiley.com/doi/10.1002/qj.4174",
                    "title": "The ERA5 global reanalysis: Preliminary extension to 1950",
                    "description": "Journal article describing the ERA5 preliminary extension.",
                    "kind": "",
                },
                {
                    "url": "https://rmets.onlinelibrary.wiley.com/doi/10.1002/qj.3803",
                    "title": "The ERA5 global reanalysis",
                    "description": "Journal article describing ERA5.",
                    "kind": "",
                },
                {
                    "url": "https://confluence.ecmwf.int/x/ggleC",
                    "title": "Renamed variable: form ocean waves 10m wind to ocean surface stress equivalent 10m neutral wind",
                    "description": "The reason for the change was a parameter name clash between variables in ERA5 wind and ERA5 ocean waves.",
                },
            ],
            "type": "dataset",
            "previewimage": "resources/reanalysis-era5-single-levels/overview.jpg",
            "publication_date": None,
            "record_update": None,
            "references": [
                {
                    "title": "Citation",
                    "content": "resources/reanalysis-era5-single-levels/citation.html",
                    "copy": True,
                    "url": None,
                    "download_file": None,
                },
                {
                    "title": "Acknowledgement",
                    "content": "resources/reanalysis-era5-single-levels/acknowledgement.html",
                    "copy": None,
                    "url": None,
                    "download_file": None,
                },
            ],
            "resource_update": datetime.date(2022, 6, 9),
            "use_eqc": True,
        },
    ]

    # run the script to load test data
    result = runner.invoke(
        entry_points.app,
        ["setup-test-database", "--connection-string", connection_string],
        env={"DOCUMENT_STORAGE": str(tmp_path)},
    )
    # check no errors
    assert result.exit_code == 0
    # check document storage
    for dataset in [
        "reanalysis-era5-land-monthly-means",
        "reanalysis-era5-pressure-levels",
    ]:
        for filename in ["constraints.json", "form.json"]:
            assert os.path.exists(
                os.path.join(tmp_path, "resources", dataset, filename)
            )
    assert os.path.exists(
        os.path.join(
            tmp_path,
            "licences",
            "licence-to-use-copernicus-products",
            "licence-to-use-copernicus-products.pdf",
        )
    )
    # check db content
    session = session_obj()
    resources = [
        manager.object_as_dict(r)
        for r in session.query(database.Resource).order_by(
            database.Resource.resource_uid
        )
    ]
    licences = [
        manager.object_as_dict(ll) for ll in session.query(database.Licence).all()
    ]

    assert licences == expected_licences
    for i, resource in enumerate(resources):
        for key in resource:
            if key == "record_update":
                continue
            assert resource[key] == expected_resources[i][key]
    session.close()

    # uncomment to update testdb.sql
    # import subprocess
    # dump_path = os.path.join(TESTDATA_PATH, "testdb.sql")
    # with open(dump_path, "w") as dumped_file:
    #     ret = subprocess.call(["pg_dump", connection_string], stdout=dumped_file)
    # assert ret == 0
    # assert os.path.exists(dump_path)
