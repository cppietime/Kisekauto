from kisekauto import mixer

j = mixer.load('mixertest.json')
print(j)
print(j._enumerate_codes(0, set(), set()))