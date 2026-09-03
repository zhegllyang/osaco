# -*- coding: utf-8 -*-
"""패싯 분해·클래스 설계표 재생성 (최종 파서 — 노트북 [5]·[7] 셀과 동일 로직)
입력: ontology_outputs/OSA_variable_inventory_v2.xlsx (SHHS_축약, MESA_축약)
출력: OSA_facet_decomposition.xlsx, OSA_ontology_class_design.xlsx
실행: python regenerate_design.py
"""
import re
from pathlib import Path

import pandas as pd

OUTD = Path(__file__).parent / "ontology_outputs"
inv = pd.read_excel(OUTD / "OSA_variable_inventory_v2.xlsx", sheet_name=None)

EVENTS = [
    (r"Central/Obstructive Apnea ratio", "중추/폐쇄비"),
    (r"Respiratory Disturbance Index|\bRDI\b", "호흡장애종합"),
    (r"Central Apnea-Hypopnea", "중추성무호흡+저호흡"),
    (r"Obstructive Apnea-Hypopnea", "폐쇄성무호흡+저호흡"),
    (r"Apnea-Hypopnea", "무호흡+저호흡"),
    (r"Obstructive Apneas?", "폐쇄성무호흡"),
    (r"Central Apneas?", "중추성무호흡"),
    (r"Hypopneas?", "저호흡"),
    (r"\bapneas?\b", "무호흡(전체)"),
    (r"oxygen desaturations?", "산소탈포화"),
    (r"oxygen saturation|SaO2", "산소포화도"),
]
MEASURES = [
    (r"\bratio\b", "비율"),
    (r"^Average (length|duration)|^Average .* length", "평균길이"),
    (r"^Longest|^Maxim", "최대"),
    (r"^Minimum|^Min\b|^Shortest", "최소"),
    (r"Index|per hour|/ ?hour", "지수"),
    (r"^Total number|^Number", "빈도"),
    (r"^Percent", "시간비율"),
    (r"^Total", "총량"),
    (r"^Average", "평균수준"),
]
AROUSAL = re.compile(r"w/ arousals?|\bwith arousals?|or (with )?arousal", re.I)

def parse_facets(dn):
    t = dn if isinstance(dn, str) else ""
    d = {}
    d["수면단계"] = "NREM" if re.search(r"\bNREM\b", t) else ("REM" if re.search(r"\bREM\b", t) else "전체")
    if re.search(r"non-?supine", t, re.I): d["체위"] = "비앙와위"
    elif re.search(r"\bsupine\b", t, re.I): d["체위"] = "앙와위"
    else: d["체위"] = "전체"
    m = re.search(r">=\s*(\d)\s*%", t)
    m2 = re.search(r"<\s*(\d+)\s*%", t)
    if m: d["desat기준"] = f">={m.group(1)}%"
    elif m2: d["desat기준"] = f"<{m2.group(1)}%"
    elif re.search(r"all oxygen desat|no oxygen desaturation threshold", t, re.I): d["desat기준"] = "전체/무기준"
    else: d["desat기준"] = "미지정"
    d["각성기준"] = "각성포함" if AROUSAL.search(t) else "각성무관"
    d["이벤트"] = next((ev for pat, ev in EVENTS if re.search(pat, t, re.I)), "?")
    d["측정치"] = next((mt for pat, mt in MEASURES if re.search(pat, t, re.I)), "?")
    return d

# id 문법 보조 근거: 표시명이 탈포화 기준을 언급하지 않을 때(미지정) NSRR id 접미 문법으로 보완
#   <stage n|nr|r><position b|o><arousal a|p><desat digit?> — 숫자 없음 = 전체 이벤트(무기준)
ID_GRAMMAR = re.compile(r"(nr|n|r)([bo])([ap])(\d?)$")
def desat_from_id(vid):
    m = ID_GRAMMAR.search(re.sub(r"5$", "", str(vid).lower()))   # MESA Exam 접미사 제거
    if not m:
        return None
    return f">={m.group(4)}%" if m.group(4) else "전체/무기준"

