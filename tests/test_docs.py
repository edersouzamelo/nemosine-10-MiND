from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_public_documentation_is_versioned_and_scoped():
    validation = (ROOT / "docs/VALIDATION.md").read_text(encoding="utf-8")
    architecture = (ROOT / "docs/ARCHITECTURE.md").read_text(encoding="utf-8")
    citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")

    assert "MiND 1.0.5 validation record" in validation
    assert "version: 1.0.5" in citation
    assert "not present in 1.0.5" in architecture
    assert "Credentials must never appear" in architecture


def test_paper_does_not_claim_unimplemented_semantic_routing():
    paper = (ROOT / "paper.md").read_text(encoding="utf-8")

    forbidden = (
        "predefined execution modules",
        "reproduce exact model outputs",
        "infers the user's intent",
    )
    for claim in forbidden:
        assert claim not in paper


def test_preview_tags_cannot_publish_to_pypi():
    workflow = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")

    assert workflow.count("!contains(github.ref_name, '-')") == 2
