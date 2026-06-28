#  DataTrust Engine

> محرك متعدد الطبقات لفحص **مصداقية البيانات (Data Trust)** في الاستبيانات والبيانات الديموغرافية العربية/السعودية — يكتشف الأخطاء المنطقية، التلاعب، والتحيز، مع وعي كامل بسياق سوق العمل السعودي.

> A multi-layer **Data Trust / Data Quality** engine for Arabic & Saudi survey data — detects logical inconsistencies, adversarial manipulation, and social bias, with built-in awareness of the Saudi labor-market context (e.g., it knows that "Islamic Studies graduate working as a programmer" is normal in Saudi Arabia, not an error).

---

## الفكرة من المشروع

أغلب أدوات "فحص جودة البيانات" التقليدية (Statistical outliers, null checks...) تفشل مع البيانات الاجتماعية والاستبيانات لسبب بسيط: **القاعدة الإحصائية لا تفهم السياق الثقافي**.

مثال: سجل فيه `المهنة = مبرمج` و`المؤهل = دراسات إسلامية` يبدو "تناقض منطقي" لأي نظام تقليدي. لكن في سوق العمل السعودي هذا شائع جدًا — كثير من المبرمجين تخرجوا من تخصصات شرعية أو غير تقنية. نفس الشيء مع `طالب` بمؤهل بكالوريوس هندسة، أو `معلم صف` بدون مؤهل مسجل.

فكرة **DataTrust Engine** هي بناء نظام تحقق لا يعتمد على قاعدة واحدة، بل على **سلسلة من 11+ طبقة فحص مستقلة**، كل طبقة تنظر للبيانات من زاوية مختلفة (إحصائية، دلالية/LLM، سببية، بايزية، تعلّم نشط من المراجعين البشريين، انحياز اجتماعي...)، ثم تجمّع النتائج في **درجة ثقة واحدة (Trust Score 0–100)** مع تفسير واضح لسبب كل قرار. النظام مصمم ليكون:

- **قابلاً للتفسير (Explainable)** — كل سجل مرفوض أو مشكوك فيه له سبب مكتوب بالعربية.
- **يتعلّم من البشر (Human-in-the-loop)** — إذا صحّح مراجع بشري قرارًا، يُحفظ كاستثناء دائم (`active_learning_memory.json`) فلا يتكرر الخطأ.
- **بايزي/تراكمي** — درجة الثقة تتحدث مع كل عملية تشغيل بدلاً من إعادة حسابها من الصفر كل مرة (`bayesian_memory.json`).
- **حساس للسياق السعودي** خصيصًا، وليس نظامًا عامًا مترجمًا من الإنجليزية.

النتيجة: لوحة تحكم (Dashboard) تفاعلية توضح لكل سجل درجة ثقته، حالته ( موثوق /  يحتاج مراجعة /  مرفوض)، وكل الإشارات (إحصائية، سببية، دلالية، تلاعب، تحيز) التي ساهمت في القرار.

### Idea in short (EN)

Generic data-quality tools fail on social/survey data because statistical rules don't understand *cultural context* — e.g. a programmer with an Islamic Studies degree is statistically "weird" but completely normal in the Saudi job market. DataTrust Engine instead runs **11+ independent detection layers** (statistical, LLM-semantic, causal, Bayesian, adversarial, social-bias, attention-based) and fuses them into one explainable **Trust Score**, while a human-feedback memory lets reviewers permanently correct false positives.

---

##  معمارية الطبقات (Layer Architecture)

كل طبقة تُشغَّل بالتسلسل على نفس DataFrame، وتُغذّي نتائجها لمحرك التفسير ولوحة التحكم النهائية:

