#!/usr/bin/env python3
"""
Pipeline de lanzamiento de cálculos CATHARE en HPC remoto (SLURM).
Orquestador principal pilotado por pipeline_launch.yaml.
"""

import argparse
import logging
import sys
from pathlib import Path

import yaml

from modules.launch.rsync import rsync
from modules.launch.remote_setup import remote_setup
from modules.launch.find_calcul import find_calcul
from modules.launch.gen_scripts import gen_scripts
from modules.launch.sbatch import sbatch
from modules.launch.monitor import monitor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s - %(message)s",
)
logger = logging.getLogger("pipeline_launch")


def parse_args() -> argparse.Namespace:
    """Parsea los argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(
        description="Pipeline de lanzamiento CATHARE/SLURM"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simula todos los pasos sin ejecutar comandos reales",
    )
    return parser.parse_args()


def load_config(path: Path) -> dict:
    """Carga y devuelve la configuración desde el YAML.

    Args:
        path: Ruta al fichero pipeline_launch.yaml.

    Raises:
        FileNotFoundError: Si el fichero no existe.
    """
    if not path.exists():
        raise FileNotFoundError(f"Fichero de configuración no encontrado: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate_workdir(cfg: dict) -> None:
    """Verifica que el pipeline se lanza desde el directorio correcto.

    Args:
        cfg: Configuración cargada desde pipeline_launch.yaml.

    Raises:
        RuntimeError: Si el directorio actual no coincide con local_workdir.
    """
    expected = cfg["project"]["local_workdir"]
    actual = Path.cwd().name
    if actual != expected:
        raise RuntimeError(
            f"El pipeline debe ejecutarse desde '{expected}/' (actual: '{actual}/')"
        )


def main() -> None:
    """Punto de entrada del orquestador."""
    args = parse_args()

    config_path = Path(__file__).parent / "pipeline_launch.yaml"
    cfg = load_config(config_path)
    validate_workdir(cfg)

    if args.dry_run:
        logger.info("[DRY RUN] Modo simulación activado — ningún comando real se ejecutará")

    rsync(cfg, dry_run=args.dry_run)
    remote_setup(cfg, dry_run=args.dry_run)
    paths = find_calcul(cfg, dry_run=args.dry_run)
    lancement_sh, master_job = gen_scripts(cfg, paths, dry_run=args.dry_run)
    job_id = sbatch(cfg, lancement_sh, master_job, dry_run=args.dry_run)
    monitor(cfg, job_id, dry_run=args.dry_run)

    logger.info("✅ PIPELINE TERMINADO CON ÉXITO")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("\n⛔ Interrupción del usuario")
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}")
        sys.exit(1)
