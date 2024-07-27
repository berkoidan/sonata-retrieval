import logging
from tis.TIS import TIS
from tis.NoteCluster import NoteCluster, sum_clusters

logger = logging.getLogger(__name__)

def correlation(right:NoteCluster, clusters:list[NoteCluster], windowSize:int=1) -> None:
    left = sum_clusters(clusters[:windowSize])
    for i in range(windowSize-1, len(clusters) + 1):

        euclid = TIS.euclid(right, left)
        angular = TIS.angular(right, left)
        radial = TIS.radial(right, left)
        logger.info(f"{right} ({TIS.norm(right)}) <-> {left} ({TIS.norm(left)}): {radial} {euclid}, {angular}")

        if i >= len(clusters):
            continue

        left.sub(clusters[i - windowSize])
        left.add(clusters[i])
    pass