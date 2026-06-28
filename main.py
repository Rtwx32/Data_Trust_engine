import pandas as pd
from layers.statistical_guard    import StatisticalGuard
from layers.data_recovery        import DataRecovery
from layers.semantic_guard       import SemanticGuard
from layers.explainability       import ExplainabilityEngine
from layers.active_learning      import ActiveLearning
from layers.root_cause           import RootCauseIntelligence
from layers.causal_detection     import CausalDetection
from layers.bayesian_trust       import BayesianTrust
from layers.adversarial_detector import AdversarialDetector
from layers.cultural_nlp         import CulturalNLP
from semantic_attention   import SemanticAttention
from layers.social_bias_drift    import SocialBiasDrift
from dashboard import print_dashboard, generate_dashboard

# ========== بيانات تجريبية ==========
data = {
    'مهنة': [
        'طبيب جراح', 'معلم صف', None, 'مهندس مدني', 'طيار مدني', None,
        'محاسب', 'مبرمج', 'محامي', 'طبيب أسنان', 'مهندس كهرباء', 'صيدلاني',
        'معلم رياضيات', 'مهندس معماري', 'طبيب', 'طيار', 'ممرض', 'مدير مشروع',
        'محلل بيانات', 'مصمم جرافيك', None, 'أخصائي موارد بشرية', 'مهندس برمجيات',
        'طبيب عيون', 'طبيب', 'محاسب قانوني', 'مدرب لياقة', 'كاتب محكمة',
        'مهندس نفط', 'أخصائي تغذية', None, 'مندوب مبيعات', 'مشرف جودة',
        'طبيب أطفال', 'مهندس زراعي', 'فني', 'مبرمج تطبيقات', 'معلم لغة عربية',
        'محلل أمن معلومات', 'طالب', 'مهندس صناعي', 'طبيب نفسي', 'أخصائي اجتماعي',
        'مصور فوتوغرافي', None, 'مهندس بيئي', 'مدقق حسابات', 'طبيب طوارئ',
        'ربة منزل', 'كيميائي',
    ],
    'مؤهل': [
        'بكالوريوس طب', None, 'بكالوريوس حاسب', 'بكالوريوس هندسة', None, 'دبلوم فني',
        'بكالوريوس محاسبة', 'دراسات إسلامية', 'ثانوية عامة', 'بكالوريوس طب أسنان',
        'بكالوريوس هندسة', 'بكالوريوس صيدلة', 'بكالوريوس تربية', 'بكالوريوس هندسة',
        'ثانوية عامة', None, 'دبلوم تمريض', 'بكالوريوس إدارة', 'بكالوريوس حاسب',
        'دبلوم تصميم', 'دبلوم فني', 'بكالوريوس إدارة', 'بكالوريوس حاسب',
        'بكالوريوس طب', 'ثانوية عامة', 'بكالوريوس محاسبة', 'دبلوم رياضة',
        'بكالوريوس حقوق', 'بكالوريوس هندسة نفط', 'بكالوريوس تغذية', None,
        'ثانوية عامة', 'بكالوريوس هندسة', 'بكالوريوس طب', 'بكالوريوس زراعة',
        'دبلوم فني', 'بكالوريوس حاسب', 'بكالوريوس تربية', 'بكالوريوس أمن معلومات',
        'ثانوية عامة', 'بكالوريوس هندسة', 'بكالوريوس طب نفس',
        'بكالوريوس خدمة اجتماعية', None, 'دبلوم فني', 'بكالوريوس هندسة بيئية',
        'بكالوريوس محاسبة', 'بكالوريوس طب', None, 'بكالوريوس كيمياء',
    ],
    'عمر': [
        45, 38, 29, None, 32, 24,
        41, 26, 34, 38, 30, 33,
        42, 35, 19, 28, 27, 44,
        31, 25, 22, 36, 29,
        40, 20, 47, 28, 39,
        43, 30, None, 27, 35,
        37, 32, 23, 26, 40,
        33, 18, 38, 46, 31,
        24, 21, 36, 50, 42,
        None, 34,
    ],
    'دخل': [
        None, 11000, 14000, 18000, 45000, 6000,
        13000, 12000, 20000, 22000, 17000, 16000,
        10000, 19000, 8000, None, 9000, 25000,
        15000, 8000, 5000, 12000, 18000,
        24000, 3500, 21000, 75000, 11000,
        30000, 13000, 6500, 8000, 14000,
        23000, 15000, 35000, 13000, 10000,
        17000, 4500, 16000, 26000, 11000,
        9000, 5000, 18000, 22000, 28000,
        12000, 15000,
    ],
    'منطقة': [
        'الرياض', 'جدة', 'الشرقية', 'الرياض', None, 'عسير',
        'جدة', 'الرياض', 'المدينة', 'جدة', 'الشرقية', 'الرياض',
        'تبوك', 'جدة', 'عسير', 'الرياض', 'المدينة', 'الرياض',
        'جدة', 'الشرقية', 'تبوك', 'الرياض', 'جدة',
        'الرياض', 'عسير', 'جدة', 'الشرقية', 'الرياض',
        'الشرقية', 'جدة', 'الرياض', 'تبوك', 'جدة',
        'الرياض', 'المدينة', 'عسير', 'جدة', 'الرياض',
        'الشرقية', 'تبوك', 'الرياض', 'جدة', 'المدينة',
        'عسير', 'الرياض', 'جدة', 'الشرقية', 'الرياض',
        None, 'جدة',
    ],
    'جنس': [
        'ذكر', 'أنثى', 'ذكر', 'ذكر', 'ذكر', None,
        'ذكر', 'ذكر', 'ذكر', 'أنثى', 'ذكر', 'أنثى',
        'أنثى', 'ذكر', 'أنثى', 'ذكر', 'أنثى', 'ذكر',
        'أنثى', 'أنثى', 'ذكر', 'أنثى', 'ذكر',
        'أنثى', None, 'ذكر', 'ذكر', 'أنثى',
        'ذكر', 'أنثى', 'ذكر', 'ذكر', 'أنثى',
        'أنثى', 'ذكر', None, 'ذكر', 'أنثى',
        'ذكر', 'أنثى', 'ذكر', 'ذكر', 'أنثى',
        'ذكر', 'أنثى', 'ذكر', 'ذكر', 'أنثى',
        'ذكر', 'أنثى',
    ],
    'خبرة_سنوات': [
        18, 12, 4,  None, 7,  1,
        15, 2,  9,  11,   5,  8,
        16, 8,  0,  3,    4,  19,
        6,  2,  1,  10,   4,
        14, 0,  20, 3,    13,
        17, 5,  None, 2,  9,
        11, 6,  1,  3,    14,
        7,  0,  12, 21,   6,
        2,  1,  9,  24,   16,
        None, 9,
    ],
}
df = pd.DataFrame(data)

