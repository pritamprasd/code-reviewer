"""
Core components for Offline AI Code Reviewer Agent.
"""

from .git_reader import GitReader
from .diff_parser import DiffParser, DiffFile, DiffHunk, DiffLine
from .repo_scanner import RepoScanner, FileContext, CodeSymbol
from .instruction_manager import InstructionManager
from .skill_manager import SkillManager, Skill
from .llm_gateway import LLMGateway
from .reviewer_agent import ReviewerAgent, ReviewComment
from .folder_picker import pick_folder_native, list_directory_entries

__all__ = [
    "GitReader",
    "DiffParser",
    "DiffFile",
    "DiffHunk",
    "DiffLine",
    "RepoScanner",
    "FileContext",
    "CodeSymbol",
    "InstructionManager",
    "SkillManager",
    "Skill",
    "LLMGateway",
    "ReviewerAgent",
    "ReviewComment",
    "pick_folder_native",
    "list_directory_entries",
]
