import sys
from openmed import extract_pii
from openmed.core import OpenMedConfig
from openmed.core.anonymizer import Anonymizer

_ = OpenMedConfig(device="cpu")
text = "@Francinean35966 @ick_real It can cause migraines"
model = "OpenMed/OpenMed-PII-SuperClinical-Small-44M-v1"

print("Original:", text)

entities = extract_pii(text, lang="en", model_name=model, use_smart_merging=True)
print("Entities:", [e.text for e in entities.entities])

anonymizer = Anonymizer(lang="en", consistent=True, seed=42)

redacted = text
# Replace from right to left to avoid messing up indices if we use start/end
# Or just replace the exact text
for ent in sorted(entities.entities, key=lambda e: len(e.text), reverse=True):
    surrogate = anonymizer.surrogate(ent.text, ent.label, lang="en")
    redacted = redacted.replace(ent.text, surrogate)

print("Replace (Custom):", redacted)
