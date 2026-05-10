"""Paso 2: Ejecución remota de generation_sensi.sh via SSH."""

import logging
import subprocess

logger = logging.getLogger(__name__)


def remote_setup(cfg: dict, dry_run: bool = False) -> None:
    """Ejecuta generation_sensi.sh en el servidor remoto.

    El script ya existe en base_path/ y se encarga de copiar workdir/
    en cada *_calcul/ y aplicar las modificaciones de sensibilidad.

    Args:
        cfg: Configuración cargada desde pipeline_launch.yaml.
        dry_run: Si True, imprime el comando SSH sin ejecutarlo.
    """
    ssh = cfg["remote"]["ssh"]
    base_path = cfg["remote"]["base_path"]
    script = cfg["launch"]["generation_script"]

    remote_cmd = f"cd {base_path} && bash {script}"
    cmd = ["ssh", ssh, remote_cmd]

    if dry_run:
        logger.info(f"[DRY RUN] Paso 2 - SSH: {' '.join(cmd)}")
        return

    logger.info(f"Paso 2 - Ejecutando {script} en {ssh}:{base_path}")
    subprocess.run(cmd, check=True)
    logger.info("Paso 2 completado")
