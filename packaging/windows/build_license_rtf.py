"""Build the Apache-2.0 legal notice shown by Windows Installer."""

from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SOURCE_LICENSE = REPOSITORY_ROOT / "LICENSE"
SOURCE_NOTICE = REPOSITORY_ROOT / "INSTALLER_LEGAL.txt"
OUTPUT_LICENSE = REPOSITORY_ROOT / "build-msi" / "LICENSE.rtf"


def escape_rtf(text: str) -> str:
    """Escape text as RTF, including characters outside ASCII."""
    escaped = []
    for char in text:
        if char == "\\":
            escaped.append(r"\\")
        elif char == "{":
            escaped.append(r"\{")
        elif char == "}":
            escaped.append(r"\}")
        elif ord(char) > 127:
            codepoint = ord(char)
            if codepoint > 32767:
                codepoint -= 65536
            escaped.append(rf"\u{codepoint}?")
        else:
            escaped.append(char)
    return "".join(escaped)


def main() -> None:
    """Write a deterministic RTF with the notice and canonical license."""
    license_text = SOURCE_LICENSE.read_text(encoding="utf-8")
    notice_text = SOURCE_NOTICE.read_text(encoding="utf-8")
    if (
        "Apache License" not in license_text
        or "Version 2.0, January 2004" not in license_text
    ):
        raise RuntimeError("Repository LICENSE is not the expected Apache-2.0 text")
    source = notice_text + "\n\nCOMPLETE APACHE LICENSE, VERSION 2.0\n\n" + license_text
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
    # Path.write_text only gained the newline parameter in Python 3.10.
    # Keep the installer generator compatible with MiND's Python 3.9 floor.
    with OUTPUT_LICENSE.open("w", encoding="ascii", newline="\n") as output_file:
        output_file.write(document)


if __name__ == "__main__":
    main()
