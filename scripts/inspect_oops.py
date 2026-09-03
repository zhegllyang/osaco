# -*- coding: utf-8 -*-
"""OOPS! 보고서(RDF/XML, rdf:Description 기반)를 파싱해 결함별 코드·이름·중요도·영향 요소 출력"""
import xml.etree.ElementTree as ET
from pathlib import Path

path = Path(__file__).parent / "ontology_outputs" / "oops_report.xml"
root = ET.parse(path).getroot()
RDF = "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}"

def local(tag):
    return tag.split("}")[-1]

n = 0
for desc in root.iter(f"{RDF}Description"):
    info, affected = {}, []
    for ch in desc:
        name = local(ch.tag)
        if name == "hasAffectedElement":
            affected.append((ch.get(f"{RDF}resource") or (ch.text or "")).strip()
                            .replace("https://w3id.org/osaco/", "osaco:"))
        else:
            info[name] = (ch.text or "").strip() or ch.get(f"{RDF}resource", "")
    if "hasCode" not in info:
        continue
    n += 1
    print(f"{info['hasCode']} [{info.get('hasImportanceLevel','')}] {info.get('hasName','')} "
          f"— 영향 {info.get('hasNumberAffectedElements', len(affected))}")
    for a in affected[:15]:
        print("    ", a[:110])
    if len(affected) > 15:
        print(f"     ... 외 {len(affected)-15}개")
print(f"\n결함 유형 {n}개")
