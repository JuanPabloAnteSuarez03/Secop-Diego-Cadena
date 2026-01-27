"""
Genera un .ico multi-resolución para Windows a partir del logo de UniValle.

Uso (desde la raíz del repo):
  python -m src.scripts.make_app_icon

Salida:
  - src/ui/assets/app.ico        (para PyQt y PyInstaller --icon)
  - installer/app.ico            (para Inno Setup SetupIconFile)
"""

from __future__ import annotations

from pathlib import Path


def main() -> None:
    try:
        from PIL import Image
    except Exception as e:  # pragma: no cover
        raise SystemExit(
            "Pillow no está instalado. Activa tu venv y ejecuta: pip install pillow\n"
            f"Detalle: {e}"
        )

    repo_root = Path(__file__).resolve().parents[2]

    # Preferimos el logo ya copiado a assets (más estable)
    src_png = repo_root / "src" / "ui" / "assets" / "logo_univalle.png"
    if not src_png.exists():
        src_png = (
            repo_root
            / "universidad-del-valle-vector-logo-seeklogo"
            / "universidad-del-valle-seeklogo.png"
        )

    if not src_png.exists():
        raise SystemExit(f"No se encontró el PNG del logo. Busqué en: {src_png}")

    out_app_ico = repo_root / "src" / "ui" / "assets" / "app.ico"
    out_installer_ico = repo_root / "installer" / "app.ico"
    out_app_ico.parent.mkdir(parents=True, exist_ok=True)
    out_installer_ico.parent.mkdir(parents=True, exist_ok=True)

    img = Image.open(src_png).convert("RGBA")

    # Tamaños comunes para iconos Windows
    sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(out_app_ico, sizes=sizes)

    # Copiar el mismo icono para el instalador
    out_installer_ico.write_bytes(out_app_ico.read_bytes())

    print(f"OK: {out_app_ico}")
    print(f"OK: {out_installer_ico}")


if __name__ == "__main__":
    main()


