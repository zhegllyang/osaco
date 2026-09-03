# -*- coding: utf-8 -*-
"""OSACO (Obstructive Sleep Apnea Cohort Variable Ontology) OWL 빌드 스크립트

입력 (ontology_outputs/):
  - OSA_ontology_class_design.xlsx : 측정 클래스(패싯 패밀리) + 패싯 변수 전체
  - OSA_mapping_final.xlsx         : 개념별 표준 용어 매핑 (등가/관련/무매핑)
  - OSA_variable_inventory_v2.xlsx : 포함 변수 목록 (개념-변수 연결용)
출력:
  - ontology_outputs/osaco.ttl / osaco.owl
실행: python build_owl.py
"""
import re
from pathlib import Path

import pandas as pd
from rdflib import Graph, Literal, Namespace, RDF, RDFS, OWL, URIRef
from rdflib.namespace import DCTERMS, SKOS, XSD

BASE_DIR = Path(__file__).parent
OUTD = BASE_DIR / "ontology_outputs"
OSACO = Namespace("https://w3id.org/osaco/")

# ── 입력 로드 ─────────────────────────────────────────────────────────────
design = pd.read_excel(OUTD / "OSA_ontology_class_design.xlsx", sheet_name=None)
mapping = pd.read_excel(OUTD / "OSA_mapping_final.xlsx", sheet_name="최종매핑")
inv = {n: pd.read_excel(OUTD / "OSA_variable_inventory_v2.xlsx", sheet_name=f"{n}_포함")
       for n in ("SHHS", "MESA")}

g = Graph()
g.bind("osaco", OSACO)
g.bind("skos", SKOS)
g.bind("dcterms", DCTERMS)

# ── 온톨로지 헤더 ─────────────────────────────────────────────────────────
ONT = URIRef("https://w3id.org/osaco")
g.add((ONT, RDF.type, OWL.Ontology))
g.add((ONT, DCTERMS.title, Literal(
    "Obstructive Sleep Apnea Cohort Variable Ontology (OSACO)", lang="en")))
g.add((ONT, DCTERMS.description, Literal(
    "An application ontology of obstructive sleep apnea (OSA)-related variables, "
    "constructed from the Sleep Heart Health Study (SHHS v0.14.0) data dictionary "
    "and cross-validated against MESA (v0.8.0). Highly combinatorial polysomnography "
    "variables are modeled as measurement families with faceted properties "
    "(sleep stage, body position, desaturation threshold, arousal criterion). "
    "Concepts are cross-referenced to SNOMED CT, HPO, MONDO, and EFO via "
    "skos:exactMatch (equivalent) and skos:relatedMatch (related/broader).", lang="en")))
g.add((ONT, OWL.versionInfo, Literal("0.1.0")))
g.add((ONT, DCTERMS.source, Literal("National Sleep Research Resource (sleepdata.org): SHHS, MESA")))

def C(local):  # 클래스 URI
    return OSACO[local]

def add_class(local, label, parent=None, comment=None):
    u = C(local)
    g.add((u, RDF.type, OWL.Class))
    g.add((u, RDFS.label, Literal(label, lang="en")))
    if parent is not None:
        g.add((u, RDFS.subClassOf, parent))
    if comment:
        g.add((u, RDFS.comment, Literal(comment, lang="en")))
    return u

# ── 상위 클래스 ───────────────────────────────────────────────────────────
root = add_class("OSACohortConcept", "OSA cohort concept")
UPPER = {
    "PolysomnographyMeasure":  "Polysomnography-derived measure",
    "SleepQuestionnaireItem":  "Sleep questionnaire item",
    "SleepApneaTreatment":     "Sleep apnea treatment",
    "MedicalHistory":          "Medical history item",
    "CardiovascularOutcome":   "Cardiovascular outcome",
    "Medication":              "Medication use",
    "ClinicalMeasure":         "Clinical measurement",
    "AnthropometricMeasure":   "Anthropometric measurement",
    "Demographics":            "Demographic attribute",
    "LifestyleFactor":         "Lifestyle and behavioral factor",
    "AdministrativeVariable":  "Administrative variable (not mapped)",
}
for local, lab in UPPER.items():
    add_class(local, lab, root)

