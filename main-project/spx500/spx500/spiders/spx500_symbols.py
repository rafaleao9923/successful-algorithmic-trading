from scrapy import Spider
from spx500.items import SymbolItem
from datetime import datetime

class SymbolSpider(Spider):
    name = 'spx500_symbols'
    start_urls = [
        'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies',
    ]

    def parse(self, response):
        symbols_list = response.css('table.wikitable tr')[1:]

        for symbol in symbols_list:
            tds = symbol.css('td')
            href = tds[0].css('a::attr(href)').get('')

            # Extract exchange from URL
            if 'nasdaq.com' in href.lower():
                exchange = 'NASDAQ'
            elif 'cboe.com' in href.lower():
                exchange = 'CBOE'
            elif 'nyse.com' in href.lower():
                exchange = 'XNYS' if ':XNYS' in href else 'NYSE'
            else:
                exchange = 'NYSE'  # Default

            # Map exchange names to IDs based on the database
            exchange_map = {
                'NYSE': 1,
                'NASDAQ': 2,
                'CBOE': 3,
                'XNYS': 1  # Map XNYS to NYSE ID
            }
            exchange_id = exchange_map.get(exchange, 1)  # Default to NYSE (1) if not found

            symbol_item = SymbolItem()
            symbol_item['exchange_id'] = exchange_id
            symbol_item['ticker'] = tds[0].css('a::text').get().strip()
            symbol_item['instrument'] = 'equity'
            symbol_item['name'] = tds[1].css('a::text').get().strip()
            symbol_item['sector'] = tds[2].css('::text').get().strip()
            symbol_item['sub_industry'] = tds[3].css('::text').get().strip()
            symbol_item['headquarter'] = tds[4].css('::text').get().strip()
            symbol_item['date_added'] = tds[5].css('::text').get().strip()
            symbol_item['cik'] = tds[6].css('::text').get().strip()
            symbol_item['founded'] = tds[7].css('::text').get().strip()
            symbol_item['currency'] = 'USD'
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            symbol_item['created_date'] = now
            symbol_item['last_updated_date'] = now
            yield symbol_item
