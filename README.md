# Evidence Gated Root Cause Diagnosis for Fintech Microservices Under Telemetry Loss

This repository contains the reproducibility package for the published research article:

**Evidence Gated Root Cause Diagnosis for Fintech Microservices Under Telemetry Loss**

**Authors:** Chidera Omoyemi Duru, Godson N Ozioma, Ijeoma C. Mordi  
**Journal:** Global Journal of Advanced Research and Reviews  
**Volume:** 4  
**Issue:** 4  
**Pages:** 048–062  
**Year:** 2026  

**Article:**  
https://gsjournals.com/gjarr/content/evidence-gated-root-cause-diagnosis-fintech-microservices-under-telemetry-loss

**DOI:**  
https://doi.org/10.58175/gjarr.2026.4.4.0091

## About this repository

This repository provides the code, synthetic datasets, generated figures, integrity checks and supporting material used to reproduce the study.

No production traces, financial customer data, human participants, or measured incident-response times are included.
## Reproduction

Run `python run_study.py` in this directory. It writes the incident-level data, telemetry, summary, signature tests and figures. The recorded environment used Python 3.12.14 and NumPy 2.3.5. See requirements.txt for the packages used. `python build_manuscript.py` recreates the Word file if the two source attachments are placed under the relative `../upload/` paths referred to by the script. Manuscript text is in manuscript_content.py.

## Design

The six call edges are API→Auth, API→Account, Account→Ledger, Ledger→Payment, Ledger→Audit and Ledger→Database. Failure symptoms propagate through reverse reachability. There are 600 independent incident seeds, each observed under four nested masks. The 2,400 rows must not be treated as independent. Family names denote amplitude multipliers rather than executable fault injections. All priors are uniform. Likelihood parameters are known from the synthetic generator and are not fitted to operational data. The fixed threshold derives from an illustrative 10:1 wrong-acceptance to deferral loss. There was no preregistration or held-out model training.

Noise has a service-independent component plus a shared component within each feature block. The missingness stress masks remove entire service records independently of fault state. The mismatch study weakens the root amplitude by multiplying its realised value by 0.6 and adds independent onset noise with standard deviation 1.2. Neither the inference model nor threshold is retuned.

## Outputs

- data/incidents.csv: 2,400 incident/missingness observations, 600 independent clusters.
- data/telemetry.csv: 16,800 node-level rows with generated values and observed flags. Unobserved values are retained solely for reproduction and are not passed to inference.
- data/model_mismatch.csv: 600 deliberately misspecified observations at 30% missingness.
- data/integrity_checks.csv: 1,400 checks, including 1,000 integrity violations, 200 clean controls, and 200 signed false claims.
- data/summary.json: exact aggregate values and cluster-bootstrap intervals.
- data/example_bundle.json: one signed manifest, telemetry objects, signature and public test key.
- data/supplied_code_check.json: reproduction of the defective supplied ranking rule.
- data/supplied_reference_audit.csv: all 89 supplied references with original text, scope and status.
- data/reference_inventory.json: 110 unique bibliographic records; 23 active citations and 87 author-review entries.
- figures/: three graphs calculated from the simulation.

## Integrity profile

Ed25519 signs the domain prefix and serialized manifest. The manifest contains SHA-256 digests of exact evidence bytes. The signature is detached. JSON is a restricted ASCII encoding with integral metadata and decimal-string measurements, sorted keys and compact separators. This is not a claim of general RFC 8785 conformance. Verification checks the signature, evidence object set, each digest, and incident/node binding. It does not check causal truth. The public deterministic private-key fixture is intentionally included in the code only to make reproduction possible; it must never be used for real security. Five mutations are evaluated independently; this is not an exhaustive adversarial security assessment. Initial integrity fixtures are the first 200 full-observation incidents, all from the first family; cryptographic mutation checks do not depend on failure-family accuracy.

## Evidence limits

The source brief's claimed 50-trial outcomes and response-time gains were not used as data. No conclusion about actual engineer speed, cognitive load, regulatory compliance, or production performance follows. The perfect matched-model accepted accuracy is an observed simulation result with favourable assumptions. Under mismatch, accepted accuracy is 92.7%. All supplied bibliography entries are retained, but only two supplied entries are used as checked conceptual context. Other supplied records require verification and relevance review before journal submission.
