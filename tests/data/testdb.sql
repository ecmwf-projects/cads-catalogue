--
-- PostgreSQL database dump
--

-- Dumped from database version 14.4
-- Dumped by pg_dump version 14.4

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
-- Name: licences; Type: TABLE; Schema: public; Owner: catalogue
--

CREATE TABLE public.licences (
    licence_id integer NOT NULL,
    licence_uid character varying NOT NULL,
    revision integer NOT NULL,
    title character varying NOT NULL,
    download_filename character varying NOT NULL
);


ALTER TABLE public.licences OWNER TO catalogue;

--
-- Name: licences_licence_id_seq; Type: SEQUENCE; Schema: public; Owner: catalogue
--

CREATE SEQUENCE public.licences_licence_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.licences_licence_id_seq OWNER TO catalogue;

--
-- Name: licences_licence_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: catalogue
--

ALTER SEQUENCE public.licences_licence_id_seq OWNED BY public.licences.licence_id;


--
-- Name: resources; Type: TABLE; Schema: public; Owner: catalogue
--

CREATE TABLE public.resources (
    resource_id integer NOT NULL,
    resource_uid character varying NOT NULL,
    title character varying,
    description json NOT NULL,
    abstract text NOT NULL,
    contact character varying(300)[],
    form character varying,
    constraints character varying,
    keywords character varying(300)[],
    version character varying(300),
    variables json,
    providers json,
    summaries json,
    extent json,
    documentation json,
    type character varying(300) NOT NULL,
    previewimage character varying,
    publication_date date,
    record_update timestamp with time zone,
    "references" json,
    resource_update date,
    use_eqc boolean
);


ALTER TABLE public.resources OWNER TO catalogue;

--
-- Name: resources_licences; Type: TABLE; Schema: public; Owner: catalogue
--

CREATE TABLE public.resources_licences (
    resource_id integer NOT NULL,
    licence_id integer NOT NULL
);


ALTER TABLE public.resources_licences OWNER TO catalogue;

--
-- Name: resources_resource_id_seq; Type: SEQUENCE; Schema: public; Owner: catalogue
--

CREATE SEQUENCE public.resources_resource_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.resources_resource_id_seq OWNER TO catalogue;

--
-- Name: resources_resource_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: catalogue
--

ALTER SEQUENCE public.resources_resource_id_seq OWNED BY public.resources.resource_id;


--
-- Name: licences licence_id; Type: DEFAULT; Schema: public; Owner: catalogue
--

ALTER TABLE ONLY public.licences ALTER COLUMN licence_id SET DEFAULT nextval('public.licences_licence_id_seq'::regclass);


--
-- Name: resources resource_id; Type: DEFAULT; Schema: public; Owner: catalogue
--

ALTER TABLE ONLY public.resources ALTER COLUMN resource_id SET DEFAULT nextval('public.resources_resource_id_seq'::regclass);


--
-- Data for Name: licences; Type: TABLE DATA; Schema: public; Owner: catalogue
--

COPY public.licences (licence_id, licence_uid, revision, title, download_filename) FROM stdin;
1	licence-to-use-copernicus-products	12	Licence to use Copernicus Products	licences/licence-to-use-copernicus-products/licence-to-use-copernicus-products.pdf
\.


--
-- Data for Name: resources; Type: TABLE DATA; Schema: public; Owner: catalogue
--

