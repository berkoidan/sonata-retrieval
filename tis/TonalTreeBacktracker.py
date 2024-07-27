import logging
from typing import Iterable
import my_utils
import AlgorithmParameters
from tonality.TonalityApproximation import TonalityApproximation, TonalityCost, approximate_tonality
from tonality.NoteCluster import NoteCluster
from tonality.Scale import Scale, TonalFunction
from tonality.Surface import Chord
from tonality.TreeConstruction import TonalityNode, TreeConstructor, get_tonal_functions, relative_key

logger = logging.getLogger(__name__)

class TonalFunctionBacktacker():
    def __init__(self, clusters: list[NoteCluster]):
        logger.info(f"Number of chords: {len(clusters)}")
        self.leaves = list(approximate_tonality(clusters))
        self.key_leaves = self._extract_keys(self.leaves)        
        logger.debug(f"Keys: {self.key_leaves}")
        self.tonic_trees:list[TonalityNode] = []
    
    def _precheck_node_tonal_functions(self, i:int) -> bool:
        for key in self._get_key_window(i):
            for chord in self.leaves[i].chord_choices:
                if i >= len(self.leaves) - 1:
                    funcs = get_tonal_functions(key, chord[0], None)
                    if len(funcs): 
                        return True
                    continue
                for next_key in self._get_key_window(i+1):
                    for next_chord in self.leaves[i+1].chord_choices:                            
                        funcs = get_tonal_functions(key, chord[0], TonalityNode.simple(next_chord[0], next_key))
                        if len(funcs) : 
                            return True
        return False
    
    def precheck(self) -> bool:
        for i in range(len(self.leaves)):
            logger.debug(f'Precheck {i} {self.leaves[i]}')
            if not self._precheck_node_tonal_functions(i):
                logger.debug(f'Precheck failed {i} {self.leaves[i]}')
                logger.debug(f'Precheck failed {i+1} {self.leaves[i+1]}')
                return False
        return True
            
    
        
    def backtrack(self) -> tuple[TonalityNode|None, list[TonalityNode]]:
        for leaves in self._backtracking_choose_key(len(self.leaves), len(self.leaves)):            
            tonic_trees = list(reversed(self.tonic_trees))
            constructor = relative_key(tonic_trees, tonic_trees[-1].key)
            if(constructor is None):
                constructor = relative_key(tonic_trees, tonic_trees[0].key)
            if(constructor is None):
                continue
            
            root = constructor.construct()
            if(root is None):
                continue
            return root, leaves
        return (None, [])

    @staticmethod
    def _extract_keys(nodes:list[TonalityApproximation]) ->list[Scale]:
        def choose_key(prev:Scale|None, current:Scale, next:Scale|None) -> Scale:
            if prev is None and next is None:
                return current
            if current != prev and current != next:
                if prev is not None: return prev
                assert next is not None
                return next                
            return current                
        
        keys:list[Scale] = []
        for i in range(len(nodes)):
            prev_key = nodes[i-1].most_likely_key() if i > 0 else None
            current_key = nodes[i].most_likely_key()
            next_key = nodes[i+1].most_likely_key() if i < len(nodes) - 1 else None
            keys.append(choose_key(prev_key, current_key, next_key))
        return keys

    # last_decision = the index of the next node, where the key and chord are decided
    # key_window_id = the index of the key window from the array self.key_windows, that points to the window the last decision is in
    # next_key_change = the index of the node when the key is changed
    def _backtracking_choose_key(self, last_decision:int, next_key_change:int) -> Iterable[list[TonalityNode]]:
        if last_decision == 0:
            logger.debug(f'BT:{last_decision} Choosing Key: No more nodes, constructing the last subtree')
            tree = TreeConstructor(list(map(TonalityNode.from_node, self.leaves[last_decision:next_key_change]))).construct()
            if tree is None:
                return
            self.tonic_trees.append(tree)
            logger.debug(f'BT:{last_decision} Choosing Key: Subtrees are completed ({len(self.tonic_trees)}): {list(reversed(self.tonic_trees))}')
            yield list(map(TonalityNode.from_node, self.leaves))
            self.tonic_trees.pop()
            return
        
        key_options = self._get_key_window(last_decision-1)
        logger.debug(f'BT:{last_decision} Choosing Key: key options: {key_options}')
        tree_constructor:TreeConstructor|None = None
        subtree:TonalityNode|None = None
        for key in key_options:
            tonic_trees_flag = False
            if last_decision < len(self.leaves) and key != self.leaves[last_decision].key:
                if next_key_change - last_decision <= 1:
                    # not allowed to change key after one node
                    continue
                logger.debug(f'BT:{last_decision} Choosing Key: Construcing closed window subtree {last_decision}-{next_key_change}')
                if tree_constructor is None:
                    tree_constructor = TreeConstructor(list(map(TonalityNode.from_node, self.leaves[last_decision:next_key_change])))
                    subtree = tree_constructor.construct()
                if subtree is None:
                    continue
                tonic_trees_flag = True
                self.tonic_trees.append(subtree)
            else:
                logger.debug(f'BT:{last_decision} Choosing Key: key is identical to next key')
            self.leaves[last_decision-1].choose_key(key)
            possible_tree_leaves = self._backtracking_choose_chord(key, last_decision - 1, last_decision if tonic_trees_flag else next_key_change)
            if possible_tree_leaves is not None:
                yield possible_tree_leaves
            if tonic_trees_flag:
                self.tonic_trees.pop() 

    def _get_key_window(self, pos:int) -> list[Scale]:
        key_options:list[Scale] = []
        for i in my_utils.from_the_middle_out(
            max(0, pos-AlgorithmParameters.STRETCH_KEY_WINDOW), 
            min(len(self.key_leaves), pos+AlgorithmParameters.STRETCH_KEY_WINDOW+1)):
            if self.key_leaves[i] not in key_options:
                key_options.append(self.key_leaves[i])
        return key_options           
    
    def get_chord_options_sorted(self, key:Scale, next_node:TonalityApproximation | None, chord_options:list[tuple[Chord, TonalityCost]]) -> list[tuple[Chord, list[TonalFunction], TonalityCost]]:
        x = [(chord, get_tonal_functions(key, chord, next_node), cost) for chord, cost in chord_options]
        x = [(chord, func, cost) for (chord, func, cost) in x if len(func) > 0]
        return x
                
    def _backtracking_choose_chord(self, key:Scale, to_be_decided:int, next_key_change:int) -> list[TonalityNode] | None:
        logger.debug(f'BT:{to_be_decided} Choosing Chord: key {key}')
        next_node = self.leaves[to_be_decided+1] if to_be_decided < next_key_change-1 else None
        if next_node is None:
            logger.debug(f'BT:{to_be_decided} Choosing Chord: Last node in subtree')
        else:
            logger.debug(f'BT:{to_be_decided} Choosing Chord: Choosing predecesor to {next_node.chord}/{next_node.key}')
        chord_options = self.get_chord_options_sorted(key, next_node, self.leaves[to_be_decided].chord_choices)
        if len(chord_options):
            logger.debug(f'BT:{to_be_decided} Choosing Chord: Options found for chords: {chord_options}')
        else:
            logger.debug(f'BT:{to_be_decided} Choosing Chord: No chord Options were found. Choices were: {self.leaves[to_be_decided].chord_choices}')
        for chord, tonal_function_options, _ in chord_options:
            self.leaves[to_be_decided].choose_chord(chord)
            for tonal_function in tonal_function_options:
                self.leaves[to_be_decided].tonal_function = tonal_function
                logger.debug(f'BT:{to_be_decided} Choosing Chord: Trying with chord {chord} as {tonal_function}')
                for x in self._backtracking_choose_key(to_be_decided, next_key_change):
                    return x
        return None                    

