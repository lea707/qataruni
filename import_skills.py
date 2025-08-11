
import argparse
from ai.json_skill_importer import JSONSkillImporter

def main():
    parser = argparse.ArgumentParser(description="Import skills from JSON files")
    parser.add_argument(
        '--folder',
        default='converted/json',
        help='Path to folder containing JSON files'
    )
    args = parser.parse_args()
    
    importer = JSONSkillImporter(args.folder)
    importer.process_all_files()

if __name__ == "__main__":
    main()