"""Generate a release-specific inventory of bundled Python distributions."""

from __future__ import annotations

import argparse
import importlib.metadata as metadata
import re
import shutil
import sys
import sysconfig
from collections import deque
from pathlib import Path
from typing import Optional

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
BASE_NOTICE = REPOSITORY_ROOT / "THIRD_PARTY_NOTICES.txt"
RUNTIME_ROOTS = (
    "anthropic",
    "fastapi",
    "openai",
    "pydantic",
    "pyinstaller",
    "uvicorn[standard]",
)
LICENSE_NAMES = re.compile(r"(^|/)(license|licence|copying|notice)([._-].*)?$", re.I)
STRONG_COPYLEFT = re.compile(r"\b(?:A?GPL)(?:[- ]?v?[123](?:\.0)?)?\b", re.I)
REVIEWED_EXCEPTIONS = {"pyinstaller"}
NO_TRANSITIVE_SCAN = {"pyinstaller"}


def _active_requirement(requirement: Requirement, extras: set[str]) -> bool:
    if requirement.marker is None:
        return True
    candidates = extras or {""}
    return any(requirement.marker.evaluate({"extra": extra}) for extra in candidates)


def dependency_closure(
    roots: tuple[str, ...] = RUNTIME_ROOTS,
) -> list[metadata.Distribution]:
    """Resolve the installed dependency closure used by the Windows bundle."""
    queue: deque[tuple[str, set[str]]] = deque()
    for value in roots:
        parsed = Requirement(value)
        queue.append((parsed.name, set(parsed.extras)))

    found: dict[str, metadata.Distribution] = {}
    requested_extras: dict[str, set[str]] = {}
    while queue:
        name, extras = queue.popleft()
        normalized = canonicalize_name(name)
        previous = requested_extras.setdefault(normalized, set())
        new_extras = extras.difference(previous)
        if normalized in found and not new_extras:
            continue
        previous.update(extras)
        distribution = metadata.distribution(name)
        found[normalized] = distribution
        if normalized in NO_TRANSITIVE_SCAN:
            continue
        for value in distribution.requires or ():
            requirement = Requirement(value)
            if _active_requirement(requirement, previous):
                queue.append((requirement.name, set(requirement.extras)))

    return [found[name] for name in sorted(found)]


def _license_value(distribution: metadata.Distribution) -> str:
    expression = distribution.metadata.get("License-Expression")
    declared = distribution.metadata.get("License")
    classifiers = [
        value.removeprefix("License :: ")
        for value in distribution.metadata.get_all("Classifier", [])
        if value.startswith("License :: ")
    ]
    return expression or declared or "; ".join(classifiers) or "NOT DECLARED"


def _project_url(distribution: metadata.Distribution) -> str:
    for value in distribution.metadata.get_all("Project-URL", []):
        if "," in value:
            label, url = value.split(",", 1)
            if label.strip().lower() in {"homepage", "repository", "source"}:
                return url.strip()
    return distribution.metadata.get("Home-page") or "not declared"


def copy_license_files(
    distribution: metadata.Distribution, destination: Path
) -> list[str]:
    """Copy license and notice files exposed by installed package metadata."""
    copied = []
    package_dir = destination / (
        f"{canonicalize_name(distribution.metadata['Name'])}-{distribution.version}"
    )
    for entry in distribution.files or ():
        relative = str(entry).replace("\\", "/")
        if not LICENSE_NAMES.search(relative):
            continue
        source = Path(distribution.locate_file(entry))
        if not source.is_file():
            continue
        package_dir.mkdir(parents=True, exist_ok=True)
        target = package_dir / Path(relative).name
        suffix = 2
        while target.exists():
            target = (
                package_dir / f"{Path(relative).stem}-{suffix}{Path(relative).suffix}"
            )
            suffix += 1
        shutil.copyfile(source, target)
        copied.append(str(target.relative_to(destination.parent)).replace("\\", "/"))
    return copied


def copy_python_license(destination: Path) -> Optional[str]:
    """Copy the CPython license shipped with the interpreter, when available."""
    candidates = (
        Path(sys.base_prefix) / "LICENSE.txt",
        Path(sys.base_prefix) / "LICENSE",
        Path(sysconfig.get_path("stdlib")) / "LICENSE.txt",
    )
    for source in candidates:
        if not source.is_file():
            continue
        target_dir = (
            destination / f"cpython-{sys.version_info.major}.{sys.version_info.minor}"
        )
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / "LICENSE.txt"
        shutil.copyfile(source, target)
        return str(target.relative_to(destination.parent)).replace("\\", "/")
    return None


def build_inventory(
    distributions: list[metadata.Distribution], licenses_dir: Path
) -> str:
    """Return the auditable inventory and copy available license texts."""
    shutil.rmtree(licenses_dir, ignore_errors=True)
    licenses_dir.mkdir(parents=True, exist_ok=True)
    python_license = copy_python_license(licenses_dir)
    lines = [
        "",
        "RELEASE-SPECIFIC WINDOWS BUNDLE INVENTORY",
        "",
        f"Python runtime: CPython {sys.version.split()[0]} (Python Software Foundation License)",
        "License reference: https://docs.python.org/3/license.html",
        "Included license file: "
        + (python_license or "none found in build interpreter"),
        "",
    ]
    blocked = []
    for distribution in distributions:
        name = distribution.metadata["Name"]
        normalized = canonicalize_name(name)
        license_value = _license_value(distribution).replace("\n", " ").strip()
        copied = copy_license_files(distribution, licenses_dir)
        lines.extend(
            [
                f"{name} {distribution.version}",
                f"  Declared license: {license_value}",
                f"  Project: {_project_url(distribution)}",
                "  Included license files: "
                + (", ".join(copied) if copied else "none found"),
                "",
            ]
        )
        if (
            STRONG_COPYLEFT.search(license_value)
            and normalized not in REVIEWED_EXCEPTIONS
        ):
            blocked.append(f"{name}: {license_value}")
    if blocked:
        raise RuntimeError(
            "Unreviewed strong-copyleft dependency: " + "; ".join(blocked)
        )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--licenses-dir", type=Path, required=True)
    args = parser.parse_args()
    inventory = build_inventory(dependency_closure(), args.licenses_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        BASE_NOTICE.read_text(encoding="utf-8").rstrip() + "\n" + inventory,
        encoding="utf-8",
        newline="\n",
    )


if __name__ == "__main__":
    main()
