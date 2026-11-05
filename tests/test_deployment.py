import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock


spec = importlib.util.spec_from_file_location(
    "deployment", Path(__file__).resolve().parents[1] / "scripts/deploy-with-copilot.py"
)
deployment = importlib.util.module_from_spec(spec)
spec.loader.exec_module(deployment)


def test_aspire_found_outside_path(monkeypatch, tmp_path):
    candidate = tmp_path / ".aspire/bin/aspire"
    candidate.parent.mkdir(parents=True)
    candidate.write_text("#!/bin/sh\n")
    candidate.chmod(0o700)
    monkeypatch.setattr(deployment.shutil, "which", lambda name: None)
    monkeypatch.setattr(deployment.Path, "home", lambda: tmp_path)
    assert deployment.find_aspire() == str(candidate)


def test_azure_deployment_builds_new_image_without_copilot_credentials(monkeypatch):
    azure = Mock(return_value={"properties": {"template": {"containers": [
        {"name": "farming", "image": "example.azurecr.io/team/farming:old"}
    ]}}})
    monkeypatch.setitem(deployment.helpers, "azure", azure)
    runner = Mock()
    monkeypatch.setattr(deployment, "run", runner)
    deployment.deploy_existing_app(
        SimpleNamespace(resource_group="demo", app="farming"),
        {"PATH": "/bin", "COPILOT_GITHUB_TOKEN": "secret", "Parameters__copilot-token": "secret"},
        "secret",
    )
    commands = [call.args[0] for call in runner.call_args_list]
    assert commands[0] == ["az", "acr", "login", "--name", "example"]
    assert commands[1][:4] == ["docker", "build", "--platform", "linux/amd64"]
    image = commands[1][5]
    assert image.startswith("example.azurecr.io/team/farming:copilot-fix-")
    assert commands[2] == ["docker", "push", image]
    assert commands[3][-4:] == ["--image", image, "--output", "none"]
    assert all(call.args[1] == {"PATH": "/bin"} for call in runner.call_args_list)
