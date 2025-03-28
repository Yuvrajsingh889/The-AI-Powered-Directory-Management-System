import os
import logging

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")

# Set up database connection
database_url = os.environ.get("DATABASE_URL")
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = database_url or "sqlite:///instance/directory_manager.db"
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# initialize the app with the extension
db.init_app(app)

# Import modules after app initialization to avoid circular imports
from file_scanner import FileScanner
from ml_categorizer import FileClassifier
from data_visualizer import DirectoryVisualizer
import models

# Create tables if they don't exist
with app.app_context():
    db.create_all()

# Initialize components
file_scanner = FileScanner()
file_classifier = FileClassifier()
directory_visualizer = DirectoryVisualizer()

@app.route('/')
def index():
    """Render the landing page."""
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """Render the main dashboard page."""
    return render_template('dashboard.html')

@app.route('/api/scan', methods=['POST'])
def scan_directory():
    """API endpoint to scan a directory."""
    data = request.json
    directory_path = data.get('path', '')
    
    if not directory_path:
        return jsonify({'error': 'No directory path provided'}), 400
    
    try:
        # Scan directory and get file information
        files_info = file_scanner.scan_directory(directory_path)
        
        # Use ML to categorize files
        categorized_files = file_classifier.categorize_files(files_info)
        
        # Save scan results to session for visualization
        session['last_scan_results'] = categorized_files
        
        return jsonify({
            'status': 'success',
            'message': f'Successfully scanned {len(categorized_files)} files',
            'files': categorized_files
        })
        
    except Exception as e:
        logging.error(f"Error scanning directory: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/visualize', methods=['GET'])
def visualize_directory():
    """API endpoint to get directory visualization data."""
    try:
        # Get the last scan results from session
        files_data = session.get('last_scan_results', [])
        
        if not files_data:
            return jsonify({'error': 'No scan data available. Please scan a directory first.'}), 400
            
        # Generate visualization data
        visualization_data = directory_visualizer.generate_visualization(files_data)
        
        return jsonify({
            'status': 'success',
            'visualization': visualization_data
        })
        
    except Exception as e:
        logging.error(f"Error generating visualization: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/search', methods=['POST'])
def search_files():
    """API endpoint to search through scanned files."""
    data = request.json
    query = data.get('query', '')
    filters = data.get('filters', {})
    
    if not query and not filters:
        return jsonify({'error': 'No search query or filters provided'}), 400
    
    try:
        # Get the last scan results from session
        files_data = session.get('last_scan_results', [])
        
        if not files_data:
            return jsonify({'error': 'No scan data available. Please scan a directory first.'}), 400
        
        # Filter files based on search query and filters
        filtered_files = file_scanner.search_files(files_data, query, filters)
        
        return jsonify({
            'status': 'success',
            'results': filtered_files,
            'count': len(filtered_files)
        })
        
    except Exception as e:
        logging.error(f"Error searching files: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/file-metadata', methods=['POST'])
def get_file_metadata():
    """API endpoint to get detailed metadata for a specific file."""
    data = request.json
    file_path = data.get('path', '')
    
    if not file_path:
        return jsonify({'error': 'No file path provided'}), 400
    
    try:
        # Get detailed metadata for the file
        metadata = file_scanner.get_file_metadata(file_path)
        
        return jsonify({
            'status': 'success',
            'metadata': metadata
        })
        
    except Exception as e:
        logging.error(f"Error retrieving file metadata: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors."""
    return render_template('index.html'), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors."""
    logging.error(f"Server error: {str(e)}")
    return jsonify({'error': 'An internal server error occurred'}), 500

