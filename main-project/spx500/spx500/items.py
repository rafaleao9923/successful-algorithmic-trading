from scrapy.item import Item, Field
from datetime import datetime

class SymbolItem(Item):
    exchange_id = Field()
    ticker = Field()
    instrument = Field()
    name = Field()
    sector = Field()
    sub_industry = Field()
    headquarter = Field()
    date_added = Field()
    cik = Field()
    founded = Field()
    currency = Field()
    created_date = Field()
    last_updated_date = Field()

class PriceItem(Item):
    data_vendor_id = Field()
    symbol_id = Field()
    price_date = Field()
    created_date = Field()
    last_updated_date = Field()
    open_price = Field()
    high_price = Field()
    low_price = Field()
    close_price = Field()
    adj_close_price = Field()
    volume = Field()

    def set_defaults(self):
        now = datetime.now().isoformat()
        self.setdefault('created_date', now)
        self.setdefault('last_updated_date', now)
        self.setdefault('data_vendor_id', 1)  # Yahoo Finance vendor ID