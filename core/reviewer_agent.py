"""
Reviewer Agent Orchestrator Module
Coordinates diff parsing, local repo context retrieval, skill application,
LLM generation, and strict output formatting: class->line_number->Review comment.
"""

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .diff_parser import DiffFile, DiffParser
from .git_reader import GitReader
from .instruction_manager import InstructionManager
from .llm_gateway import LLMGateway
from .repo_scanner import RepoScanner
from .skill_manager import SkillManager


@dataclass
class ReviewComment:
    target_class: str
    line_number: int
    comment: str
    severity: str = "Warning"  # Critical, Warning, Suggestion
    file_path: str = ""

    def to_standard_format(self) -> str:
        """Required format: class->line_number->Review comment"""
        return f"{self.target_class}->{self.line_number}->{self.comment}"


class ReviewerAgent:
    """Agent orchestrating the end-to-end PR code review."""

    REVIEW_OUTPUT_REGEX = re.compile(r"^\s*([a-zA-Z0-9_\.\-]+)\s*->\s*(\d+)\s*->\s*(.+)$")

    def __init__(
        self,
        git_reader: GitReader,
        repo_scanner: RepoScanner,
        skill_manager: SkillManager,
        llm_gateway: LLMGateway,
        instruction_manager: Optional[InstructionManager] = None,
    ):
        self.git_reader = git_reader
        self.repo_scanner = repo_scanner
        self.skill_manager = skill_manager
        self.llm_gateway = llm_gateway
        self.instruction_manager = instruction_manager or InstructionManager()


    def run_review(
        self,
        diff_text: str,
        selected_skills: Optional[List[str]] = None,
    ) -> Tuple[List[ReviewComment], str, Dict[str, Any]]:
        """
        Executes code review on the provided diff.
        Returns:
            - List of parsed ReviewComment objects
            - Raw output string in class->line_number->Review comment format
            - Metadata dictionary (stats, changed files, active skills)
        """
        # 1. Parse diff
        diff_files = DiffParser.parse(diff_text)
        if not diff_files:
            return [], "No valid diff changes detected.", {"error": "Empty or invalid diff"}

        changed_paths = [df.display_name for df in diff_files if not df.is_deleted]

        # 2. Determine active skills
        if selected_skills is None:
            active_skills = self.skill_manager.auto_detect_skills(changed_paths, diff_text)
        else:
            active_skills = selected_skills

        # 3. Retrieve context from branch_main
        context_summary = self.repo_scanner.build_context_summary(changed_paths)

        # 4. Format annotated diff
        formatted_diff = DiffParser.format_diff_for_review(diff_files)

        # 5. Build prompt
        skill_section = self.skill_manager.build_skill_prompt_section(active_skills)
        system_prompt, user_prompt = self._build_prompts(
            formatted_diff, context_summary, skill_section, diff_files, active_skills
        )

        # 6. Call LLM Gateway
        raw_response = self.llm_gateway.generate_review(system_prompt, user_prompt)

        # 7. Parse & Validate Review Comments
        comments = self._parse_and_validate_comments(raw_response, diff_files)

        # 8. Re-format strictly into class->line_number->Review comment
        standard_formatted = "\n".join([c.to_standard_format() for c in comments])
        if not standard_formatted:
            standard_formatted = raw_response.strip()

        metadata = {
            "files_reviewed": len(diff_files),
            "changed_paths": changed_paths,
            "active_skills": active_skills,
            "total_comments": len(comments),
            "critical_count": sum(1 for c in comments if c.severity == "Critical"),
            "warning_count": sum(1 for c in comments if c.severity == "Warning"),
            "suggestion_count": sum(1 for c in comments if c.severity == "Suggestion"),
        }

        return comments, standard_formatted, metadata

    def _build_prompts(
        self,
        formatted_diff: str,
        context_summary: str,
        skill_section: str,
        diff_files: List[DiffFile],
        active_skills: Optional[List[str]] = None,
    ) -> Tuple[str, str]:
        """Constructs system and user prompts with strict formatting constraints."""

        # 1. Base Layer & Custom Instructions from InstructionManager
        layered_instructions = self.instruction_manager.build_layered_prompt(active_skills or [])

        system_prompt = f"""You are a Principal Software Engineer and Staff Code Reviewer.
Your task is to review a Pull Request diff against the local `branch_main` repository state.

{layered_instructions}

## SPECIALIZED SKILL GUIDELINES & RULEBOOKS:
{skill_section}
"""

        user_prompt = f"""Please review the following PR changes against the baseline context from `branch_main`.

## BASELINE ARCHITECTURAL CONTEXT (FROM branch_main):
{context_summary}

## ANNOTATED DIFF (WITH EXACT NEW LINE NUMBERS):
{formatted_diff}

Remember: Output ONLY in the exact format:
class->line_number->Review comment
"""
        return system_prompt, user_prompt

    def _parse_and_validate_comments(
        self, raw_output: str, diff_files: List[DiffFile]
    ) -> List[ReviewComment]:
        """
        Parses LLM output into structured ReviewComment objects,
        matching the class->line_number->Review comment format.
        """
        comments: List[ReviewComment] = []
        file_map = {df.class_or_symbol_name: df for df in diff_files}
        filename_map = {df.display_name.split("/")[-1]: df for df in diff_files}

        for line in raw_output.splitlines():
            line_str = line.strip()
            if not line_str:
                continue

            match = self.REVIEW_OUTPUT_REGEX.match(line_str)
            if match:
                target_class = match.group(1).strip()
                line_no = int(match.group(2).strip())
                comment_text = match.group(3).strip()

                # Infer severity
                severity = "Warning"
                lower_comment = comment_text.lower()
                if "[critical]" in lower_comment or "critical:" in lower_comment or "security vulnerability" in lower_comment or "sql injection" in lower_comment:
                    severity = "Critical"
                elif "[suggestion]" in lower_comment or "suggestion:" in lower_comment or "nit:" in lower_comment:
                    severity = "Suggestion"

                # Find associated file
                df = file_map.get(target_class) or filename_map.get(target_class)
                file_path = df.display_name if df else target_class

                comments.append(
                    ReviewComment(
                        target_class=target_class,
                        line_number=line_no,
                        comment=comment_text,
                        severity=severity,
                        file_path=file_path,
                    )
                )

        return comments
