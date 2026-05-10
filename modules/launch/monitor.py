"""Paso 7: Monitoreo del array SLURM hasta la finalización de todos los tasks."""

import logging
import subprocess
import time

logger = logging.getLogger(__name__)

_CHECK_INTERVAL = 60
_FAILED_STATES = {"FAILED", "CANCELLED", "TIMEOUT", "NODE_FAIL"}
_DRY_RUN_CHECKS = 3


def monitor(cfg: dict, job_id: str, dry_run: bool = False) -> None:
    """Monitorea el job SLURM hasta que todos los tasks del array terminen.

    Consulta squeue cada 60 segundos. Termina cuando no hay tasks activos.

    Args:
        cfg: Configuración cargada desde pipeline_launch.yaml.
        job_id: ID del job SLURM devuelto por sbatch.
        dry_run: Si True, simula 3 checks con estado ficticio y termina.

    Raises:
        RuntimeError: Si algún task termina en estado fallido.
    """
    ssh = cfg["remote"]["ssh"]

    if dry_run:
        logger.info(f"[DRY RUN] Paso 7 - Monitoreando JOB_ID: {job_id}")
        for i in range(1, _DRY_RUN_CHECKS + 1):
            logger.info(f"[DRY RUN] Check {i}/{_DRY_RUN_CHECKS}:")
            logger.info(f"  {job_id}_0  RUNNING")
            logger.info(f"  {job_id}_1  RUNNING")
            logger.info(f"  {job_id}_2  PENDING")
            time.sleep(1)
        logger.info("[DRY RUN] Simulación de monitoreo completada")
        return

    logger.info(f"Paso 7 - Monitoreando JOB_ID: {job_id}")

    while True:
        result = subprocess.run(
            ["ssh", ssh, f"squeue --job {job_id} --format='%i %T' --noheader"],
            check=True,
            capture_output=True,
            text=True,
        )

        lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]

        if not lines:
            logger.info("Todos los tasks han finalizado")
            break

        logger.info(f"Estado actual ({len(lines)} tasks activos):")
        failed = []
        for line in lines:
            parts = line.split()
            task_id = parts[0]
            state = parts[1] if len(parts) > 1 else "UNKNOWN"
            logger.info(f"  {task_id}  {state}")
            if state in _FAILED_STATES:
                failed.append(task_id)

        if failed:
            raise RuntimeError(f"Tasks fallidos: {', '.join(failed)}")

        time.sleep(_CHECK_INTERVAL)

    logger.info("Paso 7 completado")
