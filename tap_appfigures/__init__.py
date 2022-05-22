import os
import json
import singer
from singer import utils
from tap_appfigures.client import AppfiguresClient
from tap_appfigures.discover import discover
from tap_appfigures.sync import sync
from tap_appfigures.context import Context

REQUIRED_CONFIG_KEYS = ["cookie"]

LOGGER = singer.get_logger()

@utils.handle_top_exception(LOGGER)
def main():
    # Parse command line arguments
    args = utils.parse_args(REQUIRED_CONFIG_KEYS)

    Context.state = args.state
    
    with AppfiguresClient(args.config) as client:
        # If discover flag was passed, run discovery mode and dump output to stdout
        if args.discover:
            catalog = discover(client, args.config)
            catalog.dump()
        # Otherwise run in sync mode
        else:
            if args.catalog:
                catalog = args.catalog
            else:
                catalog = discover(client, args.config)
              
            sync(client, args.config)

if __name__ == "__main__":
    main()