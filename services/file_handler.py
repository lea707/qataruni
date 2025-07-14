import os
import uuid
from werkzeug.utils import secure_filename
from pathlib import Path
from flask import current_app

class FileHandler:
    UPLOAD_FOLDER = Path('employee_documents')
    
    @classmethod
    def handle_file_uploads(cls, files):
        result = {
            'success': False,
            'saved_files': {},
            'errors': []
        }
        
        try:
            cls.UPLOAD_FOLDER.mkdir(exist_ok=True)
            
            for field_name, file in files.items():
                if file and file.filename:
                    try:
                        # Generate secure filename
                        filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
                        filepath = cls.UPLOAD_FOLDER / filename
                        
                        # Save file
                        file.save(filepath)
                        result['saved_files'][field_name] = str(filepath)
                        
                    except Exception as e:
                        result['errors'].append(f"{file.filename}: {str(e)}")
                        current_app.logger.error(f"File upload error: {e}")
            
            result['success'] = len(result['saved_files']) > 0 or len(files) == 0
            return result
            
        except Exception as e:
            current_app.logger.error(f"File handling system error: {e}")
            result['errors'].append("System error during file upload")
            return result
    
    @classmethod
    def cleanup_files(cls, filepaths):
        for path in filepaths:
            try:
                os.remove(path)
                current_app.logger.info(f"Cleaned up file: {path}")
            except Exception as e:
                current_app.logger.error(f"Failed to cleanup {path}: {e}")


def handle_file_uploads(files):
    return FileHandler.handle_file_uploads(files)

def cleanup_files(filepaths):
    return FileHandler.cleanup_files(filepaths)