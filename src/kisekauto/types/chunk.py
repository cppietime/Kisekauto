'''
kisekauto/types/chunk.py
c Yaakov Schectman 2022

Defines data classes for KisekaeII code chunks, and codes as a whole
'''

import typing

from . import subcodes, components, Consts

class Chunk:
    '''
    A chunk of data within a code; delimited with asterisks
    Represents one model or scene, so up to 10 chunks can be in one code
    "/#]" separates the components/subcodes of a chunk from its assets, if there are any assets
    This module does not support assets in any meaningful way
    
    data: the string from which to parse this chunk. The empty string by default
    '''
    def __init__(self, data: str = '') -> None:
        self.components: typing.Dict[components.ComponentType, components.Component] = {}
        self.parse(data)
    
    def parse(self, data: str) -> 'Chunk':
        '''
        Parse a string containing a KisekaeII code to populate this chunk
        
        data: the string from which to parse the chunk
        returns self
        '''
        pieces: typing.List[str] = data.split(Consts.assetDelim)
        self.assets: typing.List[str] = pieces[1:]
        srcs: typing.List[str] = filter(lambda x: x != '', pieces[0].split('_'))
        for src in srcs:
            subcode: subcodes.Subcode = subcodes.Subcode.fromString(src)
            ctype: components.ComponentType = components.ComponentType[subcode.tag]
            if ctype not in self.components:
                self.components[ctype] = components.Component(ctype)
            self.components[ctype].add(src)
        return self
    
    def __str__(self) -> str:
        base: str = '_'.join(filter(lambda x: x!='', map(str, self.components.values())))
        if self.assets != []:
            base += Consts.assetDelim + Consts.assetDelim.join(self.assets)
        return base
    
    def __getattr__(self, key: str) -> components.Component:
        ctype: ComponentType = components.ComponentType[key]
        if ctype not in self.components:
            self.components[ctype] = components.Component(ctype)
        return self.components.get(ctype)
    
    def __contains__(self, key: typing.Union[str, components.ComponentType]) -> bool:
        if isinstance(key, str):
            ctype: ComponentType = components.ComponentType[key]
        else:
            ctype = key
        return ctype in self.components
    
    def merge(self, other: 'Chunk', mode: str = 'all') -> 'Chunk':
        '''
        Merge attributes of another chunk into this one
        
        other: A chunk containing other attributes to merge into this one
        mode: Not really implemented right now
        returns self
        '''
        self.assets = list(other.assets)
        for ctype, component in other.components.items():
            if ctype not in self.components:
                self.components[ctype] = components.Component(ctype)
            self.components[ctype].merge(component, mode)
    
    def copy(self) -> 'Chunk':
        '''
        Returns a copy of this chunk, so you can modify the copy while preserving the original
        '''
        new: 'Chunk' = Chunk()
        new.assets = list(self.assets)
        new.components = dict(map(lambda x: (x[0], x[1].copy()), self.components.items()))
        return new
    
    def filter(self, cnames: typing.Iterable[str], skeys: typing.Iterable[str]) -> 'Chunk':
        '''
        Remove any components not in cnames, if cnames is not empty, then, for each component
        that remains, if skeys contains any subcodes for that component, retain only those
        subcodes
        
        cnames: Names of components to retain, or empty to only filter subcodes
        skeys: Keys of subcodes to retain, or empty to only filter components
        returns self
        '''
        if len(cnames) > 0:
            self.components = dict(filter(lambda x: x[0].name in cnames, self.components.items()))
        for component in self.components.values():
            subs = set(skeys).intersection(component.spec.singles.keys()).union(\
                set(skeys).intersection(component.spec.arrays.keys()))
            if len(subs) > 0:
                component.filter(subs)
        return self
    
    def exclude(self) -> 'Chunk':
        '''Voids absent subcodes'''
        for componentType in components.ComponentType.componentTypes():
            # if componentType not in self.components:
                # self.components[componentType] = components.Component(componentType)
            if componentType in self.components:
                self.components[componentType].exclude()
            

