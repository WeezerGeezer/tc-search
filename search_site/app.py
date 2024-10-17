from flask import Flask, request, render_template, url_for, send_file, abort, redirect, flash
from whoosh.index import open_dir
from whoosh.qparser import QueryParser, MultifieldParser
from math import ceil
import os
import pandas as pd
import logging
from whoosh.qparser import MultifieldParser, FuzzyTermPlugin
from whoosh.query import FuzzyTerm
from functools import wraps
from whoosh.analysis import StemmingAnalyzer
from dotenv import load_dotenv
from flask_cors import CORS
# Comment out database-related imports
# from flask_sqlalchemy import SQLAlchemy
# from werkzeug.security import generate_password_hash, check_password_hash
# import pymysql

app = Flask(__name__)
# Load environment variables from .env file
load_dotenv()
# Enable CORS for all routes and origins
CORS(app)

# Comment out database configuration
# db_user = os.getenv("DB_USER")
# db_pass = os.getenv("DB_PASSWORD")
# db_name = os.getenv("DB_NAME")
# db_host = os.getenv("DB_HOST")
# instance_connection_name = os.getenv("INSTANCE_CONNECTION_NAME")

# Comment out SQLAlchemy configuration
# if os.getenv("K_SERVICE"):
#     unix_socket = f'/cloudsql/{instance_connection_name}'
#     app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{db_user}:{db_pass}@/{db_name}?unix_socket={unix_socket}'
# else:
#     app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{db_user}:{db_pass}@{db_host}/{db_name}'

# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = Falseapp.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "fallback-secret-key")

app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "fallback-secret-key")

# Comment out SQLAlchemy initialization
# db = SQLAlchemy(app)
logging.basicConfig(level=logging.DEBUG)

# Ensure the index directory exists
index_dir = os.path.join(os.path.dirname(__file__), 'index')
if not os.path.exists(index_dir):
    raise RuntimeError("Whoosh index not found. Please run the indexing script first.")

# Open the Whoosh index
app.whoosh_index = open_dir(index_dir)

@app.route('/download/csv/<episode_id>')
def download_csv(episode_id):
    try:
        csv_path = os.path.join(app.root_path, 'static', 'episodes', 'transcripts', f'{episode_id}.csv')
        return send_file(csv_path, as_attachment=True, download_name=f'episode_{episode_id}.csv')
    except FileNotFoundError:
        abort(404)

@app.route('/download/transcript/<episode_id>')
def download_transcript(episode_id):
    try:
        transcript_path = os.path.join(app.root_path, 'static', 'episodes', 'txt-files', f'{episode_id}.txt')
        return send_file(transcript_path, as_attachment=True, download_name=f'episode_{episode_id}_transcript.txt')
    except FileNotFoundError:
        abort(404)

@app.route('/episode/<episode_id>')
def episode_detail(episode_id):
    app.logger.debug(f"Attempting to load episode {episode_id}")
    try:
        csv_path = os.path.join(app.root_path, 'static', 'episodes', 'transcripts', f'{episode_id}.csv')
        app.logger.debug(f"Looking for CSV file at: {csv_path}")
        
        if not os.path.exists(csv_path):
            app.logger.error(f"CSV file not found: {csv_path}")
            abort(404)
        
        app.logger.debug(f"CSV file found, attempting to read")
        df = pd.read_csv(csv_path, sep=';', names=['start_time', 'end_time', 'transcript'], quotechar='"')
        
        # Convert DataFrame to list of dictionaries
        transcript = df.to_dict('records')
        
        # Construct the wiki link
        wiki_link = f"https://the-time-crisis-universe.fandom.com/wiki/Episode_{episode_id}"
        
        # Determine if episode download is available
        episode_number = int(episode_id)
        if episode_number <= 180:
            episode_download_link = f"https://timecrisis.net/audio/{episode_number:04d}/audio.mp3"
            episode_download_text = "Download Episode"
        else:
            episode_download_link = "#"
            episode_download_text = "Download not available"
        
        # Get the episode name from the Whoosh index
        with app.whoosh_index.searcher() as searcher:
            episode_doc = searcher.document(episode=episode_id)
            episode_name = episode_doc['episode_name'] if episode_doc else "Unknown Episode"
        
        # Get the timestamp from the URL fragment
        timestamp = request.args.get('t', '')
        
        return render_template('episode.html', 
                               episode_id=episode_id,
                               episode_name=episode_name,
                               transcript=transcript,
                               tcu_wiki_link=wiki_link,
                               episode_download_link=episode_download_link,
                               episode_download_text=episode_download_text,
                               csv_download_link=url_for('download_csv', episode_id=episode_id),
                               transcript_download_link=url_for('download_transcript', episode_id=episode_id),
                               timestamp=timestamp)
    except Exception as e:
        app.logger.error(f"Error in episode_detail: {str(e)}", exc_info=True)
        abort(500)  # Return a 500 error for any other exceptions

