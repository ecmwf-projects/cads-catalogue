--
-- PostgreSQL database dump
--

-- Dumped from database version 12.9
-- Dumped by pg_dump version 12.9

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: licences; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.licences (
    licence_id character varying NOT NULL,
    revision character varying NOT NULL,
    title character varying NOT NULL,
    download_filename character varying NOT NULL
);


ALTER TABLE public.licences OWNER TO postgres;

--
-- Name: resources; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.resources (
    resource_id character varying(1024) NOT NULL,
    stac_extensions character varying(300)[],
    title character varying(1024),
    description jsonb NOT NULL,
    abstract text NOT NULL,
    contact character varying(300)[],
    form jsonb,
    citation text,
    keywords character varying(300)[],
    version character varying(300),
    variables jsonb,
    providers jsonb,
    summaries jsonb,
    extent jsonb,
    links jsonb,
    documentation jsonb,
    type character varying(300) NOT NULL,
    previewimage text,
    publication_date date,
    record_update timestamp with time zone,
    resource_update date
);


ALTER TABLE public.resources OWNER TO postgres;

--
-- Name: resources_licences; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.resources_licences (
    resource_id character varying NOT NULL,
    licence_id character varying NOT NULL,
    revision character varying NOT NULL
);


ALTER TABLE public.resources_licences OWNER TO postgres;