print("🚀 DataTrust Engine يعمل...\n")

# ══════════════════════════════════════════════
# Layer 0 — Cultural NLP (قبل أي معالجة)
# ══════════════════════════════════════════════
print("🌐 Layer 0: Cultural NLP Calibration...")
cultural = CulturalNLP()
df, calibration_log = cultural.calibrate_dataframe(df)

# ══════════════════════════════════════════════
# Layer 1 — Statistical Guard
# ══════════════════════════════════════════════
print("🔴 Layer 1: Statistical Guard...")
guard = StatisticalGuard()
layer1_results = guard.detect(df)

# ══════════════════════════════════════════════
# Layer 2 — Data Recovery
# ══════════════════════════════════════════════
print("🟡 Layer 2: Data Recovery...")
recovery = DataRecovery()
df_recovered, recovery_log = recovery.recover(df)

# ══════════════════════════════════════════════
# Layer 3 — Semantic Guard (LLM)
# ══════════════════════════════════════════════
print("🟢 Layer 3: Semantic Guard (LLM)...")
semantic = SemanticGuard()
layer3_results = semantic.check_dataframe(df_recovered)

# ══════════════════════════════════════════════
# Layer 4 + 5 — Explainability + Active Learning
# ══════════════════════════════════════════════
print("🔵 Layer 4: Explainability + Active Learning...")
explainer = ExplainabilityEngine()
active    = ActiveLearning()

