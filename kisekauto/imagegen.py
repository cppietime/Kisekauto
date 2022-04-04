'''
kisekauto/imagegen.py
c Yaakov Schectman 2022

Utilities for reading codes and generating images
'''

import asyncio
import io
import sys
import glob
from typing import Tuple, Optional, Union, List, Iterable
from os import path

from .kkl_client import KisekaeLocalClient, KisekaeServerRequest, KisekaeServerResponse
from .types.chunk import Code

_config_internal_path = path.join(path.dirname(__file__), 'bank')

class KisekautoClient(KisekaeLocalClient):
    '''
    A client type that extends the base client present in kkl_client and allows for async
    code upload and image download
    
    Do not call this constructor, call KisekautoClient.connect
    '''
    def __init__(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ):
        super().__init__(reader, writer, loop)
        self.task: asyncio.Task = asyncio.create_task(self.run())

    async def close(self) -> None:
        '''Closes this client'''
        self.task.cancel()
        self.writer.close()
        await self.writer.wait_closed()
    
    async def save_image_to(self,\
            dest: Union[str, io.IOBase],
            bg: bool = True,
            size: Optional[Tuple[int, int]] = None,
            center: Optional[Tuple[int, int]] = None,
            scale: Optional[float] = None,
            fast: bool = False) -> bool:
        '''
        It appears shifting is applied AFTER scaling, and I think BEFORE cropping
        
        Get a direct screenshot from the running KKL instance and save it to an image
        
        dest: either a file path or an IO object to save the returned image to
        bg: True if the background should be visible. True by default
        size: A tuple of integers to define the dimensions of the image taken in pixels
        center: A tuple of integers with the pixel coordinate of the image center
        scale: A factor by which to scale the image resolution. Overridden by size
        fast: True to use a faster but larger encoding method, False by default
        
        returns True when the image is saved successfully
        '''
        request: KisekaeServerRequest =\
            KisekaeServerRequest.direct_screenshot(bg, size, center, scale, fast)
        response: KisekaeServerResponse = await self.send_command(request)
        if check_response(response, 'Failed to retrieve image'):
            imgdata: bytes = response.get_data()
            if isinstance(dest, str):
                with open(dest, 'wb') as file:
                    file.write(imgdata)
            else:
                dest.write(imgdata)
            return True
        return False
    
    async def apply_code(self, code: Code,\
            save_image: bool = False, dest: io.IOBase = sys.stdout) -> bool:
        '''
        Upload and apply a code to the KKL server
        
        code: Code to apply
        save_image: True to save a screenshot of the result. False by default
        dest: an IO object to which to write the resulting image if saved_image is True
        
        returns True when the code is applied
        '''
        func = KisekaeServerRequest.import_full if save_image\
            else KisekaeServerRequest.import_partial
        request: KisekaeServerRequest = func(str(code))
        response: KisekaeServerResponse = await self.send_command(request)
        if not save_image:
            return check_response(response, 'Failed to apply code')
        if check_response(response, 'Failed to retrieve image'):
            dest.write(response.get_data())
            return True
        return False
    
    async def apply_to_character(self, code: Code, target: int, source: int = 0) -> bool:
        '''
        Apply a fast-loaded list from a code to a single character
        
        code: Code to apply
        target: 0-index of character to update
        source: 0-index of character to take the code from, 0 by default
        
        returns True on success
        '''
        data: List = code.fastloadList(source)
        request: KisekaeServerRequest =\
            KisekaeServerRequest.fastload(target, data, version = code.version)
        response: KisekaeServerResponse = await self.send_command(request)
        return check_response(response, 'Failed to apply code on character')
    
    async def capture_character(self,\
            dest: Union[str, io.IOBase],
            target: Union[int, Iterable[int]],\
            transforms: Optional[Union[Iterable[float], Iterable[Iterable[float]]]] = None,
            scale: Optional[float] = None,
            fast: bool = True) -> bool:
        '''
        Save a screenshot of a particular character
        
        dest: filepath or IO to save image to
        target: one or more 0-indices of character to image
        transforms: one or more linear transforms
        scale: Optional float to scale the image
        fast: True to get a result faster but larger, True by default
        
        returns True on success
        '''
        request: KisekaeServerRequest = KisekaeServerRequest.character_screenshot(\
            characters = target, matrices = transforms, base_scale = scale, fast_encode = fast)
        response: KisekaeServerResponse = await self.send_command(request)
        if check_response(response, 'Failed to save character snapshot'):
            imgdata: bytes = response.get_data()
            if isinstance(dest, str):
                with open(dest, 'wb') as file:
                    file.write(imgdata)
            else:
                dest.write(imgdata)
            return True
        return False

async def default_client(tries: int = 5) -> KisekautoClient:
    '''
    Get a default client to connect
    '''
    client = await KisekautoClient.connect(tries)
    # asyncio.create_task(client.run())
    return client

def check_response(response: KisekaeServerResponse, message: str) -> bool:
    if not response.is_success():
        print(message, ':', response.get_reasion(), file=sys.stderr)
        return False
    return True

def _glob_codes(filename: str) -> List[Code]:
    if path.splitext(filename)[1] == '':
        filename += '.kkl'
    recursive = '**' in filename
    file_matches = glob.glob(filename, recursive = recursive)
    codes: List[code] = []
    for file_match in file_matches:
        with open(file_match) as file:
            code: Code = custom_code(file)
            codes.append(code)
    return codes

def custom_code(source: Union[str, io.IOBase]) -> Code:
    '''
    Load a custom user-defined code from either a string containing it or an IO object
    '''
    if isinstance(source, io.IOBase):
        src: str = source.read()
    else:
        src = source
    return Code(src)

def custom_codes(filename: str) -> List[Code]:
    '''
    Get a list of all codes in files matching the provided glob pattern
    '''
    return _glob_codes(filename)

def config_preset_path(preset_path: str) -> None:
    '''
    Set the path used for preset codes. By default, they are stored in the module
    '''
    _config_internal_path = preset_path

def preset_code(name: str) -> List[Code]:
    '''
    Get all preset codes matching a provided pattern
    '''
    filename: str = path.join(_config_internal_path, name)
    return _glob_codes(filename)

def body_code(name: str) -> List[Code]:
    return preset_code(path.join('body', name))
    
def face_code(name: str) -> List[Code]:
    return preset_code(path.join('face', name))
    
def hair_code(name: str) -> List[Code]:
    return preset_code(path.join('hair', name))
    
def expression_code(name: str) -> List[Code]:
    return preset_code(path.join('expression', name))
    
def clothes_code(name: str) -> List[Code]:
    return preset_code(path.join('clothes', name))
    
def pose_code(name: str) -> List[Code]:
    return preset_code(path.join('pose', name))
    
def scene_code(name: str) -> List[Code]:
    return preset_code(path.join('scene', name))
    
def decoration_code(name: str) -> List[Code]:
    return preset_code(path.join('decoration', name))

def list_internal_codes(category: str) -> List[str]:
    '''
    List all preset codes in a category
    '''
    pathname:str = path.join(_config_internal_path, category, '*')
    return glob.glob(pathname)