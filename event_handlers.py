# event_handlers.py
from signals import documents_uploaded
from flask import current_app
from processor.employee_processor import EmployeeDocumentProcessor
import threading

@documents_uploaded.connect  # ← FIXED: Changed from documents_handlers to documents_uploaded
def handle_documents_uploaded(sender, **kwargs):
    """Handle document uploaded event in background thread"""
    employee_id = kwargs.get('employee_id')
    business_id = kwargs.get('business_id')
    
    # Get the current app instance
    app = current_app._get_current_object()
    
    def process():
        # Create a new application context for the background thread
        with app.app_context():
            try:
                current_app.logger.info(f"📬 Signal received! Processing docs for {business_id}")
                processor = EmployeeDocumentProcessor(
                    employee_id=employee_id,
                    business_id=business_id
                )
                processor.process_documents()
                current_app.logger.info(f"✅ Document processing completed for {business_id}")
            except Exception as e:
                current_app.logger.error(f"❌ Error processing documents from signal: {e}")
    
    # Run in background thread to avoid blocking
    thread = threading.Thread(target=process)
    thread.daemon = True
    thread.start()