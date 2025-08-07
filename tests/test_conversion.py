import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from processor.employee_processor import EmployeeDocumentProcessor

def test_conversion():
    employee_id = "abc-123"
    processor = EmployeeDocumentProcessor(employee_id)
    results = processor.process_documents()

    print("\n📋 Conversion Summary:")
    for file, status in results:
        print(f" - {file}: {status}")

    print("\n📝 Preview of converted output:")
    try:
        with open(processor.output_path, 'r', encoding='utf-8') as f:
            preview = f.read(500)
            print(preview)
    except Exception as e:
        print(f"❌ Could not read output file: {e}")

if __name__ == "__main__":
    test_conversion()