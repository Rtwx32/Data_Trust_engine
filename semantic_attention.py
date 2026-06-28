"""
Layer 11: Cross-Feature Semantic Attention
مستوحى من Vaswani et al. (2017) – Attention Is All You Need
يحسب أوزان الانتباه بين حقول السجل ويكتشف التناقضات الدلالية
"""

import numpy as np


class SemanticAttention:
    def __init__(self):
        # ── Embeddings: كل قيمة → متجه رقمي يحمل معناها في السياق السعودي ──
        self.job_embeddings = {
            "طبيب":               np.array([0.9, 0.1, 0.9, 0.8, 0.7]),
            "طبيب جراح":          np.array([0.95, 0.05, 0.95, 0.9, 0.8]),
            "طبيب أسنان":         np.array([0.9, 0.1, 0.9, 0.8, 0.7]),
            "طبيب عيون":          np.array([0.9, 0.1, 0.9, 0.8, 0.7]),
            "طبيب أطفال":         np.array([0.9, 0.1, 0.9, 0.8, 0.7]),
            "طبيب نفسي":          np.array([0.85, 0.15, 0.85, 0.75, 0.65]),
            "طبيب طوارئ":         np.array([0.9, 0.1, 0.9, 0.85, 0.75]),
            "صيدلاني":            np.array([0.85, 0.15, 0.85, 0.75, 0.65]),
            "طيار":               np.array([0.8, 0.2, 0.85, 0.9, 0.75]),
            "طيار مدني":          np.array([0.8, 0.2, 0.85, 0.9, 0.75]),
            "محامي":              np.array([0.85, 0.15, 0.85, 0.75, 0.65]),
            "مهندس":              np.array([0.8, 0.2, 0.8, 0.7, 0.6]),
            "مهندس مدني":         np.array([0.8, 0.2, 0.8, 0.7, 0.6]),
            "مهندس كهرباء":       np.array([0.8, 0.2, 0.8, 0.7, 0.6]),
            "مهندس معماري":       np.array([0.8, 0.2, 0.8, 0.7, 0.6]),
            "مهندس نفط":          np.array([0.8, 0.2, 0.8, 0.85, 0.7]),
            "مهندس برمجيات":      np.array([0.75, 0.25, 0.8, 0.75, 0.6]),
            "مهندس بيئي":         np.array([0.75, 0.25, 0.75, 0.65, 0.55]),
            "مهندس زراعي":        np.array([0.75, 0.25, 0.75, 0.6, 0.5]),
            "مهندس صناعي":        np.array([0.75, 0.25, 0.75, 0.65, 0.55]),
            "محاسب":              np.array([0.75, 0.25, 0.75, 0.65, 0.55]),
            "محاسب قانوني":       np.array([0.8, 0.2, 0.8, 0.7, 0.6]),
            "مدقق حسابات":        np.array([0.8, 0.2, 0.8, 0.7, 0.6]),
            "معلم":               np.array([0.7, 0.3, 0.7, 0.5, 0.45]),
            "معلم صف":            np.array([0.7, 0.3, 0.7, 0.5, 0.45]),
            "معلم رياضيات":       np.array([0.7, 0.3, 0.7, 0.5, 0.45]),
            "معلم لغة عربية":     np.array([0.7, 0.3, 0.7, 0.5, 0.45]),
            "مبرمج":              np.array([0.6, 0.4, 0.75, 0.65, 0.5]),
            "مبرمج تطبيقات":      np.array([0.6, 0.4, 0.75, 0.65, 0.5]),
            "محلل بيانات":        np.array([0.65, 0.35, 0.75, 0.7, 0.55]),
            "محلل أمن معلومات":   np.array([0.7, 0.3, 0.8, 0.75, 0.6]),
            "مدير مشروع":         np.array([0.65, 0.35, 0.7, 0.75, 0.65]),
            "أخصائي موارد بشرية": np.array([0.65, 0.35, 0.65, 0.6, 0.5]),
            "أخصائي اجتماعي":     np.array([0.65, 0.35, 0.65, 0.55, 0.45]),
            "أخصائي تغذية":       np.array([0.7, 0.3, 0.7, 0.6, 0.5]),
            "ممرض":               np.array([0.65, 0.35, 0.65, 0.55, 0.45]),
            "مصمم جرافيك":        np.array([0.4, 0.6, 0.6, 0.5, 0.4]),
            "مصور فوتوغرافي":     np.array([0.3, 0.7, 0.5, 0.45, 0.35]),
            "مدرب لياقة":         np.array([0.35, 0.65, 0.45, 0.4, 0.3]),
            "مندوب مبيعات":       np.array([0.3, 0.7, 0.4, 0.45, 0.35]),
            "كاتب محكمة":         np.array([0.6, 0.4, 0.6, 0.5, 0.45]),
            "مشرف جودة":          np.array([0.65, 0.35, 0.65, 0.6, 0.5]),
            "كيميائي":            np.array([0.75, 0.25, 0.75, 0.65, 0.55]),
            "فني":                np.array([0.3, 0.7, 0.4, 0.35, 0.3]),
            "سائق":               np.array([0.1, 0.9, 0.2, 0.25, 0.2]),
            "ربة منزل":           np.array([0.1, 0.9, 0.1, 0.0, 0.1]),
            "طالب":               np.array([0.2, 0.8, 0.3, 0.0, 0.2]),
        }

        self.edu_embeddings = {
            "بكالوريوس طب":             np.array([0.95, 0.05, 0.9, 0.85, 0.8]),
            "بكالوريوس طب أسنان":       np.array([0.9, 0.1, 0.85, 0.8, 0.75]),
            "بكالوريوس طب نفس":         np.array([0.8, 0.2, 0.8, 0.7, 0.65]),
            "بكالوريوس صيدلة":          np.array([0.85, 0.15, 0.85, 0.75, 0.7]),
            "بكالوريوس هندسة":          np.array([0.85, 0.15, 0.8, 0.75, 0.65]),
            "بكالوريوس هندسة نفط":      np.array([0.85, 0.15, 0.8, 0.85, 0.7]),
            "بكالوريوس هندسة بيئية":    np.array([0.8, 0.2, 0.75, 0.65, 0.55]),
            "بكالوريوس حاسب":           np.array([0.75, 0.25, 0.85, 0.75, 0.6]),
            "بكالوريوس أمن معلومات":    np.array([0.75, 0.25, 0.85, 0.75, 0.6]),
            "بكالوريوس محاسبة":         np.array([0.75, 0.25, 0.75, 0.7, 0.6]),
            "بكالوريوس مالية":          np.array([0.75, 0.25, 0.75, 0.75, 0.65]),
            "بكالوريوس حقوق":           np.array([0.8, 0.2, 0.75, 0.7, 0.6]),
            "بكالوريوس إدارة":          np.array([0.65, 0.35, 0.65, 0.7, 0.6]),
            "بكالوريوس تربية":          np.array([0.65, 0.35, 0.65, 0.5, 0.45]),
            "بكالوريوس تغذية":          np.array([0.7, 0.3, 0.7, 0.6, 0.5]),
            "بكالوريوس زراعة":          np.array([0.7, 0.3, 0.65, 0.55, 0.45]),
            "بكالوريوس كيمياء":         np.array([0.75, 0.25, 0.75, 0.65, 0.55]),
            "بكالوريوس خدمة اجتماعية":  np.array([0.6, 0.4, 0.6, 0.5, 0.4]),
            "بكالوريوس أي تخصص":        np.array([0.5, 0.5, 0.6, 0.55, 0.45]),
            "دراسات إسلامية":           np.array([0.4, 0.6, 0.5, 0.45, 0.35]),
            "دبلوم فني":                np.array([0.3, 0.7, 0.4, 0.35, 0.3]),
            "دبلوم تصميم":              np.array([0.3, 0.7, 0.5, 0.4, 0.3]),
            "دبلوم رياضة":              np.array([0.25, 0.75, 0.35, 0.3, 0.25]),
            "دبلوم تمريض":              np.array([0.6, 0.4, 0.6, 0.5, 0.4]),
            "ثانوية عامة":              np.array([0.1, 0.9, 0.2, 0.2, 0.15]),
            "متوسطة":                   np.array([0.05, 0.95, 0.1, 0.1, 0.1]),
        }

        # أوزان الانتباه بين الحقول (Attention Weight Matrix)
        # كل صف: [مهنة→مؤهل, مهنة→عمر, مهنة→دخل, مؤهل→دخل, عمر→دخل]
        self.attention_weights = np.array([
            [0.45, 0.25, 0.20, 0.05, 0.05],  # مهنة
            [0.45, 0.10, 0.20, 0.15, 0.10],  # مؤهل
            [0.25, 0.30, 0.25, 0.10, 0.10],  # عمر
            [0.20, 0.10, 0.35, 0.25, 0.10],  # دخل
            [0.10, 0.10, 0.10, 0.10, 0.60],  # منطقة
        ])

        # استثناءات السياق السعودي
        self.saudi_exceptions = {
            ("مبرمج", "دراسات إسلامية"):        0.85,
            ("مبرمج تطبيقات", "دراسات إسلامية"): 0.85,
            ("مدير مشروع", "دبلوم فني"):         0.70,
            ("مصمم جرافيك", "ثانوية عامة"):      0.75,
            ("مصور فوتوغرافي", "ثانوية عامة"):   0.80,
            ("مندوب مبيعات", "ثانوية عامة"):     0.85,
        }

        self.dim = 5  # أبعاد المتجه

    def _get_job_vec(self, job):
        if job and job not in ("nan", "None"):
            return self.job_embeddings.get(job, np.array([0.5, 0.5, 0.5, 0.5, 0.5]))
        return np.array([0.5, 0.5, 0.5, 0.5, 0.5])

    def _get_edu_vec(self, edu):
        if edu and edu not in ("nan", "None"):
            return self.edu_embeddings.get(edu, np.array([0.4, 0.6, 0.5, 0.45, 0.4]))
        return np.array([0.3, 0.7, 0.3, 0.3, 0.3])

    def _scaled_dot_product(self, q, k):
        """
        Scaled Dot-Product Attention
        score = (Q · K) / sqrt(d_k)
        """
        score = np.dot(q, k) / np.sqrt(self.dim)
        # تحويل لنطاق [0, 1]
        return float(np.clip(score, 0, 1))

    def _compute_attention_score(self, record):
        """
        يحسب درجة التوافق الدلالي بين حقول السجل
        """
        مهنة = str(record.get("مهنة", "") or "").strip()
        مؤهل = str(record.get("مؤهل", "") or "").strip()
        عمر  = record.get("عمر")
        دخل  = record.get("دخل")

        # تحقق من الاستثناءات السعودية أولاً
        exception_key = (مهنة, مؤهل)
        if exception_key in self.saudi_exceptions:
            score = self.saudi_exceptions[exception_key]
            return score, f"استثناء سعودي معروف — توافق دلالي {score:.2f}"

        job_vec = self._get_job_vec(مهنة)
        edu_vec = self._get_edu_vec(مؤهل)

        # عمر → متجه مُطبَّع
        age_score = 0.5
        if عمر and str(عمر) not in ("nan", "None"):
            try:
                age_val = float(عمر)
                age_score = min(1.0, max(0.0, (age_val - 15) / 50))
            except Exception:
                pass
        age_vec = np.full(self.dim, age_score)

        # دخل → متجه مُطبَّع
        income_score = 0.5
        if دخل and str(دخل) not in ("nan", "None"):
            try:
                income_val = float(دخل)
                income_score = min(1.0, max(0.0, income_val / 50000))
            except Exception:
                pass
        income_vec = np.full(self.dim, income_score)

        # ── Scaled Dot-Product بين الأزواج الرئيسية ──
        s_job_edu    = self._scaled_dot_product(job_vec, edu_vec)
        s_job_age    = self._scaled_dot_product(job_vec, age_vec)
        s_job_income = self._scaled_dot_product(job_vec, income_vec)
        s_edu_income = self._scaled_dot_product(edu_vec, income_vec)
        s_age_income = self._scaled_dot_product(age_vec, income_vec)

        scores = np.array([s_job_edu, s_job_age, s_job_income, s_edu_income, s_age_income])
        weights = self.attention_weights[0]  # استخدام صف المهنة كـ Query

        # Weighted Attention Score
        final_score = float(np.dot(scores, weights))

        # تفسير
        if final_score >= 0.75:
            interp = f"توافق دلالي عالٍ ({final_score:.2f})"
        elif final_score >= 0.55:
            interp = f"توافق دلالي متوسط ({final_score:.2f})"
        elif final_score >= 0.35:
            interp = f"تناقض دلالي جزئي ({final_score:.2f})"
        else:
            interp = f"تناقض دلالي حاد ({final_score:.2f})"

        return round(final_score, 3), interp

    def analyze(self, df):
        results = []
        flagged = 0

        for i, row in df.iterrows():
            score, interp = self._compute_attention_score(row.to_dict())
            is_flagged = score < 0.40

            results.append({
                "record_id":          i,
                "attention_score":    score,
                "attention_interp":   interp,
                "attention_flag":     is_flagged,
            })

            if is_flagged:
                flagged += 1

        print(f"   🔀 Semantic Attention: {flagged} تناقض دلالي من {len(df)}")
        return results