class Code:
    '''
    The entire KisekaeII import/export code
    "#/]" separates the models from the scene
    
    data: The string source from which to parse this code. The empty string by default
    '''
    def __init__(self, data: str = '') -> None:
        self.models: typing.List[typing.Optional[Chunk]] = [None] * 9
        self.scene: typing.Optinal[Chunk] = None
        self.version: int = -1
        self.parse(data)
    
    def parse(self, data: str) -> 'Code':
        '''
        Parse a code string to populate this code
        
        data: String containing the string representation of the code
        returns self
        '''
        if data == '':
            return self
        version_rest = data.split('**')[:2]
        if len(version_rest) == 1:
            self.version = 68
            rest = version_rest[0]
        else:
            self.version = int(version_rest[0])
            rest = version_rest[1]
        if rest[0] == '*': # Data is global
            self.scene = Chunk()
            rest = rest[1:]
        model_scene = rest.split(Consts.sceneDelim)
        models = model_scene[0]
        for i, model in enumerate(models.split('*')):
            if model != '0':
                self.models[i] = Chunk(model)
        if len(model_scene) > 1:
            scene = model_scene[1]
            self.scene = Chunk(scene)
        return self
    
    @staticmethod
    def _convertShoe(shoe: subcodes.Subcode) -> None:
        shoeRemap: typing.Dict[str, typing.Tuple] = {
            '0' : (None,    '1',    'Color2',   None,       'Color1'),
            '1' : (None,    '2',    'Color2',   None,       'Color3'),
            '10': ('1',     '3',    'Color2',   None,       'Color3'),
            '11': ('1',     '4',    'Color2',   None,       'Color3'),
            '15': (None,    '6',    'Color2',   None,       'Color1'),
            '16': ('1',     '7',    'Color2',   None,       'Color3'),
            '17': ('14',    '8',    'Color1',   'Color2',   'Color3'),
            '18': ('14',    '9',    'Color1',   'Color2',   'Color3'),
            '19': ('15',    '10',   'Color2',   None,       'Color3'),
            '20': ('16',    '11',   'Color2',   None,       None)
        }
        if shoe.Type in shoeRemap:
            entry: typing.Tuple = shoeRemap[shoe.Type]
            shoetype = shoe.Type if entry[0] is None else entry[0]
            top = shoe.Top if entry[1] is None else entry[1]
            topColor1 = shoe.TopColor1 if entry[2] is None else shoe[entry[2]]
            topColor2 = shoe.TopColor2 if entry[3] is None else shoe[entry[3]]
            color2 = shoe.Color2 if entry[4] is None else shoe[entry[4]]
            shoe.Type = shoetype
            shoe.Top = top
            shoe.TopColor1 = topColor1
            shoe.TopColor2 = topColor2
            shoe.Color2 = color2
    
    def convertVer(self, new: int) -> 'Code':
        '''
        Converts the version of this code to the one specified IN-PLACE (not a copy)
        This will usually do nothing more than change a number value, but may reset some attributes
        
        new: new version to which to convert
        returns self
        '''
        if self.version >= 83 or new < 83:
            return self
        for model in self.models:
            if model is not None:
                if components.ComponentType.Expression in model:
                    expr: components.Component = model.Expression
                    expr.hd.OffsetX = 50
                    expr.hd.OffsetY = 50
                    expr.hd.Rotation = 50
                clothes: components.Component = model.Clothing
                if components.ComponentType.Clothing in model:
                    clothes: components.Component = model.Clothing
                    Code._convertShoe(clothes.jd)
                    Code._convertShoe(clothes.je)
        self.version = new
        return self
    
    def __str__(self) -> str:
        string = str(self.version) + '**'
        if self.scene is not None:
            for model in self.models:
                string += '*'
                if model is None:
                    string += '0'
                else:
                    string += str(model)
            string += Consts.sceneDelim + str(self.scene)
        else:
            if self.models[0] is not None:
                string += str(self.models[0])
        return string
    
    def copy(self) -> 'Code':
        '''
        Returns a copy of this code so you can modify the copy and preserve this original
        '''
        scene: typing.Optional[Chunk] = None if self.scene is None else self.scene.copy()
        models: typing.List[typing.Optional[Chunk]] =\
            [None if x is None else x.copy() for x in self.models]
        new: 'Code' = Code()
        new.scene = scene
        new.models = models
        new.version = self.version
        return new
    
    def fastloadList(self, character: int = 0, empties: bool = False) -> typing.List[typing.List]:
        '''
        Get a list of attributes for fast-loading for a particular character
        
        character: 0-index of character to get the list of
        empties: whether to include empty attributes
        returns a list of attributes in the form [ [prefix, position, value], ... ]
        Where prefix is the prefix or tag of the subcode (e.g. aa, r0), position is the 0-indexed
        position of the piece being specified within the subcode, and value is its value
        
        Yeah just don't use this
        '''
        model: Chunk = self.models[character]
        lst: typing.List[typing.List] = []
        if model is not None:
            for component in model.components.values():
                for subcode in component.subcodes.values():
                    if len(subcode) == 0:
                        lst += [(subcode.getPrefix(), i, '') for i in\
                            range(len(subcode.subcode_type.names))]
                    else:
                        lst += list(map(\
                            lambda x: (subcode.getPrefix(), x[0], x[1]),\
                            enumerate(filter(lambda y: empties or y != '', subcode.pieces))))
        # string: str = str(model).split(Consts.assetDelim)[0]
        # subcodes: typing.List[str] = string.split('_')
        # for subcode in subcodes:
            # tag: str = subcode[0]
            # if subcode[1].isdigit():
                # if tag == 'u':
                    # tag += subcode[1]
                    # rest: str = subcode[2:]
                # else:
                    # tag += subcode[1:3]
                    # rest: str = subcode[3:]
            # else:
                # tag += subcode[1]
                # rest: str = subcode[2:]
            # pieces: List[str] = rest.split('.')
            # for i, piece in enumerate(pieces):
                # lst.append((tag, i, piece))
        return lst
    
    def merge(self, other: 'Code') -> 'Code':
        '''
        Merge the attributes of another code into this one
        
        other: Other code to merge with this
        returns self
        '''
        if self.version > other.version:
            other = other.copy()
            other.convertVer(self.version)
        elif self.version < other.version:
            self.convertVer(other.version)
        if other.scene is not None:
            if self.scene is None:
                self.scene = Chunk()
            self.scene.merge(other.scene)
        for i, (here, there) in enumerate(zip(self.models, other.models)):
            if there is not None:
                if here is None:
                    self.models[i] = Chunk()
                self.models[i].merge(there)
    
    def filter(self, keys: typing.Iterable[str]) -> 'Code':
        '''
        If any component names are present in keys, only those components are retained.
        If any subcode tags are present in keys, for each component that contains that subcode,
        only those subcodes are retaind.
        
        keys: Collection of keys to retain
        returns self
        '''
        component_names: typing.List[str] = []
        subcode_keys: typing.List[str] = []
        for key in keys:
            if components.ComponentType.isComponent(key):
                component_names.append(key)
            else:
                subcode_keys.append(key)
        for chunk in (self.scene, *self.models):
            if chunk is None:
                continue
            chunk.filter(component_names, subcode_keys)
        return self
    
    def exclude(self) -> 'Code':
        '''Voids absent subcodes'''
        # if self.scene is None:
            # self.scene = Chunk('')
        for model in self.models:
            if model is not None:
                model.exclude()
        return self