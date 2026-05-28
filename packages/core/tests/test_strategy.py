from misikkki_backtest import load_candles
from misikkki_core.strategy import MovingAverageCrossoverStrategy


def test_moving_average_strategy_emits_inspectable_signals():
    candles = load_candles("sample_data/btc_usdt_1m.csv")
    strategy = MovingAverageCrossoverStrategy(symbol="BTC/USDT")

    signals = [signal for candle in candles if (signal := strategy.on_candle(candle)) is not None]

    assert strategy.parameters()["short_window"] == 2
    assert strategy.parameters()["long_window"] == 3
    assert [signal.side.value for signal in signals] == ["buy", "sell", "buy"]
    assert all("short_ma" in signal.reason for signal in signals)
