import typing

from . import subcodes, components, Consts

class Chunk:
    '''
    A chunk of data within a code; delimited with asterisks
    Represents one model or scene
    '''
    def __init__(self, data: str = '') -> None:
        self.components: typing.Dict[components.ComponentType, components.Component] = {}
        self.parse(data)
    
    def parse(self, data: str) -> None:
        pieces: typing.List[str] = data.split(Consts.assetDelim)
        self.assets: typing.List[str] = pieces[1:]
        srcs: typing.List[str] = filter(lambda x: x != '', pieces[0].split('_'))
        for src in srcs:
            subcode: subcodes.Subcode = subcodes.Subcode.fromString(src)
            ctype: components.ComponentType = components.ComponentType[subcode.tag]
            if ctype not in self.components:
                self.components[ctype] = components.Component(ctype)
            self.components[ctype].add(src)
    
    def __str__(self) -> str:
        base: str = '_'.join(map(str, self.components.values()))
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
    
    def merge(self, other: 'Chunk', mode: str = 'all') -> None:
        self.assets = list(other.assets)
        for ctype, component in other.components.items():
            if ctype not in self.components:
                self.components[ctype] = components.Component(ctype)
            self.components[ctype].merge(component, mode)
    
    def copy(self) -> 'Chunk':
        new: 'Chunk' = Chunk()
        new.assets = list(self.assets)
        new.components = dict(map(lambda x: (x[0], x[1].copy()), self.components.items()))
        return new

class Code:
    def __init__(self, data: str = '') -> None:
        self.models: typing.List[typing.Optional[Chunk]] = [None] * 9
        self.scene: typing.Optinal[Chunk] = None
        self.version: int = -1
        self.parse(data)
    
    def parse(self, data: str) -> None:
        if data == '':
            return
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
    
    @staticmethod
    def convertShoe(shoe: subcodes.Subcode) -> None:
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
    
    def convertVer(self, new: int) -> None:
        if self.version >= 83 or new < 83:
            return
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
                    Code.convertShoe(clothes.jd)
                    Code.convertShoe(clothes.je)
        self.version = new
    
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
        scene: typing.Optional[Chunk] = None if self.scene is None else self.scene.copy()
        models: typing.List[typing.Optional[Chunk]] =\
            [None if x is None else x.copy() for x in self.models]
        new: 'Code' = Code()
        new.scene = scene
        new.models = models
        new.version = self.version
        return new
    
    def fastloadList(self, character: int = 0) -> typing.List[typing.List]:
        lst: typing.List[typing.List] = []
        model: Chunk = self.models[character]
        if model is not None:
            for component in model.components.values():
                for subcode in component.subcodes.values():
                    if len(subcode) == 0:
                        continue
                    lst += list(map(\
                        lambda x: (subcode.getPrefix(), x[0], x[1]),\
                        enumerate(filter(lambda y: y != '', subcode.pieces))))
        return lst
    
    def merge(self, other: 'Code') -> None:
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