from kisekauto.types import *

c1 = chunk.Chunk('aa7.0.0.0.50.7.0.0.0.50_ab_ac_ba50_bb5.1_bc333.510.6.0.1.0_bd5_be180_ga0_gb1.0.10.40.65_gc0.0_ge0000000000_gh0_gf_gg')
c2 = chunk.Chunk('aa7.0.0.0.50.7.0.0.0.50_ab_ac_ba50_bb5.1_bc333.510.6.0.1.0_bd5_be180_ad0.0.0.0.0.0.0.0.0.0_ae1.0.0.0.0_ia2.482136.43.482136.1.8.0.0.8.0.0.7.482136.482136.0.1.7.482136.482136.482136.5_if')
c0 = c1.copy()
c1.merge(c2)
print(c0)
print(c2)
print(c1)