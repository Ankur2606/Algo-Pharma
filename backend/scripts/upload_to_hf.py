from huggingface_hub import HfApi
import time

api = HfApi()
max_retries = 10

for i in range(max_retries):
    try:
        print(f"Attempt {i+1}/{max_retries} to upload files to Hugging Face...")
        api.upload_folder(
            folder_path=".",
            repo_id="DecentSanage/Algo-Pharma",
            repo_type="space",
            ignore_patterns=[
                ".git/*",
                ".venv/*",
                "__pycache__/*",
                "*.sqlite",
                "node_modules/*",
                ".pytest_cache/*",
                "*.pyc"
            ]
        )
        print("Successfully uploaded to Hugging Face Space!")
        break
    except Exception as e:
        print(f"Failed: {e}")
        print("Retrying in 3 seconds...\n")
        time.sleep(3)
