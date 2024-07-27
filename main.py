from argparse import ArgumentParser, Namespace
from enum import Enum
import logging
import shutil
import sys, os

from mido import MidiFile
from midi_parser import MidiParser

logger = logging.getLogger(__name__)

def eprint(message:str) -> None:
    print(message, file=sys.stderr)

def argsparser() -> ArgumentParser:
    parser = ArgumentParser(
        description='This program generates an hierarcal tonality tree out of a generic MIDI file')
    parser.add_argument('midi_file', nargs='+', help='List of midi files or directories')
    parser.add_argument('-r', '--recursive', action='store_true', help='Recursive search of MIDI files in directories')
    parser.add_argument('-o', dest='output', help='Output directory', default='output')
    return parser

def get_midi_files(args:Namespace) -> list[tuple[str, str]]:
    midi_files = []
    for path in args.midi_file:
        if not os.path.exists(path):
            raise Exception(f'Path does not exists: {path}')
        if not os.path.isdir(path):
            midi_files.append(os.path.split(path))
            continue
        for (root, _, files) in os.walk(path):
            relroot = os.path.relpath(root, path)
            for file in files:
                midi_files.append((path, os.path.join(relroot, file)))
            if not args.recursive:
                break
    
    for file_parts in midi_files:
        file_path = os.path.join(*file_parts)
        if not os.path.isfile(file_path):
            raise Exception(f'Path is not a file: {file_path}')
        if os.path.splitext(file_path)[-1] != '.mid':
            raise Exception(f'File is not a MIDI file: {file_path}')
    
    return midi_files

def setup_output(output_dir:str, input_path:str) -> str:
    dir, _ = os.path.splitext(input_path)
    inner_output_dir = os.path.join(output_dir, dir)    
    shutil.rmtree(inner_output_dir, ignore_errors=True)
    os.makedirs(inner_output_dir, exist_ok=True)
    logging.basicConfig(filename=os.path.join(inner_output_dir, "run.log"), level=logging.DEBUG, force=True)    
    return inner_output_dir

def dump_midi(midi_file:MidiFile, directory:str) -> None:
    os.makedirs(directory, exist_ok=True)
    midi_file.save(os.path.join(directory, f'all_tracks.mid'))
    if midi_file.type != 1:
        return
    for i in range(1, len(midi_file.tracks)):
        new_mid = MidiFile()
        new_mid.tracks.append(midi_file.tracks[0])
        new_mid.tracks.append(midi_file.tracks[i])
        new_mid.save(os.path.join(directory, f'track{i}.mid'))

def main(args:Namespace) -> None:
    midi_files = get_midi_files(args)
    results:dict[str,int] = {}
    for file_parts in midi_files:
        output_dir = setup_output(args.output, file_parts[1])
        
        midipath = os.path.join(*file_parts)
        logger.info(os.path.abspath(midipath))
        eprint(os.path.abspath(midipath))
        handle_file(output_dir, midipath)
    print("Finished parsing and rendering")

class ReturnValues(Enum):
    SUCCESS = 'Success'
    PARSE_FAILURE = "Failed to parse Midi File"
    TOO_MANY_NODES = "Too Many Nodes"
    PRECHECK_FAILURE = "Precheck Failed"
    NO_TREE_FOUND = "No tree was found"

def handle_file(output_dir:str, midipath:str) -> ReturnValues:        
        # Step 1: Parse the MIDI file
        try:
            parser = MidiParser(midipath)
            parser.pad_tracks()
        except Exception as ex:
            logger.critical(f"Failes parsing file {midipath}")
            logger.exception(ex)            
            return ReturnValues.PARSE_FAILURE
                
        # Step 3 : Sample Clusters
        parser.parse_to_clusters()
        parser.clean_cluster_edges()
        
        # Step 4 : Tonality Approximation
        logger.info(f"Number of chords: {len(parser.clusters)}")
        if(len(parser.clusters) > 350):
            logger.error(f"Number of chords exceeds the maximum amount")
            return ReturnValues.TOO_MANY_NODES
        
        return ReturnValues.SUCCESS
                            
if __name__ == '__main__':
    parser = argsparser()
    args = parser.parse_args()
    main(args)
