"""Convert the repository GPL license into the RTF used by Windows Installer."""

from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SOURCE_LICENSE = REPOSITORY_ROOT / "LICENSE"
OUTPUT_LICENSE = REPOSITORY_ROOT / "build-msi" / "LICENSE.rtf"


def escape_rtf(text: str) -> str:
    """Escape plain ASCII license text for an RTF document."""
    return text.replace("\\", r"\\").replace("{", r"\{").replace("}", r"\}")


def main() -> None:
    """Write a deterministic RTF copy of the canonical repository license."""
    source = SOURCE_LICENSE.read_text(encoding="utf-8")
    if "GNU GENERAL PUBLIC LICENSE" not in source:
        raise RuntimeError("Repository LICENSE is not the expected GNU GPL text")
    if "Lorem ipsum" in source:
        raise RuntimeError("Placeholder text found in repository LICENSE")

    body = "\\par\n".join(escape_rtf(line) for line in source.splitlines())
    document = (
        r"{\rtf1\ansi\deff0{\fonttbl{\f0 Courier New;}}"
        "\n"
        r"\fs18 "
        f"{body}\n"
        "}"
    )
    OUTPUT_LICENSE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_LICENSE.write_text(document, encoding="ascii", newline="\n")


if __name__ == "__main__":
    main()
