import numpy as np
from typing import Any, Self, cast

from tis.NoteCluster import ChromaVector, Note, NoteCluster

FFTChroma = np.ndarray[Any, np.dtype[np.complexfloating[Any, Any]]]

class TISPoint():
    @staticmethod
    def _normal_fft(chroma: ChromaVector) -> FFTChroma:
        W = [2, 11, 17, 16, 19, 7]
        mod_c = max(sum(chroma), 1)
        T = np.fft.fft(chroma)[1:7]
        return (T * W) / mod_c

    @classmethod
    def from_cluster(cls, note_cluster:NoteCluster) -> Self:
        return cls.from_chroma(note_cluster.chroma())
    
    @classmethod
    def from_chroma(cls, chroma: ChromaVector) -> Self:
        return cls(TISPoint._normal_fft(chroma))

    def __init__(self, complex:FFTChroma) -> None:
        self.complex = complex    
    
    def __sub__(self, other : Self) -> Self:
        new_val = np.subtract(self.complex, other.complex)
        return type(self)(new_val)
    
    def __abs__(self) -> np.floating[Any]:
        return np.linalg.norm(self.complex)
    
    def __mul__(self, other : Self) -> np.floating[Any]:        
        return cast(np.floating[Any], np.real(np.sum(self.complex * np.conjugate(other.complex))))        
    
    def __str__(self) -> str:
        return str(self.complex)
    
    def __matmul__(self, other: Self) -> np.floating[Any]:
        # real and clip are to avoid inaccuracies        
        assert abs(self) > 0
        assert abs(other) > 0
        cos = self * other / (abs(self) * abs(other))
        return cast(np.floating[Any], np.arccos(np.clip(cos, -1, 1)))

class TIS():
    @staticmethod
    def dissonance(chord : NoteCluster) -> np.floating[Any]:
        max_dissonance = abs(TISPoint.from_chroma([0] * Note.NOTE_LEN))
        distance = abs(TISPoint.from_cluster(chord))
        value = distance / max_dissonance
        return 1 - value
    
    @staticmethod
    def euclid(c1 : NoteCluster, c2 : NoteCluster) -> np.floating[Any]:
        return abs(TISPoint.from_cluster(c1) - TISPoint.from_cluster(c2))
    
    @staticmethod
    def angular(c1 : NoteCluster, c2 : NoteCluster) -> np.floating[Any]:
        value = TISPoint.from_cluster(c1) @ TISPoint.from_cluster(c2)
        return value / np.pi
    
    @staticmethod
    def radial(c1 : NoteCluster, c2 : NoteCluster) -> np.floating[Any]:
        return abs(TIS.norm(c1) - TIS.norm(c2))
    
    @staticmethod
    def norm(nc : NoteCluster) -> np.floating[Any]:
        return abs(TISPoint.from_cluster(nc))
        