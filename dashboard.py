import json
import os
import webbrowser
import tempfile
from datetime import datetime


def print_dashboard(all_results, root_cause):
    total    = len(all_results)
    trusted  = sum(1 for r in all_results if r["status"] == "✅ موثوق")
    review   = sum(1 for r in all_results if r["status"] == "⚠️ يحتاج مراجعة")
    rejected = sum(1 for r in all_results if r["status"] == "🚨 مرفوض")
    print("\n" + "="*55)
    print("         🎯 DataTrust Engine — لوحة التحكم")
    print("="*55)
    print(f"  إجمالي السجلات:      {total}")
    print(f"  ✅ موثوقة:           {trusted} ({round(trusted/total*100)}%)")
    print(f"  ⚠️  تحتاج مراجعة:    {review} ({round(review/total*100)}%)")
    print(f"  🚨 مرفوضة:          {rejected} ({round(rejected/total*100)}%)")
    print("-"*55)
    for rec in root_cause.get("recommendations", []):
        print(f"  {rec}")
    print("="*55)
    print("\n📋 تفاصيل السجلات:")
    for r in all_results:
        print(f"\n  سجل #{r['record_id']} | {r['status']} | Trust: {r['trust_score']}/100")
        for issue in r.get("issues", []):
            print(f"    {issue}")


