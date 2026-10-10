"""
Instruction Manager Module
Manages hierarchical, multi-tiered prompt instructions:
1. Parent Inherited Instructions (Global rules, output syntax, response tone)
2. Task / Skill-Specific Custom Instructions (Spring Boot, React, etc.)
Allows editing, saving, and persisting custom instructions via UI.
"""

import os
from typing import Dict, List, Optional


class InstructionManager:
    """Manages global parent instructions and task/skill specific instructions."""

    def __init__(self, base_dir: Optional[str] = None):
        if base_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.base_dir = base_dir
        self.instructions_dir = os.path.join(base_dir, "instructions")
        self.skills_dir = os.path.join(base_dir, "skills")
        os.makedirs(self.instructions_dir, exist_ok=True)

        self.parent_file = os.path.join(self.instructions_dir, "parent_instructions.md")

    def get_parent_instructions(self) -> str:
        """Read the global parent inherited instructions."""
        if os.path.exists(self.parent_file):
            try:
                with open(self.parent_file, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception:
                pass
        return self._default_parent_instructions()

    def save_parent_instructions(self, content: str) -> bool:
        """Save updated parent instructions to disk."""
        try:
            with open(self.parent_file, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception:
            return False

    def get_skill_custom_instructions(self, skill_name: str) -> str:
        """Read task-specific custom instructions for a given skill."""
        custom_file = os.path.join(self.skills_dir, skill_name, "custom_instructions.md")
        if os.path.exists(custom_file):
            try:
                with open(custom_file, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception:
                pass
        return ""

    def save_skill_custom_instructions(self, skill_name: str, content: str) -> bool:
        """Save updated custom instructions for a skill to disk."""
        target_dir = os.path.join(self.skills_dir, skill_name)
        os.makedirs(target_dir, exist_ok=True)
        custom_file = os.path.join(target_dir, "custom_instructions.md")
        try:
            with open(custom_file, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception:
            return False

    def build_layered_prompt(self, active_skills: List[str]) -> str:
        """
        Builds the complete layered instruction section:
        Layer 1: Parent Inherited Instructions (Global)
        Layer 2: Task-Specific Custom Instructions (Per active skill)
        """
        parts = []

        # Layer 1: Parent Inherited
        parent = self.get_parent_instructions().strip()
        if parent:
            parts.append("## GLOBAL INHERITED INSTRUCTIONS:\n" + parent)

        # Layer 2: Task-Specific Custom Instructions
        custom_sections = []
        for s in active_skills:
            custom_inst = self.get_skill_custom_instructions(s).strip()
            if custom_inst:
                custom_sections.append(f"### Custom Instructions for [{s.upper()}]:\n{custom_inst}")

        if custom_sections:
            parts.append("## TASK-SPECIFIC CUSTOM INSTRUCTIONS:\n" + "\n\n".join(custom_sections))

        return "\n\n" + ("\n" + "=" * 50 + "\n").join(parts) + "\n\n"

    def _default_parent_instructions(self) -> str:
        return """# PARENT INHERITED INSTRUCTIONS
## MANDATORY OUTPUT SYNTAX:
class->line_number->Review comment

## RULES:
- Output only valid comments matching the syntax above.
- Only comment on modified or added lines.
- Be actionable, concise, and constructive.
"""
