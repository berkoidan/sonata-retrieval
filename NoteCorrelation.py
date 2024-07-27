import logging
from typing import Any, Callable

import numpy as np
from tis.TIS import TIS
from tis.NoteCluster import NoteCluster, sum_clusters

logger = logging.getLogger(__name__)

def correlation(right:NoteCluster, 
                clusters:list[NoteCluster], 
                metric: Callable[[NoteCluster, NoteCluster], np.floating[Any]], 
                windowSize:int=1) -> None:
    left:NoteCluster = sum_clusters(clusters[:windowSize])
    for i in range(windowSize, len(clusters) + 1):
        if len(left) == 0:
            continue

        logger.info(f"{right} ({round(TIS.norm(right))}) <-> {left} ({round(TIS.norm(left))}):\t{metric(right, left)}")

        if i >= len(clusters):
            continue
        
        left += clusters[i]
        left -= clusters[i - windowSize]
