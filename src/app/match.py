import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from elasticsearch import Elasticsearch
from sqlalchemy.orm import Session

from src.core.models import SKU

logger = logging.getLogger(__name__)


class Matcher:
    def __init__(self, es: Elasticsearch, db_session: Session, max_workers: int = 10):
        self.es = es
        self.db_session = db_session
        self.max_workers = max_workers

    def create_index(self, index_name: str):
        mappings = {
            "mappings": {
                "properties": {
                    "title": {"type": "text"},
                    "description": {"type": "text"},
                    "brand": {"type": "keyword"},
                }
            }
        }
        if not self.es.indices.exists(index=index_name):
            self.es.indices.create(index=index_name, body=mappings)
            logger.info("Создан индекс '%s' в Elasticsearch", index_name)

    def find_similar_skus(self, sku: SKU):
        if sku.uuid is None:
            logger.error("SKU с product_id=%s имеет uuid=None", sku.product_id)
            return

        query = {
            "query": {
                "more_like_this": {
                    "fields": ["title", "description"],
                    "like": [
                        {
                            "_index": "skus",
                            "_id": str(sku.uuid),
                        }
                    ],
                    "min_term_freq": 1,
                    "max_query_terms": 12,
                }
            }
        }

        try:
            response = self.es.search(index="skus", body=query)
            similar_uuids = [
                hit["_id"]
                for hit in response["hits"]["hits"]
                if hit["_id"] != str(sku.uuid)
            ][:5]
            sku.similar_sku = similar_uuids
            logger.info("Updated SKU %s with similar SKUs: %s", sku.uuid, similar_uuids)
        except Exception as e:
            logger.error(
                "Error when searching for similar SKUs for SKU %s: %s", sku.uuid, e
            )

    def process_all_skus(self, batch_size: int = 1000):
        total_skus = self.db_session.query(SKU).count()
        logger.info("%d SKU found for processing", total_skus)

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_sku = {}
            offset = 0

            while offset < total_skus:
                skus = self.db_session.query(SKU).offset(offset).limit(batch_size).all()
                if not skus:
                    break
                logger.info("A package from %d SKU is being processed", len(skus))
                for sku in skus:
                    future = executor.submit(self.find_similar_skus, sku)
                    future_to_sku[future] = sku
                offset += batch_size

            for future in as_completed(future_to_sku):
                sku = future_to_sku[future]
                try:
                    future.result()
                except Exception as exc:
                    logger.error("SKU %s caused an exception: %s", sku.uuid, exc)

        try:
            self.db_session.commit()
            logger.info("All similar SKUs have been successfully updated in the db.")
        except Exception as e:
            logger.error("Error when committing changes to the db: %s", e)
            self.db_session.rollback()
