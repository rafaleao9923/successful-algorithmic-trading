from scrapy import Request, Spider
from spx500.items import PriceItem
import json
from datetime import datetime

class PriceSpider(Spider):
    name = 'spx500_prices'
    start_urls = [
        'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies',
    ]

    def parse(self, response):
        symbols_list = response.css('table.wikitable tr')[1:]

        for symbol in symbols_list:
            symbol_name = symbol.css('td a::text').get()
            yield Request(url=f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol_name}', 
                          callback=self.parse_price_data, 
                          meta={'symbol': symbol_name})

    def parse_price_data(self, response):
        symbol = response.meta['symbol']
        data = json.loads(response.text)
        result = data['chart']['result'][0]
        quote = result['indicators']['quote'][0]
        timestamps = result['timestamp']
        opens = quote['open']
        highs = quote['high']
        lows = quote['low']
        closes = quote['close']
        volumes = quote['volume']
        adj_closes = result['indicators']['adjclose'][0]['adjclose']

        for i in range(len(timestamps)):
            price_item = PriceItem()
            price_item['data_vendor_id'] = 1  # Assuming the data vendor ID is 1 for now
            price_item['symbol_id'] = 1  # Assuming the symbol ID is 1 for now
            price_item['price_date'] = timestamps[i]
            price_item['created_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            price_item['last_updated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            price_item['open_price'] = opens[i]
            price_item['high_price'] = highs[i]
            price_item['low_price'] = lows[i]
            price_item['close_price'] = closes[i]
            price_item['adj_close_price'] = adj_closes[i]
            price_item['volume'] = volumes[i]
            yield price_item
