BOT_NAME = 'spx500'

SPIDER_MODULES = ['spx500.spiders']
NEWSPIDER_MODULE = 'spx500.spiders'

ITEM_PIPELINES = {
    'spx500.pipelines.SqlitePipeline': 300,
}
