# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules


ROOT = Path(SPECPATH).parents[1]
PYTHONPATH = [
    str(ROOT / "apps" / "desktop" / "src"),
    str(ROOT / "packages" / "audit" / "src"),
    str(ROOT / "packages" / "backtest" / "src"),
    str(ROOT / "packages" / "connectors" / "src"),
    str(ROOT / "packages" / "core" / "src"),
    str(ROOT / "packages" / "data" / "src"),
    str(ROOT / "packages" / "risk" / "src"),
    str(ROOT / "packages" / "security" / "src"),
    str(ROOT / "packages" / "storage" / "src"),
]

project_packages = [
    "misikkki_audit",
    "misikkki_backtest",
    "misikkki_connectors",
    "misikkki_core",
    "misikkki_data",
    "misikkki_desktop",
    "misikkki_risk",
    "misikkki_security",
    "misikkki_storage",
]
datas = collect_data_files("misikkki_data") + collect_data_files("misikkki_storage")
hiddenimports = []
for package in project_packages:
    hiddenimports += collect_submodules(package)

cli_analysis = Analysis(
    [str(ROOT / "packaging" / "windows" / "launchers" / "misikkki_cli.py")],
    pathex=PYTHONPATH,
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
cli_pyz = PYZ(cli_analysis.pure)
cli_exe = EXE(
    cli_pyz,
    cli_analysis.scripts,
    [],
    exclude_binaries=True,
    name="misikkki",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

desktop_analysis = Analysis(
    [str(ROOT / "packaging" / "windows" / "launchers" / "desktop_launcher.py")],
    pathex=PYTHONPATH,
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
desktop_pyz = PYZ(desktop_analysis.pure)
desktop_exe = EXE(
    desktop_pyz,
    desktop_analysis.scripts,
    [],
    exclude_binaries=True,
    name="MisikkkiBot",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    cli_exe,
    desktop_exe,
    cli_analysis.binaries,
    desktop_analysis.binaries,
    cli_analysis.datas,
    desktop_analysis.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="MisikkkiBot-0.1.1-win-x64",
)
