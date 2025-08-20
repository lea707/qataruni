import os
import json
import hashlib
from datetime import datetime
from pathlib import Path
from converter.word_converter import WordConverter
from converter.pdf_converter import PDFConverter
from .ai_processor import process_file
from ai.json_skill_importer import JSONSkillImporter

class EmployeeDocumentProcessor:
    def __init__(self, employee_id, business_id, output_path=None):
        self.employee_id = employee_id
        self.business_id = business_id
        self.output_path = output_path or f"converted/{business_id}_documents.txt"
        self.json_output_dir = os.path.join(os.path.dirname(self.output_path), "json_files")
        self.meta_path = os.path.join("employee_documents", business_id, "meta.json")
        self.input_files = self._discover_documents()

    def _discover_documents(self):
        """Discover all supported documents in the employee's document folder"""
        document_folder = os.path.join("employee_documents", self.business_id, "documents")
        supported_files = []

        if not os.path.exists(document_folder):
            print(f"⚠️ Folder not found: {document_folder}")
            return supported_files

        for filename in os.listdir(document_folder):
            if filename.lower().endswith((".docx", ".pdf")):
                file_path = os.path.join(document_folder, filename)
                supported_files.append(file_path)

        return supported_files

    def _get_converter(self, file_path):
        """Get the appropriate document converter based on file extension"""
        if file_path.lower().endswith('.pdf'):
            return PDFConverter(file_path, self.output_path)
        elif file_path.lower().endswith('.docx'):
            return WordConverter(file_path, self.output_path)
        raise ValueError(f"Unsupported file type: {file_path}")

    def _extract_text(self, file_path):
        """Extract text from document using the appropriate converter"""
        try:
            converter = self._get_converter(file_path)
            converter.load_document()
            converter.convert_to_text()
            return converter.text
        except Exception as e:
            print(f"⚠️ Error extracting text from {file_path}: {e}")
            return ""

    def _save_text(self, text, file_path):
        """Save extracted text with proper formatting"""
        try:
            os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
            mode = 'a' if os.path.exists(self.output_path) else 'w'
            
            with open(self.output_path, mode, encoding="utf-8") as f:
                f.write("\n=== START DOCUMENT ===\n")
                f.write(f"Path: {file_path}\n")
                f.write(f"Processed on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(text.strip() + "\n")
                f.write("=== END DOCUMENT ===\n")
        except Exception as e:
            print(f"⚠️ Error saving text: {e}")

   # employee_processor.py - update _process_with_ai method
    def _process_with_ai(self):
        """Process the output file with AI and save results to JSON"""
        try:
            os.makedirs(self.json_output_dir, exist_ok=True)
            json_output_path = os.path.join(
                self.json_output_dir,
                f"{self.business_id}.json"  
            )
            
            result = process_file(self.output_path)

            if result:
                # ✅ Inject business_id if missing
                if "business_id" not in result:
                    result["business_id"] = self.business_id
                
                # ✅ Check if AI processing actually failed
                if "error" in result or not isinstance(result.get("skills"), list):
                    print(f"⚠️ AI processing failed for {self.business_id}")
                    # Create a minimal valid result instead of failing completely
                    result = {"skills": [], "business_id": self.business_id}
                
                with open(json_output_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=4, ensure_ascii=False)
                print(f"✅ Saved AI output to: {json_output_path}")
                return True
            else:
                print("⚠️ No valid results returned from AI processing")
                # Create empty result file to avoid repeated processing
                with open(json_output_path, "w", encoding="utf-8") as f:
                    json.dump({"skills": [], "business_id": self.business_id}, f, indent=4)
                return False
        except Exception as e:
            print(f"⚠️ AI processing failed: {e}")
            # Create empty result file
            try:
                with open(json_output_path, "w", encoding="utf-8") as f:
                    json.dump({"skills": [], "business_id": self.business_id}, f, indent=4)
            except:
                pass
            return False
    
    def load_metadata(self):
        """Load document metadata from JSON file"""
        if os.path.exists(self.meta_path):
            try:
                with open(self.meta_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Failed to load metadata: {e}")
        return {}

    def save_metadata(self, data):
        """Save document metadata to JSON file"""
        try:
            os.makedirs(os.path.dirname(self.meta_path), exist_ok=True)
            with open(self.meta_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Failed to save metadata: {e}")

    def process_documents(self):
        """Main method to process all documents"""
        meta = self.load_metadata()
        current_files = {os.path.basename(f): f for f in self.input_files}
        rebuild_needed = False

        for filename in list(meta.keys()):
            if filename not in current_files:
                print(f"🧹 Document deleted: {filename}")
                del meta[filename]
                rebuild_needed = True

        for filename, file_path in current_files.items():
            current_mtime = os.path.getmtime(file_path)
            if filename not in meta or meta[filename] != current_mtime:
                print(f"🔄 Document changed: {filename}")
                meta[filename] = current_mtime
                rebuild_needed = True

        if rebuild_needed:
            print("🔨 Rebuilding output file...")
            if os.path.exists(self.output_path):
                os.remove(self.output_path)

            for file_path in current_files.values():
                text = self._extract_text(file_path)
                if text:
                    self._save_text(text, file_path)
                    print(f"✅ Processed: {os.path.basename(file_path)}")

            self.save_metadata(meta)

            # Process with AI and then import skills
            if self._process_with_ai():
                importer = JSONSkillImporter()
                importer.process_all_files()
        else:
            print("⏸️ No changes detected. Skipping processing.")