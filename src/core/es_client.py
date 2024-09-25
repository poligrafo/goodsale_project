import logging

from elasticsearch import AsyncElasticsearch, helpers

logger = logging.getLogger(__name__)


class AsyncElasticsearchClient:
    def __init__(self, es_url: str):
        self.es = AsyncElasticsearch(hosts=[es_url])

    async def index_skus(self, skus):
        actions = []
        for sku in skus:
            if sku.uuid is None:
                logger.error(
                    "SKU with product_id=%s has uuid=None, skip indexing",
                    sku.product_id,
                )
                continue
            action = {
                "_index": "skus",
                "_id": str(sku.uuid),
                "_source": {
                    "title": sku.title,
                    "description": sku.description,
                    "brand": sku.brand,
                    "seller_id": sku.seller_id,
                    "seller_name": sku.seller_name,
                    "first_image_url": sku.first_image_url,
                    "category_id": sku.category_id,
                    "features": sku.features,
                    "price_before_discounts": sku.price_before_discounts,
                    "price_after_discounts": sku.price_after_discounts,
                    "currency": sku.currency,
                    "barcode": sku.barcode,
                    "rating_count": sku.rating_count,
                    "rating_value": sku.rating_value,
                    "discount": sku.discount,
                    "category_lvl_1": sku.category_lvl_1,
                    "category_lvl_2": sku.category_lvl_2,
                    "category_lvl_3": sku.category_lvl_3,
                    "category_remaining": sku.category_remaining,
                },
            }
            actions.append(action)

        if not actions:
            logger.warning("There is no SKU for indexing in Elasticsearch.")
            return

        try:
            # Используем официальный Async Elasticsearch helpers.bulk
            await helpers.async_bulk(
                self.es, actions, chunk_size=1000, request_timeout=60
            )
            logger.info("Indexed by %d SKU in Elasticsearch", len(actions))
        except Exception as e:
            logger.error("Error indexing the SKU in Elasticsearch: %s", e)
