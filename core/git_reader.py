"""
Git Reader Module
Reads repository files and metadata directly from a local git repository.
Operates 100% offline using `git show <main-branch>:<path>` without altering working directory state.
"""

import os
import subprocess
from typing import Dict, List, Optional, Set, Tuple


class GitReader:
    def __init__(self, repo_path: str, main_branch: str = "main"):
        self.repo_path = os.path.abspath(repo_path)
        self.main_branch = main_branch

    def validate_repo(self) -> Tuple[bool, str]:
        """Validate if the path exists and is a valid git repository."""
        if not os.path.exists(self.repo_path):
            return False, f"Directory does not exist: {self.repo_path}"
        if not os.path.isdir(self.repo_path):
            return False, f"Path is not a directory: {self.repo_path}"

        git_dir = os.path.join(self.repo_path, ".git")
        if not os.path.exists(git_dir):
            return False, f"Directory is not a git repository (missing .git): {self.repo_path}"

        # Test running git rev-parse
        try:
            res = subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=False,
            )
            if res.returncode != 0:
                return False, f"Not a valid git working tree: {res.stderr.strip()}"
        except Exception as e:
            return False, f"Failed to execute git command: {str(e)}"

        return True, "Valid git repository"

    def get_current_branch(self) -> Optional[str]:
        """Get currently checked-out branch name."""
        try:
            res = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=False,
            )
            if res.returncode == 0:
                return res.stdout.strip()
        except Exception:
            pass
        return None

    def list_branches(self) -> List[str]:
        """List local and remote branches in the repository, prioritized with main/master on top."""
        branches: Set[str] = set()
        current = self.get_current_branch()
        if current:
            branches.add(current)

        try:
            res = subprocess.run(
                ["git", "branch", "-a", "--format=%(refname:short)"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=False,
            )
            if res.returncode == 0:
                for line in res.stdout.splitlines():
                    b = line.strip()
                    if b and not b.startswith("origin/HEAD"):
                        branches.add(b)
        except Exception:
            pass

        # Sort with common defaults on top
        priority = ["main", "master", "origin/main", "origin/master"]
        sorted_branches = []
        for p in priority:
            if p in branches:
                sorted_branches.append(p)
                branches.remove(p)

        # Remaining sorted alphabetically
        sorted_branches.extend(sorted(list(branches)))
        return sorted_branches

    def get_diff_between_branches(self, base_branch: str, feature_branch: str) -> Tuple[bool, str]:
        """
        Generate git diff between base_branch (destination) and feature_branch (source)
        using three-dot notation: `git diff base...feature`
        """
        if not base_branch or not feature_branch:
            return False, "Both destination and source branches must be specified."

        try:
            res = subprocess.run(
                ["git", "diff", f"{base_branch}...{feature_branch}"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=False,
            )
            if res.returncode != 0:
                return False, f"Git diff command failed: {res.stderr.strip()}"

            diff_text = res.stdout
            if not diff_text.strip():
                return False, f"No differences found between `{base_branch}` and `{feature_branch}`."

            return True, diff_text
        except Exception as e:
            return False, f"Error running git diff: {str(e)}"


    def verify_branch_exists(self, branch_name: str) -> bool:
        """Check if branch or commit ref exists locally."""
        try:
            res = subprocess.run(
                ["git", "rev-parse", "--verify", branch_name],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=False,
            )
            return res.returncode == 0
        except Exception:
            return False

    def read_file_at_branch(self, relative_path: str, branch: Optional[str] = None) -> Optional[str]:
        """
        Read file contents at specified branch without checking it out,
        using `git show <branch>:<relative_path>`.
        """
        target_branch = branch or self.main_branch
        # Normalize relative path (forward slashes)
        clean_path = relative_path.replace("\\", "/").lstrip("/")

        try:
            res = subprocess.run(
                ["git", "show", f"{target_branch}:{clean_path}"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=False,
            )
            if res.returncode == 0:
                return res.stdout
            else:
                # File might not exist in main (e.g. newly created file)
                return None
        except Exception:
            return None

    def read_local_working_file(self, relative_path: str) -> Optional[str]:
        """Read file directly from the current working directory if available."""
        full_path = os.path.join(self.repo_path, relative_path)
        if os.path.exists(full_path) and os.path.isfile(full_path):
            try:
                with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                    return f.read()
            except Exception:
                return None
        return None
