# Data_Trust_engine

DataTrust Engine validates Saudi/Arabic survey data using a culturally-aware, multi-layer trust pipeline instead of rigid global outlier rules.

## What it now provides
- **11 independent validation layers** (completeness, type/range checks, semantic context, causal consistency, attention-style alignment, dynamic Bayesian update, response-bias detection, socio-economic checks, anti-cheating, and duplicate/fraud detection).
- **Trust Score (0–100)** for each record.
- **Arabic natural-language explanations** for every layer decision.
- **Human-in-the-loop active learning**: approved reviewer overrides are written to `active_learning_memory.json` and reused as permanent context rules in future evaluations.

## Quick usage
```python
from data_trust_engine import DataTrustEngine

engine = DataTrustEngine(memory_path="active_learning_memory.json")
result = engine.evaluate_record({
    "education": "Islamic Studies",
    "job_title": "Software Engineer",
    "age": 29,
    "income": 12000,
    "response_time_seconds": 90,
})

# Save a reviewer override as a learned rule
engine.register_human_override(
    {"education": "History", "job_title": "Data Engineer"},
    approved=True,
    reason="تحول مهني صحيح",
)
```
