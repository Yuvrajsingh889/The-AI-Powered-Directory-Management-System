import os
import stat
import time
import logging
import mimetypes
import numpy as np
from datetime import datetime
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class FileScanner:
    """Class for scanning directories and extracting file information."""
    
    def __init__(self):
        """Initialize the file scanner."""
        logging.debug("FileScanner initialized")
        mimetypes.init()
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words='english',
            ngram_range=(1, 2),  # Include both unigrams and bigrams
            min_df=1,
            max_df=0.9
        )
    
    def scan_directory(self, directory_path):
        """
        Scan a directory recursively and extract file information.
        
        Args:
            directory_path (str): Path to the directory to scan
            
        Returns:
            list: List of dictionaries containing file information
        """
        if not os.path.isdir(directory_path):
            raise ValueError(f"'{directory_path}' is not a valid directory")
        
        files_info = []
        
        try:
            for root, dirs, files in os.walk(directory_path):
                # Skip hidden directories
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                for file in files:
                    # Skip hidden files
                    if file.startswith('.'):
                        continue
                    
                    file_path = os.path.join(root, file)
                    try:
                        file_info = self._get_file_info(file_path, root, directory_path)
                        files_info.append(file_info)
                    except (PermissionError, FileNotFoundError) as e:
                        logging.warning(f"Could not access file {file_path}: {e}")
        
        except PermissionError:
            raise PermissionError(f"Permission denied when accessing directory '{directory_path}'")
        
        logging.debug(f"Scanned {len(files_info)} files in {directory_path}")
        return files_info
    
    def _get_file_info(self, file_path, root_dir, base_dir):
        """
        Extract information about a file.
        
        Args:
            file_path (str): Path to the file
            root_dir (str): Current directory being scanned
            base_dir (str): Base directory of the scan
            
        Returns:
            dict: Dictionary containing file information
        """
        filename = os.path.basename(file_path)
        stat_info = os.stat(file_path)
        
        # Extract file extension
        _, ext = os.path.splitext(filename)
        ext = ext.lower()[1:] if ext else ""
        
        # Get file size
        size_bytes = stat_info.st_size
        
        # Format size for display
        size_display = self._format_file_size(size_bytes)
        
        # Get file times
        created_time = datetime.fromtimestamp(stat_info.st_ctime)
        modified_time = datetime.fromtimestamp(stat_info.st_mtime)
        accessed_time = datetime.fromtimestamp(stat_info.st_atime)
        
        # Get mime type
        mime_type, encoding = mimetypes.guess_type(file_path)
        mime_type = mime_type if mime_type else "application/octet-stream"
        
        # Calculate relative path from base directory
        rel_path = os.path.relpath(file_path, base_dir)
        
        # Determine directory depth
        depth = len(rel_path.split(os.sep)) - 1
        
        return {
            'name': filename,
            'path': file_path,
            'relative_path': rel_path,
            'directory': root_dir,
            'extension': ext,
            'size_bytes': size_bytes,
            'size_display': size_display,
            'created': created_time,
            'modified': modified_time,
            'accessed': accessed_time,
            'mime_type': mime_type,
            'depth': depth,
            'is_executable': bool(stat_info.st_mode & stat.S_IXUSR),
            'is_readable': bool(stat_info.st_mode & stat.S_IRUSR),
            'is_writable': bool(stat_info.st_mode & stat.S_IWUSR),
            'category': None  # Will be filled by the ML categorizer
        }
    
    def _format_file_size(self, size_bytes):
        """
        Format file size in human-readable format.
        
        Args:
            size_bytes (int): File size in bytes
            
        Returns:
            str: Formatted file size (e.g., '1.23 MB')
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
    
    def get_file_metadata(self, file_path):
        """
        Get detailed metadata for a specific file.
        
        Args:
            file_path (str): Path to the file
            
        Returns:
            dict: Dictionary containing detailed file metadata
        """
        if not os.path.isfile(file_path):
            raise ValueError(f"'{file_path}' is not a valid file")
        
        try:
            basic_info = self._get_file_info(file_path, os.path.dirname(file_path), os.path.dirname(file_path))
            
            # Add additional metadata for specific file types
            mime_type = basic_info['mime_type']
            additional_metadata = {}
            
            # TODO: Add file-specific metadata extraction based on mime type
            # This would be the place to add specialized metadata extraction
            # for different file types (images, documents, audio, etc.)
            
            # Merge basic info with additional metadata
            metadata = {**basic_info, **additional_metadata}
            return metadata
            
        except Exception as e:
            logging.error(f"Error getting metadata for {file_path}: {str(e)}")
            raise
    
    def search_files(self, files_data, query="", filters=None):
        """
        Search through files based on query and filters using NLP techniques.
        
        Args:
            files_data (list): List of file information dictionaries
            query (str): Search query to match against filenames and paths
            filters (dict): Filters to apply (e.g., extension, size range, category)
            
        Returns:
            list: Filtered list of file information dictionaries
        """
        if filters is None:
            filters = {}
        
        # Apply filters first
        filtered_files = []
        for file_info in files_data:
            # Apply filters
            if 'extensions' in filters and filters['extensions']:
                if file_info['extension'] not in filters['extensions']:
                    continue
                    
            if 'categories' in filters and filters['categories']:
                if file_info['category'] not in filters['categories']:
                    continue
                    
            if 'min_size' in filters and filters['min_size'] is not None:
                if file_info['size_bytes'] < filters['min_size']:
                    continue
                    
            if 'max_size' in filters and filters['max_size'] is not None:
                if file_info['size_bytes'] > filters['max_size']:
                    continue
                    
            if 'modified_after' in filters and filters['modified_after'] is not None:
                if file_info['modified'] < filters['modified_after']:
                    continue
                    
            if 'modified_before' in filters and filters['modified_before'] is not None:
                if file_info['modified'] > filters['modified_before']:
                    continue
            
            # If file passed all filters, add it to filtered list
            filtered_files.append(file_info)
        
        # If no query, return all filtered files
        if not query or len(filtered_files) == 0:
            return filtered_files
        
        # Prepare file documents for NLP processing
        file_documents = []
        for file_info in filtered_files:
            # Create a document that includes name, path, and category (if available)
            doc = file_info['name'] + " " + file_info['path']
            if file_info['category']:
                doc += " " + file_info['category']
                
            # Include some useful metadata as words
            if file_info['extension']:
                doc += " extension:" + file_info['extension']
                
            file_documents.append(doc)
        
        # If we have a simple keyword query, handle it specially
        if len(query.split()) == 1:
            query_lower = query.lower()
            exact_matches = []
            partial_matches = []
            
            for i, file_info in enumerate(filtered_files):
                # Check for exact matches in filename
                if query_lower == file_info['name'].lower():
                    exact_matches.append(file_info)
                # Check for filename starts with query
                elif file_info['name'].lower().startswith(query_lower):
                    exact_matches.append(file_info)
                # Check for partial matches in filename or path
                elif query_lower in file_info['name'].lower() or query_lower in file_info['path'].lower():
                    partial_matches.append(file_info)
            
            # If we have exact matches, prioritize them
            if exact_matches:
                return exact_matches + partial_matches
            elif partial_matches:
                return partial_matches
        
        try:
            # Use NLP for more complex queries
            # Fit the vectorizer on documents
            tfidf_matrix = self.vectorizer.fit_transform(file_documents)
            
            # Vectorize the query
            query_vector = self.vectorizer.transform([query])
            
            # Calculate similarity between query and documents
            similarities = cosine_similarity(query_vector, tfidf_matrix).flatten()
            
            # Get indices sorted by similarity score (descending)
            ranked_indices = np.argsort(-similarities)
            
            # Filter results by similarity threshold
            similarity_threshold = 0.01  # Adjust as needed
            result = []
            
            for idx in ranked_indices:
                similarity = similarities[idx]
                if similarity >= similarity_threshold:
                    result.append(filtered_files[idx])
            
            # Fallback to basic search if NLP returns no results
            if not result and filtered_files:
                logging.info("NLP search returned no results, falling back to basic search")
                query_lower = query.lower()
                for file_info in filtered_files:
                    if (query_lower in file_info['name'].lower() or 
                        query_lower in file_info['path'].lower()):
                        result.append(file_info)
            
            return result
            
        except Exception as e:
            logging.error(f"Error in NLP search: {str(e)}. Falling back to basic search.")
            # Fallback to basic search if NLP fails
            result = []
            query_lower = query.lower()
            
            for file_info in filtered_files:
                if (query_lower in file_info['name'].lower() or 
                    query_lower in file_info['path'].lower()):
                    result.append(file_info)
            
            return result