@app.route('/', methods=['GET', 'POST'])
def search():
    query = request.args.get('query', '')
    page = int(request.args.get('page', 1))
    field = request.args.get('field', 'content')
    sort_by = request.args.get('sort_by', 'episode')
    fuzzy_search = request.args.get('fuzzy_search') == 'on'

    app.logger.debug(f"Search request - Query: {query}, Page: {page}, Fuzzy: {fuzzy_search}")

    if request.method == 'POST':
        query = request.form['query']
        app.logger.debug(f"POST request - Redirecting to search with query: {query}")
        return redirect(url_for('search', query=query, page=1, fuzzy_search=fuzzy_search))

    if query:
        try:
            with app.whoosh_index.searcher() as searcher:
                analyzer = StemmingAnalyzer()
                
                if field == 'content':
                    parser = QueryParser("content", schema=app.whoosh_index.schema)
                elif field == 'episode_name':
                    parser = QueryParser("episode_name", schema=app.whoosh_index.schema)
                else:
                    parser = MultifieldParser(["content", "episode_name"], schema=app.whoosh_index.schema)
                
                if fuzzy_search:
                    parser.add_plugin(FuzzyTermPlugin())
                
                query_obj = parser.parse(query)
                
                results = searcher.search(query_obj, limit=None)

                episode_results = {}
                for hit in results:
                    episode_id = hit['episode']
                    if episode_id not in episode_results:
                        episode_results[episode_id] = {
                            'episode_name': hit['episode_name'],
                            'episode': episode_id,
                            'episode_url': url_for('episode_detail', episode_id=episode_id),
                            'hits': [],
                            'hit_count': 0
                        }
                    if len(episode_results[episode_id]['hits']) < 10:
                        episode_results[episode_id]['hits'].append({
                            'start_time': hit['start_time'],
                            'end_time': hit['end_time'],
                            'content': hit.highlights("content") or hit['content'][:300],
                            'url': f"{url_for('episode_detail', episode_id=episode_id)}#t={hit['start_time']}"
                        })
                    episode_results[episode_id]['hit_count'] += 1

                if sort_by == 'hits':
                    sorted_episodes = sorted(episode_results.values(), key=lambda x: x['hit_count'], reverse=True)
                else:
                    sorted_episodes = sorted(episode_results.values(), key=lambda x: int(x['episode']))

                total_episodes = len(sorted_episodes)
                total_pages = max(1, ceil(total_episodes / 15))
                page = max(1, min(page, total_pages))
                
                start = (page - 1) * 15
                end = start + 15
                
                paginated_results = sorted_episodes[start:end]
                
                app.logger.debug(f"Total episodes: {total_episodes}, Total pages: {total_pages}")
                app.logger.debug(f"Returning {len(paginated_results)} episodes for page {page}")
                
                return render_template('search_results.html', 
                                       results=paginated_results, 
                                       query=query, 
                                       page=page, 
                                       total_pages=total_pages,
                                       field=field,
                                       sort_by=sort_by,
                                       fuzzy_search=fuzzy_search)
        except Exception as e:
            app.logger.error(f"Error occurred while searching: {str(e)}", exc_info=True)
            return render_template('search_results.html', query=query, error="An error occurred while searching. Please try again.")
    
    app.logger.debug("Rendering empty search page")
    return render_template('search.html', query=query, fuzzy_search=fuzzy_search)

# Comment out FlaggedSegment model
# class FlaggedSegment(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     episode_id = db.Column(db.String(10), nullable=False)
#     start_time = db.Column(db.String(10), nullable=False)
#     end_time = db.Column(db.String(10), nullable=False)
#     content = db.Column(db.Text, nullable=False)
#     reason = db.Column(db.Text, nullable=True)

# Comment out database table creation
# with app.app_context():
#     db.create_all()

#Comment out admin credentials
# ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
# ADMIN_PASSWORD = generate_password_hash(os.getenv("ADMIN_PASSWORD"))

# Comment out admin_required decorator
# def admin_required(f):
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         auth = request.authorization
#         if not auth or not check_password_hash(ADMIN_PASSWORD, auth.password) or auth.username != ADMIN_USERNAME:
#             return 'Unauthorized', 401
#         return f(*args, **kwargs)
#     return decorated_function

# Comment out flag_segment route
# @app.route('/flag_segment', methods=['POST'])
# def flag_segment():
#     episode_id = request.form['episode_id']
#     start_time = request.form['start_time']
#     end_time = request.form['end_time']
#     content = request.form['content']
#     reason = request.form['reason']

#     flagged_segment = FlaggedSegment(
#         episode_id=episode_id,
#         start_time=start_time,
#         end_time=end_time,
#         content=content,
#         reason=reason
#     )
#     db.session.add(flagged_segment)
#     db.session.commit()

#     flash('Segment flagged successfully', 'success')
#     return redirect(url_for('episode_detail', episode_id=episode_id))

# Comment out admin panel route
# @app.route('/admin')
# @admin_required
# def admin_panel():
#     flagged_segments = FlaggedSegment.query.all()
#     return render_template('admin_panel.html', flagged_segments=flagged_segments)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 8080)), debug=False)