from abc import ABC, abstractmethod
from datetime import datetime
import os

class DocumentConverter(ABC):
    def __init__(self, input_path, output_path):
        self.input_path = input_path
        self.output_path = output_path
        self.text = ""

    @abstractmethod
    def load_document(self):
        pass

    @abstractmethod
    def convert_to_text(self):
        pass

   
    def save_to_file(self, append=True, include_header=True):
        try:
            os.makedirs(os.path.dirname(self.output_path), exist_ok=True)

            mode = 'a' if append else 'w'
            with open(self.output_path, mode, encoding='utf-8') as f:
                if include_header:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    f.write("\n=== START DOCUMENT ===\n")
                    f.write(f"Path: {self.input_path}\n")
                    f.write(f"Processed on: {timestamp}\n\n")
                f.write(self.text.strip() + "\n")
                f.write("=== END DOCUMENT ===\n")
        except Exception as e:
            print(f"[❌] Failed to save file: {e}")