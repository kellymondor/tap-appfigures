import singer
import itertools

from tap_appfigures.streams.application_stream import ApplicationStream
from tap_appfigures.streams.company_stream import CompanyStream
from tap_appfigures.client import AppfiguresClient
from tap_appfigures.context import Context

LOGGER = singer.get_logger()

def sync(client, config):

    currently_syncing_stream = Context.state.get('currently_syncing_stream')
    currently_syncing_query = Context.state.get('currently_syncing_query')
    
    LOGGER.info(f"Starting sync...")

    application_stream = ApplicationStream(client)
    application_stream.sync()

    company_stream = CompanyStream(client)
    company_stream.sync()



    



    
