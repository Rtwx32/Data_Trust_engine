import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple


class DataTrustEngine:
    """Culturally-aware trust scoring engine for Saudi/Arabic survey data."""

    _KNOWN_VALID_PIVOTS = {
        ("islamic studies", "software engineer"),
        ("islamic studies", "programmer"),
        ("english literature", "product manager"),
        ("history", "ux designer"),
    }

    def __init__(self, memory_path: str = "active_learning_memory.json") -> None:
        self.memory_path = Path(memory_path)
        self.memory = self._load_memory()
        self._seen_respondents = set()

    def evaluate_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        layers: List[Tuple[str, float, str]] = [
            self._layer_completeness(record),
            self._layer_type_integrity(record),
            self._layer_ranges(record),
            self._layer_semantic_context(record),
            self._layer_causal_consistency(record),
            self._layer_attention_alignment(record),
            self._layer_dynamic_bayes(record),
            self._layer_response_bias(record),
            self._layer_income_context(record),
            self._layer_anti_cheating(record),
            self._layer_duplicate_fraud(record),
        ]

        layer_scores = {name: score for name, score, _ in layers}
        explanations_ar = [explanation for _, _, explanation in layers]
        trust_score = round(max(0.0, min(100.0, sum(layer_scores.values()) / len(layer_scores) * 100.0)), 2)

        return {
            "trust_score": trust_score,
            "layer_scores": layer_scores,
            "explanations_ar": explanations_ar,
        }

    def register_human_override(self, record: Dict[str, Any], approved: bool, reason: str = "") -> bool:
        """Store reviewer-approved context rule to prevent repeated false positives."""
        if not approved:
            return False

        education = str(record.get("education", "")).strip().lower()
        job_title = str(record.get("job_title", "")).strip().lower()
        if not education or not job_title:
            return False

        rules = self.memory.setdefault("allow_rules", [])
        key = (education, job_title)
        if any((rule.get("education"), rule.get("job_title")) == key for rule in rules):
            return False

        rules.append(
            {
                "education": education,
                "job_title": job_title,
                "reason": reason,
                "source": "human_override",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        self._save_memory()
        return True

    def _load_memory(self) -> Dict[str, Any]:
        if not self.memory_path.exists():
            return {"allow_rules": []}

        try:
            with self.memory_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    data.setdefault("allow_rules", [])
                    return data
        except (json.JSONDecodeError, OSError):
            pass
        return {"allow_rules": []}

    def _save_memory(self) -> None:
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)
        with self.memory_path.open("w", encoding="utf-8") as f:
            json.dump(self.memory, f, ensure_ascii=False, indent=2)

    def _is_known_pivot(self, education: str, job_title: str) -> bool:
        key = (education, job_title)
        if key in self._KNOWN_VALID_PIVOTS:
            return True
        return any((rule.get("education"), rule.get("job_title")) == key for rule in self.memory.get("allow_rules", []))

    def _layer_completeness(self, record: Dict[str, Any]) -> Tuple[str, float, str]:
        expected = ["age", "education", "job_title", "income", "response_time_seconds"]
        present = sum(1 for k in expected if record.get(k) not in (None, ""))
        score = present / len(expected)
        return "completeness", score, f"فحص اكتمال الحقول: تم توفير {present} من {len(expected)} حقول أساسية."

    def _layer_type_integrity(self, record: Dict[str, Any]) -> Tuple[str, float, str]:
        checks = [
            isinstance(record.get("age"), (int, float)),
            isinstance(record.get("income"), (int, float)),
            isinstance(record.get("education", ""), str),
            isinstance(record.get("job_title", ""), str),
        ]
        score = sum(checks) / len(checks)
        return "type_integrity", score, "فحص سلامة الأنواع: التوافق بين أنواع البيانات والحقول تم تقييمه."

    def _layer_ranges(self, record: Dict[str, Any]) -> Tuple[str, float, str]:
        age = record.get("age")
        income = record.get("income")
        valid_age = isinstance(age, (int, float)) and 15 <= age <= 90
        valid_income = isinstance(income, (int, float)) and 0 <= income <= 300000
        score = (float(valid_age) + float(valid_income)) / 2.0
        return "ranges", score, "فحص الحدود المنطقية: تم التحقق من العمر والدخل ضمن نطاقات واقعية محلية."

    def _layer_semantic_context(self, record: Dict[str, Any]) -> Tuple[str, float, str]:
        education = str(record.get("education", "")).strip().lower()
        job_title = str(record.get("job_title", "")).strip().lower()
        if not education or not job_title:
            return "semantic_context", 0.5, "فحص الدلالة والسياق: معلومات التعليم أو الوظيفة غير كافية للحكم الكامل."

        if self._is_known_pivot(education, job_title):
            return "semantic_context", 1.0, "فحص الدلالة والسياق: تم قبول التحول المهني كسياق محلي صحيح."

        if education in job_title or job_title in education:
            return "semantic_context", 0.9, "فحص الدلالة والسياق: هناك توافق لغوي واضح بين التعليم والوظيفة."

        return "semantic_context", 0.6, "فحص الدلالة والسياق: التوافق المهني متوسط ويتطلب دعمًا من طبقات أخرى."

    def _layer_causal_consistency(self, record: Dict[str, Any]) -> Tuple[str, float, str]:
        employment = str(record.get("employment_status", "")).strip().lower()
        income = record.get("income")
        if not isinstance(income, (int, float)):
            return "causal_consistency", 0.5, "التحليل السببي: لا توجد معلومات دخل كافية للتحقق من العلاقات السببية."

        if employment in {"unemployed", "student"} and income > 10000:
            return "causal_consistency", 0.4, "التحليل السببي: دخل مرتفع مع حالة عمل غير متوقعة يحتاج مراجعة."
        return "causal_consistency", 0.9, "التحليل السببي: العلاقات بين الحالة الوظيفية والدخل منطقية."

    def _layer_attention_alignment(self, record: Dict[str, Any]) -> Tuple[str, float, str]:
        education = str(record.get("education", "")).strip().lower()
        job_title = str(record.get("job_title", "")).strip().lower()
        if not education or not job_title:
            return "attention_alignment", 0.5, "محاذاة الحقول بالانتباه: نقص حقول أساسية يمنع حساب التوافق الكامل."

        shared_tokens = set(education.split()) & set(job_title.split())
        if shared_tokens or self._is_known_pivot(education, job_title):
            return "attention_alignment", 0.95, "محاذاة الحقول بالانتباه: الترابط بين الحقول مرتفع ولا توجد تناقضات جوهرية."
        return "attention_alignment", 0.7, "محاذاة الحقول بالانتباه: الترابط متوسط ولا يظهر تناقض حاد."

    def _layer_dynamic_bayes(self, record: Dict[str, Any]) -> Tuple[str, float, str]:
        base = 0.7
        if record.get("manual_flags"):
            base -= 0.15
        if record.get("prior_verified") is True:
            base += 0.2
        score = max(0.0, min(1.0, base))
        return "dynamic_bayes", score, "الاحتمال الديناميكي: تم تحديث درجة الثقة تراكميًا بناءً على إشارات سابقة."

    def _layer_response_bias(self, record: Dict[str, Any]) -> Tuple[str, float, str]:
        answers = record.get("likert_answers")
        if not isinstance(answers, list) or len(answers) < 3:
            return "response_bias", 0.75, "تحليل تحيز الاستجابة: بيانات القياس غير كافية لاكتشاف التحيز بدقة عالية."

        uniform = len(set(answers)) == 1
        score = 0.45 if uniform else 0.9
        return "response_bias", score, "تحليل تحيز الاستجابة: تم قياس نمط الإجابات للكشف عن الاستجابات الآلية."

    def _layer_income_context(self, record: Dict[str, Any]) -> Tuple[str, float, str]:
        income = record.get("income")
        city = str(record.get("city", "")).strip().lower()
        if not isinstance(income, (int, float)):
            return "income_context", 0.6, "تحليل الدخل الاجتماعي: نقص بيانات الدخل يحد من التقييم الاقتصادي."

        high_cost_cities = {"riyadh", "jeddah", "dammam"}
        if city in high_cost_cities and income < 2500:
            return "income_context", 0.55, "تحليل الدخل الاجتماعي: الدخل منخفض مقارنة بتكلفة المعيشة المحلية."
        return "income_context", 0.9, "تحليل الدخل الاجتماعي: نمط الدخل متسق مع السياق المحلي."

    def _layer_anti_cheating(self, record: Dict[str, Any]) -> Tuple[str, float, str]:
        rt = record.get("response_time_seconds")
        if not isinstance(rt, (int, float)):
            return "anti_cheating", 0.65, "مكافحة الغش: وقت الاستجابة غير متوفر، تم استخدام تقييم تحفظي."

        score = 0.35 if rt < 15 else 0.9
        return "anti_cheating", score, "مكافحة الغش: تم تقييم سرعة الإجابة لرصد السلوك غير الطبيعي."

    def _layer_duplicate_fraud(self, record: Dict[str, Any]) -> Tuple[str, float, str]:
        respondent_id = record.get("respondent_id")
        if respondent_id in self._seen_respondents and respondent_id is not None:
            return "duplicate_fraud", 0.2, "كشف الأنماط الاحتيالية: تم رصد تكرار معرف مستجيب بشكل مريب."

        if respondent_id is not None:
            self._seen_respondents.add(respondent_id)
        return "duplicate_fraud", 0.9, "كشف الأنماط الاحتيالية: لا توجد مؤشرات قوية على تكرار أو احتيال."
