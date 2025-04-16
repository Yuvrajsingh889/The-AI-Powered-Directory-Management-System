import os
import json
import logging
from collections import defaultdict, Counter
from ai_insights import AIInsights

class DirectoryVisualizer:
    """Class for generating directory visualization data."""
    
    def __init__(self):
        """Initialize the directory visualizer."""
        logging.debug("DirectoryVisualizer initialized")
        self.ai_insights = AIInsights()
    
    def generate_visualization(self, files_data):
        """
        Generate visualization data from file information.
        
        Args:
            files_data (list): List of file information dictionaries
            
        Returns:
            dict: Visualization data for different chart types
        """
        if not files_data:
            return {'error': 'No file data available for visualization'}
        
        try:
            # Generate different visualization datasets
            category_distribution = self._generate_category_distribution(files_data)
            size_distribution = self._generate_size_distribution(files_data)
            extension_distribution = self._generate_extension_distribution(files_data)
            directory_tree = self._generate_directory_tree(files_data)
            time_distribution = self._generate_time_distribution(files_data)
            
            # Generate AI-powered insights
            ai_insights = self.ai_insights.generate_file_insights(files_data)
            
            visualization_data = {
                'category_distribution': category_distribution,
                'size_distribution': size_distribution,
                'extension_distribution': extension_distribution,
                'directory_tree': directory_tree,
                'time_distribution': time_distribution,
                'ai_insights': ai_insights
            }
            
            return visualization_data
            
        except Exception as e:
            logging.error(f"Error generating visualization data: {str(e)}")
            raise
    
    def _generate_category_distribution(self, files_data):
        """
        Generate category distribution data for pie/bar charts.
        
        Args:
            files_data (list): List of file information dictionaries
            
        Returns:
            dict: Category distribution data
        """
        category_counts = Counter()
        category_sizes = defaultdict(int)
        
        for file_info in files_data:
            category = file_info.get('category', 'Other')
            category_counts[category] += 1
            category_sizes[category] += file_info['size_bytes']
        
        # Prepare data for charts
        labels = list(category_counts.keys())
        count_data = list(category_counts.values())
        size_data = [category_sizes[category] for category in labels]
        
        return {
            'labels': labels,
            'counts': count_data,
            'sizes': size_data,
            'total_files': sum(count_data),
            'total_size': sum(size_data)
        }
    
    def _generate_size_distribution(self, files_data):
        """
        Generate file size distribution data for histograms.
        
        Args:
            files_data (list): List of file information dictionaries
            
        Returns:
            dict: Size distribution data
        """
        # Define size buckets (in bytes)
        size_buckets = [
            (0, 1024),                # 0-1 KB
            (1024, 10 * 1024),        # 1-10 KB
            (10 * 1024, 100 * 1024),  # 10-100 KB
            (100 * 1024, 1024 * 1024),  # 100 KB - 1 MB
            (1024 * 1024, 10 * 1024 * 1024),  # 1-10 MB
            (10 * 1024 * 1024, 100 * 1024 * 1024),  # 10-100 MB
            (100 * 1024 * 1024, float('inf'))  # >100 MB
        ]
        
        bucket_labels = [
            '0-1 KB',
            '1-10 KB',
            '10-100 KB',
            '100 KB - 1 MB',
            '1-10 MB',
            '10-100 MB',
            '>100 MB'
        ]
        
        bucket_counts = [0] * len(size_buckets)
        
        for file_info in files_data:
            size = file_info['size_bytes']
            for i, (min_size, max_size) in enumerate(size_buckets):
                if min_size <= size < max_size:
                    bucket_counts[i] += 1
                    break
        
        return {
            'labels': bucket_labels,
            'counts': bucket_counts
        }
    
    def _generate_extension_distribution(self, files_data):
        """
        Generate file extension distribution data.
        
        Args:
            files_data (list): List of file information dictionaries
            
        Returns:
            dict: Extension distribution data
        """
        extension_counts = Counter()
        
        for file_info in files_data:
            ext = file_info.get('extension', '').lower()
            if not ext:
                ext = 'no extension'
            extension_counts[ext] += 1
        
        # Get top 10 extensions
        top_extensions = extension_counts.most_common(10)
        
        labels = [ext for ext, count in top_extensions]
        counts = [count for ext, count in top_extensions]
        
        return {
            'labels': labels,
            'counts': counts
        }
    
    def _generate_directory_tree(self, files_data):
        """
        Generate directory tree structure for treemap/sunburst charts.
        
        Args:
            files_data (list): List of file information dictionaries
            
        Returns:
            dict: Directory tree structure
        """
        tree = {
            'name': 'root',
            'children': []
        }
        
        # Group files by directory
        dir_files = defaultdict(list)
        
        for file_info in files_data:
            dir_path = os.path.dirname(file_info['relative_path'])
            dir_files[dir_path].append(file_info)
        
        # Build tree recursively
        for dir_path, files in dir_files.items():
            path_parts = dir_path.split(os.sep)
            
            # Skip empty path (root directory)
            if path_parts[0] == '':
                path_parts = path_parts[1:]
            
            current_level = tree
            
            # Navigate through directory structure
            for part in path_parts:
                if not part:  # Skip empty parts
                    continue
                    
                # Check if this directory already exists in the current level
                child = next((c for c in current_level['children'] if c['name'] == part and 'children' in c), None)
                
                if child is None:
                    # Create new directory node
                    child = {
                        'name': part,
                        'children': []
                    }
                    current_level['children'].append(child)
                
                current_level = child
            
            # Add files as leaf nodes
            for file_info in files:
                file_node = {
                    'name': file_info['name'],
                    'size': file_info['size_bytes'],
                    'category': file_info['category']
                }
                current_level['children'].append(file_node)
        
        return tree
    
    def _generate_time_distribution(self, files_data):
        """
        Generate file modification time distribution data.
        
        Args:
            files_data (list): List of file information dictionaries
            
        Returns:
            dict: Time distribution data
        """
        # Group files by modification month
        months = defaultdict(int)
        
        for file_info in files_data:
            mod_date = file_info['modified']
            month_key = f"{mod_date.year}-{mod_date.month:02d}"
            months[month_key] += 1
        
        # Sort months chronologically
        sorted_months = sorted(months.items())
        
        labels = [month for month, _ in sorted_months]
        counts = [count for _, count in sorted_months]
        
        return {
            'labels': labels,
            'counts': counts
        }
