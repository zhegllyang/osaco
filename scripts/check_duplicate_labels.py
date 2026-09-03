# -*- coding: utf-8 -*-
"""OSACO 클래스 라벨 중복 점검 (정확 일치 / 대소문자 무시)"""
from collections import defaultdict
from pathlib import Path

from rdflib import Graph, RDF, RDFS, OWL

g = Graph().parse(Path(__file__).parent / "ontology_outputs" / "osaco.ttl", format="turtle")
exact, ci = defaultdict(list), defaultdict(list)
for c in g.subjects(RDF.type, OWL.Class):
    for lab in g.objects(c, RDFS.label):
        s = str(lab)
        exact[s].append(str(c).split("/")[-1])
        ci[s.lower()].append(str(c).split("/")[-1])
dup_exact = {k: v for k, v in exact.items() if len(v) > 1}
dup_ci = {k: v for k, v in ci.items() if len(v) > 1}
print(f"정확 일치 중복 라벨: {len(dup_exact)}개 그룹 | 대소문자 무시 중복: {len(dup_ci)}개 그룹")
for k, v in list(dup_ci.items())[:12]:
    print(f"  '{k[:70]}' -> {v}")
