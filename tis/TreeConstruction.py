import logging
import pprint
from typing import Any, Callable, Self, Sequence
from tis.TIS import TIS
from tis.TonalityApproximation import TonalityApproximation, TonalityCost
from tis.Scale import Scale, TonalFunction, TonalFunctions
from tis.Surface import Chord
import my_utils
logger = logging.getLogger(__name__)

class TonalRegions():
    TONIC_REGION = 'TR'
    DOMINANT_REGION = 'DR'
    SUBDOMINANT_REGION = 'SR'
        
class TonalityNode():
    @classmethod
    def from_node(cls, node:TonalityApproximation) -> Self:
        assert node.chord is not None
        assert node.key is not None
        assert node.tonal_function is not None
        return cls(node.chord, node.key, node.get_chord_cost(node.chord) + node.get_key_cost(node.key), node.tonal_function)
    
    @classmethod
    def simple(cls, chord:Chord, key:Scale) -> Self:
        return cls(chord, key, 0, TonalFunction(''))
    
    def __init__(self, chord:Chord, key:Scale, cost:TonalityCost, node_function:TonalFunction):
        self.chord = chord
        self.key = key
        self.cost = cost
        self.func = node_function
        
        self.children:list[TonalityNode] = []
        self.parent:TonalityNode | None = None
    
    def add_children(self, children:list[Self]) -> None:
        self.children += children
        for child in children:
            child.parent = self
    
    def pprint(self) -> None:
        pprint.pp(self._as_list())
    
    def _as_list(self) -> list[Any]:
        return [self.func, self.chord, self.key, round(self.cost,2), list(map(lambda child: child._as_list(), self.children))]
    
    def newick(self, quoted:bool=True) -> str:
        return f'({self._newick(quoted)});'
    
    def _newick(self, quoted:bool) -> str:
        name = f'"{self.chord}|{self.key} ({self.func})"' if quoted else f'{self.chord}|{self.key}|{self.func}'
        if not self.children:
            return name
        branchset = ','.join(map(lambda node: node._newick(quoted), reversed(self.children)))
        return f'({branchset}){name}'
        
    
    def __str__(self) -> str:
        base_harm_str = self.__repr__()
        if not self.children:
            return base_harm_str
        return f'{base_harm_str} -> [{', '.join([str(child) for child in self.children])}]'
    
    def __repr__(self) -> str:
        return f'{self.func}[{self.chord} / {self.key} / {round(self.cost,2)}]'

class RuleChordChoice():
    @staticmethod
    def first_chord(key:Scale, chords:list[Chord]) -> Chord:
        return chords[0]

    @staticmethod
    def last_chord(key:Scale, chords:list[Chord]) -> Chord:
        return chords[-1]

    @staticmethod
    def _closest_chord(rel:Chord, chords:list[Chord]) -> Chord:
        return min(chords, key=lambda chord: TIS.angular(chord, rel))

    @staticmethod
    def tonic(key:Scale, chords:list[Chord]) -> Chord:
        return RuleChordChoice._closest_chord(key.tonic(), chords)    

    @staticmethod
    def dominant(key:Scale, chords:list[Chord]) -> Chord:
        return RuleChordChoice._closest_chord(key.dominant(), chords)    

    @staticmethod
    def subdominant(key:Scale, chords:list[Chord]) -> Chord:
        return RuleChordChoice._closest_chord(key.subdominant(), chords)    

RULES:list[list[tuple[Sequence[str], Callable[[Scale, list[Chord]], Chord]]]] = [    
    [((TonalFunctions.SUBDOMINANT_FUNC, TonalFunctions.SUBDOMINANT_FUNC, TonalFunctions.SUBDOMINANT_FUNC), RuleChordChoice.subdominant)],                  # Rule 7
    [((TonalFunctions.TONIC_FUNC, TonalFunctions.TONIC_PARALLEL_FUNC), RuleChordChoice.first_chord),                        # Rule 11
     ((TonalFunctions.TONIC_FUNC, TonalFunctions.TONIC_COUNTER_PARALLEL_FUNC), RuleChordChoice.first_chord),                                               # Rule 12
     ((TonalFunctions.SUBDOMINANT_FUNC, TonalFunctions.SUBDOMINANT_PARALLEL_FUNC), RuleChordChoice.first_chord),                                           # Rule 13
     ((TonalFunctions.DOMINANT_FUNC, TonalFunctions.DOMINANT_PARALLEL_FUNC), RuleChordChoice.first_chord)],                                                # Rule 14
    [((TonalFunctions.TONIC_FUNC, TonalFunctions.TONIC_FUNC, TonalFunctions.SUBDOMINANT_FUNC, TonalFunctions.TONIC_FUNC), RuleChordChoice.tonic)],   # Rule 21
    [((TonalRegions.SUBDOMINANT_REGION, TonalFunctions.SUBDOMINANT_FUNC), RuleChordChoice.first_chord)],                                                   # Rule 10
    [((TonalRegions.SUBDOMINANT_REGION, TonalRegions.SUBDOMINANT_REGION, TonalRegions.SUBDOMINANT_REGION), RuleChordChoice.subdominant)],                  # Rule 7
    [((TonalRegions.DOMINANT_REGION, TonalRegions.DOMINANT_REGION, TonalRegions.DOMINANT_REGION), RuleChordChoice.dominant),                            # Rule 7
     ((TonalRegions.TONIC_REGION, TonalRegions.TONIC_REGION, TonalRegions.TONIC_REGION), RuleChordChoice.tonic)],                                    # Rule 7
    [((TonalRegions.DOMINANT_REGION, TonalRegions.SUBDOMINANT_REGION, TonalFunctions.DOMINANT_FUNC), RuleChordChoice.last_chord),                         # Rule 5
     ((TonalRegions.TONIC_REGION, TonalRegions.TONIC_REGION, TonalRegions.DOMINANT_REGION), RuleChordChoice.first_chord)],                                 # Rule 6
    [((TonalRegions.DOMINANT_REGION, TonalFunctions.DOMINANT_FUNC), RuleChordChoice.first_chord)],                                                         # Rule 9
    [((TonalRegions.TONIC_REGION, TonalRegions.DOMINANT_REGION, TonalFunctions.TONIC_FUNC), RuleChordChoice.last_chord)],                                 # Rule 4
    [((TonalRegions.TONIC_REGION, TonalFunctions.TONIC_FUNC), RuleChordChoice.first_chord)],                                                               # Rule 8
    [((TonalRegions.TONIC_REGION, TonalRegions.SUBDOMINANT_REGION, TonalRegions.TONIC_REGION), RuleChordChoice.last_chord)],                            # My own...
]

