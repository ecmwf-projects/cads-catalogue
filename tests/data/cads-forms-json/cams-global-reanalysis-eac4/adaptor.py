import cacholote
import cdsapi


@cacholote.cacheable
def adaptor(request, config, metadata):

    # parse input options
    collection_id = config.pop("collection_id", None)
    if not collection_id:
        raise ValueError(f"collection_id is required in request")

    # retrieve data
    client = cdsapi.Client(config["url"], config["key"])
    result_path = client.retrieve(collection_id, request).download()
    return open(result_path, "rb")