COPY public.resources (resource_id, resource_uid, title, description, abstract, contact, form, constraints, keywords, version, variables, providers, summaries, extent, documentation, type, previewimage, publication_date, record_update, "references", resource_update, use_eqc) FROM stdin;
1	reanalysis-era5-land-monthly-means	ERA5-Land monthly averaged data from 1950 to present	{"file-format": "GRIB", "data-type": "Gridded", "projection": "Regular latitude-longitude grid", "horizontal-coverage": "Global", "horizontal-resolution": "0.1\\u00b0 x 0.1\\u00b0; Native resolution is 9 km.", "vertical-coverage": "From 2 m above the surface level, to a soil depth of 289 cm.\\n", "vertical-resolution": "4 levels of the ECMWF surface model: Layer 1: 0 -7cm, Layer 2: 7 -28cm, Layer 3: 28-100cm, Layer 4: 100-289cm\\nSome parameters are defined at 2 m over the surface.\\n", "temporal-coverage": "January 1950 to present", "temporal-resolution": "Monthly", "update-frequency": "Monthly with a delay of 2-3 months relatively to the actual date."}	ERA5-Land is a reanalysis dataset providing a consistent view of the evolution of land variables over several decades at an enhanced resolution compared to ERA5. ERA5-Land has been produced by replaying the land component of the ECMWF ERA5 climate reanalysis. Reanalysis combines model data with observations from across the world into a globally complete and consistent dataset using the laws of physics. Reanalysis produces data that goes several decades back in time, providing an accurate description of the climate of the past.\n\nERA5-Land provides a consistent view of the water and energy cycles at surface level during several decades.\nIt contains a detailed record from 1950 onwards, with a temporal resolution of 1 hour. The native spatial resolution of the ERA5-Land reanalysis dataset is 9km on a reduced Gaussian grid (TCo1279). The data in the CDS has been regridded to a regular lat-lon grid of 0.1x0.1 degrees.\n\nThe data presented here is a post-processed subset of the full ERA5-Land dataset. Monthly-mean averages have been pre-calculated to facilitate many applications requiring easy and fast access to the data, when sub-monthly fields are not required.\n\nHourly fields can be found in the [ERA5-Land hourly fields CDS page](https://cds-dev.copernicus-climate.eu/cdsapp#!/dataset/reanalysis-era5-land?tab=overview "ERA5-Land hourly data"). Documentation can be found in the [online ERA5-Land documentation](https://confluence.ecmwf.int/display/CKB/ERA5-Land+data+documentation "ERA5-Land data documentation").\n	\N	resources/reanalysis-era5-land-monthly-means/form.json	resources/reanalysis-era5-land-monthly-means/constraints.json	{"Product type: Reanalysis","Spatial coverage: Global","Temporal coverage: Past","Variable domain: Land (hydrology)","Variable domain: Land (physics)","Variable domain: Land (biosphere)","Provider: Copernicus C3S"}	\N	{"10m u-component of wind": {"description": "Eastward component of the 10m wind. It is the horizontal speed of air moving towards the east, at a height of ten metres above the surface of the Earth, in metres per second. Care should be taken when comparing this variable with observations, because wind observations vary on small space and time scales and are affected by the local terrain, vegetation and buildings that are represented only on average in the ECMWF Integrated Forecasting System. This variable can be combined with the V component of 10m wind to give the speed and direction of the horizontal 10m wind.", "units": "m s^-1"}, "10m v-component of wind": {"description": "Northward component of the 10m wind. It is the horizontal speed of air moving towards the north, at a height of ten metres above the surface of the Earth, in metres per second. Care should be taken when comparing this variable with observations, because wind observations vary on small space and time scales and are affected by the local terrain, vegetation and buildings that are represented only on average in the ECMWF Integrated Forecasting System. This variable can be combined with the U component of 10m wind to give the speed and direction of the horizontal 10m wind.", "units": "m s^-1"}, "2m dewpoint temperature": {"description": "Temperature to which the air, at 2 metres above the surface of the Earth, would have to be cooled for saturation to occur.It is a measure of the humidity of the air. Combined with temperature and pressure, it can be used to calculate the relative humidity. 2m dew point temperature is calculated by interpolating between the lowest model level and the Earth's surface, taking account of the atmospheric conditions. Temperature measured in kelvin can be converted to degrees Celsius (\\u00b0C) by subtracting 273.15.", "units": "K"}, "2m temperature": {"description": "Temperature of air at 2m above the surface of land, sea or in-land waters. 2m temperature is calculated by interpolating between the lowest model level and the Earth's surface, taking account of the atmospheric conditions. Temperature measured in kelvin can be converted to degrees Celsius (\\u00b0C) by subtracting 273.15.", "units": "K"}, "Evaporation from bare soil": {"description": "The amount of evaporation from bare soil at the top of the land surface. This variable is accumulated from the beginning of the forecast time to the end of the forecast step.", "units": "m of water equivalent"}, "Evaporation from open water surfaces excluding oceans": {"description": "Amount of evaporation from surface water storage like lakes and inundated areas but excluding oceans. This variable is accumulated from the beginning of the forecast time to the end of the forecast step.", "units": "m of water equivalent"}, "Evaporation from the top of canopy": {"description": "The amount of evaporation from the canopy interception reservoir at the top of the canopy. This variable is accumulated from the beginning of the forecast time to the end of the forecast step.", "units": "m of water equivalent"}, "Evaporation from vegetation transpiration": {"description": "Amount of evaporation from vegetation transpiration. This has the same meaning as root extraction i.e. the amount of water extracted from the different soil layers. This variable is accumulated from the beginning of the forecast time to the end of the forecast step.", "units": "m of water equivalent"}, "Forecast albedo": {"description": "Is a measure of the reflectivity of the Earth's surface. It is the fraction of solar (shortwave) radiation reflected by Earth's surface, across the solar spectrum, for both direct and diffuse radiation. Values are between 0 and 1. Typically, snow and ice have high reflectivity with albedo values of 0.8 and above, land has intermediate values between about 0.1 and 0.4 and the ocean has low values of 0.1 or less. Radiation from the Sun (solar, or shortwave, radiation) is partly reflected back to space by clouds and particles in the atmosphere (aerosols) and some of it is absorbed. The rest is incident on the Earth's surface, where some of it is reflected. The portion that is reflected by the Earth's surface depends on the albedo. In the ECMWF Integrated Forecasting System (IFS), a climatological background albedo (observed values averaged over a period of several years) is used, modified by the model over water, ice and snow. Albedo is often shown as a percentage (%).", "units": "dimensionless"}, "Lake bottom temperature": {"description": "Temperature of water at the bottom of inland water bodies (lakes, reservoirs, rivers) and coastal waters. ECMWF implemented a lake model in May 2015 to represent the water temperature and lake ice of all the world\\u2019s major inland water bodies in the Integrated Forecasting System. The model keeps lake depth and surface area (or fractional cover) constant in time.", "units": "K"}, "Lake ice depth": {"description": "The thickness of ice on inland water bodies (lakes, reservoirs and rivers) and coastal waters. The ECMWF Integrated Forecasting System (IFS) represents the formation and melting of ice on inland water bodies (lakes, reservoirs and rivers) and coastal water. A single ice layer is represented. This parameter is the thickness of that ice layer.", "units": "m"}, "Lake ice temperature": {"description": "The temperature of the uppermost surface of ice on inland water bodies (lakes, reservoirs, rivers) and coastal waters. The ECMWF Integrated Forecasting System represents the formation and melting of ice on lakes. A single ice layer is represented. The temperature measured in kelvin can be converted to degrees Celsius (\\u00b0C) by subtracting 273.15.", "units": "K"}, "Lake mix-layer depth": {"description": "The thickness of the upper most layer of an inland water body (lake, reservoirs, and rivers) or coastal waters that is well mixed and has a near constant temperature with depth (uniform distribution of temperature). The ECMWF Integrated Forecasting System represents inland water bodies with two layers in the vertical, the mixed layer above and the thermocline below. Thermoclines upper boundary is located at the mixed layer bottom, and the lower boundary at the lake bottom. Mixing within the mixed layer can occur when the density of the surface (and near-surface) water is greater than that of the water below. Mixing can also occur through the action of wind on the surface of the lake.", "units": "m"}, "Lake mix-layer temperature": {"description": "The temperature of the upper most layer of inland water bodies (lakes, reservoirs and rivers) or coastal waters) that is well mixed. The ECMWF Integrated Forecasting System represents inland water bodies with two layers in the vertical, the mixed layer above and the thermocline below. Thermoclines upper boundary is located at the mixed layer bottom, and the lower boundary at the lake bottom. Mixing within the mixed layer can occur when the density of the surface (and near-surface) water is greater than that of the water below. Mixing can also occur through the action of wind on the surface of the lake. Temperature measured in kelvin can be converted to degrees Celsius (\\u00b0C) by subtracting 273.15.", "units": "K"}, "Lake shape factor": {"description": "This parameter describes the way that temperature changes with depth in the thermocline layer of inland water bodies (lakes, reservoirs and rivers) and coastal waters. It is used to calculate the lake bottom temperature and other lake-related parameters. The ECMWF Integrated Forecasting System represents inland and coastal water bodies with two layers in the vertical, the mixed layer above and the thermocline below where temperature changes with depth.", "units": "dimensionless"}, "Lake total layer temperature": {"description": "The mean temperature of total water column in inland water bodies (lakes, reservoirs and rivers) and coastal waters. The ECMWF Integrated Forecasting System represents inland water bodies with two layers in the vertical, the mixed layer above and the thermocline below where temperature changes with depth. This parameter is the mean over the two layers. Temperature measured in kelvin can be converted to degrees Celsius (\\u00b0C) by subtracting 273.15.", "units": "K"}, "Leaf area index, high vegetation": {"description": "One-half of the total green leaf area per unit horizontal ground surface area for high vegetation type.", "units": "m^2 m^-2"}, "Leaf area index, low vegetation": {"description": "One-half of the total green leaf area per unit horizontal ground surface area for low vegetation type.", "units": "m^2 m^-2"}, "Potential evaporation": {"description": "Potential evaporation (pev) in the current ECMWF model is computed, by making a second call to the surface energy balance routine with the vegetation variables set to \\"crops/mixed farming\\" and assuming no stress from soil moisture. In other words, evaporation is computed for agricultural land as if it is well watered and assuming that the atmosphere is not affected by this artificial surface condition. The latter may not always be realistic. Although pev is meant to provide an estimate of irrigation requirements, the method can give unrealistic results in arid conditions due to too strong evaporation forced by dry air. Note that in ERA5-Land pev is computed as an open water evaporation (Pan evaporation) and assuming that the atmosphere is not affected by this artificial surface condition. The latter is different from the way pev is computed in ERA5. This variable is accumulated from the beginning of the forecast time to the end of the forecast step.", "units": "m"}, "Runoff": {"description": "Some water from rainfall, melting snow, or deep in the soil, stays stored in the soil. Otherwise, the water drains away, either over the surface (surface runoff), or under the ground (sub-surface runoff) and the sum of these two is simply called 'runoff'. This variable is the total amount of water accumulated from the beginning of the forecast time to the end of the forecast step. The units of runoff are depth in metres. This is the depth the water would have if it were spread evenly over the grid box. Care should be taken when comparing model variables with observations, because observations are often local to a particular point rather than averaged over a grid square area.  Observations are also often taken in different units, such as mm/day, rather than the accumulated metres produced here. Runoff is a measure of the availability of water in the soil, and can, for example, be used as an indicator of drought or flood. More information about how runoff is calculated is given in the IFS Physical Processes documentation.", "units": "m"}, "Skin reservoir content": {"description": "Amount of water in the vegetation canopy and/or in a thin layer on the soil. It represents the amount of rain intercepted by foliage, and water from dew. The maximum amount of 'skin reservoir content' a grid box can hold depends on the type of vegetation, and may be zero.  Water leaves the 'skin reservoir' by evaporation.", "units": "m of water equivalent"}, "Skin temperature": {"description": "Temperature of the surface of the Earth. The skin temperature is the theoretical temperature that is required to satisfy the surface energy balance. It represents the temperature of the uppermost surface layer, which has no heat capacity and so can respond instantaneously to changes in surface fluxes. Skin temperature is calculated differently over land and sea. Temperature measured in kelvin can be converted to degrees Celsius (\\u00b0C) by subtracting 273.15.", "units": "K"}, "Snow albedo": {"description": "It is defined as the fraction of solar (shortwave) radiation reflected by the snow, across the solar spectrum, for both direct and diffuse radiation. It is a measure of the reflectivity of the snow covered grid cells. Values vary between 0 and 1. Typically, snow and ice have high reflectivity with albedo values of 0.8 and above.", "units": "dimensionless"}, "Snow cover": {"description": "It represents the fraction (0-1) of the cell / grid-box occupied by snow (similar to the cloud cover fields of ERA5).", "units": "%"}, "Snow density": {"description": "Mass of snow per cubic metre in the snow layer. The ECMWF Integrated Forecast System (IFS) model represents snow as a single additional layer over the uppermost soil level. The snow may cover all or part of the grid box.", "units": "kg m^-3"}, "Snow depth": {"description": "Instantaneous grib-box average of the snow thickness on the ground (excluding snow on canopy).", "units": "m"}, "Snow depth water equivalent": {"description": "Depth of snow from the snow-covered area of a grid box. Its units are metres of water equivalent, so it is the depth the water would have if the snow melted and was spread evenly over the whole grid box. The ECMWF Integrated Forecast System represents snow as a single additional layer over the uppermost soil level. The snow may cover all or part of the grid box.", "units": "m of water equivalent"}, "Snow evaporation": {"description": "Evaporation from snow averaged over the grid box (to find flux over snow, divide by snow fraction). This variable is accumulated from the beginning of the forecast time to the end of the forecast step.", "units": "m of water equivalent"}, "Snowfall": {"description": "Accumulated total snow that has fallen to the Earth's surface. It consists of snow due to the large-scale atmospheric flow (horizontal scales greater than around a few hundred metres) and convection where smaller scale areas (around 5km to a few hundred kilometres) of warm air rise. If snow has melted during the period over which this variable was accumulated, then it will be higher than the snow depth. This variable is the total amount of water accumulated from the beginning of the forecast time to the end of the forecast step. The units given measure the depth the water would have if the snow melted and was spread evenly over the grid box. Care should be taken when comparing model variables with observations, because observations are often local to a particular point in space and time, rather than representing averages over a model grid box and model time step.", "units": "m of water equivalent"}, "Snowmelt": {"description": "Melting of snow averaged over the grid box (to find melt over snow, divide by snow fraction). This variable is accumulated from the beginning of the forecast time to the end of the forecast step.", "units": "m of water equivalent"}, "Soil temperature level 1": {"description": "Temperature of the soil in layer 1 (0 - 7 cm) of the ECMWF Integrated Forecasting System. The surface is at 0 cm. Soil temperature is set at the middle of each layer, and heat transfer is calculated at the interfaces between them. It is assumed that there is no heat transfer out of the bottom of the lowest layer. Temperature measured in kelvin can be converted to degrees Celsius (\\u00b0C) by subtracting 273.15.", "units": "K"}, "Soil temperature level 2": {"description": "Temperature of the soil in layer 2 (7 -28cm) of the ECMWF Integrated Forecasting System.", "units": "K"}, "Soil temperature level 3": {"description": "Temperature of the soil in layer 3 (28-100cm) of the ECMWF Integrated Forecasting System.", "units": "K"}, "Soil temperature level 4": {"description": "Temperature of the soil in layer 4 (100-289 cm) of the ECMWF Integrated Forecasting System.", "units": "K"}, "Sub-surface runoff": {"description": "Some water from rainfall, melting snow, or deep in the soil, stays stored in the soil. Otherwise, the water drains away, either over the surface (surface runoff), or under the ground (sub-surface runoff) and the sum of these two is simply called 'runoff'. This variable is accumulated from the beginning of the forecast time to the end of the forecast step. The units of runoff are depth in metres. This is the depth the water would have if it were spread evenly over the grid box. Care should be taken when comparing model variables with observations, because observations are often local to a particular point rather than averaged over a grid square area.  Observations are also often taken in different units, such as mm/day, rather than the accumulated metres produced here. Runoff is a measure of the availability of water in the soil, and can, for example, be used as an indicator of drought or flood. More information about how runoff is calculated is given in the IFS Physical Processes documentation.", "units": "m"}, "Surface latent heat flux": {"description": "Exchange of latent heat with the surface through turbulent diffusion. This variables is accumulated from the beginning of the forecast time to the end of the forecast step. By model convention, downward fluxes are positive.", "units": "J m^-2"}, "Surface net solar radiation": {"description": "Amount of solar radiation (also known as shortwave radiation) reaching the surface of the Earth (both direct and diffuse) minus the amount reflected by the Earth's surface (which is governed by the albedo).Radiation from the Sun (solar, or shortwave, radiation) is partly reflected back to space by clouds and particles in the atmosphere (aerosols) and some of it is absorbed. The rest is incident on the Earth's surface, where some of it is reflected. The difference between downward and reflected solar radiation is the surface net solar radiation. This variable is accumulated from the beginning of the forecast time to the end of the forecast step. The units are joules per square metre (J m^-2). To convert to watts per square metre (W m^-2), the accumulated values should be divided by the accumulation period expressed in seconds. The ECMWF convention for vertical fluxes is positive downwards.", "units": "J m^-2"}, "Surface net thermal radiation": {"description": "Net thermal radiation at the surface. Accumulated field from the beginning of the forecast time to the end of the forecast step. By model convention downward fluxes are positive.", "units": "J m^-2"}, "Surface pressure": {"description": "Pressure (force per unit area) of the atmosphere on the surface of land, sea and in-land water. It is a measure of the weight of all the air in a column vertically above the area of the Earth's surface represented at a fixed point. Surface pressure is often used in combination with temperature to calculate air density. The strong variation of pressure with altitude makes it difficult to see the low and high pressure systems over mountainous areas, so mean sea level pressure, rather than surface pressure, is normally used for this purpose. The units of this variable are Pascals (Pa). Surface pressure is often measured in hPa and sometimes is presented in the old units of millibars, mb (1 hPa = 1 mb = 100 Pa).", "units": "Pa"}, "Surface runoff": {"description": "Some water from rainfall, melting snow, or deep in the soil, stays stored in the soil. Otherwise, the water drains away, either over the surface (surface runoff), or under the ground (sub-surface runoff) and the sum of these two is simply called 'runoff'. This variable is the total amount of water accumulated from the beginning of the forecast time to the end of the forecast step. The units of runoff are depth in metres. This is the depth the water would have if it were spread evenly over the grid box. Care should be taken when comparing model variables with observations, because observations are often local to a particular point rather than averaged over a grid square area. Observations are also often taken in different units, such as mm/day, rather than the accumulated metres produced here. Runoff is a measure of the availability of water in the soil, and can, for example, be used as an indicator of drought or flood. More information about how runoff is calculated is given in the IFS Physical Processes documentation.", "units": "m"}, "Surface sensible heat flux": {"description": "Transfer of heat between the Earth's surface and the atmosphere through the effects of turbulent air motion (but excluding any heat transfer resulting from condensation or evaporation). The magnitude of the sensible heat flux is governed by the difference in temperature between the surface and the overlying atmosphere, wind speed and the surface roughness. For example, cold air overlying a warm surface would produce a sensible heat flux from the land (or ocean) into the atmosphere. This is a single level variable and it is accumulated from the beginning of the forecast time to the end of the forecast step. The units are joules per square metre (J m^-2). To convert to watts per square metre (W m^-2), the accumulated values should be divided by the accumulation period expressed in seconds. The ECMWF convention for vertical fluxes is positive downwards.", "units": "J m^-2"}, "Surface solar radiation downwards": {"description": "Amount of solar radiation (also known as shortwave radiation) reaching the surface of the Earth. This variable comprises both direct and diffuse solar radiation. Radiation from the Sun (solar, or shortwave, radiation) is partly reflected back to space by clouds and particles in the atmosphere (aerosols) and some of it is absorbed.  The rest is incident on the Earth's surface (represented by this variable). To a reasonably good approximation, this variable is the model equivalent of what would be measured by a pyranometer (an instrument used for measuring solar radiation) at the surface. However, care should be taken when comparing model variables with observations, because observations are often local to a particular point in space and time, rather than representing averages over a  model grid box and model time step. This variable is accumulated from the beginning of the forecast time to the end of the forecast step. The units are joules per square metre (J m^-2). To convert to watts per square metre (W m^-2), the accumulated values should be divided by the accumulation period expressed in seconds. The ECMWF convention for vertical fluxes is positive downwards.", "units": "J m-2"}, "Surface thermal radiation downwards": {"description": "Amount of thermal (also known as longwave or terrestrial) radiation emitted by the atmosphere and clouds that reaches the Earth's surface. The surface of the Earth emits thermal radiation, some of which is absorbed by the atmosphere and clouds. The atmosphere and clouds likewise emit thermal radiation in all directions, some of which reaches the surface (represented by this variable). This variable is accumulated from the beginning of the forecast time to the end of the forecast step. The units are joules per square metre (J m^-2). To convert to watts per square metre (W m^-2), the accumulated values should be divided by the accumulation period expressed in seconds. The ECMWF convention for vertical fluxes is positive downwards.", "units": "J m-2"}, "Temperature of snow layer": {"description": "This variable gives the temperature of the snow layer from the ground to the snow-air interface. The ECMWF Integrated Forecast System (IFS) model represents snow as a single additional layer over the uppermost soil level. The snow may cover all or part of the  grid box. Temperature measured in kelvin can be converted to degrees Celsius (\\u00b0C) by subtracting 273.15.", "units": "K"}, "Total evaporation": {"description": "Accumulated amount of water that has evaporated from the Earth's surface, including a simplified representation of transpiration (from vegetation), into vapour in the air above. This variable is accumulated from the beginning of the forecast to the end of the forecast step. The ECMWF Integrated Forecasting System convention is that downward fluxes are positive. Therefore, negative values indicate evaporation and positive values indicate condensation.", "units": "m of water equivalent"}, "Total precipitation": {"description": "Accumulated liquid and frozen water, including rain and snow, that falls to the Earth's surface. It is the sum of large-scale precipitation (that precipitation which is generated by large-scale weather patterns, such as troughs and cold fronts) and convective precipitation (generated by convection which occurs when air at lower levels in the atmosphere is warmer and less dense than the air above, so it rises). Precipitation variables do not include fog, dew or the precipitation that evaporates in the atmosphere before it lands at the surface of the Earth. This variable is accumulated from the beginning of the forecast time to the end of the forecast step. The units of precipitation are depth in metres. It is the depth the water would have if it were spread evenly over the grid box. Care should be taken when comparing model variables with observations, because observations are often local to a particular point in space and time, rather than representing averages over a model grid box and  model time step.", "units": "m"}, "Volumetric soil water layer 1": {"description": "Volume of water in soil layer 1 (0 - 7 cm) of the ECMWF Integrated Forecasting System. The surface is at 0 cm. The volumetric soil water is associated with the soil texture (or classification), soil depth, and the underlying groundwater level.", "units": "m^3 m^-3"}, "Volumetric soil water layer 2": {"description": "Volume of water in soil layer 2 (7 -28 cm) of the ECMWF Integrated Forecasting System.", "units": "m^3 m^-3"}, "Volumetric soil water layer 3": {"description": "Volume of water in soil layer 3 (28-100 cm) of the ECMWF Integrated Forecasting System.", "units": "m^3 m^-3"}, "Volumetric soil water layer 4": {"description": "Volume of water in soil layer 4 (100-289 cm) of the ECMWF Integrated Forecasting System.", "units": "m^3 m^-3"}}	\N	\N	\N	[{"url": "https://confluence.ecmwf.int/display/CKB/ERA5-Land%3A+data+documentation", "title": "ERA5-Land online documentation", "description": "Further and more detailed information relating to the ERA5-Land dataset can be found in the Copernicus Knowledge Base web link above."}]	dataset	resources/reanalysis-era5-land-monthly-means/overview.png	2019-06-23	2022-07-07 12:17:27.548324+02	[{"title": "Citation", "content": "resources/reanalysis-era5-land-monthly-means/citation.html", "copy": true, "url": null, "download_file": null}]	2022-03-02	t
2	reanalysis-era5-pressure-levels	ERA5 hourly data on pressure levels from 1959 to present	{"file-format": "GRIB", "data-type": "Gridded", "projection": "Regular latitude-longitude grid.", "horizontal-coverage": "Global", "horizontal-resolution": "\\nReanalysis: 0.25\\u00b0 x 0.25\\u00b0\\n\\nMean, spread and members: 0.5\\u00b0 x 0.5\\u00b0", "temporal-coverage": "1959 to present", "temporal-resolution": "Hourly", "vertical-resolution": "37 pressure levels", "vertical-coverage": "1000 hPa to 1 hPa"}	**ERA5** is the fifth generation ECMWF reanalysis for the global climate and weather for the past 4 to 7 decades.\nCurrently data is available from 1950, with Climate Data Store entries for 1950-1978 (preliminary back extension) and from 1959 onwards (final release plus timely updates, this page).\nERA5 replaces the ERA-Interim reanalysis.\n\nReanalysis combines model data with observations from across the world into a globally complete and consistent dataset using the laws of physics. This principle, called data assimilation, is based on the method used by numerical weather prediction centres, where every so many hours (12 hours at ECMWF) a previous forecast is combined with newly available observations in an optimal way to produce a new best estimate of the state of the atmosphere, called analysis, from which an updated, improved forecast is issued. Reanalysis works in the same way, but at reduced resolution to allow for the provision of a dataset spanning back several decades. Reanalysis does not have the constraint of issuing timely forecasts, so there is more time to collect observations, and when going further back in time, to allow for the ingestion of improved versions of the original observations, which all benefit the quality of the reanalysis product.\n\nERA5 provides hourly estimates for a large number of atmospheric, ocean-wave and land-surface quantities.\nAn uncertainty estimate is sampled by an underlying 10-member ensemble\nat three-hourly intervals. Ensemble mean and spread have been pre-computed for convenience.\nSuch uncertainty estimates are closely related to the information content of the available observing system which\nhas evolved considerably over time. They also indicate flow-dependent sensitive areas.\nTo facilitate many climate applications, monthly-mean averages have been pre-calculated too,\nthough monthly means are not available for the ensemble mean and spread.\n\nERA5 is updated daily with a latency of about 5 days. In case that serious flaws are detected in this early release (called ERA5T), this data could be different from the final release 2 to 3 months later. In case that this occurs users are notified.\n\nThe data set presented here is a regridded subset of the full ERA5 data set on native resolution.\nIt is online on spinning disk, which should ensure fast and easy access.\nIt should satisfy the requirements for most common applications.\n\nAn overview of all ERA5 datasets can be found in [this article](https://confluence.ecmwf.int/display/CKB/The+family+of+ERA5+datasets "The family of ERA5 datasets").\nInformation on access to ERA5 data on native resolution is provided in [these guidelines](https://confluence.ecmwf.int/display/CKB/How+to+download+ERA5 "How to download ERA5").\n\nData has been regridded to a regular lat-lon grid of 0.25 degrees for the reanalysis and 0.5 degrees for\nthe uncertainty estimate (0.5 and 1 degree respectively for ocean waves).\nThere are four main sub sets: hourly and monthly products, both on pressure levels (upper air fields) and single levels (atmospheric, ocean-wave and land surface quantities).\n\nThe present entry is "ERA5 hourly data on pressure levels from 1959 to present".\n	\N	resources/reanalysis-era5-pressure-levels/form.json	resources/reanalysis-era5-pressure-levels/constraints.json	{"Variable domain: Atmosphere (surface)","Variable domain: Atmosphere (upper air)","Temporal coverage: Past","Spatial coverage: Global","Product type: Reanalysis","Provider: Copernicus C3S"}	\N	{"Divergence": {"description": "This parameter is the horizontal divergence of velocity. It is the rate at which  air is spreading out horizontally from a point, per square metre. This parameter  is positive for air that is spreading out, or diverging, and negative for the  opposite, for air that is concentrating, or converging (convergence).", "units": "s^-1"}, "Fraction of cloud cover": {"description": "This parameter is the proportion of a grid box covered by cloud (liquid or ice)  and varies between zero and one. This parameter is available on multiple levels through the atmosphere.", "units": "Dimensionless"}, "Geopotential": {"description": "This parameter is the gravitational potential energy of a unit mass, at a  particular location, relative to mean sea level. It is also the amount of work  that would have to be done, against the force of gravity, to lift a unit mass to  that location from mean sea level.\\nThe geopotential height can be calculated by dividing the geopotential by the  Earth's gravitational acceleration, g (=9.80665 m s-2). The geopotential height  plays an important role in synoptic meteorology (analysis of weather patterns).  Charts of geopotential height plotted at constant pressure levels (e.g., 300,  500 or 850 hPa) can be used to identify weather systems such as cyclones,  anticyclones, troughs and ridges.\\nAt the surface of the Earth, this parameter shows the variations in geopotential  (height) of the surface, and is often referred to as the orography.", "units": "m^2 s^-2"}, "Ozone mass mixing ratio": {"description": "This parameter is the mass of ozone per kilogram of air.\\nIn the ECMWF Integrated Forecasting System (IFS), there is a simplified  representation of ozone chemistry (including representation of the chemistry  which has caused the ozone hole). Ozone is also transported around in the  atmosphere through the motion of air.\\nNaturally occurring ozone in the stratosphere helps protect organisms at the  surface of the Earth from the harmful effects of ultraviolet (UV) radiation from  the Sun. Ozone near the surface, often produced because of pollution, is harmful  to organisms.\\nMost of the IFS chemical species are archived as mass mixing ratios [kg kg-1].", "units": "kg kg^-1"}, "Potential vorticity": {"description": "Potential vorticity is a measure of the capacity for air to rotate in the  atmosphere. If we ignore the effects of heating and friction, potential vorticity  is conserved following an air parcel. It is used to look for places where large  wind storms are likely to originate and develop. Potential vorticity increases  strongly above the tropopause and therefore, it can also be used in studies related  to the stratosphere and stratosphere-troposphere exchanges.\\nLarge wind storms develop when a column of air in the atmosphere starts to rotate.  Potential vorticity is calculated from the wind, temperature and pressure across a  column of air in the atmosphere. ", "units": "K m^2 kg^-1 s^-1"}, "Relative humidity": {"description": "This parameter is the water vapour pressure as a percentage of the value at which  the air becomes saturated (the point at which water vapour begins to condense into  liquid water or deposition into ice).\\nFor temperatures over 0\\u00b0C (273.15 K) it is calculated for saturation over water. At  temperatures below -23\\u00b0C it is calculated for saturation over ice. Between -23\\u00b0C  and 0\\u00b0C this parameter is calculated by interpolating between the ice and water  values using a quadratic function. ", "units": "%"}, "Specific cloud ice water content": {"description": "This parameter is the mass of cloud ice particles per kilogram of the total mass of  moist air. The 'total mass of moist air' is the sum of the dry air, water vapour,  cloud liquid, cloud ice, rain and falling snow. This parameter represents the  average value for a grid box.\\nWater within clouds can be liquid or ice, or a combination of the two. Note that  'cloud frozen water' is the same as 'cloud ice water'.", "units": "kg kg^-1"}, "Specific cloud liquid water content": {"description": "This parameter is the mass of cloud liquid water droplets per kilogram of the total  mass of moist air. The 'total mass of moist air' is the sum of the dry air, water  vapour, cloud liquid, cloud ice, rain and falling snow. This parameter represents  the average value for a grid box.\\nWater within clouds can be liquid or ice, or a combination of the two. ", "units": "kg kg^-1"}, "Specific humidity": {"description": "This parameter is the mass of water vapour per kilogram of moist air.\\nThe total mass of moist air is the sum of the dry air, water vapour, cloud liquid,  cloud ice, rain and falling snow.", "units": "kg kg^-1"}, "Specific rain water content": {"description": "The mass of water produced from large-scale clouds that is of raindrop size and so  can fall to the surface as precipitation.\\nLarge-scale clouds are generated by the cloud scheme in the ECMWF Integrated  Forecasting System (IFS). The cloud scheme represents the formation and dissipation  of clouds and large-scale precipitation due to changes in atmospheric quantities  (such as pressure, temperature and moisture) predicted directly by the IFS at spatial  scales of a grid box or larger.\\nThe quantity is expressed in kilograms per kilogram of the total mass of moist air.  The 'total mass of moist air' is the sum of the dry air, water vapour, cloud liquid,  cloud ice, rain and falling snow. This parameter represents the average value for a  grid box.\\nClouds contain a continuum of different sized water droplets and ice particles. The  IFS cloud scheme simplifies this to represent a number of discrete cloud  droplets/particles including cloud water droplets, raindrops, ice crystals and snow  (aggregated ice crystals). The processes of droplet formation, phase transition and  aggregation are also highly simplified in the IFS.", "units": "kg kg^-1"}, "Specific snow water content": {"description": "The mass of snow (aggregated ice crystals) produced from large-scale clouds that can  fall to the surface as precipitation.\\nLarge-scale clouds are generated by the cloud scheme in the ECMWF Integrated  Forecasting System (IFS). The cloud scheme represents the formation and dissipation  of clouds and large-scale precipitation due to changes in atmospheric quantities (such  as pressure, temperature and moisture) predicted directly by the IFS at spatial scales  of a grid box or larger.\\nThe mass is expressed in kilograms per kilogram of the total mass of moist air. The  'total mass of moist air' is the sum of the dry air, water vapour, cloud liquid, cloud  ice, rain and falling snow. This parameter represents the average value for a grid box.\\nClouds contain a continuum of different sized water droplets and ice particles. The IFS  cloud scheme simplifies this to represent a number of discrete cloud droplets/particles  including cloud water droplets, raindrops, ice crystals and snow (aggregated ice  crystals). The processes of droplet formation, phase transition and aggregation are also  highly simplified in the IFS.", "units": "kg kg^-1"}, "Temperature": {"description": "This parameter is the temperature in the atmosphere.\\nIt has units of kelvin (K). Temperature measured in kelvin can be converted to degrees  Celsius (\\u00b0C) by subtracting 273.15.\\nThis parameter is available on multiple levels through the atmosphere.", "units": "K"}, "U-component of wind": {"description": "This parameter is the eastward component of the wind. It is the horizontal speed of air  moving towards the east. A negative sign indicates air moving towards the west.\\nThis parameter can be combined with the V component of wind to give the speed and  direction of the horizontal wind.", "units": "m s^-1"}, "V-component of wind": {"description": "This parameter is the northward component of the wind. It is the horizontal speed of air  moving towards the north. A negative sign indicates air moving towards the south.\\nThis parameter can be combined with the U component of wind to give the speed and  direction of the horizontal wind.", "units": "m s^-1"}, "Vertical velocity": {"description": "This parameter is the speed of air motion in the upward or downward direction. The ECMWF  Integrated Forecasting System (IFS) uses a pressure based vertical co-ordinate system and  pressure decreases with height, therefore negative values of vertical velocity indicate  upward motion.\\nVertical velocity can be useful to understand the large-scale dynamics of the atmosphere,  including areas of upward motion/ascent (negative values) and downward motion/subsidence  (positive values).", "units": "Pa s^-1"}, "Vorticity (relative)": {"description": "This parameter is a measure of the rotation of air in the horizontal, around a vertical  axis, relative to a fixed point on the surface of the Earth.\\nOn the scale of weather systems, troughs (weather features that can include rain) are  associated with anticlockwise rotation (in the northern hemisphere), and ridges (weather  features that bring light or still winds) are associated with clockwise rotation.\\nAdding the effect of rotation of the Earth, the Coriolis parameter, to the relative  vorticity produces the absolute vorticity.", "units": "s^-1"}}	\N	\N	\N	[{"url": "https://confluence.ecmwf.int/display/CKB/ERA5%3A+data+documentation", "title": "ERA5 data documentation", "description": "Detailed information relating to the ERA5 data archive can be found in the web link above."}, {"url": "https://rmets.onlinelibrary.wiley.com/doi/10.1002/qj.4174", "title": "The ERA5 global reanalysis: Preliminary extension to 1950", "description": "Journal article describing the ERA5 preliminary extension.", "kind": ""}, {"url": "https://rmets.onlinelibrary.wiley.com/doi/10.1002/qj.3803", "title": "The ERA5 global reanalysis", "description": "Journal article describing ERA5.", "kind": ""}]	dataset	resources/reanalysis-era5-pressure-levels/overview.jpg	\N	2022-07-07 12:17:27.566208+02	[{"title": "Citation", "content": "resources/reanalysis-era5-pressure-levels/citation.html", "copy": true, "url": null, "download_file": null}, {"title": "Acknowledgement", "content": "resources/reanalysis-era5-pressure-levels/acknowledgement.html", "copy": null, "url": null, "download_file": null}]	2022-06-09	t
\.


--
-- Data for Name: resources_licences; Type: TABLE DATA; Schema: public; Owner: catalogue
--

COPY public.resources_licences (resource_id, licence_id) FROM stdin;
1	1
2	1
\.


--
-- Name: licences_licence_id_seq; Type: SEQUENCE SET; Schema: public; Owner: catalogue
--

SELECT pg_catalog.setval('public.licences_licence_id_seq', 1, true);


--
-- Name: resources_resource_id_seq; Type: SEQUENCE SET; Schema: public; Owner: catalogue
--

SELECT pg_catalog.setval('public.resources_resource_id_seq', 2, true);


--
-- Name: licences licence_uid_revision_uc; Type: CONSTRAINT; Schema: public; Owner: catalogue
--

ALTER TABLE ONLY public.licences
    ADD CONSTRAINT licence_uid_revision_uc UNIQUE (licence_uid, revision);


--
-- Name: licences licences_pkey; Type: CONSTRAINT; Schema: public; Owner: catalogue
--

ALTER TABLE ONLY public.licences
    ADD CONSTRAINT licences_pkey PRIMARY KEY (licence_id);


--
-- Name: resources_licences resources_licences_pkey; Type: CONSTRAINT; Schema: public; Owner: catalogue
--

ALTER TABLE ONLY public.resources_licences
    ADD CONSTRAINT resources_licences_pkey PRIMARY KEY (resource_id, licence_id);


--
-- Name: resources resources_pkey; Type: CONSTRAINT; Schema: public; Owner: catalogue
--

ALTER TABLE ONLY public.resources
    ADD CONSTRAINT resources_pkey PRIMARY KEY (resource_id);


--
-- Name: ix_licences_licence_uid; Type: INDEX; Schema: public; Owner: catalogue
--

CREATE INDEX ix_licences_licence_uid ON public.licences USING btree (licence_uid);


--
-- Name: ix_licences_revision; Type: INDEX; Schema: public; Owner: catalogue
--

CREATE INDEX ix_licences_revision ON public.licences USING btree (revision);


--
-- Name: ix_resources_resource_uid; Type: INDEX; Schema: public; Owner: catalogue
--

CREATE UNIQUE INDEX ix_resources_resource_uid ON public.resources USING btree (resource_uid);


--
-- Name: resources_licences resources_licences_licence_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: catalogue
--

ALTER TABLE ONLY public.resources_licences
    ADD CONSTRAINT resources_licences_licence_id_fkey FOREIGN KEY (licence_id) REFERENCES public.licences(licence_id);


--
-- Name: resources_licences resources_licences_resource_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: catalogue
--

ALTER TABLE ONLY public.resources_licences
    ADD CONSTRAINT resources_licences_resource_id_fkey FOREIGN KEY (resource_id) REFERENCES public.resources(resource_id);


--
-- PostgreSQL database dump complete
--

