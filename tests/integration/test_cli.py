from misikkki_core.cli import main


def test_default_cli_runs_paper_demo_without_subcommand(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)

    assert main([]) == 0

    output = capsys.readouterr().out
    assert "MisikkkiBot OSS paper demo complete" in output
    assert "orders=" in output
    assert (tmp_path / ".misikkki" / "demo.sqlite").exists()
    assert (tmp_path / ".misikkki" / "audit.jsonl").exists()


def test_verify_no_live_cli(capsys):
    assert main(["verify-no-live"]) == 0
    assert "Live trading is not implemented" in capsys.readouterr().out


def test_inspect_strategy_cli(capsys):
    assert main(["inspect-strategy"]) == 0
    output = capsys.readouterr().out
    assert "strategy_id=moving_average_crossover:v1" in output
    assert "short_window=2" in output
