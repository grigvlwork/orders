import xml.etree.ElementTree as ET

import datetime
import requests

from . import endpoints  # URLS and perameters to access data


class Currency:
    def __init__(self, isoCurrencyCode):
        self.code = isoCurrencyCode.upper()
        try:
            code = APICurrencyCodeValidatorAndFetcher(self.code).fetch_api_code()
            self.fetcher = ExchangeRateFetcher(code)
        except Exception:
            raise ValueError("Provided currency code is unknown to CBR API. Can not proceed.")
            
    def rate_at_date(self, date: str):
        return self.fetcher.fetch_rate_for_date(date)
    
    def rate_at_date_range(self, start_date: str, end_date: str):
        return self.fetcher.fetch_rate_for_range_of_dates(start_date, end_date)


class APICurrencyCodeValidatorAndFetcher:
    def __init__(self, isoCurrencyCode: str):
        self.iso_currency_code = isoCurrencyCode.upper()
        
    def fetch_api_code(self) -> str:
        response = requests.get(endpoints.API_URL_CURRENCY_CODES)
        if response.status_code != requests.codes.ok:
            raise Exception("Could not connect to cbr.ru and fetch data.")
        xml_currency_codes = ET.fromstring(response.text)
        for code in xml_currency_codes:
            if code.find(endpoints.API_XML_ELEMENT_TAG_ISO_CURRENCY_CODE).text == self.iso_currency_code:
                return code.attrib["ID"]
        raise ValueError("Provided currency code is invalid or not supported by CBR API")
  

class ExchangeRateFetcher:
    '''
    ExchangeRateFetcher must be initialized with correct CBR API currency 
    code to work properly.
    '''
    def __init__(self, api_currency_code: str):
        self.api_currency_code = api_currency_code
        
    def fetch_rate_for_date(self, date) -> float:
        '''
        Accepts date in form "dd/mm/yyyy" and returns exchange rate (RUB/currency)
        at the specified date
        '''
        params = {endpoints.API_REQUEST_SINGLE_DATE: ApiDatesConverter(date).to_string(),
                  endpoints.API_REQUEST_CURRENCY_CODE: self.api_currency_code}
        xml_body = self.execute_request_and_return_xml(endpoints.API_URL_FOR_DATE, params)
        for item in xml_body:
            '''
            CBR API does not honor currency code in request (although it is 
            described in the docs) and returns all currencies rates at requested 
            date. Thus we need to go through returned
            xml elements one by one to find the needed element...
            '''
            if item.attrib["ID"] == self.api_currency_code:
                return float(item.find("Value").text.replace(",", "."))

    def fetch_rate_for_range_of_dates(self, start_date: str, end_date: str) -> dict:
        '''
        Accepts two dates in form "dd/mm/yyyy" and returns dictionary
        {datetime.datetime: float} of exchange rates (RUB/currency) at
        relevant dates. The specified dates are both included
        in the output.
        '''
        params = {endpoints.API_REQUEST_DATE_RANGE_BEGIN: ApiDatesConverter(start_date).to_string(),
                  endpoints.API_REQUEST_DATE_RANGE_END: ApiDatesConverter(end_date).to_string(),
                  endpoints.API_REQUEST_CURRENCY_CODE: self.api_currency_code}
        xml_body = self.execute_request_and_return_xml(endpoints.API_URL_FOR_DATE_RANGE, params)
        dates = [self.api_response_to_datetime(item.attrib["Date"]) for item in xml_body]
        values = [float(item.find("Value").text.replace(",", ".")) for item in xml_body]
        return dict(zip(dates, values))
    
    def api_response_to_datetime(self, datestr: str) -> datetime.datetime:
        '''
        CBR API acceps date as dd/mm/yyy but returns dd.mm.yyyy
        '''
        d, m, y = (int(n) for n in datestr.split("."))
        return datetime.datetime(y, m, d)
    
    def execute_request_and_return_xml(self, url: str, params: dict):
        response = requests.get(url, params)
        if response.status_code != requests.codes.ok:
            raise Exception("Could not connect to cbr.ru and fetch data.")
        return ET.fromstring(response.text)


class ApiDatesConverter:
    def __init__(self, date):
        if isinstance(date, str):
            self.datestr = date
            self.str_to_datetime()
            self.datetime_to_str() 
        elif isinstance(date, datetime.datetime):
            self.datetime = date
            self.datetime_to_str()
        else:
            raise ValueError("argument 'date' must be either string or datetime.datetime object")

    def to_string(self):
        return self.datestr
    
    def to_datetime(self):
        return self.datetime
   
    def datetime_to_str(self):
        self.datestr = self.datetime.strftime("%d/%m/%Y")
                
    def str_to_datetime(self):
        try:
            if self.datestr.find(".") != -1:
                self.datestr = self.datestr.replace(".", "/")
            date = datetime.datetime.strptime(self.datestr, "%d/%m/%Y")
        except ValueError:
            raise ValueError("Can only accept date as string in form '%d/%m/%Y' or '%d.%m.%Y', e.g. '01/09/2020'")
        self.datetime = date


__all__ = [Currency]
