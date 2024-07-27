import logging
from typing import Any, Callable, Iterator

import numpy as np
from tis.TIS import TIS
from tis.NoteCluster import NoteCluster, sum_clusters

logger = logging.getLogger(__name__)

def cluster_windows(clusters:list[NoteCluster], windowSize:int) -> Iterator[NoteCluster]:
    window = sum_clusters(clusters[:windowSize])    
    for i in range(windowSize, len(clusters)):
        yield window
        window += clusters[i]
        window -= clusters[i - windowSize]


def correlation(right:NoteCluster, 
                clusters:list[NoteCluster], 
                metric: Callable[[NoteCluster, NoteCluster], np.floating[Any]], 
                windowSize:int=1) -> None:    
    for left in cluster_windows(clusters, windowSize):    
        if len(left) == 0:
            continue

        logger.info(f"{right} ({round(TIS.norm(right))}) <-> {left} ({round(TIS.norm(left))}):\t{metric(right, left)}")
