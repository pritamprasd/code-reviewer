# Offline AI Code Reviewer Agent

A privacy-first, context-aware AI code review assistant with a lightweight **Streamlit UI**, powered by **LiteLLM Gateway**, **Tree-sitter / AST Code Graphs**, **modular review skills** (Spring Boot, React.js, Security, Clean Code), and **hierarchical custom instructions**.

---

## 🌟 Key Features

1. **GUI Folder Selection & Interactive Tree Browser**:
   - One-click native OS folder selection dialog (GNOME / Ubuntu file chooser via `zenity` or `tkinter`).
   - Built-in interactive in-app directory tree navigator with automatic Git repository badge detection.
2. **Local Branch Selection & Instant Diff Generation**:
   - Point to any locally cloned repository.
   - Select **Destination / Base Branch** (e.g., `main`) and **Source / Feature Branch** (e.g., `feat/login`) directly from dynamic dropdowns.
   - Click **⚡ Generate Diff from Selected Branches** to create the diff instantly via `git diff dest...src`, or upload/paste an exported `.diff`/`.patch` file.
3. **100% Offline & Private Local Context**:
   - Zero access to cloud GitHub or Azure DevOps PR APIs required.
   - Reads `branch_main` strictly from your local repository clone using non-destructive Git object reading (`git show <main_branch>:<file>`), so you never have to switch branches.
4. **Context-Aware Code Graph & Graphify Methodology**:
   - Maps class hierarchies, method signatures, imports, and **blast radius** (downstream callers in `main`) using deterministic AST parsing and optional Graphify (`graphify-out/graph.json`) integration.
5. **Multi-Tiered Custom Instructions**:
   - **Global Parent Inherited Instructions**: Valid across all projects and agents (mandates `class->line_number->Review comment` format, response tone, and severity standards).
   - **Task / Skill-Specific Instructions**: Tailored rules per technology (e.g. MapStruct in Spring Boot, TanStack Query in React, OWASP checklist in Security).
   - Fully editable and savable directly inside the Streamlit UI!
6. **Strict Standard Output Format**:
   - Enforces the exact requested review comment format:
     ```text
     class->line_number->Review comment
     ```
7. **Universal Open-Source LLM Gateway**:
   - Powered by **LiteLLM**, supporting:
     - **OpenRouter** (Claude 3.5 Sonnet, GPT-4o, DeepSeek, Llama 3.3)
     - **GitHub Copilot** (via LiteLLM Copilot Proxy or Copilot tokens)
     - **GitHub Models** (using GitHub PAT at `https://models.inference.ai.azure.com`)
     - **Local Ollama** (e.g. `qwen2.5-coder:14b`, `deepseek-coder-v2`)
     - Any custom OpenAI-compatible proxy.
8. **Ubuntu Deployment & Multi-OS CI/CD Pipeline**:
   - Ubuntu systemd service unit and desktop application shortcut included.
   - Automated GitHub Actions release pipeline building multi-OS artifacts (Linux, Windows, macOS) on every push to `main`.

---

## 📁 Repository Structure

```
code-reviewer/
├── app.py                      # Main Streamlit Web UI application
├── run_app.py                  # Standalone launcher / desktop entrypoint
├── requirements.txt            # Python dependencies
├── core/
│   ├── __init__.py
│   ├── git_reader.py           # Offline Git reader & branch diff generator
│   ├── diff_parser.py          # Unified diff parser & line number mapper
│   ├── repo_scanner.py         # AST symbol extractor & blast radius scanner
│   ├── skill_manager.py        # Modular skill loader & auto-detector
│   ├── instruction_manager.py  # Parent inherited & task-specific instructions
│   ├── llm_gateway.py          # LiteLLM universal gateway client
│   └── reviewer_agent.py       # Review orchestrator enforcing class->line->comment
├── instructions/
│   └── parent_instructions.md  # Global inherited instructions
├── skills/                     # Modular skill rulebooks
│   ├── spring-boot-reviewer/   # JPA, @Transactional, DI, REST validation
│   │   ├── config.yaml
│   │   ├── rules.md
│   │   └── custom_instructions.md
│   ├── react-js-reviewer/      # Hooks, exhaustive-deps, immutability, memoization
│   │   ├── config.yaml
│   │   ├── rules.md
│   │   └── custom_instructions.md
│   ├── clean-code-reviewer/    # SOLID, naming, error handling, performance
│   │   ├── config.yaml
│   │   ├── rules.md
│   │   └── custom_instructions.md
│   └── security-reviewer/      # OWASP, SQLi, command injection, secret leakage
│       ├── config.yaml
│       ├── rules.md
│       └── custom_instructions.md
├── deployment/                 # Ubuntu deployment assets
│   ├── install_ubuntu.sh       # One-click Ubuntu installer
│   ├── code-reviewer.desktop   # Ubuntu desktop application launcher
│   └── code-reviewer.service   # Ubuntu systemd daemon unit
├── .github/workflows/
│   └── release.yml             # GitHub Actions multi-OS release pipeline
├── test_samples/               # Ready-to-use sample diffs
│   ├── sample_spring_boot.diff
│   └── sample_react.diff
└── tests/
    └── test_reviewer.py        # Automated test suite
```

---

## 🚀 Quick Start Guide

### 1. Installation

```bash
# Navigate to the project directory
cd /home/pritam_t/code/agents/code-reviewer

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Launch the Streamlit UI

```bash
source venv/bin/activate
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 🖥️ Deploying as an Ubuntu App

