import io
import json

import pytest

import protect_secrets as ps


def run_main(monkeypatch, tool_name, tool_input):
    stdin_data = {"tool_name": tool_name, "tool_input": tool_input}
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(stdin_data)))
    with pytest.raises(SystemExit) as exc_info:
        ps.main()
    return exc_info.value.code


def test_blocks_read_env(monkeypatch, capsys):
    code = run_main(monkeypatch, "Read", {"file_path": "/project/.env"})
    assert code == 2
    assert ".env" in capsys.readouterr().err


def test_blocks_edit_env_local(monkeypatch):
    assert run_main(monkeypatch, "Edit", {"file_path": "/project/.env.local"}) == 2


def test_blocks_write_ssh_key(monkeypatch):
    assert run_main(monkeypatch, "Write", {"file_path": "/Users/x/.ssh/id_rsa"}) == 2


def test_blocks_aws_credentials(monkeypatch):
    assert run_main(monkeypatch, "Read", {"file_path": "/Users/x/.aws/credentials"}) == 2


def test_allows_read_normal_file(monkeypatch):
    assert run_main(monkeypatch, "Read", {"file_path": "/project/README.md"}) == 0


def test_blocks_bash_cat_env(monkeypatch, capsys):
    code = run_main(monkeypatch, "Bash", {"command": "cat .env"})
    assert code == 2


def test_blocks_bash_grep_env(monkeypatch):
    assert run_main(monkeypatch, "Bash", {"command": "grep -r API_KEY .env"}) == 2


def test_allows_bash_unrelated_command(monkeypatch):
    assert run_main(monkeypatch, "Bash", {"command": "ls -la"}) == 0


def test_allows_other_tool_names(monkeypatch):
    assert run_main(monkeypatch, "Glob", {"pattern": "**/.env"}) == 0


def test_main_exits_cleanly_on_malformed_stdin(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("not json"))
    with pytest.raises(SystemExit) as exc_info:
        ps.main()
    assert exc_info.value.code == 0


def test_is_protected_path_direct():
    assert ps.is_protected_path("/x/.env") is True
    assert ps.is_protected_path("/x/README.md") is False
    assert ps.is_protected_path("") is False


def test_is_protected_path_pem_and_keystore():
    assert ps.is_protected_path("/x/key.pem") is True
    assert ps.is_protected_path("/x/release.keystore") is True


def test_bash_targets_protected_file_direct():
    assert ps.bash_targets_protected_file("cp .env /tmp/leak") is True
    assert ps.bash_targets_protected_file("echo hi") is False
    assert ps.bash_targets_protected_file("") is False
