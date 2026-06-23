import os
from nlp.pii_guard import redact_pii

# Ensure FAST_MODE is false so models actually download
os.environ["FAST_MODE"] = "false"

print("Downloading PII models for English, Hindi, and Telugu...")
# Calling redact_pii with these languages triggers the OpenMed downloader
try:
    redact_pii("My name is Dr. Sharma", lang="en")
    print("✅ English PII model cached")
    redact_pii("मेरा नाम शर्मा है", lang="hi")
    print("✅ Hindi PII model cached")
    redact_pii("నా పేరు శర్మ", lang="te")
    print("✅ Telugu PII model cached")
except Exception as e:
    print(f"Error during PII model download: {e}")

print("✅ PII model setup complete!")
