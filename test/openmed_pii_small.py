from openmed import extract_pii, deidentify

# Hindi - 44M model, pure CPU
print("=" * 50)
print("  Testing Hindi PII Model (44M)")
print("=" * 50)
result = extract_pii(
    "रोगी: अनीता शर्मा, जन्मतिथि: 15 जनवरी 1984, फोन: +91 9876543210",
    lang="hi",
    model_name="OpenMed/OpenMed-PII-Hindi-SuperClinical-Small-44M-v1",
    use_smart_merging=True,
)
print(f"Hindi PII entities found: {len(result.entities)}")
for ent in result.entities:
    print(f"  [{ent.label}] {ent.text}")

# De-identify Hindi text
redacted = deidentify(
    "रोगी: अनीता शर्मा, जन्मतिथि: 15 जनवरी 1984, फोन: +91 9876543210", 
    lang="hi", 
    model_name="OpenMed/OpenMed-PII-Hindi-SuperClinical-Small-44M-v1",
    method="replace", 
    consistent=True, 
    seed=42
)
print(f"\nRedacted: {redacted.deidentified_text}")

# Telugu - 82M model, pure CPU
print("\n" + "=" * 50)
print("  Testing Telugu PII Model (82M)")
print("=" * 50)
try:
    result_te = extract_pii(
        "రోగి రాజేష్ కుమార్, ఆధార్: 9876 5432 1098, ఫోన్: +91 98765 43210",
        lang="te",
        model_name="OpenMed/OpenMed-PII-Telugu-FastClinical-Small-82M-v1",
    )
    print(f"Telugu PII entities found: {len(result_te.entities)}")
    for ent in result_te.entities:
        print(f"  [{ent.label}] {ent.text}")

    redacted_te = deidentify(
        "రోగి రాజేష్ కుమార్, ఆధార్: 9876 5432 1098, ఫోన్: +91 98765 43210", 
        lang="te", 
        model_name="OpenMed/OpenMed-PII-Telugu-FastClinical-Small-82M-v1",
        method="replace", 
        consistent=True, 
        seed=42
    )
    print(f"\nRedacted: {redacted_te.deidentified_text}")
except Exception as e:
    print(f"Telugu model failed (retry if network error): {e}")

print("\n" + "─" * 50)
print("✅ OpenMed PII test complete")