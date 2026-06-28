import numpy as np
from collections import defaultdict


class SocialBiasDrift:

    def __init__(self):
        self.ref_mean   = 14000
        self.ref_median = 11000

    def _income_inflation(self, df):
        if "دخل" not in df.columns:
            return 0.0, []
        vals = []
        for _, row in df.iterrows():
            try:
                v = float(row["دخل"])
                if v > 0:
                    vals.append(v)
            except Exception:
                pass
        if len(vals) < 3:
            return 0.0, []

        m  = np.mean(vals)
        md = np.median(vals)
        di = (m  - self.ref_mean)   / self.ref_mean
        dm = (md - self.ref_median) / self.ref_median

        alerts = []
        if di > 0.30:
            alerts.append(f"متوسط الدخل {m:,.0f} أعلى من المرجعي بـ {di*100:.0f}%")
        if dm > 0.30:
            alerts.append(f"الوسيط {md:,.0f} أعلى من المرجعي بـ {dm*100:.0f}%")

        score = round(max(0.0, min(1.0, (di + dm) / 2)), 3)
        return score, alerts

    def _income_concealment(self, df):
        if "دخل" not in df.columns:
            return 0.0, []
        missing = sum(
            1 for _, row in df.iterrows()
            if str(row.get("دخل", "")) in ("nan", "None", "")
        )
        rate = missing / len(df)
        alerts = []
        if rate > 0.20:
            alerts.append(f"{rate*100:.0f}% من المستجيبين لم يذكروا دخلهم")
        return round(rate, 3), alerts

    def _region_bias(self, df):
        if "منطقة" not in df.columns or "دخل" not in df.columns:
            return {}
        buckets = defaultdict(list)
        for _, row in df.iterrows():
            region = str(row.get("منطقة", "") or "")
            try:
                v = float(row["دخل"])
                if v > 0 and region not in ("nan", "None", ""):
                    buckets[region].append(v)
            except Exception:
                pass
        out = {}
        for region, vals in buckets.items():
            if len(vals) >= 2:
                mean  = np.mean(vals)
                drift = (mean - self.ref_mean) / self.ref_mean
                out[region] = {
                    "mean_income": round(mean, 0),
                    "drift":       round(drift, 3),
                    "flag":        abs(drift) > 0.35,
                }
        return out

    def analyze(self, df):
        inf_score,  inf_alerts  = self._income_inflation(df)
        con_score,  con_alerts  = self._income_concealment(df)
        region_bias             = self._region_bias(df)

        overall = round(inf_score * 0.6 + con_score * 0.4, 3)
        alerts  = inf_alerts + con_alerts

        flagged = [r for r, d in region_bias.items() if d.get("flag")]
        if flagged:
            alerts.append("مناطق ذات تحيز عالٍ: " + ", ".join(flagged))

        if overall >= 0.40:
            level = "🔴 تحيز اجتماعي عالٍ"
        elif overall >= 0.20:
            level = "🟡 تحيز اجتماعي متوسط"
        else:
            level = "🟢 تحيز اجتماعي منخفض"

        print(f"   📊 Social Bias: {level} ({overall})")

        return {
            "overall_bias_score":  float(overall),
            "bias_level":          level,
            "income_inflation":    float(inf_score),
            "income_concealment":  float(con_score),
            "region_bias":         {k: {**v, "mean_income": float(v["mean_income"]), "drift": float(v["drift"])} for k, v in region_bias.items()},
            "alerts":              alerts,
        }