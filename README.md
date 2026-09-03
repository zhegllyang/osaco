# OSACO — Obstructive Sleep Apnea Cohort Variable Ontology

OSACO is an application ontology of obstructive sleep apnea (OSA)-related variables,
constructed from the Sleep Heart Health Study (SHHS v0.14.0) data dictionary and
cross-validated against MESA (v0.8.0), both distributed by the
[National Sleep Research Resource](https://sleepdata.org).

- **605 classes** (11 upper classes, 32 faceted PSG measurement families, ~550 concept classes)
- **1,584 cohort-variable individuals** with facet properties (sleep stage, body position,
  desaturation threshold, arousal criterion)
- **550 cross-references** to SNOMED CT, HPO, MONDO, and EFO
  (`skos:exactMatch` 165 / `skos:relatedMatch` 385)
- Base IRI: `https://w3id.org/osaco/`

No participant-level data are contained in this repository; all content is derived from
the publicly available NSRR data dictionaries.

## Contents

| Path | Description |
|---|---|
| `ontology/osaco.ttl` / `osaco.owl` | The ontology (Turtle / RDF-XML) |
| `mappings/OSA_mapping_final.xlsx` | Final concept-to-terminology mappings with per-decision rationale |
| `mappings/adjudication_stage1.csv` | Deterministic-rule adjudication log (328 concepts) |
| `mappings/adjudication_stage2.csv` | LLM adjudication log (233 concepts) |
| `mappings/manual_curation.csv` | Curated query chains for concepts unresolved by lexical search |
| `design/` | Variable triage inventory, facet decomposition, measurement-family design tables |
| `validation/` | Competency-question outputs and participant-level validation summary tables |
| `scripts/` | Reproducible pipeline: inventory notebook, OWL builder, SPARQL competency questions, empirical validation |

## Reproducing

```bash
pip install pandas openpyxl rdflib
python scripts/build_owl.py                    # rebuilds ontology from design/mapping tables
python scripts/run_competency_questions.py     # runs the 7 SPARQL competency questions
```

`scripts/run_empirical_validation.py` requires SHHS/MESA participant-level data obtained
from NSRR under a data use agreement.

## Citation

If you use OSACO, please cite: *[manuscript under review — citation to be added]*.

## License

- Ontology and mapping tables: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
- Code (`scripts/`): MIT License (see `LICENSE`)
