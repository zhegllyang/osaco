# -*- coding: utf-8 -*-
"""패싯 파서 독립 검증: SHHS 변수 id에 부호화된 패싯 vs display_name에서 파싱한 패싯
SHHS 호흡이벤트/산소포화도 id 문법(접미 부분): <stage n|r><position b|o><arousal a|p><desat digit?>
  n=NREM r=REM | b=back(supine) o=other(non-supine) | a=with arousal p=plain | 2-5 = >=d% desat, 없음 = 전체
실행: python validate_facet_parser.py  → ontology_outputs/facet_parser_validation.xlsx
"""
import re
from pathlib import Path

import pandas as pd

OUTD = Path(__file__).parent / "ontology_outputs"
design = pd.read_excel(OUTD / "OSA_ontology_class_design.xlsx", sheet_name=None)
# MESA는 동일 문법에 Exam 접미사 '5'가 붙음(avdnbp5) → 접미사 제거 후 동일 규칙 적용
mesa = design["MESA_패싯전체"].copy()
mesa["id"] = mesa["id"].str.replace(r"5$", "", regex=True)
sh = pd.concat([design["SHHS_패싯전체"].assign(cohort="SHHS"), mesa.assign(cohort="MESA")], ignore_index=True)

GRAMMAR = re.compile(r"(nr|n|r)([bo])([ap])(\d?)$")   # 저호흡 id는 NREM을 'nr'로 표기 (hnrba vs hroa)
STAGE = {"n": "NREM", "nr": "NREM", "r": "REM"}
POS = {"b": "앙와위", "o": "비앙와위"}
AROUSAL = {"a": "각성포함", "p": "각성무관"}

rows = []
for _, r in sh.iterrows():
    m = GRAMMAR.search(str(r["id"]).lower())
    if not m:
        continue                       # 문법 밖 id(요약 지수 등)는 검증 대상에서 제외
    st, po, ar, dg = m.groups()
    exp = {"수면단계": STAGE[st], "체위": POS[po], "각성기준": AROUSAL[ar],
           "desat기준": f">={dg}%" if dg else "전체/무기준"}
    got = {k: str(r[k]) for k in exp}
    rows.append({"cohort": r["cohort"], "id": r["id"], **{f"{k}_id": v for k, v in exp.items()},
                 **{f"{k}_parsed": got[k] for k in exp},
                 **{f"{k}_match": exp[k] == got[k] for k in exp},
                 "all_match": all(exp[k] == got[k] for k in exp)})

v = pd.DataFrame(rows)
n = len(v)
print(f"id 문법에 해당하는 축약 변수: {n}개 / 전체 {len(sh)}개 "
      f"(SHHS {int((v['cohort']=='SHHS').sum())}, MESA {int((v['cohort']=='MESA').sum())})")
for k in ("수면단계", "체위", "각성기준", "desat기준"):
    print(f"  {k}: 일치 {v[f'{k}_match'].sum()}/{n} ({v[f'{k}_match'].mean()*100:.1f}%)")
print(f"  4차원 전부 일치: {v['all_match'].sum()}/{n} ({v['all_match'].mean()*100:.1f}%)")
bad = v[~v["all_match"]]
if len(bad):
    print("\n불일치 상세:")
    print(bad[["id"] + [c for c in v.columns if c.endswith("_id") or c.endswith("_parsed")]].to_string(index=False))
v.to_excel(OUTD / "facet_parser_validation.xlsx", index=False)
