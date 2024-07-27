from typing import Iterator, Self

ChromaVector = list[float]


class Note():
    NOTE_NAMES = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']
    NOTE_LEN = len(NOTE_NAMES)    
    
    def __init__(self, note:int):
        self.note:int = Note._mod(note)

    @staticmethod
    def _mod(note:int) -> int:
        return (note + 5 * Note.NOTE_LEN) % Note.NOTE_LEN
        
    def __str__(self) -> str:
        return Note.NOTE_NAMES[self.note]
    
    def __add__(self, other:Self | int) -> Self:
        if isinstance(other, int):
            return type(self)(self.note + other)
        return type(self)(self.note + other.note)
    
    def __sub__(self, other:Self | int) -> Self:
        if isinstance(other, int):
            return type(self)(self.note - other)
        return type(self)(self.note - other.note)
    
    def __repr__(self) -> str:
        return Note.NOTE_NAMES[self.note]
    
    def __hash__(self) -> int:
        return self.note
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, int):
            return self.note == Note._mod(other)
        if isinstance(other, type(self)):
            return self.note == other.note
        return NotImplemented

    @staticmethod
    def parse_note(note_str:str) -> int:
        key = Note.NOTE_NAMES.index(note_str[0]) + Note.NOTE_LEN
        if len(note_str) > 1 and note_str[1] == '#':
            key += 1
        if len(note_str) > 1 and note_str[1] == 'b':
            key -= 1
        return key % Note.NOTE_LEN
    
def all_notes() -> Iterator[Note]:
    return map(Note, range(Note.NOTE_LEN))

class NoteCluster():
    def __init__(self) -> None:
        self.notes:dict[Note,int] = dict(map(lambda note: (note, 0), all_notes()))
        self.begin_time = self.end_time = -1
        
    def add_note(self, note:Note, length:int) -> None:
        self.notes[note] += length
    
    def add_notes(self, notes:list[Note], length:int) -> None:
        for note in notes:
            self.add_note(note, length)
    
    def set_begin_time(self, time:int) -> None:
        self.begin_time = time
    
    def set_end_time(self, time:int) -> None:
        self.end_time = time
        
    def __len__(self) -> int:
        return sum(self.notes.values())
    
    def __getitem__(self, key: Note) -> float:
        return self.notes[key] / len(self)
    
    def __add__(self, other:Self) -> Self:
        ret = type(self)()
        ret.notes = dict(map(lambda note: (note, self.notes[note] + other.notes[note]), self.notes.keys()))
        ret.set_begin_time(self.begin_time)
        ret.set_end_time(other.end_time)
        return ret        
    
    def __str__(self) -> str:
        notes_str = '-'.join([f'{note}:{value}' for note, value in self.notes.items() if value > 0])
        time_str = f'{self.begin_time}->{self.end_time}'
        return f'{time_str}\t[{notes_str}]'
    
    def __eq__(self, value: object) -> bool:
        if not isinstance(value, NoteCluster):
            return NotImplemented
        value_len = len(value)
        self_len = len(self)
        if value_len == 0 and self_len == 0:
            return True
        if value_len == 0 or self_len == 0:
            return False
        for note in self.notes:
            if self.notes[note] * value_len != value.notes[note] * self_len:
                return False
        return True
    
    def __contains__(self, note:Note) -> bool:
        return self.notes[note] > 0
    
    def chroma(self) -> ChromaVector:
        chroma_vector:ChromaVector = [0] * 12
        cluster_len = len(self)
        if cluster_len == 0:
            return chroma_vector
        for note in self.notes.keys():
            chroma_vector[note.note] += self.notes[note] / cluster_len
        return chroma_vector
