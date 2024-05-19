# data_loader.py
import sys 
sys.path.append('/home/matthias/pytools')

import gc
import litstudy
from litstudy.types import DocumentSet, DocumentIdentifier
import time
from functools import partial
import aiosqlite
import asyncio
import sqlitedbgenerator
import asyncio
import inspect
from multiprocessing import Pool
from logger import logger


async def load_data(file_paths, source, load_file_func, batch_size):
    #logger.debug(f"Loading data from source: {source}")
    async for batch in load_data_storage(file_paths, source, load_file_func, batch_size):
        #logger.debug(f"Yielding batch of size: {len(batch)}")
        yield batch
    #logger.debug("Finished loading data")

async def process_file(file_path, load_file_func, source=None):
    #logger.debug(f"Processing file: {file_path}")
    if inspect.isasyncgenfunction(load_file_func):
        #logger.debug(f"load_file_func is an async generator function")
        documents = [doc async for doc in load_file_func(file_path, source)] if source and inspect.signature(load_file_func).parameters.get('source') else [doc async for doc in load_file_func(file_path)]
    elif asyncio.iscoroutinefunction(load_file_func):
        #logger.debug(f"load_file_func is a coroutine function")
        documents = await load_file_func(file_path, source) if source and inspect.signature(load_file_func).parameters.get('source') else await load_file_func(file_path)
    elif callable(load_file_func):
        #logger.debug(f"load_file_func is a callable")
        # If load_file_func is a regular function, run it in a separate thread to avoid blocking the event loop
        loop = asyncio.get_running_loop()
        try:
            if source and inspect.signature(load_file_func).parameters.get('source'):
                documents = await loop.run_in_executor(None, load_file_func, file_path, source)
            else:
                documents = await loop.run_in_executor(None, load_file_func, file_path)
        except TypeError as e:
            logger.error(f"TypeError occurred while calling load_file_func: {e}", exc_info=True)
            raise
        # If load_file_func returns a DocumentSet, convert it to a list
        if isinstance(documents, DocumentSet):
            #logger.debug(f"load_file_func returned a DocumentSet")
            documents = list(documents)
    else:
        raise TypeError('load_file_func must be an async generator function, a coroutine function, or a callable')

    #logger.debug(f"Number of documents in file: {len(documents)}")
    for doc in documents: 
        #logger.debug(f"Yielding document: {doc}")
        yield doc

async def load_data_storage(file_paths, source, load_file_func, batch_size=None):
    ##logger.debug(f"Loading data storage for source: {source}")
    batch = []
    for file_path in file_paths:
        logger.info(f"Processing file: {file_path}")
        try:
            async for document in process_file(file_path, load_file_func, source):
                if document is not None:
                    batch.append(document)
                    #logger.debug(f"Batch after appending document: {batch}")
                    if batch_size is not None and len(batch) == batch_size:
                        #logger.debug(f"Yielding batch of size: {len(batch)}")
                        #for doc in batch:
                            #logger.debug(f"Document in batch: {doc}")
                        yield batch
                        batch = []
        except TypeError:
            logger.error(f"TypeError occurred while processing file: {file_path}", exc_info=True)
        # Add an indented block here
    if batch:  # If there are any remaining documents in the batch
        logger.info(f"Yielding final batch of size: {len(batch)}")
        #for doc in batch:
            #logger.debug(f"Document in final batch: {doc}")
        yield batch  # Yield the last batch

def filter_and_log_new_documents(batch, existing_ids, source):
    #logger.debug(f"Filtering and logging new documents for source: {source}")
    existing_ids_set = set(existing_ids)
    new_documents = [(doc._identifier.doi, doc) for doc in batch if doc._identifier.doi not in existing_ids_set and doc._identifier.doi is not None]
    for doc_id, doc in new_documents:
        if doc_id is None:
            logger.warning(f"Document with None ID from source {source}: {doc}")
        #else:
            #logger.info(f"New document ID from source {source}: {doc_id}")
    logger.info(f"Number of new documents in batch from source {source}: {len(new_documents)}")
    return new_documents
                            
def filter_new_documents(batch, existing_ids):
    #logger.debug(f"Filtering new documents")

    if isinstance(batch, litstudy.DocumentSet):
        documents = batch.documents
    else:
        documents = batch

    for document in documents:
        try:
            doi = document._identifier.doi
        except AttributeError:
            print("Document does not have a '_identifier.doi' attribute")  # Debug print
            continue  # Continue to next document

        if doi not in existing_ids:
            yield doi, document
            
# Modify load_data_from_csv function to add debug logging
async def load_data_from_csv(litstudy_module, scopus_file_paths, wos_file_paths, springer_file_paths, database_file_path, batch_size=None):
    logger.debug("Loading data from CSV")
    sources = [
        (scopus_file_paths, 'scopus', litstudy_module.load_scopus_csv),
        (wos_file_paths, 'wos', partial(load_wos_csv, litstudy_module.load_csv)),
        (springer_file_paths, 'springer', litstudy_module.load_springer_csv),
    ]
    total_new_docs = 0
    existing_ids, total_docs = sqlitedbgenerator.get_existing_ids(database_file_path)

    for file_paths, source, load_file_func in sources:
        logger.debug(f"Processing source: {source}")
        source_new_docs = 0
        source_existing_docs = 0
        async for batch in load_data(file_paths, source, load_file_func, batch_size):
            logger.debug(f"Loaded batch of size: {len(batch)} from source: {source}")
            batch = [doc for doc in batch if doc._identifier.doi is not None]  # Exclude documents with None as their ID
            new_documents = filter_and_log_new_documents(batch, existing_ids, source)
            source_existing_docs += len(batch) - len(new_documents)  # Calculate number of existing documents
            source_new_docs += await sqlitedbgenerator.save_new_documents(database_file_path, new_documents, existing_ids)
            logger.debug(f"Number of documents excluded from saving to DB from source {source} because they already exist in the DB: {source_existing_docs}")
            logger.debug(f"Number of documents added to the database from source {source}: {source_new_docs}")
            yield new_documents
        gc.collect()

    logger.debug(f"Total number of new documents: {total_new_docs}")
    logger.debug(f"Total number of documents in the database: {total_docs + total_new_docs}")
    logger.debug("All documents loaded into the database. Pausing for half a minute...")
    await asyncio.sleep(3)  # pause for 1 minute
    
async def load_wos_csv(load_csv_func, file_path, fields_file_path=None):
    # Load the CSV file
    data = load_csv_func(file_path)

    for doc in data:
        doc['file_path'] = file_path
    return data