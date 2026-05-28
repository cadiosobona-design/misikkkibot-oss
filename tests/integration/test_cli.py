from misikkki_core.cli import main


def test_verify_no_live_cli(capsys):
    assert main(["verify-no-live"]) == 0
    assert "Live trading is not implemented" in capsys.readouterr().out


def test_inspect_strategy_cli(capsys):
    assert main(["inspect-strategy"]) == 0
    output = capsys.readouterr().out
    assert "strategy_id=moving_average_crossover:v1" in output
    assert "short_window=2" in output
