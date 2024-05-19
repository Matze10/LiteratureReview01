import sys 
sys.path.append('/home/matthias/pytools')

import sqlitedbgenerator
import apiconfig
import document_processing
import data_loader
import asyncio
import litstudy
from pybliometrics.scopus.utils import create_config
import apiconfig
import os
import time
from logger import logger
import dbm
#File Paths 
#Scopus Files
scopus_files = [
]

#Web Of Science Files 
wos_files = [
]

#Springer files
springer_files = [
]

async def main():
    logger.debug("Main function started")

    # Specify the desired database file path
    home_dir = os.path.expanduser("~")
    database_path = os.path.join(home_dir, "DB")
    database_file = 'literaturestudy01.db'
    database_file_path = os.path.join(database_path, database_file)

    # Create the database if it doesn't exist
    if not os.path.exists(database_file_path):
        logger.debug(f"Creating database: {database_file_path}")
        sqlitedbgenerator.create_database(database_path, database_file)

    # Load data from CSV files
    logger.debug("Loading data from CSV files...")
    scopus_file_paths = scopus_files
    wos_file_paths = wos_files
    springer_file_paths = springer_files
    batch_size = 1000
    async for data in data_loader.load_data_from_csv(litstudy, scopus_file_paths, wos_file_paths, springer_file_paths, database_file_path, batch_size):
        logger.debug(f"Loaded new documents: {len(data)}")

    logger.debug("Finished loading data")
    try:
        api_keys_file_path = os.path.join(home_dir, 'API_KEYS', 'Elsevier', 'elsevier_api_keys.txt')
        SCOPUS_API_KEYS = apiconfig.load_api_keys(api_keys_file_path)
        create_config(keys=SCOPUS_API_KEYS) #create config file with the API Keys
        # Refine the documents in the database
        logger.debug("Starting to refine documents")
        start = 0
        start = await document_processing.refine_documents_in_batches(database_file_path, batch_size, start, refine_func=document_processing.refine_document)
        logger.debug("Finished refining documents")

        # Calculate the total number of documents


    except Exception as e:
        logger.error(f"ERROR in main function: {e}")

if __name__ == '__main__':
    asyncio.run(main())
