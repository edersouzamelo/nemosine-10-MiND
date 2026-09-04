# JORS submission readiness

Status date: 2026-09-04

This checklist separates repository work that can be completed automatically
from author-controlled publication and journal actions.

## S8, final validation

- [x] Public claims reconciled with the executable architecture.
- [x] Determinism defined as middleware procedure, not identical LLM output.
- [x] Unsupported semantic routing claims removed.
- [x] CI covers Python 3.9 through 3.13, minimum dependencies, quality and clean
  wheel installation.
- [x] Windows workflow covers build, clean install, launch, upgrade and uninstall.
- [x] Secret protection and Windows credential storage tested.
- [x] Apache 2.0 legal pack and third-party notices included.
- [x] Validation and security records published in the repository.
- [ ] Merge the validated candidate into `main` after CI approval.
- [ ] Create the final stable tag after the merge.

## S9, software metapaper

- [x] Manuscript rebuilt from the current software rather than the previous
  concept description.
- [x] Abstract and statement of need revised.
- [x] Current architecture, Cycle Artifact, providers and storage documented.
- [x] Quality control and reusable integration paths documented.
- [x] Limitations and privacy boundary documented.
- [x] Availability metadata added.
- [x] References replaced with sources relevant to provenance, reporting,
  reproducibility and software citation.
- [x] Author contributions and competing interests added.
- [ ] Replace the long-term archive placeholder with the final version-specific
  Zenodo DOI.
- [ ] Author reviews wording, authorship metadata, affiliation and references.

## S10, editorial and submission package

- [x] Prior editorial criticisms mapped to repository evidence.
- [x] Cover-letter draft prepared.
- [x] Citation metadata prepared in `CITATION.cff`.
- [x] Apache 2.0 license, notice, trademark policy and dependency notices present.
- [x] Stable release workflow prevents preview tags from publishing to PyPI.
- [ ] Confirm that the stable version is visible on PyPI.
- [ ] Archive the exact stable release on Zenodo and record its DOI.
- [ ] Render and visually inspect the journal submission document.
- [ ] Confirm author email, affiliation and optional ORCID.
- [ ] Submit through the JORS portal with the author's explicit approval.

## Submission stop conditions

Do not submit while any of the following is true:

- the paper describes a feature absent from the tagged software;
- the DOI resolves to an older software revision;
- the stable package differs from the tested commit;
- author identity or declaration fields are unverified;
- the author has not reviewed the final manuscript and authorized submission.

JORS currently asks software metapapers to remain within approximately 3,000 to
4,000 words. The manuscript should be re-counted after inserting the final DOI
and any author revisions.
