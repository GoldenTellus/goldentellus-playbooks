import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validate_content_links", PROJECT_ROOT / "scripts" / "validate_content_links.py"
)
assert SPEC and SPEC.loader
validate_content_links = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validate_content_links
SPEC.loader.exec_module(validate_content_links)


def write_document(root: Path, relative_path: str, frontmatter: str, body: str = "# Content\n") -> Path:
    target = root / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(f"---\n{frontmatter}---\n\n{body}", encoding="utf-8")
    return target


class ContentLinkValidationTests(unittest.TestCase):
    def create_linked_content(self, root: Path) -> tuple[Path, Path]:
        cases = root / "cases"
        knowledge = root / "knowledge"
        write_document(
            cases,
            "by-industry/retail/case-001.md",
            """id: CASE-001
status: published
authorization: confirmed
anonymization: complete
related_knowledge: [K-ANALYST-001]
""",
        )
        write_document(
            knowledge,
            "02-analyst/article.md",
            """id: K-ANALYST-001
content_type: case-learning
source_kind: case
related_cases: [CASE-001]
""",
        )
        return cases, knowledge

    def test_accepts_unique_ids_and_symmetric_relationships(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            cases, knowledge = self.create_linked_content(Path(temporary_directory))

            self.assertEqual(validate_content_links.validate_repositories(cases, knowledge), [])

    def test_rejects_case_learning_from_unpublished_or_incomplete_case(self) -> None:
        invalid_values = (
            ("status", "draft", "status: published"),
            ("authorization", "pending", "authorization: confirmed"),
            ("anonymization", "pending", "anonymization: complete"),
        )
        for field, invalid_value, expected_message in invalid_values:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temporary_directory:
                cases, knowledge = self.create_linked_content(Path(temporary_directory))
                case = cases / "by-industry" / "retail" / "case-001.md"
                case_text = case.read_text(encoding="utf-8")
                case.write_text(
                    case_text.replace(
                        f"{field}: {'published' if field == 'status' else 'confirmed' if field == 'authorization' else 'complete'}",
                        f"{field}: {invalid_value}",
                    ),
                    encoding="utf-8",
                )

                errors = validate_content_links.validate_repositories(cases, knowledge)

                self.assertTrue(any(expected_message in error for error in errors), errors)

    def test_rejects_missing_reverse_relationship(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            cases, knowledge = self.create_linked_content(Path(temporary_directory))
            article = knowledge / "02-analyst" / "article.md"
            article.write_text("---\nid: K-ANALYST-001\nrelated_cases: []\n---\n", encoding="utf-8")

            errors = validate_content_links.validate_repositories(cases, knowledge)

            self.assertTrue(any("reverse relationship" in error for error in errors))

    def test_rejects_duplicate_ids(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            cases, knowledge = self.create_linked_content(Path(temporary_directory))
            write_document(
                cases,
                "by-industry/retail/case-duplicate.md",
                "id: CASE-001\nrelated_knowledge: []\n",
            )

            errors = validate_content_links.validate_repositories(cases, knowledge)

            self.assertTrue(any("duplicate ID CASE-001" in error for error in errors))

    def test_rejects_missing_local_markdown_link(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            cases, knowledge = self.create_linked_content(Path(temporary_directory))
            case = cases / "by-industry" / "retail" / "case-001.md"
            case.write_text(
                case.read_text(encoding="utf-8") + "\n[Missing guide](missing-guide.md)\n",
                encoding="utf-8",
            )

            errors = validate_content_links.validate_repositories(cases, knowledge)

            self.assertTrue(any("missing local link target" in error for error in errors))

    def test_accepts_a_local_markdown_link_with_a_title(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            cases, knowledge = self.create_linked_content(Path(temporary_directory))
            case = cases / "by-industry" / "retail" / "case-001.md"
            guide = case.parent / "guide.md"
            guide.write_text("# Guide\n", encoding="utf-8")
            case.write_text(
                case.read_text(encoding="utf-8") + '\n[Guide](guide.md "Read the guide")\n',
                encoding="utf-8",
            )

            self.assertEqual(validate_content_links.validate_repositories(cases, knowledge), [])

    def test_rejects_a_local_link_that_escapes_its_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            cases, knowledge = self.create_linked_content(Path(temporary_directory))
            case = cases / "by-industry" / "retail" / "case-001.md"
            case.write_text(
                case.read_text(encoding="utf-8") + "\n[Outside](../../../outside.md)\n",
                encoding="utf-8",
            )

            errors = validate_content_links.validate_repositories(cases, knowledge)

            self.assertTrue(any("escapes the repository" in error for error in errors))

    def test_rejects_a_missing_cases_checkout(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            missing_cases = root / "missing-cases"
            _, knowledge = self.create_linked_content(root)

            errors = validate_content_links.validate_repositories(missing_cases, knowledge)

            self.assertTrue(any("cases repository path does not exist" in error for error in errors))

    def test_rejects_a_missing_knowledge_checkout(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            cases, _ = self.create_linked_content(root)
            missing_knowledge = root / "missing-knowledge"

            errors = validate_content_links.validate_repositories(cases, missing_knowledge)

            self.assertTrue(any("knowledge repository path does not exist" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
