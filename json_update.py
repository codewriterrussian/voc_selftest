import requests
import json
import os

class JSONManager:
    def __init__(self, api_key, bin_id, json_file):
        """Initialize API keys and file paths."""
        self.api_key = api_key
        self.bin_id = bin_id
        self.bin_api_url = f"https://api.jsonbin.io/v3/b/{bin_id}"
        self.json_file = json_file
        self.headers = {
            "Content-Type": "application/json",
            "X-Master-Key": api_key
        }
        self.add_file = os.path.join("templates", "add.txt")  # Path to add.txt

    def load_json(self):
        """Load the local JSON file."""
        try:
            with open(self.json_file, "r", encoding="utf-8") as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            print(f"⚠️ Error: {self.json_file} not found or contains invalid JSON. Creating a new one.")
            return {"categories": {}}

    def save_json(self, data):
        """Save the JSON data locally."""
        with open(self.json_file, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
        print(f"✅ JSON file updated and saved locally.")

    def upload_json(self):
        """Upload the updated JSON file to JSONBin."""
        try:
            with open(self.json_file, "r", encoding="utf-8") as file:
                data = json.load(file)

            response = requests.put(self.bin_api_url, headers=self.headers, data=json.dumps(data))

            if response.status_code == 200:
                print(f"✅ JSON uploaded successfully! Bin ID: {self.bin_id}")
                print(f"📌 Access it at: {self.bin_api_url}")
            else:
                print(f"❌ Upload failed: {response.text}")

        except Exception as e:
            print(f"❌ Error uploading JSON: {e}")

    def download_json(self):
        """Download the latest JSON from JSONBin and overwrite local file."""
        try:
            response = requests.get(self.bin_api_url, headers=self.headers)

            if response.status_code == 200:
                data = response.json()["record"]
                self.save_json(data)
                print(f"✅ JSON downloaded and saved to {self.json_file}")
            else:
                print(f"❌ Download failed: {response.text}")

        except Exception as e:
            print(f"❌ Error downloading JSON: {e}")

    def create_category(self):
        """Create a new category."""
        data = self.load_json()
        new_category = input("Enter the new category name: ").strip()

        if new_category in data["categories"]:
            print(f"❌ Error: Category '{new_category}' already exists!")
            return

        data["categories"][new_category] = []
        self.save_json(data)
        print(f"✅ New category '{new_category}' created.")

        # Ask if user wants to add questions
        add_questions = input(f"Do you want to add questions to '{new_category}' now? (Y/N): ").strip().lower()
        if add_questions in ["y", "yes"]:
            self.append_questions(new_category)

    def append_questions(self, selected_category=None):
        """Append new questions to an existing category using `add.txt` file."""
        data = self.load_json()
        categories = list(data["categories"].keys())

        if not categories:
            print("❌ No categories available! Please create one first.")
            return

        # Choose category via number input
        if selected_category is None:
            print("\n📌 Existing Categories:")
            for idx, category in enumerate(categories, 1):
                print(f"{idx}) {category}")

            try:
                choice = int(input("\nSelect the category number to append questions: ").strip()) - 1
                if 0 <= choice < len(categories):
                    selected_category = categories[choice]
                else:
                    print("❌ Invalid selection.")
                    return
            except ValueError:
                print("❌ Please enter a valid number.")
                return

        # Read from `templates/add.txt`
        if not os.path.exists(self.add_file):
            print(f"❌ Error: {self.add_file} not found.")
            return

        try:
            with open(self.add_file, "r", encoding="utf-8") as file:
                new_questions = json.load(file)  # Ensure it's in JSON format
        except Exception as e:
            print(f"❌ Error loading file: {e}")
            return

        if not self.validate_questions_format(new_questions):
            print("❌ Error: Invalid questions format. Ensure correct structure.")
            return

        data["categories"][selected_category].extend(new_questions)
        self.save_json(data)
        print(f"✅ Added {len(new_questions)} questions to '{selected_category}'.")

    def validate_questions_format(self, questions):
        """Check if the provided questions match the expected JSON structure."""
        if not isinstance(questions, list):
            return False
        for question in questions:
            if not all(key in question for key in ["question", "options", "correct_answer", "explanation"]):
                return False
            if not isinstance(question["options"], dict) or len(question["options"]) < 2:
                return False
        return True

    def main_menu(self):
        """Main interactive menu for JSON management."""
        while True:
            print("\n=== JSON Manager ===")
            print("1) Append questions to an existing category")
            print("2) Create a new category")
            print("3) Upload JSON to JSONBin")
            print("4) Download JSON from JSONBin")
            print("5) Exit")

            choice = input("Select an option (1-5): ").strip()

            if choice == "1":
                self.append_questions()
            elif choice == "2":
                self.create_category()
            elif choice == "3":
                self.upload_json()
            elif choice == "4":
                self.download_json()
            elif choice == "5":
                break
            else:
                print("❌ Invalid choice. Please select 1-5.")

# Initialize JSONManager
if __name__ == "__main__":
    manager = JSONManager(
        api_key="$2a$10$emdSh/thUg5xTvyY9z89UOy.BurV3ykvVjjUjodpvnJe2Xqc/WAAm",
        bin_id="67a87edbacd3cb34a8db4700",
        json_file="questions.json"
    )
    manager.main_menu()
