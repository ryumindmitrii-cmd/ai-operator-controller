from ai_operator_controller.cli import main


def test_version_command(capsys):
    assert main(["--version"]) == 0
    assert "0.1.0" in capsys.readouterr().out

