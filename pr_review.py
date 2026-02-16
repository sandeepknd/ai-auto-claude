import os
import tempfile
import subprocess
import git
import subprocess
from math_ai_agent_doc import call_llama3

import httpx
from urllib.parse import urlparse
import requests

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
        prompt = f"""
Analyze this Golang PR for:
- Code quality
- Error handling
- Logging
- Edge cases
- Testing (if present)
- Best practices

GOLINT:
{lint_report}

GOVET:
{vet_report}

GIT DIFF:
{diff_output}
"""
        comment = call_llama3(prompt)
        print("\n--- LLM Generated PR Comment ---\n", comment)

        # Check if the LLM call failed
        if comment.startswith("Error calling Claude CLI:") or comment.startswith("Error:"):
            print(f"❌ Failed to generate PR review comment: {comment}")
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

