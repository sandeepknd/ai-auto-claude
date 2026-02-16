import os
import tempfile
import subprocess
import git
import subprocess
from claude_cli_client import call_llm

import httpx
from urllib.parse import urlparse
import requests

def truncate_text(text, max_lines=500):
    """Truncate text to max_lines, keeping both start and end."""
    if not text:
        return text

    lines = text.split('\n')
    if len(lines) <= max_lines:
        return text

    # Keep first 60% and last 40% of allowed lines
    keep_start = int(max_lines * 0.6)
    keep_end = max_lines - keep_start

    truncated = (
        '\n'.join(lines[:keep_start]) +
        f'\n\n... [Truncated {len(lines) - max_lines} lines] ...\n\n' +
        '\n'.join(lines[-keep_end:])
    )
    return truncated

def post_comment_to_github(pr_number, comment_body, repo_full_name, github_token):
    url = f"https://api.github.com/repos/{repo_full_name}/issues/{pr_number}/comments"

    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    data = {"body": comment_body}
    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 201:
        print("✅ Comment posted successfully.")
    else:
        print(f"❌ Failed to post comment: {response.status_code} {response.text}")

async def handle_pull_request(repo_url, branch, pr_url):
    print ('Temp directory is {}'.format(tempfile.gettempdir()))
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = git.Repo.clone_from(repo_url, tmpdir)
        print ("✅ git replo cloned.")
        repo.git.checkout(branch)
        print ("✅ Checked out the branch.")

        # 1. Add upstream remote (original repo)
        token = os.getenv("GITHUB_TOKEN")
        repo.create_remote("upstream", url="git@github.com:sandeepknd/openshift-tests-private.git")
        print ("✅ Created remote branch")

        # 2. Fetch upstream/main
        repo.git.fetch("upstream", "master")
        print ("✅ Fetched upstream master")

        # 3. Generate diff against upstream/main
        diff_output = repo.git.diff("upstream/master..HEAD")
        print ("✅ Gitdiff-ed upstream master")
        lint_report = run_golint(tmpdir)
        print ("✅ Created golint report")
        vet_report = run_govet(tmpdir)
        print ("✅ Created govet report")

        # Truncate reports to avoid exceeding context limits
        # Prioritize: lint (100 lines) + vet (100 lines) + diff (300 lines)
        lint_report_truncated = truncate_text(lint_report, max_lines=100)
        vet_report_truncated = truncate_text(vet_report, max_lines=100)
        diff_output_truncated = truncate_text(diff_output, max_lines=300)

        print(f"[INFO] Lint report: {len(lint_report.split(chr(10)))} lines -> {len(lint_report_truncated.split(chr(10)))} lines")
        print(f"[INFO] Vet report: {len(vet_report.split(chr(10)))} lines -> {len(vet_report_truncated.split(chr(10)))} lines")
        print(f"[INFO] Diff: {len(diff_output.split(chr(10)))} lines -> {len(diff_output_truncated.split(chr(10)))} lines")

        prompt = f"""
Analyze this Golang PR for:
- Code quality
- Error handling
- Logging
- Edge cases
- Testing (if present)
- Best practices

GOLINT:
{lint_report_truncated}

GOVET:
{vet_report_truncated}

GIT DIFF:
{diff_output_truncated}

Please provide a concise review focusing on the most important issues.
"""
        comment = call_llm(prompt)
        print("\n--- LLM Generated PR Comment ---\n", comment)

        # Check if the LLM call failed
        if comment.startswith("Error calling Claude CLI:") or comment.startswith("Error:") or "too long" in comment.lower():
            print(f"❌ Failed to generate PR review comment: {comment}")

            # If prompt is too long even after truncation, provide a manual review message
            if "too long" in comment.lower():
                comment = """## ⚠️ PR Review - Manual Review Required

This PR is too large for automated analysis. Please ensure:
- Code follows best practices and style guidelines
- Error handling is comprehensive
- Logging is appropriate
- Edge cases are handled
- Tests are included and comprehensive

Please review the golint and govet reports in the CI logs for specific issues.
"""
                print("[INFO] Using fallback comment due to prompt length")
            else:
                raise Exception(f"LLM failed to generate comment: {comment}")

        # Call GitHub API to post comment
        pr_num = pr_url.split('/')[-1]
        post_comment_to_github(pr_num, comment, "openshift/openshift-tests-private",token)

#----------golang tools------------

def run_golint(repo_path):
    try:
        result = subprocess.run(
            ["golint", "./..."],
            cwd=repo_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.stdout or result.stderr
    except Exception as e:
        return f"golint error: {str(e)}"

def run_govet(repo_path):
    try:
        result = subprocess.run(
            ["go", "vet", "./..."],
            cwd=repo_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.stdout or result.stderr
    except Exception as e:
        return f"go vet error: {str(e)}"

