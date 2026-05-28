from __future__ import annotations

import argparse
import tkinter as tk
from tkinter import messagebox, scrolledtext

from misikkki_core.engine import run_paper_demo, trigger_demo_kill_switch


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="misikkki-desktop", description="MisikkkiBot OSS desktop launcher")
    parser.add_argument("--headless", action="store_true", help="Run the first-run paper flow without opening a window")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.headless:
        result = run_paper_demo()
        print("MisikkkiBot OSS desktop headless smoke complete")
        print(f"session_id={result.session_id}")
        print(f"orders={result.summary['orders']}")
        print(f"audit_log={result.audit_log_path}")
        return 0

    try:
        launch_window()
    except tk.TclError:
        result = run_paper_demo()
        print("GUI display unavailable; ran headless paper flow instead")
        print(f"session_id={result.session_id}")
        print(f"orders={result.summary['orders']}")
    return 0


def launch_window() -> None:
    root = tk.Tk()
    root.title("MisikkkiBot OSS")
    root.geometry("780x520")
    root.minsize(680, 420)

    state: dict[str, object] = {"last_result": None}

    header = tk.Label(root, text="MisikkkiBot OSS Paper Workstation", font=("Segoe UI", 15, "bold"), anchor="w")
    header.pack(fill="x", padx=16, pady=(14, 6))

    controls = tk.Frame(root)
    controls.pack(fill="x", padx=16, pady=6)

    output = scrolledtext.ScrolledText(root, height=22, wrap="word")
    output.pack(fill="both", expand=True, padx=16, pady=(8, 16))

    def append(line: str) -> None:
        output.insert("end", line + "\n")
        output.see("end")

    def run_demo() -> None:
        result = run_paper_demo()
        state["last_result"] = result
        append("Paper session complete")
        append(f"session_id={result.session_id}")
        append(f"orders={result.summary['orders']}")
        append(f"risk_decisions={result.summary['risk_decisions']}")
        append(f"blocked_orders={result.summary['blocked_orders']}")
        append(f"audit_log={result.audit_log_path}")
        append("")

    def kill_switch() -> None:
        result = state.get("last_result")
        if result is None:
            messagebox.showinfo("Kill switch", "No paper session has run yet.")
            return
        payload = trigger_demo_kill_switch(result, "desktop_operator_requested")
        append(f"Kill switch activated: {payload['reason']}")

    tk.Button(controls, text="Run Paper Demo", command=run_demo, width=18).pack(side="left", padx=(0, 8))
    tk.Button(controls, text="Kill Switch", command=kill_switch, width=14).pack(side="left")

    append("Ready. Paper trading is the default; live trading is unavailable in this MVP.")
    root.mainloop()
