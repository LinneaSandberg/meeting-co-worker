"""
GitHub Integration Module
Creates GitHub issues from meeting action items and open questions.
"""

import os
import sys
from typing import Optional
from github import Github, GithubException

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logging_config import get_github_logger

logger = get_github_logger()


def create_github_issue(
    title: str,
    body: str,
    labels: Optional[list] = None,
    issue_type: str = "action_item"
) -> dict:
    """
    Create a GitHub issue using PyGithub library.

    Args:
        title: Issue title
        body: Issue description (markdown formatted)
        labels: Optional list of label strings
        issue_type: Type of issue ("action_item" or "open_question")

    Returns:
        dict with 'success', 'issue_url', 'issue_number', or 'error'
    """
    # Get configuration from environment
    token = os.getenv("GITHUB_TOKEN")
    repo_owner = os.getenv("GITHUB_REPO_OWNER")
    repo_name = os.getenv("GITHUB_REPO_NAME")
    default_labels = os.getenv("GITHUB_DEFAULT_LABELS", "meeting-copilot").split(",")

    # Validate configuration
    if not token:
        logger.error("GitHub token not configured")
        return {
            "success": False,
            "error": "GitHub token not configured. Add GITHUB_TOKEN to .env file."
        }

    if not repo_owner or not repo_name:
        logger.error("GitHub repository not configured")
        return {
            "success": False,
            "error": "GitHub repository not configured. Add GITHUB_REPO_OWNER and GITHUB_REPO_NAME to .env file."
        }

    try:
        # Initialize GitHub client
        logger.debug(f"Creating GitHub issue: {title[:50]}...")
        g = Github(token)

        # Get repository
        repo_full_name = f"{repo_owner}/{repo_name}"
        repo = g.get_repo(repo_full_name)

        # Prepare labels
        issue_labels = labels if labels else []
        issue_labels.extend(default_labels)

        # Add type-specific label
        if issue_type == "action_item":
            issue_labels.append("action-item")
        elif issue_type == "open_question":
            issue_labels.append("open-question")

        # Remove duplicates and empty strings
        issue_labels = list(set([label.strip() for label in issue_labels if label.strip()]))

        # Create issue
        issue = repo.create_issue(
            title=title,
            body=body,
            labels=issue_labels
        )

        logger.info(f"GitHub issue created: #{issue.number} - {issue.html_url}")
        return {
            "success": True,
            "issue_url": issue.html_url,
            "issue_number": issue.number,
            "error": None
        }

    except GithubException as e:
        # Handle specific GitHub errors
        if e.status == 401:
            error_msg = "GitHub authentication failed. Check your GITHUB_TOKEN in .env file."
            logger.error(f"GitHub auth failed (401): Invalid token")
        elif e.status == 404:
            error_msg = f"Repository not found: {repo_owner}/{repo_name}. Check GITHUB_REPO_OWNER and GITHUB_REPO_NAME in .env file."
            logger.error(f"GitHub repo not found (404): {repo_owner}/{repo_name}")
        elif e.status == 403:
            if "rate limit" in str(e).lower():
                error_msg = "GitHub rate limit exceeded. Please try again later."
                logger.warning("GitHub rate limit exceeded")
            else:
                error_msg = "GitHub access denied. Check your token permissions (needs 'repo' scope)."
                logger.error("GitHub access denied (403): Insufficient token permissions")
        else:
            error_msg = f"GitHub API error: {e.data.get('message', str(e)) if hasattr(e, 'data') else str(e)}"
            logger.error(f"GitHub API error ({e.status}): {error_msg}")

        return {
            "success": False,
            "error": error_msg
        }

    except Exception as e:
        logger.error(f"Unexpected error creating GitHub issue: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }


def format_action_item_issue(task: str, owner: Optional[str] = None, deadline: Optional[str] = None) -> tuple:
    """
    Format an action item as a GitHub issue title and body.

    Args:
        task: The action item task description
        owner: Optional owner of the task
        deadline: Optional deadline for the task

    Returns:
        tuple of (title, body)
    """
    title = task

    body_parts = [f"**Task:** {task}", ""]

    if owner:
        body_parts.append(f"**Owner:** @{owner}")

    if deadline:
        body_parts.append(f"**Deadline:** {deadline}")

    body_parts.extend([
        "",
        "---",
        "*This issue was automatically created from a meeting transcription by Meeting Copilot.*"
    ])

    body = "\n".join(body_parts)

    return title, body


def format_question_issue(question: str, context: Optional[str] = None) -> tuple:
    """
    Format an open question as a GitHub issue title and body.

    Args:
        question: The open question text
        context: Optional context about why it matters

    Returns:
        tuple of (title, body)
    """
    title = question

    body_parts = [f"**Question:** {question}", ""]

    if context:
        body_parts.append(f"**Context:** {context}")
        body_parts.append("")

    body_parts.extend([
        "---",
        "*This question was identified during a meeting transcription by Meeting Copilot.*"
    ])

    body = "\n".join(body_parts)

    return title, body


def check_github_config() -> dict:
    """
    Check if GitHub integration is properly configured.

    Returns:
        dict with 'enabled', 'repo', and optional 'error'
    """
    token = os.getenv("GITHUB_TOKEN")
    repo_owner = os.getenv("GITHUB_REPO_OWNER")
    repo_name = os.getenv("GITHUB_REPO_NAME")

    if not token or not repo_owner or not repo_name:
        logger.debug("GitHub integration not configured (missing env vars)")
        return {
            "enabled": False,
            "repo": None,
            "error": "GitHub not configured"
        }

    try:
        # Try to access the repository to verify credentials
        g = Github(token)
        repo = g.get_repo(f"{repo_owner}/{repo_name}")

        logger.debug(f"GitHub integration verified: {repo_owner}/{repo_name}")
        return {
            "enabled": True,
            "repo": f"{repo_owner}/{repo_name}",
            "error": None
        }

    except GithubException as e:
        logger.warning(f"GitHub config check failed: {str(e)}")
        return {
            "enabled": False,
            "repo": f"{repo_owner}/{repo_name}",
            "error": f"GitHub configuration error: {str(e)}"
        }

    except Exception as e:
        logger.error(f"Unexpected error checking GitHub config: {str(e)}", exc_info=True)
        return {
            "enabled": False,
            "repo": None,
            "error": f"Unexpected error: {str(e)}"
        }
