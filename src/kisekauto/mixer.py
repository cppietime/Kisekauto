'''
kisekauto/mixer.py
c Yaakov Schectman 2022

Utility for mix-and-matching many codes
'''

from typing import List, Tuple, Any, Dict, Union, Set, Optional
from dataclasses import dataclass, field
from os import path, walk
import asyncio
import json
import io
import sys

from . import imagegen
from .types.chunk import Code

_empty_list_factory = lambda: []

@dataclass
class Source:
    '''
    A source specifying
    source: whether internal(preset) or external(custom)
    name: what to name files generated with this source
    path: a path to the file, or pattern to match
    blacklist: tags to avoid mixing with this source
    tags: tags defining this source
    '''
    source: str = ''
    name: str = ''
    path: str = ''
    blacklist: Set[str] = field(default_factory = _empty_list_factory)
    whitelist: Set[str] = field(default_factory = _empty_list_factory)
    tags: Set[str] = field(default_factory = _empty_list_factory)
    
    __codes: Optional[List[Code]] = field(init = False, default = None)
    
    def __post_init__(self) -> None:
        self.blacklist = set(self.blacklist)
        self.whitelist = set(self.whitelist)
        self.tags = set(self.tags)
    
    def _load(self) -> None:
        codes = []
        if self.source == 'internal':
            codes += imagegen.preset_code(self.path)
        else:
            codes += (imagegen.custom_codes(self.path))
        self.__codes = codes
    
    def codes(self) -> List[Code]:
        if self.__codes is None:
            self._load()
        return self.__codes

@dataclass
class Option:
    '''
    A choosable option. Unless blacklists proclude it, one source from each option will be
    chosen for each code
    '''
    name: str = ''
    sources: List[Source] = field(default_factory = _empty_list_factory)
    
    codes: List[Code] = field(init = False)
    
    def __post_init__(self) -> None:
        self.codes = self._enumerate_codes()
    
    def _enumerate_codes(self) -> Dict[str, List[Code]]:
        return dict(map(lambda x: (x.name, x.codes()), self.sources))

@dataclass
class MixerProgram:
    '''
    The mixer containing all associated options
    '''
    destdir: str
    options: List[Option]
    
    def _enumerate_codes(self, index: int, tags: Set[str],\
            blacklist: Set[str], whitelist: Set[str]) -> Dict:
        option: Option = self.options[index]
        total: Dict = {}
        for source in option.sources:
            if source.tags.intersection(blacklist) != set() or\
                    source.blacklist.intersection(tags) != set():
                continue
            whitelist_new: Set = whitelist.union(source.whitelist)
            tags_new: Set = tags.union(source.tags)
            whitelisted: bool = len(whitelist_new) != 0 and\
                    len(whitelist_new.difference(tags_new)) != 0 and\
                    index + 1 == len(self.options)
            if whitelisted:
                continue
            if index + 1 < len(self.options):
                blacklist_new: Set = blacklist.union(source.blacklist)
                ext: Dict = (self._enumerate_codes(index + 1, tags_new, blacklist_new, whitelist_new))
                for sci, src_code in enumerate(source.codes()):
                    basename: str = source.name
                    if len(source.codes()) > 1:
                        basename += str(sci)
                    for ext_name, ext_code in ext.items():
                        name: str = basename + '_' + ext_name
                        code: Code = src_code.copy()
                        code.merge(ext_code)
                        total[name] = code
            else:
                for sci, src_code in enumerate(source.codes()):
                    name: str = source.name
                    if len(source.codes()) > 1:
                        name += sci
                    # print(f'Enum{sci}')
                    total[name] = src_code#.exclude()
        return total
    
    def enumerate_codes(self) -> Dict[str, Code]:
        '''Return a dictionary with keys of concatenated source names mapped to their code values'''
        d: Dict = self._enumerate_codes(0, set(), set(), set())
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
        print(e)
    return pair

def _decode_pairs(pairs: List[Tuple]) -> Any:
    d = dict(map(_decode_pair, pairs))
    return d

def load(source: Union[str, io.IOBase]) -> MixerProgram:
    '''Load a mixer program from a filepath or IO object'''
    if isinstance(source, str):
        with open(source) as file:
            mixer: Dict = json.load(file, object_pairs_hook = _decode_pairs)
    else:
        mixer = json.load(source, object_pairs_hook = _decode_pairs)
    return MixerProgram(**mixer)

def loads(source: str) -> MixerProgram:
    '''Load a mixer program from a JSON string'''
    mixer: Dict = json.loads(source, object_pairs_hook = _decode_pairs)
    return MixerProgram(**mixer)

async def render_program(source: str, outputdir: str = '.', **options) -> bool:
    mixer: MixerProgram = load(source)
    client: imagegen.KisekautoClient = await imagegen.KisekautoClient.connect()
    print('Connected to client')
    success: bool = True
    for name, code in mixer.enumerate_codes().items():
        code = code.exclude()
        destdir: str = path.join(outputdir, name + '.png')
        print(f'Rendering {name} to {destdir}...')
        await client.apply_code(code)
        success &= await client.capture_character(destdir, 0, **options)
    await client.close()
    return success

def output_codes(source: str, outputdir: str = '.') -> None:
    mixer: MixerProgram = load(source)
    for name, code in mixer.enumerate_codes().items():
        destdir: str = path.join(outputdir, name + '.kkl')
        with open(destdir, 'w') as file:
            file.write(str(code))

def main(argv):
    import argparse
    parser: argparse.ArgumentParser = argparse.ArgumentParser(description=
        'A utility for rendering batches of codes to images')
    parser.add_argument('-i', '--input', nargs='*', help='Any number of file patterns to match')
    parser.add_argument('-o', '--outputdir', default='.', help='A base directory for output files')
    parser.add_argument('-q', '--fast', action='store_true', help=
        'Produce image faster, but larger')
    parser.add_argument('-x', '--scale', type=int, help='Scale factor for rendering')
    parser.add_argument('-c', '--code', action='store_true', help='Only output the merged codes')
    args = parser.parse_args(argv)
    opts = {'scale': args.scale, 'fast': args.fast}
    for i in args.input:
        if args.code:
            output_codes(i, args.outputdir)
        else:
            asyncio.run(render_program(i, args.outputdir, **opts))
    
if __name__ == '__main__':
    main(sys.argv[1:])