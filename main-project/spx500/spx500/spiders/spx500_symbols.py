import scrapy
from datetime import datetime
from spx500.items import SymbolItem

class SPX500SymbolsSpider(scrapy.Spider):
    name = 'spx500_symbols'
    allowed_domains = ['wikipedia.org']
    start_urls = ['https://en.wikipedia.org/wiki/List_of_S%26P_500_companies']
    
    def _get_exchange_id(self, href):
        if 'nasdaq.com' in href.lower():
            return self._get_exchange_mapping('NASDAQ')
        elif 'cboe.com' in href.lower():
            return self._get_exchange_mapping('CBOE')
        elif 'nyse.com' in href.lower():
            return self._get_exchange_mapping('NYSE')
        return self._get_exchange_mapping('NYSE')  # Default

    def _get_exchange_mapping(self, abbrev):
        # This should match your exchange table IDs
        mappings = {
            'NYSE': 1,
            'NASDAQ': 2,
            'CBOE': 3
        }
        return mappings.get(abbrev, 1)  # Default to NYSE (1) if not found
    
    def parse(self, response):
        now = datetime.now().isoformat()
        
        # Select the first wikitable
        table = response.css('table.wikitable')[0]
        
        # Process each row except the header
        for row in table.css('tr')[1:]:
            cells = row.css('td')
            if not cells:  # Skip if no cells (header row)
                continue
                
            href = cells[0].css('a::attr(href)').get('')
            exchange_id = self._get_exchange_id(href)
            
            item = SymbolItem()
            item['exchange_id'] = exchange_id
            item['ticker'] = cells[0].css('a::text').get().strip()
            item['instrument'] = 'equity'
            item['name'] = cells[1].css('a::text').get().strip()
            item['sector'] = cells[2].css('::text').get().strip()
            item['sub_industry'] = cells[3].css('::text').get().strip()
            item['headquarter'] = cells[4].css('::text').get().strip()
            item['date_added'] = cells[5].css('::text').get().strip()
            item['cik'] = cells[6].css('::text').get().strip()
            item['founded'] = cells[7].css('::text').get().strip()
            item['currency'] = 'USD'
            item['created_date'] = now
            item['last_updated_date'] = now
            
            yield item