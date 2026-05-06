import os
from openmed import deidentify, extract_pii
os.environ["FAST_MODE"] = "false"
text = "My aadhaar is [AADHAAR]"
print(f"Original: {text}")
try:
    res = deidentify(text, lang="en", model_name="OpenMed/OpenMed-PII-SuperClinical-Small-44M-v1", method="mask")
    print(f"Masked: {res.deidentified_text}")
except Exception as e:
    print(f"Error: {e}")
