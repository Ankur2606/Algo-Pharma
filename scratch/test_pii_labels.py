import os
from openmed import extract_pii

os.environ["FAST_MODE"] = "false"
text = "Dolo 650 gave me nausea and headache"

print("--- Testing 'Dolo 650' entities ---")
res = extract_pii(text, lang="en", model_name="OpenMed/OpenMed-PII-SuperClinical-Small-44M-v1")
for ent in res.entities:
    print(f"Entity: '{ent.text}' | Label: '{ent.label}'")
