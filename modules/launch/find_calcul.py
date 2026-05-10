"""Paso 3: Búsqueda de los directorios de cálculo en el remoto."""

import logging
import subprocess

logger = logging.getLogger(__name__)


def find_calcul(cfg: dict, dry_run: bool = False) -> list[str]:
    """Localiza los directorios que contienen los ficheros jdd dentro de *_calcul/.

    Usa el primer jdd de los steps como fichero de referencia y devuelve
    los directorios padre via -printf '%h\\n'. Esos directorios son donde
    CATHARE debe ejecutarse (cd + ./cathar.unix).

    Ejemplo de estructura esperada tras generation_sensi.sh:
        base_path/
          sensib1_calcul/
            PASO1.dat   ← jdd de referencia
            PASO2.dat
            cathar.unix
          sensib2_calcul/
            PASO1.dat
            ...

    Args:
        cfg: Configuración cargada desde pipeline_launch.yaml.
        dry_run: Si True, devuelve paths simulados sin ejecutar SSH.

    Returns:
        Lista ordenada de paths absolutos a los directorios de cálculo.
    """
    ssh = cfg["remote"]["ssh"]
    base_path = cfg["remote"]["base_path"]
    calculdir = cfg["remote"]["calculdir"]
    first_jdd = cfg["launch"]["steps"][0]["jdd"]

    # -printf '%h\n' devuelve el directorio padre de cada fichero encontrado
    remote_cmd = (
        f"cd {base_path} && "
        f"find {calculdir} -name '{first_jdd}' -printf '%h\\n'"
    )
    cmd = ["ssh", ssh, remote_cmd]

    if dry_run:
        simulated = [
            f"{base_path}/sensib1_calcul",
            f"{base_path}/sensib2_calcul",
            f"{base_path}/sensib3_calcul",
        ]
        logger.info(f"[DRY RUN] Paso 3 - find: {' '.join(cmd)}")
        logger.info("[DRY RUN] Paths simulados:")
        for p in simulated:
            logger.info(f"  {p}")
        return simulated

    logger.info(f"Paso 3 - buscando '{first_jdd}' en {ssh}:{base_path}/{calculdir}")
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    paths = sorted(
        f"{base_path}/{p.strip()}"
        for p in result.stdout.splitlines()
        if p.strip()
    )
    logger.info(f"Paso 3 completado — {len(paths)} directorios encontrados")
    return paths
