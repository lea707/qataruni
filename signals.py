# signals.py
from blinker import signal

# Create a custom signal
documents_uploaded = signal('documents_uploaded')

# Create a custom signal
documents_processed = signal('documents_processed')