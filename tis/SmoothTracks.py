
from mido import MidiTrack


def smooth(metadata:MidiTrack, track:MidiTrack, ticks_per_beat:int) -> None:
    from midi_parser import MidiParser
    track_events = list(MidiParser._walk_events([metadata, track]))
    if(len(track_events) == 0):
        return
    last_start, end, last_messages, notes, time = track_events[0]
    last_note_count = len(notes)
    measure_end = time[0] * ticks_per_beat
    for start, end, messages, notes, time in track_events[1:]:
        if messages[0].type == 'end_of_track':
            continue
        if last_start + time[0] * ticks_per_beat > measure_end and len(last_messages) and len(messages) and last_note_count == 0:
            time_diff = min(measure_end, start) - last_start
            last_messages[0].time += time_diff
            messages[0].time -= time_diff
        while end > measure_end:
            measure_end += time[0] * ticks_per_beat
        last_note_count = len(notes)
        last_messages = messages
        last_start = start