class TreeConstructor():
    def __init__(self, nodes:list[TonalityNode]):
        self.key = nodes[0].key
        for node in nodes:
            assert self.key == node.key
        self.nodes = nodes
    
    def _pair_children(self, start_index:int, length:int, node_function:TonalFunction, chord:Chord) -> None:
        children = self.nodes[start_index:start_index + length]
        parent = TonalityNode(chord, self.key, sum(map(lambda node: node.cost, children)), node_function)
        parent.add_children(children)
        self.nodes[start_index] = parent
        for i in reversed(range(start_index + 1, start_index + length)):
            self.nodes.pop(i)
            
    def _construct_step(self) -> bool:        
        tonal_functions = list(map(lambda node: node.func.name, self.nodes))        
        
        first_child = self._search_for_dominant(tonal_functions)
        if first_child == len(tonal_functions) - 1:
            return False
        if first_child >= 0:
            self._pair_children(first_child, 2, TonalFunction(tonal_functions[first_child + 1]), self.nodes[first_child+1].chord)
            return True
    
        for ruleset in RULES:
            for i in my_utils.from_the_middle_out(0, len(self.nodes)):
                for rule, chord_choice in ruleset:
                    root_value = rule[0]
                    children_values = tuple(rule[1:])
                    
                    max_index = i + len(children_values)
                    if max_index > len(self.nodes):
                        continue
                    
                    if tuple(tonal_functions[i:max_index]) == children_values:
                        key = self.nodes[i].key
                        chords = [node.chord for node in self.nodes[i:max_index]]
                        self._pair_children(i, len(children_values), TonalFunction(root_value), chord_choice(key, chords))
                        return True
        return False

    def _search_for_dominant(self, tonal_functions:list[str]) -> int:
        if TonalFunctions.DIATONIC_DOMINANT_DEGREE in tonal_functions:
            return tonal_functions.index(TonalFunctions.DIATONIC_DOMINANT_DEGREE)
        if TonalFunctions.DOMINANT_DEGREE in tonal_functions:
            return tonal_functions.index(TonalFunctions.DOMINANT_DEGREE)
        if TonalFunctions.DIMINSHED_DEGREE in tonal_functions:
            return tonal_functions.index(TonalFunctions.DIMINSHED_DEGREE)
        return -1
    
    def construct(self) -> TonalityNode | None:
        logger.debug(f'BT: Constructing Tree: {self.nodes}')
        while len(self.nodes) > 1 or self.nodes[0].func != TonalRegions.TONIC_REGION:
            if not self._construct_step():
                logger.debug(f'BT: No Possible steps found: {self.nodes}')
                return None
        logger.debug(f'BT: Tree construction reached sucess: {self.nodes[0]}')        
        return self.nodes[0]

def relative_key(nodes:list[TonalityNode], key:Scale) -> TreeConstructor | None:
    for i in reversed(range(len(nodes))):
        next_node = nodes[i+1] if i < len(nodes) - 1 else None
        chord = nodes[i].key.tonic()
        tonal_functions = get_tonal_functions(key, chord, next_node)
        if(len(tonal_functions) == 0):            
            logger.warning(f"Can't find tonal function: {key}, {chord}")
            chord = nodes[i].key.parallel().tonic()
            tonal_functions = get_tonal_functions(key, chord, next_node)
            for func in tonal_functions:
                func.parallel = True
            if(len(tonal_functions) == 0):            
                logger.warning(f"Can't find tonal function: {key}, {chord}")
                return None
        modulation = TonalityNode(chord, key, nodes[i].cost, tonal_functions[0])
        modulation.add_children([nodes[i]])
        nodes[i] = modulation
    return TreeConstructor(nodes)

def get_tonal_functions(key:Scale, chord:Chord, next:TonalityApproximation | TonalityNode | None) -> list[TonalFunction]:
    functions = []
    function = key.get_function(chord)
    if function is not None:
        if next is not None or not function.is_subdominant():
            functions.append(function)
        if function.name == TonalFunctions.DOMINANT_FUNC:
            return functions

    # dominant functions
    if next is None:
        return functions
    
    next_key = next.key
    next_chord = next.chord
    assert next_key is not None
    assert next_chord is not None
    if(next_chord.dominant_degree() == chord):
        functions.append(TonalFunction(TonalFunctions.DOMINANT_DEGREE))
    if(next_chord.seventh_degree() == chord):
        functions.append(TonalFunction(TonalFunctions.DIMINSHED_DEGREE))
    if next_key == key and key.diatonic_dominant(next_chord) == chord and TonalFunction(TonalFunctions.DOMINANT_DEGREE) not in functions:
        functions.append(TonalFunction(TonalFunctions.DIATONIC_DOMINANT_DEGREE))
    return functions