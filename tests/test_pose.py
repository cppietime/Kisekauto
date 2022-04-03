import asyncio

from kisekauto import *

srcbody = '''105**aa7.0.0.0.50.7.0.0.0.50_ab_ac_ba50_bb5.1_bc150.500.8.0.1.0_bd5_be180_bi0.0.100.100_bf_bg_bh1_ca65.0.30.60.34.34.34.0.0.0.60.80_da2_db_dd0.0.34.50.50.50_dh2.30.50.50.0_di5_qa_qb_dc0.1.2.2.1.0_eh1.865A2F.100_ea0.865A2F.865A2F.56.0.0_ec1.43.865A2F.865A2F.56.38.57.0_ed0.48.1.1.865A2F.56_ef_eg_r00_fa0.50.50.50.50.65.56.0_fb7_fh4_fk_fc0.50.55.0.50.55.50.61.61.50.50.50_fj0.0.0_fd0.0.50.865A2F.56.75_fe50.61_ff0000000000_fg0.50.56.0.0.1.0.0_fi_pa0.0.0.0.40.50.85.85.0.0_t00_pb_pc_pd_pe_ga1_gb1.0.10.40.65_gc0.0_ge0000000000_gh0_gf_gg_gd000000_ha89.89_hb49.1.44.99.99.49.44_hc0.59.39.0.59.39_hd0.1.49.49.2.60.50.50_ad0.0.0.0.0.0.0.0.0.0_ae1.0.0.0.0_ia0.24.43.24.0.8.0.0.8.0.0.0.0.0.0.1.125.24.24.24.3_if_ib0.55.55.55.0.0.0.1.5.0.0.5.0.0.33.0.0.0.0.1.0.1.0.0.0.0.0_id_ic0.57.57.57.0_jc0.60.0.0.1_ie_ja_jb_jf_jg_jd6.48.48.50.0.60.0.0_je6.48.48.50.0.60.0.0_ka2.0.0.0.0_kb2.0.0.0.0_kc_kd_ke_kf_kg_la_lb_oa_os_ob_oc_od_oe_of3.22.0.0.0_lc_m3071.43.0.0.2.1.26.360.620.480.3.61.26.500.0.1.1_m3171.43.0.0.2.1.54.349.600.630.3.61.54.500.0.1.1_s00_og_oh_oo_op_oq_or_om_on_ok_ol_oi_oj_f00'''

codebody = types.Code(srcbody)

srcpose = '''105**aa43.120.0.0.50.43.232.0.0.50_ab_ac_ba74_bb8.1_bc150.500.8.0.1.0_bd8_be180_bi0.0.100.100_bf_bg_bh1_ga0_gb1.0.10.40.65_gc22.28_ge0000000000_gh0_gf_gg_gd100000_ha89.89_hb17.1.44.99.99.17.44_hc0.59.39.0.59.39_hd0.1.49.49.2.60.50.66'''

codepose = types.Code(srcpose)
print(codepose)
# codepose.merge(codebody)
# print(codepose)

async def main():
    client = await imagegen.default_client()
    
    with open('ss.png', 'wb') as file:
        print(await client.apply_code(codepose, save_image=True, dest=file))
    # print(await client.apply_to_character(codepose, 0))
    print(await client.apply_to_character(codepose, 1))
    print(await client.apply_to_character(codebody, 1))
    # await client.save_image_to('test1.png', scale=  1, size = (1500, 1000), center = (100, 50))
    # await client.save_image_to('test2.png', scale=  2, size = (1500, 1000), center = (100, 50))
    # await client.save_image_to('test4.png', scale=  4, size = (1500, 1000), center = (100, 50))
    # await client.save_image_to('testH.png', scale=0.5, size = (1500, 1000), center = (100, 50))
    await client.close()

asyncio.run(main())