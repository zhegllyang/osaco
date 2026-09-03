# -*- coding: utf-8 -*-
"""OSACO 실데이터 실증 (6단계)
E1 기술통계 | E2 AHI 중증도 분포 | E3 정의 민감도(패싯 영향) | E4 OSA 증후군 CQ 실증
E5 준거 타당도(HTN·BMI 연관) | E6 False friend 실증 | 결과: ontology_outputs/OSA_empirical_validation.xlsx
"""
from pathlib import Path
import pandas as pd

OUTD = Path(__file__).parent / "ontology_outputs"
SHHS_CSV = r"Y:\Dataset\shhs\datasets\shhs1-dataset-0.14.0.csv"
MESA_CSV = r"Y:\Dataset\mesa\datasets\mesa-sleep-dataset-0.8.0.csv"

SH_COLS = ["nsrrid", "ahi_a0h3", "ahi_a0h3a", "ahi_a0h4", "ahi_a0h4a",
           "ess_s1", "htnderv_s1", "bmi_s1", "age_s1", "gender", "avdnbp", "avdnbp5"]
ME_COLS = ["mesaid", "ahi_a0h3", "ahi_a0h3a", "ahi_a0h4", "ahi_a0h4a",
           "epslpscl5c", "bmi5c", "sleepage5c", "gender1", "avdnbp5"]

def load(path, want):
    head = pd.read_csv(path, nrows=0)
    cols = [c for c in head.columns if c.lower() in want]
    missing = set(want) - {c.lower() for c in cols}
    if missing:
        print(f"  !! 누락 컬럼: {sorted(missing)}")
    df = pd.read_csv(path, usecols=cols, low_memory=False)
    df.columns = df.columns.str.lower()
    return df

print("데이터 로드 중...")
sh = load(SHHS_CSV, set(SH_COLS))
me = load(MESA_CSV, set(ME_COLS))
print(f"SHHS1: {len(sh):,}명 | MESA: {len(me):,}명\n")

results = {}

# ── E1. 기술통계 ─────────────────────────────────────────────────────────
def desc(df, age, bmi, sexcol):
    return {"N": len(df),
            "연령 평균(SD)": f"{df[age].mean():.1f} ({df[age].std():.1f})",
            "BMI 평균(SD)": f"{df[bmi].mean():.1f} ({df[bmi].std():.1f})",
            "성별 코드분포": df[sexcol].value_counts().sort_index().to_dict()}
e1 = pd.DataFrame([{"cohort": "SHHS1", **desc(sh, "age_s1", "bmi_s1", "gender")},
                   {"cohort": "MESA", **desc(me, "sleepage5c", "bmi5c", "gender1")}])
results["E1_기술통계"] = e1
print("=== E1. 기술통계 ===")
print(e1.to_string(index=False), "\n")

# ── E2. AHI 중증도 분포 (ahi_a0h4: >=4% desat 기준) ──────────────────────
def severity(s):
    return pd.cut(s, [-1, 5, 15, 30, 10000],
                  labels=["정상(<5)", "경도(5-15)", "중등도(15-30)", "중증(>=30)"])
rows = []
for name, df in [("SHHS1", sh), ("MESA", me)]:
    for ahivar in ("ahi_a0h4", "ahi_a0h3a"):
        s = severity(df[ahivar].dropna())
        d = (s.value_counts(normalize=True).sort_index() * 100).round(1)
        rows.append({"cohort": name, "AHI정의": ahivar, "N": s.notna().sum(),
                     **{k: f"{v}%" for k, v in d.items()}})
e2 = pd.DataFrame(rows)
results["E2_중증도분포"] = e2
print("=== E2. AHI 중증도 분포 ===")
print(e2.to_string(index=False), "\n")

# ── E3. 정의 민감도: 같은 코호트, 다른 패싯(desat/각성) → AHI>=15 유병률 ──
rows = []
for name, df in [("SHHS1", sh), ("MESA", me)]:
    for v in ("ahi_a0h3", "ahi_a0h3a", "ahi_a0h4", "ahi_a0h4a"):
        s = df[v].dropna()
        rows.append({"cohort": name, "AHI정의(패싯)": v,
                     "중등도이상(>=15) %": round((s >= 15).mean() * 100, 1),
                     "중증(>=30) %": round((s >= 30).mean() * 100, 1)})
