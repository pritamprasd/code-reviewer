"""
Diff Parser Module
Parses unified diff files exported from GitHub, Azure DevOps, or Git CLI.
Accurately maps hunks and added/modified lines to precise line numbers in the new file.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class DiffLine:
    line_type: str  # 'add' (+), 'del' (-), 'context' (' ')
    content: str
    old_line_no: Optional[int] = None
    new_line_no: Optional[int] = None


@dataclass
class DiffHunk:
    old_start: int
    old_lines: int
    new_start: int
    new_lines: int
    heading: str = ""
    lines: List[DiffLine] = field(default_factory=list)


@dataclass
class DiffFile:
    old_path: str
    new_path: str
    is_new: bool = False
    is_deleted: bool = False
    is_rename: bool = False
    hunks: List[DiffHunk] = field(default_factory=list)

    @property
    def display_name(self) -> str:
        if self.new_path and self.new_path != "/dev/null":
            return self.new_path
        return self.old_path

    @property
    def class_or_symbol_name(self) -> str:
        """
        Derive class or primary symbol name from file path:
        e.g., 'src/main/java/com/example/UserService.java' -> 'UserService'
              'src/components/UserProfile.tsx' -> 'UserProfile'
        """
        filename = self.display_name.split("/")[-1]
        base_name = filename.rsplit(".", 1)[0]
        return base_name

    def get_added_or_modified_line_numbers(self) -> List[int]:
        """Returns list of line numbers in the new file that were added or modified."""
        line_nos = []
        for hunk in self.hunks:
            for line in hunk.lines:
                if line.line_type == "add" and line.new_line_no is not None:
                    line_nos.append(line.new_line_no)
        return line_nos


class DiffParser:
    """Parses unified diff format strings into structured objects."""

    HUNK_HEADER_REGEX = re.compile(
        r"^@@\s+-(\d+)(?:,(\d+))?\s+\+(\d+)(?:,(\d+))?\s+@@\s*(.*)$"
    )

    @classmethod
    def parse(cls, diff_text: str) -> List[DiffFile]:
        files: List[DiffFile] = []
        if not diff_text or not diff_text.strip():
            return files

        lines = diff_text.splitlines()
        current_file: Optional[DiffFile] = None
        current_hunk: Optional[DiffHunk] = None
        old_line_counter = 0
        new_line_counter = 0

        i = 0
        while i < len(lines):
            line = lines[i]

            # Detect git diff header: diff --git a/path b/path
            if line.startswith("diff --git "):
                if current_file:
                    if current_hunk:
                        current_file.hunks.append(current_hunk)
                        current_hunk = None
                    files.append(current_file)

                # Extract paths
                parts = line.split(" ")
                old_p = parts[2][2:] if len(parts) > 2 and parts[2].startswith("a/") else ""
                new_p = parts[3][2:] if len(parts) > 3 and parts[3].startswith("b/") else ""
                current_file = DiffFile(old_path=old_p, new_path=new_p)
                i += 1
                continue

            # Detect file status flags
            if current_file:
                if line.startswith("new file mode"):
                    current_file.is_new = True
                elif line.startswith("deleted file mode"):
                    current_file.is_deleted = True
                elif line.startswith("rename from"):
                    current_file.is_rename = True
                elif line.startswith("--- "):
                    p = line[4:].strip()
                    if p.startswith("a/"):
                        p = p[2:]
                    elif p == "/dev/null":
                        current_file.is_new = True
                    current_file.old_path = p
                elif line.startswith("+++ "):
                    p = line[4:].strip()
                    if p.startswith("b/"):
                        p = p[2:]
                    elif p == "/dev/null":
                        current_file.is_deleted = True
                    current_file.new_path = p

            # Detect hunk header: @@ -old,count +new,count @@ heading
            hunk_match = cls.HUNK_HEADER_REGEX.match(line)
            if hunk_match:
                if current_file is None:
                    # Non-git standard unified diff without 'diff --git' header
                    current_file = DiffFile(old_path="unknown", new_path="unknown")

                if current_hunk:
                    current_file.hunks.append(current_hunk)

                old_start = int(hunk_match.group(1))
                old_count = int(hunk_match.group(2)) if hunk_match.group(2) else 1
                new_start = int(hunk_match.group(3))
                new_count = int(hunk_match.group(4)) if hunk_match.group(4) else 1
                heading = hunk_match.group(5) or ""

                current_hunk = DiffHunk(
                    old_start=old_start,
                    old_lines=old_count,
                    new_start=new_start,
                    new_lines=new_count,
                    heading=heading.strip(),
                )
                old_line_counter = old_start
                new_line_counter = new_start
                i += 1
                continue

            # In-hunk lines
            if current_hunk is not None:
                if line.startswith("+") and not line.startswith("+++"):
                    current_hunk.lines.append(
                        DiffLine(
                            line_type="add",
                            content=line[1:],
                            new_line_no=new_line_counter,
                        )
                    )
                    new_line_counter += 1
                elif line.startswith("-") and not line.startswith("---"):
                    current_hunk.lines.append(
                        DiffLine(
                            line_type="del",
                            content=line[1:],
                            old_line_no=old_line_counter,
                        )
                    )
                    old_line_counter += 1
                elif line.startswith(" "):
                    current_hunk.lines.append(
                        DiffLine(
                            line_type="context",
                            content=line[1:],
                            old_line_no=old_line_counter,
                            new_line_no=new_line_counter,
                        )
                    )
                    old_line_counter += 1
                    new_line_counter += 1
                elif line.startswith("\\ No newline at end of file"):
                    pass
                else:
                    # End of hunk or unexpected line
                    pass

            i += 1

        if current_file:
            if current_hunk:
                current_file.hunks.append(current_hunk)
            files.append(current_file)

        return files

    @classmethod
    def format_diff_for_review(cls, diff_files: List[DiffFile]) -> str:
        """
        Formats parsed diff files into an annotated representation
        showing explicit new line numbers for every added or modified line.
        """
        output = []
        for df in diff_files:
            output.append(f"### FILE: {df.display_name} (Class/Component: {df.class_or_symbol_name})")
            if df.is_new:
                output.append("Status: [NEW FILE]")
            elif df.is_deleted:
                output.append("Status: [DELETED FILE]")

            for idx, hunk in enumerate(df.hunks, 1):
                output.append(f"\n--- Hunk {idx}: Lines {hunk.new_start}-{hunk.new_start + hunk.new_lines} {hunk.heading} ---")
                for line in hunk.lines:
                    if line.line_type == "add":
                        output.append(f"Line {line.new_line_no:4d} [+] {line.content}")
                    elif line.line_type == "del":
                        output.append(f"     OLD [-] {line.content}")
                    else:
                        output.append(f"Line {line.new_line_no:4d} [ ] {line.content}")
            output.append("\n" + "=" * 50 + "\n")

        return "\n".join(output)
