import os
from pathlib import Path
from processor.employee_profile_processor import EmployeeProfileProcessor

def test_upload_processor():
    # ✅ Define test file(s)
    test_files = [
        "profiles/uploaded/employees.xlsx"
    ]

    # ✅ Check file existence
    missing = [f for f in test_files if not os.path.exists(f)]
    if missing:
        print("❌ Missing test files:")
        for f in missing:
            print(f" - {f}")
        return

    # ✅ Initialize processor
    try:
        processor = EmployeeProfileProcessor(file_list=test_files)
    except Exception as e:
        print(f"⚠️ Failed to initialize processor: {e}")
        return

    # ✅ Run document processing
    try:
        processor.process_documents()
    except Exception as e:
        print(f"⚠️ Error during document processing: {e}")
        return

    # ✅ Confirm output paths
    print("\n📁 Output paths:")
    print(f" - Combined text: {processor.output_path}")
    print(f" - AI profile:    {processor.json_output_path}")
    print(f" - Metadata:      {processor.meta_path}")

    # ✅ Show combined text output
    if processor.output_path.exists():
        print(f"\n📄 Combined text saved to: {processor.output_path}")
        with open(processor.output_path, "r", encoding="utf-8") as f:
            preview = f.read(500)
            print("🔍 Preview:")
            print(preview if preview else "(empty)")
    else:
        print("⚠️ No combined text output found.")

    # ✅ Show AI output
    if processor.json_output_path.exists():
        print(f"\n🧠 AI output saved to: {processor.json_output_path}")
        with open(processor.json_output_path, "r", encoding="utf-8") as f:
            print(f.read())
    else:
        print("⚠️ No AI output generated.")

    # ✅ Check for unexpected temp files
    temp_files = list(Path("profiles/temp").glob("*.txt"))
    unexpected = [f for f in temp_files if f.name != processor.meta_path.name]
    if unexpected:
        print("\n⚠️ Unexpected .txt files in profiles/temp:")
        for f in unexpected:
            print(f" - {f}")
    else:
        print("\n✅ No unexpected .txt files in profiles/temp")

if __name__ == "__main__":
    test_upload_processor()