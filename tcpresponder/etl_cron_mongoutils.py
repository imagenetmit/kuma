import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.operations import UpdateOne
from loguru import logger
from datetime import datetime, timezone
import sys
# logger.remove()
# logger.add(sys.stderr, level="INFO", format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> - <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{level}</level> - {message}")
# logger.add('./logs/etl_cron_tickets_markdown.log', format="{time:YYYY-MM-DD HH:mm:ss} - {name}:{function} - {level} - {message}", rotation="1 week")



class MongoDBConnection:
    def __init__(self):
        # username = quote_plus(os.getenv('MONGODB_USERNAME'))
        # password = quote_plus(os.getenv('MONGODB_PASSWORD'))
        # cluster = os.getenv('MONGODB_CLUSTER')
        # self.uri = f"mongodb+srv://{username}:{password}@{cluster}"
        self.uri = os.getenv('MONGODB_URI')
        self.client = None

    async def __aenter__(self):
        self.client = AsyncIOMotorClient(self.uri, timeoutMS=120000)
        return self.client

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            self.client.close()


async def upsert_documents_async(documents, db_name,collection_name, id_field='id', upsert=True):
    async with MongoDBConnection() as client:
        db = client[db_name]
        collection = db[collection_name]
        
        operations = []
        for doc in documents:
            doc_copy = doc.copy()
            doc_copy['_id'] = doc[id_field]
            operations.append(UpdateOne(
                {'_id': doc[id_field]},
                {'$set': doc_copy},
                upsert=upsert
            ))
        
        if operations:
            try:
                result = await collection.bulk_write(operations)
                logger.info(f"MongoDB bulk write results - Matched: {result.matched_count}, "
                          f"Modified: {result.modified_count}, Upserted: {result.upserted_count}")
            except Exception as e:
                logger.error(f"Failed to perform bulk write operation: {str(e)}")
                raise


async def retrieve_documents_async(db_name, collection_name, filter_query=None, projection=None):
    async with MongoDBConnection() as client:
        db = client[db_name]
        collection = db[collection_name]

        cursor = collection.find(filter_query or {}, projection)
        documents = []
        async for doc in cursor:
            documents.append(doc)
        print(f"Retrieved {len(documents)} document(s)")
        return documents