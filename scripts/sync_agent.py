#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import json
import os
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib import error, request
from zipfile import ZIP_DEFLATED, ZipFile


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENV_FILE = Path(__file__).with_name(".env")
SUPPORTED_ENVS = ("prod", "test", "dev")


@dataclass(frozen=True)
class SyncConfig:
    env: str
    endpoint: str
    agent_id: str
    agent_name: str
    headers: dict[str, str]
    upload_url: str
    workspace_sync_url: str
    agent_url: str
    mcp_refresh_url: str


def load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            raise RuntimeError(f"Invalid env line {path}:{line_number}")

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise RuntimeError(f"Invalid env key at {path}:{line_number}")
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        os.environ.setdefault(key, value)


def env_value(env: str, name: str, *, default: str | None = None) -> str | None:
    env_key = f"DUDU_AGENT_SYNC_{env.upper()}_{name}"
    shared_key = f"DUDU_AGENT_SYNC_{name}"
    value = os.environ.get(env_key)
    if value is None:
        value = os.environ.get(shared_key)
    if value is None or value == "":
        return default
    return value


def required_env_value(env: str, name: str) -> str:
    value = env_value(env, name)
    if not value:
        raise RuntimeError(
            f"Missing DUDU_AGENT_SYNC_{env.upper()}_{name} "
            f"or DUDU_AGENT_SYNC_{name}"
        )
    return value


def parse_json_env(env: str, name: str, *, default: object) -> object:
    raw_value = env_value(env, name)
    if raw_value is None:
        return default
    try:
        return json.loads(raw_value)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"DUDU_AGENT_SYNC_{env.upper()}_{name} must be valid JSON") from exc


def load_config(env: str) -> SyncConfig:
    endpoint = env_value(env, "ENDPOINT") or env_value(env, "BASE_URL")
    if not endpoint:
        raise RuntimeError(
            f"Missing DUDU_AGENT_SYNC_{env.upper()}_ENDPOINT "
            f"or DUDU_AGENT_SYNC_{env.upper()}_BASE_URL"
        )
    endpoint = endpoint.rstrip("/")
    agent_id = required_env_value(env, "AGENT_ID")
    agent_name = required_env_value(env, "AGENT_NAME")

    headers_value = parse_json_env(env, "HEADERS", default={})
    if not isinstance(headers_value, dict) or not headers_value:
        raise RuntimeError(f"DUDU_AGENT_SYNC_{env.upper()}_HEADERS must be a JSON object")
    headers = {str(key): str(value) for key, value in headers_value.items()}

    return SyncConfig(
        env=env,
        endpoint=endpoint,
        agent_id=agent_id,
        agent_name=agent_name,
        headers=headers,
        upload_url=env_value(env, "SKILLS_UPLOAD_URL", default=f"{endpoint}/api/skills/upload"),
        workspace_sync_url=env_value(
            env,
            "SKILLS_WORKSPACE_SYNC_URL",
            default=f"{endpoint}/api/skills/sync-to-agent-workspaces",
        ),
        agent_url=env_value(env, "AGENT_URL", default=f"{endpoint}/api/agent"),
        mcp_refresh_url=env_value(
            env,
            "MCP_REFRESH_URL",
            default=f"{endpoint}/api/mcp/dudu-agent-core/refresh",
        ),
    )


