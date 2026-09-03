# -*- coding: utf-8 -*-
"""E5 준거 타당도 추세 검정 + E4 유병률 95% CI
실행: python run_trend_stats.py
"""
import numpy as np
import pandas as pd
from scipy import stats

SHHS_CSV = r"Y:\Dataset\shhs\datasets\shhs1-dataset-0.14.0.csv"
MESA_CSV = r"Y:\Dataset\mesa\datasets\mesa-sleep-dataset-0.8.0.csv"

def load(path, cols):
    df = pd.read_csv(path, usecols=lambda c: c.lower() in cols, low_memory=False)
    df.columns = df.columns.str.lower()
    return df

sh = load(SHHS_CSV, {"ahi_a0h4", "htnderv_s1", "bmi_s1", "ess_s1"})
me = load(MESA_CSV, {"ahi_a0h4", "bmi5c", "epslpscl5c"})

def sev(s):
    return pd.cut(s, [-1, 5, 15, 30, 1e9], labels=[0, 1, 2, 3]).astype("float")

def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z**2 / n
    c = (p + z**2 / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / d
    return c - h, c + h

# ── HTN by severity (SHHS): Cochran–Armitage trend (linear-by-linear chi-square) ──
d = sh.dropna(subset=["ahi_a0h4", "htnderv_s1"]).copy()
d["sev"] = sev(d["ahi_a0h4"])
tab = pd.crosstab(d["sev"], d["htnderv_s1"])
# 선형 추세: 점수(0..3)와 이진 결과의 상관 기반 카이제곱 (Mantel-Haenszel linear association)
r, _ = stats.pearsonr(d["sev"], d["htnderv_s1"])
chi2_trend = (len(d) - 1) * r**2
p_trend = stats.chi2.sf(chi2_trend, df=1)
print(f"SHHS HTN 추세: N={len(d)}, chi2_trend={chi2_trend:.1f}, p={p_trend:.2e}")

# ── BMI by severity: Spearman + Kruskal–Wallis ──
for name, df, bmi in [("SHHS", sh, "bmi_s1"), ("MESA", me, "bmi5c")]:
    d = df.dropna(subset=["ahi_a0h4", bmi]).copy()
    d["sev"] = sev(d["ahi_a0h4"])
    rho, p = stats.spearmanr(d["sev"], d[bmi])
    groups = [g[bmi].values for _, g in d.groupby("sev")]
    kw = stats.kruskal(*groups)
    print(f"{name} BMI: N={len(d)}, Spearman rho={rho:.3f} (p={p:.1e}), Kruskal-Wallis H={kw.statistic:.1f} (p={kw.pvalue:.1e})")

# ── E4 OSA 증후군 유병률 95% CI ──
for name, df, ess in [("SHHS", sh, "ess_s1"), ("MESA", me, "epslpscl5c")]:
    d = df.dropna(subset=["ahi_a0h4", ess])
    k = int(((d["ahi_a0h4"] >= 15) & (d[ess] > 10)).sum())
    lo, hi = wilson(k, len(d))
    print(f"{name} OSA 증후군: {k}/{len(d)} = {k/len(d)*100:.1f}% (95% CI {lo*100:.1f}–{hi*100:.1f})")

# ── E3 정의 민감도 극단값 CI ──
for name, df in [("SHHS", sh), ("MESA", me)]:
    a = df["ahi_a0h4"].dropna()
    k = int((a >= 15).sum()); lo, hi = wilson(k, len(a))
    print(f"{name} AHI(4%)>=15: {k/len(a)*100:.1f}% (95% CI {lo*100:.1f}–{hi*100:.1f})")
