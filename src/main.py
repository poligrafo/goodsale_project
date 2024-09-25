import logging

from src.app.match import Matcher
from src.app.parser import XMLParser
from src.core.db import SessionLocal, init_db
from src.core.es_client import ElasticsearchClient
from src.core.logging import setup_logging
from src.core.settings import settings


def main():
    setup_logging(settings.LOG_DIR)
    logger = logging.getLogger(__name__)

    logger.info("Launching the Goodsale service")

    # db initialization
    init_db()
    db_session = SessionLocal()

    try:
        # XML parsing and creation of SKU objects
        parser = XMLParser(settings.XML_FEED_URL)
        skus = list(parser.parse())

        # Adding SKU objects to a session
        db_session.add_all(skus)
        db_session.commit()
        logger.info("Inserted %d SKU into the db", len(skus))

        # Indexing data in Elasticsearch
        es_client = ElasticsearchClient(settings.ELASTICSEARCH_URL)
        es_client.index_skus(skus)

        # Creating an index and searching for similar SKU
        matcher = Matcher(
            es_client.es, db_session, max_workers=10
        )  # Adjust the number of threads
        matcher.create_index("skus")
        matcher.process_all_skus(batch_size=1000)

    except Exception as e:
        logger.error("An error has occurred: %s", e)
        db_session.rollback()
    finally:
        db_session.close()

    logger.info("Processing is completed")


if __name__ == "__main__":
    main()
