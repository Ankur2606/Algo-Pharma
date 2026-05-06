import os
from openmed import deidentify

os.environ["FAST_MODE"] = "false"
text = "My name is Arjun and my phone is 9876543210"

print("--- Testing method='replace' ---")
try:
    res = deidentify(text, lang="en", model_name="OpenMed/OpenMed-PII-SuperClinical-Small-44M-v1", method="replace")
    print(f"Replace: {res.deidentified_text}")
except Exception as e:
    print(f"Error: {e}")

print("\n--- Testing method='tag' ---")
try:
    res = deidentify(text, lang="en", model_name="OpenMed/OpenMed-PII-SuperClinical-Small-44M-v1", method="tag")
    print(f"Tag: {res.deidentified_text}")
except Exception as e:
    print(f"Tag method failed/unsupported: {e}")

print("\n--- Testing method='mask' ---")
try:
    res = deidentify(text, lang="en", model_name="OpenMed/OpenMed-PII-SuperClinical-Small-44M-v1", method="mask")
    print(f"Mask: {res.deidentified_text}")
except Exception as e:
    print(f"Mask method failed/unsupported: {e}")