def mcp_tool_names(mcp_tools_dir: Path) -> list[str]:
    if not mcp_tools_dir.exists():
        raise RuntimeError(f"MCP tools dir does not exist: {mcp_tools_dir}")

    names: list[str] = []
    seen: set[str] = set()

    for path in sorted(mcp_tools_dir.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for decorator in node.decorator_list:
                if not is_mcp_tool_decorator(decorator):
                    continue
                tool_name = mcp_tool_name_from_decorator(decorator) or node.name
                if tool_name not in seen:
                    names.append(tool_name)
                    seen.add(tool_name)

    if not names:
        raise RuntimeError(f"No MCP tool registrations found in {mcp_tools_dir}")
    return names


def is_mcp_tool_decorator(decorator: ast.expr) -> bool:
    target = decorator.func if isinstance(decorator, ast.Call) else decorator
    return (
        isinstance(target, ast.Attribute)
        and target.attr == "tool"
        and isinstance(target.value, ast.Name)
    )


def mcp_tool_name_from_decorator(decorator: ast.expr) -> str | None:
    if not isinstance(decorator, ast.Call):
        return None
    for keyword in decorator.keywords:
        if keyword.arg == "name" and isinstance(keyword.value, ast.Constant):
            value = keyword.value.value
            if isinstance(value, str) and value:
                return value
    return None


def skill_dirs(skills_dir: Path) -> list[Path]:
    if not skills_dir.exists():
        raise RuntimeError(f"Skills dir does not exist: {skills_dir}")

    directories: list[Path] = []
    for path in sorted(item for item in skills_dir.iterdir() if item.is_dir()):
        has_skill_file = any(
            child.is_file() and child.name.lower() == "skill.md"
            for child in path.iterdir()
        )
        if has_skill_file:
            directories.append(path)
    return directories


def zip_skill(skills_dir: Path, skill_dir: Path, output_dir: Path) -> Path:
    zip_path = output_dir / f"{skill_dir.name}.zip"
    with ZipFile(zip_path, "w", ZIP_DEFLATED) as archive:
        for path in sorted(item for item in skill_dir.rglob("*") if item.is_file()):
            archive.write(path, path.relative_to(skills_dir).as_posix())
    return zip_path


def multipart_body(field_name: str, file_path: Path) -> tuple[bytes, str]:
    boundary = "----dudu-agent-core-skill-upload-boundary"
    body = b"\r\n".join(
        [
            f"--{boundary}".encode("utf-8"),
            (
                f'Content-Disposition: form-data; name="{field_name}"; '
                f'filename="{file_path.name}"'
            ).encode("utf-8"),
            b"Content-Type: application/zip",
            b"",
            file_path.read_bytes(),
            f"--{boundary}--".encode("utf-8"),
            b"",
        ]
    )
    return body, f"multipart/form-data; boundary={boundary}"


def request_headers(config: SyncConfig, content_type: str | None = None) -> dict[str, str]:
    headers = dict(config.headers)
    if content_type:
        headers["Content-Type"] = content_type
    return headers


def open_request(http_request: request.Request, timeout: int = 60) -> bytes:
    try:
        with request.urlopen(http_request, timeout=timeout) as response:
            body = response.read()
            print(f"Request succeeded: {http_request.full_url} status={response.status}")
            return body
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"Request failed: {http_request.full_url} status={exc.code}")
        if body:
            print(body)
        raise


