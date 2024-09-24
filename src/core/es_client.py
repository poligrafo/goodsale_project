import logging

from elasticsearch import Elasticsearch, helpers

logger = logging.getLogger(__name__)


class ElasticsearchClient:
    def __init__(self, es_url: str):
        self.es = Elasticsearch(
            es_url,
            timeout=60,
            max_retries=10,
            retry_on_timeout=True,
        )

    def index_skus(self, skus):
        actions = []
        for sku in skus:
            if sku.uuid is None:
                logger.error(
                    "SKU with id=%s has uuid=None, skip indexing", sku.product_id
                )
                continue
            action = {
                "_index": "skus",
                "_id": str(sku.uuid),
                "_source": {
                    "title": sku.title,
                    "description": sku.description,
                    "brand": sku.brand,
                },
            }
            actions.append(action)

        if not actions:
            logger.warning("There is no SKU for indexing in Elasticsearch.")
            return

        try:
            helpers.bulk(self.es, actions, chunk_size=1000, request_timeout=60)
            logger.info("Indexed by %d SKU in Elasticsearch", len(actions))
        except Exception as e:
            logger.error("Error indexing the SKU in Elasticsearch: %s", e)
