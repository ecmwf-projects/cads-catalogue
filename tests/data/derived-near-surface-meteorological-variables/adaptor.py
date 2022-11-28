import cacholote
from cads_retrieve_tools import mapping, url_tools


@cacholote.cacheable
def url_adaptor(request, config, metadata):

    mapping_config = config.pop("mapping", {})
    mapped_request = mapping.apply_mapping(request, mapping_config)

    requests_urls = url_tools.requests_to_urls(mapped_request, patterns=config["patterns"])

    path = url_tools.download_from_urls([ru["url"] for ru in requests_urls])
    return open(path, "rb")
