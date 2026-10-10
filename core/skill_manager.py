"""
Skill Manager Module
Discovers, auto-detects, and manages modular review skills (Spring Boot, React, Security, Clean Code).
Injects specialized rules and checklists into reviewer prompts.
"""

import os
from dataclasses import dataclass, field
from fnmatch import fnmatch
from typing import Dict, List, Optional
import yaml


@dataclass
class Skill:
    name: str
    description: str
    version: str
    file_patterns: List[str]
    keywords: List[str]
    rules_markdown: str
    skill_dir: str


class SkillManager:
    """Manages discoverable, pluggable reviewer skills."""

    def __init__(self, skills_root_dir: Optional[str] = None):
        if skills_root_dir is None:
            # Default to ../skills relative to core/
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            skills_root_dir = os.path.join(base_dir, "skills")
        self.skills_root_dir = skills_root_dir
        self.skills: Dict[str, Skill] = {}
        self.load_all_skills()

    def load_all_skills(self):
        """Scans the skills directory and loads all valid skill definitions."""
        self.skills.clear()
        if not os.path.exists(self.skills_root_dir):
            return

        for entry in os.listdir(self.skills_root_dir):
            skill_path = os.path.join(self.skills_root_dir, entry)
            if not os.path.isdir(skill_path):
                continue

            config_file = os.path.join(skill_path, "config.yaml")
            rules_file = os.path.join(skill_path, "rules.md")

            if os.path.exists(config_file) and os.path.exists(rules_file):
                try:
                    with open(config_file, "r", encoding="utf-8") as f:
                        cfg = yaml.safe_load(f) or {}

                    with open(rules_file, "r", encoding="utf-8") as f:
                        rules_md = f.read()

                    skill = Skill(
                        name=cfg.get("name", entry),
                        description=cfg.get("description", ""),
                        version=cfg.get("version", "1.0.0"),
                        file_patterns=cfg.get("file_patterns", ["*"]),
                        keywords=cfg.get("keywords", []),
                        rules_markdown=rules_md,
                        skill_dir=skill_path,
                    )
                    self.skills[skill.name] = skill
                except Exception as e:
                    print(f"Error loading skill {entry}: {e}")

    def get_skill_names(self) -> List[str]:
        return list(self.skills.keys())

    def auto_detect_skills(self, changed_files: List[str], diff_content: str = "") -> List[str]:
        """
        Automatically detect which skills apply based on changed file extensions
        and content keywords.
        """
        matched = set()

        # Always include clean-code if available
        if "clean-code-reviewer" in self.skills:
            matched.add("clean-code-reviewer")

        for skill_name, skill in self.skills.items():
            # Check file patterns
            for file_path in changed_files:
                for pattern in skill.file_patterns:
                    if fnmatch(file_path.lower(), pattern.lower()) or fnmatch(os.path.basename(file_path).lower(), pattern.lower()):
                        matched.add(skill_name)
                        break

            # Check keywords in diff text
            if diff_content:
                for kw in skill.keywords:
                    if kw in diff_content:
                        matched.add(skill_name)
                        break

        return sorted(list(matched))

    def build_skill_prompt_section(self, selected_skill_names: List[str]) -> str:
        """
        Combines rules from selected skills into a unified guidelines section for the prompt.
        """
        if not selected_skill_names:
            return ""

        sections = []
        for name in selected_skill_names:
            skill = self.skills.get(name)
            if skill:
                sections.append(f"### ACTIVE SKILL: [{skill.name.upper()}]\n{skill.rules_markdown.strip()}")

        return "\n\n" + ("\n" + "=" * 50 + "\n").join(sections)
