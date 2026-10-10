"""
Streamlit Web UI for Offline AI Code Reviewer Agent.
"""

import os
import sys
import pandas as pd
import streamlit as st

# Ensure core package is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.diff_parser import DiffParser
from core.git_reader import GitReader
from core.instruction_manager import InstructionManager
from core.llm_gateway import LLMGateway
from core.repo_scanner import RepoScanner
from core.reviewer_agent import ReviewerAgent
from core.skill_manager import SkillManager

# Page setup
st.set_page_config(
    page_title="AI Code Reviewer Agent",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for clean UI styling
st.markdown(
    """
<style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 12px;
        border-left: 5px solid #1E88E5;
        margin-bottom: 10px;
    }
    .badge-critical { color: #d32f2f; font-weight: bold; }
    .badge-warning { color: #f57c00; font-weight: bold; }
    .badge-suggestion { color: #388e3c; font-weight: bold; }
    .stCodeBlock { font-family: 'JetBrains Mono', 'Fira Code', monospace; }
</style>
""",
    unsafe_allow_html=True,
)


def init_session_state():
    if "review_results" not in st.session_state:
        st.session_state.review_results = None
    if "raw_output" not in st.session_state:
        st.session_state.raw_output = ""
    if "metadata" not in st.session_state:
        st.session_state.metadata = {}
    if "diff_content" not in st.session_state:
        st.session_state.diff_content = ""
    if "dest_branch" not in st.session_state:
        st.session_state.dest_branch = "main"
    if "src_branch" not in st.session_state:
        st.session_state.src_branch = ""


init_session_state()
instruction_manager = InstructionManager()
skill_manager = SkillManager()

# ----------------- SIDEBAR -----------------
st.sidebar.title("🔍 Reviewer Agent Setup")

# 1. Local Repository Configuration
st.sidebar.subheader("1. Local Repository & Branches")
repo_path_input = st.sidebar.text_input(
    "Local Repo Path",
    value=os.getcwd(),
    help="Absolute path to locally cloned repository. No online PR access is needed.",
)

git_reader = GitReader(repo_path_input)
is_valid_repo, repo_msg = git_reader.validate_repo()

available_branches = []
if is_valid_repo:
    available_branches = git_reader.list_branches()
    current_branch = git_reader.get_current_branch()
    st.sidebar.success(f"✅ Git Repo OK (Checked out: `{current_branch}`)")
else:
    st.sidebar.warning(f"⚠️ {repo_msg}")

# Destination & Source Branch Dropdowns
if available_branches:
    dest_idx = 0
    # Try finding main or master
    for idx, b in enumerate(available_branches):
        if b in ["main", "master", "origin/main", "origin/master"]:
            dest_idx = idx
            break

    dest_branch = st.sidebar.selectbox(
        "Destination / Base Branch (e.g. main)",
        options=available_branches,
        index=dest_idx,
        help="Target branch being merged into (baseline for AST & context reading)",
    )
    st.session_state.dest_branch = dest_branch

    # Feature branch default
    src_idx = 1 if len(available_branches) > 1 else 0
    src_branch = st.sidebar.selectbox(
        "Source / Feature Branch",
        options=available_branches,
        index=src_idx,
        help="Feature branch containing new changes",
    )
    st.session_state.src_branch = src_branch
else:
    dest_branch = st.sidebar.text_input("Destination Branch", value="main")
    src_branch = st.sidebar.text_input("Source Branch", value="")
    st.session_state.dest_branch = dest_branch
    st.session_state.src_branch = src_branch

git_reader.main_branch = dest_branch

# 2. LLM Gateway Configuration
st.sidebar.subheader("2. LLM Gateway & Model")
preset_choice = st.sidebar.selectbox(
    "Gateway Provider / Preset",
    list(LLMGateway.DEFAULT_PRESETS.keys()),
    index=0,
)
preset_info = LLMGateway.DEFAULT_PRESETS[preset_choice]

default_model = preset_info["model"]
default_base = preset_info["api_base"]

model_name = st.sidebar.text_input("Model Name", value=default_model)
api_base = st.sidebar.text_input("Gateway Base URL", value=default_base)
api_key = st.sidebar.text_input(
    "API Key / GitHub Token",
    value=os.getenv("LLM_API_KEY") or os.getenv("OPENROUTER_API_KEY") or os.getenv("GITHUB_TOKEN") or "",
    type="password",
    help="API key for OpenRouter, or GitHub PAT for GitHub Models/Copilot proxy",
)

if st.sidebar.button("Test Gateway Connection"):
    gw_test = LLMGateway(model=model_name, api_key=api_key or None, api_base=api_base or None)
    with st.sidebar:
        with st.spinner("Pinging LLM Gateway..."):
            ok, test_msg = gw_test.test_connection()
            if ok:
                st.success(test_msg)
            else:
                st.error(test_msg)

# 3. Skills Management
st.sidebar.subheader("3. Modular Review Skills")
available_skills = skill_manager.get_skill_names()

auto_detect_skills = st.sidebar.checkbox(
    "Auto-Detect Skills from Diff",
    value=True,
    help="Automatically detects Spring Boot (*.java), React (*.tsx, *.jsx), etc.",
)

selected_skills = st.sidebar.multiselect(
    "Active Skills",
    options=available_skills,
    default=available_skills,
    help="Select which specialized skill rulebooks to inject into the review prompt.",
)

# ----------------- MAIN CONTENT -----------------
st.title("🤖 Offline AI Code Reviewer Agent")
st.markdown(
    """
Performs automated, context-aware pull request code reviews by analyzing your local repository
at the destination branch and evaluating changes from your feature branch, GitHub PR, or Azure DevOps PR export.
"""
)

# Main Navigation Tabs: Diff Ingestion & Custom Instructions
main_nav_tab1, main_nav_tab2 = st.tabs(["🚀 PR Review Engine", "✍️ Custom Instructions Manager"])

with main_nav_tab1:
    # Tabs for Diff Input
    tab_branches, tab_upload, tab_paste, tab_sample = st.tabs(
        [
            "🔀 Local Branch Diff",
            "📁 Upload Diff File",
            "📝 Paste Diff Text",
            "🧪 Load Sample PR",
        ]
    )

    with tab_branches:
        st.markdown(
            f"Generate diff directly from local git repository: `{st.session_state.dest_branch}` $\leftarrow$ `{st.session_state.src_branch}`"
        )
        if st.button("⚡ Generate Diff from Selected Branches", type="secondary"):
            if not is_valid_repo:
                st.error("Please configure a valid local repository in the sidebar.")
            elif st.session_state.dest_branch == st.session_state.src_branch:
                st.warning("Destination and source branches are the same. Please select different branches.")
            else:
                with st.spinner("Running local git diff..."):
                    ok, diff_out = git_reader.get_diff_between_branches(
                        st.session_state.dest_branch, st.session_state.src_branch
                    )
                    if ok:
                        st.session_state.diff_content = diff_out
                        st.success(f"Generated diff between `{st.session_state.dest_branch}` and `{st.session_state.src_branch}` ({len(diff_out)} bytes)")
                    else:
                        st.error(diff_out)

    with tab_upload:
        uploaded_file = st.file_uploader(
            "Upload PR unified diff or patch file exported from GitHub/Azure DevOps (`.diff`, `.patch`)",
            type=["diff", "patch", "txt"],
        )
        if uploaded_file is not None:
            st.session_state.diff_content = uploaded_file.getvalue().decode("utf-8", errors="replace")
            st.success(f"Loaded `{uploaded_file.name}` ({len(st.session_state.diff_content)} bytes)")

    with tab_paste:
        pasted_diff = st.text_area(
            "Paste exported diff here (e.g. from `gh pr diff` or `git diff main...feat`)",
            value=st.session_state.diff_content,
            height=200,
        )
        if pasted_diff:
            st.session_state.diff_content = pasted_diff

    with tab_sample:
        sample_col1, sample_col2 = st.columns(2)
        with sample_col1:
            if st.button("Load Spring Boot Sample PR (Java/JPA)"):
                sample_path = os.path.join(
                    os.path.dirname(__file__), "test_samples", "sample_spring_boot.diff"
                )
                if os.path.exists(sample_path):
                    with open(sample_path, "r", encoding="utf-8") as f:
                        st.session_state.diff_content = f.read()
                    st.success("Loaded Spring Boot sample diff!")
        with sample_col2:
            if st.button("Load React.js Sample PR (TSX/Hooks)"):
                sample_path = os.path.join(
                    os.path.dirname(__file__), "test_samples", "sample_react.diff"
                )
                if os.path.exists(sample_path):
                    with open(sample_path, "r", encoding="utf-8") as f:
                        st.session_state.diff_content = f.read()
                    st.success("Loaded React sample diff!")

    # Review Trigger Button
    st.markdown("---")
    col_btn, col_info = st.columns([1, 3])

    with col_btn:
        start_review = st.button("🚀 Run Code Review", type="primary", use_container_width=True)

    with col_info:
        if st.session_state.diff_content:
            preview_files = DiffParser.parse(st.session_state.diff_content)
            file_list_str = ", ".join([f"`{f.display_name}`" for f in preview_files])
            st.caption(f"Detected **{len(preview_files)}** modified files: {file_list_str}")

    # Execution Logic
    if start_review:
        if not st.session_state.diff_content.strip():
            st.error("Please provide a diff by selecting branches, uploading a file, or loading a sample.")
        else:
            with st.status("Executing Code Review...", expanded=True) as status:
                # 1. Parse Diff
                status.write("1️⃣ Parsing PR diff and mapping line numbers...")
                diff_files = DiffParser.parse(st.session_state.diff_content)
                changed_paths = [df.display_name for df in diff_files if not df.is_deleted]
                status.write(f"✓ Found {len(diff_files)} changed files with {sum(len(df.hunks) for df in diff_files)} hunks.")

                # 2. Context Extraction from destination branch
                status.write(f"2️⃣ Scanning local repository (`{dest_branch}`) for AST & symbol dependencies...")
                repo_scanner = RepoScanner(git_reader)
                ctx_summary = repo_scanner.build_context_summary(changed_paths)
                status.write(f"✓ Architectural context built for {len(changed_paths)} target files.")

                # 3. Skills Resolution
                status.write("3️⃣ Resolving active review skills & custom instructions...")
                if auto_detect_skills:
                    active_skills = skill_manager.auto_detect_skills(
                        changed_paths, st.session_state.diff_content
                    )
                else:
                    active_skills = selected_skills
                status.write(f"✓ Active skills applied: {', '.join(active_skills) or 'None'}")

                # 4. LLM Gateway Invocation
                status.write(f"4️⃣ Invoking LLM Gateway ({model_name})...")
                llm_gateway = LLMGateway(
                    model=model_name,
                    api_key=api_key or None,
                    api_base=api_base or None,
                )

                reviewer_agent = ReviewerAgent(
                    git_reader=git_reader,
                    repo_scanner=repo_scanner,
                    skill_manager=skill_manager,
                    llm_gateway=llm_gateway,
                    instruction_manager=instruction_manager,
                )

                try:
                    comments, raw_str, metadata = reviewer_agent.run_review(
                        diff_text=st.session_state.diff_content,
                        selected_skills=active_skills,
                    )
                    st.session_state.review_results = comments
                    st.session_state.raw_output = raw_str
                    st.session_state.metadata = metadata
                    status.update(label="✅ Code Review Completed!", state="complete", expanded=False)
                except Exception as e:
                    status.update(label=f"❌ Error during review: {str(e)}", state="error")
                    st.error(f"Failed to generate review: {str(e)}")

# ----------------- CUSTOM INSTRUCTIONS TAB -----------------
with main_nav_tab2:
    st.subheader("✍️ Multi-Tiered Custom Instructions")
    st.markdown(
        """
Configure instructions at two levels:
1. **Global Parent Inherited Instructions**: Applied to all tasks and projects (output format, tone, severity levels).
2. **Task / Skill-Specific Custom Instructions**: Tailored rules for specific technologies (Spring Boot, React, etc.).
"""
    )

    inst_tab1, inst_tab2 = st.tabs(["🌐 Parent Inherited Instructions", "🎯 Task-Specific Instructions"])

    with inst_tab1:
        st.markdown("**Global Parent Inherited Instructions (Applies across all projects)**")
        current_parent_text = instruction_manager.get_parent_instructions()
        parent_edit = st.text_area(
            "Edit Parent Instructions",
            value=current_parent_text,
            height=300,
            key="parent_inst_editor",
        )
        if st.button("💾 Save Parent Instructions", type="primary"):
            if instruction_manager.save_parent_instructions(parent_edit):
                st.success("Successfully saved Parent Inherited Instructions!")
            else:
                st.error("Failed to save parent instructions.")

    with inst_tab2:
        st.markdown("**Technology / Task-Specific Instructions**")
        chosen_skill = st.selectbox(
            "Select Skill to Customize",
            options=available_skills,
            index=0,
        )
        current_skill_inst = instruction_manager.get_skill_custom_instructions(chosen_skill)
        skill_edit = st.text_area(
            f"Custom Instructions for `{chosen_skill}`",
            value=current_skill_inst,
            height=250,
            key=f"skill_inst_{chosen_skill}",
            help=f"Add team-specific rules for {chosen_skill} (e.g. specific frameworks, architectural standards)",
        )
        if st.button(f"💾 Save Instructions for {chosen_skill}"):
            if instruction_manager.save_skill_custom_instructions(chosen_skill, skill_edit):
                st.success(f"Saved custom instructions for `{chosen_skill}`!")
            else:
                st.error(f"Failed to save instructions for `{chosen_skill}`.")

# ----------------- RESULTS PRESENTATION -----------------
if st.session_state.review_results is not None:
    comments = st.session_state.review_results
    raw_str = st.session_state.raw_output
    meta = st.session_state.metadata

    st.markdown("---")
    st.markdown("## 📋 Code Review Results")

    # Metrics Row
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Review Comments", len(comments))
    m2.metric("Critical Issues 🚨", meta.get("critical_count", 0))
    m3.metric("Warnings ⚠️", meta.get("warning_count", 0))
    m4.metric("Suggestions 💡", meta.get("suggestion_count", 0))

    # Result Tabs
    res_tab1, res_tab2, res_tab3, res_tab4 = st.tabs(
        [
            "📑 Standard Output Format (class->line->comment)",
            "📊 Filterable Table View",
            "🔍 Diff & Line Inspector",
            "💾 Export & Download",
        ]
    )

    with res_tab1:
        st.markdown("**Required Standard Output Format:**")
        st.caption("Each line matches `class->line_number->Review comment`")
        st.code(raw_str, language="text")

    with res_tab2:
        if comments:
            data = [
                {
                    "Severity": c.severity,
                    "Class / Component": c.target_class,
                    "Line Number": c.line_number,
                    "Review Comment": c.comment,
                    "File Path": c.file_path,
                }
                for c in comments
            ]
            df = pd.DataFrame(data)

            # Severity filter
            sev_filter = st.multiselect(
                "Filter by Severity",
                options=["Critical", "Warning", "Suggestion"],
                default=["Critical", "Warning", "Suggestion"],
            )
            filtered_df = df[df["Severity"].isin(sev_filter)]
            st.dataframe(filtered_df, use_container_width=True, hide_index=True)
        else:
            st.info("No issues detected or formatted.")

    with res_tab3:
        st.markdown("**Annotated PR Diff (with exact line numbers):**")
        parsed_dfs = DiffParser.parse(st.session_state.diff_content)
        formatted_diff_text = DiffParser.format_diff_for_review(parsed_dfs)
        st.code(formatted_diff_text, language="text")

    with res_tab4:
        st.markdown("**Download Review Report:**")
        d_col1, d_col2 = st.columns(2)
        with d_col1:
            st.download_button(
                "📥 Download Standard Format (.txt)",
                data=raw_str,
                file_name="pr_review_comments.txt",
                mime="text/plain",
            )
        with d_col2:
            md_lines = ["# Automated PR Code Review Report\n"]
            md_lines.append(f"- **Files Reviewed:** {meta.get('files_reviewed', 0)}")
            md_lines.append(f"- **Active Skills:** {', '.join(meta.get('active_skills', []))}\n")
            md_lines.append("## Findings\n")
            md_lines.append("| Class | Line | Severity | Review Comment |")
            md_lines.append("|---|---|---|---|")
            for c in comments:
                md_lines.append(f"| `{c.target_class}` | `{c.line_number}` | {c.severity} | {c.comment} |")
            md_content = "\n".join(md_lines)

            st.download_button(
                "📥 Download Markdown Report (.md)",
                data=md_content,
                file_name="pr_review_report.md",
                mime="text/markdown",
            )
