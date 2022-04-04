import typing, json, os
from . import GetterMeta, subcodes, Consts

list_t = typing.Dict[str, typing.Tuple[str, subcodes.SubcodeType]]

class ComponentType(metaclass = GetterMeta):
    '''
    A component containing subcodes
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
        return key in _components_by_id

class Component:
    '''
    An instance of a component
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
    
    def add(self, data: typing.Union[str, subcodes.Subcode]) -> None:
        if isinstance(data, str):
            subcode: subcodes.Subcode = subcodes.Subcode.fromString(data)
        else:
            subcode = data
        key = subcode.tag
        if subcode.index != -1:
            key += ('{:01}' if subcode.tag in Consts.singleDigits else '{:02}').format(subcode.index)
        self.subcodes[key] = subcode
    
    def merge(self, other: 'Component', mode: str = 'all') -> None:
        for key, subcode in other.subcodes.items():
            if key not in self.subcodes:
                self.subcodes[key] = subcode
            else:
                self.subcodes[key].merge(subcode, mode)
    
    def copy(self) -> 'Component':
        new: 'Component' = Component(self.spec)
        new.subcodes = dict(map(lambda x: (x[0], x[1].copy()), self.subcodes.items()))
        return new
    
    def filter(self, skeys: typing.Iterable[str]) -> None:
        if len(skeys) == 0:
            return
        self.subcodes = dict(filter(lambda x:\
                x[1].tag in skeys or\
                x[0] in skeys or\
                self.spec[x[1].tag][1] in skeys,\
            self.subcodes.items()))

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