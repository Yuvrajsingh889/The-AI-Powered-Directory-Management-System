import os
import logging
import shutil
from werkzeug.utils import secure_filename

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, send_file

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET") or "development_key"

# Temporarily disable database for simplicity
# We'll focus on file handling without database integration

# File upload configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'py', 'js', 'html', 'css', 'json', 'xml', 'csv', 'doc', 'docx', 'xls', 'xlsx', 'zip'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max

# Import modules after app initialization to avoid circular imports
from file_scanner import FileScanner
from ml_categorizer import FileClassifier
from data_visualizer import DirectoryVisualizer

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
        
        # Organize files into category folders (if the directory is uploads)
        if directory_path == UPLOAD_FOLDER:
            num_categories = organize_files_into_categories(categorized_files)
            organization_message = f" and organized into {num_categories} categories"
        else:
            organization_message = ""
        
        # Save scan results to session for visualization
        session['last_scan_results'] = categorized_files
        
        return jsonify({
            'status': 'success',
            'message': f'Successfully scanned {len(categorized_files)} files{organization_message}',
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
    """API endpoint to search through scanned files using NLP techniques."""
    data = request.json
    query = data.get('query', '')
    filters = data.get('filters', {})
    
    # Log the search request
    logging.info(f"Search request received - Query: '{query}', Filters: {filters}")
    
    if not query and not filters:
        logging.warning("Search request with no query or filters")
        return jsonify({'error': 'No search query or filters provided'}), 400
    
    try:
        # Get the last scan results from session
        files_data = session.get('last_scan_results', [])
        
        if not files_data:
            logging.warning("Search request with no scan data available")
            return jsonify({'error': 'No scan data available. Please scan a directory first.'}), 400
        
        logging.info(f"Searching through {len(files_data)} files")
        
        # Filter files based on search query and filters
        filtered_files = file_scanner.search_files(files_data, query, filters)
        
        logging.info(f"Search completed successfully - Found {len(filtered_files)} matching files")
        
        return jsonify({
            'status': 'success',
            'results': filtered_files,
            'count': len(filtered_files),
            'search_type': 'nlp' if query else 'filter'  # Indicate search method
        })
        
    except Exception as e:
        logging.error(f"Error searching files: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
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
        
@app.route('/api/delete-file', methods=['POST'])
def delete_file():
    """API endpoint to delete a file."""
    data = request.json
    file_path = data.get('path', '')
    
    if not file_path:
        return jsonify({'error': 'No file path provided'}), 400
    
    # Security check - make sure the file is within the upload folder
    if not file_path.startswith(UPLOAD_FOLDER):
        return jsonify({'error': 'Cannot delete files outside the upload directory'}), 403
    
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
            
        # Delete the file
        os.remove(file_path)
        logging.info(f"Deleted file: {file_path}")
        
        # Return success
        return jsonify({
            'status': 'success',
            'message': 'File deleted successfully'
        })
        
    except Exception as e:
        logging.error(f"Error deleting file: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/view_file')
def view_file():
    """Endpoint to view or download a file's contents."""
    file_path = request.args.get('path')
    
    if not file_path or not os.path.exists(file_path):
        return "File not found", 404
        
    try:
        # Get file extension
        _, file_extension = os.path.splitext(file_path)
        file_extension = file_extension.lower().lstrip('.')
        
        # Get MIME type
        mime_type = 'application/octet-stream'  # Default
        
        # Map common extensions to MIME types
        mime_map = {
            'pdf': 'application/pdf',
            'txt': 'text/plain',
            'html': 'text/html',
            'htm': 'text/html',
            'css': 'text/css',
            'js': 'text/javascript',
            'json': 'application/json',
            'xml': 'application/xml',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'svg': 'image/svg+xml',
            'py': 'text/plain',
            'c': 'text/plain',
            'cpp': 'text/plain',
            'java': 'text/plain',
            'md': 'text/plain'
        }
        
        if file_extension in mime_map:
            mime_type = mime_map[file_extension]
        
        # For safety, avoid opening very large files for viewing
        # Instead, send them as attachments
        file_size = os.path.getsize(file_path)
        
        # For binary files or large text files, send as attachment
        if (not mime_type.startswith('text/') and not mime_type.startswith('image/') and not mime_type == 'application/pdf') or file_size > 5 * 1024 * 1024:  # > 5MB
            return send_file(file_path, as_attachment=True)
        
        # Otherwise, display in browser
        return send_file(file_path, mimetype=mime_type)
    except Exception as e:
        logging.error(f"Error viewing file: {str(e)}")
        return str(e), 500

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors."""
    return render_template('index.html'), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors."""
    logging.error(f"Server error: {str(e)}")
    return jsonify({'error': 'An internal server error occurred'}), 500

def allowed_file(filename):
    """Check if file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def organize_files_into_categories(files_info):
    """
    Organize files into category folders based on their classification.
    
    Args:
        files_info (list): List of file information dictionaries with categories
    """
    # Dictionary to keep track of which categories have been created
    category_folders = {}
    
    # Base directory is the uploads folder
    base_dir = UPLOAD_FOLDER
    
    # Get unique categories from files
    categories = set(file_info['category'] for file_info in files_info)
    
    # Create category folders if they don't exist
    for category in categories:
        # Replace spaces in folder name with underscores and sanitize
        category_folder_name = secure_filename(category)
        category_path = os.path.join(base_dir, category_folder_name)
        
        if not os.path.exists(category_path):
            os.makedirs(category_path)
            logging.info(f"Created category folder: {category_path}")
        
        category_folders[category] = category_path
    
    # Move files to their respective category folders
    for file_info in files_info:
        # Get the current file location
        src_path = file_info['path']
        
        # Skip files that don't exist (might have been moved already or deleted)
        if not os.path.exists(src_path):
            logging.warning(f"File not found: {src_path}")
            continue
        
        # Get the category folder
        category = file_info['category']
        category_path = category_folders.get(category)
        
        if not category_path:
            logging.warning(f"Category path not found for: {category}")
            continue
        
        # Get the filename from the path
        filename = os.path.basename(src_path)
        
        # Create the destination path
        dst_path = os.path.join(category_path, filename)
        
        # Handle the case where the destination file already exists
        counter = 1
        base_filename, ext = os.path.splitext(filename)
        while os.path.exists(dst_path):
            new_filename = f"{base_filename}_{counter}{ext}"
            dst_path = os.path.join(category_path, new_filename)
            counter += 1
        
        # Move the file
        try:
            shutil.move(src_path, dst_path)
            # Update the file path in the file_info
            file_info['path'] = dst_path
            logging.info(f"Moved file to category folder: {dst_path}")
        except Exception as e:
            logging.error(f"Error moving file {src_path} to {dst_path}: {str(e)}")
            
    # Return the number of categories created
    return len(category_folders)

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    """Handle file uploads and process them with AI."""
    if request.method == 'GET':
        return render_template('upload.html')
    
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'files[]' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        
        files = request.files.getlist('files[]')
        
        # If user submits an empty form
        if not files or files[0].filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
        
        # Create upload directory if it doesn't exist
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)
            
        # Check if speed mode is enabled (default is now False for safer uploads)
        speed_mode = request.form.get('speed_mode') == '1'
        
        # Log which mode is being used
        if speed_mode:
            logging.info("Using FAST upload mode (no duplicate checking)")
        else:
            logging.info("Using SAFE upload mode (with duplicate checking)")
        
        # Save all valid files
        saved_files = []
        duplicates = []
        
        # If not using speed mode, we'll need to build a dictionary of existing files
        existing_file_sizes = {}  # Fast lookup by file size
        
        if not speed_mode and os.path.exists(UPLOAD_FOLDER):
            # Only scan directory if we're checking for duplicates
            logging.info("Scanning for existing files to check duplicates...")
            for root, dirs, files_in_dir in os.walk(UPLOAD_FOLDER):
                for file_name in files_in_dir:
                    try:
                        file_path = os.path.join(root, file_name)
                        file_size = os.path.getsize(file_path)
                        
                        # Index by size for quick lookup
                        if file_size not in existing_file_sizes:
                            existing_file_sizes[file_size] = []
                        existing_file_sizes[file_size].append({
                            'name': file_name,
                            'path': file_path,
                            'size': file_size
                        })
                    except (IOError, OSError):
                        # Skip files that can't be accessed
                        continue
        
        # Process each uploaded file
        for file in files:
            if file and allowed_file(file.filename):
                original_filename = file.filename
                filename = secure_filename(original_filename)
                
                if speed_mode:
                    # FAST MODE: Save directly without duplicate checking for maximum speed
                    counter = 1
                    base_filename, ext = os.path.splitext(filename)
                    file_path = os.path.join(UPLOAD_FOLDER, filename)
                    
                    # If the file already exists, add a counter to make it unique
                    while os.path.exists(file_path):
                        filename = f"{base_filename}_{counter}{ext}"
                        file_path = os.path.join(UPLOAD_FOLDER, filename)
                        counter += 1
                    
                    # Save directly (no temp file or checks)
                    file.save(file_path)
                    saved_files.append(file_path)
                    
                    # For now, we'll skip database storage and just log the file info
                    file_size = os.path.getsize(file_path)
                    logging.info(f"Saved file: {filename} (original: {original_filename}) - {file_size} bytes")
                
                else:
                    # SAFE MODE: Check for duplicates (slower but safer)
                    # First save to temp location
                    temp_path = os.path.join('/tmp', filename)
                    file.save(temp_path)
                    file_size = os.path.getsize(temp_path)
                    
                    # Fast comparison - only check files with identical size
                    is_duplicate = False
                    potential_duplicates = existing_file_sizes.get(file_size, [])
                    
                    if potential_duplicates:
                        # Only calculate hash if there are potential size-based duplicates
                        import hashlib
                        
                        # Ultra-fast partial hashing (8KB from start and 8KB from end if file is large enough)
                        SAMPLE_SIZE = 8192
                        file_hash = hashlib.md5()
                        
                        with open(temp_path, 'rb') as f:
                            start_chunk = f.read(SAMPLE_SIZE)
                            file_hash.update(start_chunk)
                            
                            # Only check end chunk if file is big enough
                            f.seek(0, os.SEEK_END)
                            file_length = f.tell()
                            if file_length > SAMPLE_SIZE * 2:
                                f.seek(-SAMPLE_SIZE, os.SEEK_END)
                                end_chunk = f.read(SAMPLE_SIZE)
                                file_hash.update(end_chunk)
                        
                        file_digest = file_hash.hexdigest()
                        
                        # Compare with potential duplicates
                        for existing_file in potential_duplicates:
                            try:
                                existing_hash = hashlib.md5()
                                with open(existing_file['path'], 'rb') as f:
                                    start_chunk = f.read(SAMPLE_SIZE)
                                    existing_hash.update(start_chunk)
                                    
                                    f.seek(0, os.SEEK_END)
                                    file_length = f.tell()
                                    if file_length > SAMPLE_SIZE * 2:
                                        f.seek(-SAMPLE_SIZE, os.SEEK_END)
                                        end_chunk = f.read(SAMPLE_SIZE)
                                        existing_hash.update(end_chunk)
                                
                                existing_digest = existing_hash.hexdigest()
                                
                                if file_digest == existing_digest:
                                    is_duplicate = True
                                    duplicates.append({
                                        'original_name': original_filename,
                                        'existing_path': existing_file['path']
                                    })
                                    break
                            except (IOError, OSError):
                                continue
                    
                    if is_duplicate:
                        # Skip duplicate file
                        os.remove(temp_path)
                        continue
                    
                    # Not a duplicate, save it
                    counter = 1
                    base_filename, ext = os.path.splitext(filename)
                    file_path = os.path.join(UPLOAD_FOLDER, filename)
                    
                    # If the file already exists, add a counter to make it unique
                    while os.path.exists(file_path):
                        filename = f"{base_filename}_{counter}{ext}"
                        file_path = os.path.join(UPLOAD_FOLDER, filename)
                        counter += 1
                    
                    # Move from temp to final location
                    shutil.move(temp_path, file_path)
                    saved_files.append(file_path)
                    
                    # Log file info
                    logging.info(f"Saved file: {filename} (original: {original_filename}) - {file_size} bytes")
        
        if not saved_files:
            flash('No valid files uploaded', 'warning')
            return redirect(request.url)
        
        try:
            # Scan the upload directory
            files_info = file_scanner.scan_directory(UPLOAD_FOLDER)
            
            # Use ML to categorize files
            categorized_files = file_classifier.categorize_files(files_info)
            
            # Organize files into category folders
            num_categories = organize_files_into_categories(categorized_files)
            
            # Save scan results to session for visualization
            session['last_scan_results'] = categorized_files
            
            # Add duplicate warning if any duplicates were found (when not in speed mode)
            if not speed_mode and duplicates:
                duplicate_msg = f"Skipped {len(duplicates)} duplicate file(s): "
                duplicate_names = [d['original_name'] for d in duplicates]
                duplicate_msg += ", ".join(duplicate_names)
                flash(duplicate_msg, 'warning')
            
            # Create success message
            success_msg = f'Successfully uploaded and analyzed {len(saved_files)} files and organized into {num_categories} categories'
            if not speed_mode and duplicates:
                success_msg += f'. {len(duplicates)} duplicate file(s) were skipped'
            
            flash(success_msg, 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            logging.error(f"Error processing uploaded files: {str(e)}")
            flash(f'Error processing files: {str(e)}', 'danger')
            return redirect(request.url)
