# -*- coding: utf-8 -*-
"""OSACO 역량 질문(Competency Question) SPARQL 검증
실행: python run_competency_questions.py
"""
from pathlib import Path
from rdflib import Graph

OUTD = Path(__file__).parent / "ontology_outputs"
g = Graph()
g.parse(OUTD / "osaco.ttl", format="turtle")
print(f"로드: {len(g):,} 트리플\n")

PREFIX = """
PREFIX osaco: <https://w3id.org/osaco/>
PREFIX rdfs:  <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX skos:  <http://www.w3.org/2004/02/skos/core#>
PREFIX owl:   <http://www.w3.org/2002/07/owl#>
"""

CQS = [
    ("CQ1. REM 수면·앙와위에서 폐쇄성 무호흡 횟수를 측정하는 변수는? (코호트 포함)", """
     SELECT ?cohort ?id ?label WHERE {
       ?v rdf:type osaco:ObstructiveApneaCount ;
          osaco:hasSleepStageScope osaco:REMSleep ;
          osaco:hasBodyPositionScope osaco:SupinePosition ;
          osaco:nsrrVariableId ?id ; osaco:sourceCohort ?cohort ; rdfs:label ?label .
     } ORDER BY ?cohort ?id LIMIT 10"""),

    ("CQ2. 두 코호트 모두에서 측정 가능한 PSG 측정 패밀리는?", """
     SELECT DISTINCT ?fam WHERE {
       ?fam rdfs:subClassOf osaco:PolysomnographyMeasure .
       FILTER EXISTS { ?vs rdf:type ?fam ; osaco:sourceCohort "SHHS" }
       FILTER EXISTS { ?vm rdf:type ?fam ; osaco:sourceCohort "MESA" }
     } ORDER BY ?fam"""),

    ("CQ3. SNOMED CT에 등가(exactMatch) 매핑된 개념 수와 예시", """
     SELECT ?c ?m WHERE {
       ?c skos:exactMatch ?m .
       FILTER(CONTAINS(STR(?m), "snomed.info"))
     } LIMIT 8"""),

    ("CQ4. 주간졸림(ESS) 도구와 연관된 설문 문항 개념은?", """
     SELECT DISTINCT ?c ?label WHERE {
       ?c skos:relatedMatch <http://snomed.info/id/708735004> ;
          rdfs:label ?label .
     } LIMIT 10"""),

    ("CQ5. >=4% 산소포화도 저하 기준을 쓰는 변수의 측정 패밀리별 분포는?", """
     SELECT ?fam (COUNT(?v) AS ?n) WHERE {
       ?v osaco:hasDesaturationThreshold osaco:Desat4Pct ; rdf:type ?fam .
       ?fam rdfs:subClassOf osaco:PolysomnographyMeasure .
     } GROUP BY ?fam ORDER BY DESC(?n) LIMIT 10"""),

    ("CQ6. 동일 NSRR 변수 id로 두 코호트에 존재하는 변수는? (교차 코호트 앵커)", """
     SELECT ?id (COUNT(DISTINCT ?cohort) AS ?n) WHERE {
       ?v osaco:nsrrVariableId ?id ; osaco:sourceCohort ?cohort .
     } GROUP BY ?id HAVING (COUNT(DISTINCT ?cohort) > 1) ORDER BY ?id LIMIT 15"""),

    ("CQ7. 심혈관 결과(CardiovascularOutcome) 개념 중 심근경색에 앵커된 것은?", """
     SELECT ?c ?label WHERE {
       ?c rdfs:subClassOf osaco:CardiovascularOutcome ; rdfs:label ?label ;
          skos:relatedMatch <http://purl.obolibrary.org/obo/MONDO_0005068> .
     } LIMIT 10"""),
]

def short(u):
    s = str(u)
    for pre in ("https://w3id.org/osaco/", "http://snomed.info/id/",
                "http://purl.obolibrary.org/obo/", "http://www.ebi.ac.uk/efo/"):
        s = s.replace(pre, "")
    return s

import time
for title, q in CQS:
    print("=" * 70)
    print(title)
    t0 = time.time()
    rows = list(g.query(PREFIX + q))
    print(f"  [{time.time() - t0:.1f}s]")
    if not rows:
        print("  !! 결과 없음")
        continue
    for row in rows:
        print("  " + " | ".join(short(x)[:60] if x is not None else "-" for x in row))
    print(f"  ({len(rows)}건)")
