import asyncio
import logging
from uuid import UUID

from elasticsearch import AsyncElasticsearch
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models import SKU

logger = logging.getLogger(__name__)


class AsyncMatcher:
    def __init__(
        self,
        es: AsyncElasticsearch,
        db_session: AsyncSession,
        semaphore: asyncio.Semaphore,
    ):
        self.es = es
        self.db_session = db_session
        self.semaphore = semaphore

    async def create_index(self, index_name: str):
        mappings = {
            "mappings": {
                "properties": {
                    "title": {"type": "text"},
                    "description": {"type": "text"},
                    "brand": {"type": "keyword"},
                }
            }
        }
        exists = await self.es.indices.exists(index=index_name)
        if not exists:
            await self.es.indices.create(index=index_name, body=mappings)
            logger.info("The index '%s' has been created in Elasticsearch", index_name)

    async def find_similar_skus(self, sku: SKU):
        if sku.uuid is None:
            logger.error("SKU with product_id=%s has uuid=None", sku.product_id)
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

        async with self.semaphore:
            try:
                response = await self.es.search(index="skus", body=query)
                similar_uuids = [
                    UUID(hit["_id"])
                    for hit in response["hits"]["hits"]
                    if hit["_id"] != str(sku.uuid)
                ][:5]
                sku.similar_sku = similar_uuids
                logger.info(
                    "Updated SKU %s with similar SKUs: %s", sku.uuid, similar_uuids
                )
            except Exception as e:
                logger.error(
                    "Error when searching for similar SKUs for SKUs %s: %s",
                    sku.uuid,
                    e,
                    exc_info=True,
                )

    async def process_all_skus(self, batch_size: int = 1000):
        result = await self.db_session.execute(select(func.count(SKU.uuid)))
        total_skus = result.scalar()
        logger.info("%d SKU found for processing", total_skus)

        # Обрабатываем SKU пакетами
        for offset in range(0, total_skus, batch_size):
            result = await self.db_session.execute(
                select(SKU).offset(offset).limit(batch_size)
            )
            skus = result.scalars().all()
            logger.info("ОA package is being processed from %d SKU", len(skus))

            tasks = [self.find_similar_skus(sku) for sku in skus]
            await asyncio.gather(*tasks)

            try:
                await self.db_session.commit()
                logger.info(
                    "The %d SKU batch has been successfully updated.", len(skus)
                )
            except Exception as e:
                logger.error(
                    "Error when committing changes to the database: %s",
                    e,
                    exc_info=True,
                )
                await self.db_session.rollback()
