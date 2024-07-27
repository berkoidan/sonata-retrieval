from typing import Self, final
from tonality.NoteCluster import Note, NoteCluster, all_notes

@final
class Chord(NoteCluster):
    @classmethod
    def get(cls, note:Note, mode:str) -> Self:
        return _ALL_CHORDS[note, mode]
    
    def __init__(self, note:Note, pattern:list[Note], mode:str) -> None:
        super().__init__()
        self.bass_note = note
        self.pattern = pattern
        self.mode = mode
        self.name = str(note) + mode
        for semitones in self.pattern:
            super().add_note(self.bass_note + semitones, 1)
        
    def __str__(self) -> str:
        return self.name
    
    def __repr__(self) -> str:
        return self.name
    
    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Chord):
            return super().__eq__(value)
        return value.name == self.name
    
    def __hash__(self) -> int:
        return hash(self.name)
    
    def dominant_degree(self) -> Self:
        if self.mode == ChordTypes.DIMINISHED:            
            return Chord.get(self.bass_note + Note(3), ChordTypes.MAJOR)
        return Chord.get(self.bass_note + Note(7), ChordTypes.MAJOR)

    def seventh_degree(self) -> Self:
        if self.mode == ChordTypes.DIMINISHED:            
            return Chord.get(self.bass_note + Note(7), ChordTypes.DIMINISHED)
        return Chord.get(self.bass_note + Note(11), ChordTypes.DIMINISHED)

class ChordTypes():
    MAJOR_PATTERN = [Note(0), Note(4), Note(7)]
    MINOR_PATTERN = [Note(0), Note(3), Note(7)]
    DIMINISHED_PATTERN = [Note(0), Note(3), Note(6)]
    
    AUGMENTED_PATTERN = [Note(0), Note(4), Note(8)]
    MAJOR_SEVENTH_PATTERN = [Note(0), Note(4), Note(7), Note(11)]
    DOMINANT_MAJOR_PATTERN = [Note(0), Note(4), Note(7), Note(10)]
    MINOR_SEVENTH_PATTERN = [Note(0), Note(3), Note(7), Note(11)]
    DOMINANT_MINOR_PATTERN = [Note(0), Note(3), Note(7), Note(10)]
    DIMINISHED_SEVENTH_PATTERN = [Note(0), Note(3), Note(6), Note(9)]
    HALF_DIMINISHED_PATTERN = [Note(0), Note(3), Note(6), Note(10)]
    AUGMENTED_SEVENTH_PATTERN = [Note(0), Note(4), Note(8), Note(11)]
    
    MAJOR = ''
    MINOR = 'm'
    DIMINISHED = '-'
    
    Types:list[tuple[str,list[Note]]] = [
        (MAJOR, MAJOR_PATTERN),
        (MINOR, MINOR_PATTERN),
        (DIMINISHED, DIMINISHED_PATTERN),        
    ]


_ALL_CHORDS = dict([((note, mode), Chord(note, pattern, mode)) for note in all_notes() for (mode, pattern) in ChordTypes.Types])
CHORD_VARIANTS:list[tuple[Chord,Chord]] = [(chord, chord) for chord in _ALL_CHORDS.values()] + [(Chord.get(note, ChordTypes.MAJOR), Chord(note, ChordTypes.DOMINANT_MAJOR_PATTERN, '7')) for note in all_notes()]
