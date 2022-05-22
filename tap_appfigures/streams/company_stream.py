import singer
from .base_stream import BaseStream
from tap_appfigures.context import Context
from tap_appfigures.exceptions import AppfiguresNotFoundError

LOGGER = singer.get_logger()

class CompanyStream(BaseStream):
    stream_id = 'companies'
    stream_name = 'companies'
    key_properties = ["developer_id"]
    replication_key = "developer_id"
    count = 0

    def sync_records(self, **kwargs):
        application_stream = Context.stream_objects['applications'](self.client)
        company_ids = application_stream.get_company_ids()

        for company_id in company_ids:
            time_extracted = singer.utils.now()
            url = self.client.get_company_url(company_id)
            try:
                record = self.client.get_request(url)
            except AppfiguresNotFoundError as e:
                LOGGER.info(e)
            
            additional_info = dict(record).get("additional_info", {})
            name = dict(record).get("name", None)
            company_info = additional_info.get("company", {})
            company_metrics = company_info.get("metrics", {})
            location = company_info.get("geo", {})
            category = company_info.get("category", {})
            linkedin = company_info.get("linkedin", {})
            twitter = company_info.get("twitter", {})
            facebook = company_info.get("facebook", {})
            
            record = {
                "developer_id": company_id,
                "name": name if name else company_info.get("name", None),
                "legal_name": company_info.get("legal_name", None),
                "domain": company_info.get("domain", None),
                "domain_aliases": company_info.get("domain_aliases", None),
                "street_number": location.get("street_number", None),
                "street_name": location.get("street_name", None),
                "city": location.get("city", None),
                "state": location.get("state_code", None),
                "country": location.get("country_code", None),
                "zipcode": location.get("postal_code", None),
                "employee_count": company_metrics.get("employees", None),
                "employee_count_range": company_metrics.get("employees_range", None),
                "annual_revenue": company_metrics.get("annual_revenue", None),
                "estimated_annual_revenue": company_metrics.get("estimated_annual_revenue", None),
                "industry": category.get("industry", None),
                "industry_group": company_metrics.get("industry_group", None),
                "description": company_info.get("description", None),
                "linkedin_handle": linkedin.get("handle", None),
                "twitter_handle": twitter.get("handle", None),
                "twitter_id": twitter.get("id", None),
                "facebook_handle": facebook.get("handle", None),
                "timezone": company_info.get("timezone", None)
                
            }
  
            self.write_record(record, time_extracted=time_extracted)
            Context.set_bookmark(self.stream_id, self.replication_key, company_id)
            CompanyStream.count += 1
        
        LOGGER.info(f"{CompanyStream.count} companies found using Apollo client.")
