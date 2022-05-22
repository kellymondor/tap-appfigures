import singer
from singer.catalog import Catalog, CatalogEntry

from tap_appfigures.streams.company_stream import CompanyStream
from tap_appfigures.streams.application_stream import ApplicationStream

LOGGER = singer.get_logger()
AVAILABLE_STREAMS = [CompanyStream, ApplicationStream]

def discover(client, config):

    LOGGER.info("Starting discovery...")

    streams = []

    for s in AVAILABLE_STREAMS:
        stream = s(client)
        streams.append(
            CatalogEntry(
                metadata = [{"metadata":{"selected": config.get("selected_by_default")}, "breadcrumb": []}], 
                tap_stream_id = stream.stream_id, 
                stream = stream.stream_name,
                schema = stream.schema, 
                key_properties = stream.key_properties,
                replication_key = stream.replication_key))

    LOGGER.info("Finished discovery.")

    return Catalog(streams)