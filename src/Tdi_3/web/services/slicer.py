import os
import subprocess
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from dotenv import load_dotenv

from .storage import OUT_DIR

_MODULE_DIR = Path(__file__).resolve()
_CONFIG_DIR = _MODULE_DIR.parents[2] / "config" / "slicer_profiles"
_DOT_ENV = _CONFIG_DIR / ".env"
load_dotenv(_DOT_ENV) if _DOT_ENV.exists() else load_dotenv()

PRUSASLICER = os.getenv(
    "PRUSASLICER_EXE",
    r"C:\Program Files\Prusa3D\PrusaSlicer\prusaslicer-console.exe",
)
PRUSA_PROFILE = os.getenv(
    "PRUSASLICER_PROFILE",
    str(_CONFIG_DIR / "prusaslicer_0.2mm.ini"),
)

CURA_ENGINE = os.getenv(
    "CURA_ENGINE_EXE",
    r"C:\Program Files\UltiMaker Cura 5.10.1\CuraEngine.exe",
)
CURA_DEF = os.getenv(
    "CURA_ENGINE_DEF",
    r"C:\Program Files\UltiMaker Cura 5.10.1\share\cura\resources\definitions\fdmprinter.def.json",
)
CURA_SEARCH_PATH = os.getenv(
    "CURA_ENGINE_SEARCH_PATH",
    r"C:\Program Files\UltiMaker Cura 5.10.1\share\cura\resources",
)
CURA_RESOLVED_SETTINGS = os.getenv("CURA_ENGINE_RESOLVED")
CURA_EXTRA_SETTINGS = os.getenv("CURA_ENGINE_EXTRA_SETTINGS", "")

DEFAULT_CURA_SETTINGS: Dict[str, Optional[str]] = {
    "layer_height": os.getenv("CURA_LAYER_HEIGHT", "0.2"),
    "wall_line_count": os.getenv("CURA_WALL_LINE_COUNT", "2"),
    "top_bottom_thickness": os.getenv("CURA_TOP_BOTTOM_THICKNESS", "0.8"),
    "infill_sparse_density": os.getenv("CURA_INFILL_DENSITY", "15"),
    "material_print_temperature": os.getenv("CURA_PRINT_TEMP", "200"),
    "material_bed_temperature": os.getenv("CURA_BED_TEMP", "60"),
    "speed_print": os.getenv("CURA_PRINT_SPEED", "50"),
}


def _parse_extra_settings(raw: str) -> Dict[str, str]:
    data: Dict[str, str] = {}
    for chunk in raw.split(","):
        pair = chunk.strip()
        if not pair or "=" not in pair:
            continue
        key, value = pair.split("=", 1)
        key = key.strip()
        value = value.strip()
        if key and value:
            data[key] = value
    return data


def _build_cura_command(
    input_model_path: str, out_path: str
) -> Optional[Tuple[List[str], Optional[Dict[str, str]]]]:
    if not os.path.exists(CURA_ENGINE):
        return None
    if not os.path.exists(CURA_DEF):
        raise FileNotFoundError(
            f"Arquivo de definição do Cura não encontrado: {CURA_DEF}"
        )

    settings: Dict[str, str] = {
        key: value for key, value in DEFAULT_CURA_SETTINGS.items() if value
    }
    settings.update(_parse_extra_settings(CURA_EXTRA_SETTINGS))

    cmd: List[str] = [
        CURA_ENGINE,
        "slice",
        "-j",
        CURA_DEF,
        "-l",
        input_model_path,
        "-o",
        out_path,
    ]

    if CURA_RESOLVED_SETTINGS and os.path.exists(CURA_RESOLVED_SETTINGS):
        cmd.extend(["-r", CURA_RESOLVED_SETTINGS])

    for key, value in settings.items():
        cmd.extend(["-s", f"{key}={value}"])

    env = os.environ.copy()
    if CURA_SEARCH_PATH and "CURA_ENGINE_SEARCH_PATH" not in env:
        env["CURA_ENGINE_SEARCH_PATH"] = CURA_SEARCH_PATH

    return cmd, env


def _build_prusa_command(
    input_model_path: str, out_path: str
) -> Optional[Tuple[List[str], Optional[Dict[str, str]]]]:
    if not os.path.exists(PRUSASLICER):
        return None

    cmd: List[str] = [PRUSASLICER, "--export-gcode", input_model_path, "--output", out_path]
    if os.path.exists(PRUSA_PROFILE):
        cmd = [
            PRUSASLICER,
            "--load",
            PRUSA_PROFILE,
            "--export-gcode",
            input_model_path,
            "--output",
            out_path,
        ]
    return cmd, None


def _run_command(cmd: List[str], env: Optional[Dict[str, str]] = None):
    proc = subprocess.run(
        cmd, capture_output=True, text=True, env=env or os.environ.copy()
    )
    if proc.returncode != 0:
        raise RuntimeError(
            "Erro ao fatiar: "
            f"retorno {proc.returncode}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}\n"
            f"Comando: {' '.join(cmd)}"
        )


def slice_model(input_model_path: str) -> str:
    if not os.path.exists(input_model_path):
        raise FileNotFoundError(f"Modelo não encontrado: {input_model_path}")

    out = os.path.join(OUT_DIR, f"{uuid.uuid4().hex}.gcode")

    builders = [_build_cura_command, _build_prusa_command]
    for builder in builders:
        result = builder(input_model_path, out)
        if not result:
            continue
        cmd, env = result
        _run_command(cmd, env)
        return out

    raise FileNotFoundError(
        "Nenhum slicer CLI encontrado. Configure CURA_ENGINE_EXE ou PRUSASLICER_EXE no .env."
    )
