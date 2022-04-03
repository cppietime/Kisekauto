import asyncio
import io
import sys
from typing import Tuple, Optional, Union, List
from os import path

from .kkl_client import KisekaeLocalClient, KisekaeServerRequest, KisekaeServerResponse
from .types.chunk import Code

class KisekautoClient(KisekaeLocalClient):
    def __init__(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ):
        super().__init__(reader, writer, loop)
        self.task: asyncio.Task = asyncio.create_task(self.run())

    async def close(self):
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
        data: List = code.fastloadList(source)
        request: KisekaeServerRequest =\
            KisekaeServerRequest.fastload(target, data, version = code.version)
        response: KisekaeServerResponse = await self.send_command(request)
        return check_response(response, 'Failed to apply code on character')

async def default_client(tries: int = 5) -> KisekautoClient:
    client = await KisekautoClient.connect(tries)
    # asyncio.create_task(client.run())
    return client

def check_response(response: KisekaeServerResponse, message: str) -> bool:
    if not response.is_success():
        print(message, ':', response.get_reasion(), file=sys.stderr)
        return False
    return True

def custom_code(source: Union[str, io.IOBase]) -> Code:
    if isinstance(source, IOBase):
        src: str = source.read()
    else:
        src = source
    return Code(src)

def preset_code(name: str) -> Code:
    filename: str = path.join(path.dirname(__file__), 'bank', name)
    if path.splitext(filename)[1] == '':
        filename += '.kkl'
    with open(filename) as file:
        code: Code = custom_code(file)
    return code

def body_code(name: str) -> Code:
    return preset_code(path.join('body', name))
    
def face_code(name: str) -> Code:
    return preset_code(path.join('face', name))
    
def hair_code(name: str) -> Code:
    return preset_code(path.join('hair', name))
    
def expression_code(name: str) -> Code:
    return preset_code(path.join('expression', name))
    
def clothes_code(name: str) -> Code:
    return preset_code(path.join('clothes', name))
    
def pose_code(name: str) -> Code:
    return preset_code(path.join('pose', name))
    
def scene_code(name: str) -> Code:
    return preset_code(path.join('scene', name))
    
def decoration_code(name: str) -> Code:
    return preset_code(path.join('decoration', name))