all_results = []
for i in range(len(df)):
    verdict, reason = active.check_exception(df.iloc[i].to_dict())
    if verdict:
        result = {
            "record_id":   i,
            "trust_score": 85,
            "issues":      [f"✅ استثناء محفوظ: {reason}"],
            "suggestions": [],
            "status":      "✅ موثوق"
        }
    else:
        result = explainer.explain(
            i,
            layer1_results[i],
            layer3_results[i],
            recovery_log
        )
    all_results.append(result)

# ══════════════════════════════════════════════
# Layer 6 — Root Cause Intelligence
# ══════════════════════════════════════════════
print("🟣 Layer 6: Root Cause Intelligence...")
root_cause_engine = RootCauseIntelligence()
analysis = root_cause_engine.analyze(all_results, df)

# ══════════════════════════════════════════════
# Layer 7 — Causal Detection (Pearl 2009)
# ══════════════════════════════════════════════
print("🧠 Layer 7: Causal Error Detection...")
causal = CausalDetection()
causal_results = causal.analyze(df_recovered)

# دمج النتائج السببية في all_results
for i, r in enumerate(all_results):
    cr = causal_results[i]
    r["causal_probability"]    = cr["causal_probability"]
    r["causal_interpretation"] = cr["causal_interpretation"]
    r["causal_flag"]           = cr["causal_flag"]
    # إذا الاحتمال السببي منخفض جداً → خفض السكور
    if cr["causal_flag"]:
        r["trust_score"] = max(0, r["trust_score"] - 10)
        r["issues"].append(f"🔗 {cr['causal_interpretation']}")

# ══════════════════════════════════════════════
# Layer 8 — Bayesian Trust Updating
# ══════════════════════════════════════════════
print("📊 Layer 8: Bayesian Trust Updating...")
bayesian = BayesianTrust()
all_results = bayesian.analyze_batch(all_results, df_recovered)
bayesian_summary = bayesian.get_summary()

# ══════════════════════════════════════════════
# Layer 9 — Adversarial Detection
# ══════════════════════════════════════════════
print("🛡️  Layer 9: Adversarial Detection...")
adversarial = AdversarialDetector()
adversarial_results = adversarial.analyze(df_recovered)

for i, r in enumerate(all_results):
    ar = adversarial_results[i]
    r["adversarial_score"] = ar["adversarial_score"]
    r["adversarial_flag"]  = ar["adversarial_flag"]
    if ar["adversarial_flag"]:
        r["trust_score"] = max(0, r["trust_score"] - 15)
        for detail in ar["adversarial_details"]:
            r["issues"].append(f"⚠️ تلاعب محتمل: {detail}")

# ══════════════════════════════════════════════
# Layer 10 — Social Bias Drift
# ══════════════════════════════════════════════
print("📉 Layer 10: Social Bias Drift...")
bias_monitor = SocialBiasDrift()
bias_analysis = bias_monitor.analyze(df_recovered)

# ══════════════════════════════════════════════
# Layer 11 — Cross-Feature Semantic Attention
# ══════════════════════════════════════════════
print("🔀 Layer 11: Cross-Feature Semantic Attention...")
attention = SemanticAttention()
attention_results = attention.analyze(df_recovered)

for i, r in enumerate(all_results):
    ar = attention_results[i]
    r["attention_score"] = ar["attention_score"]
    r["attention_interp"] = ar["attention_interp"]
    r["attention_flag"] = ar["attention_flag"]
    if ar["attention_flag"]:
        r["trust_score"] = max(0, r["trust_score"] - 10)
        r["issues"].append(f"🔀 {ar['attention_interp']}")

# ══════════════════════════════════════════════
# Dashboard
# ══════════════════════════════════════════════
print_dashboard(all_results, analysis)
generate_dashboard(
    all_results, analysis, df_recovered,
    extra_data={
        "causal_results":      causal_results,
        "bayesian_summary":    bayesian_summary,
        "adversarial_results": adversarial_results,
        "bias_analysis":       bias_analysis,
        "calibration_log":     calibration_log,
        "attention_results":   attention_results,
    }
)

# ══════════════════════════════════════════════
# Active Learning مثال
# ══════════════════════════════════════════════
print("\n💡 Active Learning:")
active.add_reviewer_feedback(
    df.iloc[1].to_dict(),
    "خطأ منطقي", "مقبول",
    "في السوق السعودي، المبرمجون كثيراً ما يكونون من خريجي تخصصات أخرى"
)