'''
kisekauto/types/components.py
c Yaakov Schectman 2022

Defines the components and their specs for KisekaeII codes
'''

import typing, json, os
from . import GetterMeta, subcodes, Consts

list_t = typing.Dict[str, typing.Tuple[str, subcodes.SubcodeType]]

class ComponentType(metaclass = GetterMeta):
    '''
    The specification for a component that contains subcodes of a common category
    
    name: Name used for access and filtering
    singles: A list of subcode types of which this component contains one each
    arrays: A list of subcode types of which this component may contain any number
    '''
    def __init__(self, name: str,\
            singles: list_t,\
            arrays: list_t) -> None:
        self.name: str = name
        self.singles: list_t = singles
        self.arrays: list_t = arrays
    
    def __getitem__(self, key: str) ->\
            typing.Tuple[bool, typing.Optional[str], subcodes.SubcodeType]:
        if key in self.singles:
            return (False,) + self.singles[key]
        return (True,) + self.arrays[key]
    
    def __getattr__(self, key: str) ->\
            typing.Tuple[bool, typing.Optional[str], subcodes.SubcodeType]:
        return self[key]
    
    def __contains__(self, key: str) -> bool:
        return key in self.singles or key in self.arrays
    
    def __str__(self) -> str:
        return f'<Component({self.name})>'
    
    @staticmethod
    def fromDict(src: typing.Dict[str, typing.Any]) -> 'ComponentType':
        '''
        Convert a dictionary read from the JSON specifiers into a component type
        '''
        transform = lambda x: (x[0], (x[1][0], subcodes.SubcodeType.classGet(x[1][1])))
        name: str = src['name']
        singles_src: typing.Dict[str, typing.Any] = src['singles']
        singles: list_t = dict(map(transform, singles_src.items()))
        arrays_src: typing.Dict[str, typing.Any] = src['arrays']
        arrays: list_t = dict(map(transform, arrays_src.items()))
        return ComponentType(name, singles, arrays)
    
    @classmethod
    def classGet(cls, key: str) -> 'ComponentType':
        if key in _components_by_id:
            return _components_by_id[key]
        return _components_by_prefix[key]
    
    @staticmethod
    def isComponent(key: str) -> bool:
        '''
        Returns True iff key is the name of a recognized component
        '''
        return key in _components_by_id
    
    @staticmethod
    def componentTypes() -> typing.List['ComponentType']:
        return _components

class Component:
    '''
    An instance of a component
    
    spec: the type of this component
    data: the string representation from which to parse the component
    '''
    def __init__(self, spec: ComponentType, data: str = '') -> None:
        self.spec: ComponentType = spec
        self.subcodes: typing.Dict[str, subcodes.Subcode] = {}
        for src in filter(lambda x: x != '', data.split('_')):
            self.add(src)
    
    def __getitem__(self, key: str) -> subcodes.Subcode:
        if key not in self.subcodes:
            self.subcodes[key] = subcodes.Subcode.fromString(key)
        return self.subcodes[key]
    
    __getattr__ = __getitem__
    
    def __setitem__(self, key: str, data: typing.Union[str, subcodes.Subcode]) -> None:
        if isinstance(data, str):
            subcode: subcodes.Subcode = subcodes.Subcode.fromString(key + data)
        else:
            subcode = data
        self.subcodes[key] = subcode
    
    def __contains__(self, key: str) -> bool:
        return key in self.subcodes
    
    def __str__(self) -> str:
        return '_'.join(map(str, self.subcodes.values()))
    
    def add(self, data: typing.Union[str, subcodes.Subcode]) -> 'Component':
        '''
        Add a subcode to this component
        
        data: either the string representation of a subcode, or a subcode object
        returns self
        '''
        if isinstance(data, str):
            subcode: subcodes.Subcode = subcodes.Subcode.fromString(data)
        else:
            subcode = data
        key = subcode.tag
        if subcode.index != -1:
            key += ('{:01}' if subcode.tag in Consts.singleDigits else '{:02}').format(subcode.index)
        self.subcodes[key] = subcode
        return self
    
    def merge(self, other: 'Component', mode: str = 'all') -> 'Component':
        '''
        Merge another component into this one IN-PLACE
        
        other: Other component to merge into this one
        mode: don't use it
        returns self
        '''
        for key, subcode in other.subcodes.items():
            if key not in self.subcodes:
                self.subcodes[key] = subcode
            else:
                self.subcodes[key].merge(subcode, mode)
    
    def copy(self) -> 'Component':
        '''
        Returns a new component with identical contents to this one
        '''
        new: 'Component' = Component(self.spec)
        new.subcodes = dict(map(lambda x: (x[0], x[1].copy()), self.subcodes.items()))
        return new
    
    def filter(self, skeys: typing.Iterable[str]) -> 'Component':
        '''
        Filter this component as described in Chunk.filter
        '''
        if len(skeys) == 0:
            return self
        self.subcodes = dict(filter(lambda x:\
                x[1].tag in skeys or\
                x[0] in skeys or\
                self.spec[x[1].tag][1] in skeys,\
            self.subcodes.items()))
        return self
    
    def exclude(self) -> 'Component':
        '''Voids absent subcodes'''
        absent = set()
        for tag, subcodeType in self.spec.singles.items():
            if tag not in self.subcodes:
                absent.add(tag)
                self.subcodes[tag] = subcodes.Subcode(subcodeType[1], tag = tag)
        for tag, subcodeType in self.spec.arrays.items():
            max_index: int = 9 if tag in Consts.singleDigits else 99
            for i in range(0, max_index):
                prefix: str = ('{:01}' if tag in Consts.singleDigits else '{:02}').format(max_index)
                if prefix not in self.subcodes:
                    self.subcodes[prefix] = subcodes.Subcode(subcodeType[1], tag = tag, index = i)
                    break
        return self

with open(os.path.join(os.path.dirname(__file__), 'components.json')) as src:
    _components_src: typing.List[typing.Dict] = json.load(src)
    _components: typing.List[ComponentType] = list(map(ComponentType.fromDict, _components_src))
    _components_by_id = dict(map(lambda x: (x.name, x), _components))
    _components_by_prefix: typing.Dict[str, ComponentType] = {}
    for comp in _components:
        for prefix in comp.singles.keys():
            _components_by_prefix[prefix] = comp
        for prefix in comp.arrays.keys():
            _components_by_prefix[prefix] = comp