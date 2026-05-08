from huggingface_hub import HfApi
import os

import time

api = HfApi()

try:
    with open('.env') as f:
        secrets_to_upload = []
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                parts = line.split('=', 1)
                if len(parts) == 2:
                    k, v = parts
                    k = k.strip()
                    v = v.strip().strip("'").strip('"')
                    if v:
                        secrets_to_upload.append((k, v))
                        
    for k, v in secrets_to_upload:
        for i in range(10):
            try:
                print(f"Setting secret {k} (Attempt {i+1})...")
                api.add_space_secret('DecentSanage/Algo-Pharma', k, v)
                break
            except Exception as e:
                print(f"Failed to set {k}: {e}. Retrying in 2 seconds...")
                time.sleep(2)
                
    print("All secrets from .env uploaded successfully!")
except Exception as e:
    print(f"Failed to read .env or upload secrets: {e}")
