'''
kisekauto/types/subcodes.py
c Yaakov Schectman 2022

Defines subcodes that make up KisekaeII codes
'''

import typing, json, os

from . import GetterMeta, Consts

class SubcodeType(metaclass = GetterMeta):
    '''
    A Kisekae subcode specification
    
    name: the name of this object
    tag: what is used to identify this subcode in a code
    names: the name for each element within the subcode
    '''
    def __init__(self, name: str, tag: str, names: typing.List[str],
            poses: typing.Optional[typing.List[str]] = None,
            colors: typing.Optional[typing.List[str]] = None,
            exprs: typing.Optional[typing.List[str]] = None,
            clothes: typing.Optional[typing.List[str]] = None,
            body: typing.Optional[typing.List[str]] = None,
            lerp: typing.Optional[typing.List[str]] = None) -> None:
        self.name: str = name
        self.tag: str= tag
        self.names: typing.List[str] = names
        self.poses: typing.Set[str] = set() if poses is None else set(poses)
        self.colors: typing.Set[str] = set() if colors is None else set(colors)
        self.exprs: typing.Set[str] = set() if exprs is None else set(exprs)
        self.clothes: typing.Set[str] = set() if clothes is None else set(clothes)
        self.body: typing.Set[str] = set() if body is None else set(body)
        self.lerp: typing.Set[str] = set() if lerp is None else set(lerp)
    
    def __getitem__(self, key: typing.Union[int, str]) -> typing.Union[str, int]:
        if isinstance(key, int):
            if key < 0 or key >= len(self.names):
                return ''
            return self.names[key]
        try:
            return self.names.index(key)
        except ValueError:
            return -1
    
    def __getattr__(self, key: str) -> int:
        return self[key]
        
    def __len__(self) -> int:
        return len(self.names)
    
    def __str__(self) -> str:
        return f'<Subcode {self.name}({repr(self.tag)})[{self.names}]>'
    
    @staticmethod
    def fromString(text: str) -> typing.List['SubcodeType']:
        '''
        Given a JSON string specifying a number of subcode types,
        read them and return the list of specs
        
        text: JSON string with subcode types
        returns a list of SubcodeTypes
        '''
        d: typing.List[typing.List[str, typing.Any]] = json.loads(text)
        return list(map(lambda x: SubcodeType(**x), d))
    
    @classmethod
    def classGet(cls, key: str) -> 'SubcodeType':
        return _subcodes_by_name[key]

class Subcode:
    '''
    An instance of a subcode
    
    subcode_type: specifies the specification of type of this subcode
    pieces: optional initial list of data
    index: optional index in a list
    '''
    def __init__(self, subcode_type: SubcodeType,\
            pieces: typing.Optional[typing.List[str]] = None,\
            index: int = -1,\
            tag: typing.Optional[str] = None) -> None:
        self.subcode_type: SubcodeType = subcode_type
        self.pieces: typing.List[str] = ([''] * len(self.subcode_type)) if pieces is None\
            else pieces
        self.index: int = index
        self.tag: str = tag if tag is not None else subcode_type.tag
    
    def getPrefix(self) -> str:
        '''
        Format the prefix to include the index if necessary, with the proper number of digits
        '''
        return self.tag +\
            (('{:01}' if self.tag in Consts.singleDigits else '{:02}').format(self.index) if self.index >= 0\
            else '')
        
    def __str__(self) -> str:
        '''
        Appends this subcode's index, if appropriate, to all pieces, unless empty
        '''
        return self.getPrefix() +\
            '.'.join(filter(lambda _: self.pieces[0] != '', self.pieces))
    
    def __getitem__(self, key: typing.Union[int, str]) -> str:
        '''
        Return the piece corresponding to a name or index, or '0' if none match
        
        key: the string name or ineger index of the piece to fetch
        returns the matching piece, or '0'
        '''
        if isinstance(key, int):
            if key < 0 or key >= len(self.pieces):
                return '0'
            return self.pieces[key]
        try:
            return self.pieces[self.subcode_type[key]]
        except IndexError:
            return '0'
    
    def __setitem__(self, key: typing.Union[int, str], value: typing.Any) -> None:
        '''
        Assigns a value to a position in pieces specified by key.
        If there is no match for key, nothing will be done.
        If the match for key is at a position greater than the current length of pieces,
        pieces will be extended by '0' strings to be made large enough
        
        key: the string name or integer index of the piece to assign
        value: an object whose string value will be assigned, if possible
        '''
        if isinstance(key, int):
            index = key
        else:
            index = self.subcode_type[key]
        if index == -1:
            return
        if index >= len(self.pieces):
            self.pieces += ['0'] * (index + 1 - len(self.pieces))
        self.pieces[index] = str(value)
    
    def __getattr__(self, key: str) -> str:
        return self[key]
    
    def __setattr__(self, key, value) -> None:
        if 'subcode_type' not in self.__dict__:
            self.__dict__['subcode_type'] = value
        elif key in self.subcode_type.names:
            self[key] = value
        else:
            self.__dict__[key] = value
    
    def __len__(self) -> int:
        return 0 if (len(self.pieces) > 1 and self.pieces[0] == '') else len(self.pieces)
    
    def clear(self) -> 'Subcode':
        '''
        Remove all data from this subcode
        
        returns self
        '''
        self.pieces = []
        return self
    
    def set(self, data: str) -> 'Subcode':
        '''
        Populate this subcode with the data in the provided string data
        
        returns self
        '''
        self.pieces = data.split('.')
        return self
    
    def merge(self, other: 'Subcode', mode: str = 'all') -> 'Subcode':
        '''
        Merge another subcode into this one
        
        returns self
        '''
        if self.subcode_type is not other.subcode_type:
            raise ValueError('Subcode Types do not match!')
        if mode == 'all' and len(other) == 0:
            self.pieces = []
            return self
        modes = mode.split('.')
        for i, other_code in enumerate(other.pieces):
            name = self.subcode_type[i]
            override = (mode == 'all') or\
                ('color' in modes and name in self.subcode_type.colors) or\
                ('pose' in modes and name in self.subcode_type.poses) or\
                ('expr' in modes and name in self.subcode_type.exprs) or\
                ('clothes' in modes and name in self.subcode_type.clothes) or\
                ('body' in modes and name in self.subcode_type.body)
            if override:
                self.pieces[i] = other_code
        return self
    
    def copy(self) -> 'Subcode':
        '''
        Returns a copy of this subcode with identical contents
        '''
        return Subcode(self.subcode_type, list(self.pieces), self.index, self.tag)
    
    @staticmethod
    def fromString(src: str) -> typing.Optional['Subcode']:
        '''
        Parse the provided string src into a subcode
        '''
        try:
            components
        except NameError:
            from . import components
        if len(src) <= 1:
            return None
        if src[1].isdigit():
            prefix: str = src[0]
            if prefix in Consts.singleDigits or len(src) == 2:
                index: int = int(src[1])
                data: str = src[2:]
            else:
                index = int(src[1:3])
                data = src[3:]
        else:
            prefix = src[:2]
            index = -1
            data = src[2:]
        component: components.ComponentType = components.ComponentType[prefix]
        subcode: SubcodeType = component[prefix][2]
        return Subcode(subcode, data.split('.'), index, prefix)

with open(os.path.join(os.path.dirname(__file__), 'subcodes.json')) as src:
    _subcodes: typing.List[SubcodeType] = SubcodeType.fromString(src.read())
    _subcodes_by_name: typing.Dict[str, SubcodeType] = dict(map(lambda x: (x.name, x), _subcodes))