--
-- Data for Name: licences; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.licences (licence_id, revision, title, download_filename) FROM stdin;
earth-radiation-budget-nasa-ceres-licence	2	NASA-CERES-EBAF licence	earth-radiation-budget-nasa-ceres-licence.pdf
ESA-CCI-sea-ice-concentration	1	ESA-CCI sea ice concentration product licence	ESA-CCI-sea-ice-concentration.pdf
satellite-cloud-properties-clara	1	EUMETSAT CM SAF products licence	satellite-cloud-properties-clara.pdf
gruan-data-policy	1	GRUAN data policy	gruan-data-policy-2015.pdf
CCI-data-policy-for-satellite-surface-radiation-budget	3	CCI product licence	CCI-data-policy-for-satellite-surface-radiation-budget.pdf
cci	1	CCI datasets licence	cci.pdf
sst-cci-ensemble	1	SST CCI ensemble dataset licence	sst-cci-ensemble.pdf
eumetsat-rom-saf	4	EUMETSAT ROM SAF products licence	eumetsat-rom-saf.pdf
cordex-licence	1	CORDEX licence	cordex-licence.pdf
fire-cci_for_satellite-burned-area	1	Fire CCI licence	fire-cci_for_satellite-burned-area.pdf
Copernicus-Global-Land-product-licence	1	Copernicus Global Land product licence	Copernicus-Global-Land-product-licence.pdf
sis-european-windstorm-indicators-licence	1	Open Data Commons Open Database Licence	sis-european-windstorm-indicators-licence.pdf
uscrn	1	USCRN data policy	uscrnv1.pdf
global-land-observations-data-policy	1	Global land observations data policy	global-land-observations-data-policy.pdf
data-protection-privacy-statement	24	Data protection and privacy statement	2021_CDS_Privacy Statement_v2.4.pdf
eumetsat-cm-saf-uth	1	EUMETSAT CM SAF products licence	eumetsat-cm-saf-uth.pdf
vito-proba-v	1	VITO licence	vito-proba-v.pdf
uhz-glaciers	5	UZH Glaciers licence	uhz-glaciers.pdf
creative-commons-attribution-4-0-international-public-licence	1	Creative Commons Attribution 4.0 International Public Licence	creative-commons-attribution-4-0-international-public-licence.pdf
igra-data-policy	1	IGRA data policy	igra-data-policy.pdf
sst-cci	2	SST CCI datasets licence	sst-cci.pdf
satellite-lake-water-level	1	Licence	satellite-lake-water-level-licence.pdf
satellite-cloud-properties-cci	1	ESA CCI  products licence	satellite-cloud-properties-cci.pdf
glamod-data-policy	1	Global land and marine observations data policy	global-land-marine-observations-data-policy_v1.pdf
CMEMS-licence	1	CMEMS licence	CMEMS-licence.pdf
satellite-land-cover	1	ESA CCI licence	satellite-land-cover.pdf
cc-by	1	CC-BY licence	cc-by.pdf
eumetsat-osi-saf-sic	1	EUMETSAT OSI SAF sea ice concentration disclaimer	eumetsat-osi-saf-sic.pdf
gnss-data-policy	1	GNSS data policy	gnss-data-policy.pdf
creative-commons-attribution-noncommercial-4-0-international-public-licence	1	Creative Commons Attribution-NonCommercial 4.0 International Public Licence	creative-commons-attribution-noncommercial-4-0-international-public-licence.pdf
efas-cems	1	EFAS datasets licence	efas-cems.pdf
licence-to-use-insitu-glaciers-extent	7	UZH Glaciers Extent licence	licence-to-use-insitu-glaciers-extent.pdf
creative-commons-attribute-4-international-licence	1	Creative Commons Attribute 4.0 International License	creative-commons-attribute-4-international-licence.pdf
earth-radiation-budget-noaa-hirs-licence	1	NOAA/NCEI HIRS OLR licence	earth-radiation-budget-noaa-hirs-licence.pdf
creative-commons-attribution-sharealike-4-0-international-public-licence	1	Creative Commons Attribution-ShareAlike 4.0 International Public Licence	creative-commons-attribution-sharealike-4-0-international-public-licence.pdf
model-data-attribution	1	Product collective licence	model-data-attribution-license-D62.3.5.1.pdf
licence-to-use-E-OBS-products	1	E-OBS product licence	licence-to-use-E-OBS-products.pdf
licence-to-use-insitu-glaciers-elevation-mass	7	UZH Glaciers Elevation and Mass Change licence	licence-to-use-insitu-glaciers-elevation-mass.pdf
satellite-ocean-colour	1	ESA CCI  Essential Climate Variable products' licence	satellite-ocean-colour.pdf
global-precipitation-climatology-project	1	GPCP product licence	global-precipitation-climatology-project.pdf
terms-of-use-ads	1	Terms of use of the Copernicus Atmosphere Data Store	20200121_Terms_of_Use_of_the_Copernicus_Atmosphere_Data_Store_V1.0.pdf
modis_for_satellite-burned-area	1	MODIS licence	modis_for_satellite-burned-area.pdf
Additional-licence-to-use-non-European-contributions	1	Additional licence to use non European contributions	Additional-licence-to-use-non-European-contributions.pdf
ads-data-protection-privacy-statement	1	Data protection and privacy statement	20200121_ADS_Privacy_Statement_v1.0.pdf
esgf-cmip5	1	CMIP5 - Data Access - Terms of Use	esgf-cmip5.pdf
eumetsat-cm-saf	1	EUMETSAT CM SAF products licence	eumetsat-cm-saf.pdf
cems-floods	1	CEMS-FLOODS datasets licence	cems-floods.pdf
licence-to-use-copernicus-products	12	Licence to use Copernicus Products	licence-to-use-copernicus-products.pdf
cmip6-wps	1	CMIP6 - Data Access - Terms of Use	cmip6-wps.pdf
terms-of-use-cds	11	Terms of use of the Copernicus Climate Data Store	20180313_Terms_of_Use_of_the_Copernicus_Climate_Data_Store_V1.1.pdf
insitu-gridded-observations-global-and-regional	1	Product collective licence	insitu-gridded-observations-global-and-regional.pdf
eumetsat-osi-saf	1	EUMETSAT OSI SAF products licence	eumetsat-osi-saf.pdf
smhi-swicca	1	SMHI licence	smhi-swicca.pdf
licence-to-use-copernicus-products	1	Licence to Use Copernicus Products	20180314_Copernicus_License_V1.1.pdf
woudc-data-policy	1	WOUDC data policy	woudc-data-policy.pdf
cicero-cmip6-indicators-licence	1	CMIP6 indicators dataset licence (CICERO)	cicero-cmip6-indicators-licence.pdf
ec-sentinel	1	Copernicus Sentinel data licence	ec-sentinel.pdf
sst-cci	1	SST CCI datasets licence	sst-cci.pdf
ghg-cci	1	GHG-CCI Licence	ghg-cci.pdf
provider-without	1	Available licences	provider-without.pdf
\.


