from pathlib import Path


SMOKE_SCRIPT = Path("scripts/smoke.ps1")


def test_smoke_script_supports_process_local_proxy_bypass_for_pip_audit():
    script = SMOKE_SCRIPT.read_text(encoding="utf-8")

    assert "[switch]$BypassProxyForPipAudit" in script
    assert "Invoke-WithProxyBypass" in script
    assert "HTTP_PROXY" in script
    assert "HTTPS_PROXY" in script
    assert "ALL_PROXY" in script
    assert "NO_PROXY" in script
    assert "pip_audit" in script
    assert "--skip-editable" in script
