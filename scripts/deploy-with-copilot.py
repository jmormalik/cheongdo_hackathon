#!/usr/bin/env python3
"""Validate a Copilot token, redeploy the app, then require live AI success."""
import argparse
import getpass
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
helpers = runpy.run_path(str(ROOT / "scripts/set-copilot-secret.py"))


def find_aspire():
    executable = shutil.which("aspire")
    if executable:
        return executable
    # The Aspire installer does not update an already-open terminal's PATH.
    for name in ("aspire", "aspire.exe"):
        candidate = Path.home() / ".aspire" / "bin" / name
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None


def deploy_existing_app(args, env, token):
    app = helpers["azure"]("containerapp", "show", "--resource-group", args.resource_group,
                           "--name", args.app, "-o", "json")
    containers = app["properties"]["template"]["containers"]
    container = next((item for item in containers if item["name"] == args.app), None)
    if container is None:
        raise RuntimeError("배포할 컨테이너를 찾을 수 없습니다. --app 이름을 확인하세요.")
    current_image = container["image"]
    registry, separator, repository = current_image.partition("/")
    if not separator or not registry.endswith(".azurecr.io"):
        raise RuntimeError("기존 앱 이미지가 Azure Container Registry에 없습니다.")
    repository = repository.split("@", 1)[0].split(":", 1)[0]
    image = f"{registry}/{repository}:copilot-fix-{uuid.uuid4().hex[:12]}"
    # Build and registry commands do not need the Copilot deployment token.
    build_env = {key: value for key, value in env.items()
                 if key not in ("COPILOT_GITHUB_TOKEN", "Parameters__copilot-token")}
    run(["az", "acr", "login", "--name", registry.removesuffix(".azurecr.io")], build_env, token)
    run(["docker", "build", "--platform", "linux/amd64", "--tag", image, "."], build_env, token)
    run(["docker", "push", image], build_env, token)
    run(["az", "containerapp", "update", "--resource-group", args.resource_group,
         "--name", args.app, "--container-name", container["name"], "--image", image,
         "--output", "none"], build_env, token)


def run(command, env, token):
    # Capture and redact deployment output, including any rendered parameters.
    result = subprocess.run(command, cwd=ROOT, env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True)
    output = result.stdout.replace(token, "[REDACTED]")
    if output:
        print(output, end="", flush=True)
    if result.returncode:
        raise RuntimeError(f"{command[0]} 실행 실패. 재배포/AI 검증을 완료하지 못했습니다.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resource-group", default="cheongdo-farming-demo")
    parser.add_argument("--app", default="this-week-farming")
    parser.add_argument("--environment", default="DemoJapan")
    parser.add_argument("--location", default="japaneast")
    parser.add_argument("--method", choices=("auto", "aspire", "azure-cli"), default="auto",
                        help="auto: use Aspire when installed, otherwise Azure CLI and Docker")
    args = parser.parse_args()
    aspire = find_aspire()
    use_aspire = args.method == "aspire" or (args.method == "auto" and aspire is not None and shutil.which("dotnet") is not None)
    if use_aspire and not aspire:
        raise RuntimeError("Aspire를 찾을 수 없습니다. --method azure-cli로 실행하세요.")
    for tool in ("az", "docker", "node") + (("dotnet",) if use_aspire else ()):
        if not shutil.which(tool):
            raise RuntimeError(f"필수 도구를 찾을 수 없습니다: {tool}")
    token = os.environ.get("COPILOT_GITHUB_TOKEN", "").strip() or getpass.getpass(
        "유효한 Copilot 토큰 (화면에 표시되지 않음): "
    ).strip()
    print("1/5 GitHub 토큰 유효성 확인", flush=True)
    helpers["validate_token"](token)
    subscription = helpers["azure"]("account", "show", "--query", "id", "-o", "json")
    env = dict(os.environ)
    env.update({
        "COPILOT_GITHUB_TOKEN": token,
        "Parameters__copilot-token": token,
        "Azure__SubscriptionId": subscription,
        "Azure__ResourceGroup": args.resource_group,
        "Azure__Location": args.location,
        "Azure__CredentialSource": "AzureCli",
        "DOCKER_DEFAULT_PLATFORM": "linux/amd64",
    })
    print("2/5 Docker 실행 확인", flush=True)
    run(["docker", "info", "--format", "{{.ServerVersion}}"], env, token)
    if use_aspire:
        print("3/5 최신 코드 이미지 빌드 및 Aspire 재배포", flush=True)
        run([aspire, "deploy", "--apphost", "AppHost/AppHost.csproj",
             "--environment", args.environment, "--non-interactive"], env, token)
    else:
        print("3/5 Azure CLI + Docker로 기존 앱 재배포 (Aspire 설치 불필요)", flush=True)
        deploy_existing_app(args, env, token)
    print("4/5 Secret 참조 통일 및 새 리비전에 토큰 적용", flush=True)
    run([sys.executable, "scripts/set-copilot-secret.py", "--resource-group",
         args.resource_group, "--app", args.app], env, token)
    domain = helpers["azure"]("containerapp", "show", "--resource-group", args.resource_group,
                              "--name", args.app, "--query",
                              "properties.configuration.ingress.fqdn", "-o", "json")
    if not domain:
        raise RuntimeError("배포 앱의 공개 도메인을 찾을 수 없습니다.")
    print("5/5 공개 URL에서 실제 모델·도구 호출 검증", flush=True)
    # Do not pass deployment credentials to the public HTTP smoke test.
    smoke_env = {key: value for key, value in env.items()
                 if key not in ("COPILOT_GITHUB_TOKEN", "Parameters__copilot-token")}
    run(["node", "scripts/smoke-deployment.mjs", "https://" + domain, "--ai"], smoke_env, token)
    print("재배포 및 실제 AI 응답 검증 완료: https://" + domain)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, EOFError, KeyboardInterrupt) as error:
        raise SystemExit(str(error) or "토큰 입력 또는 배포가 중단됐습니다.") from None