--
-- Data for Name: resources; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.resources (resource_id, stac_extensions, title, description, abstract, contact, form, citation, keywords, version, variables, providers, summaries, extent, links, documentation, type, previewimage, publication_date, record_update, resource_update) FROM stdin;
reanalysis-era5-land-monthly-means	\N	ERA5-Land monthly averaged data from 1950 to present	"{\\"file-format\\": \\"GRIB\\", \\"data-type\\": \\"Gridded\\", \\"projection\\": \\"Regular latitude-longitude grid\\", \\"horizontal-coverage\\": \\"Global\\", \\"horizontal-resolution\\": \\"0.1\\\\u00b0 x 0.1\\\\u00b0; Native resolution is 9 km.\\", \\"vertical-coverage\\": \\"From 2 m above the surface level, to a soil depth of 289 cm.\\\\n\\", \\"vertical-resolution\\": \\"4 levels of the ECMWF surface model: Layer 1: 0 -7cm, Layer 2: 7 -28cm, Layer 3: 28-100cm, Layer 4: 100-289cm\\\\nSome parameters are defined at 2 m over the surface.\\\\n\\", \\"temporal-coverage\\": \\"January 1950 to present\\", \\"temporal-resolution\\": \\"Monthly\\", \\"update-frequency\\": \\"Monthly with a delay of 2-3 months relatively to the actual date.\\"}"	ERA5-Land is a reanalysis dataset providing a consistent view of the evolution of land variables over several decades at an enhanced resolution compared to ERA5. ERA5-Land has been produced by replaying the land component of the ECMWF ERA5 climate reanalysis. Reanalysis combines model data with observations from across the world into a globally complete and consistent dataset using the laws of physics. Reanalysis produces data that goes several decades back in time, providing an accurate description of the climate of the past.\n\nERA5-Land provides a consistent view of the water and energy cycles at surface level during several decades.\nIt contains a detailed record from 1950 onwards, with a temporal resolution of 1 hour. The native spatial resolution of the ERA5-Land reanalysis dataset is 9km on a reduced Gaussian grid (TCo1279). The data in the CDS has been regridded to a regular lat-lon grid of 0.1x0.1 degrees.\n\nThe data presented here is a post-processed subset of the full ERA5-Land dataset. Monthly-mean averages have been pre-calculated to facilitate many applications requiring easy and fast access to the data, when sub-monthly fields are not required.\n\nHourly fields can be found in the [ERA5-Land hourly fields CDS page](https://cds-dev.copernicus-climate.eu/cdsapp#!/dataset/reanalysis-era5-land?tab=overview "ERA5-Land hourly data"). Documentation can be found in the [online ERA5-Land documentation](https://confluence.ecmwf.int/display/CKB/ERA5-Land+data+documentation "ERA5-Land data documentation").\n	\N	\N	\N	{"Product type: Reanalysis","Spatial coverage: Global","Temporal coverage: Past","Variable domain: Land (hydrology)","Variable domain: Land (physics)","Variable domain: Land (biosphere)","Provider: Copernicus C3S"}	\N	"{\\"10m u-component of wind\\": {\\"description\\": \\"Eastward component of the 10m wind. It is the horizontal speed of air moving towards the east, at a height of ten metres above the surface of the Earth, in metres per second. Care should be taken when comparing this variable with observations, because wind observations vary on small space and time scales and are affected by the local terrain, vegetation and buildings that are represented only on average in the ECMWF Integrated Forecasting System. This variable can be combined with the V component of 10m wind to give the speed and direction of the horizontal 10m wind.\\", \\"units\\": \\"m s^-1\\"}, \\"10m v-component of wind\\": {\\"description\\": \\"Northward component of the 10m wind. It is the horizontal speed of air moving towards the north, at a height of ten metres above the surface of the Earth, in metres per second. Care should be taken when comparing this variable with observations, because wind observations vary on small space and time scales and are affected by the local terrain, vegetation and buildings that are represented only on average in the ECMWF Integrated Forecasting System. This variable can be combined with the U component of 10m wind to give the speed and direction of the horizontal 10m wind.\\", \\"units\\": \\"m s^-1\\"}, \\"2m dewpoint temperature\\": {\\"description\\": \\"Temperature to which the air, at 2 metres above the surface of the Earth, would have to be cooled for saturation to occur.It is a measure of the humidity of the air. Combined with temperature and pressure, it can be used to calculate the relative humidity. 2m dew point temperature is calculated by interpolating between the lowest model level and the Earth's surface, taking account of the atmospheric conditions. Temperature measured in kelvin can be converted to degrees Celsius (\\\\u00b0C) by subtracting 273.15.\\", \\"units\\": \\"K\\"}, \\"2m temperature\\": {\\"description\\": \\"Temperature of air at 2m above the surface of land, sea or in-land waters. 2m temperature is calculated by interpolating between the lowest model level and the Earth's surface, taking account of the atmospheric conditions. Temperature measured in kelvin can be converted to degrees Celsius (\\\\u00b0C) by subtracting 273.15.\\", \\"units\\": \\"K\\"}, \\"Evaporation from bare soil\\": {\\"description\\": \\"The amount of evaporation from bare soil at the top of the land surface. This variable is accumulated from the beginning of the forecast time to the end of the forecast step.\\", \\"units\\": \\"m of water equivalent\\"}, \\"Evaporation from open water surfaces excluding oceans\\": {\\"description\\": \\"Amount of evaporation from surface water storage like lakes and inundated areas but excluding oceans. This variable is accumulated from the beginning of the forecast time to the end of the forecast step.\\", \\"units\\": \\"m of water equivalent\\"}, \\"Evaporation from the top of canopy\\": {\\"description\\": \\"The amount of evaporation from the canopy interception reservoir at the top of the canopy. This variable is accumulated from the beginning of the forecast time to the end of the forecast step.\\", \\"units\\": \\"m of water equivalent\\"}, \\"Evaporation from vegetation transpiration\\": {\\"description\\": \\"Amount of evaporation from vegetation transpiration. This has the same meaning as root extraction i.e. the amount of water extracted from the different soil layers. This variable is accumulated from the beginning of the forecast time to the end of the forecast step.\\", \\"units\\": \\"m of water equivalent\\"}, \\"Forecast albedo\\": {\\"description\\": \\"Is a measure of the reflectivity of the Earth's surface. It is the fraction of solar (shortwave) radiation reflected by Earth's surface, across the solar spectrum, for both direct and diffuse radiation. Values are between 0 and 1. Typically, snow and ice have high reflectivity with albedo values of 0.8 and above, land has intermediate values between about 0.1 and 0.4 and the ocean has low values of 0.1 or less. Radiation from the Sun (solar, or shortwave, radiation) is partly reflected back to space by clouds and particles in the atmosphere (aerosols) and some of it is absorbed. The rest is incident on the Earth's surface, where some of it is reflected. The portion that is reflected by the Earth's surface depends on the albedo. In the ECMWF Integrated Forecasting System (IFS), a climatological background albedo (observed values averaged over a period of several years) is used, modified by the model over water, ice and snow. Albedo is often shown as a percentage (%).\\", \\"units\\": \\"dimensionless\\"}, \\"Lake bottom temperature\\": {\\"description\\": \\"Temperature of water at the bottom of inland water bodies (lakes, reservoirs, rivers) and coastal waters. ECMWF implemented a lake model in May 2015 to represent the water temperature and lake ice of all the world\\\\u2019s major inland water bodies in the Integrated Forecasting System. The model keeps lake depth and surface area (or fractional cover) constant in time.\\", \\"units\\": \\"K\\"}, \\"Lake ice depth\\": {\\"description\\": \\"The thickness of ice on inland water bodies (lakes, reservoirs and rivers) and coastal waters. The ECMWF Integrated Forecasting System (IFS) represents the formation and melting of ice on inland water bodies (lakes, reservoirs and rivers) and coastal water. A single ice layer is represented. This parameter is the thickness of that ice layer.\\", \\"units\\": \\"m\\"}, \\"Lake ice temperature\\": {\\"description\\": \\"The temperature of the uppermost surface of ice on inland water bodies (lakes, reservoirs, rivers) and coastal waters. The ECMWF Integrated Forecasting System represents the formation and melting of ice on lakes. A single ice layer is represented. The temperature measured in kelvin can be converted to degrees Celsius (\\\\u00b0C) by subtracting 273.15.\\", \\"units\\": \\"K\\"}, \\"Lake mix-layer depth\\": {\\"description\\": \\"The thickness of the upper most layer of an inland water body (lake, reservoirs, and rivers) or coastal waters that is well mixed and has a near constant temperature with depth (uniform distribution of temperature). The ECMWF Integrated Forecasting System represents inland water bodies with two layers in the vertical, the mixed layer above and the thermocline below. Thermoclines upper boundary is located at the mixed layer bottom, and the lower boundary at the lake bottom. Mixing within the mixed layer can occur when the density of the surface (and near-surface) water is greater than that of the water below. Mixing can also occur through the action of wind on the surface of the lake.\\", \\"units\\": \\"m\\"}, \\"Lake mix-layer temperature\\": {\\"description\\": \\"The temperature of the upper most layer of inland water bodies (lakes, reservoirs and rivers) or coastal waters) that is well mixed. The ECMWF Integrated Forecasting System represents inland water bodies with two layers in the vertical, the mixed layer above and the thermocline below. Thermoclines upper boundary is located at the mixed layer bottom, and the lower boundary at the lake bottom. Mixing within the mixed layer can occur when the density of the surface (and near-surface) water is greater than that of the water below. Mixing can also occur through the action of wind on the surface of the lake. Temperature measured in kelvin can be converted to degrees Celsius (\\\\u00b0C) by subtracting 273.15.\\", \\"units\\": \\"K\\"}, \\"Lake shape factor\\": {\\"description\\": \\"This parameter describes the way that temperature changes with depth in the thermocline layer of inland water bodies (lakes, reservoirs and rivers) and coastal waters. It is used to calculate the lake bottom temperature and other lake-related parameters. The ECMWF Integrated Forecasting System represents inland and coastal water bodies with two layers in the vertical, the mixed layer above and the thermocline below where temperature changes with depth.\\", \\"units\\": \\"dimensionless\\"}, \\"Lake total layer temperature\\": {\\"description\\": \\"The mean temperature of total water column in inland water bodies (lakes, reservoirs and rivers) and coastal waters. The ECMWF Integrated Forecasting System represents inland water bodies with two layers in the vertical, the mixed layer above and the thermocline below where temperature changes with depth. This parameter is the mean over the two layers. Temperature measured in kelvin can be converted to degrees Celsius (\\\\u00b0C) by subtracting 273.15.\\", \\"units\\": \\"K\\"}, \\"Leaf area index, high vegetation\\": {\\"description\\": \\"One-half of the total green leaf area per unit horizontal ground surface area for high vegetation type.\\", \\"units\\": \\"m^2 m^-2\\"}, \\"Leaf area index, low vegetation\\": {\\"description\\": \\"One-half of the total green leaf area per unit horizontal ground surface area for low vegetation type.\\", \\"units\\": \\"m^2 m^-2\\"}, \\"Potential evaporation\\": {\\"description\\": \\"Potential evaporation (pev) in the current ECMWF model is computed, by making a second call to the surface energy balance routine with the vegetation variables set to \\\\\\"crops/mixed farming\\\\\\" and assuming no stress from soil moisture. In other words, evaporation is computed for agricultural land as if it is well watered and assuming that the atmosphere is not affected by this artificial surface condition. The latter may not always be realistic. Although pev is meant to provide an estimate of irrigation requirements, the method can give unrealistic results in arid conditions due to too strong evaporation forced by dry air. Note that in ERA5-Land pev is computed as an open water evaporation (Pan evaporation) and assuming that the atmosphere is not affected by this artificial surface condition. The latter is different from the way pev is computed in ERA5. This variable is accumulated from the beginning of the forecast time to the end of the forecast step.\\", \\"units\\": \\"m\\"}, \\"Runoff\\": {\\"description\\": \\"Some water from rainfall, melting snow, or deep in the soil, stays stored in the soil. Otherwise, the water drains away, either over the surface (surface runoff), or under the ground (sub-surface runoff) and the sum of these two is simply called 'runoff'. This variable is the total amount of water accumulated from the beginning of the forecast time to the end of the forecast step. The units of runoff are depth in metres. This is the depth the water would have if it were spread evenly over the grid box. Care should be taken when comparing model variables with observations, because observations are often local to a particular point rather than averaged over a grid square area.  Observations are also often taken in different units, such as mm/day, rather than the accumulated metres produced here. Runoff is a measure of the availability of water in the soil, and can, for example, be used as an indicator of drought or flood. More information about how runoff is calculated is given in the IFS Physical Processes documentation.\\", \\"units\\": \\"m\\"}, \\"Skin reservoir content\\": {\\"description\\": \\"Amount of water in the vegetation canopy and/or in a thin layer on the soil. It represents the amount of rain intercepted by foliage, and water from dew. The maximum amount of 'skin reservoir content' a grid box can hold depends on the type of vegetation, and may be zero.  Water leaves the 'skin reservoir' by evaporation.\\", \\"units\\": \\"m of water equivalent\\"}, \\"Skin temperature\\": {\\"description\\": \\"Temperature of the surface of the Earth. The skin temperature is the theoretical temperature that is required to satisfy the surface energy balance. It represents the temperature of the uppermost surface layer, which has no heat capacity and so can respond instantaneously to changes in surface fluxes. Skin temperature is calculated differently over land and sea. Temperature measured in kelvin can be converted to degrees Celsius (\\\\u00b0C) by subtracting 273.15.\\", \\"units\\": \\"K\\"}, \\"Snow albedo\\": {\\"description\\": \\"It is defined as the fraction of solar (shortwave) radiation reflected by the snow, across the solar spectrum, for both direct and diffuse radiation. It is a measure of the reflectivity of the snow covered grid cells. Values vary between 0 and 1. Typically, snow and ice have high reflectivity with albedo values of 0.8 and above.\\", \\"units\\": \\"dimensionless\\"}, \\"Snow cover\\": {\\"description\\": \\"It represents the fraction (0-1) of the cell / grid-box occupied by snow (similar to the cloud cover fields of ERA5).\\", \\"units\\": \\"%\\"}, \\"Snow density\\": {\\"description\\": \\"Mass of snow per cubic metre in the snow layer. The ECMWF Integrated Forecast System (IFS) model represents snow as a single additional layer over the uppermost soil level. The snow may cover all or part of the grid box.\\", \\"units\\": \\"kg m^-3\\"}, \\"Snow depth\\": {\\"description\\": \\"Instantaneous grib-box average of the snow thickness on the ground (excluding snow on canopy).\\", \\"units\\": \\"m\\"}, \\"Snow depth water equivalent\\": {\\"description\\": \\"Depth of snow from the snow-covered area of a grid box. Its units are metres of water equivalent, so it is the depth the water would have if the snow melted and was spread evenly over the whole grid box. The ECMWF Integrated Forecast System represents snow as a single additional layer over the uppermost soil level. The snow may cover all or part of the grid box.\\", \\"units\\": \\"m of water equivalent\\"}, \\"Snow evaporation\\": {\\"description\\": \\"Evaporation from snow averaged over the grid box (to find flux over snow, divide by snow fraction). This variable is accumulated from the beginning of the forecast time to the end of the forecast step.\\", \\"units\\": \\"m of water equivalent\\"}, \\"Snowfall\\": {\\"description\\": \\"Accumulated total snow that has fallen to the Earth's surface. It consists of snow due to the large-scale atmospheric flow (horizontal scales greater than around a few hundred metres) and convection where smaller scale areas (around 5km to a few hundred kilometres) of warm air rise. If snow has melted during the period over which this variable was accumulated, then it will be higher than the snow depth. This variable is the total amount of water accumulated from the beginning of the forecast time to the end of the forecast step. The units given measure the depth the water would have if the snow melted and was spread evenly over the grid box. Care should be taken when comparing model variables with observations, because observations are often local to a particular point in space and time, rather than representing averages over a model grid box and model time step.\\", \\"units\\": \\"m of water equivalent\\"}, \\"Snowmelt\\": {\\"description\\": \\"Melting of snow averaged over the grid box (to find melt over snow, divide by snow fraction). This variable is accumulated from the beginning of the forecast time to the end of the forecast step.\\", \\"units\\": \\"m of water equivalent\\"}, \\"Soil temperature level 1\\": {\\"description\\": \\"Temperature of the soil in layer 1 (0 - 7 cm) of the ECMWF Integrated Forecasting System. The surface is at 0 cm. Soil temperature is set at the middle of each layer, and heat transfer is calculated at the interfaces between them. It is assumed that there is no heat transfer out of the bottom of the lowest layer. Temperature measured in kelvin can be converted to degrees Celsius (\\\\u00b0C) by subtracting 273.15.\\", \\"units\\": \\"K\\"}, \\"Soil temperature level 2\\": {\\"description\\": \\"Temperature of the soil in layer 2 (7 -28cm) of the ECMWF Integrated Forecasting System.\\", \\"units\\": \\"K\\"}, \\"Soil temperature level 3\\": {\\"description\\": \\"Temperature of the soil in layer 3 (28-100cm) of the ECMWF Integrated Forecasting System.\\", \\"units\\": \\"K\\"}, \\"Soil temperature level 4\\": {\\"description\\": \\"Temperature of the soil in layer 4 (100-289 cm) of the ECMWF Integrated Forecasting System.\\", \\"units\\": \\"K\\"}, \\"Sub-surface runoff\\": {\\"description\\": \\"Some water from rainfall, melting snow, or deep in the soil, stays stored in the soil. Otherwise, the water drains away, either over the surface (surface runoff), or under the ground (sub-surface runoff) and the sum of these two is simply called 'runoff'. This variable is accumulated from the beginning of the forecast time to the end of the forecast step. The units of runoff are depth in metres. This is the depth the water would have if it were spread evenly over the grid box. Care should be taken when comparing model variables with observations, because observations are often local to a particular point rather than averaged over a grid square area.  Observations are also often taken in different units, such as mm/day, rather than the accumulated metres produced here. Runoff is a measure of the availability of water in the soil, and can, for example, be used as an indicator of drought or flood. More information about how runoff is calculated is given in the IFS Physical Processes documentation.\\", \\"units\\": \\"m\\"}, \\"Surface latent heat flux\\": {\\"description\\": \\"Exchange of latent heat with the surface through turbulent diffusion. This variables is accumulated from the beginning of the forecast time to the end of the forecast step. By model convention, downward fluxes are positive.\\", \\"units\\": \\"J m^-2\\"}, \\"Surface net solar radiation\\": {\\"description\\": \\"Amount of solar radiation (also known as shortwave radiation) reaching the surface of the Earth (both direct and diffuse) minus the amount reflected by the Earth's surface (which is governed by the albedo).Radiation from the Sun (solar, or shortwave, radiation) is partly reflected back to space by clouds and particles in the atmosphere (aerosols) and some of it is absorbed. The rest is incident on the Earth's surface, where some of it is reflected. The difference between downward and reflected solar radiation is the surface net solar radiation. This variable is accumulated from the beginning of the forecast time to the end of the forecast step. The units are joules per square metre (J m^-2). To convert to watts per square metre (W m^-2), the accumulated values should be divided by the accumulation period expressed in seconds. The ECMWF convention for vertical fluxes is positive downwards.\\", \\"units\\": \\"J m^-2\\"}, \\"Surface net thermal radiation\\": {\\"description\\": \\"Net thermal radiation at the surface. Accumulated field from the beginning of the forecast time to the end of the forecast step. By model convention downward fluxes are positive.\\", \\"units\\": \\"J m^-2\\"}, \\"Surface pressure\\": {\\"description\\": \\"Pressure (force per unit area) of the atmosphere on the surface of land, sea and in-land water. It is a measure of the weight of all the air in a column vertically above the area of the Earth's surface represented at a fixed point. Surface pressure is often used in combination with temperature to calculate air density. The strong variation of pressure with altitude makes it difficult to see the low and high pressure systems over mountainous areas, so mean sea level pressure, rather than surface pressure, is normally used for this purpose. The units of this variable are Pascals (Pa). Surface pressure is often measured in hPa and sometimes is presented in the old units of millibars, mb (1 hPa = 1 mb = 100 Pa).\\", \\"units\\": \\"Pa\\"}, \\"Surface runoff\\": {\\"description\\": \\"Some water from rainfall, melting snow, or deep in the soil, stays stored in the soil. Otherwise, the water drains away, either over the surface (surface runoff), or under the ground (sub-surface runoff) and the sum of these two is simply called 'runoff'. This variable is the total amount of water accumulated from the beginning of the forecast time to the end of the forecast step. The units of runoff are depth in metres. This is the depth the water would have if it were spread evenly over the grid box. Care should be taken when comparing model variables with observations, because observations are often local to a particular point rather than averaged over a grid square area. Observations are also often taken in different units, such as mm/day, rather than the accumulated metres produced here. Runoff is a measure of the availability of water in the soil, and can, for example, be used as an indicator of drought or flood. More information about how runoff is calculated is given in the IFS Physical Processes documentation.\\", \\"units\\": \\"m\\"}, \\"Surface sensible heat flux\\": {\\"description\\": \\"Transfer of heat between the Earth's surface and the atmosphere through the effects of turbulent air motion (but excluding any heat transfer resulting from condensation or evaporation). The magnitude of the sensible heat flux is governed by the difference in temperature between the surface and the overlying atmosphere, wind speed and the surface roughness. For example, cold air overlying a warm surface would produce a sensible heat flux from the land (or ocean) into the atmosphere. This is a single level variable and it is accumulated from the beginning of the forecast time to the end of the forecast step. The units are joules per square metre (J m^-2). To convert to watts per square metre (W m^-2), the accumulated values should be divided by the accumulation period expressed in seconds. The ECMWF convention for vertical fluxes is positive downwards.\\", \\"units\\": \\"J m^-2\\"}, \\"Surface solar radiation downwards\\": {\\"description\\": \\"Amount of solar radiation (also known as shortwave radiation) reaching the surface of the Earth. This variable comprises both direct and diffuse solar radiation. Radiation from the Sun (solar, or shortwave, radiation) is partly reflected back to space by clouds and particles in the atmosphere (aerosols) and some of it is absorbed.  The rest is incident on the Earth's surface (represented by this variable). To a reasonably good approximation, this variable is the model equivalent of what would be measured by a pyranometer (an instrument used for measuring solar radiation) at the surface. However, care should be taken when comparing model variables with observations, because observations are often local to a particular point in space and time, rather than representing averages over a  model grid box and model time step. This variable is accumulated from the beginning of the forecast time to the end of the forecast step. The units are joules per square metre (J m^-2). To convert to watts per square metre (W m^-2), the accumulated values should be divided by the accumulation period expressed in seconds. The ECMWF convention for vertical fluxes is positive downwards.\\", \\"units\\": \\"J m-2\\"}, \\"Surface thermal radiation downwards\\": {\\"description\\": \\"Amount of thermal (also known as longwave or terrestrial) radiation emitted by the atmosphere and clouds that reaches the Earth's surface. The surface of the Earth emits thermal radiation, some of which is absorbed by the atmosphere and clouds. The atmosphere and clouds likewise emit thermal radiation in all directions, some of which reaches the surface (represented by this variable). This variable is accumulated from the beginning of the forecast time to the end of the forecast step. The units are joules per square metre (J m^-2). To convert to watts per square metre (W m^-2), the accumulated values should be divided by the accumulation period expressed in seconds. The ECMWF convention for vertical fluxes is positive downwards.\\", \\"units\\": \\"J m-2\\"}, \\"Temperature of snow layer\\": {\\"description\\": \\"This variable gives the temperature of the snow layer from the ground to the snow-air interface. The ECMWF Integrated Forecast System (IFS) model represents snow as a single additional layer over the uppermost soil level. The snow may cover all or part of the  grid box. Temperature measured in kelvin can be converted to degrees Celsius (\\\\u00b0C) by subtracting 273.15.\\", \\"units\\": \\"K\\"}, \\"Total evaporation\\": {\\"description\\": \\"Accumulated amount of water that has evaporated from the Earth's surface, including a simplified representation of transpiration (from vegetation), into vapour in the air above. This variable is accumulated from the beginning of the forecast to the end of the forecast step. The ECMWF Integrated Forecasting System convention is that downward fluxes are positive. Therefore, negative values indicate evaporation and positive values indicate condensation.\\", \\"units\\": \\"m of water equivalent\\"}, \\"Total precipitation\\": {\\"description\\": \\"Accumulated liquid and frozen water, including rain and snow, that falls to the Earth's surface. It is the sum of large-scale precipitation (that precipitation which is generated by large-scale weather patterns, such as troughs and cold fronts) and convective precipitation (generated by convection which occurs when air at lower levels in the atmosphere is warmer and less dense than the air above, so it rises). Precipitation variables do not include fog, dew or the precipitation that evaporates in the atmosphere before it lands at the surface of the Earth. This variable is accumulated from the beginning of the forecast time to the end of the forecast step. The units of precipitation are depth in metres. It is the depth the water would have if it were spread evenly over the grid box. Care should be taken when comparing model variables with observations, because observations are often local to a particular point in space and time, rather than representing averages over a model grid box and  model time step.\\", \\"units\\": \\"m\\"}, \\"Volumetric soil water layer 1\\": {\\"description\\": \\"Volume of water in soil layer 1 (0 - 7 cm) of the ECMWF Integrated Forecasting System. The surface is at 0 cm. The volumetric soil water is associated with the soil texture (or classification), soil depth, and the underlying groundwater level.\\", \\"units\\": \\"m^3 m^-3\\"}, \\"Volumetric soil water layer 2\\": {\\"description\\": \\"Volume of water in soil layer 2 (7 -28 cm) of the ECMWF Integrated Forecasting System.\\", \\"units\\": \\"m^3 m^-3\\"}, \\"Volumetric soil water layer 3\\": {\\"description\\": \\"Volume of water in soil layer 3 (28-100 cm) of the ECMWF Integrated Forecasting System.\\", \\"units\\": \\"m^3 m^-3\\"}, \\"Volumetric soil water layer 4\\": {\\"description\\": \\"Volume of water in soil layer 4 (100-289 cm) of the ECMWF Integrated Forecasting System.\\", \\"units\\": \\"m^3 m^-3\\"}}"	\N	\N	\N	\N	"[{\\"url\\": \\"https://confluence.ecmwf.int/display/CKB/ERA5-Land%3A+data+documentation\\", \\"title\\": \\"ERA5-Land online documentation\\", \\"description\\": \\"Further and more detailed information relating to the ERA5-Land dataset can be found in the Copernicus Knowledge Base web link above.\\"}]"	dataset	overview.png	\N	2022-06-22 15:56:11.645599+02	\N
\.


--
-- Data for Name: resources_licences; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.resources_licences (resource_id, licence_id, revision) FROM stdin;
reanalysis-era5-land-monthly-means	licence-to-use-copernicus-products	12
\.


--
-- Name: licences licences_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.licences
    ADD CONSTRAINT licences_pkey PRIMARY KEY (licence_id, revision);


--
-- Name: resources_licences resources_licences_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.resources_licences
    ADD CONSTRAINT resources_licences_pkey PRIMARY KEY (resource_id, licence_id, revision);


--
-- Name: resources resources_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.resources
    ADD CONSTRAINT resources_pkey PRIMARY KEY (resource_id);


--
-- Name: resources_licences resources_licences_licence_id_revision_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.resources_licences
    ADD CONSTRAINT resources_licences_licence_id_revision_fkey FOREIGN KEY (licence_id, revision) REFERENCES public.licences(licence_id, revision);


--
-- Name: resources_licences resources_licences_resource_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.resources_licences
    ADD CONSTRAINT resources_licences_resource_id_fkey FOREIGN KEY (resource_id) REFERENCES public.resources(resource_id);


--
-- PostgreSQL database dump complete
--
