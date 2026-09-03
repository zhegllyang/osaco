# -*- coding: utf-8 -*-
"""HermiT reasoner 일관성 검사 (owlready2 내장 HermiT, Java 필요)
실행: python run_reasoner.py
"""
import sys
from pathlib import Path

import owlready2
from owlready2 import get_ontology, sync_reasoner, Nothing

owlready2.JAVA_EXE = r"C:\Program Files\Eclipse Adoptium\jre-21.0.12.101-hotspot\bin\java.exe"
OUTD = Path(__file__).parent / "ontology_outputs"

onto = get_ontology("file://" + (OUTD / "osaco.owl").resolve().as_posix()).load()  # Windows 경로: 슬래시 2개 형식
n_cls = len(list(onto.classes()))
n_ind = len(list(onto.individuals()))
n_op = len(list(onto.object_properties()))
print(f"로드: 클래스 {n_cls}, 개체 {n_ind}, 객체속성 {n_op}")

try:
    with onto:
        sync_reasoner(infer_property_values=False, debug=0)
except owlready2.OwlReadyInconsistentOntologyError:
    print("결과: 온톨로지 비일관(inconsistent)")
    sys.exit(1)

unsat = [c for c in onto.classes() if Nothing in c.equivalent_to]
print(f"결과: 일관(consistent) | 불만족(unsatisfiable) 클래스 {len(unsat)}개")
for c in unsat[:10]:
    print("  -", c.name)
