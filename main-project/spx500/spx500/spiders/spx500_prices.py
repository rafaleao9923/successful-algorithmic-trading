            
import scrapy
import json
from datetime import datetime, timezone
import sqlite3
from spx500.items import PriceItem

class SPX500PricesSpider(scrapy.Spider):
    name = 'spx500_prices'
    allowed_domains = ['query1.finance.yahoo.com']
    custom_settings = {
        'DOWNLOAD_DELAY': 1.5,  # Respect Yahoo Finance rate limits
        'RANDOMIZE_DOWNLOAD_DELAY': True
    }
    
    def __init__(self, db_path='securities_master.db', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_path = db_path
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133.0',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://finance.yahoo.com',
            'Origin': 'https://finance.yahoo.com',
        }

    def start_requests(self):
        # Connect to database and get symbols
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, ticker FROM symbol")
        symbols = cursor.fetchall()
        conn.close()

        # Generate requests for each symbol
        for symbol_id, ticker in symbols:
            # Format the Yahoo Finance URL
            ticker = ticker.replace('.', '-')
            params = {
                'period1': int(datetime(2000, 1, 1, tzinfo=timezone.utc).timestamp()),
                'period2': int(datetime.now(timezone.utc).timestamp()),
                'interval': '1d',
                'events': 'history',
                'includeAdjustedClose': 'true'
            }
            
            url = f'https://query1.finance.yahoo.com/v8/finance/chart/{ticker}'
            
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                headers=self.headers,
                meta={'symbol_id': symbol_id},
                cb_kwargs={'params': params}
            )

    def parse(self, response, params):
        symbol_id = response.meta['symbol_id']
        
        try:
            data = json.loads(response.text)
            result = data['chart']['result'][0]
            
            # Extract price data
            timestamps = result['timestamp']
            quote = result['indicators']['quote'][0]
            adjclose = result['indicators']['adjclose'][0]['adjclose']
            
            # Process each data point
            for i in range(len(timestamps)):
                # Skip if any required value is None
                if any(x is None for x in [
                    quote['open'][i], quote['high'][i], quote['low'][i],
                    quote['close'][i], quote['volume'][i], adjclose[i]
                ]):
                    continue
                
                item = PriceItem()
                item.set_defaults()
                
                item['symbol_id'] = symbol_id
                item['price_date'] = datetime.fromtimestamp(
                    timestamps[i], tz=timezone.utc
                ).isoformat()
                item['open_price'] = quote['open'][i]
                item['high_price'] = quote['high'][i]
                item['low_price'] = quote['low'][i]
                item['close_price'] = quote['close'][i]
                item['adj_close_price'] = adjclose[i]
                item['volume'] = int(quote['volume'][i])
                
                yield item
                
        except Exception as e:
            self.logger.error(f"Error processing symbol_id {symbol_id}: {e}")