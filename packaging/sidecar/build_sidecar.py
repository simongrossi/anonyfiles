"""Build the anonyfiles-api sidecar binary via PyInstaller.

Run from the repo root, inside a Python env that has `anonyfiles[packaging]`
installed (see pyproject.toml) and the spaCy model available.

Produces a folder `anonyfiles_gui/src-tauri/sidecar/anonyfiles-api/` containing
the binary + all its dependencies (PyInstaller `--onedir` mode). Tauri ships
the whole folder via `bundle.resources` and the Rust side resolves the inner
binary at runtime.

Why --onedir instead of --onefile: onefile extracts ~120 MB to a temp dir on
every launch (~20 s cold start on macOS, worse on Windows). onedir extracts
once at install, launches in 2-4 s.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Force UTF-8 stdout so non-ASCII log lines don't crash on Windows cp1252.
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DIST_DIR = REPO_ROOT / "packaging" / "sidecar" / "dist"
BUILD_DIR = REPO_ROOT / "packaging" / "sidecar" / "build"
WORK_DIR = REPO_ROOT / "packaging" / "sidecar"
TARGET_DIR = REPO_ROOT / "anonyfiles_gui" / "src-tauri" / "sidecar"
ENTRY = REPO_ROOT / "anonyfiles_api" / "__main__.py"
CONFIG_DIR = REPO_ROOT / "anonyfiles_core" / "config"

KNOWN_MODELS = {"md", "sm", "lg"}


def rust_triple() -> str:
    """Return the Rust host triple, e.g. aarch64-apple-darwin.

    Kept for CI compatibility (`--triple` flag) but NOT used to name the
    output folder: each platform builds its own set, and the folder is always
    `sidecar/anonyfiles-api/` relative to src-tauri.
    """
    try:
        out = subprocess.check_output(["rustc", "-Vv"], text=True)
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        raise RuntimeError(
            "rustc introuvable. Installe Rust (rustup) ou passe --triple manuellement."
        ) from exc
    for line in out.splitlines():
        if line.startswith("host:"):
            return line.split(":", 1)[1].strip()
    raise RuntimeError("Impossible de détecter la cible Rust depuis `rustc -Vv`")


def build(model: str, clean: bool) -> Path:
    if model not in KNOWN_MODELS:
        raise SystemExit(f"Modèle inconnu: {model}. Attendu: {sorted(KNOWN_MODELS)}")

    if clean:
        shutil.rmtree(DIST_DIR, ignore_errors=True)
        shutil.rmtree(BUILD_DIR, ignore_errors=True)
        shutil.rmtree(TARGET_DIR, ignore_errors=True)

    base_name = "anonyfiles-api"
    sep = os.pathsep  # ':' on POSIX, ';' on Windows
    model_pkg = f"fr_core_news_{model}"

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--name",
        base_name,
        "--distpath",
        str(DIST_DIR),
        "--workpath",
        str(BUILD_DIR),
        "--specpath",
        str(WORK_DIR),
        # spaCy + modèle : submodules + data
        "--collect-all",
        "spacy",
        "--collect-all",
        model_pkg,
        "--collect-all",
        "thinc",
        # notre code
        "--collect-submodules",
        "anonyfiles_api",
        "--collect-submodules",
        "anonyfiles_core",
        # cli_logger + exceptions seulement (pas la CLI Typer complète)
        "--hidden-import",
        "anonyfiles_cli.cli_logger",
        "--hidden-import",
        "anonyfiles_cli.exceptions",
        # config YAML expected by anonyfiles_api/core_config.py
        "--add-data",
        f"{CONFIG_DIR}{sep}anonyfiles_core/config",
        # uvicorn imports dynamiques
        "--hidden-import",
        "uvicorn.logging",
        "--hidden-import",
        "uvicorn.loops.auto",
        "--hidden-import",
        "uvicorn.protocols.http.auto",
        "--hidden-import",
        "uvicorn.protocols.websockets.auto",
        "--hidden-import",
        "uvicorn.lifespan.on",
        # exclusions — CLI TUI / presentation libs non utilisées par l'API
        "--exclude-module",
        "textual",
        "--exclude-module",
        "rich",
        "--exclude-module",
        "IPython",
        "--exclude-module",
        "matplotlib",
        "--exclude-module",
        "pytest",
        "--exclude-module",
        "tkinter",
        "--exclude-module",
        "unittest",
        str(ENTRY),
    ]
    print("->", " ".join(cmd), flush=True)
    subprocess.check_call(cmd, cwd=REPO_ROOT)

    produced_dir = DIST_DIR / base_name
    if not produced_dir.is_dir():
        raise RuntimeError(f"PyInstaller n'a pas produit le dossier {produced_dir}")

    # .DS_Store casse la signature ad-hoc du bundle Tauri (les hashs de
    # resources ne matchent plus après que Finder les ait créés). On les
    # supprime à la source.
    for ds in produced_dir.rglob(".DS_Store"):
        ds.unlink(missing_ok=True)

    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    final_dir = TARGET_DIR / base_name
    if final_dir.exists():
        shutil.rmtree(final_dir)
    shutil.copytree(produced_dir, final_dir)

    # Idem après copie — défensif au cas où le TARGET_DIR en contiendrait.
    for ds in final_dir.rglob(".DS_Store"):
        ds.unlink(missing_ok=True)

    # Sur Unix, préserver le bit exécutable (PyInstaller le met déjà, copytree
    # aussi, mais double-check).
    exe_suffix = ".exe" if os.name == "nt" else ""
    exe_path = final_dir / f"{base_name}{exe_suffix}"
    if exe_path.exists() and os.name != "nt":
        exe_path.chmod(0o755)

    print(f"[OK] Sidecar ({model}) ecrit dans {final_dir}")
    return final_dir


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--triple",
        help="Rust target triple — informatif, non utilisé dans le chemin de sortie.",
    )
    parser.add_argument(
        "--model",
        default="md",
        choices=sorted(KNOWN_MODELS),
        help="Modèle spaCy à bundler (défaut: md). 'sm' pour un bundle ~30 Mo plus léger.",
    )
    parser.add_argument("--clean", action="store_true", help="Wipe dist/ et build/ avant.")
    args = parser.parse_args()

    if args.triple:
        print(f"Cible (info): {args.triple}")
    else:
        try:
            print(f"Cible (info): {rust_triple()}")
        except RuntimeError as exc:
            print(f"(rustc non detecte: {exc})")

    build(model=args.model, clean=args.clean)


if __name__ == "__main__":
    main()
