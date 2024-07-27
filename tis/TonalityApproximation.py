
import logging
from typing import Any, Self

import numpy as np
from tonality.Scale import Scale, TonalFunction
from tonality.Surface import CHORD_VARIANTS, Chord

from typing import Iterable

import numpy as np
import AlgorithmParameters
from tonality.NoteCluster import NoteCluster
from tonality.Scale import ALL_SCALES, Scale
from tonality.Surface import Chord
from tonality.TIS import TIS

logger = logging.getLogger(__name__)

TonalityCost = np.floating[Any] | float | int
# TonalFunction = str

class TonalityApproximation():
    @classmethod
    def Leaf(cls, chord_choices:list[tuple[Chord, TonalityCost]], key_choices:list[tuple[Scale, TonalityCost]]) -> Self:
        ret = cls()
        ret.chord_choices = chord_choices
        ret.key_choices = key_choices
        return ret
    
    def __init__(self) -> None:
        self.cost:TonalityCost = 0
        self.tonal_function:TonalFunction | None = None
        
        # nothing was chosen
        self.chord_choices:list[tuple[Chord, TonalityCost]] = []
        self.key_choices:list[tuple[Scale, TonalityCost]] = []
        
        # chord is chosen
        self.chord:Chord | None = None        
        self.key:Scale | None = None
    
    def choose_chord(self, chord:Chord) -> None:
        self.revert_chord()
        self.chord = chord
        self.cost += self.get_chord_cost(chord)

    def get_chord_cost(self, chord:Chord) -> TonalityCost:
        return max([cost for variant, cost in self.chord_choices if chord == variant])
    
    def get_key_cost(self, key:Scale) -> TonalityCost:
        return max([cost for variant, cost in self.key_choices if key == variant])
        
    def revert_chord(self) -> None:
        if self.chord is None:
            return
        self.cost -= self.get_chord_cost(self.chord)
        self.chord = None
    
    def choose_key(self, key:Scale) -> None:
        self.revert_key()        
        self.key = key
        self.cost += self.get_key_cost(key)
    
    def revert_key(self) -> None:
        if self.key is None:
            return
        self.cost -= self.get_key_cost(self.key)
        self.key = None
        
    def __str__(self) -> str:
        chord_str = f'({' '.join([f'{chord}:{round(cost, 2)}' for chord, cost in self.chord_choices])})'        
        key_str = f'({' '.join([f'{key}:{round(cost, 2)}' for key, cost in self.key_choices])})'        
        return f'{chord_str} / {key_str}'
    
    def __repr__(self) -> str:
        return self.__str__()

    def most_likely_key(self) -> Scale:
        return self.key_choices[0][0]

    def most_likely_chord(self) -> Chord:
        return self.chord_choices[0][0]
    
def approximate_tonality(clusters: list[NoteCluster]) -> Iterable[TonalityApproximation]:
    for i in range(len(clusters)):
        if len(clusters[i]) == 0:
            continue
        chords_dict:dict[Chord, TonalityCost] = {}
        for chord, variant in CHORD_VARIANTS:            
            chords_dict[chord] = max(chords_dict.get(chord, 0), 1 - TIS.angular(variant, clusters[i]))
        chords:list[tuple[Chord, TonalityCost]] = list(chords_dict.items())
        chords.sort(key=lambda pair: pair[1], reverse=True)        
        min_cost = chords[AlgorithmParameters.CHORD_CHOICE_DEPTH+1][1] if AlgorithmParameters.CHORD_CHOICE_DEPTH+1 < len(chords) else 0
        chords = chords[:AlgorithmParameters.CHORD_CHOICE_DEPTH]        
        chords = list(map(lambda pair: (pair[0], (pair[1] - min_cost) / (1 - min_cost)), chords))
     
        from_id = max(i - AlgorithmParameters.SCALE_APPROXIMATION_BACKWARDS_LOOKUP, 0)
        to_id = from_id + AlgorithmParameters.SCALE_APPROXIMATION_WINDOW_SIZE
        scale_cluster = sum(clusters[from_id+1:to_id], start=clusters[from_id])
        scales:list[tuple[Scale, TonalityCost]] = [(scale, 1 - TIS.angular(scale, scale_cluster)) for scale in ALL_SCALES.values()]
        scales.sort(key=lambda pair: pair[1], reverse=True)
        yield TonalityApproximation.Leaf(chords, scales)