def generate_dashboard(all_results, root_cause, df=None, extra_data=None):
    if extra_data is None:
        extra_data = {}

    total    = len(all_results)
    trusted  = sum(1 for r in all_results if r["status"] == "✅ موثوق")
    review   = sum(1 for r in all_results if r["status"] == "⚠️ يحتاج مراجعة")
    rejected = sum(1 for r in all_results if r["status"] == "🚨 مرفوض")

    def pct(n):
        return round(n / total * 100) if total else 0

    # Region stats for chart
    region_stats = {}
    if df is not None:
        for i, r in enumerate(all_results):
            try:
                region = str(df.iloc[r["record_id"]].get("منطقة", "غير محدد") or "غير محدد")
                if region in ("nan","None",""): region = "غير محدد"
                if region not in region_stats:
                    region_stats[region] = {"trusted":0,"review":0,"rejected":0}
                sc = r["status"]
                if sc == "✅ موثوق": region_stats[region]["trusted"] += 1
                elif sc == "⚠️ يحتاج مراجعة": region_stats[region]["review"] += 1
                else: region_stats[region]["rejected"] += 1
            except Exception:
                pass

    records_data = []
    for r in all_results:
        rid   = r["record_id"]
        score = r["trust_score"]
        if r["status"] == "✅ موثوق":           sc = "trusted"
        elif r["status"] == "⚠️ يحتاج مراجعة": sc = "review"
        else:                                    sc = "rejected"

        row_data = {}
        if df is not None:
            try:
                row = df.iloc[rid]
                row_data = {
                    str(k): ("—" if str(v) in ("nan","None","NaT","") else str(v))
                    for k, v in row.items()
                }
            except Exception:
                pass

        records_data.append({
            "id":             rid,
            "trust_score":    score,
            "bayesian_score": r.get("bayesian_adjusted_score", score),
            "status":         r["status"],
            "status_class":   sc,
            "issues":         r.get("issues", []),
            "suggestions":    r.get("suggestions", []),
            "row_data":       row_data,
            "causal_prob":    r.get("causal_probability", None),
            "causal_interp":  r.get("causal_interpretation", ""),
            "causal_flag":    r.get("causal_flag", False),
            "adv_score":      r.get("adversarial_score", 0),
            "adv_flag":       r.get("adversarial_flag", False),
            "attn_score":     r.get("attention_score", None),
            "attn_interp":    r.get("attention_interp", ""),
            "attn_flag":      r.get("attention_flag", False),
            "region":         row_data.get("منطقة", "—"),
        })

    recs_data = []
    for rec_text in root_cause.get("recommendations", []):
        if   rec_text.startswith("🔴"): recs_data.append({"icon":"🔴","type":"red",   "text":rec_text[2:].strip()})
        elif rec_text.startswith("🟡"): recs_data.append({"icon":"🟡","type":"yellow","text":rec_text[2:].strip()})
        elif rec_text.startswith("📍"): recs_data.append({"icon":"📍","type":"blue",  "text":rec_text[2:].strip()})
        else:                           recs_data.append({"icon":"ℹ️","type":"blue",  "text":rec_text.strip()})

    bias       = extra_data.get("bias_analysis", {})
    bay_sum    = extra_data.get("bayesian_summary", [])
    cal_log    = extra_data.get("calibration_log", [])
    error_rate = root_cause.get("error_rate", f"{pct(rejected+review)}%")

    # Score distribution for histogram
    score_buckets = [0]*10
    for r in all_results:
        idx = min(9, r["trust_score"] // 10)
        score_buckets[idx] += 1

    data_blob = json.dumps({
        "total": total, "trusted": trusted, "review": review, "rejected": rejected,
        "error_rate": error_rate,
        "records": records_data,
        "recs": recs_data,
        "run_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "bias": {
            "score":       float(bias.get("overall_bias_score", 0)),
            "level":       bias.get("bias_level", "—"),
            "alerts":      bias.get("alerts", []),
            "inflation":   float(bias.get("income_inflation", 0)),
            "concealment": float(bias.get("income_concealment", 0)),
        },
        "bayesian":     bay_sum[:8],
        "calibration":  cal_log[:10],
        "region_stats": region_stats,
        "score_buckets": score_buckets,
    }, ensure_ascii=False)

    al_data = {"exceptions": []}
    if os.path.exists("active_learning_memory.json"):
        try:
            with open("active_learning_memory.json", "r", encoding="utf-8") as f:
                al_data = json.load(f)
        except Exception:
            pass
    al_blob = json.dumps(al_data, ensure_ascii=False)

    html = """<!DOCTYPE html>
<html lang="ar" dir="rtl" data-lang="ar">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DataTrust Engine — GASTAT</title>
<link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@300;400;500;700;900&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#03080f;--s1:#071220;--s2:#0c1e35;--s3:#112848;
  --b1:#0d3a6e;--b2:#1a5294;
  --blue:#1e90ff;--cyan:#00d4ff;--green:#00e676;
  --yellow:#ffea00;--red:#ff1744;--purple:#e040fb;
  --orange:#ff6d00;--pink:#ff66cc;--teal:#00bcd4;
  --text:#d0e8ff;--dim:#4a7a9b;--bright:#ffffff;
  --mono:'Space Mono',monospace;--sans:'Tajawal',sans-serif;
  --r:6px;
}
*{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth}
body{background:var(--bg);color:var(--text);font-family:var(--sans);min-height:100vh;overflow-x:hidden;font-size:15px}

/* grid bg */
body::before{content:'';position:fixed;inset:0;
  background-image:
    radial-gradient(ellipse 80% 50% at 20% 10%,rgba(30,144,255,.07),transparent),
    radial-gradient(ellipse 60% 40% at 80% 80%,rgba(0,212,255,.05),transparent),
    linear-gradient(rgba(30,144,255,.025) 1px,transparent 1px),
    linear-gradient(90deg,rgba(30,144,255,.025) 1px,transparent 1px);
  background-size:100% 100%,100% 100%,32px 32px,32px 32px;
  pointer-events:none;z-index:0}


.wrap{max-width:1500px;margin:0 auto;padding:20px 24px;position:relative;z-index:1}

/* ══ HEADER ══ */
header{
  display:flex;align-items:center;justify-content:space-between;
  padding:18px 28px;margin-bottom:18px;
  background:linear-gradient(135deg,var(--s1) 0%,var(--s2) 100%);
  border:1px solid var(--b1);border-radius:var(--r);
  position:relative;overflow:hidden;
}
header::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;
  background:linear-gradient(90deg,var(--blue),var(--cyan),var(--green),var(--purple),var(--pink))}
header::after{content:'';position:absolute;bottom:0;left:0;right:0;height:1px;
  background:linear-gradient(90deg,transparent,var(--b2),transparent)}
.logo-area{display:flex;align-items:center;gap:16px}
.logo-box{
  width:52px;height:52px;border-radius:var(--r);
  background:linear-gradient(135deg,rgba(30,144,255,.2),rgba(0,212,255,.1));
  border:1px solid var(--cyan);display:flex;align-items:center;justify-content:center;
  font-size:22px;position:relative;
  box-shadow:0 0 20px rgba(0,212,255,.2);
  animation:logopulse 3s ease-in-out infinite}
@keyframes logopulse{0%,100%{box-shadow:0 0 20px rgba(0,212,255,.2)}50%{box-shadow:0 0 35px rgba(0,212,255,.4)}}
.logo-text h1{font-size:22px;font-weight:900;color:var(--bright);letter-spacing:-0.5px}
.logo-text p{font-family:var(--mono);font-size:9px;color:var(--cyan);letter-spacing:3px;margin-top:2px}
.hdr-center{display:flex;gap:24px}
.hdr-stat{text-align:center}
.hdr-stat-val{font-family:var(--mono);font-size:22px;font-weight:700;line-height:1}
.hdr-stat-lbl{font-size:10px;color:var(--dim);margin-top:3px;letter-spacing:1px}
.hdr-right{display:flex;align-items:center;gap:10px}
.status-pill{display:flex;align-items:center;gap:7px;padding:6px 14px;
  background:rgba(0,230,118,.1);border:1px solid rgba(0,230,118,.3);border-radius:20px;
  font-family:var(--mono);font-size:10px;color:var(--green)}
.pulse{width:7px;height:7px;border-radius:50%;background:var(--green);
  animation:blink 1.4s infinite}
@keyframes blink{0%,100%{opacity:1;box-shadow:0 0 6px var(--green)}50%{opacity:.3;box-shadow:none}}
.btn{font-family:var(--mono);font-size:10px;padding:7px 16px;border-radius:4px;
  cursor:pointer;border:1px solid;transition:all .2s;letter-spacing:1px;text-transform:uppercase;font-weight:700}
.btn-lang{background:rgba(0,212,255,.08);border-color:rgba(0,212,255,.4);color:var(--cyan)}
.btn-lang:hover{background:rgba(0,212,255,.18)}
.btn-judge{background:linear-gradient(135deg,rgba(224,64,251,.15),rgba(30,144,255,.15));
  border-color:var(--purple);color:var(--purple)}
.btn-judge:hover{background:linear-gradient(135deg,rgba(224,64,251,.3),rgba(30,144,255,.3))}

/* ══ FILTER BAR ══ */
.filter-bar{
  display:flex;align-items:center;gap:8px;margin-bottom:16px;flex-wrap:wrap;
  padding:12px 16px;background:var(--s1);border:1px solid var(--b1);border-radius:var(--r)}
.filter-lbl{font-family:var(--mono);font-size:9px;color:var(--dim);letter-spacing:2px;margin-left:6px}
.fbtn{font-family:var(--mono);font-size:10px;padding:5px 13px;border-radius:3px;
  cursor:pointer;border:1px solid var(--b1);background:transparent;color:var(--dim);
  transition:all .18s;white-space:nowrap}
.fbtn:hover{border-color:var(--blue);color:var(--text)}
.fbtn.active{border-color:var(--blue);color:var(--blue);background:rgba(30,144,255,.1)}
.fbtn.ft.active{border-color:var(--green);color:var(--green);background:rgba(0,230,118,.08)}
.fbtn.fr.active{border-color:var(--yellow);color:var(--yellow);background:rgba(255,234,0,.08)}
.fbtn.fj.active{border-color:var(--red);color:var(--red);background:rgba(255,23,68,.08)}
.fbtn.fc.active{border-color:var(--purple);color:var(--purple);background:rgba(224,64,251,.08)}
.fbtn.fa.active{border-color:var(--orange);color:var(--orange);background:rgba(255,109,0,.08)}
.fbtn.fn.active{border-color:var(--pink);color:var(--pink);background:rgba(255,102,204,.08)}

/* ══ KPI GRID ══ */
.kpi-grid{display:grid;grid-template-columns:repeat(6,1fr);gap:12px;margin-bottom:16px}
.kpi{background:var(--s1);border:1px solid var(--b1);border-radius:var(--r);
  padding:16px 18px;position:relative;overflow:hidden;cursor:default;transition:border-color .2s}
.kpi:hover{border-color:var(--blue)}
.kpi::after{content:'';position:absolute;bottom:0;left:0;right:0;height:2px}
.kpi.k0::after{background:var(--blue)}.kpi.k1::after{background:var(--green)}
.kpi.k2::after{background:var(--yellow)}.kpi.k3::after{background:var(--red)}
.kpi.k4::after{background:var(--purple)}.kpi.k5::after{background:var(--pink)}
.kpi-lbl{font-family:var(--mono);font-size:8px;letter-spacing:2px;color:var(--dim);
  margin-bottom:8px;text-transform:uppercase}
.kpi-val{font-family:var(--mono);font-size:32px;font-weight:700;line-height:1;margin-bottom:4px}
.kpi.k0 .kpi-val{color:var(--blue)}.kpi.k1 .kpi-val{color:var(--green)}
.kpi.k2 .kpi-val{color:var(--yellow)}.kpi.k3 .kpi-val{color:var(--red)}
.kpi.k4 .kpi-val{color:var(--purple)}.kpi.k5 .kpi-val{color:var(--pink);font-size:18px}
.kpi-sub{font-size:11px;color:var(--dim)}

/* ══ TRUST BAR ══ */
.tbar-row{background:var(--s1);border:1px solid var(--b1);border-radius:var(--r);
  padding:16px 20px;margin-bottom:16px}
.tbar-lbl{font-family:var(--mono);font-size:9px;letter-spacing:2px;color:var(--dim);
  margin-bottom:10px;text-transform:uppercase}
.tbar{height:20px;border-radius:3px;background:var(--bg);display:flex;overflow:hidden;
  border:1px solid var(--b1)}
.tbar-seg{height:100%;transition:width 1.2s cubic-bezier(.4,0,.2,1)}
.tbar-seg.st{background:linear-gradient(90deg,#00b851,var(--green))}
.tbar-seg.sr{background:linear-gradient(90deg,#c4a000,var(--yellow))}
.tbar-seg.sj{background:linear-gradient(90deg,#cc1133,var(--red))}
.tbar-legend{display:flex;gap:20px;margin-top:10px;font-family:var(--mono);font-size:10px;color:var(--dim)}
.tleg{display:flex;align-items:center;gap:6px}
.tleg-dot{width:10px;height:10px;border-radius:2px}

/* ══ CHARTS ROW ══ */
.charts-row{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:16px}
.chart-card{background:var(--s1);border:1px solid var(--b1);border-radius:var(--r);padding:16px}
.chart-title{font-family:var(--mono);font-size:9px;letter-spacing:2px;color:var(--cyan);
  text-transform:uppercase;margin-bottom:14px}
canvas{width:100%!important;display:block;max-height:220px}

/* ══ PIPELINE ══ */
.pipeline{background:var(--s1);border:1px solid var(--b1);border-radius:var(--r);
  padding:16px 20px;margin-bottom:16px}
.pipe-scroll{display:flex;align-items:center;overflow-x:auto;padding-bottom:4px;gap:0;
  scrollbar-width:none}
.pipe-scroll::-webkit-scrollbar{display:none}
.lnode{display:flex;flex-direction:column;align-items:center;gap:5px;flex-shrink:0;cursor:default}
.lcirc{width:44px;height:44px;border-radius:50%;border:1.5px solid var(--cyan);
  display:flex;align-items:center;justify-content:center;font-size:14px;
  background:var(--s2);transition:all .2s}
.lnode:hover .lcirc{border-color:var(--blue);box-shadow:0 0 16px rgba(30,144,255,.4);transform:scale(1.1)}
.llbl{font-family:var(--mono);font-size:7.5px;text-align:center;color:var(--dim);
  max-width:58px;line-height:1.3}
.pconn{flex:1;min-width:12px;height:1px;
  background:linear-gradient(90deg,var(--b1),var(--cyan),var(--b1));margin-bottom:22px;opacity:.6}

/* ══ TABS ══ */
.tabs{display:flex;gap:0;border-bottom:1px solid var(--b1);margin-bottom:0}
.tab{font-family:var(--mono);font-size:10px;padding:10px 18px;cursor:pointer;
  border:1px solid transparent;border-bottom:none;color:var(--dim);
  letter-spacing:1px;transition:all .2s;border-radius:4px 4px 0 0;margin-bottom:-1px}
.tab:hover{color:var(--text)}
.tab.active{background:var(--s1);border-color:var(--b1);color:var(--cyan);border-bottom-color:var(--s1)}
.tpane{display:none;background:var(--s1);border:1px solid var(--b1);
  border-top:none;border-radius:0 0 var(--r) var(--r);margin-bottom:16px}
.tpane.active{display:block}

/* ══ MAIN GRID ══ */
.main-grid{display:grid;grid-template-columns:1fr 340px;gap:12px;padding:14px}
.panel{background:var(--s1);border:1px solid var(--b1);border-radius:var(--r);overflow:hidden}
.phdr{padding:11px 18px;border-bottom:1px solid var(--b1);
  display:flex;align-items:center;justify-content:space-between;background:var(--s2)}
.ptitle{font-family:var(--mono);font-size:9px;letter-spacing:2px;color:var(--cyan);text-transform:uppercase}
.pbadge{font-family:var(--mono);font-size:9px;padding:2px 8px;border-radius:3px;
  background:rgba(30,144,255,.1);border:1px solid rgba(30,144,255,.3);color:var(--blue)}
.scroll{max-height:520px;overflow-y:auto}
.scroll::-webkit-scrollbar{width:3px}
.scroll::-webkit-scrollbar-thumb{background:var(--b2);border-radius:2px}
.rlist{padding:10px;display:flex;flex-direction:column;gap:7px}

/* ══ RECORD CARDS ══ */
.rcard{background:var(--s2);border:1px solid var(--b1);border-radius:4px;
  padding:12px 14px;cursor:pointer;transition:all .18s;position:relative;overflow:hidden}
.rcard::before{content:'';position:absolute;top:0;bottom:0;right:0;width:3px}
.rcard.trusted::before{background:var(--green)}
.rcard.review::before{background:var(--yellow)}
.rcard.rejected::before{background:var(--red)}
.rcard:hover{border-color:var(--blue);transform:translateX(-2px);
  box-shadow:0 4px 20px rgba(30,144,255,.1)}
.rcard.active-card{border-color:var(--blue);background:rgba(30,144,255,.05)}
.rtop{display:flex;align-items:center;justify-content:space-between;margin-bottom:7px}
.rid{font-family:var(--mono);font-size:10px;color:var(--dim)}
.rstatus{font-size:10px;font-weight:700;padding:2px 8px;border-radius:3px}
.trusted .rstatus{color:var(--green);background:rgba(0,230,118,.08);border:1px solid rgba(0,230,118,.2)}
.review .rstatus{color:var(--yellow);background:rgba(255,234,0,.08);border:1px solid rgba(255,234,0,.2)}
.rejected .rstatus{color:var(--red);background:rgba(255,23,68,.08);border:1px solid rgba(255,23,68,.2)}
.rmeta{display:flex;gap:10px;margin-bottom:7px;flex-wrap:wrap}
.mchip{font-size:11px;font-weight:600;color:var(--bright)}
.mchip span{font-size:10px;font-weight:400;color:var(--dim);margin-right:2px}
.tmeter{display:flex;align-items:center;gap:8px}
.tmbar{flex:1;height:3px;background:var(--s3);border-radius:2px;overflow:hidden}
.tmfill{height:100%;border-radius:2px;transition:width 1s}
.trusted .tmfill{background:linear-gradient(90deg,#00b851,var(--green))}
.review .tmfill{background:linear-gradient(90deg,#c4a000,var(--yellow))}
.rejected .tmfill{background:linear-gradient(90deg,#cc1133,var(--red))}
.tval{font-family:var(--mono);font-size:10px;min-width:44px;text-align:left}
.trusted .tval{color:var(--green)}.review .tval{color:var(--yellow)}.rejected .tval{color:var(--red)}
.mini-badges{display:flex;gap:5px;margin-top:6px;flex-wrap:wrap}
.mb{font-family:var(--mono);font-size:8px;padding:1px 6px;border-radius:2px}
.mb.mc{background:rgba(224,64,251,.1);border:1px solid rgba(224,64,251,.3);color:var(--purple)}
.mb.ma{background:rgba(255,109,0,.1);border:1px solid rgba(255,109,0,.3);color:var(--orange)}
.mb.mb2{background:rgba(0,212,255,.1);border:1px solid rgba(0,212,255,.3);color:var(--cyan)}
.mb.mn{background:rgba(255,102,204,.1);border:1px solid rgba(255,102,204,.3);color:var(--pink)}

/* ══ DETAIL PANEL ══ */
.dpanel{padding:14px}
.dempty{height:240px;display:flex;flex-direction:column;align-items:center;
  justify-content:center;color:var(--dim);font-family:var(--mono);font-size:11px;gap:10px}
.dempty-icon{font-size:28px;opacity:.2}
.drid{font-family:var(--mono);font-size:9px;letter-spacing:2px;color:var(--dim);margin-bottom:10px}
.dscore{display:flex;align-items:center;gap:12px;padding:12px;
  background:var(--s2);border-radius:4px;border:1px solid var(--b1);margin-bottom:12px}
.scircle{width:58px;height:58px;border-radius:50%;border:3px solid;
  display:flex;align-items:center;justify-content:center;flex-shrink:0}
.scval{font-family:var(--mono);font-size:17px;font-weight:700}
.smeta h3{font-size:13px;font-weight:700;margin-bottom:2px}
.smeta p{font-size:11px;color:var(--dim)}
.isec{margin-bottom:10px}
.isec-t{font-family:var(--mono);font-size:8px;letter-spacing:2px;color:var(--dim);
  margin-bottom:5px;text-transform:uppercase}
.iitem{padding:7px 10px;background:var(--s2);border-right:3px solid var(--red);
  border-radius:2px;margin-bottom:3px;font-size:12px;line-height:1.5;color:var(--text)}
.sitem{padding:7px 10px;background:rgba(0,212,255,.04);border-right:3px solid var(--cyan);
  border-radius:2px;margin-bottom:3px;font-size:12px;line-height:1.5}
.drow{display:flex;justify-content:space-between;padding:5px 10px;
  background:var(--s2);margin-bottom:2px;border-radius:2px;font-size:11px;border:1px solid var(--b1)}
.drow-k{color:var(--dim)}.drow-v{font-family:var(--mono);color:var(--bright)}

/* ══ INSIGHTS GRID ══ */
.ins-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;padding:14px}
.ins-card{background:var(--s2);border:1px solid var(--b1);border-radius:4px;padding:14px}
.ins-title{font-family:var(--mono);font-size:8px;letter-spacing:2px;color:var(--dim);
  margin-bottom:8px;text-transform:uppercase}
.ins-val{font-family:var(--mono);font-size:26px;font-weight:700;margin-bottom:3px}
.ins-sub{font-size:11px;color:var(--dim);margin-bottom:8px}
.alert-i{padding:6px 9px;border-radius:2px;font-size:11px;line-height:1.5;
  margin-bottom:4px;border:1px solid}
.alert-i.w{background:rgba(255,234,0,.04);border-color:rgba(255,234,0,.2);color:#ffe066}
.alert-i.i{background:rgba(30,144,255,.04);border-color:rgba(30,144,255,.2);color:#88aaff}

/* ══ BAYESIAN TABLE ══ */
.btable{width:100%;border-collapse:collapse;font-size:12px}
.btable th{font-family:var(--mono);font-size:8px;letter-spacing:1px;color:var(--dim);
  padding:8px 12px;text-align:right;border-bottom:1px solid var(--b1);text-transform:uppercase}
.btable td{padding:8px 12px;border-bottom:1px solid rgba(13,58,110,.4)}
.btable tr:last-child td{border-bottom:none}
.btable tr:hover td{background:rgba(30,144,255,.03)}

/* ══ CALIBRATION ══ */
.cal-e{padding:8px 14px;border-bottom:1px solid var(--b1);font-size:12px;
  display:flex;align-items:center;gap:10px}
.cal-e:last-child{border-bottom:none}
.cal-arr{color:var(--cyan);font-family:var(--mono)}

/* ══ ROOT CAUSE ══ */
.rcgrid{padding:14px;display:flex;flex-direction:column;gap:7px}
.rcitem{padding:10px 14px;border-radius:3px;font-size:13px;line-height:1.6;
  border:1px solid;position:relative;padding-right:38px}
.rcitem.red{background:rgba(255,23,68,.04);border-color:rgba(255,23,68,.2);color:#ff8899}
.rcitem.yellow{background:rgba(255,234,0,.04);border-color:rgba(255,234,0,.2);color:#ffe066}
.rcitem.blue{background:rgba(30,144,255,.04);border-color:rgba(30,144,255,.2);color:#88aaff}
.rcicon{position:absolute;right:11px;top:50%;transform:translateY(-50%);font-size:14px}

/* ══ AL LOG ══ */
.alentry{padding:10px 14px;border-bottom:1px solid var(--b1);
  display:flex;align-items:flex-start;gap:10px;font-size:12px}
.alentry:last-child{border-bottom:none}
.alind{width:22px;height:22px;border-radius:3px;display:flex;align-items:center;
  justify-content:center;font-size:11px;flex-shrink:0;
  background:rgba(0,230,118,.1);border:1px solid rgba(0,230,118,.3)}
.alpat{font-family:var(--mono);font-size:10px;color:var(--blue);margin-bottom:2px}
.alreason{color:var(--dim);line-height:1.5}

/* ══ JUDGE PAGE ══ */
#page-judge{display:none;position:fixed;inset:0;background:var(--bg);z-index:500;
  overflow-y:auto;padding:32px}
.judge-wrap{max-width:1100px;margin:0 auto}
.judge-header{text-align:center;margin-bottom:40px;padding:32px;
  background:linear-gradient(135deg,var(--s1),var(--s2));
  border:1px solid var(--b1);border-radius:var(--r);position:relative;overflow:hidden}
.judge-header::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;
  background:linear-gradient(90deg,var(--blue),var(--cyan),var(--green),var(--purple))}
.judge-title{font-size:36px;font-weight:900;color:var(--bright);margin-bottom:8px;letter-spacing:-1px}
.judge-sub{font-family:var(--mono);font-size:12px;color:var(--cyan);letter-spacing:3px}
.judge-desc{font-size:15px;color:var(--dim);margin-top:12px;max-width:600px;margin-left:auto;margin-right:auto}
.judge-kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:28px}
.jkpi{background:var(--s1);border:1px solid var(--b1);border-radius:var(--r);
  padding:24px;text-align:center;position:relative;overflow:hidden}
.jkpi::after{content:'';position:absolute;bottom:0;left:0;right:0;height:3px}
.jkpi.j0::after{background:var(--blue)}.jkpi.j1::after{background:var(--green)}
.jkpi.j2::after{background:var(--yellow)}.jkpi.j3::after{background:var(--purple)}
.jkpi-val{font-family:var(--mono);font-size:42px;font-weight:700;margin-bottom:6px}
.jkpi.j0 .jkpi-val{color:var(--blue)}.jkpi.j1 .jkpi-val{color:var(--green)}
.jkpi.j2 .jkpi-val{color:var(--yellow)}.jkpi.j3 .jkpi-val{color:var(--purple)}
.jkpi-lbl{font-size:13px;color:var(--dim)}
.judge-layers{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:28px}
.jlayer{background:var(--s1);border:1px solid var(--b1);border-radius:var(--r);
  padding:18px;position:relative;overflow:hidden}
.jlayer::before{content:'';position:absolute;top:0;right:0;bottom:0;width:3px}
.jlayer.tech::before{background:var(--blue)}
.jlayer.stat::before{background:var(--green)}
.jlayer.ai::before{background:var(--purple)}
.jl-num{font-family:var(--mono);font-size:10px;color:var(--dim);margin-bottom:6px}
.jl-name{font-size:15px;font-weight:700;color:var(--bright);margin-bottom:5px}
.jl-ref{font-family:var(--mono);font-size:9px;color:var(--cyan);margin-bottom:8px}
.jl-desc{font-size:12px;color:var(--dim);line-height:1.6}
.judge-charts{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:28px}
.jchart{background:var(--s1);border:1px solid var(--b1);border-radius:var(--r);padding:20px}
.jchart-title{font-family:var(--mono);font-size:10px;letter-spacing:2px;color:var(--cyan);
  text-transform:uppercase;margin-bottom:16px}
.btn-close-judge{position:fixed;top:20px;left:20px;z-index:600;
  background:rgba(255,23,68,.15);border:1px solid rgba(255,23,68,.4);
  color:var(--red);font-family:var(--mono);font-size:11px;padding:8px 16px;
  border-radius:4px;cursor:pointer;letter-spacing:1px}
.btn-close-judge:hover{background:rgba(255,23,68,.3)}

footer{text-align:center;padding:14px;font-family:var(--mono);font-size:8px;
  letter-spacing:2px;color:var(--dim);border-top:1px solid var(--b1);
  text-transform:uppercase;margin-top:4px}

@keyframes fadeUp{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
.fu{animation:fadeUp .3s ease forwards}

[data-lang="en"] .ar{display:none}
[data-lang="ar"] .en{display:none}
</style>
</head>
<body>
<div class="wrap" id="main-page">

<!-- HEADER -->
<header>
  <div class="logo-area">
    <div class="logo-box">🛡</div>
    <div class="logo-text">
      <h1>DataTrust Engine</h1>
      <p class="ar">محرك موثوقية البيانات · v3.0 · GASTAT</p>
      <p class="en" style="font-family:var(--mono);font-size:9px;color:var(--cyan);letter-spacing:3px">DATA RELIABILITY ENGINE · v3.0 · GASTAT</p>
    </div>
  </div>
  <div class="hdr-center" id="hdr-center"></div>
  <div class="hdr-right">
    <div class="status-pill"><span class="pulse"></span><span class="ar">النظام يعمل</span><span class="en">ONLINE</span></div>
    <span id="clk" style="font-family:var(--mono);font-size:11px;color:var(--blue)"></span>
    <button class="btn btn-lang" onclick="toggleLang()">EN / عر</button>
    <button class="btn btn-judge" onclick="showJudge()">
      <span class="ar">🏆 عرض المحكمين</span><span class="en">🏆 Judge View</span>
    </button>
  </div>
</header>

<!-- FILTER BAR -->
<div class="filter-bar">
  <span class="filter-lbl ar">فلتر</span><span class="filter-lbl en">FILTER</span>
  <button class="fbtn active" onclick="setF('all',this)"><span class="ar">الكل</span><span class="en">All</span></button>
  <button class="fbtn ft" onclick="setF('trusted',this)"><span class="ar">✅ موثوق</span><span class="en">✅ Trusted</span></button>
  <button class="fbtn fr" onclick="setF('review',this)"><span class="ar">⚠️ مراجعة</span><span class="en">⚠️ Review</span></button>
  <button class="fbtn fj" onclick="setF('rejected',this)"><span class="ar">🚨 مرفوض</span><span class="en">🚨 Rejected</span></button>
  <button class="fbtn fc" onclick="setF('causal',this)"><span class="ar">🔗 سببي</span><span class="en">🔗 Causal</span></button>
  <button class="fbtn fa" onclick="setF('adversarial',this)"><span class="ar">🛡 تلاعب</span><span class="en">🛡 Adversarial</span></button>
  <button class="fbtn fn" onclick="setF('attention',this)"><span class="ar">🔀 دلالي</span><span class="en">🔀 Semantic</span></button>
</div>

<!-- KPIs -->
<div class="kpi-grid">
  <div class="kpi k0">
    <div class="kpi-lbl ar">إجمالي</div><div class="kpi-lbl en" style="display:none">TOTAL</div>
    <div class="kpi-val" id="kv0">0</div>
    <div class="kpi-sub ar">سجل محلل</div><div class="kpi-sub en" style="display:none">records</div>
  </div>
  <div class="kpi k1">
    <div class="kpi-lbl ar">موثوقة</div><div class="kpi-lbl en" style="display:none">TRUSTED</div>
    <div class="kpi-val" id="kv1">0</div>
    <div class="kpi-sub" id="ks1">—</div>
  </div>
  <div class="kpi k2">
    <div class="kpi-lbl ar">مراجعة</div><div class="kpi-lbl en" style="display:none">REVIEW</div>
    <div class="kpi-val" id="kv2">0</div>
    <div class="kpi-sub" id="ks2">—</div>
  </div>
  <div class="kpi k3">
    <div class="kpi-lbl ar">مرفوضة</div><div class="kpi-lbl en" style="display:none">REJECTED</div>
    <div class="kpi-val" id="kv3">0</div>
    <div class="kpi-sub" id="ks3">—</div>
  </div>
  <div class="kpi k4">
    <div class="kpi-lbl ar">نسبة الخطأ</div><div class="kpi-lbl en" style="display:none">ERROR RATE</div>
    <div class="kpi-val" id="kv4" style="font-size:22px">—</div>
    <div class="kpi-sub ar">مجموع المشكلات</div><div class="kpi-sub en" style="display:none">total issues</div>
  </div>
  <div class="kpi k5">
    <div class="kpi-lbl ar">تحيز اجتماعي</div><div class="kpi-lbl en" style="display:none">SOCIAL BIAS</div>
    <div class="kpi-val" id="kv5">—</div>
    <div class="kpi-sub" id="ks5">—</div>
  </div>
</div>

<!-- TRUST BAR -->
<div class="tbar-row">
  <div class="tbar-lbl ar">توزيع الثقة</div><div class="tbar-lbl en" style="display:none">TRUST DISTRIBUTION</div>
  <div class="tbar">
    <div class="tbar-seg st" id="bs" style="width:0%"></div>
    <div class="tbar-seg sr" id="br" style="width:0%"></div>
    <div class="tbar-seg sj" id="bj" style="width:0%"></div>
  </div>
  <div class="tbar-legend">
    <div class="tleg"><div class="tleg-dot" style="background:var(--green)"></div><span class="ar">موثوق</span><span class="en">Trusted</span></div>
    <div class="tleg"><div class="tleg-dot" style="background:var(--yellow)"></div><span class="ar">مراجعة</span><span class="en">Review</span></div>
    <div class="tleg"><div class="tleg-dot" style="background:var(--red)"></div><span class="ar">مرفوض</span><span class="en">Rejected</span></div>
  </div>
</div>

<!-- CHARTS ROW -->
<div class="charts-row">
  <div class="chart-card">
    <div class="chart-title ar">توزيع الحالات</div><div class="chart-title en" style="display:none">STATUS DISTRIBUTION</div>
    <canvas id="chart-donut"></canvas>
  </div>
  <div class="chart-card">
    <div class="chart-title ar">توزيع درجات الثقة</div><div class="chart-title en" style="display:none">TRUST SCORE HISTOGRAM</div>
    <canvas id="chart-hist"></canvas>
  </div>
  <div class="chart-card">
    <div class="chart-title ar">الأخطاء حسب المنطقة</div><div class="chart-title en" style="display:none">ERRORS BY REGION</div>
    <canvas id="chart-region"></canvas>
  </div>
</div>

<!-- PIPELINE -->
<div class="pipeline">
  <div style="font-family:var(--mono);font-size:9px;letter-spacing:2px;color:var(--cyan);text-transform:uppercase;margin-bottom:14px" class="ar">مسار المعالجة — 12 طبقة</div>
  <div style="font-family:var(--mono);font-size:9px;letter-spacing:2px;color:var(--cyan);text-transform:uppercase;margin-bottom:14px" class="en">PROCESSING PIPELINE — 12 LAYERS</div>
  <div class="pipe-scroll">
    <div class="lnode"><div class="lcirc">🌐</div><div class="llbl">L0 Cultural NLP</div></div><div class="pconn"></div>
    <div class="lnode"><div class="lcirc">📊</div><div class="llbl">L1 Statistical</div></div><div class="pconn"></div>
    <div class="lnode"><div class="lcirc">🔧</div><div class="llbl">L2 Recovery</div></div><div class="pconn"></div>
    <div class="lnode"><div class="lcirc">🤖</div><div class="llbl">L3 LLM Semantic</div></div><div class="pconn"></div>
    <div class="lnode"><div class="lcirc">💡</div><div class="llbl">L4 Explain</div></div><div class="pconn"></div>
    <div class="lnode"><div class="lcirc">🧬</div><div class="llbl">L5 Active Learn</div></div><div class="pconn"></div>
    <div class="lnode"><div class="lcirc">🔍</div><div class="llbl">L6 Root Cause</div></div><div class="pconn"></div>
    <div class="lnode"><div class="lcirc">🔗</div><div class="llbl">L7 Causal</div></div><div class="pconn"></div>
    <div class="lnode"><div class="lcirc">📈</div><div class="llbl">L8 Bayesian</div></div><div class="pconn"></div>
    <div class="lnode"><div class="lcirc">🛡</div><div class="llbl">L9 Adversarial</div></div><div class="pconn"></div>
    <div class="lnode"><div class="lcirc">📉</div><div class="llbl">L10 Bias Drift</div></div><div class="pconn"></div>
    <div class="lnode"><div class="lcirc">🔀</div><div class="llbl">L11 Attention</div></div>
  </div>
</div>

<!-- TABS -->
<div class="tabs">
  <div class="tab active" onclick="switchTab('records',this)"><span class="ar">📋 السجلات</span><span class="en">📋 Records</span></div>
  <div class="tab" onclick="switchTab('insights',this)"><span class="ar">🧠 التحليلات</span><span class="en">🧠 Insights</span></div>
  <div class="tab" onclick="switchTab('bayesian',this)">📊 Bayesian</div>
  <div class="tab" onclick="switchTab('calibration',this)"><span class="ar">🌐 Cultural NLP</span><span class="en">🌐 Cultural NLP</span></div>
</div>

<!-- TAB: RECORDS -->
<div class="tpane active" id="tab-records">
  <div class="main-grid">
    <div class="panel">
      <div class="phdr">
        <span class="ptitle ar">السجلات</span><span class="ptitle en" style="display:none">RECORDS</span>
        <span class="pbadge" id="rc-badge">0</span>
      </div>
      <div class="scroll"><div class="rlist" id="rlist"></div></div>
    </div>
    <div class="panel">
      <div class="phdr">
        <span class="ptitle ar">تفاصيل السجل</span><span class="ptitle en" style="display:none">DETAIL</span>
        <span class="pbadge ar">تحليل</span><span class="pbadge en" style="display:none">Analysis</span>
      </div>
      <div class="dpanel" id="dpanel">
        <div class="dempty">
          <div class="dempty-icon">🔍</div>
          <span class="ar">اختر سجلاً</span><span class="en">Select a record</span>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- TAB: INSIGHTS -->
<div class="tpane" id="tab-insights">
  <div class="ins-grid" id="ins-grid"></div>
</div>

<!-- TAB: BAYESIAN -->
<div class="tpane" id="tab-bayesian">
  <div style="padding:16px">
    <table class="btable">
      <thead><tr>
        <th class="ar">المنطقة</th><th class="en" style="display:none">Region</th>
        <th>Posterior Trust</th>
        <th class="ar">السجلات</th><th class="en" style="display:none">Records</th>
        <th class="ar">الحالة</th><th class="en" style="display:none">Status</th>
      </tr></thead>
      <tbody id="btbody"></tbody>
    </table>
  </div>
</div>

<!-- TAB: CALIBRATION -->
<div class="tpane" id="tab-calibration">
  <div id="cal-list"></div>
</div>

<!-- ROOT CAUSE -->
<div style="background:var(--s1);border:1px solid var(--b1);border-radius:var(--r);margin-bottom:14px">
  <div class="phdr">
    <span class="ptitle ar">تحليل الأسباب الجذرية</span>
    <span class="ptitle en" style="display:none">ROOT CAUSE ANALYSIS</span>
    <span class="pbadge" id="er-badge">—</span>
  </div>
  <div class="rcgrid" id="rcgrid"></div>
</div>

<!-- AL LOG -->
<div style="background:var(--s1);border:1px solid var(--b1);border-radius:var(--r);margin-bottom:14px">
  <div class="phdr">
    <span class="ptitle ar">التعلم النشط</span>
    <span class="ptitle en" style="display:none">ACTIVE LEARNING</span>
    <span class="pbadge ar">استثناءات</span><span class="pbadge en" style="display:none">Exceptions</span>
  </div>
  <div id="alentries"></div>
</div>

<footer>DataTrust Engine v3.0 · 12-Layer AI System · GASTAT Hackathon 2025 · Pearl(2009) · Vaswani(2017) · Goodfellow(2014) · Paulhus(1984) · Gelman et al.</footer>
</div>

<!-- ══════════════════════════════════════════ -->
<!-- JUDGE PAGE -->
<!-- ══════════════════════════════════════════ -->
<div id="page-judge">
  <button class="btn-close-judge" onclick="hideJudge()">✕ <span class="ar">إغلاق</span><span class="en">CLOSE</span></button>
  <div class="judge-wrap">
    <div class="judge-header">
      <div class="judge-title">DataTrust Engine</div>
      <div class="judge-sub">GASTAT HACKATHON 2025 · DATA RELIABILITY AI SYSTEM</div>
      <div class="judge-desc ar">نظام ذكاء اصطناعي متكامل للتحقق من موثوقية البيانات الاستبيانية في السياق السعودي — 12 طبقة حماية مبنية على أحدث الأبحاث العلمية</div>
      <div class="judge-desc en">A comprehensive AI system for verifying survey data reliability in the Saudi context — 12 protection layers built on cutting-edge research</div>
    </div>

    <div class="judge-kpis" id="judge-kpis"></div>

    <div style="font-family:var(--mono);font-size:9px;letter-spacing:3px;color:var(--cyan);text-transform:uppercase;margin-bottom:14px">
      <span class="ar">الطبقات التقنية</span><span class="en">TECHNICAL LAYERS</span>
    </div>
    <div class="judge-layers">
      <div class="jlayer tech"><div class="jl-num">LAYER 0–2</div><div class="jl-name ar">المعالجة الأساسية</div><div class="jl-name en" style="display:none">Core Processing</div><div class="jl-ref">Cultural NLP · Statistical · Recovery</div><div class="jl-desc ar">تطبيع اللهجة السعودية، اكتشاف الشواذ الإحصائية، استرداد القيم الناقصة ذكياً</div><div class="jl-desc en" style="display:none">Saudi dialect normalization, statistical anomaly detection, intelligent missing value recovery</div></div>
      <div class="jlayer stat"><div class="jl-num">LAYER 3–6</div><div class="jl-name ar">الذكاء الدلالي</div><div class="jl-name en" style="display:none">Semantic Intelligence</div><div class="jl-ref">LLM Semantic · Explainability · Active Learning · Root Cause</div><div class="jl-desc ar">فهم السياق بالذكاء الاصطناعي، تحليل الأسباب الجذرية، تعلم من قرارات المراجع</div><div class="jl-desc en" style="display:none">AI context understanding, root cause analysis, learning from reviewer decisions</div></div>
      <div class="jlayer ai"><div class="jl-num">LAYER 7–11</div><div class="jl-name ar">الطبقات المتقدمة</div><div class="jl-name en" style="display:none">Advanced AI Layers</div><div class="jl-ref">Pearl(2009) · Gelman · Goodfellow(2014) · Paulhus(1984) · Vaswani(2017)</div><div class="jl-desc ar">استدلال سببي، ثقة بايزية، كشف التلاعب، مراقبة التحيز، انتباه دلالي متقاطع</div><div class="jl-desc en" style="display:none">Causal inference, Bayesian trust, adversarial detection, bias monitoring, cross-feature semantic attention</div></div>
    </div>

    <div class="judge-charts">
      <div class="jchart">
        <div class="jchart-title ar">توزيع الحالات</div><div class="jchart-title en" style="display:none">STATUS DISTRIBUTION</div>
        <canvas id="j-donut"></canvas>
      </div>
      <div class="jchart">
        <div class="jchart-title ar">توزيع درجات الثقة</div><div class="jchart-title en" style="display:none">TRUST SCORE DISTRIBUTION</div>
        <canvas id="j-hist"></canvas>
      </div>
    </div>

    <div style="background:var(--s1);border:1px solid var(--b1);border-radius:var(--r);padding:20px;margin-bottom:20px">
      <div style="font-family:var(--mono);font-size:9px;letter-spacing:2px;color:var(--cyan);text-transform:uppercase;margin-bottom:14px" class="ar">توصيات النظام للهيئة</div>
      <div style="font-family:var(--mono);font-size:9px;letter-spacing:2px;color:var(--cyan);text-transform:uppercase;margin-bottom:14px" class="en">SYSTEM RECOMMENDATIONS</div>
      <div id="judge-recs"></div>
    </div>
  </div>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
<script>
const D  = """ + data_blob + """;
const AL = """ + al_blob + """;

let curFilter = 'all';
let curLang   = 'ar';

Chart.defaults.color = '#4a7a9b';
Chart.defaults.borderColor = '#0d3a6e';
Chart.defaults.font.family = 'Space Mono, monospace';
Chart.defaults.font.size   = 10;

// ── Clock ──
setInterval(()=>{ document.getElementById('clk').textContent = new Date().toLocaleTimeString('en-US'); },1000);

// ── Lang ──
function toggleLang(){
  curLang = curLang==='ar'?'en':'ar';
  document.documentElement.setAttribute('data-lang',curLang);
  document.documentElement.setAttribute('dir',curLang==='ar'?'rtl':'ltr');
  renderRecords();
}

// ── Counter ──
function animCount(id, target, suffix=''){
  let v=0; const el=document.getElementById(id);
  if(!el)return;
  const t=setInterval(()=>{
    v=Math.min(v+Math.ceil(Math.max(1,target/25)),target);
    el.textContent=v+suffix;
    if(v>=target)clearInterval(t);
  },40);
}
function pct(n){ return D.total?Math.round(n/D.total*100):0; }

animCount('kv0',D.total);
animCount('kv1',D.trusted);
animCount('kv2',D.review);
animCount('kv3',D.rejected);
document.getElementById('kv4').textContent = D.error_rate;
document.getElementById('ks1').textContent = pct(D.trusted)+'%';
document.getElementById('ks2').textContent = pct(D.review)+'%';
document.getElementById('ks3').textContent = pct(D.rejected)+'%';
document.getElementById('er-badge').textContent = 'نسبة الخطأ: '+D.error_rate;

const bs = D.bias.score;
document.getElementById('kv5').textContent = bs>=0.4?'عالٍ':bs>=0.2?'متوسط':'منخفض';
document.getElementById('ks5').textContent = 'score: '+bs;

setTimeout(()=>{
  document.getElementById('bs').style.width = pct(D.trusted)+'%';
  document.getElementById('br').style.width = pct(D.review)+'%';
  document.getElementById('bj').style.width = pct(D.rejected)+'%';
},500);

// header center stats
document.getElementById('hdr-center').innerHTML = [
  ['#1e90ff',D.total,'إجمالي'],
  ['#00e676',D.trusted,'موثوق'],
  ['#ffea00',D.review,'مراجعة'],
  ['#ff1744',D.rejected,'مرفوض'],
].map(([c,v,l])=>`<div class="hdr-stat">
  <div class="hdr-stat-val" style="color:${c}">${v}</div>
  <div class="hdr-stat-lbl">${l}</div>
</div>`).join('');

// ── Charts ──
function makeDonut(id){
  const ctx = document.getElementById(id);
  if(!ctx)return null;
  return new Chart(ctx,{
    type:'doughnut',
    data:{
      labels:['موثوق','مراجعة','مرفوض'],
      datasets:[{
        data:[D.trusted,D.review,D.rejected],
        backgroundColor:['rgba(0,230,118,.7)','rgba(255,234,0,.7)','rgba(255,23,68,.7)'],
        borderColor:['#00e676','#ffea00','#ff1744'],
        borderWidth:2,hoverOffset:8
      }]
    },
    options:{
      responsive:true,maintainAspectRatio:true,
      plugins:{legend:{position:'bottom',labels:{padding:12,boxWidth:10}},
        tooltip:{callbacks:{label:c=>' '+c.label+': '+c.raw+' ('+Math.round(c.raw/D.total*100)+'%)'}}},
      cutout:'68%',animation:{animateRotate:true,duration:1200}
    }
  });
}

function makeHist(id){
  const ctx = document.getElementById(id);
  if(!ctx)return null;
  const labels=['0-9','10-19','20-29','30-39','40-49','50-59','60-69','70-79','80-89','90-100'];
  const colors = D.score_buckets.map((_,i)=>
    i>=8?'rgba(0,230,118,.75)':i>=5?'rgba(255,234,0,.75)':'rgba(255,23,68,.75)');
  return new Chart(ctx,{
    type:'bar',
    data:{labels,datasets:[{data:D.score_buckets,backgroundColor:colors,borderWidth:0,borderRadius:2}]},
    options:{
      responsive:true,maintainAspectRatio:true,
      plugins:{legend:{display:false}},
      scales:{
        x:{grid:{color:'rgba(13,58,110,.5)'},ticks:{font:{size:9}}},
        y:{grid:{color:'rgba(13,58,110,.5)'},ticks:{stepSize:1}}
      },
      animation:{duration:1000}
    }
  });
}

function makeRegion(id){
  const ctx = document.getElementById(id);
  if(!ctx||!D.region_stats)return null;
  const regions = Object.keys(D.region_stats);
  const trusted_d = regions.map(r=>D.region_stats[r].trusted||0);
  const review_d  = regions.map(r=>D.region_stats[r].review||0);
  const reject_d  = regions.map(r=>D.region_stats[r].rejected||0);
  return new Chart(ctx,{
    type:'bar',
    data:{labels:regions,datasets:[
      {label:'موثوق',data:trusted_d,backgroundColor:'rgba(0,230,118,.7)',borderRadius:2},
      {label:'مراجعة',data:review_d,backgroundColor:'rgba(255,234,0,.7)',borderRadius:2},
      {label:'مرفوض',data:reject_d,backgroundColor:'rgba(255,23,68,.7)',borderRadius:2},
    ]},
    options:{
      responsive:true,maintainAspectRatio:true,
      plugins:{legend:{position:'bottom',labels:{padding:10,boxWidth:8}}},
      scales:{
        x:{stacked:true,grid:{display:false},ticks:{font:{size:9}}},
        y:{stacked:true,grid:{color:'rgba(13,58,110,.5)'}}
      },animation:{duration:1000}
    }
  });
}

setTimeout(()=>{
  makeDonut('chart-donut');
  makeHist('chart-hist');
  makeRegion('chart-region');
},300);

// ── Tabs ──
function switchTab(id,el){
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  document.querySelectorAll('.tpane').forEach(t=>t.classList.remove('active'));
  el.classList.add('active');
  document.getElementById('tab-'+id).classList.add('active');
}

// ── Filter ──
function setF(f,btn){
  curFilter=f;
  document.querySelectorAll('.fbtn').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  renderRecords();
}
function passes(rec){
  if(curFilter==='all')        return true;
  if(curFilter==='trusted')    return rec.status_class==='trusted';
  if(curFilter==='review')     return rec.status_class==='review';
  if(curFilter==='rejected')   return rec.status_class==='rejected';
  if(curFilter==='causal')     return rec.causal_flag===true;
  if(curFilter==='adversarial')return rec.adv_flag===true;
  if(curFilter==='attention')  return rec.attn_flag===true;
  return true;
}

// ── Records ──
function renderRecords(){
  const list=document.getElementById('rlist');
  list.innerHTML='';
  const vis=D.records.filter(passes);
  document.getElementById('rc-badge').textContent=vis.length+(curLang==='ar'?' سجل':' records');
  vis.forEach((rec,i)=>{
    const card=document.createElement('div');
    card.className='rcard '+rec.status_class+' fu';
    card.style.animationDelay=(i*.04)+'s';
    card.dataset.id=rec.id;
    const chips=Object.entries(rec.row_data).slice(0,3)
      .map(([k,v])=>`<span class="mchip">${v} <span>${k}</span></span>`).join('');
    const bgs=[];
    if(rec.causal_flag) bgs.push(`<span class="mb mc">causal ${rec.causal_prob}</span>`);
    if(rec.adv_flag)    bgs.push(`<span class="mb ma">adv ${rec.adv_score}</span>`);
    if(rec.attn_flag)   bgs.push(`<span class="mb mn">attn ${rec.attn_score}</span>`);
    if(rec.bayesian_score!==rec.trust_score) bgs.push(`<span class="mb mb2">bayes ${rec.bayesian_score}</span>`);
    card.innerHTML=`
      <div class="rtop">
        <span class="rid">REC_${String(rec.id).padStart(3,'0')} · ${rec.region}</span>
        <span class="rstatus">${rec.status}</span>
      </div>
      ${chips?`<div class="rmeta">${chips}</div>`:''}
      <div class="tmeter">
        <div class="tmbar"><div class="tmfill" style="width:${rec.trust_score}%"></div></div>
        <span class="tval">${rec.trust_score}/100</span>
      </div>
      ${bgs.length?`<div class="mini-badges">${bgs.join('')}</div>`:''}`;
    card.onclick=()=>showDetail(rec,card);
    list.appendChild(card);
  });
}

function showDetail(rec,cardEl){
  document.querySelectorAll('.rcard').forEach(c=>c.classList.remove('active-card'));
  cardEl.classList.add('active-card');
  const col={trusted:'var(--green)',review:'var(--yellow)',rejected:'var(--red)'}[rec.status_class];
  const rowHtml=Object.entries(rec.row_data)
    .map(([k,v])=>`<div class="drow"><span class="drow-k">${k}</span><span class="drow-v">${v}</span></div>`).join('');
  const issHtml=rec.issues.length
    ?rec.issues.map(i=>`<div class="iitem">${i}</div>`).join('')
    :`<div class="iitem" style="border-right-color:var(--green);color:var(--green)">✅ لا مشكلات</div>`;
  const sugHtml=rec.suggestions.length
    ?`<div class="isec"><div class="isec-t">${curLang==='ar'?'توصيات':'Suggestions'}</div>${rec.suggestions.map(s=>`<div class="sitem">${s}</div>`).join('')}</div>`:'';
  const causalHtml=rec.causal_prob!==null
    ?`<div class="isec"><div class="isec-t">Causal · Pearl 2009</div><div class="iitem" style="border-right-color:var(--purple)">🔗 ${rec.causal_interp}</div></div>`:'';
  const advHtml=rec.adv_flag
    ?`<div class="isec"><div class="isec-t">Adversarial · GAN</div><div class="iitem" style="border-right-color:var(--orange)">🛡 score: ${rec.adv_score}</div></div>`:'';
  const attnHtml=rec.attn_flag
    ?`<div class="isec"><div class="isec-t">Semantic Attention · Vaswani 2017</div><div class="iitem" style="border-right-color:var(--pink)">🔀 ${rec.attn_interp}</div></div>`:'';
  document.getElementById('dpanel').innerHTML=`<div class="fu">
    <div class="drid">REC_${String(rec.id).padStart(3,'0')}</div>
    <div class="dscore">
      <div class="scircle" style="border-color:${col}"><span class="scval" style="color:${col}">${rec.trust_score}</span></div>
      <div class="smeta">
        <h3 style="color:${col}">${rec.status}</h3>
        <p>Trust: ${rec.trust_score}/100</p>
        <p style="font-family:var(--mono);font-size:10px;color:var(--cyan);margin-top:2px">Bayesian: ${rec.bayesian_score}</p>
      </div>
    </div>
    <div class="isec"><div class="isec-t">${curLang==='ar'?'المشكلات':'Issues'}</div>${issHtml}</div>
    ${sugHtml}${causalHtml}${advHtml}${attnHtml}
    ${rowHtml?`<div class="isec"><div class="isec-t">${curLang==='ar'?'البيانات':'Data'}</div>${rowHtml}</div>`:''}
  </div>`;
}

// ── Insights ──
function renderInsights(){
  const grid=document.getElementById('ins-grid');
  const caF=D.records.filter(r=>r.causal_flag).length;
  const adF=D.records.filter(r=>r.adv_flag).length;
  const atF=D.records.filter(r=>r.attn_flag).length;
  const bc=D.bias.score>=0.4?'var(--red)':D.bias.score>=0.2?'var(--yellow)':'var(--green)';
  grid.innerHTML=`
    <div class="ins-card">
      <div class="ins-title">🔗 Causal · Pearl 2009</div>
      <div class="ins-val" style="color:var(--purple)">${caF}</div>
      <div class="ins-sub ar">سببي مشبوه</div><div class="ins-sub en" style="display:none">Causal flags</div>
      ${D.records.filter(r=>r.causal_flag).slice(0,3).map(r=>`<div class="alert-i w">REC_${String(r.id).padStart(3,'0')}: ${r.causal_interp}</div>`).join('')}
    </div>
    <div class="ins-card">
      <div class="ins-title">🛡 Adversarial · GAN</div>
      <div class="ins-val" style="color:var(--orange)">${adF}</div>
      <div class="ins-sub ar">تلاعب محتمل</div><div class="ins-sub en" style="display:none">Adversarial flags</div>
      ${D.records.filter(r=>r.adv_flag).slice(0,3).map(r=>`<div class="alert-i w">REC_${String(r.id).padStart(3,'0')}: score ${r.adv_score}</div>`).join('')}
    </div>
    <div class="ins-card">
      <div class="ins-title">🔀 Attention · Vaswani 2017</div>
      <div class="ins-val" style="color:var(--pink)">${atF}</div>
      <div class="ins-sub ar">تناقض دلالي</div><div class="ins-sub en" style="display:none">Semantic conflicts</div>
      ${D.records.filter(r=>r.attn_flag).slice(0,3).map(r=>`<div class="alert-i w">REC_${String(r.id).padStart(3,'0')}: ${r.attn_interp}</div>`).join('')}
    </div>
    <div class="ins-card">
      <div class="ins-title">📉 Bias · Paulhus 1984</div>
      <div class="ins-val" style="color:${bc}">${D.bias.score}</div>
      <div class="ins-sub">${D.bias.level||'—'}</div>
      ${D.bias.alerts.map(a=>`<div class="alert-i w">${a}</div>`).join('')||'<div class="alert-i i">لا تنبيهات</div>'}
    </div>`;
}

// ── Bayesian ──
function renderBayesian(){
  const tb=document.getElementById('btbody');
  if(!D.bayesian||!D.bayesian.length){
    tb.innerHTML='<tr><td colspan="4" style="padding:14px;color:var(--dim);font-family:var(--mono);font-size:11px">لا توجد بيانات</td></tr>';return;
  }
  tb.innerHTML=D.bayesian.map(b=>{
    const c=b.posterior_trust>=0.75?'var(--green)':b.posterior_trust<0.55?'var(--red)':'var(--yellow)';
    return `<tr>
      <td style="font-family:var(--mono);color:var(--blue)">${b.researcher}</td>
      <td><span style="color:${c};font-family:var(--mono);font-weight:700">${(b.posterior_trust*100).toFixed(1)}%</span></td>
      <td style="color:var(--dim)">${b.records_evaluated}</td>
      <td style="color:${c}">${b.status}</td>
    </tr>`;
  }).join('');
}

// ── Calibration ──
function renderCalibration(){
  const el=document.getElementById('cal-list');
  if(!D.calibration||!D.calibration.length){
    el.innerHTML='<div style="padding:14px;color:var(--dim);font-family:var(--mono);font-size:11px">لم يتم تطبيع أي قيم</div>';return;
  }
  el.innerHTML=D.calibration.map(c=>`<div class="cal-e">
    <span style="font-family:var(--mono);font-size:10px;color:var(--dim)">REC_${String(c.record_id).padStart(3,'0')} [${c.field}]</span>
    <span>${c.original}</span><span class="cal-arr">→</span>
    <span style="color:var(--cyan)">${c.normalized}</span>
  </div>`).join('');
}

// ── Root Cause ──
function renderRC(){
  const rg=document.getElementById('rcgrid');
  if(D.recs.length){
    D.recs.forEach(r=>{
      const el=document.createElement('div');
      el.className='rcitem '+r.type+' fu';
      el.innerHTML=`<span class="rcicon">${r.icon}</span>${r.text}`;
      rg.appendChild(el);
    });
  } else {
    rg.innerHTML='<div style="padding:12px;color:var(--dim);font-family:var(--mono);font-size:11px">✅ لا توصيات</div>';
  }
}

// ── Active Learning ──
function renderAL(){
  const el=document.getElementById('alentries');
  if(AL&&AL.exceptions&&AL.exceptions.length){
    AL.exceptions.forEach(ex=>{
      const pat=Object.entries(ex.pattern||{}).map(([k,v])=>k+'='+v).join('، ');
      const d=document.createElement('div');
      d.className='alentry';
      d.innerHTML=`<div class="alind">✅</div><div><div class="alpat">${pat} → ${ex.correct_verdict}</div><div class="alreason">${ex.reason}</div></div>`;
      el.appendChild(d);
    });
  } else {
    el.innerHTML='<div style="padding:12px 14px;color:var(--dim);font-family:var(--mono);font-size:11px">لا استثناءات بعد</div>';
  }
}

// ── JUDGE PAGE ──
function showJudge(){
  document.getElementById('page-judge').style.display='block';
  document.getElementById('main-page').style.display='none';

  // KPIs
  document.getElementById('judge-kpis').innerHTML=[
    ['j0',D.total,'إجمالي السجلات','TOTAL RECORDS'],
    ['j1',pct(D.trusted)+'%','نسبة الموثوقية','RELIABILITY RATE'],
    ['j2',D.error_rate,'نسبة المشكلات','ISSUE RATE'],
    ['j3','12','طبقة حماية','AI LAYERS'],
  ].map(([c,v,ar,en])=>`<div class="jkpi ${c}">
    <div class="jkpi-val">${v}</div>
    <div class="jkpi-lbl ar">${ar}</div><div class="jkpi-lbl en" style="display:none">${en}</div>
  </div>`).join('');

  // Recs
  const rg=document.getElementById('judge-recs');
  rg.innerHTML='';
  D.recs.forEach(r=>{
    const el=document.createElement('div');
    el.className='rcitem '+r.type;
    el.style.marginBottom='8px';
    el.innerHTML=`<span class="rcicon">${r.icon}</span>${r.text}`;
    rg.appendChild(el);
  });

  setTimeout(()=>{
    makeDonut('j-donut');
    makeHist('j-hist');
  },200);
}

function hideJudge(){
  document.getElementById('page-judge').style.display='none';
  document.getElementById('main-page').style.display='block';
}

// ── INIT ──
renderRecords();
renderInsights();
renderBayesian();
renderCalibration();
renderRC();
renderAL();
</script>
</body>
</html>"""

    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".html", delete=False,
        encoding="utf-8", prefix="datatrust_"
    )
    tmp.write(html)
    tmp.close()
    print(f"\n✅ Dashboard جاهز → {tmp.name}")
    webbrowser.open(f"file://{tmp.name}")
    return tmp.name