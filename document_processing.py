import sys 
sys.path.append('/home/matthias/pytools')

import os
import sqlite3
from pybliometrics.scopus.utils import create_config
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sbs
import numpy as np
import csv
import sys
import time
import aiosqlite
import asyncio
import gc
from logger import logger
from functools import partial
import litstudy
import multiprocessing
from multiprocessing import Pool, Manager
import concurrent.futures
from contextlib import suppress, ExitStack
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, TimeoutError
from litstudy.types import DocumentSet, DocumentIdentifier
from functools import partial
from data_loader import load_data_storage, filter_new_documents
import sqlitedbgenerator
import dbm
from queue import Queue
import threading
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Initialize the CSV file for logging problematic documents
PROBLEMATIC_DOCUMENTS_FILE = "/mnt/c/Users/MatthiasReese/OneDrive - Griffith University/2. University Griffith/5. Literature/Literature Review/Pollinator Biodiversity/problematic_documents.csv"
with open(PROBLEMATIC_DOCUMENTS_FILE, "w", newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Problematic Document"])

async def writer_thread(write_queue, database_file_path):
    logger.debug('Writer thread started')
    async with aiosqlite.connect(database_file_path) as db:
        while True:
            write_request = await write_queue.get()
            logger.debug(f'Received write request: {write_request}')
            
            if write_request is None:
                logger.debug('Writer thread exiting')
                write_queue.task_done()
                break

            if len(write_request) != 2:
                logger.error(f"Unexpected write request format: {write_request}")
                write_queue.task_done()
                continue

            refine_func, doc = write_request
            logger.debug(f'Unpacked refine_func: {refine_func}, doc: {doc}')
            if doc is not None:
                try:
                    result = await refine_func_wrapper((refine_func, db, doc))
                except Exception as e:
                    logger.error(f"Error refining document : {e}")
                    result = (DocumentSet([]), DocumentSet([]))

                if result is not None and hasattr(result, '__iter__'):
                    try:
                        await sqlitedbgenerator.save_data(db, {doc['id']: result})
                        await db.commit()
                        logger.debug('Data committed to database')
                    except Exception as e:
                        logger.error(f"Error writing to database: {e}")
                write_queue.task_done()

        await write_queue.join()
        logger.debug('Write queue is empty')

        
async def refine_func_wrapper(args):
    logger.debug('Refine function wrapper started')
    logger.debug(f'args: {args}')

    refine_func, db, doc = args  # Unpack the arguments tuple
    logger.debug(f'Unpacked refine_func: {refine_func}, db: {db}, doc: {doc}')

    if doc is None:
        logger.debug('Document is None, skipping refinement')
        return DocumentSet([]), DocumentSet([])

    database_file_path = '.crossref.dir' if refine_func == litstudy.refine_crossref else 'new_database_file_path'

    result = None
    if doc is not None:
        try:
            # Call refine_func directly and await its result
            result = await refine_func(database_file_path, doc)
        except Exception as e:
            logger.error(f"Error refining document {doc._identifier.doi}: {e}")
            return DocumentSet([]), DocumentSet([])

    await asyncio.sleep(0.01)
    logger.debug(f"Refinement results: {result}")

    if isinstance(result, tuple):
        logger.debug(f"Number of values in result: {len(result)}")
        logger.debug(f"Result contents: {result}")
        if len(result) == 2:
            return result
        else:
            logger.debug(f'Problem with the result: {result}')
            # Log the problematic document if result does not contain exactly two elements
            with open(PROBLEMATIC_DOCUMENTS_FILE, "a", newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow({})
            return DocumentSet([]), DocumentSet([])
    else:
        logger.debug("Result is not a tuple")
        return DocumentSet([]), DocumentSet([])
    
def get_documents(document_sets):
    logger.debug('Getting documents')
    for doc_set in document_sets.values():
        if isinstance(doc_set, DocumentSet):
            for doc in doc_set.docs:
                if doc is not None:
                    yield doc
        elif isinstance(doc_set, list):
            for doc in doc_set:
                if doc is not None:
                    yield doc
        else:
            # If doc_set is not a DocumentSet or a list, treat it as an individual document
            yield doc_set

async def submit_tasks(write_queue, refine_func, db, documents):
    logger.debug('Submitting tasks')
    futures = set()

    async def process_documents():
        for row in documents:
            doc = DocumentSet([row])  # Convert row to DocumentSet object
            write_request = (refine_func, db, doc) # Pass db as new_database_file_path
            await write_queue.put((write_request, db))  # Include db separately
            future = asyncio.create_task(refine_func_wrapper(write_request))
            futures.add(future)

    await process_documents()  # Await the process_documents function
    
    return futures


async def handle_futures(futures):
    logger.debug('Handling futures')
    done, not_done = await asyncio.wait(futures, timeout=60)  # Wait for 60 seconds
    for future in not_done:
        future.cancel()  # Cancel the tasks that didn't finish in time
    return done

async def process_results(done, refined_batches, total_results):
    logger.debug('Processing results')
    for future in done:
        try:
            batch_results = future.result()
            logger.debug(f"Future result: {batch_results}, Length: {len(batch_results)}")
            logger.debug(f"Type of batch_results: {type(batch_results)}, Content: {batch_results}")
            
            if isinstance(batch_results, tuple):
                if len(batch_results) == 2:
                    refined_doc_scopus_list, refined_doc_crossref_list = batch_results
                    for refined_doc_scopus in refined_doc_scopus_list.docs:
                        refined_batches[refined_doc_scopus._identifier.doi] = refined_doc_scopus
                        total_results['scopus'] += 1
                    for refined_doc_crossref in refined_doc_crossref_list.docs:
                        refined_batches[refined_doc_crossref._identifier.doi] = refined_doc_crossref
                        total_results['crossref'] += 1
                else:
                    logger.error(f"Unexpected number of elements in batch_results: {len(batch_results)}")
                    # Log the problematic document if result does not contain exactly two elements
                    with open(PROBLEMATIC_DOCUMENTS_FILE, "a", newline='') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow([str(future)])
            else:
                logger.error("Unexpected batch_results format")
                continue  # Skip processing if the format is unexpected

        except Exception as e:
            logger.error(f"Error processing result: {e}")
            continue

    total_results['not_found'] += len(refined_batches) - (total_results['scopus'] + total_results['crossref'])
    return refined_batches, total_results



async def refine_documents_in_batches(database_file_path, batch_size, start, refine_func=None):
    logger.debug('Refining documents in batches')
    total_results = {'scopus': 0, 'crossref': 0, 'not_found': 0}
    new_database_file_path = database_file_path.replace('.db', '_refined.db')
    database_path, new_database_file = os.path.split(new_database_file_path)

    if os.path.exists(new_database_file_path):
        logger.info(f"Database file '{new_database_file_path}' already exists.")
    else:
        logger.info("New database, preparing for creation.")
        sqlitedbgenerator.create_database(database_path, new_database_file)
        await asyncio.sleep(5)  # Pause execution for 5 seconds to simulate preparation

    total_documents = sqlitedbgenerator.get_total_documents(database_file_path)
    refined_batches = {}
    batch_count = 0

    while True:
        logger.debug('Fetching data from database...')
        document_sets = await sqlitedbgenerator.get_data(database_file_path, batch_size, start=start)
        documents = list(get_documents(document_sets))  # Convert generator to list

        if not documents:
            logger.debug('No more documents to process.')
            break

        logger.debug('Starting writer thread...')
        write_queue = asyncio.Queue()
        writer = asyncio.create_task(writer_thread(write_queue, new_database_file_path))

        futures = await submit_tasks(write_queue, refine_func, new_database_file_path, documents)  # Pass new_database_file_path
        done = await handle_futures(futures)
        await process_results(done, refined_batches, total_results)  # Properly await process_results

        await write_queue.put(None)  # Signal the writer thread to exit
        await writer  # Wait for the writer thread to complete

        logger.info(f"Batch count: {batch_count}")
        logger.info(f"Number of refined documents in this batch: {len(refined_batches)}")
        logger.info(f"First few refined documents in this batch: {list(refined_batches.items())[:5]}")

        # Only save refined documents if they are not None
        refined_to_save = {doc_id: refined_doc for doc_id, refined_doc in refined_batches.items() if refined_doc is not None}
        if refined_to_save:
            await sqlitedbgenerator.save_data(new_database_file_path, refined_to_save)
            logger.debug(f"Saved refined documents to database after batch {batch_count}")
        else:
            logger.debug(f"No refined documents to save after batch {batch_count}")

        refined_batches.clear()
        batch_count += 1
        start += batch_size

    # Handle any remaining refined batches
    if refined_batches:
        logger.debug(f"Refined batches: {refined_batches}")
        refined_to_save = {doc_id: refined_doc for doc_id, refined_doc in refined_batches.items() if refined_doc is not None}
        if True:  # Always save the data
            await sqlitedbgenerator.save_data(new_database_file_path, refined_to_save)
            logger.debug(f"Saved refined documents to database after batch {batch_count}")
            total_docs = sqlitedbgenerator.get_total_documents(new_database_file_path)
            logger.debug(f"Number of documents in the database: {total_docs}")

    # Output final statistics
    if os.path.exists(database_file_path):
        size = os.path.getsize(database_file_path)
        logger.info(f"Size of the original database file: {size} bytes")

    logger.info(f"Total documents found in Scopus: {total_results['scopus']}")
    logger.info(f"Total documents found in Crossref: {total_results['crossref']}")
    logger.info(f"Total documents not found: {total_results['not_found']}")

    if total_documents > 0:
        logger.info(f"Ratio of successfully refined documents to total documents: {(total_results['scopus'] + total_results['crossref']) / total_documents}")
    else:
        logger.info("No documents were found in the database.")

    return start
    


async def refine_document(database_file_path, document):
    logger.debug('Refining document')
    # Log the type of the document variable
    logger.debug(f'Type of document: {type(document)}')

    if document is None:
        logger.debug('Document is None, skipping refinement')
        return None  # Return None if document is None

    refined_doc_scopus, refined_doc_crossref = DocumentSet([]), DocumentSet([])

    # Convert document to DocumentSet if it's not already
    if not isinstance(document, DocumentSet):
        document = DocumentSet([document])

    try:
        # Refine the document with Scopus using asyncio.to_thread
        result_scopus = await asyncio.to_thread(litstudy.refine_scopus, document)
        logger.debug(f"Contents of result_scopus: {result_scopus}")
    except Exception as e:
        logger.error(f"Error during refinement with Scopus: {str(e)}")
        return None  # Return None if refinement with Scopus fails

    try:
        if result_scopus and len(result_scopus) == 2:
            logger.debug('Two values in result_scopus')
            refined_doc_scopus.docs.extend(list(result_scopus[0].docs))
            not_found_docs = result_scopus[1]
        else:
            not_found_docs = document
    except Exception as e:
        logger.error(f"Unexpected number of values in result_scopus: {str(e)}")
        return None  # Return None if unexpected result format

    try:
        # Refine the document with Crossref using asyncio.to_thread
        result_crossref = await asyncio.to_thread(litstudy.refine_crossref, not_found_docs)
        logger.debug(f"Contents of result_crossref: {result_crossref}")
    except Exception as e:
        logger.error(f"Error during refinement with Crossref: {str(e)}")
        return None  # Return None if refinement with Crossref fails

    try:
        if result_crossref and len(result_crossref) == 2:
            logger.debug('Two values in result_crossref')
            refined_doc_crossref.docs.extend(list(result_crossref[0].docs))
    except Exception as e:
        logger.error(f"Unexpected number of values in result_crossref: {str(e)}")
        return None  # Return None if unexpected result format

    # Ensure that both refined_doc_scopus and refined_doc_crossref are returned
    if refined_doc_scopus or refined_doc_crossref:
        return refined_doc_scopus, refined_doc_crossref  # Return refined documents if found
    else:
        logger.error("No refined documents found")
        return None  # Return None if no refined documents are found