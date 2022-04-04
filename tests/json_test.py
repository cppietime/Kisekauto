import asyncio

from kisekauto import mixer, imagegen


async def main():
    j = mixer.load('mixertest.json')
    print(j)
    codes = j._enumerate_codes(0, set(), set())
    print(codes)
    client = await imagegen.KisekautoClient.connect()
    scale: int = 1
    for name, code in codes.items():
        await client.apply_code(code)
        await client.save_image_to(name + '.png')
        await client.apply_to_character(code, 8)
        # await client.capture_character(name + 'char.png', 8, scale = scale)
        scale += 1
    await client.close()

asyncio.run(main())