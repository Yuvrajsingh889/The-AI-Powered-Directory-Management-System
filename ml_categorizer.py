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
        
        # Academic categories patterns for content-based classification
        self.academic_patterns = {
            'Engineering_Drawing': [
                'drawing', 'engineering', 'mechanical', 'cad', 'autocad', 'projection', 
                'dimension', 'blueprint', 'technical drawing', 'schematic', 'isometric',
                'orthographic', 'assembly', 'drafting', 'design', 'component'
            ],
            'Mathematics': [
                'math', 'equation', 'calculus', 'algebra', 'geometry', 'theorem', 
                'function', 'statistical', 'statistics', 'probability', 'mathematical',
                'formula', 'derivative', 'integral', 'matrix', 'vector', 'differential'
            ],
            'Physics': [
                'physics', 'mechanics', 'dynamics', 'kinematics', 'force', 'energy',
                'thermodynamics', 'electricity', 'magnetism', 'quantum', 'relativity',
                'fluid dynamics', 'optics', 'wave', 'particle'
            ],
            'Chemistry': [
                'chemistry', 'chemical', 'molecule', 'atom', 'compound', 'reaction',
                'organic', 'inorganic', 'solution', 'acid', 'base', 'element', 'periodic',
                'biochemistry', 'polymer'
            ],
            'Computer_Science': [
                'algorithm', 'data structure', 'programming', 'software', 'database',
                'network', 'artificial intelligence', 'machine learning', 'computer',
                'operating system', 'security', 'web', 'cloud computing'
            ]
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
                
        # Process documents category to identify academic subjects
        self._identify_academic_documents(files_info)
                
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
        
        # Group similar files better - specifically for academic documents
        self._group_similar_files(files_info)
        
        return files_info
        
    def _identify_academic_documents(self, files_info):
        """
        Identify academic documents by analyzing filenames and paths.
        
        Args:
            files_info (list): List of file information dictionaries
        """
        for file_info in files_info:
            # Only process document files
            if file_info['category'] not in ['Documents', 'Other']:
                continue
                
            name = file_info['name'].lower()
            path = file_info['path'].lower()
            
            # Check against academic patterns to categorize by subject
            for subject, keywords in self.academic_patterns.items():
                for keyword in keywords:
                    if keyword.lower() in name or keyword.lower() in path:
                        file_info['category'] = subject
                        break
                        
    def _group_similar_files(self, files_info):
        """
        Group similar files together by analyzing patterns in their names and paths.
        
        Args:
            files_info (list): List of file information dictionaries
        """
        # Group files with very similar names together
        # This handles files that are part of the same series or set
        name_groups = defaultdict(list)
        
        # First pass - group by common name prefixes
        for file_info in files_info:
            name = file_info['name'].lower()
            # Remove any numbers and common separators to find base name
            base_name = re.sub(r'[0-9_\-\.\s]+', '', name)
            if len(base_name) > 3:  # Only group if base name is meaningful
                name_groups[base_name].append(file_info)
        
        # For each group with multiple files, assign them the same category
        for base_name, group in name_groups.items():
            if len(group) >= 2:
                # For academic files, check if most files in group have the same category
                categories = [f['category'] for f in group]
                most_common_category = max(set(categories), key=categories.count)
                
                # Only apply if most_common_category is a specific academic category
                if most_common_category in self.academic_patterns:
                    # Apply the most common category to all files in this group
                    for file_info in group:
                        file_info['category'] = most_common_category
    
    def _apply_categorization_heuristics(self, files_info):
        """
        Apply additional heuristics to refine file categorization.
        
        Args:
            files_info (list): List of file information dictionaries
        """
        for file_info in files_info:
            name = file_info['name'].lower()
            path = file_info['path'].lower()
            
            # Academic file classification with higher specificity
            
            # Engineering Drawing specific patterns
            if (file_info['category'] == 'Documents' and 
                ('drawing' in name or 'projection' in name or 
                 'mechanical' in name or 'engineering' in name or
                 'cad' in name or 'technical' in name or
                 'blueprint' in name or 'schematic' in name or
                 'orthographic' in name or 'isometric' in name)):
                file_info['category'] = 'Engineering_Drawing'
                continue  # Skip further checks once categorized
            
            # Mathematics specific patterns
            if (file_info['category'] == 'Documents' and 
                ('math' in name or 'calculus' in name or 
                 'algebra' in name or 'equation' in name or
                 'geometry' in name or 'theorem' in name or
                 'formula' in name or 'statistical' in name)):
                file_info['category'] = 'Mathematics'
                continue  # Skip further checks once categorized
                
            # Physics specific patterns
            if (file_info['category'] == 'Documents' and 
                ('physics' in name or 'force' in name or 
                 'energy' in name or 'mechanics' in name or
                 'dynamics' in name or 'kinematics' in name)):
                file_info['category'] = 'Physics'
                continue  # Skip further checks once categorized
                
            # Chemistry specific patterns
            if (file_info['category'] == 'Documents' and 
                ('chemistry' in name or 'molecule' in name or 
                 'chemical' in name or 'compound' in name or
                 'reaction' in name or 'organic' in name)):
                file_info['category'] = 'Chemistry'
                continue  # Skip further checks once categorized
                
            # Computer Science specific patterns
            if (file_info['category'] == 'Documents' and 
                ('algorithm' in name or 'data structure' in name or 
                 'programming' in name or 'database' in name or
                 'software' in name or 'network' in name)):
                file_info['category'] = 'Computer_Science'
                continue  # Skip further checks once categorized
            
            # General system files classification
            
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
