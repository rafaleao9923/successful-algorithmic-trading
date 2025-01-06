import scrapy


class SymbolItem(scrapy.Item):
    id = scrapy.Field()
    exchange_id = scrapy.Field()
    ticker = scrapy.Field()
    instrument = scrapy.Field()
    name = scrapy.Field()
    sector = scrapy.Field()
    sub_industry = scrapy.Field()
    headquarter = scrapy.Field()
    date_added = scrapy.Field()
    cik = scrapy.Field()
    founded = scrapy.Field()
    currency = scrapy.Field()
    created_date = scrapy.Field()
    last_updated_date = scrapy.Field()


class PriceItem(scrapy.Item):
    id = scrapy.Field()
    data_vendor_id = scrapy.Field()
    symbol_id = scrapy.Field()
    price_date = scrapy.Field()
    created_date = scrapy.Field()
    last_updated_date = scrapy.Field()
    open_price = scrapy.Field()
    high_price = scrapy.Field()
    low_price = scrapy.Field()
    close_price = scrapy.Field()
    adj_close_price = scrapy.Field()
    volume = scrapy.Field()


class ExchangeItem(scrapy.Item):
    id = scrapy.Field()
    abbrev = scrapy.Field()
    name = scrapy.Field()
    city = scrapy.Field()
    country = scrapy.Field()
    currency = scrapy.Field()
    timezone_offset = scrapy.Field()
    created_date = scrapy.Field()
    last_updated_date = scrapy.Field()


class DataVendorItem(scrapy.Item):
    id = scrapy.Field()
    name = scrapy.Field()
    website_url = scrapy.Field()
    support_email = scrapy.Field()
    created_date = scrapy.Field()
    last_updated_date = scrapy.Field()
