# __all__ = ['subcodes', 'components', 'chunk']


class GetterMeta(type):
    def __getattr__(cls, key):
        return cls.classGet(key)
    def __getitem__(cls, key):
        return cls.classGet(key)

class Consts:
    singleDigits = {'u'}
    sceneDelim = '#/]'
    assetDelim = '/#]'

from .chunk import *
from .components import *
from .subcodes import *