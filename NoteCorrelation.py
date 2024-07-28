import logging
from typing import Any, Callable, Iterator

import numpy as np
from tis.TIS import TIS, Float
from tis.NoteCluster import NoteCluster, sum_clusters

logger = logging.getLogger(__name__)

def cluster_windows(clusters:list[NoteCluster], windowSize:int) -> Iterator[NoteCluster]:
    window = sum_clusters(clusters[:windowSize])    
    for i in range(windowSize, len(clusters)):
        yield window
        window += clusters[i]
        window -= clusters[i - windowSize]


def correlation(clusters:list[NoteCluster], 
                metric: Callable[[NoteCluster, NoteCluster], Float], 
                windowSize:int) -> np.ndarray[Any, np.dtype[Float]]:
    results = np.zeros((len(clusters), len(clusters)))
    clusters = list(cluster_windows(clusters, windowSize))
    for start in range(len(clusters)):
        logger.debug(f'Start at {start}')
        for offset in range(len(clusters) - start):
            right = clusters[start + offset]
            left = clusters[offset]
            if len(right) == 0 or len(left) == 0:
                continue
            distance = metric(right, left)
            logger.info(f"{right} ({round(TIS.norm(right))}) <-> {left} ({round(TIS.norm(left))}):\t{distance}")
            results[offset][start + offset] = distance
    return results

def draw_hitmap(data: np.ndarray[Any, np.dtype[Float]]) -> None:
    import matplotlib.pyplot as plt
    plt.imshow(data, cmap='coolwarm', interpolation='nearest', origin='lower')
    plt.show()
            
