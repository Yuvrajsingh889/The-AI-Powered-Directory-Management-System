from datetime import datetime
from app import db

class ScanHistory(db.Model):
    """Model to store history of directory scans."""
    id = db.Column(db.Integer, primary_key=True)
    directory_path = db.Column(db.String(500), nullable=False)
    scan_date = db.Column(db.DateTime, default=datetime.utcnow)
    file_count = db.Column(db.Integer, default=0)
    total_size = db.Column(db.BigInteger, default=0)  # Size in bytes
    
    def __repr__(self):
        return f'<ScanHistory {self.directory_path}>'

class FileCategory(db.Model):
    """Model to store file categories and their patterns."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.String(500))
    
    def __repr__(self):
        return f'<FileCategory {self.name}>'

class FileExtension(db.Model):
    """Model to store file extensions and their associated categories."""
    id = db.Column(db.Integer, primary_key=True)
    extension = db.Column(db.String(20), nullable=False, unique=True)
    category_id = db.Column(db.Integer, db.ForeignKey('file_category.id'), nullable=False)
    category = db.relationship('FileCategory', backref=db.backref('extensions', lazy=True))
    
    def __repr__(self):
        return f'<FileExtension {self.extension}>'

class FileMetadata(db.Model):
    """Model to store detailed file metadata for quick retrieval."""
    id = db.Column(db.Integer, primary_key=True)
    file_path = db.Column(db.String(1000), nullable=False, unique=True)
    filename = db.Column(db.String(255), nullable=False)
    extension = db.Column(db.String(20))
    size_bytes = db.Column(db.BigInteger)
    created_date = db.Column(db.DateTime)
    modified_date = db.Column(db.DateTime)
    category_id = db.Column(db.Integer, db.ForeignKey('file_category.id'))
    category = db.relationship('FileCategory', backref=db.backref('files', lazy=True))
    scan_id = db.Column(db.Integer, db.ForeignKey('scan_history.id'))
    scan = db.relationship('ScanHistory', backref=db.backref('files', lazy=True))
    
    def __repr__(self):
        return f'<FileMetadata {self.filename}>'

class UploadedFile(db.Model):
    """Model to store information about uploaded files."""
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(1000), nullable=False)
    extension = db.Column(db.String(20))
    size_bytes = db.Column(db.BigInteger)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    mime_type = db.Column(db.String(100))
    category = db.Column(db.String(100))
    
    def __repr__(self):
        return f'<UploadedFile {self.filename}>'