def open_json_request(http_request: request.Request, timeout: int = 60) -> dict:
    body = open_request(http_request, timeout=timeout)
    if not body:
        return {}
    data = json.loads(body.decode("utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"Expected JSON object from {http_request.full_url}")
    if data.get("success") is False:
        raise RuntimeError(data.get("message") or f"Request failed: {http_request.full_url}")
    return data


def upload_skill(config: SyncConfig, zip_path: Path) -> None:
    body, content_type = multipart_body("file", zip_path)
    upload_request = request.Request(
        config.upload_url,
        data=body,
        headers=request_headers(config, content_type),
        method="POST",
    )
    print(f"Uploading skill package: {zip_path.name}")
    open_request(upload_request)


def fetch_agent(config: SyncConfig) -> dict | None:
    agent_detail_url = f"{config.agent_url.rstrip('/')}/{config.agent_id}"
    get_request = request.Request(
        agent_detail_url,
        headers=request_headers(config),
        method="GET",
    )
    print(f"Fetching agent config: {config.agent_id}")
    try:
        response_data = open_json_request(get_request)
    except error.HTTPError as exc:
        if exc.code == 404:
            print(f"Agent does not exist: {config.agent_id}. Skipping remaining steps.")
            return None
        raise

    agent_payload = response_data.get("data")
    if not isinstance(agent_payload, dict):
        print(f"Agent config response has no data object: {config.agent_id}")
        print("Skipping remaining steps.")
        return None
    return dict(agent_payload)


def ensure_available_skills(agent_payload: dict, skill_names: list[str]) -> bool:

    agent_payload["availableSkills"] = skill_names
    print("Configured agent availableSkills: " + ", ".join(skill_names))
    return True


def ensure_available_tools(agent_payload: dict, tool_names: list[str]) -> bool:

    agent_payload["availableTools"] = tool_names
    print("Configured agent availableTools: " + ", ".join(tool_names))
    return True


def prompt_path(prompts_dir: Path, agent_name: str) -> Path:
    path = prompts_dir / agent_name / "system_prompt.md"
    if not path.exists():
        raise RuntimeError(f"Prompt file does not exist: {path}")
    return path


def update_agent(config: SyncConfig, agent_payload: dict) -> None:
    agent_payload = dict(agent_payload)
    agent_payload["id"] = agent_payload.get("id") or config.agent_id
    agent_payload["name"] = agent_payload.get("name") or config.agent_name

    body = json.dumps(agent_payload, ensure_ascii=False).encode("utf-8")
    update_request = request.Request(
        f"{config.agent_url.rstrip('/')}/{config.agent_id}",
        data=body,
        headers=request_headers(config, "application/json"),
        method="PUT",
    )
    print(f"Updating agent config: {config.agent_id}")
    open_request(update_request)


def sync_agent_workspaces(config: SyncConfig, skill_names: list[str]) -> None:
    body = json.dumps(
        {"agent_id": config.agent_id, "skill_names": skill_names},
        ensure_ascii=False,
    ).encode("utf-8")
    sync_request = request.Request(
        config.workspace_sync_url,
        data=body,
        headers=request_headers(config, "application/json"),
        method="POST",
    )
    print("Syncing skills to agent workspaces")
    open_request(sync_request)


def refresh_mcp(config: SyncConfig) -> None:
    refresh_request = request.Request(
        config.mcp_refresh_url,
        data=b"",
        headers=request_headers(config),
        method="POST",
    )
    print("Refreshing MCP server: dudu-agent-core")
    open_request(refresh_request)


def run_sync(
    config: SyncConfig,
    *,
    skills_dir: Path,
    prompts_dir: Path,
    mcp_tools_dir: Path,
    dry_run: bool,
) -> None:
    skills_dir = skills_dir.resolve()
    prompts_dir = prompts_dir.resolve()
    mcp_tools_dir = mcp_tools_dir.resolve()
    directories = skill_dirs(skills_dir)
    skill_names = [directory.name for directory in directories]
    tool_names = mcp_tool_names(mcp_tools_dir)
    system_prompt_path = prompt_path(prompts_dir, config.agent_name)
    system_prompt = system_prompt_path.read_text(encoding="utf-8")

    if dry_run:
        print(f"Environment: {config.env}")
        print(f"Endpoint: {config.endpoint}")
        print(f"Agent: {config.agent_id} ({config.agent_name})")
        print("Header keys: " + ", ".join(sorted(config.headers.keys())))
        print("Skill packages:")
        for skill_name in skill_names:
            print(f"- {skill_name}")
        print(f"Prompt: {system_prompt_path}")
        print(f"MCP tools dir: {mcp_tools_dir}")
        print("Available tools: " + ", ".join(tool_names))
        print("Dry run only; no requests were sent.")
        return

    with TemporaryDirectory() as temp_dir:
        zip_paths = [zip_skill(skills_dir, directory, Path(temp_dir)) for directory in directories]
        for zip_path in zip_paths:
            upload_skill(config, zip_path)

    agent_payload = fetch_agent(config)
    if agent_payload is None:
        return

    ensure_available_skills(agent_payload, skill_names)
    agent_payload["systemPrefix"] = system_prompt
    print(f"Loaded system prompt from: {system_prompt_path}")
    ensure_available_tools(agent_payload, tool_names)
    update_agent(config, agent_payload)
    sync_agent_workspaces(config, skill_names)
    refresh_mcp(config)


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync Dudu agent skills, prompt, and tools.")
    parser.add_argument("env", choices=SUPPORTED_ENVS, help="Target environment.")
    parser.add_argument("--env-file", default=str(DEFAULT_ENV_FILE))
    parser.add_argument("--skills-dir", default=str(REPO_ROOT / "skills"))
    parser.add_argument("--prompts-dir", default=str(REPO_ROOT / "prompts"))
    parser.add_argument("--mcp-tools-dir", default=str(REPO_ROOT / "app/api/mcp_tools"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    load_env_file(Path(args.env_file))
    config = load_config(args.env)
    run_sync(
        config,
        skills_dir=Path(args.skills_dir),
        prompts_dir=Path(args.prompts_dir),
        mcp_tools_dir=Path(args.mcp_tools_dir),
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