There are three ways to deploy and run the app on Ubuntu:

### Option 1: Standalone Desktop App (Recommended for Ubuntu Desktop)
Run the provided automated installer script:
```bash
./deployment/install_ubuntu.sh
```
This script will:
1. Verify `python3` and `git`.
2. Set up the Python virtual environment and install all packages.
3. Register `code-reviewer.desktop` in `~/.local/share/applications`.

You can now search for **AI Code Reviewer** in your Ubuntu Activities / Applications dashboard and click to launch!

To launch from the terminal:
```bash
source venv/bin/activate && python3 run_app.py
```
This automatically starts Streamlit in headless mode and opens your default browser at `http://localhost:8501`.

---

### Option 2: Always-On Ubuntu Daemon (`systemd` Service)
If you want the application running as a permanent background service on an Ubuntu workstation or server:

1. Copy the service unit to systemd:
   ```bash
   sudo cp deployment/code-reviewer.service /etc/systemd/system/
   ```
2. Enable and start the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable --now code-reviewer.service
   ```
3. Check service status:
   ```bash
   sudo systemctl status code-reviewer.service
   ```
The app will automatically run on boot and restart if it stops.

---

## 🔀 Using Branch Dropdowns & Diff Ingestion

### A. Direct Local Branch Comparison
1. In the sidebar, specify your **Local Repo Path** (e.g. `/home/user/code/my-repo`).
2. Select your **Destination / Base Branch** (e.g., `main`) and **Source / Feature Branch** (e.g., `feat/my-feature`) from the dropdowns.
3. In the main tab **🔀 Local Branch Diff**, click **⚡ Generate Diff from Selected Branches**.
4. The agent will run `git diff destination...source` locally and display the diff ready for review.

### B. Uploading an Exported PR Diff (GitHub / Azure DevOps)
If the feature branch only exists on GitHub or Azure DevOps:
1. Export the PR diff to a local file:
   - **GitHub**:
     ```bash
     gh pr diff <PR_NUMBER> > pr.diff
     ```
   - **Azure DevOps**:
     ```bash
     az repos pr diff --id <PR_ID> > pr.diff
     ```
2. In the **📁 Upload Diff File** tab, drag and drop `pr.diff`.

---

## ✍️ Customizing Instructions (Parent & Task-Specific)

Navigate to the **✍️ Custom Instructions Manager** tab in the UI:

### 1. Global Parent Inherited Instructions
- Controls global behaviors:
  - Strict output syntax: `class->line_number->Review comment`
  - Response philosophy (objective, no filler, actionable)
  - Severity taxonomy (`[Critical]`, `[Warning]`, `[Suggestion]`)
- Edits made in the UI are saved to `instructions/parent_instructions.md`.

### 2. Task / Skill-Specific Instructions
- Select a skill from the dropdown (e.g., `spring-boot-reviewer`, `react-js-reviewer`, `security-reviewer`).
- Enter project/team-specific conventions:
  - *Spring Boot*: "Use Java 21 records for DTOs; recommend MapStruct; never hold DB transactions during REST calls."
  - *React.js*: "Use TanStack Query for data fetching; use Zustand for global state; forbid explicit `any`."
- Click **Save Instructions** to persist changes directly to `skills/<skill>/custom_instructions.md`.

---

## ⚙️ Configuring LLM Gateways

### 1. OpenRouter
1. Select **OpenRouter** in the sidebar preset.
2. Enter your `OPENROUTER_API_KEY`.
3. Model: `openrouter/anthropic/claude-3.5-sonnet` (or `openrouter/openai/gpt-4o`, `openrouter/deepseek/deepseek-chat`).

### 2. GitHub Copilot & GitHub Models
- **Via GitHub Models (Marketplace)**:
  - Preset: `GitHub Models (Marketplace)`
  - Base URL: `https://models.inference.ai.azure.com`
  - Model: `github/gpt-4o`
  - API Key: Your GitHub Personal Access Token (`ghp_...`).
- **Via LiteLLM Copilot Proxy**:
  - Run LiteLLM Proxy locally: `litellm --model github_copilot/gpt-4o --port 4000`
  - Preset: `GitHub Copilot (via Proxy / LiteLLM)`
  - Base URL: `http://localhost:4000/v1`

### 3. Local Ollama
1. Start Ollama locally: `ollama run qwen2.5-coder:14b`
2. Select **Local Ollama** preset.
3. Base URL: `http://localhost:11434`
4. Model: `ollama/qwen2.5-coder:14b`

---

## 📦 GitHub Pipeline & Multi-OS Releases

The repository includes a complete GitHub Actions CI/CD pipeline at [`.github/workflows/release.yml`](file:///.github/workflows/release.yml):

- **Trigger**: Every `push` to the `main` or `master` branch.
- **Matrix Build**:
  - **Linux (Ubuntu)**: Compiles and bundles `code-reviewer-linux-x86_64.tar.gz` with PyInstaller.
  - **Windows**: Packages `code-reviewer-windows-x86_64.zip`.
  - **macOS**: Packages `code-reviewer-macos.tar.gz`.
- **Release Automation**:
  - Automatically tags the release as `v1.0.<RUN_NUMBER>`.
  - Creates a GitHub Release.
  - Attaches the pre-built distribution archives for download.

---

## 🧪 Running Automated Tests

Run the test suite with:

```bash
source venv/bin/activate
python -m unittest discover tests/
```
Output:
```
.....
----------------------------------------------------------------------
Ran 5 tests in 0.004s

OK
```
