import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from converter.word_converter import WordConverter
from converter.pdf_converter import PDFConverter
from processor.helpers.audit_logger import log_conversion
from processor.ai_employee_processor import process_file
from services.excel_reader import ExcelEmployeeReader

class EmployeeProfileProcessor:
    def __init__(self, file_list):
        self.file_list = file_list 
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:6]
        self.text_dir = Path("profiles/converted")
        self.json_dir = Path("profiles/jsons")
        self.meta_dir = Path("profiles/temp")
        self.text_dir.mkdir(parents=True, exist_ok=True)
        self.json_dir.mkdir(parents=True, exist_ok=True)
        self.meta_dir.mkdir(parents=True, exist_ok=True)
        self.json_output_path = self.json_dir / f"{self.session_id}_profile.json"
        self.meta_path = self.meta_dir / f"{self.session_id}_meta.json"

    def _get_output_file(self, file_path):
        filename = os.path.basename(file_path)
        name, _ = os.path.splitext(filename)
        return self.text_dir / f"{name}.txt"

    def _get_converter(self, file_path, output_path):
        ext = file_path.lower()
        if ext.endswith(".pdf"):
            return PDFConverter(file_path, output_path)
        elif ext.endswith(".docx"):
            return WordConverter(file_path, output_path)
        raise ValueError(f"Unsupported file type: {file_path}")

    def _process_excel(self, file_path):
        """Handle Excel files separately from document processing"""
        try:
            print("__________inside process excel______")

            # ✅ Import employees directly
            results = ExcelEmployeeReader.import_employees(file_path, update_existing=False)

            # Save raw data to JSON for audit
            output_path = self._get_output_file(file_path).with_suffix('.json')
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=4, ensure_ascii=False)

            log_conversion({
                "file_path": file_path,
                "status": "success",
                "type": "excel_import",
                "timestamp": datetime.utcnow().isoformat()
            }, output_path)

            print(f"✅ Imported {results['success']} employees from: {os.path.basename(file_path)}")
            return True

        except Exception as e:
            log_conversion({
                "file_path": file_path,
                "status": f"error: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }, None)
            print(f"⚠️ Error processing Excel file {file_path}: {e}")
            return False
    def _extract_and_save(self, file_path):
        if file_path.lower().endswith(".xlsx"):
            return self._process_excel(file_path)
        else:
            output_path = self._get_output_file(file_path)
            try:
                converter = self._get_converter(file_path, output_path)
                converter.load_document()
                converter.convert_to_text()
                converter.save_to_file(append=False, include_header=True)

                log_conversion({
                    "file_path": file_path,
                    "status": "success",
                    "text_preview": converter.text[:200],
                    "timestamp": datetime.utcnow().isoformat()
                }, output_path)  

                print(f"✅ Processed: {os.path.basename(file_path)}")
                return converter.text
            except Exception as e:
                log_conversion({
                    "file_path": file_path,
                    "status": f"error: {str(e)}",
                    "timestamp": datetime.utcnow().isoformat()
                }, output_path)

                print(f"⚠️ Error processing {file_path}: {e}")
                return ""

    def _process_with_ai(self):
        """Only process non-Excel files with AI"""
        non_excel_files = [f for f in self.file_list if not f.lower().endswith('.xlsx')]
        if not non_excel_files:
            return False

        try:
            first_file = self._get_output_file(non_excel_files[0])
            if not first_file.exists():
                print(f"⚠️ AI input file missing: {first_file}")
                return False

            result = process_file(str(first_file))
            if result:
                result.setdefault("session_id", self.session_id)
                with open(self.json_output_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=4, ensure_ascii=False)
                print(f"✅ Saved profile to: {self.json_output_path}")
                return True
            else:
                print("⚠️ No valid results returned from AI processing")
                return False
        except Exception as e:
            print(f"⚠️ AI processing failed: {e}")
            return False

    def load_metadata(self):
        if self.meta_path.exists():
            try:
                with open(self.meta_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Failed to load metadata: {e}")
        return {}

    def save_metadata(self, data):
        try:
            with open(self.meta_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Failed to save metadata: {e}")

    def process_documents(self):
        print("start process doc")
        meta = self.load_metadata()
        current_files = {os.path.basename(f): f for f in self.file_list}
        rebuild_needed = False
        print(f"meta{meta}")
        print(f"current files={current_files}")
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
        print(f"rebuild needed{rebuild_needed}")
        if rebuild_needed:
            print("🔨 Rebuilding profile output...")
            for file_path in current_files.values():
                print(f"f path= {file_path}")
                self._extract_and_save(file_path)

            self.save_metadata(meta)
            
            # Only run AI processing if there are non-Excel files
            if any(not f.lower().endswith('.xlsx') for f in current_files.values()):
                self._process_with_ai()
            else:
                print("⏩ Skipping AI processing - only Excel files processed")
        else:
            print("⏸️ No changes detected. Skipping processing.")