| # | الطبقة | الملف | الوظيفة |
|---|--------|-------|----------|
| 0 | **Cultural NLP Calibration** | `layers/cultural_nlp.py` | معايرة القيم النصية (مهن، مؤهلات) حسب القاموس السعودي قبل أي فحص |
| 1 | **Statistical Guard** | `layers/statistical_guard.py` | كشف القيم الشاذة إحصائيًا (outliers, نطاقات غير منطقية) |
| 2 | **Data Recovery** | `layers/data_recovery.py` | استرجاع/تقدير القيم المفقودة (`None`) بطريقة ذكية |
| 3 | **Semantic Guard (LLM)** | `layers/semantic_guard.py` | فحص التوافق الدلالي بين الحقول عبر LLM محلي (Ollama / Llama 3) |
| 4 | **Explainability Engine** | `layers/explainability.py` | تحويل نتائج الطبقات إلى تفسير نصي + درجة ثقة `trust_score` |
| 5 | **Active Learning** | `layers/active_learning.py` | حفظ استثناءات المراجعين البشريين ومنع تكرار الأخطاء |
| 6 | **Root Cause Intelligence** | `layers/root_cause.py` | تجميع الأنماط المتكررة في الأخطاء واستخراج توصيات |
| 7 | **Causal Detection** *(Pearl, 2009)* | `layers/causal_detection.py` | تمييز الارتباط الزائف عن العلاقة السببية الحقيقية بين الحقول |
| 8 | **Bayesian Trust Updating** | `layers/bayesian_trust.py` | تحديث درجة الثقة تراكميًا عبر التشغيلات المتعددة (ذاكرة بايزية) |
| 9 | **Adversarial Detector** | `layers/adversarial_detector.py` | كشف محاولات التلاعب/الإجابات المفتعلة في الاستبيان |
| 10 | **Social Bias Drift** | `social_bias_drift.py` | رصد انحراف الدخل (تضخيم/إخفاء) والتحيز الإقليمي |
| 11 | **Cross-Feature Semantic Attention** *(Vaswani et al., 2017)* | `semantic_attention.py` | حساب Attention Score بين الحقول (مهنة↔مؤهل↔عمر↔دخل) لكشف التناقض الدلالي الدقيق |

>  **ملاحظة مهمة:** الملفات المرفوعة حاليًا تغطي الطبقتين 10 و11 بشكل كامل (`social_bias_drift.py`, `semantic_attention.py`) بالإضافة إلى نقطة الدخول (`main.py`)، التهيئة (`config.py`)، ولوحة التحكم (`dashboard.py` / `dashboard.html`). باقي الطبقات (0 إلى 9) مُستوردة في `main.py` من حزمة `layers/` ويجب إضافتها لنفس المسار حتى يعمل المشروع بالكامل. تأكد من إنشاء مجلد `layers/` يحتوي على الملفات المذكورة في الجدول أعلاه قبل الرفع/التشغيل.

---

##  كيف يعمل (Pipeline)

```
البيانات الخام (DataFrame)
        │
        ▼
 Layer 0  Cultural NLP            ─┐
 Layer 1  Statistical Guard        │
 Layer 2  Data Recovery            │  فحص أولي
 Layer 3  Semantic Guard (LLM)     │
        │                          ┘
        ▼
 Layer 4  Explainability  +  Layer 5 Active Learning
        │
        ▼
 Layer 6  Root Cause Intelligence
        │
        ▼
 Layer 7  Causal Detection   →  تعديل trust_score
 Layer 8  Bayesian Trust     →  تعديل trust_score
 Layer 9  Adversarial        →  تعديل trust_score
 Layer 10 Social Bias Drift  →  تحليل عام على مستوى الداتاسيت
 Layer 11 Semantic Attention →  تعديل trust_score
        │
        ▼
   Dashboard (CLI + HTML تفاعلي)
```

كل سجل يخرج بدرجة ثقة نهائية `trust_score` من 0 إلى 100، تُصنَّف حسب `TRUST_THRESHOLDS` في `config.py`:

| الحالة | الحد الأدنى للدرجة |
|--------|---------------------|
|  موثوق (trusted) | ≥ 80 |
|  يحتاج مراجعة (review) | ≥ 50 |
|  مرفوض (rejected) | أقل من 50 |

---

##  هيكل المشروع

