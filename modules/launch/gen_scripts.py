"""Pasos 4+5: Generación de lancement.sh y master.job."""

import logging
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


def _build_lancement_sh(cfg: dict, paths: list[str]) -> str:
    """Genera el contenido de lancement.sh a partir de la config y los paths.

    Args:
        cfg: Configuración cargada desde pipeline_launch.yaml.
        paths: Lista de paths *_calcul obtenida en el Paso 3.

    Returns:
        Contenido completo del script bash como string.
    """
    omp = cfg["launch"]["omp"]
    steps = cfg["launch"]["steps"]

    lines = ["#!/bin/bash", "", "PATHS=("]
    for p in paths:
        lines.append(f"  {p}")
    lines += [")", "", "cd ${PATHS[$SLURM_ARRAY_TASK_ID]}", ""]

    for step in steps:
        tag = step["tag"]
        jdd = step["jdd"]
        postpro = step.get("postpro")

        lines.append(f"# {tag}")

        if omp is not None:
            lines.append(f"./cathar.unix {jdd} omp {omp}")
        else:
            lines.append(f"./cathar.unix {jdd}")

        if postpro:
            if omp is not None:
                lines.append(f"./postpro.unix {postpro} omp {omp}")
            else:
                lines.append(f"./postpro.unix {postpro}")
            lines.append(f"mkdir -p evol_{tag}")
            lines.append(f"mv *.evol evol_{tag}/")

        lines.append("")

    return "\n".join(lines)


def _build_master_job(cfg: dict, paths: list[str]) -> str:
    """Genera el contenido de master.job a partir de la config y los paths.

    Args:
        cfg: Configuración cargada desde pipeline_launch.yaml.
        paths: Lista de paths *_calcul para calcular el array size.

    Returns:
        Contenido completo del job script SLURM como string.
    """
    slurm = cfg["launch"]["slurm"]
    base_path = cfg["remote"]["base_path"]
    n = len(paths) - 1

    lines = [
        "#!/bin/bash",
        f"#SBATCH --job-name={slurm['job_name']}",
        f"#SBATCH --array=0-{n}",
        f"#SBATCH --ntasks={slurm['ntasks']}",
        f"#SBATCH --time={slurm['time']}",
        f"#SBATCH --output={slurm['output']}",
        f"#SBATCH --partition={slurm['partition']}",
        "",
        f"bash {base_path}/lancement.sh $SLURM_ARRAY_TASK_ID",
    ]
    return "\n".join(lines)


def gen_scripts(
    cfg: dict, paths: list[str], dry_run: bool = False
) -> tuple[Path, Path]:
    """Genera lancement.sh y master.job en un directorio temporal.

    Args:
        cfg: Configuración cargada desde pipeline_launch.yaml.
        paths: Lista de paths *_calcul obtenida en el Paso 3.
        dry_run: Si True, imprime los scripts en consola sin escribirlos a disco.

    Returns:
        Tupla (path_lancement_sh, path_master_job) con las rutas locales temporales.
    """
    lancement_content = _build_lancement_sh(cfg, paths)
    master_content = _build_master_job(cfg, paths)

    if dry_run:
        logger.info("[DRY RUN] Paso 4+5 - lancement.sh generado:")
        for line in lancement_content.splitlines():
            logger.info(f"  {line}")
        logger.info("[DRY RUN] Paso 4+5 - master.job generado:")
        for line in master_content.splitlines():
            logger.info(f"  {line}")
        dry_tmp = Path(tempfile.gettempdir()) / "pipeline_launch_dry_run"
        return dry_tmp / "lancement.sh", dry_tmp / "master.job"

    tmpdir = Path(tempfile.mkdtemp(prefix="pipeline_launch_"))
    lancement_path = tmpdir / "lancement.sh"
    master_path = tmpdir / "master.job"

    lancement_path.write_text(lancement_content, encoding="utf-8")
    master_path.write_text(master_content, encoding="utf-8")

    logger.info(f"Paso 4+5 completado — scripts generados en {tmpdir}")
    return lancement_path, master_path
