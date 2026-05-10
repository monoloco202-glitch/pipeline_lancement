"""Paso 1: Sincronización del directorio local → remoto via rsync."""

import logging
import subprocess

logger = logging.getLogger(__name__)


def rsync(cfg: dict, dry_run: bool = False) -> None:
    """Sincroniza local_workdir/ con base_path/workdir/ en el remoto.

    Args:
        cfg: Configuración cargada desde pipeline_launch.yaml.
        dry_run: Si True, imprime el comando sin ejecutarlo.
    """
    local_workdir = cfg["project"]["local_workdir"]
    ssh = cfg["remote"]["ssh"]
    base_path = cfg["remote"]["base_path"]
    workdir = cfg["remote"]["workdir"]

    src = f"{local_workdir}/"
    dst = f"{ssh}:{base_path}/{workdir}/"
    cmd = ["rsync", "-av", src, dst]

    if dry_run:
        logger.info(f"[DRY RUN] Paso 1 - rsync: {' '.join(cmd)}")
        return

    logger.info(f"Paso 1 - rsync {src} → {dst}")
    subprocess.run(cmd, check=True)
    logger.info("Paso 1 completado")
