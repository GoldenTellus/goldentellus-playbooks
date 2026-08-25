"""Audit IDs, cross-repository relationships, and local Markdown links."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import unquote, urlparse

import yaml


LINK_PATTERN = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")


@dataclass(frozen=True)
class ContentRecord:
    identifier: str
    metadata: dict[str, Any]
    path: Path


def markdown_link_destination(raw_destination: str) -> str:
    """Extract a Markdown link target while ignoring an optional title."""
    destination = raw_destination.strip()
    if destination.startswith("<"):
        closing_index = destination.find(">")
        return destination[1:closing_index].strip() if closing_index >= 0 else destination
    return destination.split(maxsplit=1)[0] if destination else ""


def parse_frontmatter(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        return None, None
    try:
        closing_index = lines.index("---", 1)
    except ValueError:
        return None, "frontmatter is missing its closing marker"
    try:
        metadata = yaml.safe_load("\n".join(lines[1:closing_index]))
    except yaml.YAMLError as error:
        return None, f"frontmatter is not valid YAML: {error}"
    if not isinstance(metadata, dict):
        return None, "frontmatter must be a YAML mapping"
    return metadata, None


def content_files(root: Path, kind: str) -> list[Path]:
    if kind == "cases":
        source = root / "by-industry"
        return sorted(source.rglob("*.md")) if source.exists() else []
    return sorted(path for path in root.rglob("*.md") if path.name != "README.md")


def all_markdown_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.md") if ".git" not in path.parts)


def read_records(root: Path, kind: str) -> tuple[list[ContentRecord], list[str]]:
    records: list[ContentRecord] = []
    errors: list[str] = []
    for path in content_files(root, kind):
        metadata, parsing_error = parse_frontmatter(path)
        if parsing_error:
            errors.append(f"{path}: {parsing_error}")
            continue
        if metadata is None:
            continue
        identifier = metadata.get("id")
        if not isinstance(identifier, str) or not identifier.strip():
            errors.append(f"{path}: frontmatter record is missing a string id")
            continue
        if "XXX" in identifier:
            continue
        records.append(ContentRecord(identifier, metadata, path))
    return records, errors


def index_records(records: Iterable[ContentRecord]) -> tuple[dict[str, ContentRecord], list[str]]:
    index: dict[str, ContentRecord] = {}
    errors: list[str] = []
    for record in records:
        if record.identifier in index:
            errors.append(f"{record.path}: duplicate ID {record.identifier}; first defined in {index[record.identifier].path}")
            continue
        index[record.identifier] = record
    return index, errors


def related_ids(record: ContentRecord, field: str) -> tuple[list[str], list[str]]:
    value = record.metadata.get(field, [])
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        return [], [f"{record.path}: '{field}' must be a list of IDs"]
    return value, []


def validate_relationships(cases: dict[str, ContentRecord], knowledge: dict[str, ContentRecord]) -> list[str]:
    errors: list[str] = []
    for case in cases.values():
        knowledge_ids, relationship_errors = related_ids(case, "related_knowledge")
        errors.extend(relationship_errors)
        for knowledge_id in knowledge_ids:
            article = knowledge.get(knowledge_id)
            if article is None:
                errors.append(f"{case.path}: related knowledge ID {knowledge_id} was not found")
                continue
            reverse_ids, reverse_errors = related_ids(article, "related_cases")
            errors.extend(reverse_errors)
            if case.identifier not in reverse_ids:
                errors.append(f"{case.path}: reverse relationship missing: {knowledge_id} must reference {case.identifier}")
    for article in knowledge.values():
        case_ids, relationship_errors = related_ids(article, "related_cases")
        errors.extend(relationship_errors)
        for case_id in case_ids:
            case = cases.get(case_id)
            if case is None:
                errors.append(f"{article.path}: related case ID {case_id} was not found")
                continue
            if article.metadata.get("content_type") == "case-learning":
                required_case_state = (
                    ("status", "published"),
                    ("authorization", "confirmed"),
                    ("anonymization", "complete"),
                )
                for field, expected in required_case_state:
                    actual = case.metadata.get(field)
                    if actual != expected:
                        errors.append(
                            f"{article.path}: case-learning articles require related case {case_id} "
                            f"to have {field}: {expected}; found {field}: {actual!r}"
                        )
            reverse_ids, reverse_errors = related_ids(case, "related_knowledge")
            errors.extend(reverse_errors)
            if article.identifier not in reverse_ids:
                errors.append(f"{article.path}: reverse relationship missing: {case_id} must reference {article.identifier}")
    return errors


def validate_links(roots: Iterable[Path]) -> list[str]:
    errors: list[str] = []
    for root in roots:
        resolved_root = root.resolve()
        for path in all_markdown_files(root):
            content = path.read_text(encoding="utf-8")
            for raw_destination in LINK_PATTERN.findall(content):
                destination = markdown_link_destination(raw_destination)
                if not destination or destination.startswith(("#", "mailto:")):
                    continue
                parsed = urlparse(destination)
                if parsed.scheme:
                    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                        errors.append(f"{path}: invalid external URL '{destination}'")
                    continue
                if destination.startswith(("/", "\\")):
                    errors.append(f"{path}: local links must be relative: '{destination}'")
                    continue
                local_path = unquote(destination.split("#", 1)[0].split("?", 1)[0])
                if not local_path:
                    continue
                target = (path.parent / local_path).resolve()
                try:
                    target.relative_to(resolved_root)
                except ValueError:
                    errors.append(f"{path}: local link escapes the repository: '{destination}'")
                    continue
                if not target.exists():
                    errors.append(f"{path}: missing local link target '{destination}'")
    return errors


def validate_repository_roots(cases_root: Path, knowledge_root: Path) -> list[str]:
    """Reject incomplete checkouts before an audit can silently skip their content."""
    errors: list[str] = []
    for name, root in (("cases", cases_root), ("knowledge", knowledge_root)):
        if not root.exists():
            errors.append(f"{name} repository path does not exist: {root}")
        elif not root.is_dir():
            errors.append(f"{name} repository path is not a directory: {root}")

    if cases_root.is_dir() and not (cases_root / "by-industry").is_dir():
        errors.append(f"cases repository is missing required directory: {cases_root / 'by-industry'}")
    return errors


def validate_repositories(cases_root: Path, knowledge_root: Path) -> list[str]:
    root_errors = validate_repository_roots(cases_root, knowledge_root)
    if root_errors:
        return root_errors
    case_records, case_errors = read_records(cases_root, "cases")
    knowledge_records, knowledge_errors = read_records(knowledge_root, "knowledge")
    cases, case_index_errors = index_records(case_records)
    knowledge, knowledge_index_errors = index_records(knowledge_records)
    return [
        *case_errors,
        *knowledge_errors,
        *case_index_errors,
        *knowledge_index_errors,
        *validate_relationships(cases, knowledge),
        *validate_links((cases_root, knowledge_root)),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit GoldenTellus cases and knowledge relationships.")
    parser.add_argument("--cases", type=Path, required=True, help="Path to the goldentellus-cases checkout")
    parser.add_argument("--knowledge", type=Path, required=True, help="Path to the goldentellus-knowledge checkout")
    arguments = parser.parse_args()
    errors = validate_repositories(arguments.cases, arguments.knowledge)
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        return 1
    print("Cross-repository content audit passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
