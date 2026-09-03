import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "mind_build_license_rtf", ROOT / "packaging/windows/build_license_rtf.py"
)
assert SPEC and SPEC.loader
license_rtf = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(license_rtf)


def test_repository_uses_complete_apache_license():
    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    metadata = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert "Apache License" in license_text
    assert "Version 2.0, January 2004" in license_text
    assert "END OF TERMS AND CONDITIONS" in license_text
    assert 'license = "Apache-2.0"' in metadata
    assert "GNU GENERAL PUBLIC LICENSE" not in license_text


def test_required_legal_pack_has_no_placeholder():
    required = {
        "LICENSE",
        "NOTICE",
        "TRADEMARKS.md",
        "INSTALLER_LEGAL.txt",
        "THIRD_PARTY_NOTICES.txt",
        "SOURCE_HEADER.txt",
    }
    for name in required:
        contents = (ROOT / name).read_text(encoding="utf-8")
        assert contents.strip(), name
        assert "Lorem ipsum" not in contents, name


def test_installer_legal_rtf_contains_notice_and_license(tmp_path, monkeypatch):
    output = tmp_path / "LICENSE.rtf"
    monkeypatch.setattr(license_rtf, "OUTPUT_LICENSE", output)

    license_rtf.main()

    contents = output.read_text(encoding="ascii")
    assert "LICENSE AND LEGAL NOTICE" in contents
    assert "Apache License" in contents
    assert "Version 2.0, January 2004" in contents
    assert "GNU GENERAL PUBLIC LICENSE" not in contents
    assert "Lorem ipsum" not in contents
