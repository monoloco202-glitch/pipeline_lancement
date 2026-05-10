"""Paso 6: Subida de scripts via SCP y lanzamiento via sbatch."""

import logging
import re
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

_DRY_RUN_JOB_ID = "DRY_RUN_JOB"


def sbatch(
    cfg: dict,
    lancement_sh: Path,
    master_job: Path,
    dry_run: bool = False,
) -> str:
    """Sube lancement.sh y master.job al remoto y lanza sbatch.

    Args:
        cfg: Configuración cargada desde pipeline_launch.yaml.
        lancement_sh: Path local al archivo lancement.sh generado.
        master_job: Path local al archivo master.job generado.
        dry_run: Si True, imprime los comandos sin ejecutarlos.

    Returns:
        JOB_ID asignado por sbatch (string numérico).

    Raises:
        RuntimeError: Si sbatch no devuelve un JOB_ID reconocible.
    """
    ssh = cfg["remote"]["ssh"]
    base_path = cfg["remote"]["base_path"]

    scp_lancement = ["scp", str(lancement_sh), f"{ssh}:{base_path}/lancement.sh"]
    scp_master = ["scp", str(master_job), f"{ssh}:{base_path}/master.job"]
    sbatch_cmd = ["ssh", ssh, f"cd {base_path} && sbatch master.job"]

    if dry_run:
        logger.info(f"[DRY RUN] Paso 6 - SCP lancement.sh: {' '.join(scp_lancement)}")
        logger.info(f"[DRY RUN] Paso 6 - SCP master.job:   {' '.join(scp_master)}")
        logger.info(f"[DRY RUN] Paso 6 - sbatch:           {' '.join(sbatch_cmd)}")
        logger.info(f"[DRY RUN] JOB_ID simulado: {_DRY_RUN_JOB_ID}")
        return _DRY_RUN_JOB_ID

    logger.info("Paso 6 - Subiendo scripts al remoto")
    subprocess.run(scp_lancement, check=True)
    subprocess.run(scp_master, check=True)

    logger.info("Paso 6 - Lanzando sbatch")
    result = subprocess.run(sbatch_cmd, check=True, capture_output=True, text=True)

    # sbatch stdout: "Submitted batch job 12345"
    match = re.search(r"Submitted batch job (\d+)", result.stdout)
    if not match:
        raise RuntimeError(
            f"No se pudo extraer JOB_ID del output de sbatch: {result.stdout!r}"
        )

    job_id = match.group(1)
    logger.info(f"Paso 6 completado — JOB_ID: {job_id}")
    return job_id
