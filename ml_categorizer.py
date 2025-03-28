import os
import numpy as np
import logging
from collections import defaultdict
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer

class FileClassifier:
    """Class for AI-powered file categorization."""
    
    def __init__(self):
        """Initialize the file classifier."""
        logging.debug("FileClassifier initialized")
        
        # Predefined categories based on file extensions
        self.extension_categories = {
            # Documents
            'pdf': 'Documents',
            'doc': 'Documents',
            'docx': 'Documents',
            'txt': 'Documents',
            'rtf': 'Documents',
            'odt': 'Documents',
            'md': 'Documents',
            
            # Spreadsheets
            'xls': 'Spreadsheets',
            'xlsx': 'Spreadsheets',
            'csv': 'Spreadsheets',
            'ods': 'Spreadsheets',
            
            # Presentations
            'ppt': 'Presentations',
            'pptx': 'Presentations',
            'odp': 'Presentations',
            
            # Images
            'jpg': 'Images',
            'jpeg': 'Images',
            'png': 'Images',
            'gif': 'Images',
            'bmp': 'Images',
            'svg': 'Images',
            'tiff': 'Images',
            'webp': 'Images',
            
            # Audio
            'mp3': 'Audio',
            'wav': 'Audio',
            'flac': 'Audio',
            'ogg': 'Audio',
            'aac': 'Audio',
            
            # Video
            'mp4': 'Video',
            'avi': 'Video',
            'mkv': 'Video',
            'mov': 'Video',
            'wmv': 'Video',
            'webm': 'Video',
            
            # Archives
            'zip': 'Archives',
            'rar': 'Archives',
            'tar': 'Archives',
            'gz': 'Archives',
            '7z': 'Archives',
            
            # Code
            'py': 'Code',
            'js': 'Code',
            'html': 'Code',
            'css': 'Code',
            'java': 'Code',
            'cpp': 'Code',
            'c': 'Code',
            'h': 'Code',
            'php': 'Code',
            'go': 'Code',
            'rb': 'Code',
            'rs': 'Code',
            'sh': 'Code',
            'json': 'Code',
            'xml': 'Code',
            'sql': 'Code',
            
            # Executables
            'exe': 'Executables',
            'msi': 'Executables',
            'app': 'Executables',
            'dll': 'Executables',
            'so': 'Executables',
            'bin': 'Executables',
            
            # System
            'sys': 'System',
            'ini': 'System',
            'log': 'System',
            'dat': 'System',
            'bak': 'System',
            'tmp': 'System',
            'config': 'System',
        }
        
        # Initialize ML model for filename-based categorization
        self.vectorizer = TfidfVectorizer(
            analyzer='char_wb',
            ngram_range=(2, 5),
            max_features=1000
        )
        
        self.kmeans = KMeans(
            n_clusters=10,
            random_state=42,
            n_init=10
        )
        
        self.model = Pipeline([
            ('vectorizer', self.vectorizer),
            ('kmeans', self.kmeans)
        ])
        
        self.trained = False
    
    def _extract_features(self, file_info):
        """
        Extract features from file information for classification.
        
        Args:
            file_info (dict): Dictionary containing file information
            
        Returns:
            list: List of features for classification
        """
        features = [
            file_info['name'],
            file_info['extension'],
            file_info['mime_type']
        ]
        return features
    
    def _train_model(self, files_info):
        """
        Train the ML model for filename-based categorization.
        
        Args:
            files_info (list): List of file information dictionaries
        """
        # Extract filenames for training
        filenames = [file_info['name'] for file_info in files_info]
        
        if len(filenames) < 10:  # Not enough data to train a meaningful model
            logging.warning("Not enough files to train a meaningful ML model")
            return
        
        try:
            # Train the model
            self.model.fit(filenames)
            self.trained = True
            logging.debug("ML model trained successfully")
        except Exception as e:
            logging.error(f"Error training ML model: {str(e)}")
    
    def categorize_files(self, files_info):
        """
        Categorize files based on their information.
        
        Args:
            files_info (list): List of file information dictionaries
            
        Returns:
            list: List of file information dictionaries with added categories
        """
        # First, try to categorize based on file extensions
        for file_info in files_info:
            ext = file_info['extension'].lower()
            if ext in self.extension_categories:
                file_info['category'] = self.extension_categories[ext]
            else:
                file_info['category'] = 'Other'
        
        # Count files by category
        category_counts = defaultdict(int)
        for file_info in files_info:
            category_counts[file_info['category']] += 1
        
        # For files in 'Other' category, try ML-based categorization
        uncategorized_files = [
            file_info for file_info in files_info
            if file_info['category'] == 'Other'
        ]
        
        if uncategorized_files:
            # Train model if we have enough data
            if len(files_info) >= 10:
                self._train_model(files_info)
            
            # If model is trained, use it to predict categories
            if self.trained:
                uncategorized_names = [file_info['name'] for file_info in uncategorized_files]
                try:
                    # Predict clusters
                    cluster_labels = self.model.predict(uncategorized_names)
                    
                    # Assign cluster-based categories
                    for i, file_info in enumerate(uncategorized_files):
                        cluster = cluster_labels[i]
                        file_info['category'] = f"Group {cluster + 1}"
                except Exception as e:
                    logging.error(f"Error predicting categories: {str(e)}")
        
        # Apply additional heuristics to refine categorization
        self._apply_categorization_heuristics(files_info)
        
        return files_info
    
    def _apply_categorization_heuristics(self, files_info):
        """
        Apply additional heuristics to refine file categorization.
        
        Args:
            files_info (list): List of file information dictionaries
        """
        for file_info in files_info:
            name = file_info['name'].lower()
            path = file_info['path'].lower()
            
            # Check for configuration files
            if (name.startswith('config') or 
                name.endswith('config') or 
                name.endswith('.cfg') or 
                name.endswith('.ini') or
                name.endswith('.conf')):
                file_info['category'] = 'Configuration'
            
            # Check for database files
            if (name.endswith('.db') or 
                name.endswith('.sqlite') or 
                name.endswith('.sqlite3') or
                name.endswith('.mdb')):
                file_info['category'] = 'Database'
            
            # Check for backup files
            if (name.endswith('.bak') or 
                name.endswith('.backup') or 
                name.endswith('~') or
                '.backup' in name):
                file_info['category'] = 'Backup'
            
            # Check for temporary files
            if (name.startswith('tmp') or 
                name.endswith('.tmp') or 
                'temp' in name or
                'cache' in name):
                file_info['category'] = 'Temporary'
            
            # Check for project files
            if ('project' in path or 
                'workspace' in path or
                '.git' in path):
                file_info['category'] = 'Project'
            
            # Check for font files
            if (name.endswith('.ttf') or 
                name.endswith('.otf') or
                name.endswith('.woff') or
                name.endswith('.woff2')):
                file_info['category'] = 'Fonts'
