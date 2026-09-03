# -*- coding: utf-8 -*-
"""OOPS! (OntOlogy Pitfall Scanner) REST 스캔
실행: python run_oops_scan.py  → ontology_outputs/oops_report.xml + 콘솔 요약
"""
import re
import urllib.request
from pathlib import Path

OUTD = Path(__file__).parent / "ontology_outputs"
owl = (OUTD / "osaco.owl").read_text(encoding="utf-8")

body = f"""<?xml version="1.0" encoding="UTF-8"?>
<OOPSRequest>
  <OntologyUrl></OntologyUrl>
  <OntologyContent><![CDATA[{owl}]]></OntologyContent>
  <Pitfalls></Pitfalls>
  <OutputFormat>RDF/XML</OutputFormat>
</OOPSRequest>"""

req = urllib.request.Request("https://oops.linkeddata.es/rest", data=body.encode("utf-8"),
                             headers={"Content-Type": "application/xml"}, method="POST")
with urllib.request.urlopen(req, timeout=600) as r:
    xml = r.read().decode("utf-8")
(OUTD / "oops_report.xml").write_text(xml, encoding="utf-8")

# 요약: 결함 코드·명칭·중요도·영향 요소 수
pitfalls = re.findall(
    r'<oops:hasCode[^>]*>(P\d+)</oops:hasCode>.*?<oops:hasName[^>]*>(.*?)</oops:hasName>.*?'
    r'<oops:hasImportanceLevel[^>]*>(.*?)</oops:hasImportanceLevel>.*?<oops:hasNumberAffectedElements[^>]*>(\d+)</oops:hasNumberAffectedElements>',
    xml, flags=re.S)
if not pitfalls:
    print("파싱된 결함 없음 — 원문 확인:", xml[:800])
for code, name, level, n in sorted(pitfalls):
    print(f"{code} [{level}] {name} — 영향 요소 {n}개")
print(f"\n총 결함 유형 {len(pitfalls)}개 | 보고서: {OUTD / 'oops_report.xml'}")
