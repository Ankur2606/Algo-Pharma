import os
from transformers import pipeline

drug_ner = pipeline(
    "token-classification",
    model="OpenMed/OpenMed-NER-PharmaDetect-ModernClinical-149M",
    aggregation_strategy="simple",
    device=-1,
)

res = drug_ner("paracetamol caused stomach pain")
print(res)