FOLDER2PARENT = [
    ("Measurements/Polysomnography", "PolysomnographyMeasure"),
    ("Harmonized/Polysomnography", "PolysomnographyMeasure"),
    ("Sleep and Circadian Studies/Polysomnography", "PolysomnographyMeasure"),
    ("Measurements/Blood Pressure", "ClinicalMeasure"),
    ("Measurements/Bloods", "ClinicalMeasure"),
    ("Measurements/Lung Function", "ClinicalMeasure"),
    ("Questionnaires/SHHS2/Physical Measurements", "ClinicalMeasure"),
    ("Measurements/Anthropometry", "AnthropometricMeasure"),
    ("Harmonized/Anthropometry", "AnthropometricMeasure"),
    ("Anthropometry", "AnthropometricMeasure"),
    ("Questionnaires", "SleepQuestionnaireItem"),
    ("Sleep Questionnaires", "SleepQuestionnaireItem"),
    ("Interim", "SleepQuestionnaireItem"),
    ("Sleep Treatment", "SleepApneaTreatment"),
    ("Medical History", "MedicalHistory"),
    ("CVD Outcomes", "CardiovascularOutcome"),
    ("Medications", "Medication"),
    ("Demographics", "Demographics"),
    ("Harmonized/Sociodemographics", "Demographics"),
    ("Sociodemographics", "Demographics"),
    ("Administrative", "Demographics"),
    ("Harmonized/Lifestyle", "LifestyleFactor"),
    ("Lifestyle and Behavioral Health", "LifestyleFactor"),
]
def parent_for(folder):
    f = str(folder)
    for prefix, p in FOLDER2PARENT:
        if f.startswith(prefix):
            return C(p)
    return root

# ── 패싯 값 클래스·개체 ───────────────────────────────────────────────────
FACETS = {
    "SleepStageScope": [("REMSleep", "REM sleep"), ("NREMSleep", "NREM sleep"),
                        ("AllSleepStages", "all sleep stages")],
    "BodyPositionScope": [("SupinePosition", "supine position"),
                          ("NonSupinePosition", "non-supine position"),
                          ("AllPositions", "all body positions")],
    "DesaturationThreshold": [("Desat2Pct", ">=2% desaturation"), ("Desat3Pct", ">=3% desaturation"),
                              ("Desat4Pct", ">=4% desaturation"), ("Desat5Pct", ">=5% desaturation"),
                              ("SatBelow90Abs", "saturation below 90% (absolute)"),
                              ("NoDesatThreshold", "no desaturation threshold"),
                              ("UnspecifiedThreshold", "unspecified threshold")],
    "ArousalCriterion": [("WithArousal", "with arousal"),
                         ("ArousalNotRequired", "arousal not required")],
}
for cls, values in FACETS.items():
    cu = add_class(cls, re.sub(r"(?<!^)([A-Z])", r" \1", cls).lower())
    for local, lab in values:
        vu = OSACO[local]
        g.add((vu, RDF.type, OWL.NamedIndividual))
        g.add((vu, RDF.type, cu))
        g.add((vu, RDFS.label, Literal(lab, lang="en")))

FACET_VALUE_MAP = {
    "수면단계": {"REM": "REMSleep", "NREM": "NREMSleep", "전체": "AllSleepStages"},
    "체위": {"앙와위": "SupinePosition", "비앙와위": "NonSupinePosition", "전체": "AllPositions"},
    "desat기준": {">=2%": "Desat2Pct", ">=3%": "Desat3Pct", ">=4%": "Desat4Pct",
                 ">=5%": "Desat5Pct", "<90%": "SatBelow90Abs", "전체/무기준": "NoDesatThreshold",
                 "미지정": "UnspecifiedThreshold"},
    "각성기준": {"각성포함": "WithArousal", "각성무관": "ArousalNotRequired"},
}

# ── 속성 정의 ─────────────────────────────────────────────────────────────
OBJ_PROPS = {
    "hasSleepStageScope": "SleepStageScope",
    "hasBodyPositionScope": "BodyPositionScope",
    "hasDesaturationThreshold": "DesaturationThreshold",
    "hasArousalCriterion": "ArousalCriterion",
}
for p, rng in OBJ_PROPS.items():
    pu = OSACO[p]
    g.add((pu, RDF.type, OWL.ObjectProperty))
    g.add((pu, RDFS.label, Literal(p, lang="en")))
    g.add((pu, RDFS.range, C(rng)))
for p in ("nsrrVariableId", "sourceCohort"):
    pu = OSACO[p]
    g.add((pu, RDF.type, OWL.DatatypeProperty))
    g.add((pu, RDFS.label, Literal(p, lang="en")))
    g.add((pu, RDFS.range, XSD.string))

# ── 표준 용어 IRI 변환 ────────────────────────────────────────────────────
def std_iri(cid):
    if not isinstance(cid, str) or ":" not in cid:
        return None
    prefix, local = cid.split(":", 1)
    prefix = prefix.upper()
    if prefix == "SNOMED":
        return URIRef(f"http://snomed.info/id/{local}")
    if prefix == "EFO":
        return URIRef(f"http://www.ebi.ac.uk/efo/EFO_{local}")
    return URIRef(f"http://purl.obolibrary.org/obo/{prefix}_{local}")

