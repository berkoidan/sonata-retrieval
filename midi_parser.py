from typing import Iterable
import mido
import tis.NoteCluster as NC

TimeSignature = tuple[int,int]

class MidiParser():
    def __init__(self, filepath:str) -> None:        
        self.midi = mido.MidiFile(filepath)
        if self.midi.type == 2:
            raise Exception(f'Unsupported MIDI type: {self.midi.type}')
        if self.midi.type == 0:
            while len(self.midi.tracks) > 1:
                self.midi.tracks.pop(1)
        self.ticks_per_beat:int = self.midi.ticks_per_beat
        self.longest_track = max(map(self._get_track_duration, self.midi.tracks))
    
    def _next_beat_time(self, time:int) -> int:
        return self._beat_start_time(time) + self.ticks_per_beat

    def _beat_start_time(self, time:int) -> int:
        return (time // self.ticks_per_beat) * self.ticks_per_beat
    
    def _get_track_duration(self, track:mido.MidiTrack) -> int:
        for time, msg in self._walk_track_abs(track):
            pass
        if msg.type != 'end_of_track':
            raise Exception("Unexpected type of last message")
        return time
    
    def pad_tracks(self) -> None:
        if(self.midi.type == 0):
            return
        for track in self.midi.tracks:
            end_of_track_msg = track[-1]            
            end_of_track_msg.time += self.longest_track - self._get_track_duration(track)

    def commit_cluster(self, from_time:int, to_time:int, playing_notes:list[tuple[NC.Note,int]]) -> int:
        while self._beat_start_time(to_time) > self._beat_start_time(from_time):
            self.clusters[-1].add_notes([note[0] for note in playing_notes], self._next_beat_time(from_time) - from_time)            
            self.clusters.append(NC.NoteCluster())
            from_time = self._next_beat_time(from_time)
            self.clusters[-2].set_end_time(from_time // self.midi.ticks_per_beat)
            self.clusters[-1].set_begin_time(from_time // self.midi.ticks_per_beat)
        if from_time < to_time:
            self.clusters[-1].add_notes([note[0] for note in playing_notes], to_time - from_time)
        return to_time        
            
    def parse_to_clusters(self) -> None:
        self.clusters = [NC.NoteCluster()]
        self.clusters[0].set_begin_time(0)
        for start, end, _, notes, _ in self._walk_events(self.midi.tracks):
            self.commit_cluster(start, end, notes)
        self.clusters[-1].set_end_time(end // self.midi.ticks_per_beat)
    
    @staticmethod
    def _walk_track_abs(track:mido.MidiTrack) -> Iterable[tuple[int, mido.Message | mido.MetaMessage]]:
        current_time = 0
        for message in track:
            current_time += message.time
            yield current_time, message
    
    @staticmethod
    def _walk_tracks_abs(tracks:list[mido.MidiTrack]) -> Iterable[tuple[int, mido.Message | mido.MetaMessage]]:
        messages = []
        for track in tracks:
            messages += list(MidiParser._walk_track_abs(track))        
        messages.sort(key=lambda pair: pair[0])
        
        for time, msg in messages:            
            if msg.type != 'end_of_track':
                yield time, msg
        
        yield (time, mido.MetaMessage('end_of_track', time=0))
    
    @staticmethod
    def _walk_events(tracks:list[mido.MidiTrack]) -> Iterable[tuple[int, int, list[mido.Message | mido.MetaMessage], list[tuple[NC.Note, int]], TimeSignature]]:
        last_yield = 0
        playing_notes:list[tuple[NC.Note, int]] = []
        time_signature = (4, 4)
        messages:list[mido.Message | mido.MetaMessage] = []
        
        def consume_message(msg:mido.Message | mido.MetaMessage, time:TimeSignature) -> TimeSignature:
            if msg.type == 'time_signature':
                time = (msg.numerator, msg.denominator)
            
            if msg.type == 'pitchwheel' and msg.pitch > 0:
                raise Exception("Unsupported pitchwheel value")
            if msg.type == 'note_on' and msg.velocity > 0:
                playing_notes.append((NC.Note(msg.note), msg.channel))
            if msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                playing_notes.remove((NC.Note(msg.note), msg.channel))
            
            return time
        
        for abs_time, message in MidiParser._walk_tracks_abs(tracks):
            if abs_time > last_yield:
                if not message.is_meta or message.type == 'end_of_track':
                    yield last_yield, abs_time, messages, playing_notes, time_signature
                    messages = []
                    last_yield = abs_time
            
            messages.append(message)
            
            if message.type == 'end_of_track':
                yield abs_time, abs_time, messages, [], time_signature
                return
            
            time_signature = consume_message(message, time_signature)
        
    
    def clean_cluster_edges(self) -> None:
        while(len(self.clusters[0]) == 0):
            self.clusters.pop(0)
            
        while(len(self.clusters[-1]) == 0):
            self.clusters.pop(-1)
        
        while len(self.clusters) > 1 and self.clusters[-2] == self.clusters[-1]:
            self.clusters[-2] += self.clusters[-1]
            self.clusters.pop(-1)
                    


