import os
import logging
import json
import re
from collections import defaultdict
from datetime import datetime
import numpy as np

# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
from openai import OpenAI

# Initialize the OpenAI client with error handling
api_key = os.environ.get("OPENAI_API_KEY", "")
if not api_key or "https://" in api_key:  # API key might be improperly formatted
    logging.warning("Invalid or missing OpenAI API key")
    openai_client = None
else:
    try:
        openai_client = OpenAI(api_key=api_key)
    except Exception as e:
        logging.error(f"Error initializing OpenAI client: {str(e)}")
        openai_client = None

class AIInsights:
    """Class for generating AI-powered insights about files."""
    
    def __init__(self):
        """Initialize the AI insights module."""
        logging.debug("AIInsights initialized")
    
    def generate_file_insights(self, files_data):
        """
        Generate AI-powered insights about files.
        
        Args:
            files_data (list): List of file information dictionaries
            
        Returns:
            dict: AI insights data
        """
        if not files_data:
            return {'error': 'No file data available for analysis'}
        
        try:
            # Generate different types of insights
            pattern_insights = self._generate_pattern_insights(files_data)
            content_clusters = self._analyze_file_relationships(files_data)
            organization_recommendations = self._generate_organization_recommendations(files_data)
            summary_insights = self._generate_summary_insights(files_data)
            aging_files_analysis = self._analyze_aging_files(files_data)
            duplicate_candidates = self._identify_duplicate_candidates(files_data)
            
            insights_data = {
                'pattern_insights': pattern_insights,
                'content_clusters': content_clusters,
                'organization_recommendations': organization_recommendations,
                'summary_insights': summary_insights,
                'aging_files_analysis': aging_files_analysis,
                'duplicate_candidates': duplicate_candidates
            }
            
            return insights_data
            
        except Exception as e:
            logging.error(f"Error generating AI insights: {str(e)}")
            raise
    
    def _generate_pattern_insights(self, files_data):
        """
        Generate insights about file naming patterns and organization.
        
        Args:
            files_data (list): List of file information dictionaries
            
        Returns:
            dict: Pattern insights data
        """
        # Analyze filename patterns
        naming_patterns = defaultdict(list)
        
        for file_info in files_data:
            filename = file_info['name']
            
            # Extract patterns such as prefixes, suffixes, date formats, etc.
            # Example: "Report_2023-04-15.pdf" -> pattern "Report_DATE.pdf"
            
            # Check for date patterns in filenames
            date_pattern = re.compile(r'(\d{4}[-_/]\d{1,2}[-_/]\d{1,2}|\d{1,2}[-_/]\d{1,2}[-_/]\d{4}|\d{1,2}[-_/]\d{1,2}[-_/]\d{2})')
            if date_pattern.search(filename):
                pattern = date_pattern.sub('DATE', filename)
                naming_patterns[pattern].append(file_info['path'])
                continue
            
            # Check for numbered sequences
            number_pattern = re.compile(r'(\d+)')
            if number_pattern.search(filename):
                pattern = number_pattern.sub('NUMBER', filename)
                naming_patterns[pattern].append(file_info['path'])
                continue
            
            # Default pattern
            naming_patterns[filename].append(file_info['path'])
        
        # Get top patterns (patterns with most files)
        top_patterns = sorted(naming_patterns.items(), key=lambda x: len(x[1]), reverse=True)[:5]
        
        return {
            'top_patterns': [
                {'pattern': pattern, 'count': len(files), 'files': files[:3]}  # Only include first 3 examples
                for pattern, files in top_patterns
            ]
        }
    
    def _analyze_file_relationships(self, files_data):
        """
        Analyze relationships between files to identify potential clusters.
        
        Args:
            files_data (list): List of file information dictionaries
            
        Returns:
            dict: Content clusters data
        """
        # Group files by extension and analyze patterns
        extension_groups = defaultdict(list)
        
        for file_info in files_data:
            ext = file_info.get('extension', '').lower()
            if ext:
                extension_groups[ext].append(file_info)
        
        # Find related files by analyzing names and paths
        related_groups = []
        
        for ext, files in extension_groups.items():
            if len(files) > 1:
                # Try to group by similar names (e.g., "report-v1" and "report-v2")
                name_groups = defaultdict(list)
                
                for file_info in files:
                    # Remove extension, numbers, and common separators
                    base_name = re.sub(r'[_\-\s]\d+.*$', '', os.path.splitext(file_info['name'])[0])
                    name_groups[base_name].append(file_info)
                
                # Add groups with multiple files
                for base_name, grouped_files in name_groups.items():
                    if len(grouped_files) > 1:
                        related_groups.append({
                            'relationship_type': 'naming_similarity',
                            'base_name': base_name,
                            'extension': ext,
                            'files': [f['path'] for f in grouped_files[:5]]  # Limit to 5 examples
                        })
        
        return {
            'related_groups': related_groups[:5]  # Limit to top 5 groups
        }
    
    def _generate_organization_recommendations(self, files_data):
        """
        Generate recommendations for better file organization.
        
        Args:
            files_data (list): List of file information dictionaries
            
        Returns:
            dict: Organization recommendations data
        """
        # Count files by category
        category_counts = defaultdict(int)
        for file_info in files_data:
            category = file_info.get('category', 'Uncategorized')
            category_counts[category] += 1
        
        # Find oversized categories that might need subdivision
        large_categories = []
        for category, count in category_counts.items():
            if count > 10 and category != 'Uncategorized':
                # Find potential subcategories within this category
                subcategories = self._find_potential_subcategories(
                    [f for f in files_data if f.get('category') == category]
                )
                large_categories.append({
                    'category': category,
                    'file_count': count,
                    'potential_subcategories': subcategories
                })
        
        # Check for files missing categories
        uncategorized_count = category_counts.get('Uncategorized', 0)
        
        # Check for large directory depth
        deep_paths = []
        for file_info in files_data:
            depth = file_info.get('depth', 0)
            if depth > 5:
                deep_paths.append(file_info['path'])
        
        return {
            'large_categories': large_categories,
            'uncategorized_count': uncategorized_count,
            'deep_paths_count': len(deep_paths),
            'deep_paths_examples': deep_paths[:3]  # Limit to 3 examples
        }
    
    def _find_potential_subcategories(self, category_files):
        """Find potential subcategories for a set of files."""
        # Simple analysis based on filenames
        name_patterns = defaultdict(int)
        
        for file_info in category_files:
            # Extract prefix or significant starting part of filename
            prefix = file_info['name'].split('_')[0] if '_' in file_info['name'] else ''
            if prefix:
                name_patterns[prefix] += 1
        
        # Return top potential subcategories
        return [
            {'name': prefix, 'count': count}
            for prefix, count in sorted(name_patterns.items(), key=lambda x: x[1], reverse=True)
            if count >= 3  # Only consider patterns that appear at least 3 times
        ][:3]  # Limit to top 3
    
    def _generate_summary_insights(self, files_data):
        """
        Generate overall summary insights using OpenAI API.
        
        Args:
            files_data (list): List of file information dictionaries
            
        Returns:
            dict: Summary insights data
        """
        # Check if OpenAI client is available
        if openai_client is None:
            return {
                'ai_insights': [
                    "To unlock AI-powered insights, please provide a valid OpenAI API key.",
                    "This feature uses OpenAI to analyze file patterns and provide intelligent recommendations."
                ],
                'ai_recommendation': "Set up an OpenAI API key in your environment variables to enable this feature."
            }
            
        try:
            # Prepare data summary for OpenAI
            extension_counts = defaultdict(int)
            category_counts = defaultdict(int)
            total_size = 0
            oldest_file = None
            newest_file = None
            
            for file_info in files_data:
                ext = file_info.get('extension', '').lower()
                category = file_info.get('category', 'Uncategorized')
                extension_counts[ext] += 1
                category_counts[category] += 1
                total_size += file_info['size_bytes']
                
                # Track oldest and newest files
                try:
                    mod_date = file_info['modified']
                    # Ensure we're using timezone-naive datetime for comparison
                    if hasattr(mod_date, 'tzinfo') and mod_date.tzinfo is not None:
                        mod_date = mod_date.replace(tzinfo=None)
                        
                    if oldest_file is None or mod_date < oldest_file['date']:
                        oldest_file = {'date': mod_date, 'path': file_info['path']}
                    if newest_file is None or mod_date > newest_file['date']:
                        newest_file = {'date': mod_date, 'path': file_info['path']}
                except (TypeError, ValueError) as e:
                    # Skip files with problematic date values
                    logging.warning(f"Skipping file for date comparison: {file_info.get('path', 'unknown file')}: {str(e)}")
                    continue
            
            # Format data for OpenAI prompt
            data_summary = {
                'total_files': len(files_data),
                'total_size_bytes': total_size,
                'total_size_readable': self._format_size(total_size),
                'extension_distribution': dict(extension_counts),
                'category_distribution': dict(category_counts)
            }
            
            # Add date information if available
            if oldest_file:
                data_summary['oldest_file'] = oldest_file['path']
                data_summary['oldest_file_date'] = oldest_file['date'].strftime("%Y-%m-%d")
            else:
                data_summary['oldest_file'] = "None"
                data_summary['oldest_file_date'] = "None"
                
            if newest_file:
                data_summary['newest_file'] = newest_file['path']
                data_summary['newest_file_date'] = newest_file['date'].strftime("%Y-%m-%d")
            else:
                data_summary['newest_file'] = "None"
                data_summary['newest_file_date'] = "None"
            
            # Construct prompt
            summary_prompt = f"""
            Please analyze this file system data and provide key insights about the files. 
            Give 3-5 specific insights and one recommendation for organization improvement.
            
            Data Summary:
            {json.dumps(data_summary, indent=2)}
            
            Format your response as JSON with the following structure:
            {{
                "insights": [
                    "First specific insight about the files...",
                    "Second specific insight about the files...",
                    ...
                ],
                "recommendation": "One clear recommendation for improving organization..."
            }}
            """
            
            # Get AI summary from OpenAI (double-check client is not None)
            if openai_client is None:
                raise ValueError("OpenAI client is not available")
                
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an AI file system analyst that provides concise, helpful insights about file collections. Focus on patterns, organization, and practical recommendations."},
                    {"role": "user", "content": summary_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.5,
                max_tokens=500
            )
            
            # Extract JSON response
            ai_summary = json.loads(response.choices[0].message.content)
            
            return {
                'ai_insights': ai_summary.get('insights', []),
                'ai_recommendation': ai_summary.get('recommendation', "No recommendation available.")
            }
            
        except Exception as e:
            logging.error(f"Error generating AI summary insights: {str(e)}")
            return {
                'ai_insights': ["AI insights are temporarily unavailable."],
                'ai_recommendation': "Our analysis engine is experiencing issues. Please try again later."
            }
    
    def _analyze_aging_files(self, files_data):
        """
        Analyze aging files and identify candidates for archiving.
        
        Args:
            files_data (list): List of file information dictionaries
            
        Returns:
            dict: Aging files analysis data
        """
        # Define age thresholds (in days)
        age_thresholds = {
            'old': 365,  # 1 year
            'very_old': 730,  # 2 years
            'ancient': 1095  # 3 years
        }
        
        # Make sure we're using timezone-naive datetime for comparison
        now = datetime.now().replace(tzinfo=None)
        aging_files = {
            'old': [],
            'very_old': [],
            'ancient': []
        }
        
        for file_info in files_data:
            try:
                # Calculate file age in days, ensuring both datetimes are timezone naive
                mod_date = file_info['modified']
                if hasattr(mod_date, 'tzinfo') and mod_date.tzinfo is not None:
                    mod_date = mod_date.replace(tzinfo=None)
                
                age_days = (now - mod_date).days
                
                # Categorize by age (only if age is positive)
                if age_days >= 0:
                    if age_days >= age_thresholds['ancient']:
                        aging_files['ancient'].append(file_info)
                    elif age_days >= age_thresholds['very_old']:
                        aging_files['very_old'].append(file_info)
                    elif age_days >= age_thresholds['old']:
                        aging_files['old'].append(file_info)
            except (TypeError, ValueError) as e:
                # Skip files with problematic date values
                logging.warning(f"Skipping file aging analysis for {file_info.get('path', 'unknown file')}: {str(e)}")
                continue
        
        # Summarize aging files
        summary = {
            'old_count': len(aging_files['old']),
            'very_old_count': len(aging_files['very_old']),
            'ancient_count': len(aging_files['ancient']),
            'old_examples': [f['path'] for f in aging_files['old'][:3]],
            'very_old_examples': [f['path'] for f in aging_files['very_old'][:3]],
            'ancient_examples': [f['path'] for f in aging_files['ancient'][:3]]
        }
        
        return summary
    
    def _identify_duplicate_candidates(self, files_data):
        """
        Identify potential duplicate files based on size, name, and extension.
        
        Args:
            files_data (list): List of file information dictionaries
            
        Returns:
            dict: Duplicate candidates data
        """
        # Group files by size (exact same size is a strong indicator of potential duplicates)
        size_groups = defaultdict(list)
        
        for file_info in files_data:
            size_groups[file_info['size_bytes']].append(file_info)
        
        # Find groups with multiple files of the same size
        potential_duplicates = []
        
        for size, files in size_groups.items():
            if len(files) > 1 and size > 0:  # Ignore empty files
                # Further group by extension
                ext_groups = defaultdict(list)
                for file_info in files:
                    ext = file_info.get('extension', '').lower()
                    ext_groups[ext].append(file_info)
                
                # Add groups with multiple files of same extension and size
                for ext, ext_files in ext_groups.items():
                    if len(ext_files) > 1:
                        potential_duplicates.append({
                            'size_bytes': size,
                            'size_readable': self._format_size(size),
                            'extension': ext,
                            'file_count': len(ext_files),
                            'examples': [f['path'] for f in ext_files[:3]]  # Limit to 3 examples
                        })
        
        # Sort by file size (largest first)
        potential_duplicates.sort(key=lambda x: x['size_bytes'], reverse=True)
        
        return {
            'count': len(potential_duplicates),
            'groups': potential_duplicates[:5]  # Limit to top 5 groups
        }
    
    def _format_size(self, size_bytes):
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
