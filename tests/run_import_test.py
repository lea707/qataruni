from ai.json_importer import JSONImporter

def run_import():
    importer = JSONImporter()
    unprocessed = importer.get_unprocessed_files()

    if not unprocessed:
        print("⏸️ No new or changed files to process.")
    else:
        print(f"🔍 Found {len(unprocessed)} unprocessed files:")
        for f in unprocessed:
            print(f"   - {f.name}")
        importer.process_all()
        print("✅ Import complete.")

if __name__ == "__main__":
    run_import()