e3 = pd.DataFrame(rows)
results["E3_정의민감도"] = e3
print("=== E3. 정의 민감도 (패싯이 유병률에 미치는 영향) ===")
print(e3.to_string(index=False), "\n")

# ── E4. OSA 증후군 CQ 실증: AHI>=15 & ESS>10 ────────────────────────────
rows = []
for name, df, ess in [("SHHS1", sh, "ess_s1"), ("MESA", me, "epslpscl5c")]:
    sub = df[["ahi_a0h4", ess]].dropna()
    a = sub["ahi_a0h4"] >= 15
    e = sub[ess] > 10
    rows.append({"cohort": name, "N(완전사례)": len(sub),
                 "AHI>=15 %": round(a.mean() * 100, 1),
                 "ESS>10 %": round(e.mean() * 100, 1),
                 "AHI>=15 & ESS>10 %": round((a & e).mean() * 100, 1)})
e4 = pd.DataFrame(rows)
results["E4_증후군CQ"] = e4
print("=== E4. OSA 증후군 표현형 (AHI>=15 & ESS>10) ===")
print(e4.to_string(index=False), "\n")

# ── E5. 준거 타당도: 중증도별 HTN 유병률(SHHS)·BMI 평균(양 코호트) ───────
rows = []
sh2 = sh.dropna(subset=["ahi_a0h4"]).copy()
sh2["sev"] = severity(sh2["ahi_a0h4"])
for sev, grp in sh2.groupby("sev", observed=True):
    rows.append({"cohort": "SHHS1", "중증도": str(sev), "N": len(grp),
                 "HTN %": round(grp["htnderv_s1"].mean() * 100, 1),
                 "BMI 평균": round(grp["bmi_s1"].mean(), 1)})
me2 = me.dropna(subset=["ahi_a0h4"]).copy()
me2["sev"] = severity(me2["ahi_a0h4"])
for sev, grp in me2.groupby("sev", observed=True):
    rows.append({"cohort": "MESA", "중증도": str(sev), "N": len(grp),
                 "HTN %": None, "BMI 평균": round(grp["bmi5c"].mean(), 1)})
e5 = pd.DataFrame(rows)
results["E5_준거타당도"] = e5
print("=== E5. 준거 타당도 (중증도별 HTN·BMI — 단조 증가 기대) ===")
print(e5.to_string(index=False), "\n")

# ── E6. False friend 실증: avdnbp5 (id 동일, 의미 상이) ──────────────────
pairs = [
    ("SHHS avdnbp5 (>=5% desat 이벤트 평균저하)", sh["avdnbp5"]),
    ("SHHS avdnbp  (전체 desat 이벤트 평균저하)", sh["avdnbp"]),
    ("MESA avdnbp5 (전체 desat 이벤트 평균저하, Exam5)", me["avdnbp5"]),
]
rows = []
for label, s in pairs:
    s = s.dropna()
    rows.append({"변수": label, "N": len(s), "평균": round(s.mean(), 2),
                 "SD": round(s.std(), 2), "중앙값": round(s.median(), 2)})
e6 = pd.DataFrame(rows)
results["E6_falsefriend"] = e6
print("=== E6. False friend 실증 (id 매칭 vs 의미 매칭) ===")
print(e6.to_string(index=False))
d_wrong = abs(sh["avdnbp5"].mean() - me["avdnbp5"].mean())
d_right = abs(sh["avdnbp"].mean() - me["avdnbp5"].mean())
print(f"\n  id 매칭(SHHS avdnbp5 ↔ MESA avdnbp5) 평균 차이: {d_wrong:.2f}")
print(f"  의미 매칭(SHHS avdnbp ↔ MESA avdnbp5) 평균 차이: {d_right:.2f}")
print(f"  → 의미 매칭이 {'더 가까움 (온톨로지 매칭 타당)' if d_right < d_wrong else '더 멀다 (재검토 필요)'}\n")

# ── 저장 ─────────────────────────────────────────────────────────────────
with pd.ExcelWriter(OUTD / "OSA_empirical_validation.xlsx", engine="openpyxl") as xw:
    for name, df in results.items():
        df.to_excel(xw, sheet_name=name, index=False)
print("저장:", (OUTD / "OSA_empirical_validation.xlsx").resolve())