# ── 개념 클래스 (584 - 관리변수) ──────────────────────────────────────────
def slugify(label, used):
    words = re.findall(r"[A-Za-z0-9]+", str(label))
    s = "".join(w.capitalize() if not w.isupper() or len(w) > 4 else w for w in words)[:70]
    s = s or "Concept"
    base, n = s, 2
    while s in used:
        s = f"{base}_{n}"
        n += 1
    used.add(s)
    return s

used_slugs = set(UPPER) | set(FACETS) | {"OSACohortConcept"}
concept_uri = {}   # 개념라벨(lower) → URI
n_exact = n_related = 0
for _, r in mapping.iterrows():
    label = str(r["개념라벨"])
    if r["판정"] == "관리변수":
        concept_uri[label.lower()] = C("AdministrativeVariable")
        continue
    u = add_class(slugify(label, used_slugs), label)
    g.add((u, RDFS.subClassOf, parent_for(r.get("폴더예시", ""))))
    concept_uri[label.lower()] = u
    iri = std_iri(r.get("최종ID"))
    if iri is not None:
        if r["매핑유형"] == "등가":
            g.add((u, SKOS.exactMatch, iri))
            n_exact += 1
        else:
            g.add((u, SKOS.relatedMatch, iri))
            n_related += 1
        g.add((u, SKOS.note, Literal(f"{r['최종ID']} {r['최종라벨']} [{r['출처']}]")))

# ── 측정 패밀리 클래스 (32) + 패싯 변수 개체 (899) ────────────────────────
fam_sheet = design["측정클래스(패싯패밀리)"]
fam_uri = {}
for _, r in fam_sheet.iterrows():
    name = str(r["클래스명"])
    u = add_class(name if name not in used_slugs else name + "Family",
                  re.sub(r"(?<!^)([A-Z])", r" \1", name).lower(),
                  C("PolysomnographyMeasure"))
    used_slugs.add(name)
    fam_uri[(str(r["이벤트"]), str(r["측정치"]))] = u

n_facet_vars = 0
for cohort in ("SHHS", "MESA"):
    fv = design[f"{cohort}_패싯전체"]
    for _, r in fv.iterrows():
        key = (str(r["이벤트"]), str(r["측정치"]))
        fam = fam_uri.get(key)
        if fam is None:
            continue
        v = OSACO[f"var_{cohort.lower()}_{r['id']}"]
        g.add((v, RDF.type, OWL.NamedIndividual))
        g.add((v, RDF.type, fam))
        g.add((v, RDFS.label, Literal(str(r["display_name"]))))
        g.add((v, OSACO.nsrrVariableId, Literal(str(r["id"]))))
        g.add((v, OSACO.sourceCohort, Literal(cohort)))
        for col, prop in [("수면단계", "hasSleepStageScope"), ("체위", "hasBodyPositionScope"),
                          ("desat기준", "hasDesaturationThreshold"), ("각성기준", "hasArousalCriterion")]:
            val = FACET_VALUE_MAP[col].get(str(r[col]))
            if val:
                g.add((v, OSACO[prop], OSACO[val]))
        n_facet_vars += 1

# ── 포함 변수 개체 (개념 클래스 연결) ─────────────────────────────────────
VISIT_PAT = re.compile(
    r"\s*\((sleep heart health study )?visit (one|two)\s*\(shhs[12]\)\)|\s*\(shhs[12]\)", re.I)
def norm_label(s):
    s = VISIT_PAT.sub("", s if isinstance(s, str) else "")
    return re.sub(r"\s+", " ", s).strip()

n_linked = n_orphan = 0
for cohort in ("SHHS", "MESA"):
    for _, r in inv[cohort].iterrows():
        cu = concept_uri.get(norm_label(r["display_name"]).lower())
        if cu is None:
            n_orphan += 1
            continue
        v = OSACO[f"var_{cohort.lower()}_{r['id']}"]
        g.add((v, RDF.type, OWL.NamedIndividual))
        g.add((v, RDF.type, cu))
        g.add((v, RDFS.label, Literal(str(r["display_name"]))))
        g.add((v, OSACO.nsrrVariableId, Literal(str(r["id"]))))
        g.add((v, OSACO.sourceCohort, Literal(cohort)))
        n_linked += 1

# ── 저장 및 통계 ─────────────────────────────────────────────────────────
g.serialize(OUTD / "osaco.ttl", format="turtle")
g.serialize(OUTD / "osaco.owl", format="pretty-xml")
n_cls = len(set(g.subjects(RDF.type, OWL.Class)))
n_ind = len(set(g.subjects(RDF.type, OWL.NamedIndividual)))
print(f"트리플: {len(g):,}")
print(f"클래스: {n_cls} | 개체: {n_ind}")
print(f"패싯 변수 개체: {n_facet_vars} | 개념 연결 변수 개체: {n_linked} | 미연결: {n_orphan}")
print(f"skos:exactMatch {n_exact} | skos:relatedMatch {n_related}")
print("저장: osaco.ttl / osaco.owl")