fac = {}
n_idfill = {}
with pd.ExcelWriter(OUTD / "OSA_facet_decomposition.xlsx", engine="openpyxl") as xw:
    for name in ("SHHS", "MESA"):
        sub = inv[f"{name}_축약"].copy().reset_index(drop=True)
        F = sub["display_name"].map(parse_facets).apply(pd.Series)
        sub = pd.concat([sub, F], axis=1)
        fill = sub["desat기준"].eq("미지정") & sub["id"].map(desat_from_id).notna()
        sub.loc[fill, "desat기준"] = sub.loc[fill, "id"].map(desat_from_id)
        n_idfill[name] = int(fill.sum())
        fac[name] = sub
        unk = sub[(sub["이벤트"] == "?") | (sub["측정치"] == "?")]
        print(f"{name}: 축약 {len(sub)}개, 파싱 실패 {len(unk)}개, id 문법으로 탈포화 기준 보완 {n_idfill[name]}건")
        sub.to_excel(xw, sheet_name=f"{name}_패싯", index=False)
        (sub.groupby(["측정치", "이벤트", "수면단계", "체위", "desat기준", "각성기준"])
            .size().rename("변수수").reset_index()
            .to_excel(xw, sheet_name=f"{name}_조합", index=False))

EV_EN = {"폐쇄성무호흡": "ObstructiveApnea", "중추성무호흡": "CentralApnea", "저호흡": "Hypopnea",
         "무호흡+저호흡": "ApneaHypopnea", "중추성무호흡+저호흡": "CentralApneaHypopnea",
         "폐쇄성무호흡+저호흡": "ObstructiveApneaHypopnea", "산소탈포화": "OxygenDesaturation",
         "산소포화도": "OxygenSaturation", "중추/폐쇄비": "CentralToObstructiveApnea",
         "호흡장애종합": "RespiratoryDisturbance", "무호흡(전체)": "Apnea"}
SAT_EVENTS = {"산소포화도", "산소탈포화"}
MT_EN_EVENT = {"지수": "Index", "빈도": "Count", "최대": "MaximumLength", "최소": "MinimumLength",
               "평균길이": "AverageLength", "평균수준": "AverageLevel", "시간비율": "PercentTime",
               "총량": "Total", "비율": "Ratio"}
MT_EN_SAT = {**MT_EN_EVENT, "최대": "Maximum", "최소": "Minimum"}

def class_name(ev, mt):
    return f"{EV_EN.get(ev, 'X')}{(MT_EN_SAT if ev in SAT_EVENTS else MT_EN_EVENT).get(mt, 'X')}"

rows = []
for (ev, mt), _ in pd.concat([fac["SHHS"], fac["MESA"]]).groupby(["이벤트", "측정치"]):
    sh = fac["SHHS"].query("이벤트 == @ev and 측정치 == @mt")
    me = fac["MESA"].query("이벤트 == @ev and 측정치 == @mt")
    rows.append({"클래스명": class_name(ev, mt), "이벤트": ev, "측정치": mt,
                 "n_SHHS": len(sh), "n_MESA": len(me),
                 "SHHS예시": sh["id"].iloc[0] if len(sh) else "",
                 "MESA예시": me["id"].iloc[0] if len(me) else ""})
fam = pd.DataFrame(rows).sort_values(["n_SHHS", "n_MESA"], ascending=False)

FACET_PROPS = pd.DataFrame([
    {"속성명": "hasSleepStageScope",       "차원": "수면단계",  "허용값": "REMSleep | NREMSleep | AllSleep"},
    {"속성명": "hasBodyPositionScope",     "차원": "체위",     "허용값": "SupinePosition | NonSupinePosition | AllPositions"},
    {"속성명": "hasDesaturationThreshold", "차원": "desat기준", "허용값": "2% | 3% | 4% | 5% | <90%abs | NoThreshold"},
    {"속성명": "hasArousalCriterion",      "차원": "각성기준",  "허용값": "WithArousal | ArousalNotRequired"},
    {"속성명": "hasCohortProvenance",      "차원": "출처",     "허용값": "SHHS1 | SHHS2 | MESA-Exam5"},
])
with pd.ExcelWriter(OUTD / "OSA_ontology_class_design.xlsx", engine="openpyxl") as xw:
    fam.to_excel(xw, sheet_name="측정클래스(패싯패밀리)", index=False)
    FACET_PROPS.to_excel(xw, sheet_name="패싯속성정의", index=False)
    fac["SHHS"].to_excel(xw, sheet_name="SHHS_패싯전체", index=False)
    fac["MESA"].to_excel(xw, sheet_name="MESA_패싯전체", index=False)
print(f"측정 클래스 {len(fam)}개 | 각성포함 SHHS {(fac['SHHS']['각성기준']=='각성포함').sum()} / MESA {(fac['MESA']['각성기준']=='각성포함').sum()}")
