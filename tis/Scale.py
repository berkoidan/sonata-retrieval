import logging
from tonality.NoteCluster import Note, NoteCluster, all_notes
import AlgorithmParameters
from tonality.Surface import Chord, ChordTypes

logger = logging.getLogger(__name__)

class TonalFunctions():
    TONIC_FUNC = 't'
    DOMINANT_FUNC = 'd'
    SUBDOMINANT_FUNC = 's'
    
    TONIC_PARALLEL_FUNC = 'tp'
    TONIC_COUNTER_PARALLEL_FUNC = 'tcp'
    DOMINANT_PARALLEL_FUNC = 'dp'
    SUBDOMINANT_PARALLEL_FUNC = 'sp'
    
    DOMINANT_DEGREE = 'D5'
    DIMINSHED_DEGREE = 'D7'
    DIATONIC_DOMINANT_DEGREE = '^'

class TonalFunction():
    def __init__(self, name:str):
        self.name = name
        self.parallel = False
    
    def __hash__(self) -> int:
        return hash(self.name)
    
    def __eq__(self, value: object) -> bool:
        if isinstance(value, TonalFunction):
            return self.name == value.name
        if isinstance(value, str):
            return self.name == value
        return NotImplemented
    
    def __ne__(self, value: object) -> bool:
        return not self.__eq__(value)
    
    def __str__(self) -> str:
        return self.name + ('*' if self.parallel else '')
    
    def __repr__(self) -> str:
        return self.__str__()
    
    def is_subdominant(self) -> bool:
        return self.name in (TonalFunctions.SUBDOMINANT_FUNC, TonalFunctions.SUBDOMINANT_PARALLEL_FUNC)

class Scale(NoteCluster):
    def __init__(self, note:Note, pattern:list[int], mode:str) -> None:
        super().__init__()
        self.bass_note = note
        self.pattern = pattern
        self.mode = mode
        self.name = str(note) + mode
        for semitones in all_notes():
            super().add_note(self.bass_note + semitones, self.pattern[semitones.note])
        
    def __str__(self) -> str:
        return self.name
    
    def __repr__(self) -> str:
        return self.name
    
    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Scale):
            return super().__eq__(value)
        return value.name == self.name
    
    def __hash__(self) -> int:
        return hash(self.name)
    
    def tonic(self) -> Chord:
        return self._pure_degree(0)
    
    def dominant(self) -> Chord:
        return self._pure_degree(7)
    
    def subdominant(self) -> Chord:
        return self._pure_degree(5)
        
    def _pure_degree(self, semitones:int) -> Chord:
        mode = ChordTypes.MAJOR if self.mode == ScaleTypes.MAJOR else ChordTypes.MINOR
        return Chord.get(self.bass_note + semitones, mode)
    
    def diatonic_dominant(self, chord:Chord) -> Chord | None:
        semitones = chord.bass_note - self.bass_note
        degree_mode = DEGREES_MODES[self.mode][semitones.note]
        if degree_mode == None or degree_mode != chord.mode:
            return None
        degree = DEGREES_SEMITONES[self.mode].index(semitones.note)
        dominant_degree = (degree + 4) % len(DEGREES_SEMITONES[self.mode])
        dominant_semitones = DEGREES_SEMITONES[self.mode][dominant_degree]
        dominant_mode = DEGREES_MODES[self.mode][dominant_semitones]
        assert dominant_mode is not None
        return Chord.get(self.bass_note + dominant_semitones, dominant_mode)
        
    def get_function(self, chord:Chord) -> TonalFunction | None:
        function = self._get_function(chord)
        if function is not None:
            return function
        
        function = self.parallel()._get_function(chord)
        if function is None:
            return None
        function.parallel = True
        return function

    def parallel(self):
        mode = ScaleTypes.MINOR if self.mode == ScaleTypes.MAJOR else ScaleTypes.MAJOR
        parllel = ALL_SCALES[(self.bass_note, mode)]
        return parllel
    
    def _get_function(self, chord:Chord) -> TonalFunction | None:
        semitones = chord.bass_note - self.bass_note
        
        if(self.mode == ScaleTypes.MINOR and semitones == 1 and chord.mode == ChordTypes.MAJOR):
            return TonalFunction(TonalFunctions.SUBDOMINANT_PARALLEL_FUNC)
        
        if(semitones.note not in DEGREES_SEMITONES[self.mode]):
            return None
        
        degree = DEGREES_SEMITONES[self.mode].index(semitones.note)
        degree_mode = DEGREES_MODES[self.mode][semitones.note]
        
        major = [TonalFunctions.TONIC_FUNC, 
                 TonalFunctions.SUBDOMINANT_PARALLEL_FUNC, 
                 TonalFunctions.TONIC_COUNTER_PARALLEL_FUNC, 
                 TonalFunctions.SUBDOMINANT_FUNC, 
                 TonalFunctions.DOMINANT_FUNC, 
                 TonalFunctions.TONIC_PARALLEL_FUNC, 
                 TonalFunctions.DOMINANT_PARALLEL_FUNC]        
        minor = [TonalFunctions.TONIC_FUNC, 
                 TonalFunctions.DOMINANT_PARALLEL_FUNC, 
                 TonalFunctions.TONIC_PARALLEL_FUNC, 
                 TonalFunctions.SUBDOMINANT_PARALLEL_FUNC, 
                 TonalFunctions.DOMINANT_FUNC, 
                 TonalFunctions.TONIC_COUNTER_PARALLEL_FUNC, 
                 TonalFunctions.DOMINANT_PARALLEL_FUNC]
        
        if degree_mode != chord.mode:
            return None
        
        if self.mode == ScaleTypes.MAJOR:
            return TonalFunction(major[degree])
        if self.mode == ScaleTypes.MINOR:
            return TonalFunction(minor[degree])
        return None
        
    
class ScaleTypes():
    MAJOR_PATTERN = AlgorithmParameters.KRUMHANSL_SCALE_APPROXIMATION_MAJOR
    MINOR_PATTERN = AlgorithmParameters.KRUMHANSL_SCALE_APPROXIMATION_MINOR
    
    MAJOR = 'M'
    MINOR = 'm'
    
    Types:list[tuple[str,list[int]]] = [
        (MAJOR, MAJOR_PATTERN),
        (MINOR, MINOR_PATTERN),
    ]
    
ALL_SCALES = dict([((note, mode), Scale(note, pattern, mode)) for note in all_notes() for (mode, pattern) in ScaleTypes.Types])

DEGREES_SEMITONES:dict[str,list[int]] = {
    ScaleTypes.MAJOR: [0, 2, 4, 5, 7, 9, 11],
    ScaleTypes.MINOR: [0, 2, 3, 5, 7, 8, 10]
}
DEGREES_MODES:dict[str,list[str | None]] = {
    ScaleTypes.MAJOR:    
        [ChordTypes.MAJOR, None, 
         ChordTypes.MINOR, None, 
         ChordTypes.MINOR, 
         ChordTypes.MAJOR, None, 
         ChordTypes.MAJOR, None, 
         ChordTypes.MINOR, None, 
         ChordTypes.DIMINISHED],
    ChordTypes.MINOR : 
        [ChordTypes.MINOR, None, 
         ChordTypes.DIMINISHED,
         ChordTypes.MAJOR, None, 
         ChordTypes.MINOR, None, 
         ChordTypes.MINOR, 
         ChordTypes.MAJOR, None, 
         ChordTypes.MAJOR, None]}
