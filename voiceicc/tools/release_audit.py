from pathlib import Path
import ast, json, hashlib, sys
from datetime import datetime

root = Path(__file__).resolve().parents[1]
source = root / "src" / "modulador_voz_premium_v1_3.py"
required = [
    root / "README.md", root / "GUIA_RAPIDA.md", root / "PRIVACIDAD.md",
    root / "CHECKLIST_PUBLICACION.md", root / "requirements.txt",
    root / "crear_exe.bat", root / "crear_instalador_windows.bat",
    root / "assets" / "app_icon.ico", root / "assets" / "fx_mixer_audio" / "prism_confirm.mp3", source,
]
report = {
    "product": "Modulador de Voz Premium",
    "version": "1.3.0 Voice Studio & Smart FX",
    "generated_at": datetime.now().isoformat(timespec="seconds"),
    "source": str(source.relative_to(root)),
    "missing_files": [str(p.relative_to(root)) for p in required if not p.exists()],
}
try:
    text = source.read_text(encoding="utf-8")
    tree = ast.parse(text)
    report["python_ast"] = "passed"
    release_tabs = None
    release_sections = None
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "PremiumApp":
            for item in node.body:
                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name) and target.id == "RELEASE_TABS":
                            release_tabs = ast.literal_eval(item.value)
                        if isinstance(target, ast.Name) and target.id == "RELEASE_SECTIONS":
                            release_sections = ast.literal_eval(item.value)
    report["published_modules"] = len(release_tabs or [])
    report["published_sections"] = len(release_sections or [])
    report["contains_runtime_audit"] = "def release_quality_audit" in text
    report["contains_release_asset_loader"] = "def _load_release_png_folder" in text
except Exception as exc:
    report["python_ast"] = f"failed: {exc}"

report["status"] = "PASS" if (
    not report["missing_files"]
    and report.get("python_ast") == "passed"
    and report.get("published_modules") == 33
    and report.get("published_sections") == 6
) else "FAIL"
path = root / "RELEASE_AUDIT.json"
path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
sys.exit(0 if report["status"] == "PASS" else 1)
