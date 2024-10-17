import os
from whoosh.index import create_in
from whoosh.fields import *
import pandas as pd
from whoosh.qparser import QueryParser
import logging
from whoosh.analysis import StemmingAnalyzer

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

# Define the schema for our index using StemmingAnalyzer
schema = Schema(
    episode=ID(stored=True),
    episode_name=TEXT(stored=True),  # Remove analyzer from here
    start_time=TEXT(stored=True),
    end_time=TEXT(stored=True),
    content=TEXT(stored=True, analyzer=StemmingAnalyzer())
)

# Create the index
if not os.path.exists("index"):
    os.mkdir("index")
ix = create_in("index", schema)

# Function to add documents to the index
def index_transcripts(csv_directory):
    writer = ix.writer()
    for filename in os.listdir(csv_directory):
        if filename.endswith('.csv'):
            episode_parts = filename.split('_')
            episode_id = episode_parts[0]
            episode_name = '_'.join(episode_parts[1:]).split('.')[0]
            file_path = os.path.join(csv_directory, filename)
            
            try:
                df = pd.read_csv(file_path, sep=';', names=['start_time', 'end_time', 'transcript'], quotechar='"')
                for _, row in df.iterrows():
                    writer.add_document(
                        episode=episode_id,
                        episode_name=episode_name,
                        start_time=row['start_time'],
                        end_time=row['end_time'],
                        content=row['transcript']
                    )
                logging.info(f"Indexed file: {filename}")
            except Exception as e:
                logging.error(f"Error indexing file {filename}: {e}")
    writer.commit()

# Function to search the index
def search_transcripts(query_string):
    with ix.searcher() as searcher:
        query = QueryParser("content", ix.schema).parse(query_string)
        results = searcher.search(query, limit=None)
        
        for result in results:
            print(f"Episode: {result['episode']}")
            print(f"Time: {result['start_time']} - {result['end_time']}")
            print(f"Content: {result['content']}")
            print("---")

# Index the transcripts
index_transcripts('/Users/mitchellcarter/Documents/Github/web_scraper_project/search-site/static/episodes/csv-with-title')