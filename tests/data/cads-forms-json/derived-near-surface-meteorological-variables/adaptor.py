import cacholote
from cads_adaptors import mapping, url_tools


@cacholote.cacheable
def url_adaptor(request, config, metadata):

    data_format = request.pop("format", "zip")

    if data_format not in {"zip", "tgz"}:
        raise ValueError(f"{data_format=} is not supported")

    mapping_config = config.pop("mapping", {})
    mapped_request = mapping.apply_mapping(request, mapping_config)

    requests_urls = url_tools.requests_to_urls(
        mapped_request, patterns=config["patterns"]
    )

    path = url_tools.download_from_urls(
        [ru["url"] for ru in requests_urls], data_format=data_format
    )
    return open(path, "rb")
