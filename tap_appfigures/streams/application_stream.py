import singer
from .base_stream import BaseStream
from tap_appfigures.context import Context

LOGGER = singer.get_logger()

PAGE_SIZE = 500

class ApplicationStream(BaseStream):
    stream_id = 'applications'
    stream_name = 'applications'
    key_properties = ["product_id"]
    replication_key = "updated_at"
    company_ids = set()

    def get_company_ids(self):

        if ApplicationStream.company_ids:
            for company_id in sorted(ApplicationStream.company_ids):
                yield company_id
        else:
            pass
    
    def sync_page(self, url, page_size, page_number):

        max_updated_at = None
    
        params = {"sort": "updated_date", "count": page_size, "page": page_number, "fields": "product_id,storefronts,type,stores_id,developer,developer_id,name,other_storefronts,us_price,all_rating,all_rating_count,active,categories.all,developer_email,countries,version_rating,version_rating_count,primary_description,developer_country,developer_site,devices,is_paid,categories.main,monetization_strategies,release_date,sdks,view_url,support_url,updated_date,version"}
        time_extracted = singer.utils.now()
        
        response = self.client.post_request(url, params = params)
        records = response.get('results', None)
        
        for idx, record in enumerate(records):

            max_updated_at = max(max_updated_at, record.get("updated_date", None))
            
            self.write_record(record, time_extracted)
            
            if record.get("developer_id", None):
                ApplicationStream.company_ids.add(int(record["developer_id"]))

        
        next_page = None

        if len(records) == page_size: 
            next_page = page_number + 1
        
        
        Context.set_bookmark(self.stream_id, self.replication_key, max_updated_at)
        self.write_state()

        return next_page

    def sync_records(self, **kwargs):

        url = self.client.get_application_search_url()
        next_page = self.sync_page(url, PAGE_SIZE, 1)

        while next_page:
            next_page = self.sync_page(url, PAGE_SIZE, next_page)

Context.stream_objects['applications'] = ApplicationStream