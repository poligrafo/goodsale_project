import asyncio
import logging

from src.app.match import AsyncMatcher
from src.app.parser import AsyncXMLParser
from src.core.db import async_session_maker, init_db
from src.core.es_client import AsyncElasticsearchClient
from src.core.logging import setup_logging
from src.core.settings import settings


async def main():
    setup_logging(settings.LOG_DIR)
    logger = logging.getLogger(__name__)

    logger.info("Launching the Goodsale service")

    try:
        await init_db()
    except Exception as e:
        logger.error("Error during db initialization: %s", e)
        return

    es_client = None

    async with async_session_maker() as db_session:
        try:
            # XML parsing and creation of SKU objects
            parser = AsyncXMLParser(settings.XML_FEED_URL)
            skus = [sku async for sku in parser.parse()]

            # Adding SKU objects to a session
            async with db_session.begin():
                db_session.add_all(skus)
            logger.info("Inserted %d SKU into the db", len(skus))

            # Indexing data in Elasticsearch
            es_client = AsyncElasticsearchClient(settings.ELASTICSEARCH_URL)
            await es_client.index_skus(skus)

            # Creating an index and searching for similar SKUs
            semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_REQUESTS)
            matcher = AsyncMatcher(es_client.es, db_session, semaphore)
            await matcher.create_index("skus")
            await matcher.process_all_skus(batch_size=1000)

        except Exception as e:
            logger.error("An error has occurred: %s", e)
            await db_session.rollback()
        finally:
            if es_client:
                await es_client.es.close()
            await db_session.close()

    logger.info("Processing is completed")


if __name__ == "__main__":
    asyncio.run(main())
