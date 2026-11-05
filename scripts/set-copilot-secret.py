#!/usr/bin/env python3
"""Prompt locally and update an ACA secret without putting it in shell history/argv."""
import argparse
import getpass
import json
import os
from pathlib import Path
import subprocess
import tempfile
import uuid


def azure(*args):
    result = subprocess.run(["az", *args], capture_output=True, text=True)
    if result.returncode:
        # Azure errors can contain request data; don't echo them with a secret present.
        raise RuntimeError("Azure 작업에 실패했습니다. 로그인·구독·리소스 권한을 확인하세요.")
    return json.loads(result.stdout) if result.stdout.strip() else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resource-group", default="cheongdo-farming-demo")
    parser.add_argument("--app", default="this-week-farming")
    args = parser.parse_args()
    subscription = azure("account", "show", "--query", "id", "-o", "json")
    resource = f"https://management.azure.com/subscriptions/{subscription}/resourceGroups/{args.resource_group}/providers/Microsoft.App/containerApps/{args.app}"
    version = "?api-version=2025-07-01"
    app = azure("rest", "--method", "get", "--url", resource + version)
    token = getpass.getpass("Copilot 토큰 (화면에 표시되지 않음): ").strip()
    if not token.startswith(("github_pat_", "gho_", "ghu_")):
        raise RuntimeError("지원되는 fine-grained PAT 또는 OAuth 사용자 토큰을 입력하세요.")
    secrets = azure("rest", "--method", "post", "--url", resource + "/listSecrets" + version)["value"]
    secrets = [secret for secret in secrets if secret["name"] != "copilot-token"]
    secrets.append({"name": "copilot-token", "value": token})
    template = app["properties"]["template"]
    # Express supports rolling updates but rejects explicit revision suffixes.
    template.pop("revisionSuffix", None)
    container = next(item for item in template["containers"] if item["name"] == "this-week-farming")
    container["env"] = [item for item in container.get("env", []) if item["name"] != "COPILOT_GITHUB_TOKEN"]
    container["env"].append({"name": "COPILOT_GITHUB_TOKEN", "secretRef": "copilot-token"})
    container["env"] = [item for item in container["env"] if item["name"] != "COPILOT_SECRET_REVISION"]
    container["env"].append({"name": "COPILOT_SECRET_REVISION", "value": uuid.uuid4().hex})
    payload = {"properties": {"configuration": {"secrets": secrets}, "template": template}}
    descriptor, filename = tempfile.mkstemp(prefix="farming-secret-", suffix=".json")
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w") as stream:
            json.dump(payload, stream)
        azure("rest", "--method", "patch", "--url", resource + version, "--body", "@" + filename, "--output", "none")
        azure("containerapp", "update", "--resource-group", args.resource_group, "--name", args.app,
              "--set-env-vars", "COPILOT_GITHUB_TOKEN=secretref:copilot-token",
              "COPILOT_SECRET_REVISION=" + uuid.uuid4().hex, "--output", "none")
    finally:
        Path(filename).unlink(missing_ok=True)
    print("Azure Secret과 환경 변수 참조를 등록했습니다. 새 리비전 준비 후 AI 질문을 확인하세요.")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, KeyError, StopIteration) as error:
        raise SystemExit(str(error) if isinstance(error, RuntimeError) else "Azure 앱 구성을 확인할 수 없습니다.") from None
