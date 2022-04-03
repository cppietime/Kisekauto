from typing import List, Tuple, Any, Dict, Union, Set, Optional
from dataclasses import dataclass, field
from os import path
import json
import io

from . import imagegen
from .types.chunk import Code

_empty_list_factory = lambda: []

@dataclass
class Source:
    source: str = ''
    name: str = ''
    path: str = ''
    blacklist: Set[str] = field(default_factory = _empty_list_factory)
    whitelist: Set[str] = field(default_factory = _empty_list_factory)
    tags: Set[str] = field(default_factory = _empty_list_factory)
    
    code: Code = field(init = False)
    
    def __post_init__(self) -> None:
        self.blacklist = set(self.blacklist)
        self.whitelist = set(self.whitelist)
        self.tags = set(self.tags)
        self.code = self.load()
    
    def load(self) -> Code:
        # if self.source == 'internal':
            # return imagegen.preset_code(self.path)
        # return imagegen.custom_code(self.path)
        return Code()

@dataclass
class Option:
    name: str = ''
    sources: List[Source] = field(default_factory = _empty_list_factory)
    
    codes: List[Code] = field(init = False)
    
    def __post_init__(self) -> None:
        self.codes = self._enumerate_codes()
    
    def _enumerate_codes(self) -> Dict[str, Code]:
        return dict(map(lambda x: (x.name, x.load()), self.sources))

@dataclass
class MixerProgram:
    destdir: str
    options: List[Option]
    
    def _enumerate_codes(self, index: int, tags: Set[str],\
            blacklist: Set[str]) -> Dict:
        option: Option = self.options[index]
        total: Dict = {}
        for source in option.sources:
            if source.tags.intersection(blacklist) != set() or\
                    source.blacklist.intersection(tags) != set():
                continue
            if index + 1 < len(self.options):
                blacklist_new: Set = blacklist.union(source.blacklist)
                tags_new: Set = tags.union(source.tags)
                ext: Dict = (self._enumerate_codes(index + 1, tags_new, blacklist_new))
                for ext_name, ext_code in ext.items():
                    name: str = source.name + '_' + ext_name
                    code: Code = source.code.copy()
                    code.merge(ext_code)
                    total[name] = code
            else:
                total[source.name] = source.code
        return total
    
    def enumerate_codes(self):
        d: Dict = self._enumerate_codes(0, set(), set())
        return dict(map(lambda x: (path.join(self.destdir, x[0]), x[1]), d.items()))

_singletons: Dict[str, type] = {}
_lists: Dict[str, type] = {'sources': Source, 'options': Option}

def _decode_pair(pair: Tuple) -> Tuple:
    try:
        if isinstance(pair[1], List):
            if pair[0] in _lists:
                typ: type = _lists[pair[0]]
                return (pair[0], list(map(lambda x: typ(**x), pair[1])))
        else:
            if pair[0] in _singletons:
                typ: type = _singletons[pair[0]]
                return (pair[0], typ(**pair[1]))
    except TypeError as e:
        pass
    return pair

def _decode_pairs(pairs: List[Tuple]) -> Any:
    d = dict(map(_decode_pair, pairs))
    return d

def load(source: Union[str, io.IOBase]) -> MixerProgram:
    if isinstance(source, str):
        with open(source) as file:
            mixer: Dict = json.load(file, object_pairs_hook = _decode_pairs)
    else:
        mixer = json.load(source, object_pairs_hook = _decode_pairs)
    return MixerProgram(**mixer)

def loads(source: str) -> MixerProgram:
    mixer: Dict = json.loads(source, object_pairs_hook = _decode_pairs)
    return MixerProgram(**mixer)