```
.
├── main.py                      # نقطة التشغيل — يستدعي جميع الطبقات بالترتيب
├── config.py                    # حدود الثقة + دليل المهن والمؤهلات السعودي
├── dashboard.py                 # توليد لوحة تحكم HTML تفاعلية + طباعة في الترمنال
├── dashboard.html               # آخر لوحة تحكم تم توليدها (مُعاينة)
├── dashboard_b64.txt            # نسخة Base64 من اللوحة (للتضمين/المشاركة)
├── semantic_attention.py        # Layer 11 — Cross-Feature Semantic Attention
├── social_bias_drift.py         # Layer 10 — Social Bias Drift
├── active_learning_memory.json  # ذاكرة الاستثناءات المتعلّمة من المراجعين
├── bayesian_memory.json         # الذاكرة البايزية التراكمية لدرجات الثقة
├── __init__.py
└── layers/                      # ⚠️ مطلوب إضافتها — تحتوي الطبقات 0–9
    ├── cultural_nlp.py
    ├── statistical_guard.py
    ├── data_recovery.py
    ├── semantic_guard.py
    ├── explainability.py
    ├── active_learning.py
    ├── root_cause.py
    ├── causal_detection.py
    ├── bayesian_trust.py
    └── adversarial_detector.py
```

---

##  التشغيل (Getting Started)

### المتطلبات

- Python 3.9+
- `pandas`, `numpy`
- [Ollama](https://ollama.ai) مُشغّل محليًا (لازم لطبقة Semantic Guard التي تستخدم LLM):
  ```bash
  ollama pull llama3
  ollama serve
  ```

### التثبيت

```bash
git clone https://github.com/<username>/datatrust-engine.git
cd datatrust-engine
pip install pandas numpy requests
```

### التشغيل

```bash
python main.py
```

سيقوم البرنامج بـ:
1. تشغيل جميع الطبقات على بيانات تجريبية مضمّنة داخل `main.py` (50 سجل تجريبي بحقول: مهنة، مؤهل، عمر، دخل، منطقة، جنس، خبرة بالسنوات).
2. طباعة ملخص في الترمنال.
3. توليد لوحة تحكم HTML تفاعلية وفتحها تلقائيًا في المتصفح.

> لاستخدام بياناتك الخاصة، استبدل قاموس `data` في `main.py` بإطار بياناتك (نفس أسماء الأعمدة)، أو حوّل الكود لقراءة CSV/Excel عبر `pd.read_csv(...)`.

---

##  الذاكرة الدائمة (Persistent Memory)

النظام لا "ينسى" بين التشغيلات:

- **`active_learning_memory.json`** — كل مرة يصحح فيها مراجع بشري قرار النظام (`active.add_reviewer_feedback(...)`)، يُحفظ النمط (مثل: مهنة=مبرمج + مؤهل=دراسات إسلامية) كاستثناء دائم، فلا يُعاد رفض سجلات مشابهة في المستقبل.
- **`bayesian_memory.json`** — يحتفظ بتوزيعات Beta/أولية (priors) لدرجات الثقة تتحدث مع كل دفعة بيانات جديدة (Bayesian updating)، بحيث تتحسن دقة النظام كلما زاد حجم البيانات التي رآها.

---

##  لوحة التحكم (Dashboard)

`dashboard.py` يولّد:
- ملخص في الترمنال (نسبة الموثوق / المراجعة / المرفوض).
- صفحة HTML تفاعلية (`dashboard.html`) تعرض لكل سجل: درجة الثقة، الحالة، كل الإشارات (سببية، بايزية، تلاعب، انتباه دلالي)، وتوزيع حسب المنطقة.

---

##  ملاحظات

- بيانات `main.py` الحالية **تجريبية (synthetic)** لأغراض العرض والاختبار فقط، وليست بيانات حقيقية لأي أفراد.
- طبقة `Semantic Guard` تعتمد على LLM محلي (Ollama) — تأكد من تشغيله قبل `python main.py` أو عطّل هذه الطبقة في `main.py` إذا لم يتوفر.
- المشروع حاليًا في مرحلة تطوير نشطة؛ بعض ملفات `layers/` غير مرفقة في هذا التسليم.

##  الترخيص

أضف ملف `LICENSE` المناسب (MIT مثلاً) قبل نشر الريبو بشكل علني.

##  المساهمة

Pull Requests مرحب بها — خصوصًا لإضافة طبقات `layers/` المتبقية، أو توسيع `SAUDI_JOBS_GUIDE` في `config.py` بمزيد من المهن والمؤهلات.
