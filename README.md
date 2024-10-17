# Time Crisis Search Engine

## Introduction

Time Crisis, the world's premier internet radio show, lacked a comprehensive search engine for its near decade-long lore. To address this, I've created a search tool that allows the real TC heads to explore the show's transcripts with ease. Use tc-search.com to explore the wealth of the Time Crisis Universe (or run it locally if you'd like!)

## Features

- Full-text search across (mostly!)all Time Crisis episode transcripts
    - Some episodes are missing bc I haven't downloaded & indexed them yet :/
- Episode-specific transcript viewing with timestamp navigation
- Advanced search options including field-specific queries, pagination, and sorting
- Responsive design for both desktop and mobile use

## Technologies Used

- Python 3.8+
- Flask (Web framework)
- Whoosh (Full-text search engine)
- OpenAI Whisper (Speech recognition model for transcription)
- HTML/CSS/JavaScript (Frontend)
- Jinja2 (Templating engine)

## Setup (If you'd like to run it locally)

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/time-crisis-search.git
   cd time-crisis-search
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Set up the Whoosh index:
   ```
   python create_index.py
   ```

5. Run the Flask application:
   ```
   python app.py
   ```

6. Open a web browser and navigate to `http://localhost:5000` to use the search engine.

## Project Structure

- `app.py`: Main Flask application
- `create_index.py`: Script to create the Whoosh search index
- `templates/`: HTML templates for the web interface
- `static/`: CSS, JavaScript, and other static files
- `index/`: Directory containing the Whoosh search index
- `transcripts/`: Directory containing episode transcripts (CSV and TXT formats)

## Contributing

Contributions to improve transcripts or searches are welcome! I know some of the transcriptions are incorrect, I'm going through the csvs to fix them over time. Please feel free to submit pull requests or open issues to discuss potential enhancements!

## Acknowledgments

- Thanks to Ezra Koenig and the entire Crisis Crew for making the show in the first place
- Transcriptions were completed by OpenAI's Whisper model
- Shoutout to Nick & Steph as well as TC Heads worldwide