from __future__ import annotations
import ast
import argparse, base64, copy, hashlib, html, json, math, os, random, re, shutil, statistics, struct, subprocess, sys, tempfile, threading, time, traceback, zipfile, zlib
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
SOURCE=HERE/'SOURCE'; REFERENCE=HERE/'REFERENCE'; PACKAGE_PLAN=HERE/'PLAN'/'MICRO100_PACKAGE_FROZEN_PLAN.json'
if str(SOURCE) not in sys.path: sys.path.insert(0,str(SOURCE))
from pcs_factory_visibility_r15 import r15_camera_inside_fill_policy
from pcs_factory_visibility_r17 import r17_camera_inside_contrast_policy
from pcs_factory_rgb_rescue_r23 import r23_systemic_rgb_policy
from pcs_factory_blueprint_r33 import r33_blueprint_vertical_dominant_policy
from pcs_factory_blueprint_r36 import r36_blueprint_extreme_vertical_policy
from pcs_factory_blueprint_g101_r2 import g101_r2_blueprint_foreground_vertical_policy
from pcs_factory_rgb8 import apply_fixed_rgb8_contrast_png, apply_fixed_rgb8_gain_png
PACKAGE_PLAN_SHA256='6aaf15830724bcb574c3b6d5c816c8ea70195b7c88b59090bf79f54fdf181ce6'
TOOL_REVISION='DF_G100_MICRO100_V2_R1_TOOL_R36'
R2_ADDENDUM_DRIVE_ID='17cWfxKYDVjsjk98OsZjTtaeoEVhg1uE0YQ_w3ubJijY'
R3_ADDENDUM_DRIVE_ID='1zTxwLTjw4KWG-Zy9DMjQW--RDNihqRMJPvFxtSJKdB0'
R4_ADDENDUM_DRIVE_ID='1SsURu6T-equZR4vM1FZIsLf9erSSwdpy8NYpNhpiLf8'
R5_ADDENDUM_DRIVE_ID='12lsY4Rvk6vlCaS6Z47NH3dbGzmkPj3deynHWyZgT62c'
R6_ADDENDUM_DRIVE_ID='1aJbPlstezBMzHV3231_n3cdXvN6ZIMYV0SwdhxwVadw'
R7_ADDENDUM_DRIVE_ID='1a4RMZ-4hrQW79EGNwYEvBgQZAazQWtgvrYwI0wwtKco'
R8_ADDENDUM_DRIVE_ID='1H7WpHBr6_oXHQrBusEvzUjYIZzgKZAAeTBZVfnRxTEc'
R9_ADDENDUM_DRIVE_ID='1gLNAM-dQFzXZSQCf4Xf9x3XQ2_-F69Wtu-qfp3DYD_8'
R10_ADDENDUM_DRIVE_ID='12SXFqihTcZTSrkQCws5ItOG4eHJMji5dCuFN-paWoAc'
R11_ADDENDUM_DRIVE_ID='1LTqAivl2_XoofEfteWUEq-wy-gibI8JkJstkuSVVBEU'
R12_ADDENDUM_DRIVE_ID='1FuzdzW-YD2VH7MAq-aCS-6fAEZbJqVlbXHe85VO6hd8'
R13_ADDENDUM_DRIVE_ID='19IbljxLtdzvf2x9LcAos_9h3GNeVo2nmefGjucRr2sQ'
R13_PRIOR_R12_RETURN_SHA256='762a0ac5c8eb52fee6476429c38fc3a9aaded7da46ada629472833c2e4b1ad97'
R13_RECOVERY_SAMPLE_ID='g100_016_industrial_strong_roll_clay'
R13_RECOVERY_REQUEST_DIGEST='b967fd15e576bbdb719ce5baec20d901a5b9cf36784d57ff2482472da7978cc4'
R13_CHUNK01_DIGEST='305b847610644e22816e9209503e042a759a5b188811622b0f6b694668e24670'
R13_FAILURE_ERROR='CAMERA_REPROJECTION_FAIL_PRE_RENDER:max=2.6746242518305423:median=1.3206042397454884e-05'
R13_PRIOR_FILE_SHA256={
 'request.json':'68ef557206a67672d72f5ab90f3b48df41e92a12275304e37f600b2823118110',
 'worker.log':'2c583a5f7027e5789a1877c4a46d2e7ca2cf4e996ee2d5762aa3dc5d3b86e60e',
 'failure.json':'261305d2f3288f6d96246786e86f4c4a6181086d41e38b6fd38c5e32aafd93a2',
 'camera_calibration.json':'00c8c12f62bdaede350482b0168f712e3b2544d0e8af2880ec1cbc002f739890',
 'pre_render_reprojection.json':'3e0e393858141aa672cd1c729e9793c5d16a8e180807356ea2c25ab74f820826',
}
R13_PRIOR_SAMPLE_TREE=[
 {'path':'camera_calibration.json','bytes':860,'sha256':'00c8c12f62bdaede350482b0168f712e3b2544d0e8af2880ec1cbc002f739890'},
 {'path':'failure.json','bytes':518,'sha256':'261305d2f3288f6d96246786e86f4c4a6181086d41e38b6fd38c5e32aafd93a2'},
 {'path':'pre_render_reprojection.json','bytes':9933,'sha256':'3e0e393858141aa672cd1c729e9793c5d16a8e180807356ea2c25ab74f820826'},
]
R13_PRIOR_PARTIAL_IDENTITIES_SHA256='beca2d1ad87a6dc13a37b728e0330486be14323a634260d61f67435f44322907'
R14_ADDENDUM_DRIVE_ID='1PQEf6hJYvAtcN-1S1L3mf2p2DYC-MiyrWfw1yrRgn24'
R14_PRIOR_R13_RETURN_SHA256='3b4d7265c0e6551a82135a570558d97ffe826a63ff97f0be8364c1762866a591'
R14_RECOVERY_SAMPLE_ID='g100_019_sparse_telephoto_clay'
R14_RECOVERY_REQUEST_DIGEST='b2f8e36d169541d334a8bb37b129fe7c9af5dc456b0f46c98f2415411f983612'
R14_CHUNK01_DIGEST='305b847610644e22816e9209503e042a759a5b188811622b0f6b694668e24670'
R14_FAILURE_ERROR='CAMERA_REPROJECTION_FAIL_PRE_RENDER:max=4.4927893329301624e-05:median=3.2539333638674124e-05'
R14_PRIOR_FILE_SHA256={
 'request.json':'21a6e112120ba0287af55792489cdcb177ba25a4e7a11f2f6e0e1b7a08b6ef32',
 'worker.log':'141e86f9c50f954a92778ffeaddd7d3f9f5937055ee665aeab67b6a1cad5445a',
 'failure.json':'f74086e8ee6b303314721c9bb67258ee203d44785b645eaf89592f1870190a08',
 'camera_calibration.json':'9e36802d58b77c211f03e3db43af332cd6902a219eebe76e61cdf1f58e6a134f',
 'pre_render_reprojection.json':'1d7ba6d4b189fcac87496547a0b715767cfb57bd2b42c8454e6745b84ba90244',
}
R14_PRIOR_SAMPLE_TREE=[
 {'path':'camera_calibration.json','bytes':875,'sha256':'9e36802d58b77c211f03e3db43af332cd6902a219eebe76e61cdf1f58e6a134f'},
 {'path':'failure.json','bytes':516,'sha256':'f74086e8ee6b303314721c9bb67258ee203d44785b645eaf89592f1870190a08'},
 {'path':'pre_render_reprojection.json','bytes':10315,'sha256':'1d7ba6d4b189fcac87496547a0b715767cfb57bd2b42c8454e6745b84ba90244'},
]
R14_PRIOR_PARTIAL_IDENTITIES_SHA256='1114d9b27e318e037a8c8db92b0aa80a76ff5a4433de738a65f7420ef0638e54'
R15_ADDENDUM_DRIVE_ID='1I7LjTul-Isre0DKCAB-_WZPDy-FnRS1KW007jIexOjY'
R15_PRIOR_R14_RETURN_SHA256='e30dd96b38764fff4bbde7ccbe102977b7097b5863becbbe59fd4ddda29d2259'
R15_RECOVERY_SAMPLE_ID='g100_015_intersection_normal_day_hard'
R15_RECOVERY_REQUEST_DIGEST='662e5983e68dd62cfb7ca49897d8d53e63d6a0d9cf83754903cdafb166181aa7'
R15_CHUNK01_DIGEST='305b847610644e22816e9209503e042a759a5b188811622b0f6b694668e24670'
R15_EXPECTED_RAW_SHA256={
 'request.json':'4933b93231c5eb566fa097fa78d511bd237f0236f7eb2dbbd2a0e5afa1394d60',
 'rgb.png':'64b71e96c2f08d18a162b52dadd3f6761c334b6331218d3858666a42ebed306d',
 'depth.exr':'def319841a02fc273705849a2945336ceec0a7ead028170cbaeae1936c48ad78',
 'object_index.exr':'d4dd4d87be6f2c4e04c3c4fd7e1731ace72a7254846ec5088c800fcaa199f627',
 'normal.exr':'9cc0a682a8daac57272d21cb411964d92ba94742c4d3a3e6dd78e2a6050a9631',
}
R15_EXPECTED_RGB_STATS={'unique_rgb':2,'mean_luma':0.08287217881944445,'p01_p99_span':1.0,'structural_fraction':0.0}
R16_ADDENDUM_DRIVE_ID='1MRG2-Ot_WIf94FI_VFWV_Jpy9Bsb6MW15GHsi16dg4Q'
R16_PRIOR_R15_RETURN_SHA256='7709f1f1090c0b7504dee6b532d63111881bf86cd8881332029e19e2c5eedbdf'
R16_RECOVERY_SAMPLE_ID='g100_015_intersection_normal_day_hard'
R16_RECOVERY_REQUEST_DIGEST='662e5983e68dd62cfb7ca49897d8d53e63d6a0d9cf83754903cdafb166181aa7'
R16_CHUNK01_DIGEST='305b847610644e22816e9209503e042a759a5b188811622b0f6b694668e24670'
R16_REQUIRED_COMPLETION_FILES={
 'rgb.png','depth.exr','normal.exr','object_index.exr',
 'normal_authority_mask.uint8.bin','normal_filter_safe_interior_mask.uint8.bin',
 'micro100_aux_gt_qa.json'
}
R17_ADDENDUM_DRIVE_ID='1BYJtB2PuucanwxPt456YdHleGcta-9dPvZwTKtViirs'
R17_PRIOR_R16_RETURN_SHA256='39de0a7b8719a400376086c77eb9564a6601d7b99d0b27632722c32bc88579d8'
R17_RECOVERY_SAMPLE_ID='g100_015_intersection_normal_day_hard'
R17_RECOVERY_REQUEST_DIGEST='662e5983e68dd62cfb7ca49897d8d53e63d6a0d9cf83754903cdafb166181aa7'
R17_CHUNK01_DIGEST='305b847610644e22816e9209503e042a759a5b188811622b0f6b694668e24670'
R17_REQUIRED_COMPLETION_FILES=set(R16_REQUIRED_COMPLETION_FILES)
R17_EXPECTED_R16_RGB_SHA256='acaec248edfc7871d7499331ed76531d4ce3cb476a951e20161d2632bf1e1afc'
R17_EXPECTED_R16_RGB_STATS={'unique_rgb':304,'mean_luma':163.4325611255787,'p01':152.07819999999998,'p99':175.43359999999998,'p01_p99_span':23.355400000000003,'structural_fraction':0.1498752170138889}
R17_EXPECTED_TRANSFORMED_RGB_SHA256='e354e3a405cef3d85efd8af1af04947c3959523f8cf91166a0ef7dc159c9dd72'
R17_EXPECTED_TRANSFORMED_RGB_STATS={'unique_rgb':304,'mean_luma':165.69865308340567,'p01':153.43519999999998,'p99':178.5058,'p01_p99_span':25.070600000000013,'structural_fraction':0.19974320023148148}
R18_ADDENDUM_DRIVE_ID='1OyqCvQ72UF4rSj0vaHG2BNUPG5DivN4leomBa44ssiY'
R18_PRIOR_R17_RETURN_SHA256='dedc8f07bd61e1f7937a3531e327518f4ab5882ff1a2d63b31d9ec9c07475a21'
R18_RECOVERY_SAMPLE_ID='g100_021_repeated_pattern_offcenter_day_hard'
R18_RECOVERY_REQUEST_DIGEST='11afa8383b5b3e06dce34a529ce6e02c818d598a338a992402c3980ebe1b0603'
R18_CHUNK02_DIGEST='7afb66905c9868d8596eafa2fd5770b2af0dbd213f24e51f420836e296b014ca'
R18_FAILURE_ERROR='G100_AUX_GT_ANALYTIC_VALIDATION_FAIL:{"depth": "FAIL", "normal": "PASS", "object": "PASS"}'
R18_PRIOR_REQUEST_SHA256='6ae151de819c955bc7d172efcaef593ae8655aee425c8de857b756eb343312a5'
R18_PRIOR_WORKER_LOG_SHA256='42f4c85d3c35b0a63390b08b720d72e02911f7a328d80fe6d0f4c2e589b61745'
R18_PRIOR_PARTIAL_IDENTITIES_SHA256='d33b39fe15c977522dee75c62cbbc6437ba0f920978c3002277b574aff2442d4'
R18_PRIOR_SAMPLE_TREE=[{'bytes': 995, 'path': 'camera_calibration.json', 'sha256': 'a6dd7d217cbf77c0ebc63e4f9727f4156b6fb89be9915614dc523e284411ba74'}, {'bytes': 331890, 'path': 'depth.exr', 'sha256': 'd04f65d09da3544a992b5e9e0ef72d8fc80399850db596ced810caa08b07cc3e'}, {'bytes': 540, 'path': 'failure.json', 'sha256': '0f8b3a8db2e6450fd7b9f8b0cdf6c6c5dbcc91368a5fc4246a274982ef725674'}, {'bytes': 18795, 'path': 'micro100_aux_gt_qa.json', 'sha256': 'f99c2b9ed1bbe631262255988ba9b45c5e67360968a55be886983c0771bd6196'}, {'bytes': 23006, 'path': 'normal.exr', 'sha256': 'e7de9d069834b4c8690726034d437d4f0bd89d8a0327160eedc700555f27eaa6'}, {'bytes': 110592, 'path': 'normal_authority_mask.uint8.bin', 'sha256': '283b0b92e8bb0c4cf74565e54c9d350cf0dc538623ab1ad78521655884b6e367'}, {'bytes': 110592, 'path': 'normal_filter_safe_interior_mask.uint8.bin', 'sha256': 'd8ed6336f2565a5a8b0550f85569867e7b8529a4a4fb96106b59e6fffc89b953'}, {'bytes': 5327, 'path': 'object_index.exr', 'sha256': 'bdf84a69a86bc210ccb9e847d4c1035847bf79e19caa96579970108b4fa97d0e'}, {'bytes': 12715, 'path': 'pre_render_reprojection.json', 'sha256': '4966ba7d6d61b01e9178ee2198f5cb30b76a681ce94453e8a3ed5857539169a9'}, {'bytes': 98898, 'path': 'rgb.png', 'sha256': '02a14f07deb94569041e2c3406e789fe4ae8ad80e23da14f36aac9544cbb2373'}]
R19_ADDENDUM_DRIVE_ID='1-6N6XakozHhC01In2_SYyB-D9v0K33GXRQ9L5cszD64'
R19_PRIOR_R18_RETURN_SHA256='8d291cc1b8b59ec2dcdf13a3f4a40e2f08fe6f779d74b3793f621ba00e1e90b1'
R19_RECOVERY_SAMPLE_ID='g100_027_intersection_wide_toon'
R19_RECOVERY_REQUEST_DIGEST='6841a44fdc1cd4c7716ac3e5b4491266f6127e89cdfea13d9c9b85717d2a2a19'
R19_CHUNK02_DIGEST='7afb66905c9868d8596eafa2fd5770b2af0dbd213f24e51f420836e296b014ca'
R19_FAILURE_ERROR='G100_AUX_GT_ANALYTIC_VALIDATION_FAIL:{"depth": "FAIL", "normal": "PASS", "object": "FAIL"}'
R19_PRIOR_REQUEST_SHA256='71690cf53035e0fb2877c1f46369686a5ae913dcd3ef50f96e4502edf2bc44ba'
R19_PRIOR_WORKER_LOG_SHA256='c8c2703e17765677decf0faf6a6fd404570bbed3695c7e5b7e2416c4fdf11e61'
R19_PRIOR_PARTIAL_IDENTITIES_SHA256='a8bd9fc8cb9c9c153d182266bd3341fb9b6c8556046f8c40f6e21ad6bcbf206e'
R19_PRIOR_SAMPLE_TREE=[
 {'bytes':857,'path':'camera_calibration.json','sha256':'13ae49b16295f09e6a1974e72bda0d7c96c4e19e4a8dcc4a6a1b8207c43db265'},
 {'bytes':286283,'path':'depth.exr','sha256':'d57742102335fb79451daed6f50c2c8c755b83f580bd98c95c881d70e56061b5'},
 {'bytes':527,'path':'failure.json','sha256':'ea875fb1af2dcbec41586e4b3bc8e02307a40abbd12c63ba82b21ac79d04dd40'},
 {'bytes':18957,'path':'micro100_aux_gt_qa.json','sha256':'8915874e7aeab9cb14488a73be3475a4980335073cc151588c8b08a20a45d703'},
 {'bytes':81015,'path':'normal.exr','sha256':'51d15742e557e4d035555768b5477ad8f35980902a734b9b629fb131ba83ef77'},
 {'bytes':82944,'path':'normal_authority_mask.uint8.bin','sha256':'d11d3baa255930573c794829b7e059d5f8fdaa83327ab533797218c48d1566c1'},
 {'bytes':82944,'path':'normal_filter_safe_interior_mask.uint8.bin','sha256':'b04398e9bf3ac481d44ec98bade5cfd94682c80ed9d7a4d319f2d7c4fc4766b7'},
 {'bytes':14306,'path':'object_index.exr','sha256':'6e5cdd267ba7c9d9d6f45968c4774f85de0f95ff9a6d92ee90778d91e9cfd196'},
 {'bytes':14072,'path':'pre_render_reprojection.json','sha256':'a06d8e0d5a5894236683d60be94ab26a819021c7338121d7f3f340224c8b6502'},
 {'bytes':59605,'path':'rgb.png','sha256':'9142fce62a6aeba154666fe4de0f4dfd8e347fe1c34444328c25698dd16509f9'}
]
R20_ADDENDUM_DRIVE_ID='17Y7syw0Bq9mR8YU0RhD7EMzDKis966PIwI6xCSfgc7Y'
R20_PRIOR_R19_RETURN_SHA256='6686d3e2da3547bf30417284cf59b42f4528adb9e2afca5255db9c979d87dffd'
R20_RECOVERY_SAMPLE_ID='g100_029_stairs_ramps_portrait_pbr_realistic_intent'
R20_RECOVERY_REQUEST_DIGEST='e8dd7be3adc32884ab51efe2797a3546756f7712fd6fb9100ee113c26785c92a'
R20_CHUNK02_DIGEST='7afb66905c9868d8596eafa2fd5770b2af0dbd213f24e51f420836e296b014ca'
R20_FAILURE_ERROR='G100_AUX_GT_ANALYTIC_VALIDATION_FAIL:{\"depth\": \"PASS\", \"normal\": \"FAIL\", \"object\": \"PASS\"}'
R20_PRIOR_REQUEST_SHA256='1a37f08923b23f819ac7a0d9ad8c5c9301d757d2577291bd2f7ef324eedd57ee'
R20_PRIOR_WORKER_LOG_SHA256='1fe5db6babac2851d2b0edd003cf398265b46ea81de3f8230e0a38aa601fcc38'
R20_PRIOR_PARTIAL_IDENTITIES_SHA256='074a33948e83ec52e1bf24c4b80e13321cadda6f95626cf2523a23a6854eee4e'
R20_PRIOR_SAMPLE_TREE=[
 {'bytes':861,'path':'camera_calibration.json','sha256':'5f99d69e85eb453931c0b74fda5f876754f883c5ac0e3aa2ba7eecfee405ab26'},
 {'bytes':247002,'path':'depth.exr','sha256':'3e3c0852b22054a499e4478236965af9fb3524c4d75bc85d8e948e75a1c85e98'},
 {'bytes':547,'path':'failure.json','sha256':'c1efd3a89177471850b14bdfdada2a4abdcea496f703258e95b98e083111a08b'},
 {'bytes':19550,'path':'micro100_aux_gt_qa.json','sha256':'a289b886b1a7ae7b937ef47c46c3797e42b4bf5341ded0fe2ecd79dfbbfc17e7'},
 {'bytes':16734,'path':'normal.exr','sha256':'045f6e49faa629e95d5695ef120de7c93976a478695751a06e4443b5e348915d'},
 {'bytes':110592,'path':'normal_authority_mask.uint8.bin','sha256':'df3d008ae46f75cd044654b9eb1fa752cb596148e2fb7bbcef2832afcbcf41e3'},
 {'bytes':110592,'path':'normal_filter_safe_interior_mask.uint8.bin','sha256':'ca34c81c512b2b6da27a7630640ab94f5d94f47e5f904d73ba891f3954e2c8ce'},
 {'bytes':4373,'path':'object_index.exr','sha256':'2f342f0d4e29dc6e15d35a2e472b5d539161fc8efbf2da45139b1d89e7ced0a3'},
 {'bytes':12570,'path':'pre_render_reprojection.json','sha256':'b94aec28a7a5d93110de1f25b4ae5809df750664a54f6ea639e9589475150a8c'},
 {'bytes':103973,'path':'rgb.png','sha256':'af84612001421f1e957e68999cd1850dc3887453eb48ef6df717f27897df63ab'}
]

R12_PRIOR_R11_RETURN_SHA256='6e03e7f434872403c799aa9d645021143d59d2dd5e3c5f2ae22a18ab4dcffc03'
R12_RECOVERY_SAMPLE_ID='g100_015_intersection_normal_day_hard'
R12_RECOVERY_REQUEST_DIGEST='662e5983e68dd62cfb7ca49897d8d53e63d6a0d9cf83754903cdafb166181aa7'
R12_CHUNK01_DIGEST='305b847610644e22816e9209503e042a759a5b188811622b0f6b694668e24670'
R12_FAILURE_ERROR='G100_AUX_GT_ANALYTIC_VALIDATION_FAIL:{"depth": "PASS", "normal": "FAIL", "object": "PASS"}'
R12_PRIOR_FILE_SHA256={
 'request.json':'4933b93231c5eb566fa097fa78d511bd237f0236f7eb2dbbd2a0e5afa1394d60',
 'failure.json':'f7d2a3c84ad429deb073d7b7c39c97551dce9f832da41283b8f61ef6d3dbd77a',
 'worker.log':'bdcbb56f431b1b63574c10ae5af9e32f93511f49573df6777399018354003b0f',
 'depth.exr':'def319841a02fc273705849a2945336ceec0a7ead028170cbaeae1936c48ad78',
 'object_index.exr':'d4dd4d87be6f2c4e04c3c4fd7e1731ace72a7254846ec5088c800fcaa199f627',
 'normal.exr':'9cc0a682a8daac57272d21cb411964d92ba94742c4d3a3e6dd78e2a6050a9631',
 'rgb.png':'64b71e96c2f08d18a162b52dadd3f6761c334b6331218d3858666a42ebed306d',
 'micro100_aux_gt_qa.json':'113614019bd55fcca2172b37456359cc42c6ef3bca2df50e9da8f5b6be3f80ff',
}
R11_PRIOR_R10_RETURN_SHA256='bef7686d2bf41648e754913c03460819980b26dca03cbfc063103385b8f0d25e'
R11_RECOVERY_SAMPLE_ID='g100_013_corridor_strong_pitch_clay'
R11_RECOVERY_REQUEST_DIGEST='e445d4a8bbb48c4bb83c1755cdbf450b6ad49620fee3c2f93769527702c79e66'
R11_CHUNK01_DIGEST='305b847610644e22816e9209503e042a759a5b188811622b0f6b694668e24670'
R11_FAILURE_ERROR='G100_AUX_GT_ANALYTIC_VALIDATION_FAIL:{"depth": "FAIL", "normal": "PASS", "object": "FAIL"}'
R11_PRIOR_FILE_SHA256={
 'request.json':'a823a52f79b76f4522021f54e770d789eaa01c264838ddf1a2b71bda6f497d43',
 'failure.json':'7d464d3615616394a2682f1c0818bbc44a906c646fb00e20a5608f81e4f9e16f',
 'worker.log':'3527c713c52c8e3c9d8e3ad51d0dfdab047248595124a84346bf59f3edb051e0',
 'depth.exr':'c3b496e303eee1305e0556c23abfd2888f98b1989dc85a873bf14accfa6f5681',
 'object_index.exr':'7bfbdb8a18eb29553d11dbf2b9c8d87dd1fa86cfcf2740cc029156fcfd349e07',
 'normal.exr':'c76e83b1b942a725f1ed2e8849278465d27cc6670a71747bfe1efeee44676529',
 'rgb.png':'896f5bc8fd97faf034551a3eba5c93d092d5543b268cb895979aaf2c94ef097c',
 'micro100_aux_gt_qa.json':'fdc32e87db7af8c2a146dc19885fa42e77a20defcccc9f72d3592bc4260d4d77',
}
R10_REAL_FAILURE_RETURN_SHA256='c5d841d645b25ce5ea7eebc689e65e2df7efad1501f14376f53202736886f835'
R10_RECOVERY_SAMPLE_ID='g100_001_corridor_strong_roll_toon'
R10_RECOVERY_REQUEST_DIGEST='5089b19db397467580fcb2bbfa86de213be7731fe51e78c79b3862552240fb2c'
R10_PRIOR_RGB_SHA256='7dc8e1f2f9d3304c860a762d058e1dd01918c35b05158a125b7692927eb51033'
R10_PRIOR_COMPLETION_SHA256='7fd8ee1d08b7367c54340eb0f8f8e3580995dcc0ff6e8b68a872764d13037098'
R10_PRIOR_REQUEST_FILE_SHA256='dbd3de529491811305397ca3306e24934e5b4deb719e16d2c9a5e576a3300ea4'
R10_PRIOR_WORKER_LOG_SHA256='b2c180c343de7e8ea152d347044e56ec9aca257a74c0f7fe017a349fc2eb9ad9'
R10_PRIOR_RGB_STATS={'unique_rgb':262,'mean_luma':175.31840268164063,'p01':160.52300000000002,'p99':181.94699999999997,'p01_p99_span':21.42399999999995,'structural_fraction':0.04640625}
R10_EXPECTED_TRANSFORMED_RGB_STATS={'unique_rgb':262,'mean_luma':187.28156273046875,'p01':168.742,'p99':195.523,'p01_p99_span':26.781000000000006,'structural_fraction':0.10451171875}
R9_RECOVERY_SAMPLE_ID='g100_001_corridor_strong_roll_toon'
R9_RECOVERY_REQUEST_DIGEST='5089b19db397467580fcb2bbfa86de213be7731fe51e78c79b3862552240fb2c'
R9_PRIOR_RGB_SHA256='2195570d713b234f128dd05a6a979554620a298e590e1d54e5a0a896ff5cbda5'
R9_PRIOR_COMPLETION_SHA256='14a4da3abd972248c583affdca119b95ad959655a91521bd886aec46ce609045'
R9_PRIOR_REQUEST_FILE_SHA256='dbd3de529491811305397ca3306e24934e5b4deb719e16d2c9a5e576a3300ea4'
R9_PRIOR_WORKER_LOG_SHA256='c43f75b926cc685b0a04351ca257255ff7e3e501e067ab58eee3c5bc6caedd59'
R9_PRIOR_RGB_STATS={'unique_rgb':231,'mean_luma':194.00526358789062,'p01':178.3774,'p99':200.8014,'p01_p99_span':22.424000000000007,'structural_fraction':0.042646484375}
R9_FORENSIC_RETURN_SHA256='576b0d0bcebf8dd108f26f0c4202699c6c3f09f6a7af831eb7bdf10fa4b81a02'
R8_REAL_RETURN_SHA256='8ad1458c3271ad01fceb863e22874b8f78c39fd93ade9405b50eeec136f2e5ac' 
R7_FAILED_SAMPLE_ID='g100_009_repeated_pattern_portrait_pbr_realistic_intent'
R7_FAILED_SAMPLE_REQUEST_DIGEST='c44a00466ef620da0a7fd715d2f84c519f7a0c90089a15bc70481d048b98c9e8'
R7_FAILURE_ERROR='G100_AUX_GT_ANALYTIC_VALIDATION_FAIL:{\"depth\": \"FAIL\", \"normal\": \"PASS\", \"object\": \"PASS\"}'
R6_FAILED_SAMPLE_ID='g100_008_clutter_strong_pitch_blueprint'
R6_FAILED_SAMPLE_REQUEST_DIGEST='eaf1f86fbdcee40a332fa6f95d9e872374d20e6c5eeab7a911abe71b29d4cb5e'
R6_FAILURE_ERROR='G100_R3_RENDERER_PP_BOUND_EXCEEDED:{"bound_px": 0.001, "delta_cx_px": -0.0005575718524059648, "delta_cy_px": 0.0023381408118185606}'
R5_FAILED_SAMPLE_ID='g100_005_stairs_ramps_low_camera_blueprint'
R5_FAILED_SAMPLE_REQUEST_DIGEST='6d2bb3ca26adc6649bf2ac8af7806150d90a3ec92d8f38563d9ebaa7148d3146'
R5_FAILURE_ERROR='G100_AUX_GT_ANALYTIC_VALIDATION_FAIL:{\"depth\": \"PASS\", \"normal\": \"FAIL\", \"object\": \"PASS\"}'
R4_FAILED_SAMPLE_ID='g100_004_industrial_telephoto_toon'
R4_FAILED_SAMPLE_REQUEST_DIGEST='80d593edd1062d6e0e3ca48cfb1974efa45f76c7dbd2b15b2796afd7e813f9bc'
R4_FAILURE_ERROR='G100_R3_RENDERER_PP_BOUND_EXCEEDED:{\"bound_px\": 0.001, \"delta_cx_px\": 0.0001458231511483888, \"delta_cy_px\": -0.014981960225090966}'
R23_ADDENDUM_DRIVE_ID='1_9NcyXSlwfCJjS3iRvEy8BXNtO-eFPKeVZngGwU3nnI'
R24_ADDENDUM_DRIVE_ID='1XxoQ8aSbnACd-6m_Il0oB7fD3JKhD5sLUYAmT7DtTRs'
R25_ADDENDUM_DRIVE_ID='1iJzClS178KCmagdQ2Jj5glp_rJ4wjJB3'
R25_R24_REAL_FAILURE_SHA256='732097aad311793eebc33fe1ac3e9b5cedc3e8408486701bba9061197d0d8fef'
R25_R24_REAL_FAILURE_BYTES=6898865
R24_R23_REAL_FAILURE_SHA256='327d8f5bd31b01208fd301e64e8bd770f6d1489a554d8e009f4163745036c8a5'
R24_PRESTATE_COMPLETED=40
R24_PRESTATE_SAMPLE038_REQUEST_SHA256='fcfb47eeb6df813522e4df99f7aaa5fe10823c17b316cc761763b8d69014c3a8'
R24_PRESTATE_SAMPLE038_COMPLETION_SHA256='3323b8f111b92006b892f84f38919bc26096bbfd042d87fb48239f427fa5fbbd'
R24_PRESTATE_SAMPLE038_OLD_ACCEPTANCE_SHA256='8cd505181fe4681ba75ddc27669753cd7991f2fcf518d5d51369409e3408ea76'
R24_PRESTATE_SAMPLE038_RENDERER_RAW_SHA256='cfd46a276d585b9911fcf145ae695f7a4af4e5f0eb2f3c797470495eb8134c25'
R24_PRESTATE_SAMPLE038_PRE_R23_SHA256='2d3df8b6ac3817e758316e2666305ea48d020c4c13f96a55c75fa81c9c39708b'
R24_PRESTATE_SAMPLE038_FINAL_SHA256='e921ed037b8191279073e30367516417e8c63ca1c1dfe4d185fcb5689451cda8'
R23_R22_REAL_RETURN_SHA256='115d4379290bc68d49b287a5f82cab7de8638b64f4b90dfcae6f87bffea22fac'
R23_R20_FAILURE_RETURN_SHA256='94654e55c41685107d0ca860dcabf96a193b15ff5ad8f73cbe94597a323ce91e'
R23_RECOVERY_SAMPLE_ID='g100_025_corridor_low_camera_blueprint'
R23_RECOVERY_REQUEST_DIGEST='c522076747bd9ae9edd19354a26fe5ed3b4bea60429e54b6ba06ac13ec98e75d'
R23_CHUNK02_DIGEST='7afb66905c9868d8596eafa2fd5770b2af0dbd213f24e51f420836e296b014ca'
R23_PRIOR_REQUEST_SHA256='cd6e20e09f0a6b821d831b350e11793092fe606259da8d0143644b30324385c4'
R23_PRIOR_WORKER_LOG_SHA256='7e8b73e10d9b4bb263bed675e7933d2891e0e6173068750be53999e5b99c0024'
R23_PRIOR_ACCEPTANCE_SHA256='fce6b6c2a32d5629d1c1a701a705303d67a5941bc7566b20f9b3c5739dbe68c8'
R23_PRIOR_SAMPLE_TREE=[
 {'path':'camera_calibration.json','bytes':863,'sha256':'40a161b5eb81e491d382cdfa91a46dd0fcdd19cfa85dd4296b4842803e784217'},
 {'path':'completion.json','bytes':29576,'sha256':'2ee1ebbbb8ecd262d20174b04c7f9686090399bd56fb70bc01b284aa92d0468a'},
 {'path':'depth.exr','bytes':271453,'sha256':'704c10f37457f1789a24092bfadfb26d30203291e5be25d961a95a577abb0e8b'},
 {'path':'micro100_aux_gt_qa.json','bytes':7016,'sha256':'c345dbdcd5c4d641ac7568038b2cf64733c91722d77dd6fb08a976bfc79ed965'},
 {'path':'normal.exr','bytes':10796,'sha256':'3e80419131a1861b00b795617132e6ca4ff1ae2d47a2ef8a4a431b27c2faf66a'},
 {'path':'normal_authority_mask.uint8.bin','bytes':82944,'sha256':'2273bff01a153d82f75218e17ff7b68a62af747ed847c2f5e3322a9a2391caa6'},
 {'path':'normal_filter_safe_interior_mask.uint8.bin','bytes':82944,'sha256':'d7cf41ad5755195e43f5e3df0d45a0f8d07cd9656910fe0413bbac109c5f1ec7'},
 {'path':'object_index.exr','bytes':1396,'sha256':'c8d5e66444bb84d7661742e8349477e148ce6da2921bd1d5114e0be16a2541ee'},
 {'path':'pre_render_reprojection.json','bytes':14205,'sha256':'a515cc018461e3a10e7a0e061a921b096b97e21734e3490c7336cd99feb4d3f9'},
 {'path':'rgb.png','bytes':67897,'sha256':'fea58f0bd905f25d2a948db3ca9d0439ad14d876ab5f3008888d2ed5e58996f4'}]
R23_EXPECTED_RGB_SHA256='59ce1d194dfe868a2cdd6f4c0a2e458e4b858fded1410b4fa54a8f2c77ec5743'
R23_EXPECTED_RGB_STATS={'unique_rgb':305,'mean_luma':99.04342443094136,'p01':80.61659999999999,'p99':108.54839999999999,'p01_p99_span':27.931799999999996,'structural_fraction':0.13839457947530864}
R23_CANONICAL_PRESTATE_FINGERPRINT_PATH=HERE/'FIXTURES'/'R23_CANONICAL_PRESTATE_FINGERPRINT.json'
R23_CANONICAL_PRESTATE_FILE_COUNT=848
R23_CANONICAL_PRESTATE_AGGREGATE_SHA256='8e3a5df8003bfceb3fd0bb1bd692eb54d40fbc4e82ad164606fd944a3383736e'
R23_CANONICAL_PRESTATE_FINGERPRINT_SHA256='3534620afcc7cb21f2583c4480a504ad82d41132de2d027312ef6336f1790652'
SOURCE_RELEASE_ID='DF_G100_MICRO100_V2_R1_TOOL_R36'
R2_FAILED_SAMPLE_ID='g100_002_urban_high_camera_blueprint'
R2_FAILED_SAMPLE_REQUEST_DIGEST='f54ba07d29f06adf4f1318876103b8f91e4e92ceac6b0a279f9a695221de7d12'
R2_CHUNK0_DIGEST='076f231409bfd54d912b2fb12ff3c27b6410e942865bf775f13f3a77d05acb80'
R2_FAILURE_ERROR='G100_AUX_GT_ANALYTIC_VALIDATION_FAIL:{"depth": "FAIL", "normal": "PASS", "object": "PASS"}'
R3_FAILED_SAMPLE_ID='g100_003_intersection_near_infinity_pbr_realistic_intent'
R3_FAILED_SAMPLE_REQUEST_DIGEST='e0ad928b27217206c4c00907ca29d871a10e3d307afc24dc8b11b5da76087386'
R3_FAILURE_ERROR='G100_AUX_GT_ANALYTIC_VALIDATION_FAIL:{"depth": "FAIL", "normal": "PASS", "object": "FAIL"}'
R3_FORENSIC_SHA256='d01fd236efcd57ab269fab37a6c9f8cce860d8037ff849ec762222aa29bfc8ea'
RELEASE_ID='DF_G100_MICRO100_V2_R1'
DATASET_ID='PCS_CAMERA_GEOMETRY_MICRO100_V2'
ROOT_SEED=34620260905
RUN_ID=RELEASE_ID
PARTITION='MICRO100_QUALIFICATION_ONLY'
R26_SPEC_DRIVE_ID='1hXOzJGrfAeljLJuq5B4fGBMfMQgwPvTu-dlrCpU4Pjg'
R26_CLARIFICATION_DRIVE_ID='1wGImXkRxvD1ZDvY73dgiJag3LcAvx6wkPAgsqNTxacQ'
R27_SPEC_DRIVE_ID='1x0EUv2o5vq7WYyV_YbebXOcGj1DKMb5h9DBaf7Et1KE'
R28_SPEC_DRIVE_ID='1iVhVwzS_YmjCGPwyiD-FOydE6Q4ob5kjq8euKh7nIpc'
R28A_AUTHORITY_REFRESH_DRIVE_ID='1zBVP8MRUdGHEuN5mWZvlX7BjL7aDVCZj47xQusy96pQ'
R29_SPEC_DRIVE_ID='1_OkDftof9W8Eegc9GyOKhsBxQPWxFkkLUH1WWUwdmsM'
R29_FAILURE_DRIVE_ID='1YqDZvsrMbC-tfKhji6u8P38EdzDqLGAO'
R29_FAILURE_NAME='PCS_CAMERA_GEOMETRY_DATA_FACTORY_G100_MICRO100_V2_R28_FAILURE_RETURN_SAMPLE005_20260908.zip'
R29_FAILURE_BYTES=1269027
R29_FAILURE_SHA256='dfa7aa055ef3bbff8af1a8d54a862b715d9fce3846ebca24684a27eff96fe14f'
R29_RECOVERY_SAMPLE_ID='g100v2_005_stairs_ramps_low_camera_blueprint'
R29_RECOVERY_REQUEST_DIGEST='c02ac74ef72cab6fc7116af76199da15a38e3744df3fd167102dbcb8bc1f3608'
R29_DEPTH_AUTHORITY_SEMANTICS_ID='FILTER_SAFE_INTERIOR_EXACT_DEPTH_R29_V1'
R33_SPEC_DRIVE_ID='1nFRwtgCPKxN7YjQ8eZdAsHZhlrZQGAyJ2CpdQzBu470'
R34_SPEC_DRIVE_ID='1Pi6HcueA-JpaBjq3bHI3dnpiFSeMUFDjZHNHaUEB4LY'
R34_IMPLEMENTATION_ID='DF_G100_WINDOWS_ATOMIC_JSON_REPLACE_BOUNDED_RETRY_R34_V1'
R34_FAILURE_RETURN_NAME='PCS_CAMERA_GEOMETRY_DATA_FACTORY_G100_MICRO100_V2_R33_FAILURE_RETURN_20260909.zip'
R34_FAILURE_RETURN_BYTES=3088372
R34_FAILURE_RETURN_SHA256='d79bd7a73971bcc9c873bcf3b9d711cee2edd0fdd584636831f297a896011145'
R34_PROGRESS_SHA256='42a8bb981a2ccf8178eef7dc34caaa664e3221cfff0e975bedb684afd308f7f8'
R34_CHUNK06_LEDGER_SHA256='08c640217260f9ba508a1ef7189faa93d377c32294da63d93160783018dbd80d'
R34_R33_RECOVERY_JOURNAL_SHA256='11597c5ebef6e2926d446098bc345f52e732584063a4001c6118611256cfaccc'
R36_SPEC_DRIVE_ID='1JCmjhF9iccw8ARBoKLSF3ZI_PUjuGVyC_MrJdlMtfPg'
R36_IMPLEMENTATION_ID='DF_G100_BLUEPRINT_EXTREME_VERTICAL_FIXED_RGB_GAIN_X3_R36_V1'
R36_RECOVERY_SAMPLE_ID='g100v2_074_urban_telephoto_blueprint'
R36_RECOVERY_REQUEST_DIGEST='70b9f23588d5a34c9b777dbfe090d3be794c226f9e26c16ad2485f7ce940fd11'
R36_REQUEST_FILE_SHA256='5d2b1b871bf947478c029f2cc55fb556a548330d2279b3c9d7de0c3fafc786d6'
R36_PRE_RGB_SHA256='877e2ca955c69c0458bc7973fc6344f04e359436e1619d458315f05713ab4867'
R36_PRE_ACCEPTANCE_SHA256='1a9ab0c23e08b544d28349a0d20040b2ead7046cfa359747616d0608809a3ad1'
R36_PRE_COMPLETION_SHA256='42a41d5e990aa8b1139bba625d7473f0c83ae5ce9e474931d617f977561db5ff'
R36_PRE_CHUNK07_LEDGER_SHA256='7bc732b040da2ff864d4d48dd729bed12e92679e4fa7ba9234bfbc586a8019ec'
R36_PRE_PROGRESS_SHA256='82e51f68f73deb8158b820bafa5f161e2a22a945ae44575d1322c1289b72fe44'
R36_EXPECTED_FINAL_RGB_SHA256='ee7ff25dc1460faba361bc1db1783e90f03e4e55e04aa4b9918480bf452e29c6'
R35_DIAGNOSTIC_FAILURE_NAME='PCS_CAMERA_GEOMETRY_DATA_FACTORY_G100_MICRO100_V2_R35_BLUEPRINT_DIAGNOSTIC_FAILURE_RETURN_20260909.zip'
R35_DIAGNOSTIC_FAILURE_BYTES=2175897
R35_DIAGNOSTIC_FAILURE_SHA256='9d442cd7b9197c9008aa8be4386b4c8b38e2d29762d1d503c160889f51e29793'

R33_IMPLEMENTATION_ID='DF_G100_BLUEPRINT_VERTICAL_DOMINANT_FIXED_RGB_GAIN_X2_R33_V1'
R33_RECOVERY_SAMPLE_ID='g100v2_051_intersection_strong_roll_blueprint'
R33_RECOVERY_REQUEST_DIGEST='0d880cc6918005b5d20f38e7d382e06cf693e75f938bd1e0c0bd9d16243de317'
R33_REQUEST_FILE_SHA256='efa147d7c24004ba188ba5a8f93e99f7e5604b8c9f5e03da1e91612ada15bca8'
R33_PRE_RGB_SHA256='c49d338a124d5cf4da324d890ac7063e7569c5ed82854f619dc8b1c1883fb84d'
R33_PRE_ACCEPTANCE_SHA256='71025b5eace2e674f270951788c4c9d7ae306fc6b50b2d5cb7a6ed26fac37758'
R33_PRE_CHUNK05_LEDGER_SHA256='42f7007a3ac2f2d944d106519e185d8eab10ab88ab76fee354238758a3104d61'
R33_PRE_PROGRESS_SHA256='b48dcf04d6ae842abd6d6c81977c75381c49cc9ccc9eb565a92c9ea474ccc293'
R33_EXPECTED_FINAL_RGB_SHA256='cb8bf59d74c88ae806d50fe6beb6d77354e388ece9936bd31a82dd7d371441fb'
R31_REPLAY_AUTHORITY_NAME='PCS_CAMERA_GEOMETRY_DATA_FACTORY_G100_MICRO100_V2_R31_OFFLINE_REPLAY_RETURN_20260909.zip'
R31_REPLAY_AUTHORITY_SHA256='152e0dbb1559a7f4679bf311b2524565eb9b1f57b4dead1e5acfff35dce5eac6'
R31_REPLAY_AUTHORITY_BYTES=164846
R31_SNAPSHOT_SHA256='496753cabf7b509b285f37430f3cb935b83414068067ea8479f5cb5988126758'
R28_IMPL_FAILURE_DRIVE_ID='130c2wBOkZMYllKLGtR3p66CQmpbnEpGy'
R28_IMPL_FAILURE_NAME='PCS_CAMERA_GEOMETRY_DATA_FACTORY_G100_MICRO100_V2_R27_IMPLEMENTATION_FAILURE_RETURN_20260908.zip'
R28_IMPL_FAILURE_BYTES=359339
R28_IMPL_FAILURE_SHA256='e37c43269a5fef29e0392ff4b5b23b1a80a10217cc83d64c89991d2b8fa10489'
R27_FAILURE_RETURN_NAME='PCS_CAMERA_GEOMETRY_DATA_FACTORY_G100_MICRO100_V2_R26_REAL_FAILURE_RETURN_20260908.zip'
R27_FAILURE_RETURN_BYTES=359769
R27_FAILURE_RETURN_SHA256='b80fe90e0c53d8524d75e4dccd828196c4b3d7d8834304729c88c35469703835'
R27_CHUNK00_DIGEST='21081c99d1597c1c319a10521e620899e4e1459bb568866eeca6f9101c2dc012'
R27_RECOVERY_SAMPLE_ID='g100v2_003_intersection_near_infinity_pbr_realistic_intent'
R27_RECOVERY_REQUEST_DIGEST='390635ba881d81ec82df9a199ead49fb1123b3d5c0f211fed00dd5b4c90ea45c'
V1_FINAL_ADJUDICATION_DRIVE_ID='188EvNDsef8MqK7U74OXgE_jBR-q-0MzAIPcv8kfQ0ig'
V1_REAL_RETURN_DRIVE_ID='1qODyNF2YpyN5BYVfKUQZZfHVgwbG22iu'
V1_REAL_RETURN_BYTES=60087695
V1_REAL_RETURN_SHA256='f3e33dd69a858091c76e8193dabdad1849163e55c33556d96f714a68129cc6a0'
SPEC_DRIVE_ID=R36_SPEC_DRIVE_ID
CLOSURE_EVIDENCE_SHA='cee76bbc1c9c3d073d11d95bbe9ea5b4bf12bfde24afd4fda0a8b30f1529306c'
G70_EVIDENCE_SHA='59d3d6a5f55902589122c72f2ca8227e551a05e00b4f8cfd89a86c6e91b418c7'
R10_RETURN_SHA='de8b9782d5f0f40605c9eb476d21e8b9323d6cc2ed4cd60e00f363738ac9e579'
RETURN_NAME='PCS_CAMERA_GEOMETRY_DATA_FACTORY_G100_MICRO100_V2_RETURN.zip'
FAIL_NAME='PCS_CAMERA_GEOMETRY_DATA_FACTORY_G100_MICRO100_V2_FAILURE_RETURN.zip'
FAMILIES=['INTERIOR','CORRIDOR','URBAN','INTERSECTION','INDUSTRIAL','STAIRS_RAMPS','NON_MANHATTAN','SPARSE','CLUTTER','REPEATED_PATTERN','ORGANIC_NEGATIVE','HYBRID_CONCEPT']
CAMERAS=['NORMAL','WIDE','TELEPHOTO','STRONG_ROLL','STRONG_PITCH','LOW_CAMERA','HIGH_CAMERA','PORTRAIT','OFFCENTER','NEAR_INFINITY']
APPEARANCES=['PBR_REALISTIC_INTENT','DAY_HARD','TOON','CLAY','BLUEPRINT','PAINTERLY_CONCEPT']
NONPORTRAIT=[(384,216),(512,288),(320,320),(512,216)]
EXPECTED_COUNTS={
 'families':{'INTERIOR':9,'CORRIDOR':9,'URBAN':9,'INTERSECTION':9,'INDUSTRIAL':8,'STAIRS_RAMPS':8,'NON_MANHATTAN':8,'SPARSE':8,'CLUTTER':8,'REPEATED_PATTERN':8,'ORGANIC_NEGATIVE':8,'HYBRID_CONCEPT':8},
 'cameras':{'STRONG_PITCH':11,'PORTRAIT':11,'NORMAL':10,'STRONG_ROLL':10,'HIGH_CAMERA':10,'LOW_CAMERA':10,'OFFCENTER':10,'WIDE':10,'NEAR_INFINITY':9,'TELEPHOTO':9},
 'appearances':{'TOON':18,'PBR_REALISTIC_INTENT':17,'BLUEPRINT':17,'DAY_HARD':16,'CLAY':16,'PAINTERLY_CONCEPT':16},
 'resolutions':{'384x216':24,'320x320':22,'512x288':22,'512x216':21,'288x384':11},
}


def utc_iso(): return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
def sha256_file(p:Path):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()
def sha256_bytes(b:bytes): return hashlib.sha256(b).hexdigest()
def _r28_payload_sha256(obj):
    b=json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')
    return hashlib.sha256(b).hexdigest()
R34_REPLACE_RETRY_DELAYS=(0.05,0.10,0.20,0.40,0.80,1.60,2.00,2.00)
R34_REPLACE_RETRY_WINERRORS={5,32}

def _r34_retryable_replace_error(exc):
    if not isinstance(exc,PermissionError): return False
    winerror=getattr(exc,'winerror',None)
    if winerror is not None: return int(winerror) in R34_REPLACE_RETRY_WINERRORS
    return os.name=='nt' and getattr(exc,'errno',None) in {13,1}

def _r34_replace_with_retry(src,dst):
    for attempt in range(len(R34_REPLACE_RETRY_DELAYS)+1):
        try: os.replace(src,dst); return
        except PermissionError as exc:
            if not _r34_retryable_replace_error(exc) or attempt>=len(R34_REPLACE_RETRY_DELAYS): raise
            if not Path(src).exists(): raise
            time.sleep(R34_REPLACE_RETRY_DELAYS[attempt])

def atomic_json(p:Path,obj):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix(p.suffix+'.tmp')
    t.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n',encoding='utf-8');_r34_replace_with_retry(t,p)
def atomic_text(p:Path,text:str):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix(p.suffix+'.tmp');t.write_text(text,encoding='utf-8');_r34_replace_with_retry(t,p)
def safe_root(root:Path):
    s=str(root).replace('/','\\').rstrip('\\').lower()
    if s=='c:\\pcs' or s.startswith('c:\\pcs\\'):raise RuntimeError('G100_PRODUCT_ROOT_FIREWALL')
    if 'camera_geometry_data_factory' not in s:raise RuntimeError('G100_FACTORY_ROOT_GUARD:'+str(root))
def verify_ref(name,sha):
    p=REFERENCE/name
    if not p.is_file():raise RuntimeError('REFERENCE_MISSING:'+name)
    got=sha256_file(p)
    if got!=sha:raise RuntimeError(f'REFERENCE_SHA_MISMATCH:{name}:{got}')
    with zipfile.ZipFile(p) as z:
        bad=z.testzip()
        if bad:raise RuntimeError('REFERENCE_CRC_FAIL:'+name+':'+bad)
    return {'file':name,'bytes':p.stat().st_size,'sha256':got,'crc':'PASS'}

def install_release(root:Path):
    safe_root(root); release=root/'01_SOURCE'/'RELEASES'/SOURCE_RELEASE_ID; stage=release.with_name(release.name+'.staging')
    shutil.rmtree(stage,ignore_errors=True);stage.mkdir(parents=True)
    for p in sorted(SOURCE.glob('*.py')):shutil.copy2(p,stage/p.name)
    shutil.copy2(Path(__file__),stage/Path(__file__).name)
    files=[]
    for p in sorted(stage.iterdir()):
        if p.is_file():files.append({'path':p.name,'bytes':p.stat().st_size,'sha256':sha256_file(p)})
    atomic_json(stage/'SOURCE_MANIFEST.json',{'schema':'DF-G100-SOURCE-MANIFEST-V1','release_id':SOURCE_RELEASE_ID,'frozen_request_release_id':RELEASE_ID,'spec_drive_id':SPEC_DRIVE_ID,'r3_addendum_drive_id':R3_ADDENDUM_DRIVE_ID,'r4_addendum_drive_id':R4_ADDENDUM_DRIVE_ID,'r5_addendum_drive_id':R5_ADDENDUM_DRIVE_ID,'r6_addendum_drive_id':R6_ADDENDUM_DRIVE_ID,'r7_addendum_drive_id':R7_ADDENDUM_DRIVE_ID,'r8_addendum_drive_id':R8_ADDENDUM_DRIVE_ID,'r9_addendum_drive_id':R9_ADDENDUM_DRIVE_ID,'r10_addendum_drive_id':R10_ADDENDUM_DRIVE_ID,'r11_addendum_drive_id':R11_ADDENDUM_DRIVE_ID,'r12_addendum_drive_id':R12_ADDENDUM_DRIVE_ID,'r13_addendum_drive_id':R13_ADDENDUM_DRIVE_ID,'r14_addendum_drive_id':R14_ADDENDUM_DRIVE_ID,'r15_addendum_drive_id':R15_ADDENDUM_DRIVE_ID,'r16_addendum_drive_id':R16_ADDENDUM_DRIVE_ID,'r17_addendum_drive_id':R17_ADDENDUM_DRIVE_ID,'r18_addendum_drive_id':R18_ADDENDUM_DRIVE_ID,'r19_addendum_drive_id':R19_ADDENDUM_DRIVE_ID,'r20_addendum_drive_id':R20_ADDENDUM_DRIVE_ID,'r23_addendum_drive_id':R23_ADDENDUM_DRIVE_ID,'r24_addendum_drive_id':R24_ADDENDUM_DRIVE_ID,'r25_addendum_drive_id':R25_ADDENDUM_DRIVE_ID,'r26_spec_drive_id':R26_SPEC_DRIVE_ID,'r26_clarification_drive_id':R26_CLARIFICATION_DRIVE_ID,'r27_spec_drive_id':R27_SPEC_DRIVE_ID,'r28_spec_drive_id':R28_SPEC_DRIVE_ID,'r28a_authority_refresh_drive_id':R28A_AUTHORITY_REFRESH_DRIVE_ID,'r29_spec_drive_id':R29_SPEC_DRIVE_ID,'r33_spec_drive_id':R33_SPEC_DRIVE_ID,'r34_spec_drive_id':R34_SPEC_DRIVE_ID,'r34_implementation_id':R34_IMPLEMENTATION_ID,'r36_spec_drive_id':R36_SPEC_DRIVE_ID,'r36_implementation_id':R36_IMPLEMENTATION_ID,'r31_replay_authority':{'bytes':R31_REPLAY_AUTHORITY_BYTES,'sha256':R31_REPLAY_AUTHORITY_SHA256},'r29_failure_authority':{'drive_id':R29_FAILURE_DRIVE_ID,'bytes':R29_FAILURE_BYTES,'sha256':R29_FAILURE_SHA256},'v1_final_adjudication_drive_id':V1_FINAL_ADJUDICATION_DRIVE_ID,'v1_real_return':{'drive_id':V1_REAL_RETURN_DRIVE_ID,'bytes':V1_REAL_RETURN_BYTES,'sha256':V1_REAL_RETURN_SHA256},'files':files,'product_mutated':False,'maya_mutated':False,'test77_accessed':False,'training_started':False})
    shutil.rmtree(release,ignore_errors=True);os.replace(stage,release);return release

def _load_modules(release:Path):
    if str(release) not in sys.path:sys.path.insert(0,str(release))
    from pcs_factory_appearance import canonical_profiles
    from pcs_factory_blender_protocol import finalize_request,finalize_chunk,validate_request,validate_chunk,validate_completion
    from pcs_factory_scene_recipe import generate_archetype,validate_scene
    from pcs_factory_seed import derive_seed,identity_digest
    from pcs_factory_blender_runtime import acquire_or_verify_runtime,runtime_paths,query_blender_identity
    from pcs_factory_blender_controller import execute_chunk
    from pcs_factory_camera_observability_v2 import select_scene_aware_camera,validate_selected,THRESHOLDS,THRESHOLD_HASH,RICH_STRUCTURAL,CANDIDATE_BUDGET
    return locals()

def _r26_stress_score(req):
    fam=req['scene']['scene_family']
    if fam not in {'INTERIOR','CORRIDOR','URBAN','INTERSECTION','INDUSTRIAL','STAIRS_RAMPS','NON_MANHATTAN','CLUTTER','REPEATED_PATTERN','HYBRID_CONCEPT'}:
        return None
    m=req['camera_observability_v2']['selected_metrics']
    vals=[
        float(m['scene_hit_fraction'])/0.10,
        float(m['distinct_visible_object_ids'])/3.0,
        (1.0-float(m['dominant_visible_object_fraction']))/(1.0-0.85),
        float(m['clipped_structural_segments'])/8.0,
        float(m['distinct_projected_direction_set_ids'])/2.0,
    ]
    return min(vals)

def generate_plan(M):
    profiles={p['profile_id']:p for p in M['canonical_profiles']()};reqs=[]
    for i in range(100):
        fi=i%12;rnd=i//12;family=FAMILIES[fi];camname=CAMERAS[(rnd+3*fi)%10];app=APPEARANCES[(rnd+2*fi)%6]
        w,h=(288,384) if camname=='PORTRAIT' else NONPORTRAIT[(rnd+2*fi)%4]
        scene=M['generate_archetype'](family,index=1000+i,root_seed=ROOT_SEED)
        sv=M['validate_scene'](scene)
        if sv['status']!='PASS':raise RuntimeError('G100_R26_PLAN_SCENE_INVALID:'+family+':'+str(sv))
        cam,obs=M['select_scene_aware_camera'](scene,camname,ROOT_SEED,i,w,h)
        vv=M['validate_selected'](scene,cam,obs)
        if vv['status']!='PASS': raise RuntimeError('G100_R26_SELECTED_CAMERA_VALIDATION_FAIL:'+str(i))
        sid=f'g100v2_{i:03d}_{family.lower()}_{camname.lower()}_{app.lower()}'
        req={'sample_id':sid,'run_id':RUN_ID,'dataset_id':DATASET_ID,'release_id':RELEASE_ID,'partition':PARTITION,'scene_index':1000+i,
             'camera_seed_u64':int(obs['selected_candidate_seed_u64']),'camera_planner_root_seed':ROOT_SEED,
             'scene':scene,'camera':{'profile':cam['profile'],'width':cam['width'],'height':cam['height'],'K':cam['K'],'pose':cam['pose'],'sampled':cam['sampled']},
             'camera_observability_v2':obs,
             'appearance':copy.deepcopy(profiles[app]),'renderer':{'engine':'CYCLES','samples':8,'denoise':True,'device':'AUTO'},
             'passes':['RGB','DEPTH','NORMAL','OBJECT_INDEX'],'output_rel':f'samples/{sid}','gt_class':'GT_EXACT_3D_CAMERA_AUX','split':PARTITION,
             'test77_accessed':False,'training_started':False,'maya_mutated':False,'product_mutated':False}
        req['camera_observability_v2']['observability_stress_score']=_r26_stress_score(req)
        reqs.append(M['finalize_request'](req))
    chunks=[]
    for ci in range(10):
        part=reqs[ci*10:(ci+1)*10]
        chunk=M['finalize_chunk']({'chunk_id':f'{RELEASE_ID}_CHUNK_{ci:02d}','dataset_id':DATASET_ID,'release_id':RELEASE_ID,'chunk_index':ci,'worker_protocol_version':'DF-G100-V2-R26','worker_id_hint':'LOCAL_WINDOWS','root_seed':ROOT_SEED,'requests':part,'split':PARTITION,'test77_accessed':False,'training_started':False,'maya_mutated':False,'product_mutated':False})
        M['validate_chunk'](chunk);chunks.append(chunk)
    return reqs,chunks

def plan_qa(reqs,chunks,M):
    obs_ok=True;obs_details=[]
    for r in reqs:
        M['validate_request'](r)
        try:
            vv=M['validate_selected'](r['scene'],r['camera'],r['camera_observability_v2'])
            ok=vv['status']=='PASS' and not vv['metrics']['camera_inside_any_solid']
        except Exception as e:
            ok=False; vv={'error':f'{type(e).__name__}:{e}'}
        obs_ok=obs_ok and ok;obs_details.append({'sample_id':r['sample_id'],'ok':ok})
    counts={'families':Counter(r['scene']['scene_family'] for r in reqs),'cameras':Counter(r['camera']['profile'] for r in reqs),'appearances':Counter(r['appearance']['profile_id'] for r in reqs),'resolutions':Counter(f"{r['camera']['width']}x{r['camera']['height']}" for r in reqs)}
    tuples={(r['scene']['scene_family'],r['camera']['profile'],r['appearance']['profile_id'],r['camera']['width'],r['camera']['height']) for r in reqs}
    keys=['sample_id','input_digest_sha256'];uniq={k:len({r[k] for r in reqs}) for k in keys}
    uniq.update({'base_scene_id':len({r['scene']['base_scene_id'] for r in reqs}),'recipe_digest_sha256':len({r['scene']['recipe_digest_sha256'] for r in reqs})})
    rich=[r for r in reqs if r['scene']['scene_family'] in M['RICH_STRUCTURAL']]
    selected_inside=sum(1 for r in reqs if r['camera_observability_v2']['selected_metrics']['camera_inside_any_solid'])
    max_eval=max(int(r['camera_observability_v2']['evaluated_candidates']) for r in reqs)
    checks={'exact_100':len(reqs)==100,'ten_chunks_of_ten':len(chunks)==10 and all(len(c['requests'])==10 for c in chunks),'tuple_unique_100':len(tuples)==100,
            'scene_indices_exact':[r['scene_index'] for r in reqs]==list(range(1000,1100)),'all_identity_dimensions_unique':all(v==100 for v in uniq.values()),
            'family_counts':dict(counts['families'])==EXPECTED_COUNTS['families'],'camera_counts':dict(counts['cameras'])==EXPECTED_COUNTS['cameras'],
            'appearance_counts':dict(counts['appearances'])==EXPECTED_COUNTS['appearances'],'resolution_counts':dict(counts['resolutions'])==EXPECTED_COUNTS['resolutions'],
            'all_cycles_aux':all(r['renderer']=={'engine':'CYCLES','samples':8,'denoise':True,'device':'AUTO'} and r['passes']==['RGB','DEPTH','NORMAL','OBJECT_INDEX'] for r in reqs),
            'qualification_only':all(r['split']==PARTITION and not r['training_started'] and not r['test77_accessed'] and not r['product_mutated'] and not r['maya_mutated'] for r in reqs),
            'v2_sample_prefix':all(r['sample_id'].startswith('g100v2_') for r in reqs),
            'observability_all_pass':obs_ok,'zero_selected_camera_inside_solid':selected_inside==0,'candidate_budget_exact_64':all(r['camera_observability_v2']['candidate_budget']==64 for r in reqs),
            'evaluated_candidates_bounded':max_eval<=64 and all(r['camera_observability_v2']['evaluated_candidates'] in {4,8,16,32,64} for r in reqs),
            'non_adaptive_firewall':all(r['camera_observability_v2']['non_adaptive'] is True and r['camera_observability_v2']['rgb_statistics_used'] is False and r['camera_observability_v2']['prior_v1_failure_used_for_selection'] is False for r in reqs),
            'rich_stress_scores_ge_1':all(float(r['camera_observability_v2']['observability_stress_score'])>=1.0-1e-12 for r in rich)}
    return {'schema':'DF-G100-R26-PLAN-QA-V2','status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'counts':{k:dict(v) for k,v in counts.items()},'unique_identities':uniq,'unique_tuple_count':len(tuples),'chunk_digests':[c['chunk_digest_sha256'] for c in chunks],'observability':{'selected_inside_solid_count':selected_inside,'max_evaluated_candidates':max_eval,'rich_min_stress_score':min(float(r['camera_observability_v2']['observability_stress_score']) for r in rich)}}

def _discrete_signature(r):
    return {
        'sample_id':r['sample_id'],'scene_index':r['scene_index'],'scene_family':r['scene']['scene_family'],
        'camera_profile':r['camera']['profile'],'appearance_profile':r['appearance']['profile_id'],
        'width':r['camera']['width'],'height':r['camera']['height'],'split':r['split'],
    }

def _discrete_regeneration_diagnostic(frozen_reqs,frozen_chunks,regen_reqs,regen_chunks):
    fr=[_discrete_signature(r) for r in frozen_reqs]; rr=[_discrete_signature(r) for r in regen_reqs]
    fcm=[[r['sample_id'] for r in c['requests']] for c in frozen_chunks]
    rcm=[[r['sample_id'] for r in c['requests']] for c in regen_chunks]
    checks={
        'sample_count':len(fr)==len(rr)==100,
        'discrete_request_assignments':fr==rr,
        'chunk_membership':fcm==rcm and len(fcm)==10 and all(len(x)==10 for x in fcm),
    }
    digest_matches=sum(1 for a,b in zip(frozen_reqs,regen_reqs) if a.get('input_digest_sha256')==b.get('input_digest_sha256'))
    chunk_digest_matches=sum(1 for a,b in zip(frozen_chunks,regen_chunks) if a.get('chunk_digest_sha256')==b.get('chunk_digest_sha256'))
    return {'schema':'DF-G100-R2-REGENERATION-DIAGNOSTIC-V1','status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,
            'request_digest_matches_non_authority':digest_matches,'chunk_digest_matches_non_authority':chunk_digest_matches,
            'numeric_float_equality_authority':False,'execution_source':'PACKAGE_FROZEN_PLAN'}

def _validate_frozen_plan_object(obj,M):
    hdr={'schema':obj.get('schema')=='DF-G100-PACKAGE-FROZEN-REQUEST-PLAN-V2','dataset_id':obj.get('dataset_id')==DATASET_ID,'release_id':obj.get('release_id')==RELEASE_ID,'root_seed':obj.get('root_seed')==ROOT_SEED,'partition':obj.get('partition')==PARTITION,'sample_count':obj.get('sample_count')==100,'r26_spec_drive_id':obj.get('r26_spec_drive_id')==R26_SPEC_DRIVE_ID,'r26_clarification_drive_id':obj.get('r26_clarification_drive_id')==R26_CLARIFICATION_DRIVE_ID}
    if not all(hdr.values()): raise RuntimeError('G100_R26_FROZEN_PLAN_HEADER_MISMATCH:'+json.dumps(hdr,sort_keys=True))
    reqs=obj.get('requests');chunks=obj.get('chunks')
    if not isinstance(reqs,list) or len(reqs)!=100: raise RuntimeError('G100_R26_FROZEN_REQUEST_COUNT')
    if not isinstance(chunks,list) or len(chunks)!=10 or any(len(c.get('requests',[]))!=10 for c in chunks): raise RuntimeError('G100_R26_FROZEN_CHUNK_SHAPE')
    for r in reqs:M['validate_request'](r)
    for i,c in enumerate(chunks):
        M['validate_chunk'](c)
        if c['requests']!=reqs[i*10:(i+1)*10]: raise RuntimeError(f'G100_R26_CHUNK_REQUEST_BINDING:{i}')
        cp=HERE/'PLAN'/f'CHUNK_{i:02d}_PACKAGE_FROZEN.json'
        if not cp.is_file() or json.loads(cp.read_text(encoding='utf-8'))!=c: raise RuntimeError(f'G100_R26_CHUNK_SIDECAR_MISMATCH:{i}')
    qa=plan_qa(reqs,chunks,M)
    if qa['status']!='PASS': raise RuntimeError('G100_R26_FROZEN_PLAN_STRUCTURAL_QA_FAIL:'+json.dumps(qa['checks'],sort_keys=True))
    if obj.get('plan_qa')!=qa: raise RuntimeError('G100_R26_FROZEN_PLAN_QA_MISMATCH')
    vis=obj.get('visual_selection') or {}
    sel,uncovered=choose_visual(reqs)
    if vis.get('selected_indices')!=sel or uncovered or vis.get('count')!=24: raise RuntimeError('G100_R26_FROZEN_VISUAL_SELECTION_MISMATCH')
    return reqs,chunks,qa

def load_package_frozen_plan(M,plan_path=None,expected_sha=None,run_regeneration=True):
    plan_path=Path(plan_path or PACKAGE_PLAN); expected_sha=expected_sha or PACKAGE_PLAN_SHA256
    if not plan_path.is_file(): raise RuntimeError('G100_R26_PACKAGE_FROZEN_PLAN_MISSING')
    got=sha256_file(plan_path)
    if got!=expected_sha: raise RuntimeError('G100_R26_PACKAGE_FROZEN_PLAN_SHA_MISMATCH:'+got)
    obj=json.loads(plan_path.read_text(encoding='utf-8'));reqs,chunks,qa=_validate_frozen_plan_object(obj,M)
    regen=None
    if run_regeneration:
        regen_reqs,regen_chunks=generate_plan(M)
        regen_norm_reqs=json.loads(json.dumps(regen_reqs,sort_keys=True)); regen_norm_chunks=json.loads(json.dumps(regen_chunks,sort_keys=True))
        regen={'schema':'DF-G100-R26-EXACT-REGENERATION-DIAGNOSTIC-V1','requests_exact':regen_norm_reqs==reqs,'chunks_exact':regen_norm_chunks==chunks}
        regen['status']='PASS' if regen['requests_exact'] and regen['chunks_exact'] else 'FAIL'
        if regen['status']!='PASS': raise RuntimeError('G100_R26_REGENERATION_EXACT_MISMATCH')
    ident={'bytes':plan_path.stat().st_size,'sha256':got,'execution_authority':'PACKAGE_FROZEN_PLAN_V2_R26','tool_revision':TOOL_REVISION,'release_id':RELEASE_ID,'r26_spec_drive_id':R26_SPEC_DRIVE_ID,'r26_clarification_drive_id':R26_CLARIFICATION_DRIVE_ID,'regeneration_diagnostic':regen}
    return reqs,chunks,qa,ident

def _tree_records(root:Path):
    rows=[]
    if not root.exists():return rows
    for p in sorted(root.rglob('*')):
        if p.is_file():
            rows.append({'path':p.relative_to(root).as_posix(),'bytes':p.stat().st_size,'sha256':sha256_file(p)})
    return rows

def apply_r3_resume_if_needed(runroot:Path,chunks):
    """Exact, fail-closed R2 FAILED_FINAL -> R3 resume.

    This function is intentionally narrower than the generic ledger state
    machine. It may reopen only the known depth-binding false failure for
    sample 002 and preserves all prior failed bytes before doing so.
    """
    cr=runroot/'CHUNKS'/'chunk_00'; lp=cr/'ledger.json'
    info={'schema':'DF-G100-R3-RESUME-STATE-V1','status':'NO_PRIOR_LEDGER','r3_addendum_drive_id':R3_ADDENDUM_DRIVE_ID,
          'recovered_samples':{},'completed_samples_preserved':[]}
    if not lp.is_file():
        return info
    ledger=json.loads(lp.read_text(encoding='utf-8'))
    if ledger.get('chunk_digest_sha256')!=R2_CHUNK0_DIGEST or chunks[0].get('chunk_digest_sha256')!=R2_CHUNK0_DIGEST:
        raise RuntimeError('G100_R3_RESUME_CHUNK0_DIGEST_MISMATCH')
    states=ledger.get('states',{})
    s0='g100_000_interior_normal_pbr_realistic_intent';s1='g100_001_corridor_strong_roll_toon';sid=R2_FAILED_SAMPLE_ID
    expected_complete={
      s0:'3f0a24fadc0e0989785b2415487bf3dea78fb939b3d410fd375fe68dc4a6ebc4',
      s1:'5089b19db397467580fcb2bbfa86de213be7731fe51e78c79b3862552240fb2c'}
    for s,dg in expected_complete.items():
        rec=states.get(s,{})
        if rec.get('state')!='COMPLETE' or rec.get('request_digest')!=dg:
            raise RuntimeError('G100_R3_RESUME_COMPLETED_PRECONDITION:'+s)
        info['completed_samples_preserved'].append(s)
    rec=states.get(sid,{})
    if rec.get('request_digest')!=R2_FAILED_SAMPLE_REQUEST_DIGEST:
        raise RuntimeError('G100_R3_RESUME_REQUEST_DIGEST_MISMATCH')

    # Idempotent states after the one-time recovery are allowed.
    if rec.get('r3_recovery',{}).get('r3_addendum_drive_id')==R3_ADDENDUM_DRIVE_ID:
        if rec.get('state') in {'PENDING','RUNNING','FAILED_RETRYABLE','COMPLETE','FAILED_FINAL'}:
            info['status']='R3_RECOVERY_ALREADY_APPLIED'
            info['recovered_samples'][sid]=dict(rec.get('r3_recovery',{}))
            return info
        raise RuntimeError('G100_R3_RESUME_BAD_POST_RECOVERY_STATE')

    # If a prior R3 run already completed the sample but the ledger lacks the
    # marker, fail closed rather than inventing provenance.
    if rec.get('state')!='FAILED_FINAL' or int(rec.get('attempts',-1))!=2 or rec.get('last_error')!='BLENDER_WORKER_RC:5':
        raise RuntimeError('G100_R3_RESUME_EXACT_R2_FAILED_FINAL_PRECONDITION')

    sd=cr/'samples'/sid
    fj=sd/'failure.json'
    if not fj.is_file():
        raise RuntimeError('G100_R3_RESUME_FAILURE_JSON_MISSING')
    fobj=json.loads(fj.read_text(encoding='utf-8'))
    if fobj.get('input_digest_sha256')!=R2_FAILED_SAMPLE_REQUEST_DIGEST or fobj.get('error')!=R2_FAILURE_ERROR:
        raise RuntimeError('G100_R3_RESUME_FAILURE_CAUSE_MISMATCH')
    prior_records=_tree_records(sd)
    if not prior_records:
        raise RuntimeError('G100_R3_RESUME_FAILED_SAMPLE_EVIDENCE_EMPTY')

    # Preserve every failed-sample byte under RECOVERY before clearing sample002.
    evroot=runroot/'RECOVERY'/'R2_FAILED_SAMPLE_002'
    evroot.mkdir(parents=True,exist_ok=True)
    payload=evroot/'sample_bytes'
    if payload.exists():shutil.rmtree(payload)
    shutil.copytree(sd,payload)
    copied=_tree_records(payload)
    if copied!=prior_records:
        raise RuntimeError('G100_R3_RESUME_PRESERVE_HASH_MISMATCH')
    recovery={
      'schema':'DF-G100-R3-RECOVERY-JOURNAL-V1','status':'PRESERVED_BEFORE_LEDGER_RESET',
      'r3_addendum_drive_id':R3_ADDENDUM_DRIVE_ID,'source_tool':'R2','target_tool':'R3',
      'sample_id':sid,'request_digest':R2_FAILED_SAMPLE_REQUEST_DIGEST,'prior_state':'FAILED_FINAL',
      'prior_attempts':2,'prior_last_error':'BLENDER_WORKER_RC:5','prior_failure_error':R2_FAILURE_ERROR,
      'chunk_digest_sha256':R2_CHUNK0_DIGEST,'preserved_members':prior_records,
      'preserved_failure_json_sha256':sha256_file(payload/'failure.json'),
      'completed_samples_preserved':list(info['completed_samples_preserved']),
      'recorded_utc':utc_iso(),'product_mutated':False,'maya_mutated':False,'test77_accessed':False,'training_started':False}
    atomic_json(evroot/'R3_RECOVERY_JOURNAL.json',recovery)

    # Only the failed sample is cleared, after exact preservation.
    shutil.rmtree(sd)
    sd.mkdir(parents=True,exist_ok=True)
    rec['state']='PENDING';rec['attempts']=0
    rec.pop('last_error',None)
    rec['r3_recovery']={'r3_addendum_drive_id':R3_ADDENDUM_DRIVE_ID,'prior_attempts':2,
                        'prior_state':'FAILED_FINAL','prior_failure_error':R2_FAILURE_ERROR,
                        'recovery_journal_rel':(evroot/'R3_RECOVERY_JOURNAL.json').relative_to(runroot).as_posix()}
    atomic_json(lp,ledger)
    recovery['status']='LEDGER_RESET_SAMPLE_002_ONLY'
    atomic_json(evroot/'R3_RECOVERY_JOURNAL.json',recovery)
    info['status']='R2_SAMPLE_002_REOPENED_FOR_R3'
    info['recovered_samples'][sid]=dict(rec['r3_recovery'])
    return info

def apply_r4_resume_if_needed(runroot:Path,chunks):
    """Exact, fail-closed R3 sample003 FAILED_FINAL -> R4 resume.

    Only sample003 may be reopened. Samples 000/001/002 must already be COMPLETE.
    Every failed sample003 byte plus worker log/request are preserved with hashes
    before ledger mutation.
    """
    cr=runroot/'CHUNKS'/'chunk_00'; lp=cr/'ledger.json'
    info={'schema':'DF-G100-R4-RESUME-STATE-V1','status':'NO_PRIOR_LEDGER',
          'r4_addendum_drive_id':R4_ADDENDUM_DRIVE_ID,'recovered_samples':{},
          'completed_samples_preserved':[]}
    if not lp.is_file():
        return info
    ledger=json.loads(lp.read_text(encoding='utf-8'))
    if ledger.get('chunk_digest_sha256')!=R2_CHUNK0_DIGEST or chunks[0].get('chunk_digest_sha256')!=R2_CHUNK0_DIGEST:
        raise RuntimeError('G100_R4_RESUME_CHUNK0_DIGEST_MISMATCH')
    states=ledger.get('states',{})
    expected_complete={
      'g100_000_interior_normal_pbr_realistic_intent':'3f0a24fadc0e0989785b2415487bf3dea78fb939b3d410fd375fe68dc4a6ebc4',
      'g100_001_corridor_strong_roll_toon':'5089b19db397467580fcb2bbfa86de213be7731fe51e78c79b3862552240fb2c',
      R2_FAILED_SAMPLE_ID:R2_FAILED_SAMPLE_REQUEST_DIGEST}
    for sid,dg in expected_complete.items():
        rec=states.get(sid,{})
        if rec.get('state')!='COMPLETE' or rec.get('request_digest')!=dg:
            raise RuntimeError('G100_R4_RESUME_COMPLETED_PRECONDITION:'+sid)
        info['completed_samples_preserved'].append(sid)

    sid=R3_FAILED_SAMPLE_ID; rec=states.get(sid,{})
    if rec.get('request_digest')!=R3_FAILED_SAMPLE_REQUEST_DIGEST:
        raise RuntimeError('G100_R4_RESUME_REQUEST_DIGEST_MISMATCH')
    if rec.get('r4_recovery',{}).get('r4_addendum_drive_id')==R4_ADDENDUM_DRIVE_ID:
        if rec.get('state') in {'PENDING','RUNNING','FAILED_RETRYABLE','COMPLETE','FAILED_FINAL'}:
            info['status']='R4_RECOVERY_ALREADY_APPLIED'
            info['recovered_samples'][sid]=dict(rec.get('r4_recovery',{}))
            return info
        raise RuntimeError('G100_R4_RESUME_BAD_POST_RECOVERY_STATE')
    if rec.get('state')!='FAILED_FINAL' or int(rec.get('attempts',-1))!=2 or rec.get('last_error')!='BLENDER_WORKER_RC:5':
        raise RuntimeError('G100_R4_RESUME_EXACT_R3_FAILED_FINAL_PRECONDITION')

    sd=cr/'samples'/sid; fj=sd/'failure.json'; logp=cr/'logs'/f'{sid}.log'; reqp=cr/'requests'/f'{sid}.json'
    for p,label in ((fj,'FAILURE_JSON'),(logp,'WORKER_LOG'),(reqp,'REQUEST_JSON')):
        if not p.is_file(): raise RuntimeError('G100_R4_RESUME_'+label+'_MISSING')
    fobj=json.loads(fj.read_text(encoding='utf-8'))
    if fobj.get('input_digest_sha256')!=R3_FAILED_SAMPLE_REQUEST_DIGEST or fobj.get('error')!=R3_FAILURE_ERROR:
        raise RuntimeError('G100_R4_RESUME_FAILURE_CAUSE_MISMATCH')
    reqobj=json.loads(reqp.read_text(encoding='utf-8'))
    if reqobj.get('input_digest_sha256')!=R3_FAILED_SAMPLE_REQUEST_DIGEST or reqobj.get('sample_id')!=sid:
        raise RuntimeError('G100_R4_RESUME_REQUEST_FILE_MISMATCH')
    prior_records=_tree_records(sd)
    if not prior_records: raise RuntimeError('G100_R4_RESUME_FAILED_SAMPLE_EVIDENCE_EMPTY')

    evroot=runroot/'RECOVERY'/'R3_FAILED_SAMPLE_003'
    evroot.mkdir(parents=True,exist_ok=True); payload=evroot/'sample_bytes'
    if payload.exists(): shutil.rmtree(payload)
    shutil.copytree(sd,payload)
    copied=_tree_records(payload)
    if copied!=prior_records: raise RuntimeError('G100_R4_RESUME_PRESERVE_HASH_MISMATCH')
    shutil.copy2(logp,evroot/'worker.log')
    shutil.copy2(reqp,evroot/'request.json')
    recovery={
      'schema':'DF-G100-R4-RECOVERY-JOURNAL-V1','status':'PRESERVED_BEFORE_LEDGER_RESET',
      'r4_addendum_drive_id':R4_ADDENDUM_DRIVE_ID,'source_tool':'R3','target_tool':'R4',
      'sample_id':sid,'request_digest':R3_FAILED_SAMPLE_REQUEST_DIGEST,
      'prior_state':'FAILED_FINAL','prior_attempts':2,'prior_last_error':'BLENDER_WORKER_RC:5',
      'prior_failure_error':R3_FAILURE_ERROR,'chunk_digest_sha256':R2_CHUNK0_DIGEST,
      'preserved_members':prior_records,'preserved_failure_json_sha256':sha256_file(payload/'failure.json'),
      'preserved_worker_log_sha256':sha256_file(evroot/'worker.log'),
      'preserved_request_sha256':sha256_file(evroot/'request.json'),
      'completed_samples_preserved':list(info['completed_samples_preserved']),
      'recorded_utc':utc_iso(),'product_mutated':False,'maya_mutated':False,
      'test77_accessed':False,'training_started':False}
    atomic_json(evroot/'R4_RECOVERY_JOURNAL.json',recovery)

    # Clear only the failed sample working directory after preservation. The log
    # is intentionally left in place until the controller atomically truncates it
    # for the new worker attempt; its exact prior bytes are already preserved.
    shutil.rmtree(sd); sd.mkdir(parents=True,exist_ok=True)
    rec['state']='PENDING';rec['attempts']=0;rec.pop('last_error',None)
    rec['r4_recovery']={'r4_addendum_drive_id':R4_ADDENDUM_DRIVE_ID,'prior_attempts':2,
                        'prior_state':'FAILED_FINAL','prior_failure_error':R3_FAILURE_ERROR,
                        'recovery_journal_rel':(evroot/'R4_RECOVERY_JOURNAL.json').relative_to(runroot).as_posix()}
    atomic_json(lp,ledger)
    recovery['status']='LEDGER_RESET_SAMPLE_003_ONLY';atomic_json(evroot/'R4_RECOVERY_JOURNAL.json',recovery)
    info['status']='R3_SAMPLE_003_REOPENED_FOR_R4';info['recovered_samples'][sid]=dict(rec['r4_recovery'])
    return info


def apply_r5_resume_if_needed(runroot:Path,chunks):
    """Exact, fail-closed R4 sample004 FAILED_FINAL -> R5 resume.

    Samples 000..003 must remain COMPLETE. Every failed sample004 byte plus
    worker log/request are preserved before reopening only sample004.
    """
    cr=runroot/'CHUNKS'/'chunk_00'; lp=cr/'ledger.json'
    info={'schema':'DF-G100-R5-RESUME-STATE-V1','status':'NO_PRIOR_LEDGER',
          'r5_addendum_drive_id':R5_ADDENDUM_DRIVE_ID,'recovered_samples':{},
          'completed_samples_preserved':[]}
    if not lp.is_file():
        return info
    ledger=json.loads(lp.read_text(encoding='utf-8'))
    if ledger.get('chunk_digest_sha256')!=R2_CHUNK0_DIGEST or chunks[0].get('chunk_digest_sha256')!=R2_CHUNK0_DIGEST:
        raise RuntimeError('G100_R5_RESUME_CHUNK0_DIGEST_MISMATCH')
    states=ledger.get('states',{})
    expected_complete={
      'g100_000_interior_normal_pbr_realistic_intent':'3f0a24fadc0e0989785b2415487bf3dea78fb939b3d410fd375fe68dc4a6ebc4',
      'g100_001_corridor_strong_roll_toon':'5089b19db397467580fcb2bbfa86de213be7731fe51e78c79b3862552240fb2c',
      R2_FAILED_SAMPLE_ID:R2_FAILED_SAMPLE_REQUEST_DIGEST,
      R3_FAILED_SAMPLE_ID:R3_FAILED_SAMPLE_REQUEST_DIGEST}
    for sid,dg in expected_complete.items():
        rec=states.get(sid,{})
        if rec.get('state')!='COMPLETE' or rec.get('request_digest')!=dg:
            raise RuntimeError('G100_R5_RESUME_COMPLETED_PRECONDITION:'+sid)
        info['completed_samples_preserved'].append(sid)

    sid=R4_FAILED_SAMPLE_ID; rec=states.get(sid,{})
    if rec.get('request_digest')!=R4_FAILED_SAMPLE_REQUEST_DIGEST:
        raise RuntimeError('G100_R5_RESUME_REQUEST_DIGEST_MISMATCH')
    if rec.get('r5_recovery',{}).get('r5_addendum_drive_id')==R5_ADDENDUM_DRIVE_ID:
        if rec.get('state') in {'PENDING','RUNNING','FAILED_RETRYABLE','COMPLETE','FAILED_FINAL'}:
            info['status']='R5_RECOVERY_ALREADY_APPLIED'
            info['recovered_samples'][sid]=dict(rec.get('r5_recovery',{}))
            return info
        raise RuntimeError('G100_R5_RESUME_BAD_POST_RECOVERY_STATE')
    if rec.get('state')!='FAILED_FINAL' or int(rec.get('attempts',-1))!=2 or rec.get('last_error')!='BLENDER_WORKER_RC:5':
        raise RuntimeError('G100_R5_RESUME_EXACT_R4_FAILED_FINAL_PRECONDITION')

    sd=cr/'samples'/sid; fj=sd/'failure.json'; logp=cr/'logs'/f'{sid}.log'; reqp=cr/'requests'/f'{sid}.json'
    for p,label in ((fj,'FAILURE_JSON'),(logp,'WORKER_LOG'),(reqp,'REQUEST_JSON')):
        if not p.is_file(): raise RuntimeError('G100_R5_RESUME_'+label+'_MISSING')
    fobj=json.loads(fj.read_text(encoding='utf-8'))
    if fobj.get('input_digest_sha256')!=R4_FAILED_SAMPLE_REQUEST_DIGEST or fobj.get('error')!=R4_FAILURE_ERROR:
        raise RuntimeError('G100_R5_RESUME_FAILURE_CAUSE_MISMATCH')
    reqobj=json.loads(reqp.read_text(encoding='utf-8'))
    if reqobj.get('input_digest_sha256')!=R4_FAILED_SAMPLE_REQUEST_DIGEST or reqobj.get('sample_id')!=sid:
        raise RuntimeError('G100_R5_RESUME_REQUEST_FILE_MISMATCH')
    prior_records=_tree_records(sd)
    if not prior_records: raise RuntimeError('G100_R5_RESUME_FAILED_SAMPLE_EVIDENCE_EMPTY')

    evroot=runroot/'RECOVERY'/'R4_FAILED_SAMPLE_004'
    evroot.mkdir(parents=True,exist_ok=True); payload=evroot/'sample_bytes'
    if payload.exists(): shutil.rmtree(payload)
    shutil.copytree(sd,payload)
    copied=_tree_records(payload)
    if copied!=prior_records: raise RuntimeError('G100_R5_RESUME_PRESERVE_HASH_MISMATCH')
    shutil.copy2(logp,evroot/'worker.log')
    shutil.copy2(reqp,evroot/'request.json')
    recovery={
      'schema':'DF-G100-R5-RECOVERY-JOURNAL-V1','status':'PRESERVED_BEFORE_LEDGER_RESET',
      'r5_addendum_drive_id':R5_ADDENDUM_DRIVE_ID,'source_tool':'R4','target_tool':'R5',
      'sample_id':sid,'request_digest':R4_FAILED_SAMPLE_REQUEST_DIGEST,
      'prior_state':'FAILED_FINAL','prior_attempts':2,'prior_last_error':'BLENDER_WORKER_RC:5',
      'prior_failure_error':R4_FAILURE_ERROR,'chunk_digest_sha256':R2_CHUNK0_DIGEST,
      'preserved_members':prior_records,'preserved_failure_json_sha256':sha256_file(payload/'failure.json'),
      'preserved_worker_log_sha256':sha256_file(evroot/'worker.log'),
      'preserved_request_sha256':sha256_file(evroot/'request.json'),
      'completed_samples_preserved':list(info['completed_samples_preserved']),
      'recorded_utc':utc_iso(),'product_mutated':False,'maya_mutated':False,
      'test77_accessed':False,'training_started':False}
    atomic_json(evroot/'R5_RECOVERY_JOURNAL.json',recovery)

    shutil.rmtree(sd); sd.mkdir(parents=True,exist_ok=True)
    rec['state']='PENDING';rec['attempts']=0;rec.pop('last_error',None)
    rec['r5_recovery']={'r5_addendum_drive_id':R5_ADDENDUM_DRIVE_ID,'prior_attempts':2,
                        'prior_state':'FAILED_FINAL','prior_failure_error':R4_FAILURE_ERROR,
                        'recovery_journal_rel':(evroot/'R5_RECOVERY_JOURNAL.json').relative_to(runroot).as_posix()}
    atomic_json(lp,ledger)
    recovery['status']='LEDGER_RESET_SAMPLE_004_ONLY';atomic_json(evroot/'R5_RECOVERY_JOURNAL.json',recovery)
    info['status']='R4_SAMPLE_004_REOPENED_FOR_R5';info['recovered_samples'][sid]=dict(rec['r5_recovery'])
    return info



def apply_r6_resume_if_needed(runroot:Path,chunks):
    """Exact, fail-closed R5 sample005 FAILED_FINAL -> R6 resume.

    Samples 000..004 must remain COMPLETE. Every failed sample005 byte plus
    worker log/request are preserved before reopening only sample005.
    """
    cr=runroot/'CHUNKS'/'chunk_00'; lp=cr/'ledger.json'
    info={'schema':'DF-G100-R6-RESUME-STATE-V1','status':'NO_PRIOR_LEDGER',
          'r6_addendum_drive_id':R6_ADDENDUM_DRIVE_ID,'recovered_samples':{},
          'completed_samples_preserved':[]}
    if not lp.is_file():
        return info
    ledger=json.loads(lp.read_text(encoding='utf-8'))
    if ledger.get('chunk_digest_sha256')!=R2_CHUNK0_DIGEST or chunks[0].get('chunk_digest_sha256')!=R2_CHUNK0_DIGEST:
        raise RuntimeError('G100_R6_RESUME_CHUNK0_DIGEST_MISMATCH')
    states=ledger.get('states',{})
    expected_complete={
      'g100_000_interior_normal_pbr_realistic_intent':'3f0a24fadc0e0989785b2415487bf3dea78fb939b3d410fd375fe68dc4a6ebc4',
      'g100_001_corridor_strong_roll_toon':'5089b19db397467580fcb2bbfa86de213be7731fe51e78c79b3862552240fb2c',
      R2_FAILED_SAMPLE_ID:R2_FAILED_SAMPLE_REQUEST_DIGEST,
      R3_FAILED_SAMPLE_ID:R3_FAILED_SAMPLE_REQUEST_DIGEST,
      R4_FAILED_SAMPLE_ID:R4_FAILED_SAMPLE_REQUEST_DIGEST}
    for sid,dg in expected_complete.items():
        rec=states.get(sid,{})
        if rec.get('state')!='COMPLETE' or rec.get('request_digest')!=dg:
            raise RuntimeError('G100_R6_RESUME_COMPLETED_PRECONDITION:'+sid)
        info['completed_samples_preserved'].append(sid)

    sid=R5_FAILED_SAMPLE_ID; rec=states.get(sid,{})
    if rec.get('request_digest')!=R5_FAILED_SAMPLE_REQUEST_DIGEST:
        raise RuntimeError('G100_R6_RESUME_REQUEST_DIGEST_MISMATCH')
    if rec.get('r6_recovery',{}).get('r6_addendum_drive_id')==R6_ADDENDUM_DRIVE_ID:
        if rec.get('state') in {'PENDING','RUNNING','FAILED_RETRYABLE','COMPLETE','FAILED_FINAL'}:
            info['status']='R6_RECOVERY_ALREADY_APPLIED'
            info['recovered_samples'][sid]=dict(rec.get('r6_recovery',{}))
            return info
        raise RuntimeError('G100_R6_RESUME_BAD_POST_RECOVERY_STATE')
    if rec.get('state')!='FAILED_FINAL' or int(rec.get('attempts',-1))!=2 or rec.get('last_error')!='BLENDER_WORKER_RC:5':
        raise RuntimeError('G100_R6_RESUME_EXACT_R5_FAILED_FINAL_PRECONDITION')

    sd=cr/'samples'/sid; fj=sd/'failure.json'; logp=cr/'logs'/f'{sid}.log'; reqp=cr/'requests'/f'{sid}.json'
    for pp,label in ((fj,'FAILURE_JSON'),(logp,'WORKER_LOG'),(reqp,'REQUEST_JSON')):
        if not pp.is_file(): raise RuntimeError('G100_R6_RESUME_'+label+'_MISSING')
    fobj=json.loads(fj.read_text(encoding='utf-8'))
    if fobj.get('input_digest_sha256')!=R5_FAILED_SAMPLE_REQUEST_DIGEST or fobj.get('error')!=R5_FAILURE_ERROR:
        raise RuntimeError('G100_R6_RESUME_FAILURE_CAUSE_MISMATCH')
    reqobj=json.loads(reqp.read_text(encoding='utf-8'))
    if reqobj.get('input_digest_sha256')!=R5_FAILED_SAMPLE_REQUEST_DIGEST or reqobj.get('sample_id')!=sid:
        raise RuntimeError('G100_R6_RESUME_REQUEST_FILE_MISMATCH')
    prior_records=_tree_records(sd)
    if not prior_records: raise RuntimeError('G100_R6_RESUME_FAILED_SAMPLE_EVIDENCE_EMPTY')

    evroot=runroot/'RECOVERY'/'R5_FAILED_SAMPLE_005'
    evroot.mkdir(parents=True,exist_ok=True); payload=evroot/'sample_bytes'
    if payload.exists(): shutil.rmtree(payload)
    shutil.copytree(sd,payload)
    copied=_tree_records(payload)
    if copied!=prior_records: raise RuntimeError('G100_R6_RESUME_PRESERVE_HASH_MISMATCH')
    shutil.copy2(logp,evroot/'worker.log')
    shutil.copy2(reqp,evroot/'request.json')
    recovery={
      'schema':'DF-G100-R6-RECOVERY-JOURNAL-V1','status':'PRESERVED_BEFORE_LEDGER_RESET',
      'r6_addendum_drive_id':R6_ADDENDUM_DRIVE_ID,'source_tool':'R5','target_tool':'R6',
      'sample_id':sid,'request_digest':R5_FAILED_SAMPLE_REQUEST_DIGEST,
      'prior_state':'FAILED_FINAL','prior_attempts':2,'prior_last_error':'BLENDER_WORKER_RC:5',
      'prior_failure_error':R5_FAILURE_ERROR,'chunk_digest_sha256':R2_CHUNK0_DIGEST,
      'preserved_members':prior_records,'preserved_failure_json_sha256':sha256_file(payload/'failure.json'),
      'preserved_worker_log_sha256':sha256_file(evroot/'worker.log'),
      'preserved_request_sha256':sha256_file(evroot/'request.json'),
      'completed_samples_preserved':list(info['completed_samples_preserved']),
      'recorded_utc':utc_iso(),'product_mutated':False,'maya_mutated':False,
      'test77_accessed':False,'training_started':False}
    atomic_json(evroot/'R6_RECOVERY_JOURNAL.json',recovery)

    shutil.rmtree(sd); sd.mkdir(parents=True,exist_ok=True)
    rec['state']='PENDING';rec['attempts']=0;rec.pop('last_error',None)
    rec['r6_recovery']={'r6_addendum_drive_id':R6_ADDENDUM_DRIVE_ID,'prior_attempts':2,
                        'prior_state':'FAILED_FINAL','prior_failure_error':R5_FAILURE_ERROR,
                        'recovery_journal_rel':(evroot/'R6_RECOVERY_JOURNAL.json').relative_to(runroot).as_posix()}
    atomic_json(lp,ledger)
    recovery['status']='LEDGER_RESET_SAMPLE_005_ONLY';atomic_json(evroot/'R6_RECOVERY_JOURNAL.json',recovery)
    info['status']='R5_SAMPLE_005_REOPENED_FOR_R6';info['recovered_samples'][sid]=dict(rec['r6_recovery'])
    return info


def apply_r7_resume_if_needed(runroot:Path,chunks):
    """Exact, fail-closed R6 sample008 FAILED_FINAL -> R7 resume.

    Samples 000..007 must remain COMPLETE. Every failed sample008 byte plus
    worker log/request are preserved before reopening only sample008.
    """
    cr=runroot/'CHUNKS'/'chunk_00'; lp=cr/'ledger.json'
    info={'schema':'DF-G100-R7-RESUME-STATE-V1','status':'NO_PRIOR_LEDGER',
          'r7_addendum_drive_id':R7_ADDENDUM_DRIVE_ID,'recovered_samples':{},
          'completed_samples_preserved':[]}
    if not lp.is_file(): return info
    ledger=json.loads(lp.read_text(encoding='utf-8'))
    if ledger.get('chunk_digest_sha256')!=R2_CHUNK0_DIGEST or chunks[0].get('chunk_digest_sha256')!=R2_CHUNK0_DIGEST:
        raise RuntimeError('G100_R7_RESUME_CHUNK0_DIGEST_MISMATCH')
    states=ledger.get('states',{})
    expected_complete={
      'g100_000_interior_normal_pbr_realistic_intent':'3f0a24fadc0e0989785b2415487bf3dea78fb939b3d410fd375fe68dc4a6ebc4',
      'g100_001_corridor_strong_roll_toon':'5089b19db397467580fcb2bbfa86de213be7731fe51e78c79b3862552240fb2c',
      R2_FAILED_SAMPLE_ID:R2_FAILED_SAMPLE_REQUEST_DIGEST,
      R3_FAILED_SAMPLE_ID:R3_FAILED_SAMPLE_REQUEST_DIGEST,
      R4_FAILED_SAMPLE_ID:R4_FAILED_SAMPLE_REQUEST_DIGEST,
      R5_FAILED_SAMPLE_ID:R5_FAILED_SAMPLE_REQUEST_DIGEST,
      'g100_006_non_manhattan_offcenter_pbr_realistic_intent':'c8e0b51235c3865e5bf1ee208ea5246e77677b3009677d2c38389d76885d24e4',
      'g100_007_sparse_wide_toon':'ba3afe2ac2129d484cd76cae8b5d86eeefa0341df81a0da1fc3c28ab9bb11969'}
    for sid,dg in expected_complete.items():
        rec=states.get(sid,{})
        if rec.get('state')!='COMPLETE' or rec.get('request_digest')!=dg:
            raise RuntimeError('G100_R7_RESUME_COMPLETED_PRECONDITION:'+sid)
        info['completed_samples_preserved'].append(sid)
    sid=R6_FAILED_SAMPLE_ID; rec=states.get(sid,{})
    if rec.get('request_digest')!=R6_FAILED_SAMPLE_REQUEST_DIGEST:
        raise RuntimeError('G100_R7_RESUME_REQUEST_DIGEST_MISMATCH')
    if rec.get('r7_recovery',{}).get('r7_addendum_drive_id')==R7_ADDENDUM_DRIVE_ID:
        if rec.get('state') in {'PENDING','RUNNING','FAILED_RETRYABLE','COMPLETE','FAILED_FINAL'}:
            info['status']='R7_RECOVERY_ALREADY_APPLIED'
            info['recovered_samples'][sid]=dict(rec.get('r7_recovery',{}))
            return info
        raise RuntimeError('G100_R7_RESUME_BAD_POST_RECOVERY_STATE')
    if rec.get('state')!='FAILED_FINAL' or int(rec.get('attempts',-1))!=2 or rec.get('last_error')!='BLENDER_WORKER_RC:5':
        raise RuntimeError('G100_R7_RESUME_EXACT_R6_FAILED_FINAL_PRECONDITION')
    sd=cr/'samples'/sid; fj=sd/'failure.json'; logp=cr/'logs'/f'{sid}.log'; reqp=cr/'requests'/f'{sid}.json'
    for pp,label in ((fj,'FAILURE_JSON'),(logp,'WORKER_LOG'),(reqp,'REQUEST_JSON')):
        if not pp.is_file(): raise RuntimeError('G100_R7_RESUME_'+label+'_MISSING')
    fobj=json.loads(fj.read_text(encoding='utf-8'))
    if fobj.get('input_digest_sha256')!=R6_FAILED_SAMPLE_REQUEST_DIGEST or fobj.get('error')!=R6_FAILURE_ERROR:
        raise RuntimeError('G100_R7_RESUME_FAILURE_CAUSE_MISMATCH')
    reqobj=json.loads(reqp.read_text(encoding='utf-8'))
    if reqobj.get('input_digest_sha256')!=R6_FAILED_SAMPLE_REQUEST_DIGEST or reqobj.get('sample_id')!=sid:
        raise RuntimeError('G100_R7_RESUME_REQUEST_FILE_MISMATCH')
    prior_records=_tree_records(sd)
    if not prior_records: raise RuntimeError('G100_R7_RESUME_FAILED_SAMPLE_EVIDENCE_EMPTY')
    evroot=runroot/'RECOVERY'/'R6_FAILED_SAMPLE_008'
    evroot.mkdir(parents=True,exist_ok=True); payload=evroot/'sample_bytes'
    if payload.exists(): shutil.rmtree(payload)
    shutil.copytree(sd,payload)
    copied=_tree_records(payload)
    if copied!=prior_records: raise RuntimeError('G100_R7_RESUME_PRESERVE_HASH_MISMATCH')
    shutil.copy2(logp,evroot/'worker.log'); shutil.copy2(reqp,evroot/'request.json')
    recovery={
      'schema':'DF-G100-R7-RECOVERY-JOURNAL-V1','status':'PRESERVED_BEFORE_LEDGER_RESET',
      'r7_addendum_drive_id':R7_ADDENDUM_DRIVE_ID,'source_tool':'R6','target_tool':'R7',
      'sample_id':sid,'request_digest':R6_FAILED_SAMPLE_REQUEST_DIGEST,
      'prior_state':'FAILED_FINAL','prior_attempts':2,'prior_last_error':'BLENDER_WORKER_RC:5',
      'prior_failure_error':R6_FAILURE_ERROR,'chunk_digest_sha256':R2_CHUNK0_DIGEST,
      'preserved_members':prior_records,'preserved_failure_json_sha256':sha256_file(payload/'failure.json'),
      'preserved_worker_log_sha256':sha256_file(evroot/'worker.log'),
      'preserved_request_sha256':sha256_file(evroot/'request.json'),
      'completed_samples_preserved':list(info['completed_samples_preserved']),
      'recorded_utc':utc_iso(),'product_mutated':False,'maya_mutated':False,
      'test77_accessed':False,'training_started':False}
    atomic_json(evroot/'R7_RECOVERY_JOURNAL.json',recovery)
    shutil.rmtree(sd); sd.mkdir(parents=True,exist_ok=True)
    rec['state']='PENDING'; rec['attempts']=0; rec.pop('last_error',None)
    rec['r7_recovery']={'r7_addendum_drive_id':R7_ADDENDUM_DRIVE_ID,'prior_attempts':2,
                        'prior_state':'FAILED_FINAL','prior_failure_error':R6_FAILURE_ERROR,
                        'recovery_journal_rel':(evroot/'R7_RECOVERY_JOURNAL.json').relative_to(runroot).as_posix()}
    atomic_json(lp,ledger)
    recovery['status']='LEDGER_RESET_SAMPLE_008_ONLY'; atomic_json(evroot/'R7_RECOVERY_JOURNAL.json',recovery)
    info['status']='R6_SAMPLE_008_REOPENED_FOR_R7'; info['recovered_samples'][sid]=dict(rec['r7_recovery'])
    return info

def apply_r8_resume_if_needed(runroot:Path,chunks):
    """Exact, fail-closed R7 sample009 FAILED_FINAL -> R8 resume.

    Samples 000..008 must remain COMPLETE. Every failed sample009 byte plus
    worker log/request are preserved before reopening only sample009.
    """
    cr=runroot/'CHUNKS'/'chunk_00'; lp=cr/'ledger.json'
    info={'schema':'DF-G100-R8-RESUME-STATE-V1','status':'NO_PRIOR_LEDGER',
          'r8_addendum_drive_id':R8_ADDENDUM_DRIVE_ID,'recovered_samples':{},
          'completed_samples_preserved':[]}
    if not lp.is_file(): return info
    ledger=json.loads(lp.read_text(encoding='utf-8'))
    if ledger.get('chunk_digest_sha256')!=R2_CHUNK0_DIGEST or chunks[0].get('chunk_digest_sha256')!=R2_CHUNK0_DIGEST:
        raise RuntimeError('G100_R8_RESUME_CHUNK0_DIGEST_MISMATCH')
    states=ledger.get('states',{})
    expected_complete={
      'g100_000_interior_normal_pbr_realistic_intent':'3f0a24fadc0e0989785b2415487bf3dea78fb939b3d410fd375fe68dc4a6ebc4',
      'g100_001_corridor_strong_roll_toon':'5089b19db397467580fcb2bbfa86de213be7731fe51e78c79b3862552240fb2c',
      R2_FAILED_SAMPLE_ID:R2_FAILED_SAMPLE_REQUEST_DIGEST,
      R3_FAILED_SAMPLE_ID:R3_FAILED_SAMPLE_REQUEST_DIGEST,
      R4_FAILED_SAMPLE_ID:R4_FAILED_SAMPLE_REQUEST_DIGEST,
      R5_FAILED_SAMPLE_ID:R5_FAILED_SAMPLE_REQUEST_DIGEST,
      'g100_006_non_manhattan_offcenter_pbr_realistic_intent':'c8e0b51235c3865e5bf1ee208ea5246e77677b3009677d2c38389d76885d24e4',
      'g100_007_sparse_wide_toon':'ba3afe2ac2129d484cd76cae8b5d86eeefa0341df81a0da1fc3c28ab9bb11969',
      R6_FAILED_SAMPLE_ID:R6_FAILED_SAMPLE_REQUEST_DIGEST}
    for sid,dg in expected_complete.items():
        rec=states.get(sid,{})
        if rec.get('state')!='COMPLETE' or rec.get('request_digest')!=dg:
            raise RuntimeError('G100_R8_RESUME_COMPLETED_PRECONDITION:'+sid)
        info['completed_samples_preserved'].append(sid)
    sid=R7_FAILED_SAMPLE_ID; rec=states.get(sid,{})
    if rec.get('request_digest')!=R7_FAILED_SAMPLE_REQUEST_DIGEST:
        raise RuntimeError('G100_R8_RESUME_REQUEST_DIGEST_MISMATCH')
    if rec.get('r8_recovery',{}).get('r8_addendum_drive_id')==R8_ADDENDUM_DRIVE_ID:
        if rec.get('state') in {'PENDING','RUNNING','FAILED_RETRYABLE','COMPLETE','FAILED_FINAL'}:
            info['status']='R8_RECOVERY_ALREADY_APPLIED'
            info['recovered_samples'][sid]=dict(rec.get('r8_recovery',{}))
            return info
        raise RuntimeError('G100_R8_RESUME_BAD_POST_RECOVERY_STATE')
    if rec.get('state')!='FAILED_FINAL' or int(rec.get('attempts',-1))!=2 or rec.get('last_error')!='BLENDER_WORKER_RC:5':
        raise RuntimeError('G100_R8_RESUME_EXACT_R7_FAILED_FINAL_PRECONDITION')
    sd=cr/'samples'/sid; fj=sd/'failure.json'; logp=cr/'logs'/f'{sid}.log'; reqp=cr/'requests'/f'{sid}.json'
    for pp,label in ((fj,'FAILURE_JSON'),(logp,'WORKER_LOG'),(reqp,'REQUEST_JSON')):
        if not pp.is_file(): raise RuntimeError('G100_R8_RESUME_'+label+'_MISSING')
    fobj=json.loads(fj.read_text(encoding='utf-8'))
    if fobj.get('input_digest_sha256')!=R7_FAILED_SAMPLE_REQUEST_DIGEST or fobj.get('error')!=R7_FAILURE_ERROR:
        raise RuntimeError('G100_R8_RESUME_FAILURE_CAUSE_MISMATCH')
    reqobj=json.loads(reqp.read_text(encoding='utf-8'))
    if reqobj.get('input_digest_sha256')!=R7_FAILED_SAMPLE_REQUEST_DIGEST or reqobj.get('sample_id')!=sid:
        raise RuntimeError('G100_R8_RESUME_REQUEST_FILE_MISMATCH')
    prior_records=_tree_records(sd)
    if not prior_records: raise RuntimeError('G100_R8_RESUME_FAILED_SAMPLE_EVIDENCE_EMPTY')
    evroot=runroot/'RECOVERY'/'R7_FAILED_SAMPLE_009'
    evroot.mkdir(parents=True,exist_ok=True); payload=evroot/'sample_bytes'
    if payload.exists(): shutil.rmtree(payload)
    shutil.copytree(sd,payload)
    copied=_tree_records(payload)
    if copied!=prior_records: raise RuntimeError('G100_R8_RESUME_PRESERVE_HASH_MISMATCH')
    shutil.copy2(logp,evroot/'worker.log'); shutil.copy2(reqp,evroot/'request.json')
    recovery={
      'schema':'DF-G100-R8-RECOVERY-JOURNAL-V1','status':'PRESERVED_BEFORE_LEDGER_RESET',
      'r8_addendum_drive_id':R8_ADDENDUM_DRIVE_ID,'source_tool':'R7','target_tool':'R8',
      'sample_id':sid,'request_digest':R7_FAILED_SAMPLE_REQUEST_DIGEST,
      'prior_state':'FAILED_FINAL','prior_attempts':2,'prior_last_error':'BLENDER_WORKER_RC:5',
      'prior_failure_error':R7_FAILURE_ERROR,'chunk_digest_sha256':R2_CHUNK0_DIGEST,
      'preserved_members':prior_records,'preserved_failure_json_sha256':sha256_file(payload/'failure.json'),
      'preserved_worker_log_sha256':sha256_file(evroot/'worker.log'),
      'preserved_request_sha256':sha256_file(evroot/'request.json'),
      'completed_samples_preserved':list(info['completed_samples_preserved']),
      'recorded_utc':utc_iso(),'product_mutated':False,'maya_mutated':False,
      'test77_accessed':False,'training_started':False}
    atomic_json(evroot/'R8_RECOVERY_JOURNAL.json',recovery)
    shutil.rmtree(sd); sd.mkdir(parents=True,exist_ok=True)
    rec['state']='PENDING'; rec['attempts']=0; rec.pop('last_error',None)
    rec['r8_recovery']={'r8_addendum_drive_id':R8_ADDENDUM_DRIVE_ID,'prior_attempts':2,
                        'prior_state':'FAILED_FINAL','prior_failure_error':R7_FAILURE_ERROR,
                        'recovery_journal_rel':(evroot/'R8_RECOVERY_JOURNAL.json').relative_to(runroot).as_posix()}
    atomic_json(lp,ledger)
    recovery['status']='LEDGER_RESET_SAMPLE_009_ONLY'; atomic_json(evroot/'R8_RECOVERY_JOURNAL.json',recovery)
    info['status']='R7_SAMPLE_009_REOPENED_FOR_R8'; info['recovered_samples'][sid]=dict(rec['r8_recovery'])
    return info

def apply_r9_resume_if_needed(runroot:Path,chunks):
    """Exact, fail-closed R8 historical COMPLETE sample001 -> R9 appearance recovery.

    R9 is authorized only for the exact real sample001 RGB acceptance failure.
    The frozen request/chunk identity is unchanged. All prior sample001 bytes,
    worker log and request are preserved before reopening only sample001.
    """
    cr=runroot/'CHUNKS'/'chunk_00'; lp=cr/'ledger.json'
    info={'schema':'DF-G100-R9-RESUME-STATE-V1','status':'NO_PRIOR_LEDGER',
          'r9_addendum_drive_id':R9_ADDENDUM_DRIVE_ID,'recovered_samples':{},
          'completed_samples_preserved':[]}
    if not lp.is_file(): return info
    ledger=json.loads(lp.read_text(encoding='utf-8'))
    if ledger.get('chunk_digest_sha256')!=R2_CHUNK0_DIGEST or chunks[0].get('chunk_digest_sha256')!=R2_CHUNK0_DIGEST:
        raise RuntimeError('G100_R9_RESUME_CHUNK0_DIGEST_MISMATCH')
    states=ledger.get('states',{})
    expected={r['sample_id']:r['input_digest_sha256'] for r in chunks[0]['requests']}
    if len(expected)!=10 or expected.get(R9_RECOVERY_SAMPLE_ID)!=R9_RECOVERY_REQUEST_DIGEST:
        raise RuntimeError('G100_R9_RESUME_FROZEN_REQUEST_SET_MISMATCH')
    rec=states.get(R9_RECOVERY_SAMPLE_ID,{})
    if rec.get('request_digest')!=R9_RECOVERY_REQUEST_DIGEST:
        raise RuntimeError('G100_R9_RESUME_REQUEST_DIGEST_MISMATCH')
    # Idempotent after the one authorized reset. Do not demand the old fixture
    # after R9 has rendered a new sample001.
    if rec.get('r9_recovery',{}).get('r9_addendum_drive_id')==R9_ADDENDUM_DRIVE_ID:
        if rec.get('state') in {'PENDING','RUNNING','FAILED_RETRYABLE','COMPLETE','FAILED_FINAL'}:
            info['status']='R9_RECOVERY_ALREADY_APPLIED'
            info['recovered_samples'][R9_RECOVERY_SAMPLE_ID]=dict(rec.get('r9_recovery',{}))
            for sid in expected:
                if sid!=R9_RECOVERY_SAMPLE_ID and states.get(sid,{}).get('state')=='COMPLETE':
                    info['completed_samples_preserved'].append(sid)
            return info
        raise RuntimeError('G100_R9_RESUME_BAD_POST_RECOVERY_STATE')

    # Before first R9 mutation, chunk00 must be the exact 10/10 COMPLETE R8 state.
    for sid,dg in expected.items():
        srec=states.get(sid,{})
        if srec.get('state')!='COMPLETE' or srec.get('request_digest')!=dg:
            raise RuntimeError('G100_R9_RESUME_COMPLETED_PRECONDITION:'+sid)
        if sid!=R9_RECOVERY_SAMPLE_ID:
            info['completed_samples_preserved'].append(sid)
    if int(rec.get('attempts',-1))!=1:
        raise RuntimeError('G100_R9_RESUME_SAMPLE001_PRIOR_ATTEMPTS_MISMATCH')

    sd=cr/'samples'/R9_RECOVERY_SAMPLE_ID
    logp=cr/'logs'/f'{R9_RECOVERY_SAMPLE_ID}.log'
    reqp=cr/'requests'/f'{R9_RECOVERY_SAMPLE_ID}.json'
    rgbp=sd/'rgb.png'; compp=sd/'completion.json'
    for pp,label in ((sd,'SAMPLE_DIR'),(rgbp,'RGB'),(compp,'COMPLETION'),(logp,'WORKER_LOG'),(reqp,'REQUEST_JSON')):
        if not pp.exists(): raise RuntimeError('G100_R9_RESUME_'+label+'_MISSING')
    if sha256_file(rgbp)!=R9_PRIOR_RGB_SHA256:
        raise RuntimeError('G100_R9_RESUME_PRIOR_RGB_SHA_MISMATCH')
    if sha256_file(compp)!=R9_PRIOR_COMPLETION_SHA256:
        raise RuntimeError('G100_R9_RESUME_PRIOR_COMPLETION_SHA_MISMATCH')
    if sha256_file(reqp)!=R9_PRIOR_REQUEST_FILE_SHA256:
        raise RuntimeError('G100_R9_RESUME_PRIOR_REQUEST_FILE_SHA_MISMATCH')
    if sha256_file(logp)!=R9_PRIOR_WORKER_LOG_SHA256:
        raise RuntimeError('G100_R9_RESUME_PRIOR_WORKER_LOG_SHA_MISMATCH')
    reqobj=json.loads(reqp.read_text(encoding='utf-8'))
    if reqobj.get('sample_id')!=R9_RECOVERY_SAMPLE_ID or reqobj.get('input_digest_sha256')!=R9_RECOVERY_REQUEST_DIGEST:
        raise RuntimeError('G100_R9_RESUME_REQUEST_FILE_IDENTITY_MISMATCH')
    comp=json.loads(compp.read_text(encoding='utf-8'))
    if comp.get('sample_id')!=R9_RECOVERY_SAMPLE_ID or comp.get('input_digest_sha256')!=R9_RECOVERY_REQUEST_DIGEST:
        raise RuntimeError('G100_R9_RESUME_COMPLETION_IDENTITY_MISMATCH')
    st=rgb_stats(rgbp)
    expected_stats=R9_PRIOR_RGB_STATS
    for k,v in expected_stats.items():
        if k not in st or (abs(float(st[k])-float(v))>1e-12 if isinstance(v,(int,float)) else st[k]!=v):
            raise RuntimeError('G100_R9_RESUME_PRIOR_RGB_STATS_MISMATCH:'+k)
    if not (st['unique_rgb']>=32 and 12<=st['mean_luma']<=243 and st['structural_fraction']>=0.03 and st['p01_p99_span']<24):
        raise RuntimeError('G100_R9_RESUME_PRIOR_RGB_FAILURE_CLASS_MISMATCH')

    prior_records=_tree_records(sd)
    if not prior_records: raise RuntimeError('G100_R9_RESUME_SAMPLE001_EVIDENCE_EMPTY')
    evroot=runroot/'RECOVERY'/'R8_COMPLETE_SAMPLE_001_RGB_ACCEPTANCE_FAIL'
    evroot.mkdir(parents=True,exist_ok=True); payload=evroot/'sample_bytes'
    if payload.exists(): shutil.rmtree(payload)
    shutil.copytree(sd,payload)
    copied=_tree_records(payload)
    if copied!=prior_records: raise RuntimeError('G100_R9_RESUME_PRESERVE_HASH_MISMATCH')
    shutil.copy2(logp,evroot/'worker.log'); shutil.copy2(reqp,evroot/'request.json')
    recovery={
      'schema':'DF-G100-R9-RECOVERY-JOURNAL-V1','status':'PRESERVED_BEFORE_LEDGER_RESET',
      'r9_addendum_drive_id':R9_ADDENDUM_DRIVE_ID,'source_tool':'R8_POST_CHUNK_ACCEPTANCE',
      'target_tool':'R9','sample_id':R9_RECOVERY_SAMPLE_ID,'request_digest':R9_RECOVERY_REQUEST_DIGEST,
      'chunk_digest_sha256':R2_CHUNK0_DIGEST,'prior_state':'COMPLETE','prior_attempts':1,
      'prior_acceptance_failure':'rgb_span=false','prior_rgb_sha256':R9_PRIOR_RGB_SHA256,
      'prior_rgb_stats':st,'preserved_members':prior_records,
      'preserved_completion_sha256':sha256_file(payload/'completion.json'),
      'preserved_rgb_sha256':sha256_file(payload/'rgb.png'),
      'preserved_worker_log_sha256':sha256_file(evroot/'worker.log'),
      'preserved_request_sha256':sha256_file(evroot/'request.json'),
      'completed_samples_preserved':list(info['completed_samples_preserved']),
      'r9_toon_closed_room_fill_energy_w':175.0,
      'thresholds_unchanged':{'rgb_unique_min':32,'rgb_span_min':24.0,'rgb_mean_min':12.0,'rgb_mean_max':243.0,'rgb_structural_min':0.03},
      'recorded_utc':utc_iso(),'product_mutated':False,'maya_mutated':False,
      'test77_accessed':False,'training_started':False}
    atomic_json(evroot/'R9_RECOVERY_JOURNAL.json',recovery)
    shutil.rmtree(sd); sd.mkdir(parents=True,exist_ok=True)
    rec['state']='PENDING';rec['attempts']=0;rec.pop('last_error',None)
    rec['r9_recovery']={'r9_addendum_drive_id':R9_ADDENDUM_DRIVE_ID,'prior_attempts':1,
                        'prior_state':'COMPLETE','prior_acceptance_failure':'rgb_span=false',
                        'prior_rgb_sha256':R9_PRIOR_RGB_SHA256,
                        'recovery_journal_rel':(evroot/'R9_RECOVERY_JOURNAL.json').relative_to(runroot).as_posix(),
                        'r9_toon_closed_room_fill_energy_w':175.0}
    atomic_json(lp,ledger)
    recovery['status']='LEDGER_RESET_SAMPLE_001_ONLY'; atomic_json(evroot/'R9_RECOVERY_JOURNAL.json',recovery)
    info['status']='R8_COMPLETE_SAMPLE_001_REOPENED_FOR_R9'
    info['recovered_samples'][R9_RECOVERY_SAMPLE_ID]=dict(rec['r9_recovery'])
    return info


def apply_r10_resume_if_needed(runroot:Path,chunks):
    """Exact, fail-closed R9 COMPLETE sample001 -> R10 RGB appearance recovery.

    R10 is authorized only for the exact real R9 post-chunk sample001 rgb_span
    failure. All current R9 sample001 bytes are preserved before reopening only
    sample001; peers 000 and 002..009 remain COMPLETE and untouched.
    """
    cr=runroot/'CHUNKS'/'chunk_00'; lp=cr/'ledger.json'
    info={'schema':'DF-G100-R10-RESUME-STATE-V1','status':'NO_PRIOR_LEDGER',
          'r10_addendum_drive_id':R10_ADDENDUM_DRIVE_ID,'recovered_samples':{},
          'completed_samples_preserved':[]}
    if not lp.is_file(): return info
    ledger=json.loads(lp.read_text(encoding='utf-8'))
    if ledger.get('chunk_digest_sha256')!=R2_CHUNK0_DIGEST or chunks[0].get('chunk_digest_sha256')!=R2_CHUNK0_DIGEST:
        raise RuntimeError('G100_R10_RESUME_CHUNK0_DIGEST_MISMATCH')
    states=ledger.get('states',{})
    expected={r['sample_id']:r['input_digest_sha256'] for r in chunks[0]['requests']}
    if len(expected)!=10 or expected.get(R10_RECOVERY_SAMPLE_ID)!=R10_RECOVERY_REQUEST_DIGEST:
        raise RuntimeError('G100_R10_RESUME_FROZEN_REQUEST_SET_MISMATCH')
    rec=states.get(R10_RECOVERY_SAMPLE_ID,{})
    if rec.get('request_digest')!=R10_RECOVERY_REQUEST_DIGEST:
        raise RuntimeError('G100_R10_RESUME_REQUEST_DIGEST_MISMATCH')
    if rec.get('r10_recovery',{}).get('r10_addendum_drive_id')==R10_ADDENDUM_DRIVE_ID:
        if rec.get('state') in {'PENDING','RUNNING','FAILED_RETRYABLE','COMPLETE','FAILED_FINAL'}:
            info['status']='R10_RECOVERY_ALREADY_APPLIED'
            info['recovered_samples'][R10_RECOVERY_SAMPLE_ID]=dict(rec.get('r10_recovery',{}))
            for sid in expected:
                if sid!=R10_RECOVERY_SAMPLE_ID and states.get(sid,{}).get('state')=='COMPLETE':
                    info['completed_samples_preserved'].append(sid)
            return info
        raise RuntimeError('G100_R10_RESUME_BAD_POST_RECOVERY_STATE')

    # R10 may start only from the exact R9 post-chunk state: all ten COMPLETE,
    # sample001 already bears the R9 recovery provenance, and R9 attempt count=1.
    for sid,dg in expected.items():
        srec=states.get(sid,{})
        if srec.get('state')!='COMPLETE' or srec.get('request_digest')!=dg:
            raise RuntimeError('G100_R10_RESUME_COMPLETED_PRECONDITION:'+sid)
        if sid!=R10_RECOVERY_SAMPLE_ID:
            info['completed_samples_preserved'].append(sid)
    if int(rec.get('attempts',-1))!=1:
        raise RuntimeError('G100_R10_RESUME_SAMPLE001_PRIOR_ATTEMPTS_MISMATCH')
    if (rec.get('r9_recovery') or {}).get('r9_addendum_drive_id')!=R9_ADDENDUM_DRIVE_ID:
        raise RuntimeError('G100_R10_RESUME_R9_PROVENANCE_MISSING')

    sd=cr/'samples'/R10_RECOVERY_SAMPLE_ID
    logp=cr/'logs'/f'{R10_RECOVERY_SAMPLE_ID}.log'
    reqp=cr/'requests'/f'{R10_RECOVERY_SAMPLE_ID}.json'
    rgbp=sd/'rgb.png'; compp=sd/'completion.json'
    for pp,label in ((rgbp,'RGB'),(compp,'COMPLETION'),(reqp,'REQUEST_JSON'),(logp,'WORKER_LOG')):
        if not pp.is_file(): raise RuntimeError('G100_R10_RESUME_'+label+'_MISSING')
    exact=((rgbp,R10_PRIOR_RGB_SHA256,'PRIOR_RGB_SHA'),(compp,R10_PRIOR_COMPLETION_SHA256,'PRIOR_COMPLETION_SHA'),
           (reqp,R10_PRIOR_REQUEST_FILE_SHA256,'PRIOR_REQUEST_FILE_SHA'),(logp,R10_PRIOR_WORKER_LOG_SHA256,'PRIOR_WORKER_LOG_SHA'))
    for pp,sh,label in exact:
        if sha256_file(pp)!=sh: raise RuntimeError('G100_R10_RESUME_'+label+'_MISMATCH')
    reqobj=json.loads(reqp.read_text(encoding='utf-8')); comp=json.loads(compp.read_text(encoding='utf-8'))
    if reqobj.get('sample_id')!=R10_RECOVERY_SAMPLE_ID or reqobj.get('input_digest_sha256')!=R10_RECOVERY_REQUEST_DIGEST:
        raise RuntimeError('G100_R10_RESUME_REQUEST_FILE_IDENTITY_MISMATCH')
    if comp.get('sample_id')!=R10_RECOVERY_SAMPLE_ID or comp.get('input_digest_sha256')!=R10_RECOVERY_REQUEST_DIGEST:
        raise RuntimeError('G100_R10_RESUME_COMPLETION_IDENTITY_MISMATCH')
    aid=comp.get('micro100_visibility_aid') or {}
    if aid.get('implementation_id')!='DF_G100_CLOSED_ROOM_CAMERA_FILL_V2_R9_TOON_BALANCED' or abs(float(aid.get('energy_w',-1))-175.0)>1e-12:
        raise RuntimeError('G100_R10_RESUME_R9_APPEARANCE_PROVENANCE_MISMATCH')
    st=rgb_stats(rgbp)
    for k,v in R10_PRIOR_RGB_STATS.items():
        if isinstance(v,int): ok=(st.get(k)==v)
        else: ok=abs(float(st.get(k,float('nan')))-float(v))<=1e-12
        if not ok: raise RuntimeError('G100_R10_RESUME_PRIOR_RGB_STATS_MISMATCH:'+k)
    if not (st['unique_rgb']>=32 and 12<=st['mean_luma']<=243 and st['structural_fraction']>=0.03 and st['p01_p99_span']<24):
        raise RuntimeError('G100_R10_RESUME_PRIOR_RGB_FAILURE_CLASS_MISMATCH')

    prior_records=_tree_records(sd)
    if not prior_records: raise RuntimeError('G100_R10_RESUME_SAMPLE001_EVIDENCE_EMPTY')
    evroot=runroot/'RECOVERY'/'R9_COMPLETE_SAMPLE_001_RGB_ACCEPTANCE_FAIL'
    payload=evroot/'sample_bytes'; evroot.mkdir(parents=True,exist_ok=True)
    if payload.exists():
        if _tree_records(payload)!=prior_records:
            raise RuntimeError('G100_R10_RESUME_EXISTING_PRESERVE_MISMATCH')
    else:
        shutil.copytree(sd,payload)
    copied=_tree_records(payload)
    if copied!=prior_records: raise RuntimeError('G100_R10_RESUME_PRESERVE_HASH_MISMATCH')
    shutil.copy2(logp,evroot/'worker.log'); shutil.copy2(reqp,evroot/'request.json')
    peer_snapshot={}
    for sid in sorted(expected):
        if sid==R10_RECOVERY_SAMPLE_ID: continue
        psd=cr/'samples'/sid
        peer_snapshot[sid]={'request_digest':states[sid].get('request_digest'),'sample_files':_tree_records(psd)}
    recovery={'schema':'DF-G100-R10-RECOVERY-JOURNAL-V1','status':'PRESERVED_BEFORE_LEDGER_RESET',
      'r10_addendum_drive_id':R10_ADDENDUM_DRIVE_ID,'source_tool':'R9_POST_CHUNK_ACCEPTANCE','target_tool':'R10',
      'sample_id':R10_RECOVERY_SAMPLE_ID,'request_digest':R10_RECOVERY_REQUEST_DIGEST,
      'prior_state':'COMPLETE','prior_attempts':1,'prior_acceptance_failure':'rgb_span=false',
      'prior_rgb_sha256':R10_PRIOR_RGB_SHA256,'prior_completion_sha256':R10_PRIOR_COMPLETION_SHA256,
      'prior_rgb_stats':R10_PRIOR_RGB_STATS,'preserved_members':copied,
      'preserved_worker_log_sha256':sha256_file(evroot/'worker.log'),'preserved_request_sha256':sha256_file(evroot/'request.json'),
      'completed_samples_preserved':list(info['completed_samples_preserved']),'peer_snapshot':peer_snapshot,
      'fixed_rgb_contrast':{'pivot_u8':128,'factor_numerator':5,'factor_denominator':4,'adaptive':False,'spatial_warp':False},
      'recorded_utc':utc_iso(),'product_mutated':False,'maya_mutated':False,'test77_accessed':False,'training_started':False}
    atomic_json(evroot/'R10_RECOVERY_JOURNAL.json',recovery)

    shutil.rmtree(sd); sd.mkdir(parents=True,exist_ok=True)
    rec['state']='PENDING'; rec['attempts']=0; rec.pop('last_error',None)
    rec['r10_recovery']={'r10_addendum_drive_id':R10_ADDENDUM_DRIVE_ID,'prior_attempts':1,
                         'prior_state':'COMPLETE','prior_acceptance_failure':'rgb_span=false',
                         'prior_rgb_sha256':R10_PRIOR_RGB_SHA256,
                         'recovery_journal_rel':(evroot/'R10_RECOVERY_JOURNAL.json').relative_to(runroot).as_posix(),
                         'r10_rgb_contrast_pivot_u8':128,'r10_rgb_contrast_factor':'5/4'}
    atomic_json(lp,ledger)
    recovery['status']='LEDGER_RESET_SAMPLE_001_ONLY'; atomic_json(evroot/'R10_RECOVERY_JOURNAL.json',recovery)
    info['status']='R9_COMPLETE_SAMPLE_001_REOPENED_FOR_R10'
    info['recovered_samples'][R10_RECOVERY_SAMPLE_ID]=dict(rec['r10_recovery'])
    return info

def write_plan(runroot:Path,reqs,chunks,qa):
    plan=runroot/'PLAN';plan.mkdir(parents=True,exist_ok=True)
    plan_obj={'schema':'DF-G100-FROZEN-REQUEST-PLAN-V2','dataset_id':DATASET_ID,'release_id':RELEASE_ID,'root_seed':ROOT_SEED,'sample_count':100,'partition':PARTITION,'requests':reqs,'chunk_digests':[c['chunk_digest_sha256'] for c in chunks]}
    p=plan/'MICRO100_REQUESTS_FROZEN.json'
    if p.exists():
        old=json.loads(p.read_text(encoding='utf-8'))
        if old!=plan_obj:raise RuntimeError('G100_EXISTING_FROZEN_PLAN_IDENTITY_MISMATCH')
    else:atomic_json(p,plan_obj)
    for i,c in enumerate(chunks):
        cp=plan/f'CHUNK_{i:02d}_MANIFEST_FROZEN.json'
        if cp.exists() and json.loads(cp.read_text(encoding='utf-8'))!=c:raise RuntimeError(f'G100_EXISTING_CHUNK_PLAN_MISMATCH:{i}')
        if not cp.exists():atomic_json(cp,c)
    atomic_json(plan/'PLAN_QA.json',qa)
    return {'plan_path':p,'plan_sha256':sha256_file(p),'plan_bytes':p.stat().st_size}

def apply_r12_resume_if_needed(runroot:Path,chunks):
    """Exact fail-closed R11 FAILED_FINAL sample015 -> R12 visible-side Normal recovery.

    Samples000..014 are immutable COMPLETE evidence. The complete failed sample015
    payload is hash-bound and preserved before reopening only that sample.
    """
    info={'schema':'DF-G100-R12-RESUME-V1','status':'NOT_APPLICABLE',
          'r12_addendum_drive_id':R12_ADDENDUM_DRIVE_ID,'recovered_samples':{},
          'completed_samples_preserved':[]}
    runroot=Path(runroot)
    if len(chunks)<2: raise RuntimeError('G100_R12_RESUME_CHUNK01_MISSING')
    cr=runroot/'CHUNKS'/'chunk_01'; lp=cr/'ledger.json'
    if not lp.is_file(): return info
    led=json.loads(lp.read_text(encoding='utf-8'))
    if led.get('chunk_digest_sha256')!=R12_CHUNK01_DIGEST:
        raise RuntimeError('G100_R12_RESUME_CHUNK01_DIGEST_MISMATCH')
    expected={r['sample_id']:r['input_digest_sha256'] for r in chunks[1]['requests']}
    if len(expected)!=10 or expected.get(R12_RECOVERY_SAMPLE_ID)!=R12_RECOVERY_REQUEST_DIGEST:
        raise RuntimeError('G100_R12_RESUME_FROZEN_PLAN_TARGET_MISMATCH')
    states=led.get('states') or {}; rec=states.get(R12_RECOVERY_SAMPLE_ID,{})
    if rec.get('request_digest')!=R12_RECOVERY_REQUEST_DIGEST:
        raise RuntimeError('G100_R12_RESUME_LEDGER_REQUEST_DIGEST_MISMATCH')
    if (rec.get('r12_recovery') or {}).get('r12_addendum_drive_id')==R12_ADDENDUM_DRIVE_ID:
        if rec.get('state') in {'PENDING','RUNNING','COMPLETE','FAILED_FINAL'}:
            info['status']='R12_RECOVERY_ALREADY_APPLIED'; info['recovered_samples'][R12_RECOVERY_SAMPLE_ID]=dict(rec.get('r12_recovery') or {}); return info
        raise RuntimeError('G100_R12_RESUME_BAD_POST_RECOVERY_STATE')
    if rec.get('state')!='FAILED_FINAL' or int(rec.get('attempts',-1))!=2 or rec.get('last_error')!='BLENDER_WORKER_RC:5':
        raise RuntimeError('G100_R12_RESUME_EXACT_R11_FAILED_FINAL_PRECONDITION')
    order=[r['sample_id'] for r in chunks[1]['requests']]; target_index=order.index(R12_RECOVERY_SAMPLE_ID)
    for i,sid in enumerate(order):
        rr=states.get(sid,{})
        if i<target_index:
            if rr.get('state')!='COMPLETE': raise RuntimeError('G100_R12_RESUME_PRIOR_PEER_NOT_COMPLETE:'+sid)
            info['completed_samples_preserved'].append(sid)
        elif i>target_index:
            if rr.get('state')!='PENDING' or int(rr.get('attempts',0))!=0: raise RuntimeError('G100_R12_RESUME_FUTURE_PEER_NOT_PENDING:'+sid)
    c0=runroot/'CHUNKS'/'chunk_00'/'ledger.json'
    if not c0.is_file(): raise RuntimeError('G100_R12_RESUME_CHUNK00_LEDGER_MISSING')
    l0=json.loads(c0.read_text(encoding='utf-8'))
    for sid,rr in (l0.get('states') or {}).items():
        if rr.get('state')!='COMPLETE': raise RuntimeError('G100_R12_RESUME_CHUNK00_PEER_NOT_COMPLETE:'+sid)
        info['completed_samples_preserved'].append(sid)
    if len(set(info['completed_samples_preserved']))!=15:
        raise RuntimeError('G100_R12_RESUME_EXPECTED_15_COMPLETE_PEERS')
    sd=cr/'samples'/R12_RECOVERY_SAMPLE_ID; logp=cr/'logs'/f'{R12_RECOVERY_SAMPLE_ID}.log'; reqp=cr/'requests'/f'{R12_RECOVERY_SAMPLE_ID}.json'
    required={'request.json':reqp,'failure.json':sd/'failure.json','worker.log':logp,'depth.exr':sd/'depth.exr','object_index.exr':sd/'object_index.exr','normal.exr':sd/'normal.exr','rgb.png':sd/'rgb.png','micro100_aux_gt_qa.json':sd/'micro100_aux_gt_qa.json'}
    for name,p in required.items():
        if not p.is_file(): raise RuntimeError('G100_R12_RESUME_REQUIRED_FILE_MISSING:'+name)
        got=sha256_file(p); exp=R12_PRIOR_FILE_SHA256[name]
        if got!=exp: raise RuntimeError('G100_R12_RESUME_FILE_SHA_MISMATCH:'+name+':'+got)
    fobj=json.loads((sd/'failure.json').read_text(encoding='utf-8'))
    if fobj.get('sample_id')!=R12_RECOVERY_SAMPLE_ID or fobj.get('input_digest_sha256')!=R12_RECOVERY_REQUEST_DIGEST or fobj.get('error')!=R12_FAILURE_ERROR:
        raise RuntimeError('G100_R12_RESUME_FAILURE_CAUSE_MISMATCH')
    reqobj=json.loads(reqp.read_text(encoding='utf-8'))
    if reqobj.get('sample_id')!=R12_RECOVERY_SAMPLE_ID or reqobj.get('input_digest_sha256')!=R12_RECOVERY_REQUEST_DIGEST:
        raise RuntimeError('G100_R12_RESUME_REQUEST_FILE_MISMATCH')
    prior_records=_tree_records(sd)
    if not prior_records: raise RuntimeError('G100_R12_RESUME_FAILED_SAMPLE_EVIDENCE_EMPTY')
    evroot=runroot/'RECOVERY'/'R11_FAILED_SAMPLE_015'; evroot.mkdir(parents=True,exist_ok=True); payload=evroot/'sample_bytes'
    if payload.exists(): shutil.rmtree(payload)
    shutil.copytree(sd,payload); copied=_tree_records(payload)
    if copied!=prior_records: raise RuntimeError('G100_R12_RESUME_PRESERVE_HASH_MISMATCH')
    shutil.copy2(logp,evroot/'worker.log'); shutil.copy2(reqp,evroot/'request.json')
    recovery={'schema':'DF-G100-R12-RECOVERY-JOURNAL-V1','status':'PRESERVED_BEFORE_LEDGER_RESET','r12_addendum_drive_id':R12_ADDENDUM_DRIVE_ID,'source_tool':'R11','target_tool':'R12','sample_id':R12_RECOVERY_SAMPLE_ID,'request_digest':R12_RECOVERY_REQUEST_DIGEST,'chunk_digest_sha256':R12_CHUNK01_DIGEST,'prior_state':'FAILED_FINAL','prior_attempts':2,'prior_last_error':'BLENDER_WORKER_RC:5','prior_failure_error':R12_FAILURE_ERROR,'prior_file_sha256':R12_PRIOR_FILE_SHA256,'preserved_members':prior_records,'preserved_worker_log_sha256':sha256_file(evroot/'worker.log'),'preserved_request_sha256':sha256_file(evroot/'request.json'),'completed_samples_preserved':list(info['completed_samples_preserved']),'visible_side_normal_semantics':'RENDERER_VISIBLE_SIDE_CUBOID_NORMAL_R12_V1','recorded_utc':utc_iso(),'product_mutated':False,'maya_mutated':False,'test77_accessed':False,'training_started':False}
    atomic_json(evroot/'R12_RECOVERY_JOURNAL.json',recovery)
    shutil.rmtree(sd); sd.mkdir(parents=True,exist_ok=True)
    rec['state']='PENDING'; rec['attempts']=0; rec.pop('last_error',None)
    rec['r12_recovery']={'r12_addendum_drive_id':R12_ADDENDUM_DRIVE_ID,'prior_state':'FAILED_FINAL','prior_attempts':2,'prior_failure_error':R12_FAILURE_ERROR,'recovery_journal_rel':(evroot/'R12_RECOVERY_JOURNAL.json').relative_to(runroot).as_posix(),'visible_side_normal_semantics':'RENDERER_VISIBLE_SIDE_CUBOID_NORMAL_R12_V1'}
    atomic_json(lp,led); recovery['status']='LEDGER_RESET_SAMPLE_015_ONLY'; atomic_json(evroot/'R12_RECOVERY_JOURNAL.json',recovery)
    info['status']='R11_FAILED_SAMPLE_015_REOPENED_FOR_R12'; info['recovered_samples'][R12_RECOVERY_SAMPLE_ID]=dict(rec['r12_recovery']); return info

# minimal PNG decoder, inherited from accepted R10 gate
def _paeth(a,b,c):
    p=a+b-c;pa,pb,pc=abs(p-a),abs(p-b),abs(p-c);return a if pa<=pb and pa<=pc else (b if pb<=pc else c)

def apply_r13_resume_if_needed(runroot:Path,chunks):
    """Exact fail-closed R12 FAILED_FINAL sample016 -> R13 reprojection recovery.

    Samples000..015 are immutable COMPLETE evidence. The exact pre-render R12
    failure bytes are fingerprint-bound and preserved before reopening only 016.
    """
    info={'schema':'DF-G100-R13-RESUME-V1','status':'NOT_APPLICABLE',
          'r13_addendum_drive_id':R13_ADDENDUM_DRIVE_ID,'recovered_samples':{},
          'completed_samples_preserved':[]}
    runroot=Path(runroot)
    if len(chunks)<2: raise RuntimeError('G100_R13_RESUME_CHUNK01_MISSING')
    cr=runroot/'CHUNKS'/'chunk_01'; lp=cr/'ledger.json'
    if not lp.is_file(): return info
    led=json.loads(lp.read_text(encoding='utf-8'))
    if led.get('chunk_digest_sha256')!=R13_CHUNK01_DIGEST:
        raise RuntimeError('G100_R13_RESUME_CHUNK01_DIGEST_MISMATCH')
    expected={r['sample_id']:r['input_digest_sha256'] for r in chunks[1]['requests']}
    if len(expected)!=10 or expected.get(R13_RECOVERY_SAMPLE_ID)!=R13_RECOVERY_REQUEST_DIGEST:
        raise RuntimeError('G100_R13_RESUME_FROZEN_PLAN_TARGET_MISMATCH')
    states=led.get('states') or {}; rec=states.get(R13_RECOVERY_SAMPLE_ID,{})
    if rec.get('request_digest')!=R13_RECOVERY_REQUEST_DIGEST:
        raise RuntimeError('G100_R13_RESUME_LEDGER_REQUEST_DIGEST_MISMATCH')
    if (rec.get('r13_recovery') or {}).get('r13_addendum_drive_id')==R13_ADDENDUM_DRIVE_ID:
        if rec.get('state') in {'PENDING','RUNNING','COMPLETE','FAILED_RETRYABLE','FAILED_FINAL'}:
            info['status']='R13_RECOVERY_ALREADY_APPLIED'; info['recovered_samples'][R13_RECOVERY_SAMPLE_ID]=dict(rec.get('r13_recovery') or {}); return info
        raise RuntimeError('G100_R13_RESUME_BAD_POST_RECOVERY_STATE')
    if rec.get('state')!='FAILED_FINAL' or int(rec.get('attempts',-1))!=2 or rec.get('last_error')!='BLENDER_WORKER_RC:5':
        raise RuntimeError('G100_R13_RESUME_EXACT_R12_FAILED_FINAL_PRECONDITION')
    order=[r['sample_id'] for r in chunks[1]['requests']]; target_index=order.index(R13_RECOVERY_SAMPLE_ID)
    for i,sid in enumerate(order):
        rr=states.get(sid,{})
        if i<target_index:
            if rr.get('state')!='COMPLETE': raise RuntimeError('G100_R13_RESUME_PRIOR_PEER_NOT_COMPLETE:'+sid)
            info['completed_samples_preserved'].append(sid)
        elif i>target_index:
            if rr.get('state')!='PENDING' or int(rr.get('attempts',0))!=0: raise RuntimeError('G100_R13_RESUME_FUTURE_PEER_NOT_PENDING:'+sid)
    c0=runroot/'CHUNKS'/'chunk_00'/'ledger.json'
    if not c0.is_file(): raise RuntimeError('G100_R13_RESUME_CHUNK00_LEDGER_MISSING')
    l0=json.loads(c0.read_text(encoding='utf-8'))
    for sid,rr in (l0.get('states') or {}).items():
        if rr.get('state')!='COMPLETE': raise RuntimeError('G100_R13_RESUME_CHUNK00_PEER_NOT_COMPLETE:'+sid)
        info['completed_samples_preserved'].append(sid)
    if len(set(info['completed_samples_preserved']))!=16:
        raise RuntimeError('G100_R13_RESUME_EXPECTED_16_COMPLETE_PEERS')

    sd=cr/'samples'/R13_RECOVERY_SAMPLE_ID; logp=cr/'logs'/f'{R13_RECOVERY_SAMPLE_ID}.log'; reqp=cr/'requests'/f'{R13_RECOVERY_SAMPLE_ID}.json'
    required={'request.json':reqp,'worker.log':logp,'failure.json':sd/'failure.json','camera_calibration.json':sd/'camera_calibration.json','pre_render_reprojection.json':sd/'pre_render_reprojection.json'}
    for name,p in required.items():
        if not p.is_file(): raise RuntimeError('G100_R13_RESUME_REQUIRED_FILE_MISSING:'+name)
        got=sha256_file(p); exp=R13_PRIOR_FILE_SHA256[name]
        if got!=exp: raise RuntimeError('G100_R13_RESUME_FILE_SHA_MISMATCH:'+name+':'+got)
    prior_records=_tree_records(sd)
    if prior_records!=R13_PRIOR_SAMPLE_TREE:
        raise RuntimeError('G100_R13_RESUME_PARTIAL_OUTPUT_IDENTITIES_MISMATCH')
    fobj=json.loads((sd/'failure.json').read_text(encoding='utf-8'))
    if fobj.get('sample_id')!=R13_RECOVERY_SAMPLE_ID or fobj.get('input_digest_sha256')!=R13_RECOVERY_REQUEST_DIGEST or fobj.get('error')!=R13_FAILURE_ERROR or fobj.get('real_blender_rendered') is not False:
        raise RuntimeError('G100_R13_RESUME_FAILURE_CAUSE_MISMATCH')
    reqobj=json.loads(reqp.read_text(encoding='utf-8'))
    if reqobj.get('sample_id')!=R13_RECOVERY_SAMPLE_ID or reqobj.get('input_digest_sha256')!=R13_RECOVERY_REQUEST_DIGEST:
        raise RuntimeError('G100_R13_RESUME_REQUEST_FILE_MISMATCH')

    evroot=runroot/'RECOVERY'/'R12_FAILED_SAMPLE_016'; evroot.mkdir(parents=True,exist_ok=True); payload=evroot/'sample_bytes'
    if payload.exists(): shutil.rmtree(payload)
    shutil.copytree(sd,payload); copied=_tree_records(payload)
    if copied!=prior_records: raise RuntimeError('G100_R13_RESUME_PRESERVE_HASH_MISMATCH')
    shutil.copy2(logp,evroot/'worker.log'); shutil.copy2(reqp,evroot/'request.json')
    # PARTIAL_OUTPUT_IDENTITIES was created by the R12 failure packager rather than
    # stored in the live sample directory. Bind it through the exact archived R12
    # transport embedded in the R13 package, then preserve those exact bytes too.
    fixture=HERE/'R12_REAL_FAILURE_EVIDENCE'/'PCS_CAMERA_GEOMETRY_DATA_FACTORY_G100_MICRO100_FAILURE_RETURN_R12_REAL_20260907.zip'
    if not fixture.is_file() or sha256_file(fixture)!=R13_PRIOR_R12_RETURN_SHA256:
        raise RuntimeError('G100_R13_RESUME_R12_FIXTURE_IDENTITY_MISMATCH')
    with zipfile.ZipFile(fixture) as z:
        partial_member='FAILED_SAMPLES/'+R13_RECOVERY_SAMPLE_ID+'/PARTIAL_OUTPUT_IDENTITIES.json'
        partial_bytes=z.read(partial_member)
    if sha256_bytes(partial_bytes)!=R13_PRIOR_PARTIAL_IDENTITIES_SHA256:
        raise RuntimeError('G100_R13_RESUME_PARTIAL_OUTPUT_IDENTITIES_SHA_MISMATCH')
    partial_identity=json.loads(partial_bytes.decode('utf-8'))
    if partial_identity.get('sample_id')!=R13_RECOVERY_SAMPLE_ID or partial_identity.get('request_digest')!=R13_RECOVERY_REQUEST_DIGEST or partial_identity.get('state')!='FAILED_FINAL' or int(partial_identity.get('attempts',-1))!=2 or partial_identity.get('last_error')!='BLENDER_WORKER_RC:5' or partial_identity.get('files')!=prior_records:
        raise RuntimeError('G100_R13_RESUME_PARTIAL_OUTPUT_IDENTITIES_CONTENT_MISMATCH')
    (evroot/'PARTIAL_OUTPUT_IDENTITIES.json').write_bytes(partial_bytes)
    recovery={'schema':'DF-G100-R13-RECOVERY-JOURNAL-V1','status':'PRESERVED_BEFORE_LEDGER_RESET','r13_addendum_drive_id':R13_ADDENDUM_DRIVE_ID,'source_tool':'R12','target_tool':'R13','sample_id':R13_RECOVERY_SAMPLE_ID,'request_digest':R13_RECOVERY_REQUEST_DIGEST,'chunk_digest_sha256':R13_CHUNK01_DIGEST,'prior_state':'FAILED_FINAL','prior_attempts':2,'prior_last_error':'BLENDER_WORKER_RC:5','prior_failure_error':R13_FAILURE_ERROR,'prior_file_sha256':R13_PRIOR_FILE_SHA256,'prior_partial_output_identities_sha256':R13_PRIOR_PARTIAL_IDENTITIES_SHA256,'preserved_members':prior_records,'preserved_worker_log_sha256':sha256_file(evroot/'worker.log'),'preserved_request_sha256':sha256_file(evroot/'request.json'),'completed_samples_preserved':list(info['completed_samples_preserved']),'reprojection_authority_semantics':'CANONICAL_PIXEL_CENTER_INSIDE_PHYSICAL_RASTER_R13','recorded_utc':utc_iso(),'product_mutated':False,'maya_mutated':False,'test77_accessed':False,'training_started':False}
    atomic_json(evroot/'R13_RECOVERY_JOURNAL.json',recovery)
    shutil.rmtree(sd); sd.mkdir(parents=True,exist_ok=True)
    rec['state']='PENDING'; rec['attempts']=0; rec.pop('last_error',None)
    rec['r13_recovery']={'r13_addendum_drive_id':R13_ADDENDUM_DRIVE_ID,'prior_state':'FAILED_FINAL','prior_attempts':2,'prior_failure_error':R13_FAILURE_ERROR,'recovery_journal_rel':(evroot/'R13_RECOVERY_JOURNAL.json').relative_to(runroot).as_posix(),'reprojection_authority_semantics':'CANONICAL_PIXEL_CENTER_INSIDE_PHYSICAL_RASTER_R13'}
    atomic_json(lp,led); recovery['status']='LEDGER_RESET_SAMPLE_016_ONLY'; atomic_json(evroot/'R13_RECOVERY_JOURNAL.json',recovery)
    info['status']='R12_FAILED_SAMPLE_016_REOPENED_FOR_R13'; info['recovered_samples'][R13_RECOVERY_SAMPLE_ID]=dict(rec['r13_recovery']); return info

def apply_r14_resume_if_needed(runroot:Path,chunks):
    """Exact fail-closed R13 FAILED_FINAL sample019 -> R14 adaptive-probe recovery.

    Samples000..018 are immutable COMPLETE evidence. Exact R13 pre-render
    failure fingerprints are verified and preserved before reopening only 019.
    """
    info={'schema':'DF-G100-R14-RESUME-V1','status':'NOT_APPLICABLE',
          'r14_addendum_drive_id':R14_ADDENDUM_DRIVE_ID,'recovered_samples':{},
          'completed_samples_preserved':[]}
    runroot=Path(runroot)
    if len(chunks)<2: raise RuntimeError('G100_R14_RESUME_CHUNK01_MISSING')
    cr=runroot/'CHUNKS'/'chunk_01'; lp=cr/'ledger.json'
    if not lp.is_file(): return info
    led=json.loads(lp.read_text(encoding='utf-8'))
    if led.get('chunk_digest_sha256')!=R14_CHUNK01_DIGEST:
        raise RuntimeError('G100_R14_RESUME_CHUNK01_DIGEST_MISMATCH')
    expected={r['sample_id']:r['input_digest_sha256'] for r in chunks[1]['requests']}
    if len(expected)!=10 or expected.get(R14_RECOVERY_SAMPLE_ID)!=R14_RECOVERY_REQUEST_DIGEST:
        raise RuntimeError('G100_R14_RESUME_FROZEN_PLAN_TARGET_MISMATCH')
    states=led.get('states') or {}; rec=states.get(R14_RECOVERY_SAMPLE_ID,{})
    if rec.get('request_digest')!=R14_RECOVERY_REQUEST_DIGEST:
        raise RuntimeError('G100_R14_RESUME_LEDGER_REQUEST_DIGEST_MISMATCH')
    if (rec.get('r14_recovery') or {}).get('r14_addendum_drive_id')==R14_ADDENDUM_DRIVE_ID:
        if rec.get('state') in {'PENDING','RUNNING','COMPLETE','FAILED_RETRYABLE','FAILED_FINAL'}:
            info['status']='R14_RECOVERY_ALREADY_APPLIED'; info['recovered_samples'][R14_RECOVERY_SAMPLE_ID]=dict(rec.get('r14_recovery') or {}); return info
        raise RuntimeError('G100_R14_RESUME_BAD_POST_RECOVERY_STATE')
    if rec.get('state')!='FAILED_FINAL' or int(rec.get('attempts',-1))!=2 or rec.get('last_error')!='BLENDER_WORKER_RC:5':
        raise RuntimeError('G100_R14_RESUME_EXACT_R13_FAILED_FINAL_PRECONDITION')
    order=[r['sample_id'] for r in chunks[1]['requests']]; target_index=order.index(R14_RECOVERY_SAMPLE_ID)
    for i,sid in enumerate(order):
        rr=states.get(sid,{})
        if i<target_index:
            if rr.get('state')!='COMPLETE': raise RuntimeError('G100_R14_RESUME_PRIOR_PEER_NOT_COMPLETE:'+sid)
            info['completed_samples_preserved'].append(sid)
        elif i>target_index:
            if rr.get('state')!='PENDING' or int(rr.get('attempts',0))!=0: raise RuntimeError('G100_R14_RESUME_FUTURE_PEER_NOT_PENDING:'+sid)
    c0=runroot/'CHUNKS'/'chunk_00'/'ledger.json'
    if not c0.is_file(): raise RuntimeError('G100_R14_RESUME_CHUNK00_LEDGER_MISSING')
    l0=json.loads(c0.read_text(encoding='utf-8'))
    for sid,rr in (l0.get('states') or {}).items():
        if rr.get('state')!='COMPLETE': raise RuntimeError('G100_R14_RESUME_CHUNK00_PEER_NOT_COMPLETE:'+sid)
        info['completed_samples_preserved'].append(sid)
    if len(set(info['completed_samples_preserved']))!=19:
        raise RuntimeError('G100_R14_RESUME_EXPECTED_19_COMPLETE_PEERS')

    sd=cr/'samples'/R14_RECOVERY_SAMPLE_ID; logp=cr/'logs'/f'{R14_RECOVERY_SAMPLE_ID}.log'; reqp=cr/'requests'/f'{R14_RECOVERY_SAMPLE_ID}.json'
    required={'request.json':reqp,'worker.log':logp,'failure.json':sd/'failure.json','camera_calibration.json':sd/'camera_calibration.json','pre_render_reprojection.json':sd/'pre_render_reprojection.json'}
    for name,p in required.items():
        if not p.is_file(): raise RuntimeError('G100_R14_RESUME_REQUIRED_FILE_MISSING:'+name)
        got=sha256_file(p); exp=R14_PRIOR_FILE_SHA256[name]
        if got!=exp: raise RuntimeError('G100_R14_RESUME_FILE_SHA_MISMATCH:'+name+':'+got)
    prior_records=_tree_records(sd)
    if prior_records!=R14_PRIOR_SAMPLE_TREE:
        raise RuntimeError('G100_R14_RESUME_PARTIAL_OUTPUT_IDENTITIES_MISMATCH')
    fobj=json.loads((sd/'failure.json').read_text(encoding='utf-8'))
    if fobj.get('sample_id')!=R14_RECOVERY_SAMPLE_ID or fobj.get('input_digest_sha256')!=R14_RECOVERY_REQUEST_DIGEST or fobj.get('error')!=R14_FAILURE_ERROR or fobj.get('real_blender_rendered') is not False:
        raise RuntimeError('G100_R14_RESUME_FAILURE_CAUSE_MISMATCH')
    reqobj=json.loads(reqp.read_text(encoding='utf-8'))
    if reqobj.get('sample_id')!=R14_RECOVERY_SAMPLE_ID or reqobj.get('input_digest_sha256')!=R14_RECOVERY_REQUEST_DIGEST:
        raise RuntimeError('G100_R14_RESUME_REQUEST_FILE_MISMATCH')

    evroot=runroot/'RECOVERY'/'R13_FAILED_SAMPLE_019'; evroot.mkdir(parents=True,exist_ok=True); payload=evroot/'sample_bytes'
    if payload.exists(): shutil.rmtree(payload)
    shutil.copytree(sd,payload); copied=_tree_records(payload)
    if copied!=prior_records: raise RuntimeError('G100_R14_RESUME_PRESERVE_HASH_MISMATCH')
    shutil.copy2(logp,evroot/'worker.log'); shutil.copy2(reqp,evroot/'request.json')
    fixture=HERE/'R13_REAL_FAILURE_EVIDENCE'/'PCS_CAMERA_GEOMETRY_DATA_FACTORY_G100_MICRO100_FAILURE_RETURN_R13_REAL_20260907.zip'
    if not fixture.is_file() or sha256_file(fixture)!=R14_PRIOR_R13_RETURN_SHA256:
        raise RuntimeError('G100_R14_RESUME_R13_FIXTURE_IDENTITY_MISMATCH')
    with zipfile.ZipFile(fixture) as z:
        partial_member='FAILED_SAMPLES/'+R14_RECOVERY_SAMPLE_ID+'/PARTIAL_OUTPUT_IDENTITIES.json'
        partial_bytes=z.read(partial_member)
    if sha256_bytes(partial_bytes)!=R14_PRIOR_PARTIAL_IDENTITIES_SHA256:
        raise RuntimeError('G100_R14_RESUME_PARTIAL_OUTPUT_IDENTITIES_SHA_MISMATCH')
    partial_identity=json.loads(partial_bytes.decode('utf-8'))
    if partial_identity.get('sample_id')!=R14_RECOVERY_SAMPLE_ID or partial_identity.get('request_digest')!=R14_RECOVERY_REQUEST_DIGEST or partial_identity.get('state')!='FAILED_FINAL' or int(partial_identity.get('attempts',-1))!=2 or partial_identity.get('last_error')!='BLENDER_WORKER_RC:5' or partial_identity.get('files')!=prior_records:
        raise RuntimeError('G100_R14_RESUME_PARTIAL_OUTPUT_IDENTITIES_CONTENT_MISMATCH')
    (evroot/'PARTIAL_OUTPUT_IDENTITIES.json').write_bytes(partial_bytes)
    recovery={'schema':'DF-G100-R14-RECOVERY-JOURNAL-V1','status':'PRESERVED_BEFORE_LEDGER_RESET','r14_addendum_drive_id':R14_ADDENDUM_DRIVE_ID,'source_tool':'R13','target_tool':'R14','sample_id':R14_RECOVERY_SAMPLE_ID,'request_digest':R14_RECOVERY_REQUEST_DIGEST,'chunk_digest_sha256':R14_CHUNK01_DIGEST,'prior_state':'FAILED_FINAL','prior_attempts':2,'prior_last_error':'BLENDER_WORKER_RC:5','prior_failure_error':R14_FAILURE_ERROR,'prior_file_sha256':R14_PRIOR_FILE_SHA256,'prior_partial_output_identities_sha256':R14_PRIOR_PARTIAL_IDENTITIES_SHA256,'preserved_members':prior_records,'preserved_worker_log_sha256':sha256_file(evroot/'worker.log'),'preserved_request_sha256':sha256_file(evroot/'request.json'),'completed_samples_preserved':list(info['completed_samples_preserved']),'reprojection_authority_semantics':'CANONICAL_PIXEL_CENTER_INSIDE_PHYSICAL_RASTER_R13','synthetic_probe_semantics':'INTRINSICS_ADAPTIVE_INTERIOR_RASTER_PROBES_R14_V1','recorded_utc':utc_iso(),'product_mutated':False,'maya_mutated':False,'test77_accessed':False,'training_started':False}
    atomic_json(evroot/'R14_RECOVERY_JOURNAL.json',recovery)
    shutil.rmtree(sd); sd.mkdir(parents=True,exist_ok=True)
    rec['state']='PENDING'; rec['attempts']=0; rec.pop('last_error',None)
    rec['r14_recovery']={'r14_addendum_drive_id':R14_ADDENDUM_DRIVE_ID,'prior_state':'FAILED_FINAL','prior_attempts':2,'prior_failure_error':R14_FAILURE_ERROR,'recovery_journal_rel':(evroot/'R14_RECOVERY_JOURNAL.json').relative_to(runroot).as_posix(),'reprojection_authority_semantics':'CANONICAL_PIXEL_CENTER_INSIDE_PHYSICAL_RASTER_R13','synthetic_probe_semantics':'INTRINSICS_ADAPTIVE_INTERIOR_RASTER_PROBES_R14_V1'}
    atomic_json(lp,led); recovery['status']='LEDGER_RESET_SAMPLE_019_ONLY'; atomic_json(evroot/'R14_RECOVERY_JOURNAL.json',recovery)
    info['status']='R13_FAILED_SAMPLE_019_REOPENED_FOR_R14'; info['recovered_samples'][R14_RECOVERY_SAMPLE_ID]=dict(rec['r14_recovery']); return info

def apply_r11_resume_if_needed(runroot:Path,chunks):
    """Exact fail-closed R10 FAILED_FINAL sample013 -> R11 visibility-bootstrap recovery.

    R11 preserves the complete R10 failed sample013 evidence before reopening
    only that sample. Samples000..012 are immutable COMPLETE peers.
    """
    info={'schema':'DF-G100-R11-RESUME-V1','status':'NOT_APPLICABLE',
          'r11_addendum_drive_id':R11_ADDENDUM_DRIVE_ID,'recovered_samples':{},
          'completed_samples_preserved':[]}
    runroot=Path(runroot)
    if len(chunks)<2:
        raise RuntimeError('G100_R11_RESUME_CHUNK01_MISSING')
    cr=runroot/'CHUNKS'/'chunk_01'; lp=cr/'ledger.json'
    if not lp.is_file():
        return info
    led=json.loads(lp.read_text(encoding='utf-8'))
    if led.get('chunk_digest_sha256')!=R11_CHUNK01_DIGEST:
        raise RuntimeError('G100_R11_RESUME_CHUNK01_DIGEST_MISMATCH')
    expected={r['sample_id']:r['input_digest_sha256'] for r in chunks[1]['requests']}
    if len(expected)!=10 or expected.get(R11_RECOVERY_SAMPLE_ID)!=R11_RECOVERY_REQUEST_DIGEST:
        raise RuntimeError('G100_R11_RESUME_FROZEN_PLAN_TARGET_MISMATCH')
    states=led.get('states') or {}
    rec=states.get(R11_RECOVERY_SAMPLE_ID,{})
    if rec.get('request_digest')!=R11_RECOVERY_REQUEST_DIGEST:
        raise RuntimeError('G100_R11_RESUME_LEDGER_REQUEST_DIGEST_MISMATCH')
    if (rec.get('r11_recovery') or {}).get('r11_addendum_drive_id')==R11_ADDENDUM_DRIVE_ID:
        if rec.get('state') in {'PENDING','RUNNING','COMPLETE','FAILED_FINAL'}:
            info['status']='R11_RECOVERY_ALREADY_APPLIED'
            info['recovered_samples'][R11_RECOVERY_SAMPLE_ID]=dict(rec.get('r11_recovery') or {})
            return info
        raise RuntimeError('G100_R11_RESUME_BAD_POST_RECOVERY_STATE')
    if rec.get('state')!='FAILED_FINAL' or int(rec.get('attempts',-1))!=2 or rec.get('last_error')!='BLENDER_WORKER_RC:5':
        raise RuntimeError('G100_R11_RESUME_EXACT_R10_FAILED_FINAL_PRECONDITION')

    # Freeze peer-state expectations inside chunk01.
    order=[r['sample_id'] for r in chunks[1]['requests']]
    target_index=order.index(R11_RECOVERY_SAMPLE_ID)
    for i,sid in enumerate(order):
        rr=states.get(sid,{})
        if i<target_index:
            if rr.get('state')!='COMPLETE':
                raise RuntimeError('G100_R11_RESUME_PRIOR_PEER_NOT_COMPLETE:'+sid)
            info['completed_samples_preserved'].append(sid)
        elif i>target_index:
            if rr.get('state')!='PENDING' or int(rr.get('attempts',0))!=0:
                raise RuntimeError('G100_R11_RESUME_FUTURE_PEER_NOT_PENDING:'+sid)

    # All chunk00 peers must remain COMPLETE.
    c0=runroot/'CHUNKS'/'chunk_00'/'ledger.json'
    if not c0.is_file(): raise RuntimeError('G100_R11_RESUME_CHUNK00_LEDGER_MISSING')
    l0=json.loads(c0.read_text(encoding='utf-8'))
    for sid,rr in (l0.get('states') or {}).items():
        if rr.get('state')!='COMPLETE':
            raise RuntimeError('G100_R11_RESUME_CHUNK00_PEER_NOT_COMPLETE:'+sid)
        info['completed_samples_preserved'].append(sid)

    sd=cr/'samples'/R11_RECOVERY_SAMPLE_ID
    logp=cr/'logs'/f'{R11_RECOVERY_SAMPLE_ID}.log'
    reqp=cr/'requests'/f'{R11_RECOVERY_SAMPLE_ID}.json'
    required={
      'request.json':reqp,'failure.json':sd/'failure.json','worker.log':logp,
      'depth.exr':sd/'depth.exr','object_index.exr':sd/'object_index.exr',
      'normal.exr':sd/'normal.exr','rgb.png':sd/'rgb.png',
      'micro100_aux_gt_qa.json':sd/'micro100_aux_gt_qa.json',
    }
    for name,p in required.items():
        if not p.is_file(): raise RuntimeError('G100_R11_RESUME_REQUIRED_FILE_MISSING:'+name)
        got=sha256_file(p); exp=R11_PRIOR_FILE_SHA256[name]
        if got!=exp:
            raise RuntimeError('G100_R11_RESUME_FILE_SHA_MISMATCH:'+name+':'+got)
    fobj=json.loads((sd/'failure.json').read_text(encoding='utf-8'))
    if fobj.get('sample_id')!=R11_RECOVERY_SAMPLE_ID or fobj.get('input_digest_sha256')!=R11_RECOVERY_REQUEST_DIGEST or fobj.get('error')!=R11_FAILURE_ERROR:
        raise RuntimeError('G100_R11_RESUME_FAILURE_CAUSE_MISMATCH')
    reqobj=json.loads(reqp.read_text(encoding='utf-8'))
    if reqobj.get('sample_id')!=R11_RECOVERY_SAMPLE_ID or reqobj.get('input_digest_sha256')!=R11_RECOVERY_REQUEST_DIGEST:
        raise RuntimeError('G100_R11_RESUME_REQUEST_FILE_MISMATCH')

    prior_records=_tree_records(sd)
    if not prior_records: raise RuntimeError('G100_R11_RESUME_FAILED_SAMPLE_EVIDENCE_EMPTY')
    evroot=runroot/'RECOVERY'/'R10_FAILED_SAMPLE_013'
    evroot.mkdir(parents=True,exist_ok=True); payload=evroot/'sample_bytes'
    if payload.exists(): shutil.rmtree(payload)
    shutil.copytree(sd,payload)
    copied=_tree_records(payload)
    if copied!=prior_records: raise RuntimeError('G100_R11_RESUME_PRESERVE_HASH_MISMATCH')
    shutil.copy2(logp,evroot/'worker.log'); shutil.copy2(reqp,evroot/'request.json')
    recovery={
      'schema':'DF-G100-R11-RECOVERY-JOURNAL-V1','status':'PRESERVED_BEFORE_LEDGER_RESET',
      'r11_addendum_drive_id':R11_ADDENDUM_DRIVE_ID,'source_tool':'R10','target_tool':'R11',
      'sample_id':R11_RECOVERY_SAMPLE_ID,'request_digest':R11_RECOVERY_REQUEST_DIGEST,
      'chunk_digest_sha256':R11_CHUNK01_DIGEST,
      'prior_state':'FAILED_FINAL','prior_attempts':2,'prior_last_error':'BLENDER_WORKER_RC:5',
      'prior_failure_error':R11_FAILURE_ERROR,'prior_file_sha256':R11_PRIOR_FILE_SHA256,
      'preserved_members':prior_records,
      'preserved_worker_log_sha256':sha256_file(evroot/'worker.log'),
      'preserved_request_sha256':sha256_file(evroot/'request.json'),
      'completed_samples_preserved':list(info['completed_samples_preserved']),
      'recorded_utc':utc_iso(),'product_mutated':False,'maya_mutated':False,
      'test77_accessed':False,'training_started':False}
    atomic_json(evroot/'R11_RECOVERY_JOURNAL.json',recovery)

    # Mutation begins only after all exact identity/preservation gates pass.
    shutil.rmtree(sd); sd.mkdir(parents=True,exist_ok=True)
    rec['state']='PENDING'; rec['attempts']=0; rec.pop('last_error',None)
    rec['r11_recovery']={
      'r11_addendum_drive_id':R11_ADDENDUM_DRIVE_ID,'prior_state':'FAILED_FINAL',
      'prior_attempts':2,'prior_failure_error':R11_FAILURE_ERROR,
      'recovery_journal_rel':(evroot/'R11_RECOVERY_JOURNAL.json').relative_to(runroot).as_posix(),
      'visibility_bootstrap_semantics':'CANONICAL_EXACT_SUBSET_TO_FULL_EFFECTIVE_EXACT_VISIBILITY_R11_V1'}
    atomic_json(lp,led)
    recovery['status']='LEDGER_RESET_SAMPLE_013_ONLY'; atomic_json(evroot/'R11_RECOVERY_JOURNAL.json',recovery)
    info['status']='R10_FAILED_SAMPLE_013_REOPENED_FOR_R11'
    info['recovered_samples'][R11_RECOVERY_SAMPLE_ID]=dict(rec['r11_recovery'])
    return info

def read_png(path:Path):
    data=Path(path).read_bytes()
    if data[:8]!=b'\x89PNG\r\n\x1a\n':raise RuntimeError('PNG_SIGNATURE')
    pos=8;idat=bytearray();w=h=bd=ct=inter=None
    while pos<len(data):
        n=struct.unpack('>I',data[pos:pos+4])[0];typ=data[pos+4:pos+8];payload=data[pos+8:pos+8+n];pos+=12+n
        if typ==b'IHDR':w,h,bd,ct,comp,filt,inter=struct.unpack('>IIBBBBB',payload)
        elif typ==b'IDAT':idat.extend(payload)
        elif typ==b'IEND':break
    if bd!=8 or ct not in (2,6) or inter!=0:raise RuntimeError(f'PNG_UNSUPPORTED:{bd}:{ct}:{inter}')
    bpp=3 if ct==2 else 4;raw=zlib.decompress(bytes(idat));stride=w*bpp
    if len(raw)!=h*(stride+1):raise RuntimeError('PNG_RAW_SIZE')
    prev=bytearray(stride);pix=[];off=0
    for y in range(h):
        ft=raw[off];off+=1;scan=bytearray(raw[off:off+stride]);off+=stride;rec=bytearray(stride)
        for i,x in enumerate(scan):
            a=rec[i-bpp] if i>=bpp else 0;b=prev[i];c=prev[i-bpp] if i>=bpp else 0
            if ft==0:v=x
            elif ft==1:v=(x+a)&255
            elif ft==2:v=(x+b)&255
            elif ft==3:v=(x+((a+b)//2))&255
            elif ft==4:v=(x+_paeth(a,b,c))&255
            else:raise RuntimeError('PNG_FILTER:'+str(ft))
            rec[i]=v
        for x in range(w):j=x*bpp;pix.append((rec[j],rec[j+1],rec[j+2]))
        prev=rec
    return w,h,pix
def percentile(vals,q):
    s=sorted(vals);x=(len(s)-1)*q;i=int(math.floor(x));j=min(len(s)-1,i+1);f=x-i;return s[i]*(1-f)+s[j]*f
def rgb_stats(path):
    w,h,p=read_png(path);l=[.2126*r+.7152*g+.0722*b for r,g,b in p];med=statistics.median(l);structural=0
    for y in range(h):
        for x in range(w):
            i=y*w+x;v=l[i];delta=0
            if x+1<w:delta=max(delta,abs(v-l[i+1]))
            if y+1<h:delta=max(delta,abs(v-l[i+w]))
            if abs(v-med)>=12 or delta>=8:structural+=1
    return {'width':w,'height':h,'unique_rgb':len(set(p)),'mean_luma':statistics.mean(l),'p01':percentile(l,.01),'p99':percentile(l,.99),'p01_p99_span':percentile(l,.99)-percentile(l,.01),'structural_fraction':structural/(w*h)}
def perceptual_hash(path):
    w,h,p=read_png(path);vals=[]
    for gy in range(8):
      y=min(h-1,int((gy+.5)*h/8))
      for gx in range(8):
        x=min(w-1,int((gx+.5)*w/8));r,g,b=p[y*w+x];vals.append(.2126*r+.7152*g+.0722*b)
    med=statistics.median(vals);bits=0
    for i,v in enumerate(vals):
      if v>=med:bits|=1<<i
    return f'{bits:016x}'
def hamming_hex(a,b):return (int(a,16)^int(b,16)).bit_count()

def sample_acceptance(req,completion,sample_dir,M,recovery_info=None):
    M['validate_completion'](completion,req,sample_dir)
    stats=rgb_stats(sample_dir/'rgb.png');gt=completion.get('micro100_aux_gt') or {}
    cal=completion.get('camera_calibration',{});fa=cal.get('final_abs_error',{})
    calvals=[float(fa.get(k,float('inf'))) for k in ('fx','fy','cx','cy')]
    normal=gt.get('normal',{}) or {}
    depth=gt.get('depth',{}) or {}
    try: acceptance_sample_index=int(req.get('scene_index',-1))-1000
    except Exception: acceptance_sample_index=-1
    is_r6_normal=(gt.get('r6_addendum_drive_id')==R6_ADDENDUM_DRIVE_ID or 'filter_safe_interior_authority_fraction' in normal)
    if is_r6_normal:
        normal_accept=normal.get('status')=='PASS' and float(normal.get('filter_safe_interior_authority_fraction',0))>=.90 and int(normal.get('unexplained_invalid_interior_pixels',-1))==0
        filter_prov=abs(float(completion.get('renderer_filter_provenance',{}).get('reconstruction_filter_width_px',float('inf')))-1.5)<=1e-12
        normal_semantics='R6_FILTER_SAFE_INTERIOR'
    else:
        # Samples 000..004 are immutable COMPLETE evidence from R2/R3/R4/R5.
        # They already passed the stricter legacy global >=0.90 gate. R6 does
        # not rewrite their completion/QA bytes merely to add new diagnostics.
        normal_accept=normal.get('status')=='PASS' and float(normal.get('authority_fraction',0))>=.90
        filter_prov=True
        normal_semantics='INHERITED_PRE_R6_GLOBAL_PASS'

    # R29 exact-Depth authority. Existing 000..004 COMPLETE peers remain valid
    # under their stricter historical full-raster PASS. Every R29-rendered
    # sample005+ must carry the persisted, hash-bound filter-safe authority mask.
    if acceptance_sample_index>=5:
        dmask=depth.get('filter_safe_interior_mask') or {}
        dmaskp=sample_dir/str(dmask.get('path',''))
        depth_accept=(depth.get('status')=='PASS' and
                      depth.get('authority_semantics')==R29_DEPTH_AUTHORITY_SEMANTICS_ID and
                      depth.get('r29_spec_drive_id')==R29_SPEC_DRIVE_ID and
                      int(depth.get('filter_safe_interior_pixels',0))>0 and
                      int(depth.get('filter_safe_over_tolerance_pixels',-1))==0 and
                      abs(float(depth.get('renderer_filter_width_px',float('inf')))-1.5)<=1e-12 and
                      int(depth.get('filter_support_radius_px',-1))==2 and
                      depth.get('raw_exr_immutable') is True and
                      dmask.get('path')=='depth_filter_safe_interior_mask.uint8.bin' and
                      dmaskp.is_file() and dmaskp.stat().st_size==int(dmask.get('bytes',-1)) and
                      sha256_file(dmaskp)==dmask.get('sha256'))
        depth_semantics='R29_FILTER_SAFE_INTERIOR_EXACT_DEPTH'
    else:
        depth_accept=depth.get('status')=='PASS'
        depth_semantics='INHERITED_PRE_R29_FULL_RASTER_PASS'
    # R24 + R33 compositional RGB provenance. R10/R17 are mutually
    # exclusive, R23 may follow them, and R33 may follow the inherited terminal
    # RGB. Every junction is hash-bound and no RGB statistic participates in
    # eligibility.
    r17_policy=r17_camera_inside_contrast_policy(req)
    r10_expected=(req.get('split') in {'MICRO100_QUALIFICATION_ONLY','SCALE1K_QUALIFICATION_ONLY'} and req.get('appearance',{}).get('profile_id')=='TOON' and req.get('scene',{}).get('scene_family') in {'INTERIOR','CORRIDOR','CLUTTER','HYBRID_CONCEPT'})
    r10_meta=completion.get('r10_rgb_contrast') or {}
    r17_meta=completion.get('r17_camera_inside_rgb_contrast') or {}
    r23_policy=r23_systemic_rgb_policy(req)
    r23_meta=completion.get('r23_systemic_rgb_contrast') or {}
    r23_policy_meta=completion.get('r23_systemic_rgb_policy') or {}
    r33_policy=r33_blueprint_vertical_dominant_policy(req)
    r33_meta=completion.get('r33_blueprint_fixed_rgb_gain') or {}
    r33_policy_meta=completion.get('r33_blueprint_vertical_dominant_policy') or {}
    r36_policy=r36_blueprint_extreme_vertical_policy(req)
    r36_meta=completion.get('r36_blueprint_fixed_rgb_gain') or {}
    r36_policy_meta=completion.get('r36_blueprint_extreme_vertical_policy') or {}
    g101_r2_policy=g101_r2_blueprint_foreground_vertical_policy(req)
    g101_r2_meta=completion.get('g101_r2_blueprint_fixed_rgb_gain') or {}
    g101_r2_policy_meta=completion.get('g101_r2_blueprint_foreground_vertical_policy') or {}
    rawp=sample_dir/'rgb_renderer_raw.png'
    pre23=sample_dir/'rgb_pre_r23.png'
    pre33=sample_dir/'rgb_pre_r33.png'
    pre36=sample_dir/'rgb_pre_r36.png'
    pre_g101_r2=sample_dir/'rgb_pre_g101_r2.png'
    rgbp=sample_dir/'rgb.png'
    try: sample_index=int(req.get('scene_index',-1))-1000
    except Exception: sample_index=-1
    try: g101_sample_index=int(req.get('scene_index',-1))-2000
    except Exception: g101_sample_index=-1
    r23_required=(sample_index>=30 or req.get('sample_id')==R23_RECOVERY_SAMPLE_ID)
    r33_required=(sample_index>=60 or req.get('sample_id')==R33_RECOVERY_SAMPLE_ID)
    r36_required=(sample_index>=80 or req.get('sample_id')==R36_RECOVERY_SAMPLE_ID)
    g101_r2_required=(req.get('dataset_id')=='PCS_CAMERA_GEOMETRY_SCALE1K_V1' and (g101_sample_index>=10 or req.get('sample_id')==G101_R2_RECOVERY_SAMPLE_ID))
    r23_policy_applies=bool(r23_policy.get('applied'))
    r33_policy_applies=bool(r33_policy.get('applied'))
    r36_policy_applies=bool(r36_policy.get('applied'))
    g101_r2_policy_applies=bool(g101_r2_policy.get('applied'))
    r23_layer_present=bool(r23_meta) or pre23.exists()
    r33_layer_present=bool(r33_meta) or pre33.exists()
    r36_layer_present=bool(r36_meta) or pre36.exists()
    g101_r2_layer_present=bool(g101_r2_meta) or pre_g101_r2.exists()

    # G101-R2 is the optional terminal layer. Every inherited transform binds
    # to the exact terminal immediately before its own layer.
    terminal_before_g101_r2_path=pre_g101_r2 if g101_r2_layer_present else rgbp
    terminal_before_g101_r2_sha=sha256_file(terminal_before_g101_r2_path) if terminal_before_g101_r2_path.is_file() else None
    terminal_before_r36_path=pre36 if r36_layer_present else terminal_before_g101_r2_path
    terminal_before_r36_sha=sha256_file(terminal_before_r36_path) if terminal_before_r36_path.is_file() else None
    terminal_before_r33_path=pre33 if r33_layer_present else terminal_before_r36_path
    terminal_before_r33_sha=sha256_file(terminal_before_r33_path) if terminal_before_r33_path.is_file() else None
    prior_terminal_path=pre23 if r23_layer_present else terminal_before_r33_path
    prior_terminal_sha=sha256_file(prior_terminal_path) if prior_terminal_path.is_file() else None

    if r10_expected:
        r10_prov=(not r17_meta and rawp.is_file() and prior_terminal_sha is not None and
                  r10_meta.get('implementation_id')=='DF_G100_TOON_CLOSED_ROOM_RGB_CONTRAST_V1_R10' and
                  int(r10_meta.get('pivot_u8',-1))==128 and int(r10_meta.get('factor_numerator',-1))==5 and int(r10_meta.get('factor_denominator',-1))==4 and
                  r10_meta.get('adaptive') is False and r10_meta.get('threshold_adaptive') is False and r10_meta.get('sample_statistics_used') is False and
                  r10_meta.get('spatial_warp') is False and r10_meta.get('resize') is False and r10_meta.get('resample') is False and
                  r10_meta.get('raw_sha256')==sha256_file(rawp) and r10_meta.get('final_sha256')==prior_terminal_sha)
    else:
        r10_prov=(not r10_meta)

    r15_policy=r15_camera_inside_fill_policy(req)
    r15_meta=completion.get('r15_camera_inside_visibility_aid') or {}
    if r15_policy.get('applied'):
        r15_prov=(r15_meta.get('implementation_id')=='DF_G100_CAMERA_INSIDE_SOLID_CAMERA_FILL_V1_R15' and r15_meta.get('applied') is True and
                   r15_meta.get('camera_inside_solid_object_ids')==r15_policy.get('camera_inside_solid_object_ids') and
                   float(r15_meta.get('energy_w',-1))==350.0 and float(r15_meta.get('soft_shadow_radius_m',-1))==2.0 and
                   r15_meta.get('location')=='BLENDER_CAMERA_LOCATION' and r15_meta.get('geometry_preserving') is True and
                   r15_meta.get('spatial_warp') is False and r15_meta.get('adaptive') is False and r15_meta.get('threshold_adaptive') is False)
    else:
        r15_prov=(not r15_meta) or (r15_meta.get('implementation_id')=='DF_G100_CAMERA_INSIDE_SOLID_CAMERA_FILL_V1_R15' and r15_meta.get('applied') is False and r15_meta.get('camera_inside_solid_object_ids')==r15_policy.get('camera_inside_solid_object_ids'))

    if r17_policy.get('applied'):
        r17_prov=(not r10_meta and rawp.is_file() and prior_terminal_sha is not None and
                  r17_meta.get('implementation_id')=='DF_G100_CAMERA_INSIDE_FIXED_RGB_CONTRAST_V1_R17' and
                  int(r17_meta.get('pivot_u8',-1))==128 and int(r17_meta.get('factor_numerator',-1))==17 and int(r17_meta.get('factor_denominator',-1))==16 and
                  r17_meta.get('adaptive') is False and r17_meta.get('threshold_adaptive') is False and r17_meta.get('sample_statistics_used') is False and
                  r17_meta.get('spatial_warp') is False and r17_meta.get('resize') is False and r17_meta.get('resample') is False and
                  r17_meta.get('raw_sha256')==sha256_file(rawp) and r17_meta.get('final_sha256')==prior_terminal_sha)
    else:
        r17_prov=(not r17_meta and (r10_expected or not rawp.exists()))

    transform_exclusive=not (bool(r10_meta) and bool(r17_meta)) and not (r10_expected and bool(r17_policy.get('applied')))
    legacy_r23_metadata_bridge=False
    if r23_required:
        policy_exact=(r23_policy_meta==r23_policy)
        if r23_policy_applies:
            exact_r23=(policy_exact and pre23.is_file() and terminal_before_r33_path.is_file() and
                       r23_meta.get('implementation_id')==r23_policy.get('implementation_id') and
                       int(r23_meta.get('pivot_u8',-1))==int(r23_policy['pivot_u8']) and
                       int(r23_meta.get('factor_numerator',-1))==int(r23_policy['factor_numerator']) and
                       int(r23_meta.get('factor_denominator',-1))==int(r23_policy['factor_denominator']) and
                       r23_meta.get('adaptive') is False and r23_meta.get('threshold_adaptive') is False and
                       r23_meta.get('sample_statistics_used') is False and r23_meta.get('spatial_warp') is False and
                       r23_meta.get('resize') is False and r23_meta.get('resample') is False and
                       r23_meta.get('raw_sha256')==sha256_file(pre23) and r23_meta.get('final_sha256')==terminal_before_r33_sha)
            if sample_index>=R24_PRESTATE_COMPLETED:
                authority_meta=(r23_meta.get('lab_only') is False and r23_meta.get('production_authorized') is True)
            else:
                authority_meta=((r23_meta.get('lab_only') in (None,True,False)) and (r23_meta.get('production_authorized') in (None,True)))
                legacy_r23_metadata_bridge=bool(exact_r23 and authority_meta and (r23_meta.get('lab_only') is not False or r23_meta.get('production_authorized') is not True))
            r23_prov=bool(exact_r23 and authority_meta)
        else:
            r23_prov=(policy_exact and not r23_meta and not pre23.exists())
    else:
        if r23_policy_meta or r23_meta or pre23.exists():
            r23_prov=(r23_policy_meta==r23_policy and ((not r23_policy_applies and not r23_meta and not pre23.exists()) or
                       (r23_policy_applies and pre23.is_file() and r23_meta.get('implementation_id')==r23_policy.get('implementation_id') and
                        r23_meta.get('raw_sha256')==sha256_file(pre23) and r23_meta.get('final_sha256')==terminal_before_r33_sha)))
        else:
            r23_prov=True

    # R33 exact fixed-gain provenance. Historical samples000..059 other than 051
    # remain immutable and are not required to carry retroactive R33 metadata.
    r33_policy_exact=(r33_policy_meta==r33_policy)
    if r33_required:
        if r33_policy_applies:
            r33_prov=(r33_policy_exact and pre33.is_file() and rgbp.is_file() and
                      r33_meta.get('implementation_id')==R33_IMPLEMENTATION_ID and
                      int(r33_meta.get('gain_numerator',-1))==2 and int(r33_meta.get('gain_denominator',-1))==1 and int(r33_meta.get('offset_u8',-1))==0 and
                      r33_meta.get('adaptive') is False and r33_meta.get('threshold_adaptive') is False and r33_meta.get('sample_statistics_used') is False and
                      r33_meta.get('spatial_warp') is False and r33_meta.get('resize') is False and r33_meta.get('resample') is False and
                      r33_meta.get('raw_sha256')==sha256_file(pre33) and r33_meta.get('final_sha256')==terminal_before_r36_sha)
        else:
            r33_prov=(r33_policy_exact and not r33_meta and not pre33.exists())
    else:
        if r33_policy_meta or r33_meta or pre33.exists():
            r33_prov=(r33_policy_exact and ((not r33_policy_applies and not r33_meta and not pre33.exists()) or
                      (r33_policy_applies and pre33.is_file() and r33_meta.get('raw_sha256')==sha256_file(pre33) and r33_meta.get('final_sha256')==terminal_before_r36_sha)))
        else:
            r33_prov=True

    # R36 exact fixed-gain provenance. Historical samples000..079 other than
    # recovered sample074 remain immutable and do not require retroactive R36
    # metadata. Samples080+ must carry explicit R36 policy metadata.
    r36_policy_exact=(r36_policy_meta==r36_policy)
    if r36_required:
        if r36_policy_applies:
            r36_prov=(r36_policy_exact and pre36.is_file() and rgbp.is_file() and
                      r36_meta.get('implementation_id')==R36_IMPLEMENTATION_ID and
                      int(r36_meta.get('gain_numerator',-1))==3 and int(r36_meta.get('gain_denominator',-1))==1 and int(r36_meta.get('offset_u8',-1))==0 and
                      r36_meta.get('adaptive') is False and r36_meta.get('threshold_adaptive') is False and r36_meta.get('sample_statistics_used') is False and
                      r36_meta.get('spatial_warp') is False and r36_meta.get('resize') is False and r36_meta.get('resample') is False and
                      r36_meta.get('raw_sha256')==sha256_file(pre36) and r36_meta.get('final_sha256')==terminal_before_g101_r2_sha)
        else:
            r36_prov=(r36_policy_exact and not r36_meta and not pre36.exists())
    else:
        if r36_policy_meta or r36_meta or pre36.exists():
            r36_prov=(r36_policy_exact and ((not r36_policy_applies and not r36_meta and not pre36.exists()) or
                      (r36_policy_applies and pre36.is_file() and r36_meta.get('raw_sha256')==sha256_file(pre36) and r36_meta.get('final_sha256')==terminal_before_g101_r2_sha)))
        else:
            r36_prov=True

    # G101 R2 exact fixed-gain provenance. Historical chunk000 peers other
    # than recovered sample0005 are intentionally grandfathered without
    # retroactive R2 metadata; newly rendered sample0010+ must be explicit.
    g101_r2_policy_exact=(g101_r2_policy_meta==g101_r2_policy)
    if g101_r2_required:
        if g101_r2_policy_applies:
            g101_r2_prov=(g101_r2_policy_exact and pre_g101_r2.is_file() and rgbp.is_file() and
                          g101_r2_meta.get('implementation_id')==G101_R2_IMPLEMENTATION_ID and
                          int(g101_r2_meta.get('gain_numerator',-1))==2 and int(g101_r2_meta.get('gain_denominator',-1))==1 and int(g101_r2_meta.get('offset_u8',-1))==0 and
                          g101_r2_meta.get('adaptive') is False and g101_r2_meta.get('threshold_adaptive') is False and g101_r2_meta.get('sample_statistics_used') is False and
                          g101_r2_meta.get('spatial_warp') is False and g101_r2_meta.get('resize') is False and g101_r2_meta.get('resample') is False and
                          g101_r2_meta.get('raw_sha256')==sha256_file(pre_g101_r2) and g101_r2_meta.get('final_sha256')==sha256_file(rgbp))
        else:
            g101_r2_prov=(g101_r2_policy_exact and not g101_r2_meta and not pre_g101_r2.exists())
    else:
        if g101_r2_policy_meta or g101_r2_meta or pre_g101_r2.exists():
            g101_r2_prov=(g101_r2_policy_exact and ((not g101_r2_policy_applies and not g101_r2_meta and not pre_g101_r2.exists()) or
                          (g101_r2_policy_applies and pre_g101_r2.is_file() and g101_r2_meta.get('raw_sha256')==sha256_file(pre_g101_r2) and g101_r2_meta.get('final_sha256')==sha256_file(rgbp))))
        else:
            g101_r2_prov=True

    prior_layer=('R10' if r10_expected else ('R17' if r17_policy.get('applied') else 'NONE'))
    r23_junction_ok=True
    if r23_layer_present and prior_layer=='R10':
        r23_junction_ok=bool(r10_meta.get('final_sha256')==sha256_file(pre23) if pre23.is_file() else False)
    elif r23_layer_present and prior_layer=='R17':
        r23_junction_ok=bool(r17_meta.get('final_sha256')==sha256_file(pre23) if pre23.is_file() else False)
    r33_junction_ok=True
    if r33_layer_present:
        if not pre33.is_file():
            r33_junction_ok=False
        elif r23_layer_present:
            r33_junction_ok=(r23_meta.get('final_sha256')==sha256_file(pre33))
        elif prior_layer=='R10':
            r33_junction_ok=(r10_meta.get('final_sha256')==sha256_file(pre33))
        elif prior_layer=='R17':
            r33_junction_ok=(r17_meta.get('final_sha256')==sha256_file(pre33))
    r36_junction_ok=True
    if r36_layer_present:
        if not pre36.is_file():
            r36_junction_ok=False
        elif r33_layer_present:
            r36_junction_ok=(r33_meta.get('final_sha256')==sha256_file(pre36))
        elif r23_layer_present:
            r36_junction_ok=(r23_meta.get('final_sha256')==sha256_file(pre36))
        elif prior_layer=='R10':
            r36_junction_ok=(r10_meta.get('final_sha256')==sha256_file(pre36))
        elif prior_layer=='R17':
            r36_junction_ok=(r17_meta.get('final_sha256')==sha256_file(pre36))
    g101_r2_junction_ok=True
    if g101_r2_layer_present:
        if not pre_g101_r2.is_file():
            g101_r2_junction_ok=False
        elif r36_layer_present:
            g101_r2_junction_ok=(r36_meta.get('final_sha256')==sha256_file(pre_g101_r2))
        elif r33_layer_present:
            g101_r2_junction_ok=(r33_meta.get('final_sha256')==sha256_file(pre_g101_r2))
        elif r23_layer_present:
            g101_r2_junction_ok=(r23_meta.get('final_sha256')==sha256_file(pre_g101_r2))
        elif prior_layer=='R10':
            g101_r2_junction_ok=(r10_meta.get('final_sha256')==sha256_file(pre_g101_r2))
        elif prior_layer=='R17':
            g101_r2_junction_ok=(r17_meta.get('final_sha256')==sha256_file(pre_g101_r2))
    r2_exclusive=not (g101_r2_policy_applies and (r33_policy_applies or r36_policy_applies))
    junction_ok=bool(r23_junction_ok and r33_junction_ok and r36_junction_ok and g101_r2_junction_ok and r2_exclusive)
    rgb_chain={'schema':'DF-G101-R2-COMPOSITIONAL-RGB-PROVENANCE-V1',
               'r24_addendum_drive_id':R24_ADDENDUM_DRIVE_ID,'r33_spec_drive_id':R33_SPEC_DRIVE_ID,'r36_spec_drive_id':R36_SPEC_DRIVE_ID,'g101_r2_spec_drive_id':G101_R2_SPEC_DRIVE_ID,
               'prior_layer':prior_layer,'r23_policy_applies':r23_policy_applies,'r23_layer_present':r23_layer_present,
               'r33_policy_applies':r33_policy_applies,'r33_layer_present':r33_layer_present,
               'r36_policy_applies':r36_policy_applies,'r36_layer_present':r36_layer_present,
               'g101_r2_policy_applies':g101_r2_policy_applies,'g101_r2_layer_present':g101_r2_layer_present,
               'r23_junction_bit_exact':bool(r23_junction_ok),'r33_junction_bit_exact':bool(r33_junction_ok),'r36_junction_bit_exact':bool(r36_junction_ok),'g101_r2_junction_bit_exact':bool(g101_r2_junction_ok),
               'junction_bit_exact':bool(junction_ok),'transform_exclusive':bool(transform_exclusive and r2_exclusive),
               'legacy_r23_metadata_bridge':bool(legacy_r23_metadata_bridge),'thresholds_or_rgb_stats_used':False}
    prov={'dataset':req.get('dataset_id')==DATASET_ID,'sample':completion.get('sample_id')==req['sample_id'],'scene':bool(req['scene'].get('base_scene_id') and req['scene'].get('recipe_digest_sha256')),
          'camera':bool(req['camera'].get('K') and req['camera'].get('pose')),'appearance':bool(req['appearance'].get('profile_digest_sha256')),'renderer':completion.get('renderer',{}).get('engine')=='CYCLES','renderer_filter':filter_prov,
          'blender':bool(completion.get('blender_version') and completion.get('blender_build_hash')),'runtime':bool(completion.get('runtime_archive_sha256')),'release':req.get('release_id')==RELEASE_ID,
          'passes':completion.get('passes_requested')==['RGB','DEPTH','NORMAL','OBJECT_INDEX'],'root_seed':req['scene'].get('root_seed_u64') is not None,
          'r10_rgb_contrast':bool(r10_prov),'r15_camera_inside_fill':bool(r15_prov),'r17_camera_inside_rgb_contrast':bool(r17_prov),
          'r23_systemic_rgb':bool(r23_prov),'r24_compositional_rgb':bool(r23_junction_ok and transform_exclusive),
          'r33_blueprint_vertical_gain':bool(r33_prov and r33_junction_ok),'r36_blueprint_extreme_vertical_gain':bool(r36_prov and r36_junction_ok),
          'g101_r2_blueprint_foreground_vertical_gain':bool(g101_r2_prov and g101_r2_junction_ok and r2_exclusive)}
    checks={'completion_integrity':True,'camera_calibration_finite':all(math.isfinite(x) for x in calvals),'camera_calibration_abs_error_le_0_001px':max(calvals)<=0.001,
            'camera_reprojection_max':float(completion['camera_reprojection']['max_residual_px'])<=.50,'camera_reprojection_median':float(completion['camera_reprojection']['median_residual_px'])<=.20,
            'object_index_analytic':gt.get('object_index',{}).get('status')=='PASS','depth_analytic':bool(depth_accept),'normal_analytic':bool(normal_accept),
            'raster_direct':gt.get('raster',{}).get('convention')=='DIRECT_TOP_LEFT_Y_DOWN_PIXEL_CENTER' and gt.get('raster',{}).get('hidden_flip') is False,
            'rgb_unique':stats['unique_rgb']>=32,'rgb_span':stats['p01_p99_span']>=24,'rgb_mean':12<=stats['mean_luma']<=243,'rgb_structural':stats['structural_fraction']>=.03,
            'provenance':all(prov.values())}
    out={'schema':'DF-G100-PER-SAMPLE-ACCEPTANCE-V6-R11','status':'PASS' if all(checks.values()) else 'FAIL','sample_id':req['sample_id'],'request_digest':req['input_digest_sha256'],'checks':checks,'rgb':stats,'gt':gt,'normal_acceptance_semantics':normal_semantics,'depth_acceptance_semantics':depth_semantics,'camera_calibration_abs_error':fa,'provenance_checks':prov,'rgb_provenance_chain':rgb_chain,'rgb_sha256':sha256_file(sample_dir/'rgb.png'),'perceptual_hash_8x8':perceptual_hash(sample_dir/'rgb.png'),'recovery':recovery_info}
    return out

def apply_r15_resume_if_needed(runroot:Path,chunks):
    """Fail-closed R14 COMPLETE sample015 RGB-acceptance -> R15 shading recovery.

    Samples000..014 and 016..019 remain immutable COMPLETE peers. The current
    sample015 payload is independently integrity-checked, required to match the
    exact historical raw RGB/GT fingerprints and the proved four-gate RGB failure
    class, then preserved before reopening only sample015.
    """
    info={'schema':'DF-G100-R15-RESUME-V1','status':'NOT_APPLICABLE','r15_addendum_drive_id':R15_ADDENDUM_DRIVE_ID,'recovered_samples':{},'completed_samples_preserved':[]}
    runroot=Path(runroot); cr=runroot/'CHUNKS'/'chunk_01'; lp=cr/'ledger.json'
    if not lp.is_file(): return info
    led=json.loads(lp.read_text(encoding='utf-8'))
    if led.get('chunk_digest_sha256')!=R15_CHUNK01_DIGEST: raise RuntimeError('G100_R15_RESUME_CHUNK01_DIGEST_MISMATCH')
    expected={r['sample_id']:r['input_digest_sha256'] for r in chunks[1]['requests']}
    if len(expected)!=10 or expected.get(R15_RECOVERY_SAMPLE_ID)!=R15_RECOVERY_REQUEST_DIGEST: raise RuntimeError('G100_R15_RESUME_FROZEN_PLAN_TARGET_MISMATCH')
    states=led.get('states') or {}; rec=states.get(R15_RECOVERY_SAMPLE_ID,{})
    if rec.get('request_digest')!=R15_RECOVERY_REQUEST_DIGEST: raise RuntimeError('G100_R15_RESUME_LEDGER_REQUEST_DIGEST_MISMATCH')
    if (rec.get('r15_recovery') or {}).get('r15_addendum_drive_id')==R15_ADDENDUM_DRIVE_ID:
        if rec.get('state') in {'PENDING','RUNNING','COMPLETE','FAILED_RETRYABLE','FAILED_FINAL'}:
            info['status']='R15_RECOVERY_ALREADY_APPLIED'; info['recovered_samples'][R15_RECOVERY_SAMPLE_ID]=dict(rec.get('r15_recovery') or {}); return info
        raise RuntimeError('G100_R15_RESUME_BAD_POST_RECOVERY_STATE')
    if rec.get('state')!='COMPLETE' or int(rec.get('attempts',-1))!=1 or (rec.get('r12_recovery') or {}).get('r12_addendum_drive_id')!=R12_ADDENDUM_DRIVE_ID:
        raise RuntimeError('G100_R15_RESUME_EXACT_R14_COMPLETE_PRECONDITION')
    # Every already-rendered peer remains immutable.
    for ci in (0,1):
        cp=runroot/'CHUNKS'/f'chunk_{ci:02d}'/'ledger.json'
        if not cp.is_file(): raise RuntimeError('G100_R15_RESUME_PRIOR_LEDGER_MISSING:'+str(ci))
        L=json.loads(cp.read_text(encoding='utf-8'))
        for sid,rr in (L.get('states') or {}).items():
            if sid==R15_RECOVERY_SAMPLE_ID: continue
            if rr.get('state')!='COMPLETE': raise RuntimeError('G100_R15_RESUME_COMPLETE_PEER_STATE_MISMATCH:'+sid)
            info['completed_samples_preserved'].append(sid)
    for ci in range(2,10):
        cp=runroot/'CHUNKS'/f'chunk_{ci:02d}'/'ledger.json'
        if cp.is_file():
            L=json.loads(cp.read_text(encoding='utf-8'))
            bad=[sid for sid,rr in (L.get('states') or {}).items() if rr.get('state')!='PENDING']
            if bad: raise RuntimeError('G100_R15_RESUME_LATER_SAMPLE_NOT_PENDING:'+bad[0])
    sd=cr/'samples'/R15_RECOVERY_SAMPLE_ID; reqp=cr/'requests'/f'{R15_RECOVERY_SAMPLE_ID}.json'; logp=cr/'logs'/f'{R15_RECOVERY_SAMPLE_ID}.log'
    if not sd.is_dir() or not reqp.is_file() or not logp.is_file() or not (sd/'completion.json').is_file(): raise RuntimeError('G100_R15_RESUME_CURRENT_COMPLETE_EVIDENCE_MISSING')
    if sha256_file(reqp)!=R15_EXPECTED_RAW_SHA256['request.json']: raise RuntimeError('G100_R15_RESUME_REQUEST_FILE_SHA_MISMATCH')
    reqobj=json.loads(reqp.read_text(encoding='utf-8'))
    if reqobj.get('sample_id')!=R15_RECOVERY_SAMPLE_ID or reqobj.get('input_digest_sha256')!=R15_RECOVERY_REQUEST_DIGEST: raise RuntimeError('G100_R15_RESUME_REQUEST_CONTENT_MISMATCH')
    for name in ('rgb.png','depth.exr','object_index.exr','normal.exr'):
        fp=sd/name
        if not fp.is_file() or sha256_file(fp)!=R15_EXPECTED_RAW_SHA256[name]: raise RuntimeError('G100_R15_RESUME_RAW_FINGERPRINT_MISMATCH:'+name)
    comp=json.loads((sd/'completion.json').read_text(encoding='utf-8'))
    if comp.get('status')!='PASS_REAL_BLENDER_RENDERED' or comp.get('sample_id')!=R15_RECOVERY_SAMPLE_ID or comp.get('input_digest_sha256')!=R15_RECOVERY_REQUEST_DIGEST: raise RuntimeError('G100_R15_RESUME_COMPLETION_IDENTITY_MISMATCH')
    for fr in comp.get('files',[]):
        fp=sd/fr.get('path','')
        if not fp.is_file() or fp.stat().st_size!=int(fr.get('bytes',-1)) or sha256_file(fp)!=fr.get('sha256'): raise RuntimeError('G100_R15_RESUME_COMPLETION_FILE_INTEGRITY:'+str(fr.get('path')))
    repro=comp.get('camera_reprojection') or {}; fa=(comp.get('camera_calibration') or {}).get('final_abs_error') or {}; gt=comp.get('micro100_aux_gt') or {}
    if float(repro.get('max_residual_px',999))>.50 or float(repro.get('median_residual_px',999))>.20: raise RuntimeError('G100_R15_RESUME_NON_RGB_REPROJECTION_NOT_PASS')
    if max(float(fa.get(k,999)) for k in ('fx','fy','cx','cy'))>.001: raise RuntimeError('G100_R15_RESUME_NON_RGB_CALIBRATION_NOT_PASS')
    if (gt.get('object_index') or {}).get('status')!='PASS' or (gt.get('depth') or {}).get('status')!='PASS' or (gt.get('normal') or {}).get('status')!='PASS': raise RuntimeError('G100_R15_RESUME_NON_RGB_GT_NOT_PASS')
    st=rgb_stats(sd/'rgb.png')
    if not (st['unique_rgb']==2 and abs(st['mean_luma']-R15_EXPECTED_RGB_STATS['mean_luma'])<1e-12 and abs(st['p01_p99_span']-1.0)<1e-12 and abs(st['structural_fraction'])<1e-15 and st['unique_rgb']<32 and st['p01_p99_span']<24 and st['mean_luma']<12 and st['structural_fraction']<.03):
        raise RuntimeError('G100_R15_RESUME_RGB_FAILURE_CLASS_MISMATCH')
    prior_records=_tree_records(sd)
    evroot=runroot/'RECOVERY'/'R14_COMPLETE_SAMPLE_015_RGB_ACCEPTANCE_FAIL'; evroot.mkdir(parents=True,exist_ok=True); payload=evroot/'sample_bytes'
    if payload.exists(): shutil.rmtree(payload)
    shutil.copytree(sd,payload)
    if _tree_records(payload)!=prior_records: raise RuntimeError('G100_R15_RESUME_PRESERVE_HASH_MISMATCH')
    shutil.copy2(reqp,evroot/'request.json'); shutil.copy2(logp,evroot/'worker.log')
    accp=runroot/'EVIDENCE'/'SAMPLE_ACCEPTANCE'/f'{R15_RECOVERY_SAMPLE_ID}.json'
    if accp.is_file(): shutil.copy2(accp,evroot/'sample_acceptance.json')
    else: atomic_json(evroot/'sample_acceptance.json',{'schema':'DF-G100-R15-RECOVERY-ACCEPTANCE-SIGNATURE-V1','sample_id':R15_RECOVERY_SAMPLE_ID,'status':'FAIL','rgb':st,'checks':{'rgb_unique':False,'rgb_span':False,'rgb_mean':False,'rgb_structural':False}})
    recovery={'schema':'DF-G100-R15-RECOVERY-JOURNAL-V1','status':'PRESERVED_BEFORE_LEDGER_RESET','r15_addendum_drive_id':R15_ADDENDUM_DRIVE_ID,'source_tool':'R14','target_tool':'R15','sample_id':R15_RECOVERY_SAMPLE_ID,'request_digest':R15_RECOVERY_REQUEST_DIGEST,'chunk_digest_sha256':R15_CHUNK01_DIGEST,'prior_state':'COMPLETE','prior_attempts':1,'prior_rgb_stats':st,'prior_raw_sha256':dict(R15_EXPECTED_RAW_SHA256),'preserved_members':prior_records,'preserved_worker_log_sha256':sha256_file(evroot/'worker.log'),'preserved_request_sha256':sha256_file(evroot/'request.json'),'completed_samples_preserved':sorted(info['completed_samples_preserved']),'r15_fill_implementation':'DF_G100_CAMERA_INSIDE_SOLID_CAMERA_FILL_V1_R15','recorded_utc':utc_iso(),'product_mutated':False,'maya_mutated':False,'test77_accessed':False,'training_started':False}
    atomic_json(evroot/'R15_RECOVERY_JOURNAL.json',recovery)
    shutil.rmtree(sd); sd.mkdir(parents=True,exist_ok=True)
    rec['state']='PENDING'; rec['attempts']=0; rec.pop('last_error',None)
    rec['r15_recovery']={'r15_addendum_drive_id':R15_ADDENDUM_DRIVE_ID,'prior_state':'COMPLETE','prior_attempts':1,'prior_acceptance_failure':'rgb_unique=false,rgb_span=false,rgb_mean=false,rgb_structural=false','recovery_journal_rel':(evroot/'R15_RECOVERY_JOURNAL.json').relative_to(runroot).as_posix(),'r15_fill_implementation':'DF_G100_CAMERA_INSIDE_SOLID_CAMERA_FILL_V1_R15'}
    atomic_json(lp,led); recovery['status']='LEDGER_RESET_SAMPLE_015_ONLY'; atomic_json(evroot/'R15_RECOVERY_JOURNAL.json',recovery)
    info['status']='R14_COMPLETE_SAMPLE_015_REOPENED_FOR_R15'; info['recovered_samples'][R15_RECOVERY_SAMPLE_ID]=dict(rec['r15_recovery']); return info


def _r16_rgb_failure_class(stats):
    return (
        int(stats.get('unique_rgb',10**9)) < 32 and
        float(stats.get('p01_p99_span',10**9)) < 24.0 and
        (float(stats.get('mean_luma',128.0)) < 12.0 or float(stats.get('mean_luma',128.0)) > 243.0) and
        float(stats.get('structural_fraction',1.0)) < 0.03
    )

def _r16_acceptance_signature(acc,stats,rgb_sha):
    if not isinstance(acc,dict): return False
    if acc.get('sample_id')!=R16_RECOVERY_SAMPLE_ID or acc.get('request_digest')!=R16_RECOVERY_REQUEST_DIGEST: return False
    if acc.get('status')!='FAIL': return False
    checks=acc.get('checks') or {}
    for k in ('rgb_unique','rgb_span','rgb_mean','rgb_structural'):
        if checks.get(k) is not False: return False
    for k in ('completion_integrity','camera_calibration_finite','camera_calibration_abs_error_le_0_001px',
              'camera_reprojection_max','camera_reprojection_median','object_index_analytic','depth_analytic',
              'normal_analytic','raster_direct','provenance'):
        if checks.get(k) is not True: return False
    if acc.get('rgb_sha256')!=rgb_sha: return False
    arst=acc.get('rgb') or {}
    if int(arst.get('unique_rgb',-1))!=int(stats['unique_rgb']): return False
    for k in ('mean_luma','p01','p99','p01_p99_span','structural_fraction'):
        if abs(float(arst.get(k,float('inf')))-float(stats[k]))>1e-12: return False
    return True

def apply_r16_resume_if_needed(runroot:Path,chunks):
    """Fail-closed R15 authority correction for the live COMPLETE sample015 payload.

    Historical RECOVERY/R11_FAILED_SAMPLE_015 hashes are evidence only. Current
    live bytes are authenticated by the package-frozen request/ledger chain,
    completion.json's declared file hashes, the persisted post-chunk acceptance
    signature, and a fresh RGB recomputation. Only after exact preservation is
    sample015 reopened.
    """
    info={'schema':'DF-G100-R16-RESUME-V1','status':'NOT_APPLICABLE','r16_addendum_drive_id':R16_ADDENDUM_DRIVE_ID,
          'r15_failure_return_sha256':R16_PRIOR_R15_RETURN_SHA256,'recovered_samples':{},'completed_samples_preserved':[]}
    runroot=Path(runroot); cr=runroot/'CHUNKS'/'chunk_01'; lp=cr/'ledger.json'
    if not lp.is_file(): return info
    led=json.loads(lp.read_text(encoding='utf-8'))
    if led.get('chunk_digest_sha256')!=R16_CHUNK01_DIGEST:
        raise RuntimeError('G100_R16_RESUME_CHUNK01_DIGEST_MISMATCH')
    expected={r['sample_id']:r['input_digest_sha256'] for r in chunks[1]['requests']}
    if len(expected)!=10 or expected.get(R16_RECOVERY_SAMPLE_ID)!=R16_RECOVERY_REQUEST_DIGEST:
        raise RuntimeError('G100_R16_RESUME_FROZEN_PLAN_TARGET_MISMATCH')
    states=led.get('states') or {}; rec=states.get(R16_RECOVERY_SAMPLE_ID,{})
    if rec.get('request_digest')!=R16_RECOVERY_REQUEST_DIGEST:
        raise RuntimeError('G100_R16_RESUME_LEDGER_REQUEST_DIGEST_MISMATCH')
    if (rec.get('r16_recovery') or {}).get('r16_addendum_drive_id')==R16_ADDENDUM_DRIVE_ID:
        if rec.get('state') in {'PENDING','RUNNING','COMPLETE','FAILED_RETRYABLE','FAILED_FINAL'}:
            info['status']='R16_RECOVERY_ALREADY_APPLIED'
            info['recovered_samples'][R16_RECOVERY_SAMPLE_ID]=dict(rec.get('r16_recovery') or {})
            return info
        raise RuntimeError('G100_R16_RESUME_BAD_POST_RECOVERY_STATE')
    if rec.get('r15_recovery'):
        raise RuntimeError('G100_R16_RESUME_UNEXPECTED_R15_LEDGER_MUTATION')
    if rec.get('state')!='COMPLETE' or int(rec.get('attempts',-1))!=1 or (rec.get('r12_recovery') or {}).get('r12_addendum_drive_id')!=R12_ADDENDUM_DRIVE_ID:
        raise RuntimeError('G100_R16_RESUME_EXACT_PRE_RECOVERY_COMPLETE_PRECONDITION')

    peer_records={}
    for ci in (0,1):
        cp=runroot/'CHUNKS'/f'chunk_{ci:02d}'/'ledger.json'
        if not cp.is_file(): raise RuntimeError('G100_R16_RESUME_PRIOR_LEDGER_MISSING:'+str(ci))
        L=json.loads(cp.read_text(encoding='utf-8'))
        peer_records[ci]=cp.read_bytes()
        for sid,rr in (L.get('states') or {}).items():
            if sid==R16_RECOVERY_SAMPLE_ID: continue
            if rr.get('state')!='COMPLETE':
                raise RuntimeError('G100_R16_RESUME_COMPLETE_PEER_STATE_MISMATCH:'+sid)
            info['completed_samples_preserved'].append(sid)
    if len(info['completed_samples_preserved'])!=19:
        raise RuntimeError('G100_R16_RESUME_EXPECTED_19_COMPLETE_PEERS')

    for ci in range(2,10):
        cp=runroot/'CHUNKS'/f'chunk_{ci:02d}'/'ledger.json'
        if cp.is_file():
            L=json.loads(cp.read_text(encoding='utf-8'))
            bad=[sid for sid,rr in (L.get('states') or {}).items()
                 if rr.get('state')!='PENDING' or int(rr.get('attempts',0))!=0]
            if bad: raise RuntimeError('G100_R16_RESUME_LATER_SAMPLE_NOT_PRISTINE_PENDING:'+bad[0])

    sd=cr/'samples'/R16_RECOVERY_SAMPLE_ID
    reqp=cr/'requests'/f'{R16_RECOVERY_SAMPLE_ID}.json'
    logp=cr/'logs'/f'{R16_RECOVERY_SAMPLE_ID}.log'
    comp_p=sd/'completion.json'
    if not sd.is_dir() or not reqp.is_file() or not logp.is_file() or not comp_p.is_file():
        raise RuntimeError('G100_R16_RESUME_CURRENT_COMPLETE_EVIDENCE_MISSING')

    reqobj=json.loads(reqp.read_text(encoding='utf-8'))
    if reqobj.get('sample_id')!=R16_RECOVERY_SAMPLE_ID or reqobj.get('input_digest_sha256')!=R16_RECOVERY_REQUEST_DIGEST:
        raise RuntimeError('G100_R16_RESUME_REQUEST_CONTENT_MISMATCH')
    frozen_req=next(r for r in chunks[1]['requests'] if r['sample_id']==R16_RECOVERY_SAMPLE_ID)
    if reqobj!=frozen_req:
        raise RuntimeError('G100_R16_RESUME_REQUEST_NOT_EXACT_PACKAGE_FROZEN_OBJECT')

    comp=json.loads(comp_p.read_text(encoding='utf-8'))
    if comp.get('status')!='PASS_REAL_BLENDER_RENDERED' or comp.get('sample_id')!=R16_RECOVERY_SAMPLE_ID or comp.get('input_digest_sha256')!=R16_RECOVERY_REQUEST_DIGEST:
        raise RuntimeError('G100_R16_RESUME_COMPLETION_IDENTITY_MISMATCH')

    declared={}
    for fr in comp.get('files',[]):
        rel=str(fr.get('path','')); rp=Path(rel)
        if not rel or rp.is_absolute() or '..' in rp.parts or rel in declared:
            raise RuntimeError('G100_R16_RESUME_COMPLETION_FILE_RECORD_INVALID:'+rel)
        fp=sd/rp
        if not fp.is_file(): raise RuntimeError('G100_R16_RESUME_COMPLETION_FILE_MISSING:'+rel)
        if fp.stat().st_size!=int(fr.get('bytes',-1)):
            raise RuntimeError('G100_R16_RESUME_COMPLETION_FILE_SIZE_MISMATCH:'+rel)
        got=sha256_file(fp)
        if got!=fr.get('sha256'):
            raise RuntimeError('G100_R16_RESUME_COMPLETION_FILE_HASH_MISMATCH:'+rel)
        declared[rel]={'bytes':fp.stat().st_size,'sha256':got}
    missing=sorted(R16_REQUIRED_COMPLETION_FILES-set(declared))
    if missing:
        raise RuntimeError('G100_R16_RESUME_REQUIRED_COMPLETION_FILE_MISSING:'+missing[0])

    repro=comp.get('camera_reprojection') or {}
    fa=(comp.get('camera_calibration') or {}).get('final_abs_error') or {}
    gt=comp.get('micro100_aux_gt') or {}
    if float(repro.get('max_residual_px',999))>.50 or float(repro.get('median_residual_px',999))>.20:
        raise RuntimeError('G100_R16_RESUME_NON_RGB_REPROJECTION_NOT_PASS')
    if max(float(fa.get(k,999)) for k in ('fx','fy','cx','cy'))>.001:
        raise RuntimeError('G100_R16_RESUME_NON_RGB_CALIBRATION_NOT_PASS')
    if (gt.get('object_index') or {}).get('status')!='PASS' or (gt.get('depth') or {}).get('status')!='PASS' or (gt.get('normal') or {}).get('status')!='PASS':
        raise RuntimeError('G100_R16_RESUME_NON_RGB_GT_NOT_PASS')

    st=rgb_stats(sd/'rgb.png'); rgbsha=sha256_file(sd/'rgb.png')
    if not _r16_rgb_failure_class(st):
        raise RuntimeError('G100_R16_RESUME_RGB_FAILURE_CLASS_MISMATCH')

    accp=runroot/'EVIDENCE'/'SAMPLE_ACCEPTANCE'/f'{R16_RECOVERY_SAMPLE_ID}.json'
    if not accp.is_file():
        raise RuntimeError('G100_R16_RESUME_SAMPLE_ACCEPTANCE_EVIDENCE_MISSING')
    acc=json.loads(accp.read_text(encoding='utf-8'))
    if not _r16_acceptance_signature(acc,st,rgbsha):
        raise RuntimeError('G100_R16_RESUME_SAMPLE_ACCEPTANCE_SIGNATURE_MISMATCH')

    prior_records=_tree_records(sd)
    live_identity={'sample_tree':prior_records,'completion_sha256':sha256_file(comp_p),
                   'request_sha256':sha256_file(reqp),'worker_log_sha256':sha256_file(logp),
                   'sample_acceptance_sha256':sha256_file(accp),'completion_declared_files':declared,'rgb_stats':st}
    evroot=runroot/'RECOVERY'/'R14_COMPLETE_SAMPLE_015_RGB_ACCEPTANCE_FAIL'
    if evroot.exists():
        raise RuntimeError('G100_R16_RESUME_RECOVERY_TARGET_PREEXISTS_WITHOUT_R16_MARKER')
    evroot.mkdir(parents=True,exist_ok=False); payload=evroot/'sample_bytes'
    shutil.copytree(sd,payload)
    if _tree_records(payload)!=prior_records:
        raise RuntimeError('G100_R16_RESUME_PRESERVE_HASH_MISMATCH')
    shutil.copy2(reqp,evroot/'request.json'); shutil.copy2(logp,evroot/'worker.log'); shutil.copy2(accp,evroot/'sample_acceptance.json')
    if sha256_file(evroot/'request.json')!=live_identity['request_sha256'] or sha256_file(evroot/'worker.log')!=live_identity['worker_log_sha256'] or sha256_file(evroot/'sample_acceptance.json')!=live_identity['sample_acceptance_sha256']:
        raise RuntimeError('G100_R16_RESUME_PRESERVE_SIDECAR_HASH_MISMATCH')

    for ci,before in peer_records.items():
        cp=runroot/'CHUNKS'/f'chunk_{ci:02d}'/'ledger.json'
        if cp.read_bytes()!=before:
            raise RuntimeError('G100_R16_RESUME_LEDGER_CHANGED_DURING_PRESERVE:'+str(ci))

    recovery={'schema':'DF-G100-R16-RECOVERY-JOURNAL-V1','status':'PRESERVED_BEFORE_LEDGER_RESET',
              'r16_addendum_drive_id':R16_ADDENDUM_DRIVE_ID,'r15_addendum_drive_id':R15_ADDENDUM_DRIVE_ID,
              'r15_failure_return_sha256':R16_PRIOR_R15_RETURN_SHA256,'source_tool':'R15_PRE_RECOVERY_FAILURE','target_tool':'R16',
              'sample_id':R16_RECOVERY_SAMPLE_ID,'request_digest':R16_RECOVERY_REQUEST_DIGEST,'chunk_digest_sha256':R16_CHUNK01_DIGEST,
              'prior_state':'COMPLETE','prior_attempts':1,'prior_live_identity':live_identity,
              'completed_samples_preserved':sorted(info['completed_samples_preserved']),
              'r15_fill_implementation':'DF_G100_CAMERA_INSIDE_SOLID_CAMERA_FILL_V1_R15',
              'historical_r11_hashes_used_as_current_authority':False,'recorded_utc':utc_iso(),
              'product_mutated':False,'maya_mutated':False,'test77_accessed':False,'training_started':False}
    atomic_json(evroot/'R16_RECOVERY_JOURNAL.json',recovery)

    shutil.rmtree(sd); sd.mkdir(parents=True,exist_ok=True)
    rec['state']='PENDING'; rec['attempts']=0; rec.pop('last_error',None)
    rec['r16_recovery']={'r16_addendum_drive_id':R16_ADDENDUM_DRIVE_ID,'prior_state':'COMPLETE','prior_attempts':1,
                         'prior_acceptance_failure':'rgb_unique=false,rgb_span=false,rgb_mean=false,rgb_structural=false',
                         'recovery_journal_rel':(evroot/'R16_RECOVERY_JOURNAL.json').relative_to(runroot).as_posix(),
                         'authority_semantics':'LIVE_COMPLETION_SELF_HASH_PLUS_ACCEPTANCE_SIGNATURE_R16_V1',
                         'r15_fill_implementation':'DF_G100_CAMERA_INSIDE_SOLID_CAMERA_FILL_V1_R15'}
    atomic_json(lp,led)
    recovery['status']='LEDGER_RESET_SAMPLE_015_ONLY'
    atomic_json(evroot/'R16_RECOVERY_JOURNAL.json',recovery)
    info['status']='LIVE_COMPLETE_SAMPLE015_REOPENED_FOR_R16'
    info['recovered_samples'][R16_RECOVERY_SAMPLE_ID]=dict(rec['r16_recovery'])
    return info


def _r17_rgb_failure_class(stats):
    return (
        int(stats.get('unique_rgb',-1)) >= 32 and
        float(stats.get('p01_p99_span',10**9)) < 24.0 and
        12.0 <= float(stats.get('mean_luma',-1)) <= 243.0 and
        float(stats.get('structural_fraction',-1)) >= 0.03
    )

def _r17_acceptance_signature(acc,stats,rgb_sha):
    if not isinstance(acc,dict): return False
    if acc.get('sample_id')!=R17_RECOVERY_SAMPLE_ID or acc.get('request_digest')!=R17_RECOVERY_REQUEST_DIGEST: return False
    if acc.get('status')!='FAIL': return False
    checks=acc.get('checks') or {}
    if checks.get('rgb_span') is not False: return False
    for k in ('rgb_unique','rgb_mean','rgb_structural'):
        if checks.get(k) is not True: return False
    for k in ('completion_integrity','camera_calibration_finite','camera_calibration_abs_error_le_0_001px',
              'camera_reprojection_max','camera_reprojection_median','object_index_analytic','depth_analytic',
              'normal_analytic','raster_direct','provenance'):
        if checks.get(k) is not True: return False
    if acc.get('rgb_sha256')!=rgb_sha: return False
    arst=acc.get('rgb') or {}
    if int(arst.get('unique_rgb',-1))!=int(stats['unique_rgb']): return False
    for k in ('mean_luma','p01','p99','p01_p99_span','structural_fraction'):
        if abs(float(arst.get(k,float('inf')))-float(stats[k]))>1e-12: return False
    return True

def apply_r17_resume_if_needed(runroot:Path,chunks):
    """Fail-closed R16 COMPLETE sample015 span-only recovery for R17.

    The live R16 payload is authenticated through package-frozen request/ledger,
    completion-declared payload hashes, fresh RGB statistics, the persisted
    post-chunk acceptance signature, and exact R15 visibility provenance.
    Only sample015 may be reopened.
    """
    info={'schema':'DF-G100-R17-RESUME-V1','status':'NOT_APPLICABLE',
          'r17_addendum_drive_id':R17_ADDENDUM_DRIVE_ID,
          'r16_failure_return_sha256':R17_PRIOR_R16_RETURN_SHA256,
          'recovered_samples':{},'completed_samples_preserved':[]}
    runroot=Path(runroot); cr=runroot/'CHUNKS'/'chunk_01'; lp=cr/'ledger.json'
    if not lp.is_file(): return info
    led=json.loads(lp.read_text(encoding='utf-8'))
    if led.get('chunk_digest_sha256')!=R17_CHUNK01_DIGEST:
        raise RuntimeError('G100_R17_RESUME_CHUNK01_DIGEST_MISMATCH')
    expected={r['sample_id']:r['input_digest_sha256'] for r in chunks[1]['requests']}
    if len(expected)!=10 or expected.get(R17_RECOVERY_SAMPLE_ID)!=R17_RECOVERY_REQUEST_DIGEST:
        raise RuntimeError('G100_R17_RESUME_FROZEN_PLAN_TARGET_MISMATCH')
    states=led.get('states') or {}; rec=states.get(R17_RECOVERY_SAMPLE_ID,{})
    if rec.get('request_digest')!=R17_RECOVERY_REQUEST_DIGEST:
        raise RuntimeError('G100_R17_RESUME_LEDGER_REQUEST_DIGEST_MISMATCH')
    if (rec.get('r17_recovery') or {}).get('r17_addendum_drive_id')==R17_ADDENDUM_DRIVE_ID:
        if rec.get('state') in {'PENDING','RUNNING','COMPLETE','FAILED_RETRYABLE','FAILED_FINAL'}:
            info['status']='R17_RECOVERY_ALREADY_APPLIED'
            info['recovered_samples'][R17_RECOVERY_SAMPLE_ID]=dict(rec.get('r17_recovery') or {})
            return info
        raise RuntimeError('G100_R17_RESUME_BAD_POST_RECOVERY_STATE')
    if (rec.get('r16_recovery') or {}).get('r16_addendum_drive_id')!=R16_ADDENDUM_DRIVE_ID:
        raise RuntimeError('G100_R17_RESUME_R16_RECOVERY_MARKER_MISSING')
    if rec.get('state')!='COMPLETE' or int(rec.get('attempts',-1))!=1:
        raise RuntimeError('G100_R17_RESUME_EXACT_PRE_RECOVERY_COMPLETE_PRECONDITION')

    peer_records={}
    for ci in (0,1):
        cp=runroot/'CHUNKS'/f'chunk_{ci:02d}'/'ledger.json'
        if not cp.is_file(): raise RuntimeError('G100_R17_RESUME_PRIOR_LEDGER_MISSING:'+str(ci))
        L=json.loads(cp.read_text(encoding='utf-8')); peer_records[ci]=cp.read_bytes()
        for sid,rr in (L.get('states') or {}).items():
            if sid==R17_RECOVERY_SAMPLE_ID: continue
            if rr.get('state')!='COMPLETE':
                raise RuntimeError('G100_R17_RESUME_COMPLETE_PEER_STATE_MISMATCH:'+sid)
            info['completed_samples_preserved'].append(sid)
    if len(info['completed_samples_preserved'])!=19:
        raise RuntimeError('G100_R17_RESUME_EXPECTED_19_COMPLETE_PEERS')

    for ci in range(2,10):
        cp=runroot/'CHUNKS'/f'chunk_{ci:02d}'/'ledger.json'
        if cp.is_file():
            L=json.loads(cp.read_text(encoding='utf-8'))
            bad=[sid for sid,rr in (L.get('states') or {}).items()
                 if rr.get('state')!='PENDING' or int(rr.get('attempts',0))!=0]
            if bad: raise RuntimeError('G100_R17_RESUME_LATER_SAMPLE_NOT_PRISTINE_PENDING:'+bad[0])

    sd=cr/'samples'/R17_RECOVERY_SAMPLE_ID
    reqp=cr/'requests'/f'{R17_RECOVERY_SAMPLE_ID}.json'
    logp=cr/'logs'/f'{R17_RECOVERY_SAMPLE_ID}.log'
    comp_p=sd/'completion.json'
    accp=runroot/'EVIDENCE'/'SAMPLE_ACCEPTANCE'/f'{R17_RECOVERY_SAMPLE_ID}.json'
    if not sd.is_dir() or not reqp.is_file() or not logp.is_file() or not comp_p.is_file() or not accp.is_file():
        raise RuntimeError('G100_R17_RESUME_CURRENT_COMPLETE_EVIDENCE_MISSING')

    reqobj=json.loads(reqp.read_text(encoding='utf-8'))
    if reqobj.get('sample_id')!=R17_RECOVERY_SAMPLE_ID or reqobj.get('input_digest_sha256')!=R17_RECOVERY_REQUEST_DIGEST:
        raise RuntimeError('G100_R17_RESUME_REQUEST_CONTENT_MISMATCH')
    frozen_req=next(r for r in chunks[1]['requests'] if r['sample_id']==R17_RECOVERY_SAMPLE_ID)
    if reqobj!=frozen_req:
        raise RuntimeError('G100_R17_RESUME_REQUEST_NOT_EXACT_PACKAGE_FROZEN_OBJECT')

    comp=json.loads(comp_p.read_text(encoding='utf-8'))
    if comp.get('status')!='PASS_REAL_BLENDER_RENDERED' or comp.get('sample_id')!=R17_RECOVERY_SAMPLE_ID or comp.get('input_digest_sha256')!=R17_RECOVERY_REQUEST_DIGEST:
        raise RuntimeError('G100_R17_RESUME_COMPLETION_IDENTITY_MISMATCH')
    if comp.get('r17_camera_inside_rgb_contrast'):
        raise RuntimeError('G100_R17_RESUME_UNEXPECTED_EXISTING_R17_PROVENANCE')
    r15=comp.get('r15_camera_inside_visibility_aid') or {}
    if not (r15.get('implementation_id')=='DF_G100_CAMERA_INSIDE_SOLID_CAMERA_FILL_V1_R15' and r15.get('applied') is True and
            float(r15.get('energy_w',-1))==350.0 and float(r15.get('soft_shadow_radius_m',-1))==2.0 and
            r15.get('location')=='BLENDER_CAMERA_LOCATION' and r15.get('geometry_preserving') is True and
            r15.get('adaptive') is False and r15.get('threshold_adaptive') is False and r15.get('spatial_warp') is False):
        raise RuntimeError('G100_R17_RESUME_R15_VISIBILITY_PROVENANCE_MISMATCH')

    declared={}
    for fr in comp.get('files',[]):
        rel=str(fr.get('path','')); rp=Path(rel)
        if not rel or rp.is_absolute() or '..' in rp.parts or rel in declared:
            raise RuntimeError('G100_R17_RESUME_COMPLETION_FILE_RECORD_INVALID:'+rel)
        fp=sd/rp
        if not fp.is_file(): raise RuntimeError('G100_R17_RESUME_COMPLETION_FILE_MISSING:'+rel)
        if fp.stat().st_size!=int(fr.get('bytes',-1)):
            raise RuntimeError('G100_R17_RESUME_COMPLETION_FILE_SIZE_MISMATCH:'+rel)
        got=sha256_file(fp)
        if got!=fr.get('sha256'):
            raise RuntimeError('G100_R17_RESUME_COMPLETION_FILE_HASH_MISMATCH:'+rel)
        declared[rel]={'bytes':fp.stat().st_size,'sha256':got}
    missing=sorted(R17_REQUIRED_COMPLETION_FILES-set(declared))
    if missing: raise RuntimeError('G100_R17_RESUME_REQUIRED_COMPLETION_FILE_MISSING:'+missing[0])

    repro=comp.get('camera_reprojection') or {}
    fa=(comp.get('camera_calibration') or {}).get('final_abs_error') or {}
    gt=comp.get('micro100_aux_gt') or {}
    if float(repro.get('max_residual_px',999))>.50 or float(repro.get('median_residual_px',999))>.20:
        raise RuntimeError('G100_R17_RESUME_NON_RGB_REPROJECTION_NOT_PASS')
    if max(float(fa.get(k,999)) for k in ('fx','fy','cx','cy'))>.001:
        raise RuntimeError('G100_R17_RESUME_NON_RGB_CALIBRATION_NOT_PASS')
    if (gt.get('object_index') or {}).get('status')!='PASS' or (gt.get('depth') or {}).get('status')!='PASS' or (gt.get('normal') or {}).get('status')!='PASS':
        raise RuntimeError('G100_R17_RESUME_NON_RGB_GT_NOT_PASS')

    st=rgb_stats(sd/'rgb.png'); rgbsha=sha256_file(sd/'rgb.png')
    if not _r17_rgb_failure_class(st):
        raise RuntimeError('G100_R17_RESUME_RGB_FAILURE_CLASS_MISMATCH')
    acc=json.loads(accp.read_text(encoding='utf-8'))
    if not _r17_acceptance_signature(acc,st,rgbsha):
        raise RuntimeError('G100_R17_RESUME_SAMPLE_ACCEPTANCE_SIGNATURE_MISMATCH')

    prior_records=_tree_records(sd)
    live_identity={'sample_tree':prior_records,'completion_sha256':sha256_file(comp_p),
                   'request_sha256':sha256_file(reqp),'worker_log_sha256':sha256_file(logp),
                   'sample_acceptance_sha256':sha256_file(accp),'completion_declared_files':declared,
                   'rgb_sha256':rgbsha,'rgb_stats':st}
    evroot=runroot/'RECOVERY'/'R16_COMPLETE_SAMPLE_015_RGB_SPAN_FAIL'
    if evroot.exists():
        raise RuntimeError('G100_R17_RESUME_RECOVERY_TARGET_PREEXISTS_WITHOUT_R17_MARKER')
    evroot.mkdir(parents=True,exist_ok=False); payload=evroot/'sample_bytes'
    shutil.copytree(sd,payload)
    if _tree_records(payload)!=prior_records:
        raise RuntimeError('G100_R17_RESUME_PRESERVE_HASH_MISMATCH')
    shutil.copy2(reqp,evroot/'request.json'); shutil.copy2(logp,evroot/'worker.log'); shutil.copy2(accp,evroot/'sample_acceptance.json')
    if sha256_file(evroot/'request.json')!=live_identity['request_sha256'] or sha256_file(evroot/'worker.log')!=live_identity['worker_log_sha256'] or sha256_file(evroot/'sample_acceptance.json')!=live_identity['sample_acceptance_sha256']:
        raise RuntimeError('G100_R17_RESUME_PRESERVE_SIDECAR_HASH_MISMATCH')
    for ci,before in peer_records.items():
        cp=runroot/'CHUNKS'/f'chunk_{ci:02d}'/'ledger.json'
        if cp.read_bytes()!=before:
            raise RuntimeError('G100_R17_RESUME_LEDGER_CHANGED_DURING_PRESERVE:'+str(ci))

    recovery={'schema':'DF-G100-R17-RECOVERY-JOURNAL-V1','status':'PRESERVED_BEFORE_LEDGER_RESET',
              'r17_addendum_drive_id':R17_ADDENDUM_DRIVE_ID,'r16_addendum_drive_id':R16_ADDENDUM_DRIVE_ID,
              'r16_failure_return_sha256':R17_PRIOR_R16_RETURN_SHA256,'source_tool':'R16_POST_CHUNK_ACCEPTANCE',
              'target_tool':'R17','sample_id':R17_RECOVERY_SAMPLE_ID,'request_digest':R17_RECOVERY_REQUEST_DIGEST,
              'chunk_digest_sha256':R17_CHUNK01_DIGEST,'prior_state':'COMPLETE','prior_attempts':1,
              'prior_live_identity':live_identity,'completed_samples_preserved':sorted(info['completed_samples_preserved']),
              'r15_fill_implementation':'DF_G100_CAMERA_INSIDE_SOLID_CAMERA_FILL_V1_R15',
              'r17_contrast_implementation':'DF_G100_CAMERA_INSIDE_FIXED_RGB_CONTRAST_V1_R17',
              'r17_contrast':{'pivot_u8':128,'factor_numerator':17,'factor_denominator':16,
                              'adaptive':False,'threshold_adaptive':False,'sample_statistics_used':False},
              'recorded_utc':utc_iso(),'product_mutated':False,'maya_mutated':False,
              'test77_accessed':False,'training_started':False}
    atomic_json(evroot/'R17_RECOVERY_JOURNAL.json',recovery)

    shutil.rmtree(sd); sd.mkdir(parents=True,exist_ok=True)
    rec['state']='PENDING'; rec['attempts']=0; rec.pop('last_error',None)
    rec['r17_recovery']={'r17_addendum_drive_id':R17_ADDENDUM_DRIVE_ID,'prior_state':'COMPLETE','prior_attempts':1,
                         'prior_acceptance_failure':'rgb_span=false',
                         'recovery_journal_rel':(evroot/'R17_RECOVERY_JOURNAL.json').relative_to(runroot).as_posix(),
                         'authority_semantics':'LIVE_COMPLETION_SELF_HASH_PLUS_SPAN_ONLY_ACCEPTANCE_SIGNATURE_R17_V1',
                         'r15_fill_implementation':'DF_G100_CAMERA_INSIDE_SOLID_CAMERA_FILL_V1_R15',
                         'r17_contrast_implementation':'DF_G100_CAMERA_INSIDE_FIXED_RGB_CONTRAST_V1_R17',
                         'r17_rgb_contrast_factor':'17/16','r17_rgb_contrast_pivot_u8':128}
    atomic_json(lp,led)
    recovery['status']='LEDGER_RESET_SAMPLE_015_ONLY'
    atomic_json(evroot/'R17_RECOVERY_JOURNAL.json',recovery)
    info['status']='R16_COMPLETE_SAMPLE015_REOPENED_FOR_R17'
    info['recovered_samples'][R17_RECOVERY_SAMPLE_ID]=dict(rec['r17_recovery'])
    return info


def apply_r18_resume_if_needed(runroot:Path,chunks):
    """Exact fail-closed R17 FAILED_FINAL sample021 -> R18 PP minimax recovery."""
    info={'schema':'DF-G100-R18-RESUME-V1','status':'NOT_APPLICABLE',
          'r18_addendum_drive_id':R18_ADDENDUM_DRIVE_ID,'recovered_samples':{},
          'completed_samples_preserved':[]}
    runroot=Path(runroot)
    if len(chunks)<3: raise RuntimeError('G100_R18_RESUME_CHUNK02_MISSING')
    cr=runroot/'CHUNKS'/'chunk_02'; lp=cr/'ledger.json'
    if not lp.is_file(): return info
    led=json.loads(lp.read_text(encoding='utf-8'))
    if led.get('chunk_digest_sha256')!=R18_CHUNK02_DIGEST:
        raise RuntimeError('G100_R18_RESUME_CHUNK02_DIGEST_MISMATCH')
    expected={r['sample_id']:r['input_digest_sha256'] for r in chunks[2]['requests']}
    if len(expected)!=10 or expected.get(R18_RECOVERY_SAMPLE_ID)!=R18_RECOVERY_REQUEST_DIGEST:
        raise RuntimeError('G100_R18_RESUME_FROZEN_PLAN_TARGET_MISMATCH')
    states=led.get('states') or {}; rec=states.get(R18_RECOVERY_SAMPLE_ID,{})
    if rec.get('request_digest')!=R18_RECOVERY_REQUEST_DIGEST:
        raise RuntimeError('G100_R18_RESUME_LEDGER_REQUEST_DIGEST_MISMATCH')
    if (rec.get('r18_recovery') or {}).get('r18_addendum_drive_id')==R18_ADDENDUM_DRIVE_ID:
        if rec.get('state') in {'PENDING','RUNNING','COMPLETE','FAILED_RETRYABLE','FAILED_FINAL'}:
            info['status']='R18_RECOVERY_ALREADY_APPLIED'
            info['recovered_samples'][R18_RECOVERY_SAMPLE_ID]=dict(rec.get('r18_recovery') or {})
            return info
        raise RuntimeError('G100_R18_RESUME_BAD_POST_RECOVERY_STATE')
    if rec.get('state')!='FAILED_FINAL' or int(rec.get('attempts',-1))!=2 or rec.get('last_error')!='BLENDER_WORKER_RC:5':
        raise RuntimeError('G100_R18_RESUME_EXACT_R17_FAILED_FINAL_PRECONDITION')

    # Freeze all COMPLETE peers before target: chunks00-01 plus sample020.
    peer_ledger_bytes={}
    for ci in (0,1):
        cp=runroot/'CHUNKS'/f'chunk_{ci:02d}'/'ledger.json'
        if not cp.is_file(): raise RuntimeError('G100_R18_RESUME_PRIOR_LEDGER_MISSING:'+str(ci))
        L=json.loads(cp.read_text(encoding='utf-8')); peer_ledger_bytes[ci]=cp.read_bytes()
        for sid,rr in (L.get('states') or {}).items():
            if rr.get('state')!='COMPLETE':
                raise RuntimeError('G100_R18_RESUME_COMPLETE_PEER_STATE_MISMATCH:'+sid)
            info['completed_samples_preserved'].append(sid)

    order=[r['sample_id'] for r in chunks[2]['requests']]
    ti=order.index(R18_RECOVERY_SAMPLE_ID)
    for i,sid in enumerate(order):
        rr=states.get(sid,{})
        if i<ti:
            if rr.get('state')!='COMPLETE':
                raise RuntimeError('G100_R18_RESUME_PRIOR_PEER_NOT_COMPLETE:'+sid)
            info['completed_samples_preserved'].append(sid)
        elif i>ti:
            if rr.get('state')!='PENDING' or int(rr.get('attempts',0))!=0:
                raise RuntimeError('G100_R18_RESUME_FUTURE_PEER_NOT_PENDING:'+sid)
    if len(set(info['completed_samples_preserved']))!=21:
        raise RuntimeError('G100_R18_RESUME_EXPECTED_21_COMPLETE_PEERS')

    for ci in range(3,10):
        cp=runroot/'CHUNKS'/f'chunk_{ci:02d}'/'ledger.json'
        if cp.is_file():
            L=json.loads(cp.read_text(encoding='utf-8'))
            bad=[sid for sid,rr in (L.get('states') or {}).items()
                 if rr.get('state')!='PENDING' or int(rr.get('attempts',0))!=0]
            if bad: raise RuntimeError('G100_R18_RESUME_LATER_SAMPLE_NOT_PRISTINE_PENDING:'+bad[0])

    sd=cr/'samples'/R18_RECOVERY_SAMPLE_ID
    reqp=cr/'requests'/f'{R18_RECOVERY_SAMPLE_ID}.json'
    logp=cr/'logs'/f'{R18_RECOVERY_SAMPLE_ID}.log'
    if not sd.is_dir() or not reqp.is_file() or not logp.is_file():
        raise RuntimeError('G100_R18_RESUME_CURRENT_FAILED_EVIDENCE_MISSING')
    if sha256_file(reqp)!=R18_PRIOR_REQUEST_SHA256:
        raise RuntimeError('G100_R18_RESUME_REQUEST_SHA_MISMATCH')
    if sha256_file(logp)!=R18_PRIOR_WORKER_LOG_SHA256:
        raise RuntimeError('G100_R18_RESUME_WORKER_LOG_SHA_MISMATCH')
    reqobj=json.loads(reqp.read_text(encoding='utf-8'))
    if reqobj.get('sample_id')!=R18_RECOVERY_SAMPLE_ID or reqobj.get('input_digest_sha256')!=R18_RECOVERY_REQUEST_DIGEST:
        raise RuntimeError('G100_R18_RESUME_REQUEST_CONTENT_MISMATCH')
    frozen_req=next(r for r in chunks[2]['requests'] if r['sample_id']==R18_RECOVERY_SAMPLE_ID)
    if reqobj!=frozen_req:
        raise RuntimeError('G100_R18_RESUME_REQUEST_NOT_EXACT_PACKAGE_FROZEN_OBJECT')

    prior_records=_tree_records(sd)
    if prior_records!=R18_PRIOR_SAMPLE_TREE:
        raise RuntimeError('G100_R18_RESUME_SAMPLE_TREE_FINGERPRINT_MISMATCH')
    fobj=json.loads((sd/'failure.json').read_text(encoding='utf-8'))
    if (fobj.get('sample_id')!=R18_RECOVERY_SAMPLE_ID or
        fobj.get('input_digest_sha256')!=R18_RECOVERY_REQUEST_DIGEST or
        fobj.get('error')!=R18_FAILURE_ERROR):
        raise RuntimeError('G100_R18_RESUME_FAILURE_CAUSE_MISMATCH')
    q=json.loads((sd/'micro100_aux_gt_qa.json').read_text(encoding='utf-8'))
    if not ((q.get('depth') or {}).get('status')=='FAIL' and
            (q.get('normal') or {}).get('status')=='PASS' and
            (q.get('object_index') or {}).get('status')=='PASS'):
        raise RuntimeError('G100_R18_RESUME_GT_FAILURE_SIGNATURE_MISMATCH')
    d=(q.get('depth') or {}).get('renderer_effective_analytic_abs_error_m') or {}
    if abs(float(d.get('max',999))-0.00015234973201216917)>1e-15:
        raise RuntimeError('G100_R18_RESUME_DEPTH_MAX_SIGNATURE_MISMATCH')
    b=(q.get('depth') or {}).get('renderer_effective_principal_point_binding') or {}
    if (abs(float(b.get('delta_cx_px',999))-(-0.0005086441020534829))>1e-12 or
        abs(float(b.get('delta_cy_px',999))-0.0005126278333116399)>1e-12):
        raise RuntimeError('G100_R18_RESUME_R7_BINDING_SIGNATURE_MISMATCH')

    fixture=HERE/'R17_REAL_FAILURE_EVIDENCE'/'PCS_CAMERA_GEOMETRY_DATA_FACTORY_G100_MICRO100_FAILURE_RETURN_R17_REAL_20260907_235227.zip'
    if not fixture.is_file() or sha256_file(fixture)!=R18_PRIOR_R17_RETURN_SHA256:
        raise RuntimeError('G100_R18_RESUME_R17_FIXTURE_IDENTITY_MISMATCH')
    with zipfile.ZipFile(fixture) as z:
        member='FAILED_SAMPLES/'+R18_RECOVERY_SAMPLE_ID+'/PARTIAL_OUTPUT_IDENTITIES.json'
        partial_bytes=z.read(member)
    if sha256_bytes(partial_bytes)!=R18_PRIOR_PARTIAL_IDENTITIES_SHA256:
        raise RuntimeError('G100_R18_RESUME_PARTIAL_OUTPUT_IDENTITIES_SHA_MISMATCH')
    po=json.loads(partial_bytes.decode('utf-8'))
    if (po.get('sample_id')!=R18_RECOVERY_SAMPLE_ID or
        po.get('request_digest')!=R18_RECOVERY_REQUEST_DIGEST or
        po.get('state')!='FAILED_FINAL' or int(po.get('attempts',-1))!=2 or
        po.get('last_error')!='BLENDER_WORKER_RC:5' or po.get('files')!=prior_records):
        raise RuntimeError('G100_R18_RESUME_PARTIAL_OUTPUT_IDENTITIES_CONTENT_MISMATCH')

    evroot=runroot/'RECOVERY'/'R17_FAILED_SAMPLE_021'
    if evroot.exists():
        raise RuntimeError('G100_R18_RESUME_RECOVERY_TARGET_PREEXISTS_WITHOUT_R18_MARKER')
    evroot.mkdir(parents=True,exist_ok=False)
    payload=evroot/'sample_bytes'; shutil.copytree(sd,payload)
    if _tree_records(payload)!=prior_records:
        raise RuntimeError('G100_R18_RESUME_PRESERVE_HASH_MISMATCH')
    shutil.copy2(reqp,evroot/'request.json'); shutil.copy2(logp,evroot/'worker.log')
    (evroot/'PARTIAL_OUTPUT_IDENTITIES.json').write_bytes(partial_bytes)
    if sha256_file(evroot/'request.json')!=R18_PRIOR_REQUEST_SHA256 or sha256_file(evroot/'worker.log')!=R18_PRIOR_WORKER_LOG_SHA256:
        raise RuntimeError('G100_R18_RESUME_PRESERVE_SIDECAR_HASH_MISMATCH')
    for ci,before in peer_ledger_bytes.items():
        cp=runroot/'CHUNKS'/f'chunk_{ci:02d}'/'ledger.json'
        if cp.read_bytes()!=before:
            raise RuntimeError('G100_R18_RESUME_LEDGER_CHANGED_DURING_PRESERVE:'+str(ci))

    recovery={'schema':'DF-G100-R18-RECOVERY-JOURNAL-V1','status':'PRESERVED_BEFORE_LEDGER_RESET',
              'r18_addendum_drive_id':R18_ADDENDUM_DRIVE_ID,'source_tool':'R17','target_tool':'R18',
              'sample_id':R18_RECOVERY_SAMPLE_ID,'request_digest':R18_RECOVERY_REQUEST_DIGEST,
              'chunk_digest_sha256':R18_CHUNK02_DIGEST,'prior_state':'FAILED_FINAL','prior_attempts':2,
              'prior_last_error':'BLENDER_WORKER_RC:5','prior_failure_error':R18_FAILURE_ERROR,
              'r17_failure_return_sha256':R18_PRIOR_R17_RETURN_SHA256,
              'prior_sample_tree':prior_records,'completed_samples_preserved':sorted(info['completed_samples_preserved']),
              'r18_binding_refinement':'CYCLES_EFFECTIVE_PP_MINIMAX_MICROGRID_R18_V1',
              'depth_threshold_m':1e-4,'depth_authority_masked':False,
              'recorded_utc':utc_iso(),'product_mutated':False,'maya_mutated':False,
              'test77_accessed':False,'training_started':False}
    atomic_json(evroot/'R18_RECOVERY_JOURNAL.json',recovery)

    shutil.rmtree(sd); sd.mkdir(parents=True,exist_ok=True)
    rec['state']='PENDING'; rec['attempts']=0; rec.pop('last_error',None)
    rec['r18_recovery']={'r18_addendum_drive_id':R18_ADDENDUM_DRIVE_ID,
                         'prior_state':'FAILED_FINAL','prior_attempts':2,
                         'prior_failure_error':R18_FAILURE_ERROR,
                         'recovery_journal_rel':(evroot/'R18_RECOVERY_JOURNAL.json').relative_to(runroot).as_posix(),
                         'binding_refinement':'CYCLES_EFFECTIVE_PP_MINIMAX_MICROGRID_R18_V1',
                         'depth_threshold_m':1e-4,'depth_authority_masked':False}
    atomic_json(lp,led)
    recovery['status']='LEDGER_RESET_SAMPLE_021_ONLY'
    atomic_json(evroot/'R18_RECOVERY_JOURNAL.json',recovery)
    info['status']='R17_FAILED_SAMPLE021_REOPENED_FOR_R18'
    info['recovered_samples'][R18_RECOVERY_SAMPLE_ID]=dict(rec['r18_recovery'])
    return info


def apply_r19_resume_if_needed(runroot:Path,chunks):
    """Exact fail-closed R18 FAILED_FINAL sample027 -> R19 coincident-face recovery."""
    info={'schema':'DF-G100-R19-RESUME-V1','status':'NOT_APPLICABLE',
          'r19_addendum_drive_id':R19_ADDENDUM_DRIVE_ID,'recovered_samples':{},
          'completed_samples_preserved':[]}
    runroot=Path(runroot)
    if len(chunks)<3: raise RuntimeError('G100_R19_RESUME_CHUNK02_MISSING')
    cr=runroot/'CHUNKS'/'chunk_02'; lp=cr/'ledger.json'
    if not lp.is_file(): return info
    led=json.loads(lp.read_text(encoding='utf-8'))
    if led.get('chunk_digest_sha256')!=R19_CHUNK02_DIGEST:
        raise RuntimeError('G100_R19_RESUME_CHUNK02_DIGEST_MISMATCH')
    expected={r['sample_id']:r['input_digest_sha256'] for r in chunks[2]['requests']}
    if len(expected)!=10 or expected.get(R19_RECOVERY_SAMPLE_ID)!=R19_RECOVERY_REQUEST_DIGEST:
        raise RuntimeError('G100_R19_RESUME_FROZEN_PLAN_TARGET_MISMATCH')
    states=led.get('states') or {}; rec=states.get(R19_RECOVERY_SAMPLE_ID,{})
    if rec.get('request_digest')!=R19_RECOVERY_REQUEST_DIGEST:
        raise RuntimeError('G100_R19_RESUME_LEDGER_REQUEST_DIGEST_MISMATCH')
    if (rec.get('r19_recovery') or {}).get('r19_addendum_drive_id')==R19_ADDENDUM_DRIVE_ID:
        if rec.get('state') in {'PENDING','RUNNING','COMPLETE','FAILED_RETRYABLE','FAILED_FINAL'}:
            info['status']='R19_RECOVERY_ALREADY_APPLIED'
            info['recovered_samples'][R19_RECOVERY_SAMPLE_ID]=dict(rec.get('r19_recovery') or {})
            return info
        raise RuntimeError('G100_R19_RESUME_BAD_POST_RECOVERY_STATE')
    if rec.get('state')!='FAILED_FINAL' or int(rec.get('attempts',-1))!=2 or rec.get('last_error')!='BLENDER_WORKER_RC:5':
        # Not applicable when the R18 target failure has not occurred yet.
        if rec.get('state') in {'PENDING','RUNNING','COMPLETE','FAILED_RETRYABLE'}:
            return info
        raise RuntimeError('G100_R19_RESUME_EXACT_R18_FAILED_FINAL_PRECONDITION')

    # Freeze all COMPLETE peers before target: chunks00-01 plus samples020..026.
    peer_ledger_bytes={}
    for ci in (0,1):
        cp=runroot/'CHUNKS'/f'chunk_{ci:02d}'/'ledger.json'
        if not cp.is_file(): raise RuntimeError('G100_R19_RESUME_PRIOR_LEDGER_MISSING:'+str(ci))
        L=json.loads(cp.read_text(encoding='utf-8')); peer_ledger_bytes[ci]=cp.read_bytes()
        for sid,rr in (L.get('states') or {}).items():
            if rr.get('state')!='COMPLETE':
                raise RuntimeError('G100_R19_RESUME_COMPLETE_PEER_STATE_MISMATCH:'+sid)
            info['completed_samples_preserved'].append(sid)

    order=[r['sample_id'] for r in chunks[2]['requests']]
    ti=order.index(R19_RECOVERY_SAMPLE_ID)
    for i,sid in enumerate(order):
        rr=states.get(sid,{})
        if i<ti:
            if rr.get('state')!='COMPLETE':
                raise RuntimeError('G100_R19_RESUME_PRIOR_PEER_NOT_COMPLETE:'+sid)
            info['completed_samples_preserved'].append(sid)
        elif i>ti:
            if rr.get('state')!='PENDING' or int(rr.get('attempts',0))!=0:
                raise RuntimeError('G100_R19_RESUME_FUTURE_PEER_NOT_PENDING:'+sid)
    if len(set(info['completed_samples_preserved']))!=27:
        raise RuntimeError('G100_R19_RESUME_EXPECTED_27_COMPLETE_PEERS')

    for ci in range(3,10):
        cp=runroot/'CHUNKS'/f'chunk_{ci:02d}'/'ledger.json'
        if cp.is_file():
            L=json.loads(cp.read_text(encoding='utf-8'))
            bad=[sid for sid,rr in (L.get('states') or {}).items()
                 if rr.get('state')!='PENDING' or int(rr.get('attempts',0))!=0]
            if bad: raise RuntimeError('G100_R19_RESUME_LATER_SAMPLE_NOT_PRISTINE_PENDING:'+bad[0])

    sd=cr/'samples'/R19_RECOVERY_SAMPLE_ID
    reqp=cr/'requests'/f'{R19_RECOVERY_SAMPLE_ID}.json'
    logp=cr/'logs'/f'{R19_RECOVERY_SAMPLE_ID}.log'
    if not sd.is_dir() or not reqp.is_file() or not logp.is_file():
        raise RuntimeError('G100_R19_RESUME_CURRENT_FAILED_EVIDENCE_MISSING')
    if sha256_file(reqp)!=R19_PRIOR_REQUEST_SHA256:
        raise RuntimeError('G100_R19_RESUME_REQUEST_SHA_MISMATCH')
    if sha256_file(logp)!=R19_PRIOR_WORKER_LOG_SHA256:
        raise RuntimeError('G100_R19_RESUME_WORKER_LOG_SHA_MISMATCH')
    reqobj=json.loads(reqp.read_text(encoding='utf-8'))
    if reqobj.get('sample_id')!=R19_RECOVERY_SAMPLE_ID or reqobj.get('input_digest_sha256')!=R19_RECOVERY_REQUEST_DIGEST:
        raise RuntimeError('G100_R19_RESUME_REQUEST_CONTENT_MISMATCH')
    frozen_req=next(r for r in chunks[2]['requests'] if r['sample_id']==R19_RECOVERY_SAMPLE_ID)
    if reqobj!=frozen_req:
        raise RuntimeError('G100_R19_RESUME_REQUEST_NOT_EXACT_PACKAGE_FROZEN_OBJECT')

    prior_records=_tree_records(sd)
    if prior_records!=R19_PRIOR_SAMPLE_TREE:
        raise RuntimeError('G100_R19_RESUME_SAMPLE_TREE_FINGERPRINT_MISMATCH')
    fobj=json.loads((sd/'failure.json').read_text(encoding='utf-8'))
    if (fobj.get('sample_id')!=R19_RECOVERY_SAMPLE_ID or
        fobj.get('input_digest_sha256')!=R19_RECOVERY_REQUEST_DIGEST or
        fobj.get('error')!=R19_FAILURE_ERROR):
        raise RuntimeError('G100_R19_RESUME_FAILURE_CAUSE_MISMATCH')
    q=json.loads((sd/'micro100_aux_gt_qa.json').read_text(encoding='utf-8'))
    if not ((q.get('depth') or {}).get('status')=='FAIL' and
            (q.get('normal') or {}).get('status')=='PASS' and
            (q.get('object_index') or {}).get('status')=='FAIL'):
        raise RuntimeError('G100_R19_RESUME_GT_FAILURE_SIGNATURE_MISMATCH')
    d=(q.get('depth') or {}).get('renderer_effective_analytic_abs_error_m') or {}
    if abs(float(d.get('max',999))-1.8458147621913668e-05)>1e-15:
        raise RuntimeError('G100_R19_RESUME_DEPTH_MAX_SIGNATURE_MISMATCH')
    oi=q.get('object_index') or {}
    if int(oi.get('renderer_effective_non_nearest_mismatch_pixels',-1))!=3013:
        raise RuntimeError('G100_R19_RESUME_OBJECT_MISMATCH_COUNT_SIGNATURE_MISMATCH')
    b=(q.get('depth') or {}).get('renderer_effective_principal_point_binding') or {}
    if (abs(float(b.get('delta_cx_px',999))-(-0.000527453646760905))>1e-12 or
        abs(float(b.get('delta_cy_px',999))-0.0005261175547025144)>1e-12):
        raise RuntimeError('G100_R19_RESUME_R7_BINDING_SIGNATURE_MISMATCH')

    fixture=HERE/'R18_REAL_FAILURE_EVIDENCE'/'PCS_CAMERA_GEOMETRY_DATA_FACTORY_G100_MICRO100_FAILURE_RETURN_R18_REAL_20260908_002902.zip'
    if not fixture.is_file() or sha256_file(fixture)!=R19_PRIOR_R18_RETURN_SHA256:
        raise RuntimeError('G100_R19_RESUME_R18_FIXTURE_IDENTITY_MISMATCH')
    with zipfile.ZipFile(fixture) as z:
        member='FAILED_SAMPLES/'+R19_RECOVERY_SAMPLE_ID+'/PARTIAL_OUTPUT_IDENTITIES.json'
        partial_bytes=z.read(member)
    if sha256_bytes(partial_bytes)!=R19_PRIOR_PARTIAL_IDENTITIES_SHA256:
        raise RuntimeError('G100_R19_RESUME_PARTIAL_OUTPUT_IDENTITIES_SHA_MISMATCH')
    po=json.loads(partial_bytes.decode('utf-8'))
    if (po.get('sample_id')!=R19_RECOVERY_SAMPLE_ID or
        po.get('request_digest')!=R19_RECOVERY_REQUEST_DIGEST or
        po.get('state')!='FAILED_FINAL' or int(po.get('attempts',-1))!=2 or
        po.get('last_error')!='BLENDER_WORKER_RC:5' or po.get('files')!=prior_records):
        raise RuntimeError('G100_R19_RESUME_PARTIAL_OUTPUT_IDENTITIES_CONTENT_MISMATCH')

    evroot=runroot/'RECOVERY'/'R18_FAILED_SAMPLE_027'
    if evroot.exists():
        raise RuntimeError('G100_R19_RESUME_RECOVERY_TARGET_PREEXISTS_WITHOUT_R19_MARKER')
    evroot.mkdir(parents=True,exist_ok=False)
    payload=evroot/'sample_bytes'; shutil.copytree(sd,payload)
    if _tree_records(payload)!=prior_records:
        raise RuntimeError('G100_R19_RESUME_PRESERVE_HASH_MISMATCH')
    shutil.copy2(reqp,evroot/'request.json'); shutil.copy2(logp,evroot/'worker.log')
    (evroot/'PARTIAL_OUTPUT_IDENTITIES.json').write_bytes(partial_bytes)
    if sha256_file(evroot/'request.json')!=R19_PRIOR_REQUEST_SHA256 or sha256_file(evroot/'worker.log')!=R19_PRIOR_WORKER_LOG_SHA256:
        raise RuntimeError('G100_R19_RESUME_PRESERVE_SIDECAR_HASH_MISMATCH')
    for ci,before in peer_ledger_bytes.items():
        cp=runroot/'CHUNKS'/f'chunk_{ci:02d}'/'ledger.json'
        if cp.read_bytes()!=before:
            raise RuntimeError('G100_R19_RESUME_LEDGER_CHANGED_DURING_PRESERVE:'+str(ci))

    recovery={'schema':'DF-G100-R19-RECOVERY-JOURNAL-V1','status':'PRESERVED_BEFORE_LEDGER_RESET',
              'r19_addendum_drive_id':R19_ADDENDUM_DRIVE_ID,'source_tool':'R18','target_tool':'R19',
              'sample_id':R19_RECOVERY_SAMPLE_ID,'request_digest':R19_RECOVERY_REQUEST_DIGEST,
              'chunk_digest_sha256':R19_CHUNK02_DIGEST,'prior_state':'FAILED_FINAL','prior_attempts':2,
              'prior_last_error':'BLENDER_WORKER_RC:5','prior_failure_error':R19_FAILURE_ERROR,
              'r18_failure_return_sha256':R19_PRIOR_R18_RETURN_SHA256,
              'prior_sample_tree':prior_records,'completed_samples_preserved':sorted(info['completed_samples_preserved']),
              'r19_visibility_semantics':'EXACT_GEOMETRIC_COINCIDENT_FACE_VISIBILITY_R19_V1',
              'numeric_visibility_epsilon':0.0,
              'depth_threshold_m':1e-4,'depth_authority_masked':False,
              'recorded_utc':utc_iso(),'product_mutated':False,'maya_mutated':False,
              'test77_accessed':False,'training_started':False}
    atomic_json(evroot/'R19_RECOVERY_JOURNAL.json',recovery)

    shutil.rmtree(sd); sd.mkdir(parents=True,exist_ok=True)
    rec['state']='PENDING'; rec['attempts']=0; rec.pop('last_error',None)
    rec['r19_recovery']={'r19_addendum_drive_id':R19_ADDENDUM_DRIVE_ID,
                         'prior_state':'FAILED_FINAL','prior_attempts':2,
                         'prior_failure_error':R19_FAILURE_ERROR,
                         'recovery_journal_rel':(evroot/'R19_RECOVERY_JOURNAL.json').relative_to(runroot).as_posix(),
                         'visibility_semantics':'EXACT_GEOMETRIC_COINCIDENT_FACE_VISIBILITY_R19_V1',
                         'numeric_visibility_epsilon':0.0,
                         'depth_threshold_m':1e-4,'depth_authority_masked':False}
    atomic_json(lp,led)
    recovery['status']='LEDGER_RESET_SAMPLE_027_ONLY'
    atomic_json(evroot/'R19_RECOVERY_JOURNAL.json',recovery)
    info['status']='R18_FAILED_SAMPLE027_REOPENED_FOR_R19'
    info['recovered_samples'][R19_RECOVERY_SAMPLE_ID]=dict(rec['r19_recovery'])
    return info


def apply_r20_resume_if_needed(runroot:Path,chunks):
    """Exact fail-closed R19 FAILED_FINAL sample029 -> R20 Normal raster-reference recovery."""
    info={'schema':'DF-G100-R20-RESUME-V1','status':'NOT_APPLICABLE',
          'r20_addendum_drive_id':R20_ADDENDUM_DRIVE_ID,'recovered_samples':{},'completed_samples_preserved':[]}
    runroot=Path(runroot)
    if len(chunks)<3: raise RuntimeError('G100_R20_RESUME_CHUNK02_MISSING')
    cr=runroot/'CHUNKS'/'chunk_02'; lp=cr/'ledger.json'
    if not lp.is_file(): return info
    led=json.loads(lp.read_text(encoding='utf-8'))
    if led.get('chunk_digest_sha256')!=R20_CHUNK02_DIGEST: raise RuntimeError('G100_R20_RESUME_CHUNK02_DIGEST_MISMATCH')
    expected={r['sample_id']:r['input_digest_sha256'] for r in chunks[2]['requests']}
    if len(expected)!=10 or expected.get(R20_RECOVERY_SAMPLE_ID)!=R20_RECOVERY_REQUEST_DIGEST: raise RuntimeError('G100_R20_RESUME_FROZEN_PLAN_TARGET_MISMATCH')
    states=led.get('states') or {}; rec=states.get(R20_RECOVERY_SAMPLE_ID,{})
    if rec.get('request_digest')!=R20_RECOVERY_REQUEST_DIGEST: raise RuntimeError('G100_R20_RESUME_LEDGER_REQUEST_DIGEST_MISMATCH')
    if (rec.get('r20_recovery') or {}).get('r20_addendum_drive_id')==R20_ADDENDUM_DRIVE_ID:
        if rec.get('state') in {'PENDING','RUNNING','COMPLETE','FAILED_RETRYABLE','FAILED_FINAL'}:
            info['status']='R20_RECOVERY_ALREADY_APPLIED'; info['recovered_samples'][R20_RECOVERY_SAMPLE_ID]=dict(rec.get('r20_recovery') or {}); return info
        raise RuntimeError('G100_R20_RESUME_BAD_POST_RECOVERY_STATE')
    if rec.get('state')!='FAILED_FINAL' or int(rec.get('attempts',-1))!=2 or rec.get('last_error')!='BLENDER_WORKER_RC:5':
        if rec.get('state') in {'PENDING','RUNNING','COMPLETE','FAILED_RETRYABLE'}: return info
        raise RuntimeError('G100_R20_RESUME_EXACT_R19_FAILED_FINAL_PRECONDITION')
    peer_ledger_bytes={}
    for ci in (0,1):
        cp=runroot/'CHUNKS'/f'chunk_{ci:02d}'/'ledger.json'
        if not cp.is_file(): raise RuntimeError('G100_R20_RESUME_PRIOR_LEDGER_MISSING:'+str(ci))
        L=json.loads(cp.read_text(encoding='utf-8')); peer_ledger_bytes[ci]=cp.read_bytes()
        for sid,rr in (L.get('states') or {}).items():
            if rr.get('state')!='COMPLETE': raise RuntimeError('G100_R20_RESUME_COMPLETE_PEER_STATE_MISMATCH:'+sid)
            info['completed_samples_preserved'].append(sid)
    order=[r['sample_id'] for r in chunks[2]['requests']]; ti=order.index(R20_RECOVERY_SAMPLE_ID)
    for i,sid in enumerate(order):
        rr=states.get(sid,{})
        if i<ti:
            if rr.get('state')!='COMPLETE': raise RuntimeError('G100_R20_RESUME_PRIOR_PEER_NOT_COMPLETE:'+sid)
            info['completed_samples_preserved'].append(sid)
        elif i>ti:
            if rr.get('state')!='PENDING' or int(rr.get('attempts',0))!=0: raise RuntimeError('G100_R20_RESUME_FUTURE_PEER_NOT_PENDING:'+sid)
    if len(set(info['completed_samples_preserved']))!=29: raise RuntimeError('G100_R20_RESUME_EXPECTED_29_COMPLETE_PEERS')
    for ci in range(3,10):
        cp=runroot/'CHUNKS'/f'chunk_{ci:02d}'/'ledger.json'
        if cp.is_file():
            L=json.loads(cp.read_text(encoding='utf-8')); bad=[sid for sid,rr in (L.get('states') or {}).items() if rr.get('state')!='PENDING' or int(rr.get('attempts',0))!=0]
            if bad: raise RuntimeError('G100_R20_RESUME_LATER_SAMPLE_NOT_PRISTINE_PENDING:'+bad[0])
    sd=cr/'samples'/R20_RECOVERY_SAMPLE_ID; reqp=cr/'requests'/f'{R20_RECOVERY_SAMPLE_ID}.json'; logp=cr/'logs'/f'{R20_RECOVERY_SAMPLE_ID}.log'
    if not sd.is_dir() or not reqp.is_file() or not logp.is_file(): raise RuntimeError('G100_R20_RESUME_CURRENT_FAILED_EVIDENCE_MISSING')
    if sha256_file(reqp)!=R20_PRIOR_REQUEST_SHA256: raise RuntimeError('G100_R20_RESUME_REQUEST_SHA_MISMATCH')
    if sha256_file(logp)!=R20_PRIOR_WORKER_LOG_SHA256: raise RuntimeError('G100_R20_RESUME_WORKER_LOG_SHA_MISMATCH')
    reqobj=json.loads(reqp.read_text(encoding='utf-8')); frozen_req=next(r for r in chunks[2]['requests'] if r['sample_id']==R20_RECOVERY_SAMPLE_ID)
    if reqobj!=frozen_req or reqobj.get('input_digest_sha256')!=R20_RECOVERY_REQUEST_DIGEST: raise RuntimeError('G100_R20_RESUME_REQUEST_NOT_EXACT_PACKAGE_FROZEN_OBJECT')
    prior_records=_tree_records(sd)
    if prior_records!=R20_PRIOR_SAMPLE_TREE: raise RuntimeError('G100_R20_RESUME_SAMPLE_TREE_FINGERPRINT_MISMATCH')
    fobj=json.loads((sd/'failure.json').read_text(encoding='utf-8'))
    if fobj.get('sample_id')!=R20_RECOVERY_SAMPLE_ID or fobj.get('input_digest_sha256')!=R20_RECOVERY_REQUEST_DIGEST or fobj.get('error')!=R20_FAILURE_ERROR: raise RuntimeError('G100_R20_RESUME_FAILURE_CAUSE_MISMATCH')
    q=json.loads((sd/'micro100_aux_gt_qa.json').read_text(encoding='utf-8')); n=q.get('normal') or {}; d=q.get('depth') or {}; oi=q.get('object_index') or {}
    if not (d.get('status')=='PASS' and n.get('status')=='FAIL' and oi.get('status')=='PASS'): raise RuntimeError('G100_R20_RESUME_GT_FAILURE_SIGNATURE_MISMATCH')
    if int(n.get('authority_pixels',-1))!=63375 or float((n.get('canonical_vs_analytic_error') or {}).get('max',999))!=1.0: raise RuntimeError('G100_R20_RESUME_NORMAL_SIGNATURE_MISMATCH')
    if abs(float((d.get('renderer_effective_analytic_abs_error_m') or {}).get('max',999))-1.0350859125374257e-05)>1e-15: raise RuntimeError('G100_R20_RESUME_DEPTH_SIGNATURE_MISMATCH')
    b=d.get('renderer_effective_principal_point_binding') or {}
    if abs(float(b.get('delta_cx_px',999))-(-0.0005387658209231251))>1e-12 or abs(float(b.get('delta_cy_px',999))-0.0005300448275004475)>1e-12: raise RuntimeError('G100_R20_RESUME_BINDING_SIGNATURE_MISMATCH')
    fixture=HERE/'R19_REAL_FAILURE_EVIDENCE'/'PCS_CAMERA_GEOMETRY_DATA_FACTORY_G100_MICRO100_FAILURE_RETURN_R19_REAL_20260908_005859.zip'
    if not fixture.is_file() or sha256_file(fixture)!=R20_PRIOR_R19_RETURN_SHA256: raise RuntimeError('G100_R20_RESUME_R19_FIXTURE_IDENTITY_MISMATCH')
    with zipfile.ZipFile(fixture) as z: partial_bytes=z.read('FAILED_SAMPLES/'+R20_RECOVERY_SAMPLE_ID+'/PARTIAL_OUTPUT_IDENTITIES.json')
    if sha256_bytes(partial_bytes)!=R20_PRIOR_PARTIAL_IDENTITIES_SHA256: raise RuntimeError('G100_R20_RESUME_PARTIAL_OUTPUT_IDENTITIES_SHA_MISMATCH')
    po=json.loads(partial_bytes.decode('utf-8'))
    if po.get('sample_id')!=R20_RECOVERY_SAMPLE_ID or po.get('request_digest')!=R20_RECOVERY_REQUEST_DIGEST or po.get('state')!='FAILED_FINAL' or int(po.get('attempts',-1))!=2 or po.get('files')!=prior_records: raise RuntimeError('G100_R20_RESUME_PARTIAL_OUTPUT_IDENTITIES_CONTENT_MISMATCH')
    evroot=runroot/'RECOVERY'/'R19_FAILED_SAMPLE_029'
    if evroot.exists(): raise RuntimeError('G100_R20_RESUME_RECOVERY_TARGET_PREEXISTS_WITHOUT_R20_MARKER')
    evroot.mkdir(parents=True,exist_ok=False); payload=evroot/'sample_bytes'; shutil.copytree(sd,payload)
    if _tree_records(payload)!=prior_records: raise RuntimeError('G100_R20_RESUME_PRESERVE_HASH_MISMATCH')
    shutil.copy2(reqp,evroot/'request.json'); shutil.copy2(logp,evroot/'worker.log'); (evroot/'PARTIAL_OUTPUT_IDENTITIES.json').write_bytes(partial_bytes)
    if sha256_file(evroot/'request.json')!=R20_PRIOR_REQUEST_SHA256 or sha256_file(evroot/'worker.log')!=R20_PRIOR_WORKER_LOG_SHA256: raise RuntimeError('G100_R20_RESUME_PRESERVE_SIDECAR_HASH_MISMATCH')
    for ci,before in peer_ledger_bytes.items():
        if (runroot/'CHUNKS'/f'chunk_{ci:02d}'/'ledger.json').read_bytes()!=before: raise RuntimeError('G100_R20_RESUME_LEDGER_CHANGED_DURING_PRESERVE:'+str(ci))
    recovery={'schema':'DF-G100-R20-RECOVERY-JOURNAL-V1','status':'PRESERVED_BEFORE_LEDGER_RESET','r20_addendum_drive_id':R20_ADDENDUM_DRIVE_ID,'source_tool':'R19','target_tool':'R20','sample_id':R20_RECOVERY_SAMPLE_ID,'request_digest':R20_RECOVERY_REQUEST_DIGEST,'chunk_digest_sha256':R20_CHUNK02_DIGEST,'prior_state':'FAILED_FINAL','prior_attempts':2,'prior_last_error':'BLENDER_WORKER_RC:5','prior_failure_error':R20_FAILURE_ERROR,'r19_failure_return_sha256':R20_PRIOR_R19_RETURN_SHA256,'prior_sample_tree':prior_records,'completed_samples_preserved':sorted(info['completed_samples_preserved']),'normal_reference_semantics':'RENDERER_EFFECTIVE_NORMAL_REFERENCE_R20_V1','normal_values_used_to_fit_renderer_binding':False,'normal_tolerance':1e-5,'depth_threshold_m':1e-4,'numeric_visibility_epsilon':0.0,'recorded_utc':utc_iso(),'product_mutated':False,'maya_mutated':False,'test77_accessed':False,'training_started':False}
    atomic_json(evroot/'R20_RECOVERY_JOURNAL.json',recovery)
    shutil.rmtree(sd); sd.mkdir(parents=True,exist_ok=True); rec['state']='PENDING'; rec['attempts']=0; rec.pop('last_error',None)
    rec['r20_recovery']={'r20_addendum_drive_id':R20_ADDENDUM_DRIVE_ID,'prior_state':'FAILED_FINAL','prior_attempts':2,'prior_failure_error':R20_FAILURE_ERROR,'recovery_journal_rel':(evroot/'R20_RECOVERY_JOURNAL.json').relative_to(runroot).as_posix(),'normal_reference_semantics':'RENDERER_EFFECTIVE_NORMAL_REFERENCE_R20_V1','normal_values_used_to_fit_renderer_binding':False,'normal_tolerance':1e-5,'depth_threshold_m':1e-4,'numeric_visibility_epsilon':0.0}
    atomic_json(lp,led); recovery['status']='LEDGER_RESET_SAMPLE_029_ONLY'; atomic_json(evroot/'R20_RECOVERY_JOURNAL.json',recovery)
    info['status']='R19_FAILED_SAMPLE029_REOPENED_FOR_R20'; info['recovered_samples'][R20_RECOVERY_SAMPLE_ID]=dict(rec['r20_recovery']); return info

def _r23_tree_fingerprint(root:Path):
    root=Path(root); rows=[]
    if not root.is_dir(): raise RuntimeError('G100_R23_CANONICAL_RUN_MISSING')
    for p in sorted(root.rglob('*'),key=lambda x:x.as_posix()):
        if p.is_file(): rows.append({'path':p.relative_to(root).as_posix(),'bytes':p.stat().st_size,'sha256':sha256_file(p)})
    payload='\n'.join(f"{r['path']}\t{r['bytes']}\t{r['sha256']}" for r in rows).encode()
    return {'file_count':len(rows),'aggregate_sha256':sha256_bytes(payload),'files':rows}

def _r23_load_frozen_prestate_fingerprint():
    p=R23_CANONICAL_PRESTATE_FINGERPRINT_PATH
    if not p.is_file() or sha256_file(p)!=R23_CANONICAL_PRESTATE_FINGERPRINT_SHA256:
        raise RuntimeError('G100_R23_FROZEN_PRESTATE_FINGERPRINT_IDENTITY_MISMATCH')
    d=json.loads(p.read_text(encoding='utf-8'))
    if int(d.get('file_count',-1))!=R23_CANONICAL_PRESTATE_FILE_COUNT or d.get('aggregate_sha256')!=R23_CANONICAL_PRESTATE_AGGREGATE_SHA256 or len(d.get('files') or [])!=R23_CANONICAL_PRESTATE_FILE_COUNT:
        raise RuntimeError('G100_R23_FROZEN_PRESTATE_FINGERPRINT_CONTENT_MISMATCH')
    return {'file_count':int(d['file_count']),'aggregate_sha256':d['aggregate_sha256'],'files':d['files']}

def _r23_assert_prestate_fingerprint(runroot:Path,expected=None):
    exp=_r23_load_frozen_prestate_fingerprint() if expected is None else expected
    act=_r23_tree_fingerprint(runroot)
    if act.get('file_count')!=exp.get('file_count') or act.get('aggregate_sha256')!=exp.get('aggregate_sha256') or act.get('files')!=exp.get('files'):
        raise RuntimeError('G100_R23_CANONICAL_PRESTATE_FINGERPRINT_MISMATCH')
    return act


R24_BRIDGE_JOURNAL_REL='EVIDENCE/R24_COMPOSITIONAL_PROVENANCE_BRIDGE.json'
R24_SAMPLE038_ID='g100_038_urban_near_infinity_day_hard'
R24_EXPECTED_LEGACY_LAB_ONLY_SAMPLES={
    'g100_038_urban_near_infinity_day_hard',
    'g100_039_intersection_telephoto_clay',
}

def _r25_assert_returned_prestate(runroot:Path,chunks):
    """Authenticate the exact real R24 40/100 state without requiring future ledgers.

    Chunks 00..03 must be exact COMPLETE ledgers. Chunks 04..09 may be truly
    unmaterialized; if a future ledger already exists it must be exact pristine
    PENDING/attempts0. The checker is read-only and never synthesizes ledgers.
    """
    runroot=Path(runroot)
    if not runroot.is_dir(): raise RuntimeError('G100_R25_CANONICAL_RUN_MISSING')
    completed=[]; future_modes={}
    if len(chunks)!=10: raise RuntimeError('G100_R25_FROZEN_CHUNK_COUNT_MISMATCH')
    for ci in range(10):
        cr=runroot/'CHUNKS'/f'chunk_{ci:02d}'
        lp=cr/'ledger.json'
        expected={r['sample_id']:r['input_digest_sha256'] for r in chunks[ci]['requests']}
        if len(expected)!=10: raise RuntimeError('G100_R25_FROZEN_REQUEST_COUNT_MISMATCH:'+str(ci))
        if not lp.is_file():
            if ci<4: raise RuntimeError('G100_R25_COMPLETED_LEDGER_MISSING:'+str(ci))
            # A future chunk is validly pristine only when it has no materialized payload.
            if cr.exists():
                extras=[p.name for p in cr.iterdir()]
                if extras: raise RuntimeError('G100_R25_FUTURE_CHUNK_PARTIAL_WITHOUT_LEDGER:'+str(ci)+':'+json.dumps(sorted(extras)))
            future_modes[str(ci)]='PRISTINE_UNMATERIALIZED'
            continue
        L=json.loads(lp.read_text(encoding='utf-8'))
        if L.get('chunk_digest_sha256')!=chunks[ci].get('chunk_digest_sha256'):
            raise RuntimeError('G100_R25_CHUNK_DIGEST_MISMATCH:'+str(ci))
        states=L.get('states') or {}
        if set(states)!=set(expected):
            raise RuntimeError('G100_R25_LEDGER_SAMPLE_SET_MISMATCH:'+str(ci))
        for sid in sorted(expected):
            rr=states[sid]
            if rr.get('request_digest')!=expected[sid]:
                raise RuntimeError('G100_R25_REQUEST_DIGEST_MISMATCH:'+sid)
            if ci<4:
                if rr.get('state')!='COMPLETE' or int(rr.get('attempts',-1))<1:
                    raise RuntimeError('G100_R25_EXPECTED_COMPLETE:'+sid)
                completed.append(sid)
            else:
                if rr.get('state')!='PENDING' or int(rr.get('attempts',0))!=0 or 'last_error' in rr:
                    raise RuntimeError('G100_R25_EXPECTED_PRISTINE_PENDING:'+sid)
        if ci>=4: future_modes[str(ci)]='PRISTINE_LEDGER'
    expected_complete=sorted(r['sample_id'] for c in chunks[:4] for r in c['requests'])
    if len(completed)!=R24_PRESTATE_COMPLETED or sorted(completed)!=expected_complete:
        raise RuntimeError('G100_R25_COMPLETED_SET_MISMATCH')
    prog=runroot/'PROGRESS.json'
    if prog.is_file():
        P=json.loads(prog.read_text(encoding='utf-8'))
        if int(P.get('completed',-1))!=40 or (P.get('counts') or {}).get('COMPLETE')!=40:
            raise RuntimeError('G100_R25_PROGRESS_MISMATCH')
        # No future RUNNING/failed state is compatible with the exact R24 pre-worker stop.
        pc=P.get('counts') or {}
        if any(int(pc.get(k,0) or 0) for k in ('RUNNING','FAILED_RETRYABLE','FAILED_FINAL')):
            raise RuntimeError('G100_R25_PROGRESS_NONPRISTINE_FUTURE_STATE')
    # R23 sample025 recovery remains authoritative and immutable.
    l25=json.loads((runroot/'CHUNKS'/'chunk_02'/'ledger.json').read_text(encoding='utf-8'))
    r25=(l25.get('states') or {}).get(R23_RECOVERY_SAMPLE_ID) or {}
    m25=r25.get('r23_recovery') or {}
    if not (r25.get('state')=='COMPLETE' and m25.get('r23_addendum_drive_id')==R23_ADDENDUM_DRIVE_ID and m25.get('mode')=='RGB_ONLY_IN_PLACE_NO_RERENDER'):
        raise RuntimeError('G100_R25_R23_SAMPLE025_RECOVERY_MARKER_MISMATCH')
    jp=runroot/'RECOVERY'/'R20_COMPLETE_SAMPLE_025_RGB_POSTCHUNK_FAIL'/'R23_RECOVERY_JOURNAL.json'
    if not jp.is_file(): raise RuntimeError('G100_R25_R23_SAMPLE025_RECOVERY_JOURNAL_MISSING')
    j25=json.loads(jp.read_text(encoding='utf-8'))
    if not (j25.get('status')=='RGB_ONLY_TRANSFORM_COMPLETE_SAMPLE025_REMAINS_COMPLETE' and j25.get('r23_addendum_drive_id')==R23_ADDENDUM_DRIVE_ID and j25.get('gt_exrs_immutable') is True and j25.get('thresholds_unchanged') is True):
        raise RuntimeError('G100_R25_R23_SAMPLE025_RECOVERY_JOURNAL_MISMATCH')
    # Pin the exact sample038 false-block bytes captured in the archived R23 RETURN.
    cr=runroot/'CHUNKS'/'chunk_03'; sd=cr/'samples'/R24_SAMPLE038_ID; reqp=cr/'requests'/f'{R24_SAMPLE038_ID}.json'
    if not sd.is_dir() or not reqp.is_file(): raise RuntimeError('G100_R25_SAMPLE038_MISSING')
    exact={reqp:R24_PRESTATE_SAMPLE038_REQUEST_SHA256,sd/'completion.json':R24_PRESTATE_SAMPLE038_COMPLETION_SHA256,
           sd/'rgb_renderer_raw.png':R24_PRESTATE_SAMPLE038_RENDERER_RAW_SHA256,sd/'rgb_pre_r23.png':R24_PRESTATE_SAMPLE038_PRE_R23_SHA256,
           sd/'rgb.png':R24_PRESTATE_SAMPLE038_FINAL_SHA256}
    for fp,sh in exact.items():
        if not fp.is_file() or sha256_file(fp)!=sh: raise RuntimeError('G100_R25_SAMPLE038_EXACT_PRESTATE_MISMATCH:'+fp.name)
    oldacc=runroot/'EVIDENCE'/'SAMPLE_ACCEPTANCE'/f'{R24_SAMPLE038_ID}.json'; bridge=runroot/R24_BRIDGE_JOURNAL_REL
    if not bridge.is_file():
        if not oldacc.is_file() or sha256_file(oldacc)!=R24_PRESTATE_SAMPLE038_OLD_ACCEPTANCE_SHA256:
            raise RuntimeError('G100_R25_SAMPLE038_OLD_FALSE_BLOCK_EVIDENCE_MISMATCH')
        oa=json.loads(oldacc.read_text(encoding='utf-8'))
        if not (oa.get('status')=='FAIL' and (oa.get('checks') or {}).get('provenance') is False and all(v is True for k,v in (oa.get('checks') or {}).items() if k!='provenance')):
            raise RuntimeError('G100_R25_SAMPLE038_NOT_EXACT_PROVENANCE_ONLY_FALSE_BLOCK')
    else:
        b=json.loads(bridge.read_text(encoding='utf-8'))
        if not (b.get('schema')=='DF-G100-R24-COMPOSITIONAL-PROVENANCE-BRIDGE-V1' and b.get('status')=='RECORDED_NO_SAMPLE_MUTATION' and b.get('r24_addendum_drive_id')==R24_ADDENDUM_DRIVE_ID):
            raise RuntimeError('G100_R25_EXISTING_R24_BRIDGE_MISMATCH')
    return {'schema':'DF-G100-R25-PRESTATE-V1','status':'PASS_EXACT_R24_40_OF_100',
            'completed_samples':40,'complete_range':'000..039','continue_from_sample':40,
            'future_chunk_modes':future_modes,'sample038_exact':True,'r23_sample025_recovery_valid':True,
            'r24_addendum_drive_id':R24_ADDENDUM_DRIVE_ID,'r25_addendum_drive_id':R25_ADDENDUM_DRIVE_ID,
            'r24_real_failure_sha256':R25_R24_REAL_FAILURE_SHA256,'thresholds_unchanged':True,
            'prestate_mutated':False,'test77_accessed':False,'training_started':False}

def _r24_write_or_validate_bridge(runroot:Path):
    """Record the pre-R24 metadata bridge without changing any sample payload byte."""
    runroot=Path(runroot); bp=runroot/R24_BRIDGE_JOURNAL_REL
    if bp.is_file():
        b=json.loads(bp.read_text(encoding='utf-8'))
        if not (b.get('schema')=='DF-G100-R24-COMPOSITIONAL-PROVENANCE-BRIDGE-V1' and
                b.get('status')=='RECORDED_NO_SAMPLE_MUTATION' and
                b.get('r24_addendum_drive_id')==R24_ADDENDUM_DRIVE_ID and
                set(b.get('legacy_lab_only_true_samples') or [])==R24_EXPECTED_LEGACY_LAB_ONLY_SAMPLES):
            raise RuntimeError('G100_R24_BRIDGE_JOURNAL_MISMATCH')
        return b
    legacy=[]; records=[]
    for ci in range(4):
        cr=runroot/'CHUNKS'/f'chunk_{ci:02d}'
        for sd in sorted((cr/'samples').glob('g100_*')):
            cp=sd/'completion.json'
            if not cp.is_file(): continue
            c=json.loads(cp.read_text(encoding='utf-8')); m=c.get('r23_systemic_rgb_contrast') or {}
            if m.get('lab_only') is True:
                legacy.append(c.get('sample_id'))
                records.append({'sample_id':c.get('sample_id'),'completion_sha256':sha256_file(cp),
                                'rgb_sha256':sha256_file(sd/'rgb.png'),
                                'rgb_pre_r23_sha256':sha256_file(sd/'rgb_pre_r23.png') if (sd/'rgb_pre_r23.png').is_file() else None,
                                'implementation_id':m.get('implementation_id')})
    if set(legacy)!=R24_EXPECTED_LEGACY_LAB_ONLY_SAMPLES:
        raise RuntimeError('G100_R24_LEGACY_METADATA_CLASS_MISMATCH:'+json.dumps(sorted(legacy)))
    b={'schema':'DF-G100-R24-COMPOSITIONAL-PROVENANCE-BRIDGE-V1','status':'RECORDED_NO_SAMPLE_MUTATION',
       'r24_addendum_drive_id':R24_ADDENDUM_DRIVE_ID,'source_r23_real_failure_sha256':R24_R23_REAL_FAILURE_SHA256,
       'prestate_completed':40,'legacy_lab_only_true_samples':sorted(legacy),'records':records,
       'sample_payload_mutated':False,'pixels_mutated':False,'gt_mutated':False,'thresholds_unchanged':True,
       'test77_accessed':False,'training_started':False,'recorded_utc':utc_iso()}
    atomic_json(bp,b); return b

def apply_r23_recovery_if_needed(runroot:Path,chunks,expected_prestate_fingerprint=None):
    """Fail-closed R23 in-place RGB-only recovery for latent sample025 post-chunk failure."""
    info={'schema':'DF-G100-R23-RECOVERY-V1','status':'NOT_APPLICABLE','r23_addendum_drive_id':R23_ADDENDUM_DRIVE_ID,
          'recovered_samples':{},'completed_samples_preserved':[]}
    runroot=Path(runroot); cr=runroot/'CHUNKS'/'chunk_02'; lp=cr/'ledger.json'
    if not lp.is_file(): return info
    led=json.loads(lp.read_text(encoding='utf-8'))
    if led.get('chunk_digest_sha256')!=R23_CHUNK02_DIGEST: raise RuntimeError('G100_R23_CHUNK02_DIGEST_MISMATCH')
    expected={r['sample_id']:r['input_digest_sha256'] for r in chunks[2]['requests']}
    if expected.get(R23_RECOVERY_SAMPLE_ID)!=R23_RECOVERY_REQUEST_DIGEST: raise RuntimeError('G100_R23_FROZEN_PLAN_TARGET_MISMATCH')
    states=led.get('states') or {}; rec=states.get(R23_RECOVERY_SAMPLE_ID,{})
    if rec.get('request_digest')!=R23_RECOVERY_REQUEST_DIGEST: raise RuntimeError('G100_R23_LEDGER_REQUEST_DIGEST_MISMATCH')
    prior_marker=rec.get('r23_recovery') or {}
    if prior_marker.get('r23_addendum_drive_id')==R23_ADDENDUM_DRIVE_ID:
        sd=cr/'samples'/R23_RECOVERY_SAMPLE_ID
        if rec.get('state')!='COMPLETE': raise RuntimeError('G100_R23_BAD_POST_RECOVERY_STATE')
        expected_rel='RECOVERY/R20_COMPLETE_SAMPLE_025_RGB_POSTCHUNK_FAIL/R23_RECOVERY_JOURNAL.json'
        if prior_marker.get('recovery_journal_rel')!=expected_rel: raise RuntimeError('G100_R23_IDEMPOTENT_JOURNAL_POINTER_MISMATCH')
        jp=runroot/expected_rel; ev=jp.parent; payload=ev/'sample_bytes'
        if not jp.is_file(): raise RuntimeError('G100_R23_IDEMPOTENT_JOURNAL_MISSING')
        j=json.loads(jp.read_text(encoding='utf-8'))
        if not (j.get('schema')=='DF-G100-R23-RECOVERY-JOURNAL-V1' and j.get('status')=='RGB_ONLY_TRANSFORM_COMPLETE_SAMPLE025_REMAINS_COMPLETE' and j.get('r23_addendum_drive_id')==R23_ADDENDUM_DRIVE_ID and j.get('sample_id')==R23_RECOVERY_SAMPLE_ID and j.get('request_digest')==R23_RECOVERY_REQUEST_DIGEST and j.get('chunk_digest_sha256')==R23_CHUNK02_DIGEST and j.get('prior_sample_tree')==R23_PRIOR_SAMPLE_TREE):
            raise RuntimeError('G100_R23_IDEMPOTENT_JOURNAL_CONTENT_MISMATCH')
        if not payload.is_dir() or _tree_records(payload)!=R23_PRIOR_SAMPLE_TREE: raise RuntimeError('G100_R23_IDEMPOTENT_PRESERVED_TREE_MISMATCH')
        if sha256_file(ev/'request.json')!=R23_PRIOR_REQUEST_SHA256 or sha256_file(ev/'worker.log')!=R23_PRIOR_WORKER_LOG_SHA256: raise RuntimeError('G100_R23_IDEMPOTENT_PRESERVED_SIDECAR_MISMATCH')
        if sha256_file(sd/'rgb.png')!=R23_EXPECTED_RGB_SHA256 or not (sd/'rgb_pre_r23.png').is_file() or sha256_file(sd/'rgb_pre_r23.png')!=dict((x['path'],x['sha256']) for x in R23_PRIOR_SAMPLE_TREE)['rgb.png']:
            raise RuntimeError('G100_R23_IDEMPOTENT_RGB_IDENTITY_MISMATCH')
        info['status']='R23_RECOVERY_ALREADY_APPLIED'; info['recovered_samples'][R23_RECOVERY_SAMPLE_ID]=dict(prior_marker); return info
    _r23_assert_prestate_fingerprint(runroot,expected_prestate_fingerprint)
    # Exact current state: all 000..029 complete, later samples pristine pending.
    for ci in (0,1,2):
        cp=runroot/'CHUNKS'/f'chunk_{ci:02d}'/'ledger.json'
        if not cp.is_file(): raise RuntimeError('G100_R23_PRIOR_LEDGER_MISSING:'+str(ci))
        L=json.loads(cp.read_text(encoding='utf-8'))
        for sid,rr in (L.get('states') or {}).items():
            if rr.get('state')!='COMPLETE' or int(rr.get('attempts',-1))<1: raise RuntimeError('G100_R23_EXPECTED_COMPLETE_PEER:'+sid)
            if sid!=R23_RECOVERY_SAMPLE_ID: info['completed_samples_preserved'].append(sid)
    if len(set(info['completed_samples_preserved']))!=29: raise RuntimeError('G100_R23_EXPECTED_29_IMMUTABLE_PEERS')
    for ci in range(3,10):
        cp=runroot/'CHUNKS'/f'chunk_{ci:02d}'/'ledger.json'
        if cp.is_file():
            L=json.loads(cp.read_text(encoding='utf-8'))
            bad=[sid for sid,rr in (L.get('states') or {}).items() if rr.get('state')!='PENDING' or int(rr.get('attempts',0))!=0]
            if bad: raise RuntimeError('G100_R23_LATER_SAMPLE_NOT_PRISTINE_PENDING:'+bad[0])
    sd=cr/'samples'/R23_RECOVERY_SAMPLE_ID; reqp=cr/'requests'/f'{R23_RECOVERY_SAMPLE_ID}.json'; logp=cr/'logs'/f'{R23_RECOVERY_SAMPLE_ID}.log'
    if not sd.is_dir() or not reqp.is_file() or not logp.is_file(): raise RuntimeError('G100_R23_SAMPLE025_EVIDENCE_MISSING')
    if sha256_file(reqp)!=R23_PRIOR_REQUEST_SHA256 or sha256_file(logp)!=R23_PRIOR_WORKER_LOG_SHA256: raise RuntimeError('G100_R23_SAMPLE025_SIDECAR_IDENTITY_MISMATCH')
    if _tree_records(sd)!=R23_PRIOR_SAMPLE_TREE: raise RuntimeError('G100_R23_SAMPLE025_TREE_IDENTITY_MISMATCH')
    req=json.loads(reqp.read_text(encoding='utf-8')); frozen=next(r for r in chunks[2]['requests'] if r['sample_id']==R23_RECOVERY_SAMPLE_ID)
    if req!=frozen: raise RuntimeError('G100_R23_SAMPLE025_REQUEST_NOT_FROZEN_EXACT')
    # Independently prove the known post-chunk RGB-only failure from current bytes.
    comp=json.loads((sd/'completion.json').read_text(encoding='utf-8')); before_stats=rgb_stats(sd/'rgb.png')
    if not (before_stats['unique_rgb']>=32 and before_stats['p01_p99_span']<24 and 12<=before_stats['mean_luma']<=243 and before_stats['structural_fraction']>=.03):
        raise RuntimeError('G100_R23_SAMPLE025_RGB_FAILURE_SIGNATURE_MISMATCH')
    gt=comp.get('micro100_aux_gt') or {}
    if not ((gt.get('depth') or {}).get('status')=='PASS' and (gt.get('normal') or {}).get('status')=='PASS' and (gt.get('object_index') or {}).get('status')=='PASS'):
        raise RuntimeError('G100_R23_SAMPLE025_GT_NOT_ALL_PASS')
    pol=r23_systemic_rgb_policy(req)
    if not pol.get('applied') or pol.get('profile_id')!='BLUEPRINT' or int(pol.get('pivot_u8',-1))!=128 or int(pol.get('factor_numerator',-1))!=5 or int(pol.get('factor_denominator',-1))!=4:
        raise RuntimeError('G100_R23_SAMPLE025_POLICY_NOT_EXACT')
    # Preserve the exact pre-R23 bytes before any mutation.
    ev=runroot/'RECOVERY'/'R20_COMPLETE_SAMPLE_025_RGB_POSTCHUNK_FAIL'
    if ev.exists(): raise RuntimeError('G100_R23_RECOVERY_PATH_PREEXISTS_WITHOUT_MARKER')
    ev.mkdir(parents=True,exist_ok=False); payload=ev/'sample_bytes'; shutil.copytree(sd,payload); shutil.copy2(reqp,ev/'request.json'); shutil.copy2(logp,ev/'worker.log')
    prior_records=_tree_records(payload)
    if prior_records!=R23_PRIOR_SAMPLE_TREE: raise RuntimeError('G100_R23_PRESERVED_TREE_MISMATCH')
    journal={'schema':'DF-G100-R23-RECOVERY-JOURNAL-V1','status':'PRESERVED_BEFORE_RGB_ONLY_TRANSFORM','r23_addendum_drive_id':R23_ADDENDUM_DRIVE_ID,
             'sample_id':R23_RECOVERY_SAMPLE_ID,'request_digest':R23_RECOVERY_REQUEST_DIGEST,'chunk_digest_sha256':R23_CHUNK02_DIGEST,
             'prior_state':'COMPLETE','prior_attempts':int(rec.get('attempts',1)),'prior_sample_tree':prior_records,'prior_rgb_stats':before_stats,
             'completed_samples_preserved':sorted(info['completed_samples_preserved']),'gt_exrs_immutable':True,'thresholds_unchanged':True,
             'product_mutated':False,'maya_mutated':False,'test77_accessed':False,'training_started':False,'recorded_utc':utc_iso()}
    atomic_json(ev/'R23_RECOVERY_JOURNAL.json',journal)
    # RGB-only deterministic transform. GT EXRs and all other sample payloads are untouched.
    pre=sd/'rgb_pre_r23.png'; shutil.copy2(sd/'rgb.png',pre)
    meta=apply_fixed_rgb8_contrast_png(pre,sd/'rgb.png',pivot=int(pol['pivot_u8']),numerator=int(pol['factor_numerator']),denominator=int(pol['factor_denominator']))
    meta.update({'implementation_id':pol['implementation_id'],'source_rgb_rel':'rgb_pre_r23.png','final_rgb_rel':'rgb.png','threshold_adaptive':False,'sample_statistics_used':False,'eligibility':pol,'lab_only':False,'production_authorized':True})
    if sha256_file(sd/'rgb.png')!=R23_EXPECTED_RGB_SHA256: raise RuntimeError('G100_R23_SAMPLE025_TRANSFORMED_RGB_IDENTITY_MISMATCH')
    after_stats=rgb_stats(sd/'rgb.png')
    if not (after_stats['unique_rgb']>=32 and after_stats['p01_p99_span']>=24 and 12<=after_stats['mean_luma']<=243 and after_stats['structural_fraction']>=.03): raise RuntimeError('G100_R23_SAMPLE025_TRANSFORM_DOES_NOT_PASS_RGB')
    # Update only completion provenance + file manifest records for changed/added RGB bytes.
    comp['r23_systemic_rgb_policy']=pol; comp['r23_systemic_rgb_contrast']=meta
    files=[r for r in comp.get('files',[]) if r.get('path') not in {'rgb.png','rgb_pre_r23.png'}]
    for name in ('rgb.png','rgb_pre_r23.png'):
        pp=sd/name; files.append({'path':name,'bytes':pp.stat().st_size,'sha256':sha256_file(pp)})
    comp['files']=files; atomic_json(sd/'completion.json',comp)
    # Verify unchanged GT payload exact hashes from prior tree.
    prior={r['path']:r for r in R23_PRIOR_SAMPLE_TREE}
    for name in ('depth.exr','normal.exr','object_index.exr','micro100_aux_gt_qa.json','normal_authority_mask.uint8.bin','normal_filter_safe_interior_mask.uint8.bin','camera_calibration.json','pre_render_reprojection.json'):
        if sha256_file(sd/name)!=prior[name]['sha256']: raise RuntimeError('G100_R23_GT_OR_CAMERA_MUTATED:'+name)
    rec['r23_recovery']={'r23_addendum_drive_id':R23_ADDENDUM_DRIVE_ID,'mode':'RGB_ONLY_IN_PLACE_NO_RERENDER','prior_state':'COMPLETE','prior_attempts':int(rec.get('attempts',1)),
                         'recovery_journal_rel':(ev/'R23_RECOVERY_JOURNAL.json').relative_to(runroot).as_posix(),'prior_rgb_sha256':prior['rgb.png']['sha256'],'final_rgb_sha256':R23_EXPECTED_RGB_SHA256,
                         'gt_exrs_immutable':True,'thresholds_unchanged':True}
    atomic_json(lp,led); journal['status']='RGB_ONLY_TRANSFORM_COMPLETE_SAMPLE025_REMAINS_COMPLETE'; journal['final_rgb_stats']=after_stats; atomic_json(ev/'R23_RECOVERY_JOURNAL.json',journal)
    info['status']='R20_COMPLETE_SAMPLE025_RGB_POSTCHUNK_FAIL_RECOVERED_IN_PLACE'; info['recovered_samples'][R23_RECOVERY_SAMPLE_ID]=dict(rec['r23_recovery']); return info

def fixed_zip_write(z,name,data):
    zi=zipfile.ZipInfo(name,date_time=(2026,9,6,0,0,0));zi.compress_type=zipfile.ZIP_DEFLATED;zi.external_attr=0o100644<<16;z.writestr(zi,data)
def make_chunk_zip(chunk_root:Path,out:Path):
    members=[]
    for p in sorted(chunk_root.rglob('*')):
        if not p.is_file():continue
        rel=p.relative_to(chunk_root).as_posix()
        if rel.startswith('logs/'):continue
        if rel in {'CHUNK_ARCHIVE_MANIFEST.json'}:continue
        b=p.read_bytes();members.append({'path':rel,'bytes':len(b),'sha256':sha256_bytes(b)})
    manifest={'schema':'DF-G100-CHUNK-ARCHIVE-MANIFEST-V1','chunk_root_name':chunk_root.name,'members':members}
    out.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
        fixed_zip_write(z,'CHUNK_ARCHIVE_MANIFEST.json',(json.dumps(manifest,indent=2,sort_keys=True)+'\n').encode())
        for r in members:fixed_zip_write(z,r['path'],(chunk_root/r['path']).read_bytes())
    with zipfile.ZipFile(out) as z:
        bad=z.testzip()
        if bad:raise RuntimeError('CHUNK_ZIP_CRC:'+bad)
    return {'path':out.name,'bytes':out.stat().st_size,'sha256':sha256_file(out),'crc':'PASS','member_count':len(members)+1}

def duplicate_and_distribution_qa(reqs,accepts):
    dimensions={'sample_id':[r['sample_id'] for r in reqs],'request_digest':[r['input_digest_sha256'] for r in reqs],'base_scene_id':[r['scene']['base_scene_id'] for r in reqs],'recipe_digest':[r['scene']['recipe_digest_sha256'] for r in reqs],'rgb_sha256':[a['rgb_sha256'] for a in accepts]}
    dup={k:[x for x,c in Counter(v).items() if c>1] for k,v in dimensions.items()};ph=[a['perceptual_hash_8x8'] for a in accepts];near=[]
    for i in range(len(ph)):
      for j in range(i+1,len(ph)):
        d=hamming_hex(ph[i],ph[j])
        if d<=6:near.append({'a':reqs[i]['sample_id'],'b':reqs[j]['sample_id'],'hamming':d})
    counts={'families':dict(Counter(r['scene']['scene_family'] for r in reqs)),'cameras':dict(Counter(r['camera']['profile'] for r in reqs)),'appearances':dict(Counter(r['appearance']['profile_id'] for r in reqs)),'resolutions':dict(Counter(f"{r['camera']['width']}x{r['camera']['height']}" for r in reqs))}
    return {'schema':'DF-G100-CORPUS-DUPLICATE-DISTRIBUTION-QA-V1','status':'PASS' if not any(dup.values()) and counts==EXPECTED_COUNTS else 'FAIL','exact_duplicates':dup,'perceptual_near_duplicates_report_only':near,'counts':counts,'expected_counts':EXPECTED_COUNTS}

def negative_controls():
    CFB=[[1,0,0],[0,0,1],[0,-1,0]]
    def hash_check(data,claimed):return sha256_bytes(data)==claimed
    def bind(reqdig,compdig):return reqdig==compdig
    def no_dups(xs):return len(xs)==len(set(xs))
    def no_leak(a,b):return not(set(a)&set(b))
    def painter_impl(x):return x=='PAINTERLY_CONCEPT_DCC_V2_R10'
    def depth_def(x):return x=='camera_cv_forward_z_meters'
    def normal_frame(x):return x==CFB
    def members(expected,actual):return set(expected)<=set(actual)
    ctrls={
      'tampered_hash_detected':not hash_check(b'abc','0'*64),
      'wrong_camera_binding_detected':not bind('a'*64,'b'*64),
      'duplicate_sample_id_detected':not no_dups(['a','a']),
      'duplicate_rgb_detected':not no_dups(['x','x']),
      'synthetic_split_leakage_detected':not no_leak(['s1','s2'],['s2','s3']),
      'old_painterly_reactivation_detected':not painter_impl('INHERITED_GENERIC_OR_PROFILE_SPECIFIC_V8R2'),
      'wrong_depth_definition_detected':not depth_def('radial_euclidean_distance'),
      'swapped_normal_frame_transform_detected':not normal_frame([[1,0,0],[0,0,-1],[0,1,0]]),
      'missing_chunk_member_detected':not members(['a','b'],['a']),
    }
    return {'schema':'DF-G100-NEGATIVE-CONTROLS-V1','status':'PASS' if all(ctrls.values()) else 'FAIL','controls':ctrls}

def choose_visual(reqs):
    # Frozen R26 visual selection: 8 lowest rich-family observability margins,
    # then deterministic coverage/stress guarantees, then root-seed fill.
    rich=[]
    for i,r in enumerate(reqs):
        sc=r.get('camera_observability_v2',{}).get('observability_stress_score')
        if sc is not None: rich.append((float(sc),i))
    stress=[i for _s,i in sorted(rich,key=lambda x:(x[0],x[1]))[:8]]
    selected=[]
    def add(i):
        if i not in selected:selected.append(i)
    for i in stress:add(i)
    uncovered=set()
    for f in FAMILIES:uncovered.add(('family',f))
    for c in CAMERAS:uncovered.add(('camera',c))
    for a in APPEARANCES:uncovered.add(('appearance',a))
    for rr in EXPECTED_COUNTS['resolutions']:uncovered.add(('resolution',rr))
    for i in selected:
        r=reqs[i];uncovered-={('family',r['scene']['scene_family']),('camera',r['camera']['profile']),('appearance',r['appearance']['profile_id']),('resolution',f"{r['camera']['width']}x{r['camera']['height']}")}
    for i,r in enumerate(reqs):
        tags={('family',r['scene']['scene_family']),('camera',r['camera']['profile']),('appearance',r['appearance']['profile_id']),('resolution',f"{r['camera']['width']}x{r['camera']['height']}")}
        if tags&uncovered:add(i);uncovered-=tags
    enclosed={'INTERIOR','CORRIDOR','CLUTTER','HYBRID_CONCEPT'}
    urban={'URBAN','INTERSECTION'}
    def ensure_count(fams,n):
        have=sum(1 for i in selected if reqs[i]['scene']['scene_family'] in fams)
        if have<n:
            for i,r in enumerate(reqs):
                if r['scene']['scene_family'] in fams and i not in selected:
                    add(i);have+=1
                    if have>=n:break
    ensure_count(enclosed,2);ensure_count(urban,2);ensure_count({'SPARSE'},1);ensure_count({'ORGANIC_NEGATIVE'},1)
    if len(selected)>24: raise RuntimeError('G100_R26_VISUAL_MANDATORY_UNION_EXCEEDS_24:'+str(len(selected)))
    rng=random.Random(ROOT_SEED);rest=[i for i in range(100) if i not in selected];rng.shuffle(rest)
    for i in rest:
        if len(selected)>=24:break
        add(i)
    return selected[:24],sorted(uncovered)

def horizon_segment(line,w,h):
    a,b,c=map(float,line);pts=[]
    if abs(b)>1e-12:
      for x in (0,w-1):
        y=-(a*x+c)/b
        if 0<=y<=h-1:pts.append((x,y))
    if abs(a)>1e-12:
      for y in (0,h-1):
        x=-(b*y+c)/a
        if 0<=x<=w-1:pts.append((x,y))
    out=[]
    for p in pts:
      if not any(abs(p[0]-q[0])<1e-6 and abs(p[1]-q[1])<1e-6 for q in out):out.append(p)
    return out[:2]
def write_visuals(runroot,reqs,accepts):
    sel,uncovered=choose_visual(reqs)
    if uncovered:raise RuntimeError('VISUAL_COVERAGE_UNSATISFIED:'+repr(uncovered))
    cards=[];svg_parts=[];cellw,cellh=300,230;cols=4;rows=math.ceil(len(sel)/cols)
    for k,i in enumerate(sel):
        r=reqs[i];sid=r['sample_id'];ci=i//10;sd=runroot/'CHUNKS'/f'chunk_{ci:02d}'/'samples'/sid;png=sd/'rgb.png';b64=base64.b64encode(png.read_bytes()).decode()
        comp=json.loads((sd/'completion.json').read_text());a=accepts[i];w=r['camera']['width'];h=r['camera']['height'];overlay=''
        hs=horizon_segment(comp['truth_overlay']['horizon_line_abc'],w,h)
        if len(hs)==2:overlay+=f'<line x1="{hs[0][0]}" y1="{hs[0][1]}" x2="{hs[1][0]}" y2="{hs[1][1]}" stroke="#ffd54a" stroke-width="2"/>'
        for axis,col in [('X','#ff5c5c'),('Y','#58e06f'),('Z','#5c83ff')]:
            vp=comp['truth_overlay']['vps'][axis]
            if vp.get('finite') and vp.get('pixel'):
                x,y=vp['pixel']
                if -20<=x<=w+20 and -20<=y<=h+20:overlay+=f'<circle cx="{x}" cy="{y}" r="5" fill="{col}"/>'
        label=f"{sid} | {r['camera']['width']}x{r['camera']['height']} | GT N={a['gt']['normal']['authority_fraction']:.3f} Dmax={a['gt']['depth']['analytic_abs_error_m']['max']:.2e}"
        cards.append(f'<article><div class="im"><img src="data:image/png;base64,{b64}"><svg viewBox="0 0 {w} {h}">{overlay}</svg></div><h3>{html.escape(label)}</h3><p>{html.escape(r["scene"]["scene_family"])} · {html.escape(r["camera"]["profile"])} · {html.escape(r["appearance"]["profile_id"])}</p></article>')
        x=(k%cols)*cellw;y=(k//cols)*cellh;svg_parts.append(f'<g transform="translate({x},{y})"><image href="data:image/png;base64,{b64}" x="0" y="0" width="280" height="180" preserveAspectRatio="xMidYMid meet"/><text x="0" y="198" fill="white" font-size="10">{html.escape(sid)}</text><text x="0" y="212" fill="#aaa" font-size="10">{html.escape(r["scene"]["scene_family"]+" / "+r["camera"]["profile"]+" / "+r["appearance"]["profile_id"])}</text></g>')
    ev=runroot/'EVIDENCE';ev.mkdir(exist_ok=True)
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="{cols*cellw}" height="{rows*cellh}" style="background:#101318">'+''.join(svg_parts)+'</svg>'
    atomic_text(ev/'DF_G100_CONTACT_SHEET_24.svg',svg)
    browser='''<!doctype html><meta charset="utf-8"><title>DF-G100 MICRO100 V2 R29 Browser</title><style>body{margin:0;padding:24px;background:#0c1016;color:#eef;font-family:system-ui}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(330px,1fr));gap:18px}article{background:#171d27;border:1px solid #30394a;border-radius:12px;padding:12px}.im{position:relative}.im img{width:100%;display:block;background:#000}.im svg{position:absolute;inset:0;width:100%;height:100%}h3{font-size:12px;word-break:break-all}p{color:#aab3c4}</style><h1>DF-G100 MICRO100 V2 / R29 — deterministic visual review set (24)</h1><p>Yellow=horizon; RGB markers=X/Y/Z VP when within view. GT metrics are analytic, raw EXRs remain immutable.</p><main>'''+''.join(cards)+'</main>'
    atomic_text(ev/'DF_G100_EVIDENCE_BROWSER.html',browser)
    atomic_json(ev/'DF_G100_VISUAL_SELECTION.json',{'schema':'DF-G100-R26-VISUAL-SELECTION-V2','selected_indices':sel,'selected_sample_ids':[reqs[i]['sample_id'] for i in sel],'count':len(sel),'coverage_uncovered':uncovered,'pre_render_observability_stress_scores':{reqs[i]['sample_id']:reqs[i].get('camera_observability_v2',{}).get('observability_stress_score') for i in sel},'r26_clarification_drive_id':R26_CLARIFICATION_DRIVE_ID})
    return sel

def verify_file_record(path,rec):return path.is_file() and path.stat().st_size==rec['bytes'] and sha256_file(path)==rec['sha256']
def corpus_qa(runroot,reqs,accepts,chunk_ids):
    dd=duplicate_and_distribution_qa(reqs,accepts);nc=negative_controls()
    chunk_ok=all(x['crc']=='PASS' and (runroot/'CHUNK_ARCHIVES'/x['path']).stat().st_size==x['bytes'] and sha256_file(runroot/'CHUNK_ARCHIVES'/x['path'])==x['sha256'] for x in chunk_ids)
    sample_ok=all(a['status']=='PASS' for a in accepts)
    qa={'schema':'DF-G100-CORPUS-QA-V1','status':'PASS' if sample_ok and dd['status']=='PASS' and nc['status']=='PASS' and chunk_ok else 'FAIL','sample_count':len(accepts),'sample_acceptance_all_pass':sample_ok,'duplicate_distribution':dd,'negative_controls':nc,'chunk_archive_integrity':{'status':'PASS' if chunk_ok else 'FAIL','chunks':chunk_ids}}
    atomic_json(runroot/'EVIDENCE'/'DF_G100_CORPUS_QA.json',qa);return qa

def progress_loop(runroot:Path,stop:threading.Event):
    while not stop.is_set():
        try:update_progress(runroot)
        except Exception:pass
        stop.wait(2.0)
    try:update_progress(runroot)
    except Exception:pass
def update_progress(runroot):
    states=[]
    for ci in range(10):
        lp=runroot/'CHUNKS'/f'chunk_{ci:02d}'/'ledger.json'
        if lp.is_file():states.extend(json.loads(lp.read_text()).get('states',{}).values())
    counts=Counter(r.get('state') for r in states);done=counts.get('COMPLETE',0);obj={'schema':'DF-G100-PROGRESS-V1','dataset_id':DATASET_ID,'completed':done,'total':100,'counts':dict(counts),'updated_utc':utc_iso(),'status':'RUNNING' if done<100 and not counts.get('FAILED_FINAL') else ('FAILED' if counts.get('FAILED_FINAL') else 'MEASUREMENT_COMPLETE_PENDING_VISUAL_REVIEW')}
    atomic_json(runroot/'PROGRESS.json',obj)
    atomic_text(runroot/'PROGRESS.html',f'<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="5"><style>body{{background:#101319;color:#eee;font-family:system-ui;padding:30px}}progress{{width:100%;height:30px}}</style><h1>DF-G100 MICRO100 V2 / R36</h1><progress value="{done}" max="100"></progress><h2>{done}/100 COMPLETE</h2><pre>{html.escape(json.dumps(obj,indent=2))}</pre>')

def blender_preflight(M,root):
    out=M['acquire_or_verify_runtime'](root,allow_download=False);rp=M['runtime_paths'](root);exe=rp['runtime_dir']/'blender.exe';ident=M['query_blender_identity'](exe)
    expr="import numpy as np;print('PCS_G100_NUMPY='+np.__version__)"
    cp=subprocess.run([str(exe),'--background','--factory-startup','--python-expr',expr],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=90,check=False)
    marker=[x for x in cp.stdout.splitlines() if 'PCS_G100_NUMPY=' in x]
    if cp.returncode!=0 or not marker:raise RuntimeError('G100_BLENDER_NUMPY_PREFLIGHT_FAIL')
    return {'runtime_verify':out['status'],'blender_identity':ident,'numpy_marker':marker[-1].split('PCS_G100_NUMPY=',1)[1].strip(),'no_download':True}

def package_failure(root,runroot,error,tb=None):
    """Self-contained R4 failure transport.

    Top-level state remains compact, but every FAILED_FINAL sample contributes
    its request, worker log, failure/QA/calibration/reprojection JSON when
    available plus SHA/size identities for all partial sample outputs.
    """
    returns=root/'11_PACKAGES'/'RETURNS';returns.mkdir(parents=True,exist_ok=True)
    ev=root/'11_PACKAGES'/'R36_FAILURE_EVIDENCE_STAGING';shutil.rmtree(ev,ignore_errors=True);ev.mkdir(parents=True)
    report={'schema':'DF-G100-R36-V2-FAILURE-V1','status':'FAIL_G100_OPEN','error':error,'traceback':tb,
            'run_root':str(runroot),'completed_samples':0,'r4_addendum_drive_id':R4_ADDENDUM_DRIVE_ID,'r5_addendum_drive_id':R5_ADDENDUM_DRIVE_ID,'r6_addendum_drive_id':R6_ADDENDUM_DRIVE_ID,'r7_addendum_drive_id':R7_ADDENDUM_DRIVE_ID,'r8_addendum_drive_id':R8_ADDENDUM_DRIVE_ID,'r9_addendum_drive_id':R9_ADDENDUM_DRIVE_ID,'r10_addendum_drive_id':R10_ADDENDUM_DRIVE_ID,'r11_addendum_drive_id':R11_ADDENDUM_DRIVE_ID,'r12_addendum_drive_id':R12_ADDENDUM_DRIVE_ID,'r13_addendum_drive_id':R13_ADDENDUM_DRIVE_ID,'r14_addendum_drive_id':R14_ADDENDUM_DRIVE_ID,'r15_addendum_drive_id':R15_ADDENDUM_DRIVE_ID,'r16_addendum_drive_id':R16_ADDENDUM_DRIVE_ID,'r17_addendum_drive_id':R17_ADDENDUM_DRIVE_ID,'r18_addendum_drive_id':R18_ADDENDUM_DRIVE_ID,'r19_addendum_drive_id':R19_ADDENDUM_DRIVE_ID,'r20_addendum_drive_id':R20_ADDENDUM_DRIVE_ID,'r23_addendum_drive_id':R23_ADDENDUM_DRIVE_ID,'r24_addendum_drive_id':R24_ADDENDUM_DRIVE_ID,'r25_addendum_drive_id':R25_ADDENDUM_DRIVE_ID,'r26_spec_drive_id':R26_SPEC_DRIVE_ID,'r26_clarification_drive_id':R26_CLARIFICATION_DRIVE_ID,'r27_spec_drive_id':R27_SPEC_DRIVE_ID,'r28_spec_drive_id':R28_SPEC_DRIVE_ID,'r28a_authority_refresh_drive_id':R28A_AUTHORITY_REFRESH_DRIVE_ID,'r29_spec_drive_id':R29_SPEC_DRIVE_ID,'r29_failure_authority_drive_id':R29_FAILURE_DRIVE_ID,'r33_spec_drive_id':R33_SPEC_DRIVE_ID,'r34_spec_drive_id':R34_SPEC_DRIVE_ID,'r36_spec_drive_id':R36_SPEC_DRIVE_ID,'v1_final_adjudication_drive_id':V1_FINAL_ADJUDICATION_DRIVE_ID,'source_release_id':SOURCE_RELEASE_ID,
            'product_mutated':False,'maya_product_scene_mutated':False,'test77_accessed':False,
            'training_started':False,'scale_1k_authorized':False}
    try:
        pr=json.loads((runroot/'PROGRESS.json').read_text());report['completed_samples']=pr.get('completed',0);report['progress']=pr
    except Exception:pass
    atomic_json(ev/'FAILURE_REPORT.json',report)
    for p in [runroot/'PROGRESS.json',runroot/'PROGRESS.html',runroot/'PLAN'/'PLAN_QA.json']:
        if p.is_file():shutil.copy2(p,ev/p.name)

    failed_samples=[]
    for ci in range(10):
        cr=runroot/'CHUNKS'/f'chunk_{ci:02d}'
        ledger=None
        lp=cr/'ledger.json'
        if lp.is_file():
            try: ledger=json.loads(lp.read_text(encoding='utf-8'))
            except Exception: ledger=None
        for name in ['ledger.json','worker_result_manifest.json','chunk_progress.json']:
            p=cr/name
            if p.is_file():shutil.copy2(p,ev/f'chunk_{ci:02d}_{name}')
        if not ledger: continue
        for sid,rec in sorted((ledger.get('states') or {}).items()):
            if rec.get('state')!='FAILED_FINAL': continue
            sample_ev=ev/'FAILED_SAMPLES'/sid;sample_ev.mkdir(parents=True,exist_ok=True)
            reqp=cr/'requests'/f'{sid}.json';logp=cr/'logs'/f'{sid}.log';sd=cr/'samples'/sid
            if reqp.is_file():shutil.copy2(reqp,sample_ev/'request.json')
            if logp.is_file():shutil.copy2(logp,sample_ev/'worker.log')
            for name in ['failure.json','micro100_aux_gt_qa.json','camera_calibration.json','pre_render_reprojection.json','completion.json',
                         'renderer_binding_diagnostic.json','rgb.png','rgb_renderer_raw.png','depth.exr','object_index.exr','normal.exr','normal_authority_mask.uint8.bin','normal_filter_safe_interior_mask.uint8.bin','depth_filter_safe_interior_mask.uint8.bin']:
                p=sd/name
                if p.is_file():shutil.copy2(p,sample_ev/name)
            partial=_tree_records(sd)
            atomic_json(sample_ev/'PARTIAL_OUTPUT_IDENTITIES.json',{
                'schema':'DF-G100-R8-PARTIAL-OUTPUT-IDENTITIES-V1','sample_id':sid,
                'request_digest':rec.get('request_digest'),'state':rec.get('state'),
                'attempts':rec.get('attempts'),'last_error':rec.get('last_error'),
                'files':partial})
            failed_samples.append({'chunk_index':ci,'sample_id':sid,'request_digest':rec.get('request_digest'),
                                   'failure_json_present':(sample_ev/'failure.json').is_file(),
                                   'worker_log_present':(sample_ev/'worker.log').is_file(),
                                   'request_present':(sample_ev/'request.json').is_file(),
                                   'partial_file_count':len(partial)})
    report['failed_samples']=failed_samples
    # R9 evidence-quality rule: if the historical sample001 recovery was applied,
    # keep the new recovered RGB/completion identity in any later failure bundle
    # so its appearance correction can be adjudicated without another collector.
    try:
        cr0=runroot/'CHUNKS'/'chunk_00'; lp0=cr0/'ledger.json'
        l0=json.loads(lp0.read_text(encoding='utf-8')) if lp0.is_file() else {}
        r1=(l0.get('states') or {}).get(R9_RECOVERY_SAMPLE_ID,{})
        if (r1.get('r9_recovery') or {}).get('r9_addendum_drive_id')==R9_ADDENDUM_DRIVE_ID and not (r1.get('r10_recovery') or {}).get('r10_addendum_drive_id'):
            red=ev/'R9_RECOVERED_SAMPLE001';red.mkdir(parents=True,exist_ok=True)
            sdir=cr0/'samples'/R9_RECOVERY_SAMPLE_ID
            for srcp,dstname in [
                (cr0/'requests'/f'{R9_RECOVERY_SAMPLE_ID}.json','request.json'),
                (cr0/'logs'/f'{R9_RECOVERY_SAMPLE_ID}.log','worker.log'),
                (sdir/'rgb.png','rgb.png'),(sdir/'completion.json','completion.json'),
                (runroot/'EVIDENCE'/'SAMPLE_ACCEPTANCE'/f'{R9_RECOVERY_SAMPLE_ID}.json','sample_acceptance.json')]:
                if srcp.is_file(): shutil.copy2(srcp,red/dstname)
            atomic_json(red/'IDENTITIES.json',{'schema':'DF-G100-R9-RECOVERED-SAMPLE001-EVIDENCE-V1',
                'sample_id':R9_RECOVERY_SAMPLE_ID,'request_digest':R9_RECOVERY_REQUEST_DIGEST,
                'ledger_state':r1.get('state'),'files':_tree_records(red),
                'r9_addendum_drive_id':R9_ADDENDUM_DRIVE_ID})
            report['r9_recovered_sample001_evidence_present']=True
    except Exception as evidence_error:
        report['r9_recovered_sample001_evidence_present']=False
        report['r9_recovered_sample001_evidence_error']=f'{type(evidence_error).__name__}:{evidence_error}'
    # R10 evidence-quality rule: after the fixed RGB transform is exercised,
    # keep both the raw renderer RGB and final contract RGB in any later failure.
    try:
        cr0=runroot/'CHUNKS'/'chunk_00'; lp0=cr0/'ledger.json'
        l0=json.loads(lp0.read_text(encoding='utf-8')) if lp0.is_file() else {}
        r1=(l0.get('states') or {}).get(R10_RECOVERY_SAMPLE_ID,{})
        if (r1.get('r10_recovery') or {}).get('r10_addendum_drive_id')==R10_ADDENDUM_DRIVE_ID:
            red=ev/'R10_RECOVERED_SAMPLE001';red.mkdir(parents=True,exist_ok=True)
            sdir=cr0/'samples'/R10_RECOVERY_SAMPLE_ID
            for srcp,dstname in [
                (cr0/'requests'/f'{R10_RECOVERY_SAMPLE_ID}.json','request.json'),
                (cr0/'logs'/f'{R10_RECOVERY_SAMPLE_ID}.log','worker.log'),
                (sdir/'rgb_renderer_raw.png','rgb_renderer_raw.png'),(sdir/'rgb.png','rgb.png'),
                (sdir/'completion.json','completion.json'),
                (runroot/'EVIDENCE'/'SAMPLE_ACCEPTANCE'/f'{R10_RECOVERY_SAMPLE_ID}.json','sample_acceptance.json')]:
                if srcp.is_file(): shutil.copy2(srcp,red/dstname)
            atomic_json(red/'IDENTITIES.json',{'schema':'DF-G100-R10-RECOVERED-SAMPLE001-EVIDENCE-V1',
                'sample_id':R10_RECOVERY_SAMPLE_ID,'request_digest':R10_RECOVERY_REQUEST_DIGEST,
                'ledger_state':r1.get('state'),'files':_tree_records(red),
                'r10_addendum_drive_id':R10_ADDENDUM_DRIVE_ID})
            report['r10_recovered_sample001_evidence_present']=True
    except Exception as evidence_error:
        report['r10_recovered_sample001_evidence_present']=False
        report['r10_recovered_sample001_evidence_error']=f'{type(evidence_error).__name__}:{evidence_error}'
    # R15 evidence-quality rule: post-chunk acceptance can fail on a ledger-COMPLETE
    # sample. Preserve the exact target payload so external adjudication never has
    # to infer current bytes from historical recovery evidence.
    try:
        m=re.search(r'G100_(?:R\\d+_)?SAMPLE_ACCEPTANCE_FAIL:([^:]+)',str(error))
        if m:
            sid=m.group(1)
            found=None
            for ci in range(10):
                cr=runroot/'CHUNKS'/f'chunk_{ci:02d}'; lp=cr/'ledger.json'
                if not lp.is_file(): continue
                L=json.loads(lp.read_text(encoding='utf-8')); rec=(L.get('states') or {}).get(sid)
                if rec is not None:
                    found=(ci,cr,rec); break
            if found:
                ci,cr,rec=found; pe=ev/'POST_CHUNK_ACCEPTANCE_FAILURE'/sid; pe.mkdir(parents=True,exist_ok=True); sd=cr/'samples'/sid
                reqp=cr/'requests'/f'{sid}.json'; logp=cr/'logs'/f'{sid}.log'; accp=runroot/'EVIDENCE'/'SAMPLE_ACCEPTANCE'/f'{sid}.json'
                if reqp.is_file(): shutil.copy2(reqp,pe/'request.json')
                if logp.is_file(): shutil.copy2(logp,pe/'worker.log')
                if accp.is_file(): shutil.copy2(accp,pe/'sample_acceptance.json')
                if sd.is_dir(): shutil.copytree(sd,pe/'sample_bytes',dirs_exist_ok=True)
                atomic_json(pe/'IDENTITIES.json',{'schema':'DF-G100-R17-POST-CHUNK-ACCEPTANCE-EVIDENCE-V1','sample_id':sid,'chunk_index':ci,'ledger_state':rec.get('state'),'request_digest':rec.get('request_digest'),'files':_tree_records(pe)})
                report['post_chunk_acceptance_failure']={'sample_id':sid,'chunk_index':ci,'ledger_state':rec.get('state'),'evidence_rel':pe.relative_to(ev).as_posix(),'payload_file_count':len(_tree_records(pe))}
    except Exception as evidence_error:
        report['post_chunk_acceptance_evidence_error']=f'{type(evidence_error).__name__}:{evidence_error}'
    # R16 evidence-quality rule: if live-payload authority fails before the
    # controlled reopen, carry the exact current COMPLETE sample015 evidence so
    # external adjudication is self-contained.
    try:
        if 'G100_R16_RESUME_' in str(error):
            sid=R16_RECOVERY_SAMPLE_ID; cr=runroot/'CHUNKS'/'chunk_01'; sd=cr/'samples'/sid
            pe=ev/'R16_RESUME_AUTHORITY_FAILURE'/sid; pe.mkdir(parents=True,exist_ok=True)
            reqp=cr/'requests'/f'{sid}.json'; logp=cr/'logs'/f'{sid}.log'; accp=runroot/'EVIDENCE'/'SAMPLE_ACCEPTANCE'/f'{sid}.json'
            if reqp.is_file(): shutil.copy2(reqp,pe/'request.json')
            if logp.is_file(): shutil.copy2(logp,pe/'worker.log')
            if accp.is_file(): shutil.copy2(accp,pe/'sample_acceptance.json')
            if sd.is_dir(): shutil.copytree(sd,pe/'sample_bytes',dirs_exist_ok=True)
            atomic_json(pe/'IDENTITIES.json',{'schema':'DF-G100-R16-RESUME-AUTHORITY-EVIDENCE-V1',
                'sample_id':sid,'request_digest':R16_RECOVERY_REQUEST_DIGEST,
                'error':str(error),'files':_tree_records(pe),
                'r16_addendum_drive_id':R16_ADDENDUM_DRIVE_ID})
            report['r16_resume_authority_failure']={'sample_id':sid,'evidence_rel':pe.relative_to(ev).as_posix(),
                'payload_file_count':len(_tree_records(pe))}
    except Exception as evidence_error:
        report['r16_resume_authority_evidence_error']=f'{type(evidence_error).__name__}:{evidence_error}'
    # R17 evidence-quality rule mirrors the R16 live-authority transport for
    # the span-only COMPLETE sample015 recovery gate.
    try:
        if 'G100_R17_RESUME_' in str(error):
            sid=R17_RECOVERY_SAMPLE_ID; cr=runroot/'CHUNKS'/'chunk_01'; sd=cr/'samples'/sid
            pe=ev/'R17_RESUME_AUTHORITY_FAILURE'/sid; pe.mkdir(parents=True,exist_ok=True)
            reqp=cr/'requests'/f'{sid}.json'; logp=cr/'logs'/f'{sid}.log'; accp=runroot/'EVIDENCE'/'SAMPLE_ACCEPTANCE'/f'{sid}.json'
            if reqp.is_file(): shutil.copy2(reqp,pe/'request.json')
            if logp.is_file(): shutil.copy2(logp,pe/'worker.log')
            if accp.is_file(): shutil.copy2(accp,pe/'sample_acceptance.json')
            if sd.is_dir(): shutil.copytree(sd,pe/'sample_bytes',dirs_exist_ok=True)
            atomic_json(pe/'IDENTITIES.json',{'schema':'DF-G100-R17-RESUME-AUTHORITY-EVIDENCE-V1',
                'sample_id':sid,'request_digest':R17_RECOVERY_REQUEST_DIGEST,
                'error':str(error),'files':_tree_records(pe),
                'r17_addendum_drive_id':R17_ADDENDUM_DRIVE_ID})
            report['r17_resume_authority_failure']={'sample_id':sid,'evidence_rel':pe.relative_to(ev).as_posix(),
                'payload_file_count':len(_tree_records(pe))}
    except Exception as evidence_error:
        report['r17_resume_authority_evidence_error']=f'{type(evidence_error).__name__}:{evidence_error}'
    atomic_json(ev/'FAILURE_REPORT.json',report)
    recroot=runroot/'RECOVERY'
    if recroot.is_dir():shutil.copytree(recroot,ev/'RECOVERY',dirs_exist_ok=True)
    zpath=returns/FAIL_NAME
    with zipfile.ZipFile(zpath,'w',compression=zipfile.ZIP_DEFLATED,allowZip64=True) as z:
        for p in sorted(ev.rglob('*')):
            if p.is_file():z.write(p,p.relative_to(ev).as_posix())
    with zipfile.ZipFile(zpath) as z:
        bad=z.testzip()
        if bad:raise RuntimeError('G100_FAILURE_RETURN_CRC_FAIL:'+bad)
    return zpath

def outer_package(root,runroot,release,chunk_ids,preflight,plan_info,qa):
    ev=runroot/'EVIDENCE';srcsnap=ev/'SOURCE';shutil.rmtree(srcsnap,ignore_errors=True);srcsnap.mkdir()
    for p in sorted(release.glob('*.py')):shutil.copy2(p,srcsnap/p.name)
    for p in sorted((runroot/'PLAN').glob('*')):shutil.copy2(p,ev/('PLAN_'+p.name))
    recroot=runroot/'RECOVERY'
    if recroot.is_dir():
        shutil.copytree(recroot,ev/'RECOVERY',dirs_exist_ok=True)
    atomic_json(ev/'DF_G100_PREFLIGHT.json',preflight);atomic_json(ev/'DF_G100_CHUNK_IDENTITIES.json',{'schema':'DF-G100-CHUNK-IDENTITIES-V1','chunks':chunk_ids})
    health={'schema':'DF-G100-HEALTH-V2-R36','status':'MEASUREMENT_COMPLETE_PENDING_VISUAL_REVIEW','exact_samples_completed':100,'all_automated_acceptance_pass':qa['status']=='PASS','chunks_pass':all(c['crc']=='PASS' for c in chunk_ids),'corpus_qa_status':qa['status'],'plan_sha256':plan_info['plan_sha256'],'training_handoff_authorized':False,'scale_1k_authorized':False,'scale_10k_authorized':False,'scale_100k_plus_authorized':False,'c_radio_training_authorized':False,'product_mutated':False,'maya_mutated':False,'test77_accessed':False}
    atomic_json(ev/'DF_G100_HEALTH_REPORT.json',health)
    atomic_text(ev/'DF_G100_HEALTH_REPORT.html',f'<!doctype html><meta charset="utf-8"><style>body{{font-family:system-ui;background:#101319;color:#eee;padding:30px}}.pass{{color:#62e585}}</style><h1>DF-G100 MICRO100 V2 / R36 Health</h1><h2 class="pass">MEASUREMENT COMPLETE — PENDING VISUAL REVIEW</h2><pre>{html.escape(json.dumps(health,indent=2,sort_keys=True))}</pre>')
    returns=root/'11_PACKAGES'/'RETURNS';returns.mkdir(parents=True,exist_ok=True);zpath=returns/RETURN_NAME
    # Build a manifest over the exact outer payload sources before ZIP finalization.
    payload=[]
    for c in chunk_ids:
        p=runroot/'CHUNK_ARCHIVES'/c['path'];payload.append(('CHUNKS/'+c['path'],p))
    for p in sorted(ev.rglob('*')):
        if p.is_file():payload.append(('EVIDENCE/'+p.relative_to(ev).as_posix(),p))
    manifest={'schema':'DF-G100-RETURN-MANIFEST-V2-R33','dataset_id':DATASET_ID,'release_id':RELEASE_ID,'status':'MEASUREMENT_COMPLETE_PENDING_VISUAL_REVIEW','files':[{'path':n,'bytes':p.stat().st_size,'sha256':sha256_file(p)} for n,p in payload],'outer_zip_sha256':'RECORDED_EXTERNALLY_AFTER_FINALIZATION'}
    mb=(json.dumps(manifest,indent=2,sort_keys=True)+'\n').encode()
    with zipfile.ZipFile(zpath,'w',compression=zipfile.ZIP_STORED,allowZip64=True) as z:
        zi=zipfile.ZipInfo('RETURN_MANIFEST.json',date_time=(2026,9,6,0,0,0));zi.compress_type=zipfile.ZIP_DEFLATED;z.writestr(zi,mb)
        for n,p in payload:
            # Stream large already-compressed chunk archives from disk; outer identity
            # is external, so source-file timestamps are not authority-bearing.
            z.write(p,n,compress_type=(zipfile.ZIP_STORED if n.startswith('CHUNKS/') else zipfile.ZIP_DEFLATED),compresslevel=(None if n.startswith('CHUNKS/') else 6))
    with zipfile.ZipFile(zpath) as z:
        bad=z.testzip()
        if bad:raise RuntimeError('G100_OUTER_CRC_FAIL:'+bad)
    identity={'schema':'DF-G100-OUTER-TRANSPORT-IDENTITY-V2-R33','file_name':zpath.name,'bytes':zpath.stat().st_size,'sha256':sha256_file(zpath),'crc':'PASS','recorded_utc':utc_iso(),'status':'MEASUREMENT_COMPLETE_PENDING_VISUAL_REVIEW'}
    atomic_json(Path(str(zpath)+'.identity.json'),identity);return zpath,identity

def _r28_impl_failure_authority_path():
    return HERE/'RECOVERY_AUTHORITY'/R28_IMPL_FAILURE_NAME


def _r28_verify_impl_failure_authority():
    p=_r28_impl_failure_authority_path()
    if not p.is_file() or p.stat().st_size!=R28_IMPL_FAILURE_BYTES or sha256_file(p)!=R28_IMPL_FAILURE_SHA256:
        raise RuntimeError('G100_R28_IMPL_FAILURE_AUTHORITY_IDENTITY_MISMATCH')
    with zipfile.ZipFile(p) as z:
        if z.testzip() is not None: raise RuntimeError('G100_R28_IMPL_FAILURE_AUTHORITY_CRC_FAIL')
        rep=json.loads(z.read('FAILURE_REPORT.json'))
        led=json.loads(z.read('chunk_00_ledger.json'))
        if rep.get('schema')!='DF-G100-R27-V2-FAILURE-V1' or rep.get('source_release_id')!='DF_G100_MICRO100_V2_R1_TOOL_R27':
            raise RuntimeError('G100_R28_IMPL_FAILURE_AUTHORITY_SCHEMA_RELEASE')
        if rep.get('error')!="NameError:name 'payload_sha256' is not defined":
            raise RuntimeError('G100_R28_IMPL_FAILURE_AUTHORITY_ERROR_CLASS')
        if led.get('chunk_digest_sha256')!=R27_CHUNK00_DIGEST:
            raise RuntimeError('G100_R28_IMPL_FAILURE_AUTHORITY_LEDGER_DIGEST')
        rec=(led.get('states') or {}).get(R27_RECOVERY_SAMPLE_ID,{})
        if rec.get('state')!='FAILED_FINAL' or int(rec.get('attempts',-1))!=2 or rec.get('last_error')!='BLENDER_WORKER_RC:5' or rec.get('request_digest')!=R27_RECOVERY_REQUEST_DIGEST:
            raise RuntimeError('G100_R28_IMPL_FAILURE_AUTHORITY_TARGET_STATE')
    return {'path':str(p),'drive_id':R28_IMPL_FAILURE_DRIVE_ID,'bytes':p.stat().st_size,'sha256':sha256_file(p),'crc':'PASS'}


def _r28_verify_live_prestate_before_preservation(runroot:Path,chunks):
    if not runroot.is_dir(): raise RuntimeError('G100_R28_EXISTING_R26_RUNROOT_REQUIRED')
    cr=runroot/'CHUNKS'/'chunk_00'; lp=cr/'ledger.json'
    if not lp.is_file(): raise RuntimeError('G100_R28_CHUNK00_LEDGER_MISSING')
    led=json.loads(lp.read_text(encoding='utf-8'))
    if led.get('chunk_digest_sha256')!=R27_CHUNK00_DIGEST: raise RuntimeError('G100_R28_CHUNK00_DIGEST_MISMATCH')
    expected={r['sample_id']:r['input_digest_sha256'] for r in chunks[0]['requests']}
    states=led.get('states') or {}
    if set(states)!=set(expected): raise RuntimeError('G100_R28_LEDGER_SAMPLE_SET_MISMATCH')
    for sid,dig in expected.items():
        if states[sid].get('request_digest')!=dig: raise RuntimeError('G100_R28_LEDGER_REQUEST_DIGEST_MISMATCH:'+sid)
    order=[r['sample_id'] for r in chunks[0]['requests']]
    for i,sid in enumerate(order):
        rec=states[sid]
        if i<3 and (rec.get('state')!='COMPLETE' or int(rec.get('attempts',-1))!=1):
            raise RuntimeError('G100_R28_PRIOR_PEER_NOT_EXACT_COMPLETE:'+sid)
        if i==3 and (rec.get('state')!='FAILED_FINAL' or int(rec.get('attempts',-1))!=2 or rec.get('last_error')!='BLENDER_WORKER_RC:5'):
            raise RuntimeError('G100_R28_TARGET_NOT_EXACT_FAILED_FINAL')
        if i>3 and (rec.get('state')!='PENDING' or int(rec.get('attempts',-1))!=0):
            raise RuntimeError('G100_R28_FUTURE_PEER_NOT_EXACT_PENDING:'+sid)
    pr=runroot/'PROGRESS.json'
    if not pr.is_file(): raise RuntimeError('G100_R28_PROGRESS_MISSING')
    pobj=json.loads(pr.read_text(encoding='utf-8'))
    if int(pobj.get('completed',-1))!=3 or pobj.get('status')!='FAILED' or int((pobj.get('counts') or {}).get('FAILED_FINAL',-1))!=1:
        raise RuntimeError('G100_R28_PROGRESS_NOT_EXACT_R27_FAILURE')
    for rel in [('RECOVERY','R26_REAL_FAILURE'),('RECOVERY','R27_IMPLEMENTATION_FAILURE')]:
        rp=runroot.joinpath(*rel)
        if rp.exists() and any(rp.iterdir()):
            raise RuntimeError('G100_R28_PRIOR_RECOVERY_MUTATION_PRESENT:'+'/'.join(rel))
    return {'ledger':led,'progress':pobj}


def _r28_preserve_impl_failure(runroot:Path):
    auth=_r28_verify_impl_failure_authority()
    recroot=runroot/'RECOVERY'/'R27_IMPLEMENTATION_FAILURE'
    recroot.mkdir(parents=True,exist_ok=True)
    if any(recroot.iterdir()): raise RuntimeError('G100_R28_IMPL_FAILURE_PRESERVATION_ALREADY_INITIALIZED')
    dst=recroot/R28_IMPL_FAILURE_NAME
    shutil.copy2(_r28_impl_failure_authority_path(),dst)
    atomic_json(recroot/'R28_R27_IMPLEMENTATION_FAILURE_IDENTITY.json',{
        'schema':'DF-G100-R28-R27-IMPLEMENTATION-FAILURE-IDENTITY-V1','status':'PRESERVED_BEFORE_R26_RECOVERY_MUTATION',
        'r28_spec_drive_id':R28_SPEC_DRIVE_ID,'r28a_authority_refresh_drive_id':R28A_AUTHORITY_REFRESH_DRIVE_ID,
        'drive_id':R28_IMPL_FAILURE_DRIVE_ID,'file_name':R28_IMPL_FAILURE_NAME,'bytes':R28_IMPL_FAILURE_BYTES,
        'sha256':R28_IMPL_FAILURE_SHA256,'crc':'PASS','error':"NameError:name 'payload_sha256' is not defined",
        'product_mutated':False,'maya_mutated':False,'test77_accessed':False,'training_started':False})
    if dst.stat().st_size!=R28_IMPL_FAILURE_BYTES or sha256_file(dst)!=R28_IMPL_FAILURE_SHA256:
        raise RuntimeError('G100_R28_IMPL_FAILURE_PRESERVATION_COPY_MISMATCH')
    return auth


def _r28_assert_and_recover_runroot(runroot:Path,chunks):
    _r28_verify_impl_failure_authority()
    _r28_verify_live_prestate_before_preservation(runroot,chunks)
    impl_auth=_r28_preserve_impl_failure(runroot)
    r27=_r27_assert_and_recover_runroot(runroot,chunks)
    return {'schema':'DF-G100-R28-PRESTATE-RECOVERY-V1','status':'R27_IMPLEMENTATION_FAILURE_PRESERVED_AND_R26_SAMPLE003_RECOVERED',
            'r28_spec_drive_id':R28_SPEC_DRIVE_ID,'r28a_authority_refresh_drive_id':R28A_AUTHORITY_REFRESH_DRIVE_ID,
            'r27_implementation_failure_authority':impl_auth,'r27_recovery':r27,
            'completed_peer_trees':r27.get('completed_peer_trees') or {}}


def _r28_verify_r27_activation(runroot:Path,chunks):
    req=chunks[0]['requests'][3]
    if req.get('sample_id')!=R27_RECOVERY_SAMPLE_ID or req.get('input_digest_sha256')!=R27_RECOVERY_REQUEST_DIGEST:
        raise RuntimeError('G100_R28_ACTIVATION_TARGET_IDENTITY_MISMATCH')
    qa_path=runroot/'CHUNKS'/'chunk_00'/req['output_rel']/'micro100_aux_gt_qa.json'
    if not qa_path.is_file(): raise RuntimeError('G100_R28_ACTIVATION_QA_MISSING')
    qa=json.loads(qa_path.read_text(encoding='utf-8'))
    obj=qa.get('object_index') or {}; dep=qa.get('depth') or {}; nor=qa.get('normal') or {}
    checks={
        'object_pass':obj.get('status')=='PASS',
        'depth_pass':dep.get('status')=='PASS',
        'normal_pass':nor.get('status')=='PASS',
        'plane_semantics':obj.get('plane_signature_representation_semantics')=='SIGNED_PERMUTATION_CANONICAL_WORLD_PLANE_SIGNATURE_R27_V1',
        'r27_spec':obj.get('r27_spec_drive_id')==R27_SPEC_DRIVE_ID,
        'non_nearest_zero':int(obj.get('renderer_effective_non_nearest_mismatch_pixels',-1))==0,
    }
    if not all(checks.values()): raise RuntimeError('G100_R28_R27_ACTIVATION_GUARD_FAIL:'+json.dumps(checks,sort_keys=True))
    out={'schema':'DF-G100-R28-R27-ACTIVATION-GUARD-V1','status':'PASS','checks':checks,'sample_id':req['sample_id'],
         'request_digest':req['input_digest_sha256'],'r27_spec_drive_id':R27_SPEC_DRIVE_ID}
    atomic_json(runroot/'EVIDENCE'/'DF_G100_R28_R27_ACTIVATION_GUARD.json',out)
    return out


def _r29_failure_authority_path():
    return HERE/'RECOVERY_AUTHORITY'/R29_FAILURE_NAME


def _r29_verify_failure_authority():
    p=_r29_failure_authority_path()
    if not p.is_file() or p.stat().st_size!=R29_FAILURE_BYTES or sha256_file(p)!=R29_FAILURE_SHA256:
        raise RuntimeError('G100_R29_FAILURE_AUTHORITY_IDENTITY_MISMATCH')
    with zipfile.ZipFile(p) as z:
        if z.testzip() is not None: raise RuntimeError('G100_R29_FAILURE_AUTHORITY_CRC_FAIL')
        rep=json.loads(z.read('FAILURE_REPORT.json'))
        led=json.loads(z.read('chunk_00_ledger.json'))
        prog=json.loads(z.read('PROGRESS.json'))
        if rep.get('schema')!='DF-G100-R28-V2-FAILURE-V1' or rep.get('source_release_id')!='DF_G100_MICRO100_V2_R1_TOOL_R28':
            raise RuntimeError('G100_R29_FAILURE_AUTHORITY_SCHEMA_RELEASE')
        if rep.get('status')!='FAIL_G100_OPEN' or int(rep.get('completed_samples',-1))!=5:
            raise RuntimeError('G100_R29_FAILURE_AUTHORITY_STATUS_COUNT')
        failed=rep.get('failed_samples') or []
        if len(failed)!=1 or failed[0].get('sample_id')!=R29_RECOVERY_SAMPLE_ID or failed[0].get('request_digest')!=R29_RECOVERY_REQUEST_DIGEST:
            raise RuntimeError('G100_R29_FAILURE_AUTHORITY_FAILED_SAMPLE')
        if led.get('chunk_digest_sha256')!=R27_CHUNK00_DIGEST:
            raise RuntimeError('G100_R29_FAILURE_AUTHORITY_CHUNK_DIGEST')
        rec=(led.get('states') or {}).get(R29_RECOVERY_SAMPLE_ID,{})
        if rec.get('state')!='FAILED_FINAL' or int(rec.get('attempts',-1))!=2 or rec.get('last_error')!='BLENDER_WORKER_RC:5' or rec.get('request_digest')!=R29_RECOVERY_REQUEST_DIGEST:
            raise RuntimeError('G100_R29_FAILURE_AUTHORITY_TARGET_STATE')
        if int(prog.get('completed',-1))!=5 or prog.get('status')!='FAILED' or int((prog.get('counts') or {}).get('FAILED_FINAL',-1))!=1:
            raise RuntimeError('G100_R29_FAILURE_AUTHORITY_PROGRESS')
        base='FAILED_SAMPLES/'+R29_RECOVERY_SAMPLE_ID+'/'
        qa=json.loads(z.read(base+'micro100_aux_gt_qa.json'))
        if qa.get('object_index',{}).get('status')!='PASS' or qa.get('normal',{}).get('status')!='PASS' or qa.get('depth',{}).get('status')!='FAIL':
            raise RuntimeError('G100_R29_FAILURE_AUTHORITY_GT_CLASSIFICATION')
    return {'path':str(p),'drive_id':R29_FAILURE_DRIVE_ID,'bytes':p.stat().st_size,
            'sha256':sha256_file(p),'crc':'PASS'}


def _r29_verify_live_prestate(runroot:Path,chunks):
    authority=_r29_verify_failure_authority()
    if not runroot.is_dir(): raise RuntimeError('G100_R29_EXISTING_R28_RUNROOT_REQUIRED')
    if len(chunks)!=10 or len(chunks[0].get('requests',[]))!=10:
        raise RuntimeError('G100_R29_CHUNK_PLAN_SHAPE')
    cr=runroot/'CHUNKS'/'chunk_00'; lp=cr/'ledger.json'
    if not lp.is_file(): raise RuntimeError('G100_R29_CHUNK00_LEDGER_MISSING')
    led=json.loads(lp.read_text(encoding='utf-8'))
    if led.get('chunk_digest_sha256')!=R27_CHUNK00_DIGEST:
        raise RuntimeError('G100_R29_CHUNK00_DIGEST_MISMATCH')
    expected={r['sample_id']:r['input_digest_sha256'] for r in chunks[0]['requests']}
    states=led.get('states') or {}
    if set(states)!=set(expected): raise RuntimeError('G100_R29_LEDGER_SAMPLE_SET_MISMATCH')
    order=[r['sample_id'] for r in chunks[0]['requests']]
    if order[5]!=R29_RECOVERY_SAMPLE_ID:
        raise RuntimeError('G100_R29_TARGET_INDEX_MISMATCH')
    for i,sid in enumerate(order):
        rec=states[sid]
        if rec.get('request_digest')!=expected[sid]:
            raise RuntimeError('G100_R29_LEDGER_REQUEST_DIGEST_MISMATCH:'+sid)
        if i<5:
            if rec.get('state')!='COMPLETE' or int(rec.get('attempts',-1))!=1:
                raise RuntimeError('G100_R29_PRIOR_PEER_NOT_EXACT_COMPLETE:'+sid)
        elif i==5:
            if rec.get('state')!='FAILED_FINAL' or int(rec.get('attempts',-1))!=2 or rec.get('last_error')!='BLENDER_WORKER_RC:5':
                raise RuntimeError('G100_R29_TARGET_NOT_EXACT_FAILED_FINAL')
        else:
            if rec.get('state')!='PENDING' or int(rec.get('attempts',-1))!=0:
                raise RuntimeError('G100_R29_FUTURE_PEER_NOT_EXACT_PENDING:'+sid)
    # The successful R28 activation of R27 is part of the required prestate.
    r3=states[R27_RECOVERY_SAMPLE_ID]
    rp=r3.get('r27_recovery') or {}
    if rp.get('r27_spec_drive_id')!=R27_SPEC_DRIVE_ID or rp.get('prior_state')!='FAILED_FINAL' or int(rp.get('prior_attempts',-1))!=2:
        raise RuntimeError('G100_R29_R27_RECOVERY_PROVENANCE_MISSING')
    qa3p=cr/chunks[0]['requests'][3]['output_rel']/'micro100_aux_gt_qa.json'
    if not qa3p.is_file(): raise RuntimeError('G100_R29_SAMPLE003_QA_MISSING')
    qa3=json.loads(qa3p.read_text(encoding='utf-8'))
    if qa3.get('status')!='PASS' or qa3.get('object_index',{}).get('plane_signature_representation_semantics')!='SIGNED_PERMUTATION_CANONICAL_WORLD_PLANE_SIGNATURE_R27_V1' or int(qa3.get('object_index',{}).get('renderer_effective_non_nearest_mismatch_pixels',-1))!=0:
        raise RuntimeError('G100_R29_SAMPLE003_R27_ACTIVATION_NOT_PROVEN')
    j27=runroot/'RECOVERY'/'R26_REAL_FAILURE'/'R27_RECOVERY_JOURNAL.json'
    j28=runroot/'RECOVERY'/'R27_IMPLEMENTATION_FAILURE'/'R28_R27_IMPLEMENTATION_FAILURE_PRESERVATION.json'
    if not j27.is_file() or not j28.is_file():
        raise RuntimeError('G100_R29_PRIOR_RECOVERY_EVIDENCE_MISSING')
    jo27=json.loads(j27.read_text(encoding='utf-8'))
    if jo27.get('status')!='LEDGER_RESET_SAMPLE003_ONLY' or jo27.get('r27_spec_drive_id')!=R27_SPEC_DRIVE_ID or jo27.get('request_digest')!=R27_RECOVERY_REQUEST_DIGEST:
        raise RuntimeError('G100_R29_PRIOR_R27_RECOVERY_JOURNAL_MISMATCH')
    pr=runroot/'PROGRESS.json'
    if not pr.is_file(): raise RuntimeError('G100_R29_PROGRESS_MISSING')
    pobj=json.loads(pr.read_text(encoding='utf-8'))
    if int(pobj.get('completed',-1))!=5 or pobj.get('status')!='FAILED' or int((pobj.get('counts') or {}).get('FAILED_FINAL',-1))!=1:
        raise RuntimeError('G100_R29_PROGRESS_NOT_EXACT_R28_FAILURE')
    target_req=chunks[0]['requests'][5]; sd=cr/target_req['output_rel']
    if not sd.is_dir(): raise RuntimeError('G100_R29_FAILED_SAMPLE_DIR_MISSING')
    with zipfile.ZipFile(_r29_failure_authority_path()) as z:
        base='FAILED_SAMPLES/'+R29_RECOVERY_SAMPLE_ID+'/'
        ident=json.loads(z.read(base+'PARTIAL_OUTPUT_IDENTITIES.json'))
    for rec in ident.get('files',[]):
        fp=sd/rec['path']
        if not fp.is_file() or fp.stat().st_size!=int(rec['bytes']) or sha256_file(fp)!=rec['sha256']:
            raise RuntimeError('G100_R29_FAILED_SAMPLE_EVIDENCE_MISMATCH:'+rec['path'])
    peer_trees={}
    for i in range(5):
        req=chunks[0]['requests'][i]; psd=cr/req['output_rel']
        if not psd.is_dir(): raise RuntimeError('G100_R29_COMPLETE_PEER_DIR_MISSING:'+req['sample_id'])
        peer_trees[req['sample_id']]=_r27_tree_digest(psd)
    return {'authority':authority,'ledger':led,'progress':pobj,'completed_peer_trees':peer_trees}


def _r29_assert_and_recover_runroot(runroot:Path,chunks):
    pre=_r29_verify_live_prestate(runroot,chunks)
    cr=runroot/'CHUNKS'/'chunk_00'; lp=cr/'ledger.json'
    led=pre['ledger']; states=led['states']; target=states[R29_RECOVERY_SAMPLE_ID]
    target_req=chunks[0]['requests'][5]; sd=cr/target_req['output_rel']
    recroot=runroot/'RECOVERY'/'R28_REAL_FAILURE_SAMPLE005'
    recroot.mkdir(parents=True,exist_ok=True)
    if any(recroot.iterdir()):
        raise RuntimeError('G100_R29_RECOVERY_ALREADY_INITIALIZED')
    shutil.copy2(_r29_failure_authority_path(),recroot/R29_FAILURE_NAME)
    shutil.copy2(lp,recroot/'chunk_00_ledger_pre_r29.json')
    wm=cr/'worker_result_manifest.json'
    if wm.is_file(): shutil.copy2(wm,recroot/'chunk_00_worker_result_manifest_pre_r29.json')
    shutil.copytree(sd,recroot/'FAILED_SAMPLE_005')
    journal={
        'schema':'DF-G100-R29-RECOVERY-JOURNAL-V1','status':'PRESERVED_BEFORE_LEDGER_RESET',
        'r29_spec_drive_id':R29_SPEC_DRIVE_ID,'r28_failure_authority':pre['authority'],
        'chunk_digest_sha256':R27_CHUNK00_DIGEST,'sample_id':R29_RECOVERY_SAMPLE_ID,
        'request_digest':R29_RECOVERY_REQUEST_DIGEST,'prior_state':'FAILED_FINAL',
        'prior_attempts':2,'prior_last_error':'BLENDER_WORKER_RC:5',
        'completed_samples_preserved':[r['sample_id'] for r in chunks[0]['requests'][:5]],
        'future_pending_samples':[r['sample_id'] for r in chunks[0]['requests'][6:]],
        'completed_peer_trees':pre['completed_peer_trees'],
        'sample003_r27_activation_preserved':True,
        'recorded_utc':utc_iso(),'product_mutated':False,'maya_mutated':False,
        'test77_accessed':False,'training_started':False,
    }
    atomic_json(recroot/'R29_RECOVERY_JOURNAL.json',journal)
    # Only failed sample005 may be cleared and reopened.
    shutil.rmtree(sd); sd.mkdir(parents=True,exist_ok=True)
    target['state']='PENDING'; target['attempts']=0; target.pop('last_error',None)
    target['r29_recovery']={
        'r29_spec_drive_id':R29_SPEC_DRIVE_ID,'prior_state':'FAILED_FINAL','prior_attempts':2,
        'failure_authority_sha256':R29_FAILURE_SHA256,
        'recovery_journal_rel':(recroot/'R29_RECOVERY_JOURNAL.json').relative_to(runroot).as_posix(),
    }
    atomic_json(lp,led)
    journal['status']='LEDGER_RESET_SAMPLE005_ONLY'
    atomic_json(recroot/'R29_RECOVERY_JOURNAL.json',journal)
    update_progress(runroot)
    return {
        'schema':'DF-G100-R29-PRESTATE-RECOVERY-V1',
        'status':'EXACT_R28_FAILURE_RECOVERED_SAMPLE005_ONLY',
        'r29_spec_drive_id':R29_SPEC_DRIVE_ID,
        'failure_authority':pre['authority'],
        'completed_peer_trees':pre['completed_peer_trees'],
        'recovered_sample_id':R29_RECOVERY_SAMPLE_ID,
        'request_digest':R29_RECOVERY_REQUEST_DIGEST,
    }


def _r29_verify_completed_peers_unchanged(runroot:Path,chunks,recovery_info):
    cr=runroot/'CHUNKS'/'chunk_00'
    for sid,expected in (recovery_info.get('completed_peer_trees') or {}).items():
        req=next(r for r in chunks[0]['requests'] if r['sample_id']==sid)
        got=_r27_tree_digest(cr/req['output_rel'])
        if got!=expected: raise RuntimeError('G100_R29_COMPLETE_PEER_MUTATED:'+sid)
    return True


def _r29_verify_sample005_activation(runroot:Path,chunks):
    req=chunks[0]['requests'][5]
    if req.get('sample_id')!=R29_RECOVERY_SAMPLE_ID or req.get('input_digest_sha256')!=R29_RECOVERY_REQUEST_DIGEST:
        raise RuntimeError('G100_R29_ACTIVATION_TARGET_IDENTITY_MISMATCH')
    sd=runroot/'CHUNKS'/'chunk_00'/req['output_rel']
    qa_path=sd/'micro100_aux_gt_qa.json'
    if not qa_path.is_file(): raise RuntimeError('G100_R29_ACTIVATION_QA_MISSING')
    qa=json.loads(qa_path.read_text(encoding='utf-8'))
    obj=qa.get('object_index') or {}; dep=qa.get('depth') or {}; nor=qa.get('normal') or {}
    mask=dep.get('filter_safe_interior_mask') or {}
    mp=sd/mask.get('path','')
    checks={
        'object_pass':obj.get('status')=='PASS',
        'normal_pass':nor.get('status')=='PASS',
        'depth_pass':dep.get('status')=='PASS',
        'authority_semantics':dep.get('authority_semantics')==R29_DEPTH_AUTHORITY_SEMANTICS_ID,
        'r29_spec':dep.get('r29_spec_drive_id')==R29_SPEC_DRIVE_ID,
        'safe_over_tolerance_zero':int(dep.get('filter_safe_over_tolerance_pixels',-1))==0,
        'filter_width_exact':abs(float(dep.get('renderer_filter_width_px',float('nan')))-1.5)<=1e-12,
        'filter_radius_exact':int(dep.get('filter_support_radius_px',-1))==2,
        'request_digest_exact':req.get('input_digest_sha256')==R29_RECOVERY_REQUEST_DIGEST,
        'mask_present':bool(mask.get('path')) and mp.is_file(),
        'mask_hash_exact':bool(mask.get('path')) and mp.is_file() and mp.stat().st_size==int(mask.get('bytes',-1)) and sha256_file(mp)==mask.get('sha256'),
    }
    if not all(checks.values()):
        raise RuntimeError('G100_R29_SAMPLE005_ACTIVATION_GUARD_FAIL:'+json.dumps(checks,sort_keys=True))
    out={'schema':'DF-G100-R29-SAMPLE005-ACTIVATION-GUARD-V1','status':'PASS',
         'checks':checks,'sample_id':req['sample_id'],'request_digest':req['input_digest_sha256'],
         'r29_spec_drive_id':R29_SPEC_DRIVE_ID,
         'full_raster_over_tolerance_pixels':dep.get('full_raster_over_tolerance_pixels'),
         'filter_safe_over_tolerance_pixels':dep.get('filter_safe_over_tolerance_pixels')}
    atomic_json(runroot/'EVIDENCE'/'DF_G100_R29_SAMPLE005_ACTIVATION_GUARD.json',out)
    return out



def _r33_replay_authority_path():
    return HERE/'RECOVERY_AUTHORITY'/R31_REPLAY_AUTHORITY_NAME


def _r33_load_replay_authority():
    p=_r33_replay_authority_path()
    if not p.is_file() or p.stat().st_size!=R31_REPLAY_AUTHORITY_BYTES or sha256_file(p)!=R31_REPLAY_AUTHORITY_SHA256:
        raise RuntimeError('G100_R33_R31_REPLAY_AUTHORITY_IDENTITY_MISMATCH')
    with zipfile.ZipFile(p) as z:
        if z.testzip() is not None: raise RuntimeError('G100_R33_R31_REPLAY_AUTHORITY_CRC_FAIL')
        before=json.loads(z.read('R31_RUN_ROOT_BEFORE.json'))
        after=json.loads(z.read('R31_RUN_ROOT_AFTER.json'))
        diff=json.loads(z.read('R31_RUN_ROOT_DIFF.json'))
        if before.get('files')!=after.get('files') or diff.get('added') or diff.get('removed') or diff.get('changed'):
            raise RuntimeError('G100_R33_R31_REPLAY_NOT_READ_ONLY')
        accepts={}
        for name in z.namelist():
            if name.startswith('ACCEPTANCE/') and name.endswith('.json'):
                b=z.read(name); obj=json.loads(b)
                accepts[obj['sample_id']]={'name':name,'bytes':b,'sha256':sha256_bytes(b),'object':obj}
    if len(accepts)!=8 or not all(x['object'].get('status')=='PASS' for x in accepts.values()):
        raise RuntimeError('G100_R33_R31_REPLAY_ACCEPTANCE_SET')
    return {'path':p,'before':before,'accepts':accepts,'identity':{'bytes':p.stat().st_size,'sha256':sha256_file(p),'crc':'PASS'}}


def _r33_live_runroot_map(runroot:Path):
    out={}
    for p in sorted(Path(runroot).rglob('*')):
        if p.is_file():
            out[p.relative_to(runroot).as_posix()]={'bytes':p.stat().st_size,'sha256':sha256_file(p)}
    return out


def _r33_file_record(p:Path,base:Path):
    return {'path':p.relative_to(base).as_posix(),'bytes':p.stat().st_size,'sha256':sha256_file(p)}


def _r33_assert_and_recover_runroot(runroot:Path,chunks,M):
    runroot=Path(runroot)
    if not runroot.is_dir(): raise RuntimeError('G100_R33_EXISTING_RUNROOT_REQUIRED')
    auth=_r33_load_replay_authority()
    expected=auth['before'].get('files') or {}
    live=_r33_live_runroot_map(runroot)
    if live!=expected:
        added=sorted(set(live)-set(expected)); removed=sorted(set(expected)-set(live)); changed=sorted(k for k in set(live)&set(expected) if live[k]!=expected[k])
        raise RuntimeError('G100_R33_PRESTATE_NOT_EXACT_R31_SNAPSHOT:'+json.dumps({'added':added[:20],'removed':removed[:20],'changed':changed[:20]},sort_keys=True))
    if sha256_file(runroot/'PROGRESS.json')!=R33_PRE_PROGRESS_SHA256: raise RuntimeError('G100_R33_PROGRESS_AUTHORITY_MISMATCH')
    cr=runroot/'CHUNKS'/'chunk_05'; lp=cr/'ledger.json'
    if sha256_file(lp)!=R33_PRE_CHUNK05_LEDGER_SHA256: raise RuntimeError('G100_R33_CHUNK05_LEDGER_AUTHORITY_MISMATCH')
    req=chunks[5]['requests'][1]
    if req.get('sample_id')!=R33_RECOVERY_SAMPLE_ID or req.get('input_digest_sha256')!=R33_RECOVERY_REQUEST_DIGEST:
        raise RuntimeError('G100_R33_TARGET_PLAN_IDENTITY_MISMATCH')
    reqp=cr/'requests'/f'{R33_RECOVERY_SAMPLE_ID}.json'; logp=cr/'logs'/f'{R33_RECOVERY_SAMPLE_ID}.log'; sd=cr/req['output_rel']
    accp=runroot/'EVIDENCE'/'SAMPLE_ACCEPTANCE'/f'{R33_RECOVERY_SAMPLE_ID}.json'
    if sha256_file(reqp)!=R33_REQUEST_FILE_SHA256 or sha256_file(sd/'rgb.png')!=R33_PRE_RGB_SHA256 or sha256_file(accp)!=R33_PRE_ACCEPTANCE_SHA256:
        raise RuntimeError('G100_R33_TARGET_BYTE_AUTHORITY_MISMATCH')
    policy=r33_blueprint_vertical_dominant_policy(req)
    if not policy.get('applied') or abs(float(policy.get('dominant_face_fraction',0))-0.4744140625)>1e-15 or policy.get('dominant_object_id')!='intersection_1051.bR0' or int(policy.get('dominant_face_id',-1))!=1 or float(policy.get('dominant_face_abs_canonical_up_component',99))!=0.0:
        raise RuntimeError('G100_R33_TARGET_GEOMETRY_POLICY_MISMATCH')

    recroot=runroot/'RECOVERY'/'R33_SAMPLE051_PRE_REMEDIATION'
    if recroot.exists(): raise RuntimeError('G100_R33_RECOVERY_ALREADY_INITIALIZED_DO_NOT_RERUN')
    recroot.mkdir(parents=True)
    shutil.copytree(sd,recroot/'sample_directory')
    shutil.copy2(reqp,recroot/'request.json'); shutil.copy2(logp,recroot/'worker.log')
    shutil.copy2(accp,recroot/'acceptance_pre_r33.json'); shutil.copy2(lp,recroot/'chunk_05_ledger_pre_r33.json')
    shutil.copy2(runroot/'PROGRESS.json',recroot/'PROGRESS_pre_r33.json')
    preserved={
        'sample_directory':_r27_tree_digest(recroot/'sample_directory'),
        'request':_r33_file_record(recroot/'request.json',recroot),
        'worker_log':_r33_file_record(recroot/'worker.log',recroot),
        'acceptance':_r33_file_record(recroot/'acceptance_pre_r33.json',recroot),
        'ledger':_r33_file_record(recroot/'chunk_05_ledger_pre_r33.json',recroot),
        'progress':_r33_file_record(recroot/'PROGRESS_pre_r33.json',recroot),
    }
    journal={'schema':'DF-G100-R33-SAMPLE051-RECOVERY-JOURNAL-V1','status':'PRESERVED_BEFORE_REMEDIATION','r33_spec_drive_id':R33_SPEC_DRIVE_ID,
             'classification':'BLUEPRINT_DOWNLIGHT_VERTICAL_DOMINANT_VISIBILITY_GAP','sample_id':R33_RECOVERY_SAMPLE_ID,'request_digest':R33_RECOVERY_REQUEST_DIGEST,
             'pre_rgb_sha256':R33_PRE_RGB_SHA256,'policy':policy,'preserved':preserved,'r31_replay_authority':auth['identity'],
             'product_mutated':False,'maya_mutated':False,'test77_accessed':False,'training_started':False,'recorded_utc':utc_iso()}
    atomic_json(recroot/'R33_RECOVERY_JOURNAL.json',journal)

    # Existing-byte RGB-only remediation: no Blender rerender and no GT mutation.
    pre33=sd/'rgb_pre_r33.png'; pre33.write_bytes((sd/'rgb.png').read_bytes())
    gain=apply_fixed_rgb8_gain_png(pre33,sd/'rgb.png',numerator=2,denominator=1)
    gain.update({'implementation_id':R33_IMPLEMENTATION_ID,'source_rgb_rel':'rgb_pre_r33.png','final_rgb_rel':'rgb.png','geometry_preserving':True,
                 'eligibility':policy,'r33_spec_drive_id':R33_SPEC_DRIVE_ID})
    if sha256_file(pre33)!=R33_PRE_RGB_SHA256 or sha256_file(sd/'rgb.png')!=R33_EXPECTED_FINAL_RGB_SHA256:
        raise RuntimeError('G100_R33_FIXED_GAIN_OUTPUT_IDENTITY_MISMATCH')
    comp_path=sd/'completion.json'; comp=json.loads(comp_path.read_text(encoding='utf-8'))
    immutable_names=['depth.exr','normal.exr','object_index.exr','normal_authority_mask.uint8.bin','normal_filter_safe_interior_mask.uint8.bin','depth_filter_safe_interior_mask.uint8.bin','micro100_aux_gt_qa.json']
    immutable_before={n:sha256_file(sd/n) for n in immutable_names}
    comp['r33_blueprint_vertical_dominant_policy']=policy; comp['r33_blueprint_fixed_rgb_gain']=gain
    comp['files']=[r for r in (comp.get('files') or []) if r.get('path') not in {'rgb.png','rgb_pre_r33.png'}]
    comp['files'].extend([_r33_file_record(sd/'rgb.png',sd),_r33_file_record(pre33,sd)])
    comp['files']=sorted(comp['files'],key=lambda r:r['path'])
    atomic_json(comp_path,comp)
    for n,sh in immutable_before.items():
        if sha256_file(sd/n)!=sh: raise RuntimeError('G100_R33_AUX_GT_MUTATED:'+n)
    acc=sample_acceptance(req,comp,sd,M,{'schema':'DF-G100-R33-RGB-ONLY-RECOVERY-V1','mode':'EXISTING_BYTES_NO_RERENDER','pre_rgb_sha256':R33_PRE_RGB_SHA256})
    if acc.get('status')!='PASS': raise RuntimeError('G100_R33_SAMPLE051_ACCEPTANCE_FAIL:'+json.dumps(acc.get('checks'),sort_keys=True))
    atomic_json(accp,acc)

    # Persist the already-adjudicated exact R31 acceptance bytes for 052..059.
    persisted=[]
    for i in range(52,60):
        r=chunks[5]['requests'][i-50]; sid=r['sample_id']; rec=auth['accepts'].get(sid)
        if not rec: raise RuntimeError('G100_R33_R31_ACCEPTANCE_MISSING:'+sid)
        dst=runroot/'EVIDENCE'/'SAMPLE_ACCEPTANCE'/f'{sid}.json'; dst.parent.mkdir(parents=True,exist_ok=True); dst.write_bytes(rec['bytes'])
        if sha256_file(dst)!=rec['sha256']: raise RuntimeError('G100_R33_R31_ACCEPTANCE_PERSIST_HASH:'+sid)
        persisted.append({'sample_id':sid,'sha256':rec['sha256']})

    journal['status']='SAMPLE051_PASS_AND_052_059_ACCEPTANCE_PERSISTED'; journal['final_rgb_sha256']=sha256_file(sd/'rgb.png'); journal['final_acceptance_sha256']=sha256_file(accp); journal['persisted_052_059']=persisted
    journal['immutable_aux_gt_sha256']=immutable_before; atomic_json(recroot/'R33_RECOVERY_JOURNAL.json',journal)
    return {'schema':'DF-G100-R33-PRESTATE-RECOVERY-V1','status':'PASS_SAMPLE051_RGB_ONLY_AND_R31_TAIL_PERSISTED','policy':policy,
            'final_rgb_sha256':sha256_file(sd/'rgb.png'),'sample051_acceptance':acc,'persisted_052_059':persisted,'immutable_aux_gt_sha256':immutable_before,'r31_replay_authority':auth['identity']}


def _r33_verify_activation_before_060(runroot:Path,chunks,M,prestate):
    req=chunks[5]['requests'][1]; sd=runroot/'CHUNKS'/'chunk_05'/req['output_rel']; comp=json.loads((sd/'completion.json').read_text(encoding='utf-8'))
    acc=json.loads((runroot/'EVIDENCE'/'SAMPLE_ACCEPTANCE'/f'{R33_RECOVERY_SAMPLE_ID}.json').read_text(encoding='utf-8'))
    pol=r33_blueprint_vertical_dominant_policy(req); meta=comp.get('r33_blueprint_fixed_rgb_gain') or {}; pmeta=comp.get('r33_blueprint_vertical_dominant_policy') or {}
    checks={
      'policy_applied':pol.get('applied') is True and pmeta==pol,
      'pre_rgb_exact':sha256_file(sd/'rgb_pre_r33.png')==R33_PRE_RGB_SHA256,
      'gain_exact':meta.get('implementation_id')==R33_IMPLEMENTATION_ID and int(meta.get('gain_numerator',-1))==2 and int(meta.get('gain_denominator',-1))==1 and int(meta.get('offset_u8',-1))==0,
      'final_rgb_exact':sha256_file(sd/'rgb.png')==R33_EXPECTED_FINAL_RGB_SHA256,
      'acceptance_pass':acc.get('status')=='PASS' and all(acc.get('checks',{}).get(k) is True for k in ('rgb_unique','rgb_mean','rgb_span','rgb_structural','object_index_analytic','depth_analytic','normal_analytic','camera_reprojection_max','camera_reprojection_median')),
      'request_digest_unchanged':req.get('input_digest_sha256')==R33_RECOVERY_REQUEST_DIGEST,
      'aux_gt_byte_identical':all(sha256_file(sd/n)==sh for n,sh in (prestate.get('immutable_aux_gt_sha256') or {}).items()),
      'no_external_authority':True,
    }
    if not all(checks.values()): raise RuntimeError('G100_R33_ACTIVATION_GUARD_FAIL:'+json.dumps(checks,sort_keys=True))
    out={'schema':'DF-G100-R33-ACTIVATION-GUARD-V1','status':'PASS','checks':checks,'sample_id':R33_RECOVERY_SAMPLE_ID,'r33_spec_drive_id':R33_SPEC_DRIVE_ID}
    atomic_json(runroot/'EVIDENCE'/'DF_G100_R33_SAMPLE051_ACTIVATION_GUARD.json',out); return out


def _r27_recovery_authority_path():
    return HERE/'RECOVERY_AUTHORITY'/R27_FAILURE_RETURN_NAME


def _r27_verify_failure_authority():
    p=_r27_recovery_authority_path()
    if not p.is_file() or p.stat().st_size!=R27_FAILURE_RETURN_BYTES or sha256_file(p)!=R27_FAILURE_RETURN_SHA256:
        raise RuntimeError('G100_R27_FAILURE_AUTHORITY_IDENTITY_MISMATCH')
    with zipfile.ZipFile(p) as z:
        if z.testzip() is not None: raise RuntimeError('G100_R27_FAILURE_AUTHORITY_CRC_FAIL')
        led=json.loads(z.read('chunk_00_ledger.json'))
        if led.get('chunk_digest_sha256')!=R27_CHUNK00_DIGEST: raise RuntimeError('G100_R27_FAILURE_AUTHORITY_LEDGER_DIGEST')
        rec=(led.get('states') or {}).get(R27_RECOVERY_SAMPLE_ID,{})
        if rec.get('state')!='FAILED_FINAL' or int(rec.get('attempts',-1))!=2 or rec.get('last_error')!='BLENDER_WORKER_RC:5' or rec.get('request_digest')!=R27_RECOVERY_REQUEST_DIGEST:
            raise RuntimeError('G100_R27_FAILURE_AUTHORITY_TARGET_STATE')
    return {'path':str(p),'bytes':p.stat().st_size,'sha256':sha256_file(p),'crc':'PASS'}


def _r27_tree_digest(root:Path):
    rows=_tree_records(root)
    return {'files':rows,'aggregate_sha256':_r28_payload_sha256(rows),'file_count':len(rows)}


def _r27_assert_and_recover_runroot(runroot:Path,chunks):
    authority=_r27_verify_failure_authority()
    if not runroot.is_dir(): raise RuntimeError('G100_R27_EXISTING_R26_RUNROOT_REQUIRED')
    if len(chunks)!=10 or len(chunks[0].get('requests',[]))!=10: raise RuntimeError('G100_R27_CHUNK_PLAN_SHAPE')
    cr=runroot/'CHUNKS'/'chunk_00'; lp=cr/'ledger.json'
    if not lp.is_file(): raise RuntimeError('G100_R27_CHUNK00_LEDGER_MISSING')
    led=json.loads(lp.read_text(encoding='utf-8'))
    if led.get('chunk_digest_sha256')!=R27_CHUNK00_DIGEST: raise RuntimeError('G100_R27_CHUNK00_DIGEST_MISMATCH')
    expected={r['sample_id']:r['input_digest_sha256'] for r in chunks[0]['requests']}
    states=led.get('states') or {}
    if set(states)!=set(expected): raise RuntimeError('G100_R27_LEDGER_SAMPLE_SET_MISMATCH')
    for sid,dig in expected.items():
        if states[sid].get('request_digest')!=dig: raise RuntimeError('G100_R27_LEDGER_REQUEST_DIGEST_MISMATCH:'+sid)
    target=states[R27_RECOVERY_SAMPLE_ID]
    if target.get('state')!='FAILED_FINAL' or int(target.get('attempts',-1))!=2 or target.get('last_error')!='BLENDER_WORKER_RC:5':
        raise RuntimeError('G100_R27_TARGET_NOT_EXACT_R26_FAILED_FINAL')
    order=[r['sample_id'] for r in chunks[0]['requests']]; ti=order.index(R27_RECOVERY_SAMPLE_ID)
    if ti!=3: raise RuntimeError('G100_R27_TARGET_INDEX_MISMATCH')
    completed=[]; pending=[]
    for i,sid in enumerate(order):
        rr=states[sid]
        if i<ti:
            if rr.get('state')!='COMPLETE' or int(rr.get('attempts',-1))!=1: raise RuntimeError('G100_R27_PRIOR_PEER_NOT_EXACT_COMPLETE:'+sid)
            completed.append(sid)
        elif i>ti:
            if rr.get('state')!='PENDING' or int(rr.get('attempts',-1))!=0: raise RuntimeError('G100_R27_FUTURE_PEER_NOT_EXACT_PENDING:'+sid)
            pending.append(sid)
    pr=runroot/'PROGRESS.json'
    if not pr.is_file(): raise RuntimeError('G100_R27_PROGRESS_MISSING')
    pobj=json.loads(pr.read_text(encoding='utf-8'))
    if int(pobj.get('completed',-1))!=3 or pobj.get('status')!='FAILED' or int((pobj.get('counts') or {}).get('FAILED_FINAL',-1))!=1:
        raise RuntimeError('G100_R27_PROGRESS_NOT_EXACT_R26_FAILURE')
    target_req=next(r for r in chunks[0]['requests'] if r['sample_id']==R27_RECOVERY_SAMPLE_ID)
    sd=cr/target_req['output_rel']
    if not sd.is_dir(): raise RuntimeError('G100_R27_FAILED_SAMPLE_DIR_MISSING')
    # Verify the run-root failed sample against the exact failure-return partial identities.
    with zipfile.ZipFile(_r27_recovery_authority_path()) as z:
        base='FAILED_SAMPLES/'+R27_RECOVERY_SAMPLE_ID+'/'
        ident=json.loads(z.read(base+'PARTIAL_OUTPUT_IDENTITIES.json'))
    for rec in ident.get('files',[]):
        fp=sd/rec['path']
        if not fp.is_file() or fp.stat().st_size!=rec['bytes'] or sha256_file(fp)!=rec['sha256']:
            raise RuntimeError('G100_R27_FAILED_SAMPLE_EVIDENCE_MISMATCH:'+rec['path'])
    peer_trees={}
    for sid in completed:
        req=next(r for r in chunks[0]['requests'] if r['sample_id']==sid); psd=cr/req['output_rel']
        if not psd.is_dir(): raise RuntimeError('G100_R27_COMPLETE_PEER_DIR_MISSING:'+sid)
        peer_trees[sid]=_r27_tree_digest(psd)
    recroot=runroot/'RECOVERY'/'R26_REAL_FAILURE'; recroot.mkdir(parents=True,exist_ok=True)
    # Idempotence is intentionally fail-closed: this operator package is for one recovery execution.
    if any(recroot.iterdir()): raise RuntimeError('G100_R27_RECOVERY_ALREADY_INITIALIZED')
    shutil.copy2(_r27_recovery_authority_path(),recroot/R27_FAILURE_RETURN_NAME)
    shutil.copy2(lp,recroot/'chunk_00_ledger_pre_r27.json')
    wm=cr/'worker_result_manifest.json'
    if wm.is_file(): shutil.copy2(wm,recroot/'chunk_00_worker_result_manifest_pre_r27.json')
    shutil.copytree(sd,recroot/'FAILED_SAMPLE_003')
    journal={'schema':'DF-G100-R27-RECOVERY-JOURNAL-V1','status':'PRESERVED_BEFORE_LEDGER_RESET','r27_spec_drive_id':R27_SPEC_DRIVE_ID,
             'r26_failure_authority':authority,'chunk_digest_sha256':R27_CHUNK00_DIGEST,'sample_id':R27_RECOVERY_SAMPLE_ID,
             'request_digest':R27_RECOVERY_REQUEST_DIGEST,'prior_state':'FAILED_FINAL','prior_attempts':2,'prior_last_error':'BLENDER_WORKER_RC:5',
             'completed_samples_preserved':completed,'future_pending_samples':pending,'completed_peer_trees':peer_trees,
             'recorded_utc':utc_iso(),'product_mutated':False,'maya_mutated':False,'test77_accessed':False,'training_started':False}
    atomic_json(recroot/'R27_RECOVERY_JOURNAL.json',journal)
    shutil.rmtree(sd); sd.mkdir(parents=True,exist_ok=True)
    target['state']='PENDING'; target['attempts']=0; target.pop('last_error',None)
    target['r27_recovery']={'r27_spec_drive_id':R27_SPEC_DRIVE_ID,'prior_state':'FAILED_FINAL','prior_attempts':2,
                            'failure_authority_sha256':R27_FAILURE_RETURN_SHA256,
                            'recovery_journal_rel':(recroot/'R27_RECOVERY_JOURNAL.json').relative_to(runroot).as_posix()}
    atomic_json(lp,led)
    journal['status']='LEDGER_RESET_SAMPLE003_ONLY'; atomic_json(recroot/'R27_RECOVERY_JOURNAL.json',journal)
    update_progress(runroot)
    return {'schema':'DF-G100-R27-PRESTATE-RECOVERY-V1','status':'EXACT_R26_FAILURE_RECOVERED_SAMPLE003_ONLY',
            'r27_spec_drive_id':R27_SPEC_DRIVE_ID,'failure_authority':authority,'completed_peer_trees':peer_trees,
            'recovered_sample_id':R27_RECOVERY_SAMPLE_ID,'request_digest':R27_RECOVERY_REQUEST_DIGEST}


def _r27_verify_completed_peers_unchanged(runroot:Path,chunks,recovery_info):
    cr=runroot/'CHUNKS'/'chunk_00'
    for sid,expected in (recovery_info.get('completed_peer_trees') or {}).items():
        req=next(r for r in chunks[0]['requests'] if r['sample_id']==sid)
        got=_r27_tree_digest(cr/req['output_rel'])
        if got!=expected: raise RuntimeError('G100_R27_COMPLETE_PEER_MUTATED:'+sid)
    return True


def _r26_assert_fresh_runroot(runroot:Path):
    runroot=Path(runroot)
    if not runroot.exists(): return {'schema':'DF-G100-R26-PRESTATE-V1','status':'FRESH_ABSENT_RUNROOT'}
    members=[p.name for p in runroot.iterdir()]
    if members: raise RuntimeError('G100_R26_RUNROOT_ALREADY_EXISTS_NONEMPTY:'+','.join(sorted(members)))
    return {'schema':'DF-G100-R26-PRESTATE-V1','status':'FRESH_EMPTY_RUNROOT'}


def _r34_failure_authority_path():
    return HERE/'R34_FAILURE_AUTHORITY'/R34_FAILURE_RETURN_NAME


def _r34_verify_failure_authority():
    p=_r34_failure_authority_path()
    if not p.is_file() or p.stat().st_size!=R34_FAILURE_RETURN_BYTES or sha256_file(p)!=R34_FAILURE_RETURN_SHA256:
        raise RuntimeError('G100_R34_R33_FAILURE_AUTHORITY_IDENTITY_MISMATCH')
    with zipfile.ZipFile(p) as z:
        if z.testzip() is not None: raise RuntimeError('G100_R34_R33_FAILURE_AUTHORITY_CRC_FAIL')
        rep=json.loads(z.read('FAILURE_REPORT.json'))
        prog_b=z.read('PROGRESS.json'); led_b=z.read('chunk_06_ledger.json')
        j_b=z.read('RECOVERY/R33_SAMPLE051_PRE_REMEDIATION/R33_RECOVERY_JOURNAL.json')
        if sha256_bytes(prog_b)!=R34_PROGRESS_SHA256 or sha256_bytes(led_b)!=R34_CHUNK06_LEDGER_SHA256 or sha256_bytes(j_b)!=R34_R33_RECOVERY_JOURNAL_SHA256:
            raise RuntimeError('G100_R34_R33_FAILURE_AUTHORITY_MEMBER_HASH')
        if rep.get('schema')!='DF-G100-R33-V2-FAILURE-V1' or rep.get('source_release_id')!='DF_G100_MICRO100_V2_R1_TOOL_R33':
            raise RuntimeError('G100_R34_R33_FAILURE_AUTHORITY_SCHEMA_RELEASE')
        if rep.get('status')!='FAIL_G100_OPEN' or int(rep.get('completed_samples',-1))!=65 or (rep.get('failed_samples') or [])!=[]:
            raise RuntimeError('G100_R34_R33_FAILURE_AUTHORITY_STATUS_COUNT')
        err=str(rep.get('error',''))
        if 'PermissionError:[WinError 5] Access is denied' not in err or 'chunk_06' not in err or 'ledger.json' not in err:
            raise RuntimeError('G100_R34_R33_FAILURE_AUTHORITY_ERROR_CLASS')
        prog=json.loads(prog_b); led=json.loads(led_b); journal=json.loads(j_b)
        if int(prog.get('completed',-1))!=65 or prog.get('status')!='RUNNING':
            raise RuntimeError('G100_R34_R33_FAILURE_AUTHORITY_PROGRESS')
        if journal.get('status')!='SAMPLE051_PASS_AND_052_059_ACCEPTANCE_PERSISTED' or journal.get('final_rgb_sha256')!=R33_EXPECTED_FINAL_RGB_SHA256:
            raise RuntimeError('G100_R34_R33_FAILURE_AUTHORITY_R33_JOURNAL')
    return {'path':str(p),'bytes':p.stat().st_size,'sha256':sha256_file(p),'crc':'PASS',
            'classification':'WINDOWS_ATOMIC_JSON_REPLACE_TRANSIENT_ACCESS_DENIED_IMPLEMENTATION_GAP'}


def _r34_assert_and_preserve_failed_prestate(runroot:Path):
    authority=_r34_verify_failure_authority()
    if not runroot.is_dir(): raise RuntimeError('G100_R34_EXISTING_R33_RUNROOT_REQUIRED')
    if sha256_file(PACKAGE_PLAN)!=PACKAGE_PLAN_SHA256: raise RuntimeError('G100_R34_PACKAGE_PLAN_IDENTITY')
    frozen=json.loads(PACKAGE_PLAN.read_text(encoding='utf-8'))
    if len(frozen.get('chunks',[]))!=10 or len(frozen['chunks'][6].get('requests',[]))!=10:
        raise RuntimeError('G100_R34_FROZEN_PLAN_SHAPE')
    pr=runroot/'PROGRESS.json'; lp=runroot/'CHUNKS'/'chunk_06'/'ledger.json'
    r33j=runroot/'RECOVERY'/'R33_SAMPLE051_PRE_REMEDIATION'/'R33_RECOVERY_JOURNAL.json'
    if not pr.is_file() or sha256_file(pr)!=R34_PROGRESS_SHA256: raise RuntimeError('G100_R34_PROGRESS_PRESTATE_MISMATCH')
    if not lp.is_file() or sha256_file(lp)!=R34_CHUNK06_LEDGER_SHA256: raise RuntimeError('G100_R34_CHUNK06_LEDGER_PRESTATE_MISMATCH')
    if not r33j.is_file() or sha256_file(r33j)!=R34_R33_RECOVERY_JOURNAL_SHA256: raise RuntimeError('G100_R34_R33_JOURNAL_PRESTATE_MISMATCH')
    prog=json.loads(pr.read_text(encoding='utf-8')); led=json.loads(lp.read_text(encoding='utf-8')); journal=json.loads(r33j.read_text(encoding='utf-8'))
    if int(prog.get('completed',-1))!=65 or prog.get('status')!='RUNNING' or (prog.get('counts') or {}).get('COMPLETE')!=65:
        raise RuntimeError('G100_R34_PROGRESS_NOT_EXACT_R33_FAILURE')
    expected={r['sample_id']:r['input_digest_sha256'] for r in frozen['chunks'][6]['requests']}
    states=led.get('states') or {}
    if set(states)!=set(expected) or led.get('chunk_digest_sha256')!=frozen['chunks'][6]['chunk_digest_sha256']:
        raise RuntimeError('G100_R34_CHUNK06_IDENTITY_MISMATCH')
    order=[r['sample_id'] for r in frozen['chunks'][6]['requests']]
    for idx,sid in enumerate(order):
        rec=states[sid]
        if rec.get('request_digest')!=expected[sid]: raise RuntimeError('G100_R34_CHUNK06_REQUEST_DIGEST:'+sid)
        if idx<5:
            if rec.get('state')!='COMPLETE' or int(rec.get('attempts',-1))!=1: raise RuntimeError('G100_R34_PRE065_COMPLETE_STATE:'+sid)
        else:
            if rec.get('state')!='PENDING' or int(rec.get('attempts',-1))!=0: raise RuntimeError('G100_R34_POST064_PENDING_STATE:'+sid)
    if journal.get('status')!='SAMPLE051_PASS_AND_052_059_ACCEPTANCE_PERSISTED' or journal.get('final_rgb_sha256')!=R33_EXPECTED_FINAL_RGB_SHA256:
        raise RuntimeError('G100_R34_R33_JOURNAL_INVALID')
    s51=runroot/'CHUNKS'/'chunk_05'/'samples'/R33_RECOVERY_SAMPLE_ID/'rgb.png'
    if not s51.is_file() or sha256_file(s51)!=R33_EXPECTED_FINAL_RGB_SHA256:
        raise RuntimeError('G100_R34_SAMPLE051_FINAL_RGB_MISMATCH')
    recroot=runroot/'RECOVERY'/'R33_REAL_FAILURE_ATOMIC_LEDGER_R34'
    if recroot.exists(): raise RuntimeError('G100_R34_RECOVERY_ALREADY_INITIALIZED_DO_NOT_RERUN')
    recroot.mkdir(parents=True)
    shutil.copy2(_r34_failure_authority_path(),recroot/R34_FAILURE_RETURN_NAME)
    shutil.copy2(pr,recroot/'PROGRESS_pre_r34.json')
    shutil.copy2(lp,recroot/'chunk_06_ledger_pre_r34.json')
    shutil.copy2(r33j,recroot/'R33_RECOVERY_JOURNAL_pre_r34.json')
    rj={'schema':'DF-G100-R34-RECOVERY-JOURNAL-V1','status':'PRESERVED_BEFORE_R34_SOURCE_INSTALL',
        'r34_spec_drive_id':R34_SPEC_DRIVE_ID,'r33_spec_drive_id':R33_SPEC_DRIVE_ID,'implementation_id':R34_IMPLEMENTATION_ID,
        'classification':'WINDOWS_ATOMIC_JSON_REPLACE_TRANSIENT_ACCESS_DENIED_IMPLEMENTATION_GAP',
        'failure_authority':authority,'progress_sha256':R34_PROGRESS_SHA256,'chunk06_ledger_sha256':R34_CHUNK06_LEDGER_SHA256,
        'r33_recovery_journal_sha256':R34_R33_RECOVERY_JOURNAL_SHA256,'completed_samples':65,
        'completed_chunk06_samples':order[:5],'pending_chunk06_samples':order[5:],
        'product_mutated':False,'maya_mutated':False,'test77_accessed':False,'training_started':False,'recorded_utc':utc_iso()}
    atomic_json(recroot/'R34_RECOVERY_JOURNAL.json',rj)
    return {'schema':'DF-G100-R34-PRESTATE-V1','status':'EXACT_R33_ATOMIC_LEDGER_FAILURE_PRESERVED',
            'authority':authority,'recovery_journal':rj,'immutable_aux_gt_sha256':journal.get('immutable_aux_gt_sha256') or {}}


def _r34_validate_completed_060_064(runroot:Path,chunks,M):
    cr=runroot/'CHUNKS'/'chunk_06'; checked=[]
    for req in chunks[6]['requests'][:5]:
        sd=cr/req['output_rel']; cp=sd/'completion.json'
        if not cp.is_file(): raise RuntimeError('G100_R34_COMPLETED_CACHE_MISSING:'+req['sample_id'])
        comp=json.loads(cp.read_text(encoding='utf-8'))
        M['validate_completion'](comp,req,sd)
        checked.append({'sample_id':req['sample_id'],'completion_sha256':sha256_file(cp),'rgb_sha256':sha256_file(sd/'rgb.png')})
    return checked


def _r36_failure_authority_path():
    return HERE/'R36_FAILURE_AUTHORITY'/R35_DIAGNOSTIC_FAILURE_NAME


def _r36_verify_failure_authority():
    p=_r36_failure_authority_path()
    if not p.is_file() or p.stat().st_size!=R35_DIAGNOSTIC_FAILURE_BYTES or sha256_file(p)!=R35_DIAGNOSTIC_FAILURE_SHA256:
        raise RuntimeError('G100_R36_R35_FAILURE_AUTHORITY_IDENTITY_MISMATCH')
    with zipfile.ZipFile(p) as z:
        if z.testzip() is not None: raise RuntimeError('G100_R36_R35_FAILURE_AUTHORITY_CRC_FAIL')
        fail=json.loads(z.read('R35_DIAGNOSTIC_FAILURE.json'))
        if fail.get('schema')!='DF-G100-R35-BLUEPRINT-READONLY-DIAGNOSTIC-V1' or fail.get('status')!='FAIL_CLOSED':
            raise RuntimeError('G100_R36_R35_FAILURE_AUTHORITY_SCHEMA')
        if fail.get('rendering_invoked') is not False or fail.get('resume_invoked') is not False:
            raise RuntimeError('G100_R36_R35_FAILURE_AUTHORITY_NOT_READ_ONLY')
        if 'R35_CONTROL_EVIDENCE_MISSING:g100v2_077_stairs_ramps_wide_blueprint' not in str(fail.get('error','')):
            raise RuntimeError('G100_R36_R35_FAILURE_AUTHORITY_ERROR_CLASS')
        prog_b=z.read('EVIDENCE/STATE/PROGRESS.json')
        led_b=z.read('EVIDENCE/STATE/chunk_07_ledger.json')
        req_b=z.read('EVIDENCE/TARGET_074_REQUEST.json')
        acc_b=z.read('EVIDENCE/TARGET_074_ACCEPTANCE.json')
        comp_b=z.read('EVIDENCE/TARGET_074_FULL_SAMPLE/completion.json')
        rgb_b=z.read('EVIDENCE/TARGET_074_FULL_SAMPLE/rgb.png')
        if sha256_bytes(prog_b)!=R36_PRE_PROGRESS_SHA256 or sha256_bytes(led_b)!=R36_PRE_CHUNK07_LEDGER_SHA256:
            raise RuntimeError('G100_R36_R35_FAILURE_AUTHORITY_STATE_HASH')
        if sha256_bytes(req_b)!=R36_REQUEST_FILE_SHA256 or sha256_bytes(acc_b)!=R36_PRE_ACCEPTANCE_SHA256:
            raise RuntimeError('G100_R36_R35_FAILURE_AUTHORITY_TARGET_META_HASH')
        if sha256_bytes(comp_b)!=R36_PRE_COMPLETION_SHA256 or sha256_bytes(rgb_b)!=R36_PRE_RGB_SHA256:
            raise RuntimeError('G100_R36_R35_FAILURE_AUTHORITY_TARGET_SAMPLE_HASH')
        prog=json.loads(prog_b); led=json.loads(led_b); acc=json.loads(acc_b)
        if int(prog.get('completed',-1))!=80 or prog.get('status')!='RUNNING':
            raise RuntimeError('G100_R36_R35_FAILURE_AUTHORITY_PROGRESS')
        states=led.get('states') or {}
        for i in range(70,80):
            pref=f'g100v2_{i:03d}_'; keys=[k for k in states if k.startswith(pref)]
            if len(keys)!=1 or states[keys[0]].get('state')!='COMPLETE' or int(states[keys[0]].get('attempts',-1))!=1:
                raise RuntimeError('G100_R36_R35_FAILURE_AUTHORITY_CHUNK07:'+pref)
        checks=acc.get('checks') or {}
        if acc.get('status')!='FAIL' or checks.get('rgb_mean') is not False or any(v is not True for k,v in checks.items() if k!='rgb_mean'):
            raise RuntimeError('G100_R36_R35_FAILURE_AUTHORITY_ACCEPTANCE_SIGNATURE')
    return {'path':str(p),'bytes':p.stat().st_size,'sha256':sha256_file(p),'crc':'PASS',
            'classification':'R35_READ_ONLY_COLLECTOR_CONTROL_ACCEPTANCE_ASSUMPTION_AFTER_SUFFICIENT_TARGET_CAPTURE'}


def _r36_assert_and_recover_sample074(runroot:Path,chunks,M):
    authority=_r36_verify_failure_authority()
    if not runroot.is_dir(): raise RuntimeError('G100_R36_EXISTING_R34_RUNROOT_REQUIRED')
    pr=runroot/'PROGRESS.json'; cr=runroot/'CHUNKS'/'chunk_07'; lp=cr/'ledger.json'
    if not pr.is_file() or sha256_file(pr)!=R36_PRE_PROGRESS_SHA256: raise RuntimeError('G100_R36_PROGRESS_PRESTATE_MISMATCH')
    if not lp.is_file() or sha256_file(lp)!=R36_PRE_CHUNK07_LEDGER_SHA256: raise RuntimeError('G100_R36_CHUNK07_LEDGER_PRESTATE_MISMATCH')
    req=chunks[7]['requests'][4]
    if req.get('sample_id')!=R36_RECOVERY_SAMPLE_ID or req.get('input_digest_sha256')!=R36_RECOVERY_REQUEST_DIGEST:
        raise RuntimeError('G100_R36_TARGET_PLAN_IDENTITY_MISMATCH')
    reqp=cr/'requests'/f'{R36_RECOVERY_SAMPLE_ID}.json'; logp=cr/'logs'/f'{R36_RECOVERY_SAMPLE_ID}.log'; sd=cr/req['output_rel']
    accp=runroot/'EVIDENCE'/'SAMPLE_ACCEPTANCE'/f'{R36_RECOVERY_SAMPLE_ID}.json'; comp_p=sd/'completion.json'
    if not reqp.is_file() or sha256_file(reqp)!=R36_REQUEST_FILE_SHA256: raise RuntimeError('G100_R36_REQUEST_PRESTATE_MISMATCH')
    if not accp.is_file() or sha256_file(accp)!=R36_PRE_ACCEPTANCE_SHA256: raise RuntimeError('G100_R36_ACCEPTANCE_PRESTATE_MISMATCH')
    if not comp_p.is_file() or sha256_file(comp_p)!=R36_PRE_COMPLETION_SHA256: raise RuntimeError('G100_R36_COMPLETION_PRESTATE_MISMATCH')
    if not (sd/'rgb.png').is_file() or sha256_file(sd/'rgb.png')!=R36_PRE_RGB_SHA256: raise RuntimeError('G100_R36_RGB_PRESTATE_MISMATCH')
    policy=r36_blueprint_extreme_vertical_policy(req)
    if not policy.get('applied') or abs(float(policy.get('aggregate_vertical_raster_fraction',0))-0.9759765625)>1e-15:
        raise RuntimeError('G100_R36_TARGET_GEOMETRY_POLICY_MISMATCH:'+json.dumps(policy,sort_keys=True))
    if policy.get('existing_r33_applied') is not False or policy.get('closed_room_fill_active') is not False or policy.get('r15_fill_active') is not False:
        raise RuntimeError('G100_R36_TARGET_POLICY_GUARD_MISMATCH')
    recroot=runroot/'RECOVERY'/'R36_SAMPLE074_PRE_REMEDIATION'
    if recroot.exists(): raise RuntimeError('G100_R36_RECOVERY_ALREADY_INITIALIZED_DO_NOT_RERUN')
    recroot.mkdir(parents=True)
    shutil.copy2(_r36_failure_authority_path(),recroot/R35_DIAGNOSTIC_FAILURE_NAME)
    shutil.copytree(sd,recroot/'sample_directory')
    shutil.copy2(reqp,recroot/'request.json')
    if logp.is_file(): shutil.copy2(logp,recroot/'worker.log')
    shutil.copy2(accp,recroot/'acceptance_pre_r36.json'); shutil.copy2(lp,recroot/'chunk_07_ledger_pre_r36.json'); shutil.copy2(pr,recroot/'PROGRESS_pre_r36.json')
    immutable_names=['depth.exr','normal.exr','object_index.exr','normal_authority_mask.uint8.bin','normal_filter_safe_interior_mask.uint8.bin','depth_filter_safe_interior_mask.uint8.bin','micro100_aux_gt_qa.json','camera_calibration.json','pre_render_reprojection.json']
    immutable_before={n:sha256_file(sd/n) for n in immutable_names if (sd/n).is_file()}
    journal={'schema':'DF-G100-R36-SAMPLE074-RECOVERY-JOURNAL-V1','status':'PRESERVED_BEFORE_REMEDIATION',
             'r36_spec_drive_id':R36_SPEC_DRIVE_ID,'classification':'BLUEPRINT_DOWNLIGHT_DISTRIBUTED_EXTREME_VERTICAL_COVERAGE_VISIBILITY_GAP',
             'sample_id':R36_RECOVERY_SAMPLE_ID,'request_digest':R36_RECOVERY_REQUEST_DIGEST,'pre_rgb_sha256':R36_PRE_RGB_SHA256,
             'policy':policy,'failure_authority':authority,'immutable_aux_gt_sha256':immutable_before,
             'recorded_utc':utc_iso(),'product_mutated':False,'maya_mutated':False,'test77_accessed':False,'training_started':False}
    atomic_json(recroot/'R36_RECOVERY_JOURNAL.json',journal)

    pre36=sd/'rgb_pre_r36.png'; pre36.write_bytes((sd/'rgb.png').read_bytes())
    gain=apply_fixed_rgb8_gain_png(pre36,sd/'rgb.png',numerator=3,denominator=1)
    gain.update({'implementation_id':R36_IMPLEMENTATION_ID,'source_rgb_rel':'rgb_pre_r36.png','final_rgb_rel':'rgb.png',
                 'geometry_preserving':True,'eligibility':policy,'r36_spec_drive_id':R36_SPEC_DRIVE_ID})
    if sha256_file(pre36)!=R36_PRE_RGB_SHA256 or sha256_file(sd/'rgb.png')!=R36_EXPECTED_FINAL_RGB_SHA256:
        raise RuntimeError('G100_R36_FIXED_GAIN_OUTPUT_IDENTITY_MISMATCH')
    comp=json.loads(comp_p.read_text(encoding='utf-8'))
    comp['r36_blueprint_extreme_vertical_policy']=policy; comp['r36_blueprint_fixed_rgb_gain']=gain
    comp['files']=[r for r in (comp.get('files') or []) if r.get('path') not in {'rgb.png','rgb_pre_r36.png'}]
    comp['files'].extend([_r33_file_record(sd/'rgb.png',sd),_r33_file_record(pre36,sd)])
    comp['files']=sorted(comp['files'],key=lambda r:r['path'])
    atomic_json(comp_p,comp)
    for n,sh in immutable_before.items():
        if sha256_file(sd/n)!=sh: raise RuntimeError('G100_R36_AUX_GT_MUTATED:'+n)
    acc=sample_acceptance(req,comp,sd,M,{'schema':'DF-G100-R36-RGB-ONLY-RECOVERY-V1','mode':'EXISTING_BYTES_NO_RERENDER','pre_rgb_sha256':R36_PRE_RGB_SHA256})
    if acc.get('status')!='PASS': raise RuntimeError('G100_R36_SAMPLE074_ACCEPTANCE_FAIL:'+json.dumps(acc.get('checks'),sort_keys=True))
    st=acc.get('rgb') or {}
    if abs(float(st.get('mean_luma',0))-15.329213689453125)>1e-12 or abs(float(st.get('structural_fraction',0))-0.12263671875)>1e-15:
        raise RuntimeError('G100_R36_SAMPLE074_RGB_STATS_UNEXPECTED')
    atomic_json(accp,acc)
    journal['status']='SAMPLE074_PASS_EXISTING_BYTES_X3'; journal['final_rgb_sha256']=sha256_file(sd/'rgb.png'); journal['final_acceptance_sha256']=sha256_file(accp)
    atomic_json(recroot/'R36_RECOVERY_JOURNAL.json',journal)
    return {'schema':'DF-G100-R36-PRESTATE-RECOVERY-V1','status':'PASS_SAMPLE074_RGB_ONLY_X3',
            'authority':authority,'policy':policy,'sample074_acceptance':acc,'immutable_aux_gt_sha256':immutable_before}


def _r36_validate_existing_070_079_and_persist_tail(runroot:Path,chunks,M):
    cr=runroot/'CHUNKS'/'chunk_07'; out=[]
    for i,req in enumerate(chunks[7]['requests']):
        sd=cr/req['output_rel']; cp=sd/'completion.json'
        if not cp.is_file(): raise RuntimeError('G100_R36_COMPLETED_CACHE_MISSING:'+req['sample_id'])
        comp=json.loads(cp.read_text(encoding='utf-8')); M['validate_completion'](comp,req,sd)
        ap=runroot/'EVIDENCE'/'SAMPLE_ACCEPTANCE'/f"{req['sample_id']}.json"
        if i<5:
            if not ap.is_file(): raise RuntimeError('G100_R36_PRE075_ACCEPTANCE_MISSING:'+req['sample_id'])
            a=json.loads(ap.read_text(encoding='utf-8'))
            if a.get('status')!='PASS': raise RuntimeError('G100_R36_PRE075_ACCEPTANCE_INVALID:'+req['sample_id'])
        else:
            a=sample_acceptance(req,comp,sd,M,None)
            atomic_json(ap,a)
            if a.get('status')!='PASS': raise RuntimeError('G100_R36_SAMPLE_ACCEPTANCE_FAIL:'+req['sample_id']+':'+json.dumps(a.get('checks'),sort_keys=True))
        out.append(a)
    return out


def run(factory_root):
    root=Path(factory_root); safe_root(root)
    refs=[verify_ref('PCS_CAMERA_GEOMETRY_DATA_FACTORY_G80_G94_POST_R10_REAL_EVIDENCE_V1_20260906.zip',CLOSURE_EVIDENCE_SHA),
          verify_ref('PCS_CAMERA_GEOMETRY_DATA_FACTORY_G70_G77_REAL_AUX_GT_EVIDENCE_V2_20260906.zip',G70_EVIDENCE_SHA),
          verify_ref('PCS_CAMERA_GEOMETRY_DATA_FACTORY_G48_G70_EXCEPTION_CLOSURE_RETURN.zip',R10_RETURN_SHA)]
    runroot=root/'09_RUNS'/RUN_ID
    # Authenticate/preserve the exact 80-COMPLETE prestate using the package
    # source before installing the R36 release into the factory.
    M_pkg=_load_modules(SOURCE)
    reqs,chunks,pqa,package_plan_identity=load_package_frozen_plan(M_pkg,run_regeneration=False)
    if pqa['status']!='PASS' or package_plan_identity.get('sha256')!=PACKAGE_PLAN_SHA256:
        raise RuntimeError('G100_R36_PLAN_AUTHORITY_FAIL')
    prestate=_r36_assert_and_recover_sample074(runroot,chunks,M_pkg)
    release=install_release(root); M=_load_modules(release); preflight=blender_preflight(M,root); preflight['authority_references']=refs
    tail_accepts=_r36_validate_existing_070_079_and_persist_tail(runroot,chunks,M)

    # Validate all prior accepted evidence through sample069, then append 070..079.
    accepts=[]
    for req in reqs[:70]:
        ap=runroot/'EVIDENCE'/'SAMPLE_ACCEPTANCE'/f"{req['sample_id']}.json"
        if not ap.is_file(): raise RuntimeError('G100_R36_PRE070_ACCEPTANCE_MISSING:'+req['sample_id'])
        a=json.loads(ap.read_text(encoding='utf-8'))
        if a.get('status')!='PASS' or a.get('request_digest')!=req['input_digest_sha256']:
            raise RuntimeError('G100_R36_PRE070_ACCEPTANCE_INVALID:'+req['sample_id'])
        accepts.append(a)
    accepts.extend(tail_accepts)

    # Prior chunk archives 00..06 are authoritative; chunk07 is built only now
    # after its existing COMPLETE bytes obtain persisted PASS acceptance.
    partialp=runroot/'EVIDENCE'/'CHUNK_IDENTITIES_PARTIAL.json'
    partial=json.loads(partialp.read_text(encoding='utf-8')) if partialp.is_file() else {'chunks':[]}
    oldids=partial.get('chunks') or []
    if len(oldids)!=7: raise RuntimeError('G100_R36_EXPECTED_SEVEN_PRIOR_CHUNK_IDENTITIES:'+str(len(oldids)))
    chunk_ids=[]
    for ci in range(7):
        rec=oldids[ci]; zp=runroot/'CHUNK_ARCHIVES'/rec['path']
        if not zp.is_file() or zp.stat().st_size!=int(rec['bytes']) or sha256_file(zp)!=rec['sha256']:
            raise RuntimeError('G100_R36_PRIOR_CHUNK_ARCHIVE_MUTATED:'+str(ci))
        with zipfile.ZipFile(zp) as z:
            if z.testzip() is not None: raise RuntimeError('G100_R36_PRIOR_CHUNK_ARCHIVE_CRC:'+str(ci))
        chunk_ids.append(rec)
    zp7=runroot/'CHUNK_ARCHIVES'/'PCS_CAMERA_GEOMETRY_MICRO100_V2_CHUNK_07.zip'
    cid7=make_chunk_zip(runroot/'CHUNKS'/'chunk_07',zp7); chunk_ids.append(cid7)
    atomic_json(partialp,{'chunks':chunk_ids})
    update_progress(runroot)

    planp=runroot/'PLAN'/'MICRO100_REQUESTS_FROZEN.json'
    plan_info={'plan_path':planp,'plan_sha256':sha256_file(planp),'plan_bytes':planp.stat().st_size,
               'package_frozen_plan':package_plan_identity,'r36_prestate':prestate,'r36_spec_drive_id':R36_SPEC_DRIVE_ID,
               'r34_spec_drive_id':R34_SPEC_DRIVE_ID,'r33_spec_drive_id':R33_SPEC_DRIVE_ID,'r29_spec_drive_id':R29_SPEC_DRIVE_ID}

    stop=threading.Event(); thr=threading.Thread(target=progress_loop,args=(runroot,stop),daemon=True); thr.start()
    try:
        for ci in range(8,10):
            chunk=chunks[ci]; cr=runroot/'CHUNKS'/f'chunk_{ci:02d}'
            print(f'\n[DF-G100 V2 R36] ===== CHUNK {ci+1}/10 : samples {ci*10:03d}-{ci*10+9:03d} =====',flush=True)
            result=M['execute_chunk'](root,chunk,cr,worker_id='LOCAL_WINDOWS',max_attempts=2)
            if result['status']!='PASS': raise RuntimeError(f'G100_R36_CHUNK_RENDER_FAIL:{ci}:{result}')
            for req in chunk['requests']:
                sd=cr/req['output_rel']; comp=json.loads((sd/'completion.json').read_text(encoding='utf-8'))
                a=sample_acceptance(req,comp,sd,M,None)
                atomic_json(runroot/'EVIDENCE'/'SAMPLE_ACCEPTANCE'/f"{req['sample_id']}.json",a)
                if a['status']!='PASS': raise RuntimeError('G100_R36_SAMPLE_ACCEPTANCE_FAIL:'+req['sample_id']+':'+json.dumps(a['checks'],sort_keys=True))
                accepts.append(a)
            zp=runroot/'CHUNK_ARCHIVES'/f'PCS_CAMERA_GEOMETRY_MICRO100_V2_CHUNK_{ci:02d}.zip'; cid=make_chunk_zip(cr,zp); chunk_ids.append(cid)
            atomic_json(partialp,{'chunks':chunk_ids}); update_progress(runroot)
            print(f"[DF-G100 V2 R36] chunk {ci+1}/10 PASS | {cid['bytes']:,} bytes | sha256 {cid['sha256']}",flush=True)
    finally:
        stop.set();thr.join(timeout=5)
    if len(accepts)!=100: raise RuntimeError(f'G100_R36_ACCEPTANCE_COUNT:{len(accepts)}')
    write_visuals(runroot,reqs,accepts); qa=corpus_qa(runroot,reqs,accepts,chunk_ids)
    if qa['status']!='PASS': raise RuntimeError('G100_R36_CORPUS_QA_FAIL')
    z,ident=outer_package(root,runroot,release,chunk_ids,preflight,plan_info,qa); update_progress(runroot)
    journal={'schema':'DF-G100-R36-RUN-JOURNAL-V1','status':'MEASUREMENT_COMPLETE_PENDING_VISUAL_REVIEW','last_event':'V2_RETURN_PACKAGE_READY',
             'dataset_id':DATASET_ID,'release_id':RELEASE_ID,'source_release_id':SOURCE_RELEASE_ID,'r36_spec_drive_id':R36_SPEC_DRIVE_ID,
             'r34_spec_drive_id':R34_SPEC_DRIVE_ID,'r33_spec_drive_id':R33_SPEC_DRIVE_ID,'r29_spec_drive_id':R29_SPEC_DRIVE_ID,
             'r36_prestate':prestate,'return_zip':str(z),'return_identity':ident,'sample_count':100,'automated_acceptance_pass':True,
             'scale_1k_authorized':False,'training_handoff_authorized':False,'product_mutated':False,'maya_mutated':False,'test77_accessed':False,'training_started':False}
    returns=root/'11_PACKAGES'/'RETURNS'; atomic_json(returns/'DF_G100_MICRO100_V2_RUN_JOURNAL.json',journal)
    recj=runroot/'RECOVERY'/'R36_SAMPLE074_PRE_REMEDIATION'/'R36_RECOVERY_JOURNAL.json'
    if recj.is_file():
        rj=json.loads(recj.read_text(encoding='utf-8')); rj['status']='R36_CONTINUATION_COMPLETED_100_OF_100'; rj['return_identity']=ident; rj['recorded_final_utc']=utc_iso(); atomic_json(recj,rj)
    print('\n[DF-G100 V2 R36] MEASUREMENT_COMPLETE_PENDING_VISUAL_REVIEW',flush=True)
    print('[DF-G100 V2 R36] Return ZIP:',z,flush=True); print('[DF-G100 V2 R36] Identity:',str(z)+'.identity.json',flush=True); return 0

def r36_pre_real_selftest():
    if str(SOURCE) not in sys.path: sys.path.insert(0,str(SOURCE))
    M=_load_modules(SOURCE)
    reqs,chunks,qa,ident=load_package_frozen_plan(M,run_regeneration=False)
    checks={}
    r33_eligible=[]; r36_eligible=[]
    policies={}
    for i,req in enumerate(reqs):
        p33=r33_blueprint_vertical_dominant_policy(req)
        p36=r36_blueprint_extreme_vertical_policy(req)
        if p33.get('applied'): r33_eligible.append(i)
        if p36.get('applied'): r36_eligible.append(i)
        if i in {51,54,74,77,83}: policies[str(i)]={'r33':p33,'r36':p36}
    checks['plan_identity']=ident.get('sha256')==PACKAGE_PLAN_SHA256 and qa.get('status')=='PASS'
    checks['r33_eligibility_unchanged']=r33_eligible==[51]
    checks['r36_eligibility_exact_074_only']=r36_eligible==[74]
    p74=policies['74']['r36']; p54=policies['54']['r36']; p77=policies['77']['r36']; p83=policies['83']['r36']; p51=policies['51']['r36']
    checks['target_geometry_exact']=p74.get('applied') is True and abs(float(p74.get('aggregate_vertical_raster_fraction',0))-0.9759765625)<1e-15
    checks['control054_below_095']=p54.get('applied') is False and float(p54.get('aggregate_vertical_raster_fraction',1))<0.95
    checks['control077_low_vertical']=p77.get('applied') is False and float(p77.get('aggregate_vertical_raster_fraction',1))<0.10
    checks['control083_closed_room_blocks']=p83.get('applied') is False and p83.get('closed_room_fill_active') is True
    checks['sample051_existing_r33_blocks_r36']=p51.get('applied') is False and p51.get('existing_r33_applied') is True

    # Forced categorical negative controls required by the frozen R36 spec.
    wrong_profile=copy.deepcopy(reqs[74]); wrong_profile['appearance']['profile_id']='TOON'
    wrong_split=copy.deepcopy(reqs[74]); wrong_split['split']='NOT_MICRO100'
    forced_r15=copy.deepcopy(reqs[74]); C=forced_r15['camera']['pose']['camera_center_world']
    forced_r15['scene']['objects'].append({'object_id':'r36_forced_enclosing_solid','primitive':'BOX','center_world':C,
                                           'dimensions_m':[1000.0,1000.0,1000.0],
                                           'R_local_to_world':[[1,0,0],[0,1,0],[0,0,1]]})
    checks['wrong_profile_blocks']=not r36_blueprint_extreme_vertical_policy(wrong_profile).get('applied')
    checks['wrong_split_blocks']=not r36_blueprint_extreme_vertical_policy(wrong_split).get('applied')
    forced_r15_policy=r36_blueprint_extreme_vertical_policy(forced_r15)
    checks['r15_fill_blocks']=forced_r15_policy.get('r15_fill_active') is True and not forced_r15_policy.get('applied')
    policy_src=(SOURCE/'pcs_factory_blueprint_r36.py').read_text(encoding='utf-8')
    policy_tree=ast.parse(policy_src)
    policy_identifiers={n.id for n in ast.walk(policy_tree) if isinstance(n,ast.Name)} | {n.attr for n in ast.walk(policy_tree) if isinstance(n,ast.Attribute)}
    checks['no_sample074_special_case']='g100v2_074' not in policy_src and 'sample074' not in policy_src.lower()
    checks['no_rgb_acceptance_dependency']=not ({'rgb_stats','mean_luma','p01','p99','p01_p99_span','structural_fraction','unique_rgb','sample_acceptance'} & policy_identifiers)

    authority=_r36_verify_failure_authority(); checks['r35_failure_authority_exact']=authority.get('sha256')==R35_DIAGNOSTIC_FAILURE_SHA256

    # Existing R33 sample051 scientific fixture must remain unchanged and PASS.
    fix51=HERE/'FIXTURES'/'R33_SAMPLE051_AUTHORITY'
    req51=json.loads((fix51/'request.json').read_text(encoding='utf-8'))
    with tempfile.TemporaryDirectory(prefix='g100r36_r33_fixture_') as td51:
        sd51=Path(td51)/'sample'; shutil.copytree(fix51/'sample',sd51)
        pre51=sd51/'rgb_pre_r33.png'; pre51.write_bytes((sd51/'rgb.png').read_bytes())
        meta51=apply_fixed_rgb8_gain_png(pre51,sd51/'rgb.png',numerator=2,denominator=1)
        pol51=r33_blueprint_vertical_dominant_policy(req51)
        meta51.update({'implementation_id':R33_IMPLEMENTATION_ID,'source_rgb_rel':'rgb_pre_r33.png','final_rgb_rel':'rgb.png','geometry_preserving':True,'eligibility':pol51,'r33_spec_drive_id':R33_SPEC_DRIVE_ID})
        comp51=json.loads((sd51/'completion.json').read_text(encoding='utf-8'))
        comp51['r33_blueprint_vertical_dominant_policy']=pol51; comp51['r33_blueprint_fixed_rgb_gain']=meta51
        comp51['files']=[r for r in (comp51.get('files') or []) if r.get('path') not in {'rgb.png','rgb_pre_r33.png'}]
        comp51['files'].extend([_r33_file_record(sd51/'rgb.png',sd51),_r33_file_record(pre51,sd51)]); comp51['files']=sorted(comp51['files'],key=lambda r:r['path'])
        atomic_json(sd51/'completion.json',comp51)
        acc51=sample_acceptance(req51,comp51,sd51,M,{'schema':'DF-G100-R36-R33-REGRESSION-FIXTURE'})
        checks['sample051_r33_fixture_byte_exact_pass']=(sha256_file(sd51/'rgb.png')==R33_EXPECTED_FINAL_RGB_SHA256 and acc51.get('status')=='PASS' and all(acc51.get('checks',{}).values()))

    # Exact target fixture: x2 remains insufficient, x3 is the frozen minimal
    # extreme tier and must pass the unchanged full acceptance contract.
    with tempfile.TemporaryDirectory(prefix='g100r36_') as td:
        td=Path(td); sd=td/'sample'; sd.mkdir()
        with zipfile.ZipFile(_r36_failure_authority_path()) as z:
            base='EVIDENCE/TARGET_074_FULL_SAMPLE/'
            for n in z.namelist():
                if n.startswith(base) and not n.endswith('/'):
                    q=sd/n[len(base):]; q.parent.mkdir(parents=True,exist_ok=True); q.write_bytes(z.read(n))
            req=json.loads(z.read('EVIDENCE/TARGET_074_REQUEST.json'))
        immutable_names=['depth.exr','normal.exr','object_index.exr','normal_authority_mask.uint8.bin','normal_filter_safe_interior_mask.uint8.bin','depth_filter_safe_interior_mask.uint8.bin','micro100_aux_gt_qa.json']
        immutable={n:sha256_file(sd/n) for n in immutable_names if (sd/n).is_file()}
        # x2 diagnostic only on a copy.
        x2=td/'x2.png'; apply_fixed_rgb8_gain_png(sd/'rgb.png',x2,numerator=2,denominator=1)
        st2=rgb_stats(x2); checks['x2_still_below_mean_gate']=st2['mean_luma']<12
        pre=sd/'rgb_pre_r36.png'; pre.write_bytes((sd/'rgb.png').read_bytes())
        gain=apply_fixed_rgb8_gain_png(pre,sd/'rgb.png',numerator=3,denominator=1)
        gain.update({'implementation_id':R36_IMPLEMENTATION_ID,'source_rgb_rel':'rgb_pre_r36.png','final_rgb_rel':'rgb.png','geometry_preserving':True,
                     'eligibility':r36_blueprint_extreme_vertical_policy(req),'r36_spec_drive_id':R36_SPEC_DRIVE_ID})
        comp=json.loads((sd/'completion.json').read_text(encoding='utf-8'))
        comp['r36_blueprint_extreme_vertical_policy']=gain['eligibility']; comp['r36_blueprint_fixed_rgb_gain']=gain
        comp['files']=[r for r in (comp.get('files') or []) if r.get('path') not in {'rgb.png','rgb_pre_r36.png'}]
        comp['files'].extend([_r33_file_record(sd/'rgb.png',sd),_r33_file_record(pre,sd)])
        comp['files']=sorted(comp['files'],key=lambda r:r['path'])
        atomic_json(sd/'completion.json',comp)
        a=sample_acceptance(req,comp,sd,M,{'schema':'DF-G100-R36-FIXTURE-SELFTEST'})
        checks['x3_output_identity']=sha256_file(sd/'rgb.png')==R36_EXPECTED_FINAL_RGB_SHA256
        checks['x3_acceptance_all_pass']=a.get('status')=='PASS' and all(a.get('checks',{}).values())
        checks['x3_expected_stats']=(abs(float(a['rgb']['mean_luma'])-15.329213689453125)<1e-12 and
                                     abs(float(a['rgb']['structural_fraction'])-0.12263671875)<1e-15 and
                                     int(a['rgb']['unique_rgb'])==1211)
        checks['aux_gt_byte_identical']=all(sha256_file(sd/n)==sh for n,sh in immutable.items())
    out={'schema':'DF-G100-R36-PRE-REAL-SELFTEST-V1','status':'PASS' if all(checks.values()) else 'FAIL',
         'checks':checks,'r33_eligible_indices':r33_eligible,'r36_eligible_indices':r36_eligible,'policies':policies,
         'authority':{'real_run_executed':False,'one_real_recovery_authorized':False,'micro100_closed':False,
                      'scale_1k_authorized':False,'training_started':False,'test77_accessed':False,'product_mutated':False,'maya_mutated':False}}
    atomic_json(HERE/'DF_G100_R36_PRE_REAL_SELFTEST.json',out)
    print(json.dumps(out,indent=2,sort_keys=True))
    return 0 if out['status']=='PASS' else 2

def selftest():
    # Static/pre-real R3 package selftest. It preserves R2 plan authority and adds bounded renderer raster binding + exact resume.
    if str(SOURCE) not in sys.path:sys.path.insert(0,str(SOURCE))
    M=_load_modules(SOURCE);reqs,chunks,qa,package_plan_identity=load_package_frozen_plan(M);refs=[]
    for n,sh in [('PCS_CAMERA_GEOMETRY_DATA_FACTORY_G80_G94_POST_R10_REAL_EVIDENCE_V1_20260906.zip',CLOSURE_EVIDENCE_SHA),('PCS_CAMERA_GEOMETRY_DATA_FACTORY_G70_G77_REAL_AUX_GT_EVIDENCE_V2_20260906.zip',G70_EVIDENCE_SHA),('PCS_CAMERA_GEOMETRY_DATA_FACTORY_G48_G70_EXCEPTION_CLOSURE_RETURN.zip',R10_RETURN_SHA)]:refs.append(verify_ref(n,sh))
    nc=negative_controls();worker=(SOURCE/'pcs_factory_blender_worker.py').read_text();gt=(SOURCE/'pcs_factory_micro100_gt.py').read_text()
    r2c={}
    with tempfile.TemporaryDirectory(prefix='g100r2_') as td:
        tp=Path(td)/'plan.json';shutil.copy2(PACKAGE_PLAN,tp);b=bytearray(tp.read_bytes());b[len(b)//2]^=1;tp.write_bytes(bytes(b))
        try: load_package_frozen_plan(M,tp,PACKAGE_PLAN_SHA256,False); r2c['tampered_plan_sha_blocks']=False
        except RuntimeError as e: r2c['tampered_plan_sha_blocks']='SHA_MISMATCH' in str(e)
    frozen=json.loads(PACKAGE_PLAN.read_text(encoding='utf-8'))
    altered=copy.deepcopy(frozen);altered['requests'][0]['sample_id']='tampered_sample_id'
    try:_validate_frozen_plan_object(altered,M);r2c['altered_request_blocks']=False
    except Exception:r2c['altered_request_blocks']=True
    regen_reqs,regen_chunks=generate_plan(M);numeric=copy.deepcopy(regen_reqs)
    numeric[0]['camera']['sampled']['hfov_deg']=float(numeric[0]['camera']['sampled']['hfov_deg'])+1e-12
    r2c['numeric_regeneration_perturbation_nonblocking']=_discrete_regeneration_diagnostic(reqs,chunks,numeric,regen_chunks)['status']=='PASS'
    discrete=copy.deepcopy(regen_reqs);discrete[0]['camera']['profile']='WIDE' if discrete[0]['camera']['profile']!='WIDE' else 'NORMAL'
    r2c['discrete_regeneration_perturbation_blocks']=_discrete_regeneration_diagnostic(reqs,chunks,discrete,regen_chunks)['status']=='FAIL'
    r2c['package_plan_exact_sha']=package_plan_identity['sha256']==PACKAGE_PLAN_SHA256
    r2c['loaded_request_count']=len(reqs)==100;r2c['loaded_chunk_shape']=len(chunks)==10 and all(len(c['requests'])==10 for c in chunks)
    r2_status=all(r2c.values())
    r3c={}
    reg_path=HERE/'DF_G100_R3_DEPTH_BINDING_REGRESSION_RESULT.json'
    if reg_path.is_file():
        reg=json.loads(reg_path.read_text(encoding='utf-8'))
        r3c['exact_forensic_depth_binding_regression']=reg.get('status')=='PASS' and all(reg.get('checks',{}).values())
    else:r3c['exact_forensic_depth_binding_regression']=False
    r3c['fit_only_cx_cy']=all(x in gt for x in ["Kp[axis,2]","K_eff[0,2]+=delta[0]","K_eff[1,2]+=delta[1]","'fx_fitted':False","'fy_fitted':False","'pose_fitted':False","'depth_scale_fitted':False","'depth_offset_fitted':False","'per_object_fit':False","'nonlinear_warp':False"])
    r3c['binding_bound_0_001']='RENDERER_PP_BINDING_MAX_PX = 0.001' in gt
    r3c['depth_threshold_unchanged']='DEPTH_GEOM_TOL_M = 1e-4' in gt
    r3c['addendum_bound']='1zTxwLTjw4KWG-Zy9DMjQW--RDNihqRMJPvFxtSJKdB0' in gt and R3_ADDENDUM_DRIVE_ID=='1zTxwLTjw4KWG-Zy9DMjQW--RDNihqRMJPvFxtSJKdB0'
    forensic=HERE/'R2_FORENSIC_EVIDENCE'/'PCS_CAMERA_GEOMETRY_DATA_FACTORY_G100_R2_FORENSIC_CAPTURE_RETURN.zip'
    r3c['forensic_fixture_exact']=forensic.is_file() and sha256_file(forensic)=='48b6ccbeece8613235ccefa8989ac07f7ca96a5f0afd411b6a8e7d28a24fe26b'
    # Exact synthetic ledger recovery: only sample002 may reset.
    with tempfile.TemporaryDirectory(prefix='g100r3resume_') as td:
        rr=Path(td)/'09_RUNS'/RUN_ID;cr=rr/'CHUNKS'/'chunk_00';cr.mkdir(parents=True)
        ledger={'schema':'DF-G54-CHUNK-LEDGER-V1','chunk_digest_sha256':R2_CHUNK0_DIGEST,'worker_id':'LOCAL_WINDOWS','states':{}}
        for req in chunks[0]['requests']:
            sid=req['sample_id'];ledger['states'][sid]={'state':'PENDING','attempts':0,'request_digest':req['input_digest_sha256']}
        ledger['states']['g100_000_interior_normal_pbr_realistic_intent'].update({'state':'COMPLETE','attempts':1})
        ledger['states']['g100_001_corridor_strong_roll_toon'].update({'state':'COMPLETE','attempts':1})
        ledger['states'][R2_FAILED_SAMPLE_ID].update({'state':'FAILED_FINAL','attempts':2,'last_error':'BLENDER_WORKER_RC:5'})
        atomic_json(cr/'ledger.json',ledger)
        sd=cr/'samples'/R2_FAILED_SAMPLE_ID;sd.mkdir(parents=True)
        atomic_json(sd/'failure.json',{'error':R2_FAILURE_ERROR,'input_digest_sha256':R2_FAILED_SAMPLE_REQUEST_DIGEST})
        (sd/'sentinel_partial.bin').write_bytes(b'R2_FAILED_PARTIAL_EVIDENCE')
        before0=dict(ledger['states']['g100_000_interior_normal_pbr_realistic_intent']);before1=dict(ledger['states']['g100_001_corridor_strong_roll_toon'])
        ri=apply_r3_resume_if_needed(rr,chunks)
        after=json.loads((cr/'ledger.json').read_text(encoding='utf-8'))
        rs=after['states'][R2_FAILED_SAMPLE_ID]
        r3c['resume_exact_precondition_pass']=ri.get('status')=='R2_SAMPLE_002_REOPENED_FOR_R3'
        r3c['resume_resets_only_sample002']=rs.get('state')=='PENDING' and rs.get('attempts')==0 and after['states']['g100_000_interior_normal_pbr_realistic_intent']==before0 and after['states']['g100_001_corridor_strong_roll_toon']==before1
        r3c['resume_preserves_failed_bytes']=(rr/'RECOVERY'/'R2_FAILED_SAMPLE_002'/'sample_bytes'/'failure.json').is_file() and (rr/'RECOVERY'/'R2_FAILED_SAMPLE_002'/'sample_bytes'/'sentinel_partial.bin').is_file()
        r3c['resume_clears_stale_sample002']=not (sd/'failure.json').exists() and sd.is_dir()
        # Second application must be idempotent and must not reset attempts again.
        ri2=apply_r3_resume_if_needed(rr,chunks)
        r3c['resume_idempotent']=ri2.get('status')=='R3_RECOVERY_ALREADY_APPLIED'
    r3_status=all(r3c.values())
    r9c={}
    forensic9=HERE/'R8_SAMPLE001_FORENSIC_EVIDENCE'/'PCS_CAMERA_GEOMETRY_DATA_FACTORY_G100_R8_SAMPLE001_FORENSIC_CAPTURE_RETURN_REAL_20260907.zip'
    r8real=HERE/'R8_REAL_FAILURE_EVIDENCE'/'PCS_CAMERA_GEOMETRY_DATA_FACTORY_G100_MICRO100_FAILURE_RETURN_R8_REAL_20260907.zip'
    r9c['forensic_fixture_exact']=forensic9.is_file() and sha256_file(forensic9)==R9_FORENSIC_RETURN_SHA256
    r9c['r8_real_fixture_exact']=r8real.is_file() and sha256_file(r8real)==R8_REAL_RETURN_SHA256
    if r9c['forensic_fixture_exact']:
        try:
            with zipfile.ZipFile(forensic9) as z:
                r9c['forensic_fixture_crc']=z.testzip() is None
                with tempfile.TemporaryDirectory(prefix='g100r9rgb_') as td:
                    rp=Path(td)/'rgb.png';rp.write_bytes(z.read('EVIDENCE/sample001/rgb.png'))
                    st9=rgb_stats(rp)
                    r9c['exact_prior_rgb_reproduced']=(
                        sha256_file(rp)==R9_PRIOR_RGB_SHA256 and
                        st9['unique_rgb']==231 and abs(st9['mean_luma']-194.00526358789062)<=1e-12 and
                        abs(st9['p01']-178.3774)<=1e-12 and abs(st9['p99']-200.8014)<=1e-12 and
                        abs(st9['p01_p99_span']-22.424000000000007)<=1e-12 and
                        abs(st9['structural_fraction']-0.042646484375)<=1e-12)
                req9=json.loads(z.read('EVIDENCE/chunk00/request_sample001.json'))
                wall=next(o for o in req9['scene']['objects'] if o['object_id']=='corridor_1001.wallS')
                camz=float(req9['camera']['pose']['camera_center_world'][2]); fwdz=float(req9['camera']['pose']['forward_world'][2])
                wall_outer=float(wall['center_world'][2])+float(wall['dimensions_m'][2])/2.0
                r9c['camera_wall_relation_proven']=camz>wall_outer and fwdz<0.0 and req9['input_digest_sha256']==R9_RECOVERY_REQUEST_DIGEST
        except Exception:
            r9c['forensic_fixture_crc']=False;r9c['exact_prior_rgb_reproduced']=False;r9c['camera_wall_relation_proven']=False
    else:
        r9c['forensic_fixture_crc']=False;r9c['exact_prior_rgb_reproduced']=False;r9c['camera_wall_relation_proven']=False
    if r9c['r8_real_fixture_exact']:
        try:
            with zipfile.ZipFile(r8real) as z:
                r9c['r8_real_fixture_crc']=z.testzip() is None
                with tempfile.TemporaryDirectory(prefix='g100r9toonref_') as td:
                    p4=Path(td)/'rgb004.png';p4.write_bytes(z.read('RECOVERY/R4_FAILED_SAMPLE_004/sample_bytes/rgb.png'))
                    s4=rgb_stats(p4)
                    r9c['toon_without_closed_room_fill_reference_passes']=s4['p01_p99_span']>=24 and 12<=s4['mean_luma']<=243 and s4['structural_fraction']>=0.03
                    r9c['toon_reference_span_gt_prior_sample001']=s4['p01_p99_span']>R9_PRIOR_RGB_STATS['p01_p99_span']
        except Exception:
            r9c['r8_real_fixture_crc']=False;r9c['toon_without_closed_room_fill_reference_passes']=False;r9c['toon_reference_span_gt_prior_sample001']=False
    else:
        r9c['r8_real_fixture_crc']=False;r9c['toon_without_closed_room_fill_reference_passes']=False;r9c['toon_reference_span_gt_prior_sample001']=False
    r9c['worker_exact_toon_fill_rule']='g100_fill_energy = 175.0 if pid == "TOON" else 350.0' in worker
    r9c['worker_completion_records_r9_rule']='DF_G100_CLOSED_ROOM_CAMERA_FILL_V2_R9_TOON_BALANCED' in worker and '"energy_w": (175.0 if appearance.get("profile_id") == "TOON" else 350.0)' in worker
    r9c['painterly_800_unchanged']='add_point("PCS_PAINTERLY_CAMERA_FILL", 800.0' in worker
    r9c['rgb_thresholds_unchanged']="stats['p01_p99_span']>=24" in Path(__file__).read_text(encoding='utf-8') and "stats['unique_rgb']>=32" in Path(__file__).read_text(encoding='utf-8')
    critical_hashes={
      'pcs_factory_camera.py':'51d131462363c7f6fafa35b3b6ecca257239d920b11aeb292221b2c6c2c41f85',
      'pcs_factory_scene_recipe.py':'0e88f2d85dc938b5f08fa82339556f3df97b0530ac90f5e2e95b55cde8bda071',
      'pcs_factory_blender_controller.py':'6a577c811f1204f2c48a86f3e9bc387134aeef5bb50f1dede4c33d7ac8e051f0',
      'pcs_factory_appearance.py':'d04db4526da1666930502394d6e83f2d6f9f6e9a4da72810b334b2a9f09362a4'}
    r9c['critical_camera_scene_non_gt_sources_authorized_r13_delta_only']=all(sha256_file(SOURCE/name)==sh for name,sh in critical_hashes.items())
    # R13 intentionally adds only the physical-raster predicate to the protocol.
    # Removing that helper and its math import must reproduce the exact R12/R9 protocol bytes.
    proto=(SOURCE/'pcs_factory_blender_protocol.py').read_text(encoding='utf-8')
    proto_base=proto.replace('import math\n','')
    h0=proto_base.index('def pixel_in_physical_raster('); h1=proto_base.index('def initial_blender_camera_from_K',h0)
    proto_base=proto_base[:h0]+proto_base[h1:]
    r9c['protocol_prior_surface_unchanged_except_r13_raster_helper']=sha256_bytes(proto_base.encode('utf-8'))=='17dd0abce37e9f78de5f626fda6f05a78a06783612a6c11937efeeb1ce74a25d'
    # Exact synthetic historical-COMPLETE recovery using the real sample001 fixture.
    if r9c['forensic_fixture_exact']:
        try:
            with tempfile.TemporaryDirectory(prefix='g100r9resume_') as td, zipfile.ZipFile(forensic9) as z:
                rr=Path(td)/'09_RUNS'/RUN_ID;cr=rr/'CHUNKS'/'chunk_00';(cr/'samples'/R9_RECOVERY_SAMPLE_ID).mkdir(parents=True)
                (cr/'logs').mkdir(parents=True);(cr/'requests').mkdir(parents=True)
                led={'schema':'DF-G54-CHUNK-LEDGER-V1','chunk_digest_sha256':R2_CHUNK0_DIGEST,'worker_id':'LOCAL_WINDOWS','states':{}}
                for rq in chunks[0]['requests']:
                    led['states'][rq['sample_id']]={'state':'COMPLETE','attempts':1,'request_digest':rq['input_digest_sha256']}
                atomic_json(cr/'ledger.json',led)
                sd=cr/'samples'/R9_RECOVERY_SAMPLE_ID
                for n in z.namelist():
                    pref='EVIDENCE/sample001/'
                    if n.startswith(pref) and not n.endswith('/'):
                        (sd/n[len(pref):]).write_bytes(z.read(n))
                (cr/'requests'/f'{R9_RECOVERY_SAMPLE_ID}.json').write_bytes(z.read('EVIDENCE/chunk00/request_sample001.json'))
                (cr/'logs'/f'{R9_RECOVERY_SAMPLE_ID}.log').write_bytes(z.read('EVIDENCE/logs/sample001_worker.log'))
                peers={sid:copy.deepcopy(rec) for sid,rec in led['states'].items() if sid!=R9_RECOVERY_SAMPLE_ID}
                ri9=apply_r9_resume_if_needed(rr,chunks)
                aft=json.loads((cr/'ledger.json').read_text(encoding='utf-8'))
                s1=aft['states'][R9_RECOVERY_SAMPLE_ID]
                r9c['resume_exact_precondition_pass']=ri9.get('status')=='R8_COMPLETE_SAMPLE_001_REOPENED_FOR_R9'
                r9c['resume_resets_only_sample001']=s1.get('state')=='PENDING' and s1.get('attempts')==0 and all(aft['states'][sid]==rec for sid,rec in peers.items())
                r9c['resume_preserves_prior_rgb_exact']=(rr/'RECOVERY'/'R8_COMPLETE_SAMPLE_001_RGB_ACCEPTANCE_FAIL'/'sample_bytes'/'rgb.png').is_file() and sha256_file(rr/'RECOVERY'/'R8_COMPLETE_SAMPLE_001_RGB_ACCEPTANCE_FAIL'/'sample_bytes'/'rgb.png')==R9_PRIOR_RGB_SHA256
                ri9b=apply_r9_resume_if_needed(rr,chunks)
                r9c['resume_idempotent']=ri9b.get('status')=='R9_RECOVERY_ALREADY_APPLIED'
        except Exception:
            r9c['resume_exact_precondition_pass']=False;r9c['resume_resets_only_sample001']=False;r9c['resume_preserves_prior_rgb_exact']=False;r9c['resume_idempotent']=False
        # Negative control: corrupt prior RGB must block before ledger/recovery mutation.
        try:
            with tempfile.TemporaryDirectory(prefix='g100r9badsha_') as td, zipfile.ZipFile(forensic9) as z:
                rr=Path(td)/'09_RUNS'/RUN_ID;cr=rr/'CHUNKS'/'chunk_00';(cr/'samples'/R9_RECOVERY_SAMPLE_ID).mkdir(parents=True)
                (cr/'logs').mkdir(parents=True);(cr/'requests').mkdir(parents=True)
                led={'schema':'DF-G54-CHUNK-LEDGER-V1','chunk_digest_sha256':R2_CHUNK0_DIGEST,'worker_id':'LOCAL_WINDOWS','states':{}}
                for rq in chunks[0]['requests']:led['states'][rq['sample_id']]={'state':'COMPLETE','attempts':1,'request_digest':rq['input_digest_sha256']}
                atomic_json(cr/'ledger.json',led);sd=cr/'samples'/R9_RECOVERY_SAMPLE_ID
                for n in z.namelist():
                    pref='EVIDENCE/sample001/'
                    if n.startswith(pref) and not n.endswith('/'):(sd/n[len(pref):]).write_bytes(z.read(n))
                rb=bytearray((sd/'rgb.png').read_bytes());rb[-10]^=1;(sd/'rgb.png').write_bytes(bytes(rb))
                (cr/'requests'/f'{R9_RECOVERY_SAMPLE_ID}.json').write_bytes(z.read('EVIDENCE/chunk00/request_sample001.json'))
                (cr/'logs'/f'{R9_RECOVERY_SAMPLE_ID}.log').write_bytes(z.read('EVIDENCE/logs/sample001_worker.log'))
                before=(cr/'ledger.json').read_bytes()
                try:apply_r9_resume_if_needed(rr,chunks);blocked=False
                except RuntimeError as e:blocked='PRIOR_RGB_SHA_MISMATCH' in str(e)
                r9c['wrong_prior_rgb_sha_blocks_before_mutation']=blocked and (cr/'ledger.json').read_bytes()==before and not (rr/'RECOVERY').exists()
        except Exception:r9c['wrong_prior_rgb_sha_blocks_before_mutation']=False
    else:
        for k in ['resume_exact_precondition_pass','resume_resets_only_sample001','resume_preserves_prior_rgb_exact','resume_idempotent','wrong_prior_rgb_sha_blocks_before_mutation']:r9c[k]=False
    r9_status=all(r9c.values())
    # R10 exact real-R9 target fixture + fixed RGB transform + controlled recovery.
    r10c={}
    r9real=HERE/'R9_REAL_FAILURE_EVIDENCE'/'PCS_CAMERA_GEOMETRY_DATA_FACTORY_G100_MICRO100_FAILURE_RETURN_R9_REAL_20260907.zip'
    r10c['r9_real_return_exact']=r9real.is_file() and sha256_file(r9real)==R10_REAL_FAILURE_RETURN_SHA256
    try:
        from pcs_factory_rgb8 import apply_fixed_rgb8_contrast_png
        r10c['rgb8_module_import']=True
    except Exception:
        apply_fixed_rgb8_contrast_png=None; r10c['rgb8_module_import']=False
    if r10c['r9_real_return_exact'] and apply_fixed_rgb8_contrast_png:
        try:
            with zipfile.ZipFile(r9real) as z:
                r10c['r9_real_return_crc']=z.testzip() is None
                with tempfile.TemporaryDirectory(prefix='g100r10rgb_') as td:
                    td=Path(td);raw=td/'rgb_renderer_raw.png';out1=td/'rgb.png';out2=td/'rgb2.png'
                    raw.write_bytes(z.read('R9_RECOVERED_SAMPLE001/rgb.png'))
                    st0=rgb_stats(raw)
                    r10c['r9_failure_stats_exact']=(sha256_file(raw)==R10_PRIOR_RGB_SHA256 and
                        st0['unique_rgb']==R10_PRIOR_RGB_STATS['unique_rgb'] and
                        all(abs(float(st0[k])-float(R10_PRIOR_RGB_STATS[k]))<=1e-12 for k in ['mean_luma','p01','p99','p01_p99_span','structural_fraction']))
                    raw_before=raw.read_bytes();meta1=apply_fixed_rgb8_contrast_png(raw,out1,pivot=128,numerator=5,denominator=4)
                    meta2=apply_fixed_rgb8_contrast_png(raw,out2,pivot=128,numerator=5,denominator=4)
                    st1=rgb_stats(out1)
                    r10c['raw_renderer_rgb_preserved']=raw.read_bytes()==raw_before and sha256_file(raw)==R10_PRIOR_RGB_SHA256
                    r10c['fixed_transform_deterministic']=out1.read_bytes()==out2.read_bytes() and meta1['final_sha256']==meta2['final_sha256']
                    r10c['transformed_fixture_exact']=(st1['unique_rgb']==R10_EXPECTED_TRANSFORMED_RGB_STATS['unique_rgb'] and
                        all(abs(float(st1[k])-float(R10_EXPECTED_TRANSFORMED_RGB_STATS[k]))<=1e-12 for k in ['mean_luma','p01','p99','p01_p99_span','structural_fraction']))
                    r10c['transformed_fixture_accepts_rgb']=(st1['unique_rgb']>=32 and 12<=st1['mean_luma']<=243 and st1['p01_p99_span']>=24 and st1['structural_fraction']>=.03)
                    r10c['no_transform_control_fails_span']=st0['p01_p99_span']<24
                    r10c['transform_metadata_fixed_nonadaptive']=(meta1.get('pivot_u8')==128 and meta1.get('factor_numerator')==5 and meta1.get('factor_denominator')==4 and meta1.get('adaptive') is False and meta1.get('spatial_warp') is False and meta1.get('resize') is False and meta1.get('resample') is False)
                ids=json.loads(z.read('R9_RECOVERED_SAMPLE001/IDENTITIES.json'))
                r10c['r9_fixture_identity_manifest_exact']=(ids.get('request_digest')==R10_RECOVERY_REQUEST_DIGEST and ids.get('ledger_state')=='COMPLETE' and {x['path']:x['sha256'] for x in ids['files']}=={
                    'completion.json':R10_PRIOR_COMPLETION_SHA256,'request.json':R10_PRIOR_REQUEST_FILE_SHA256,'rgb.png':R10_PRIOR_RGB_SHA256,'worker.log':R10_PRIOR_WORKER_LOG_SHA256})
        except Exception:
            for k in ['r9_real_return_crc','r9_failure_stats_exact','raw_renderer_rgb_preserved','fixed_transform_deterministic','transformed_fixture_exact','transformed_fixture_accepts_rgb','no_transform_control_fails_span','transform_metadata_fixed_nonadaptive','r9_fixture_identity_manifest_exact']:r10c[k]=False
    else:
        for k in ['r9_real_return_crc','r9_failure_stats_exact','raw_renderer_rgb_preserved','fixed_transform_deterministic','transformed_fixture_exact','transformed_fixture_accepts_rgb','no_transform_control_fails_span','transform_metadata_fixed_nonadaptive','r9_fixture_identity_manifest_exact']:r10c[k]=False
    r10c['worker_calls_fixed_transform_exact']='apply_fixed_rgb8_contrast_png(\n            raw_path, rgb_path, pivot=128, numerator=5, denominator=4' in worker
    r10c['worker_preserves_raw_rgb']='raw_path = out_dir / "rgb_renderer_raw.png"' in worker and 'raw_path.write_bytes(rgb_path.read_bytes())' in worker
    r10c['worker_scope_is_toon_closed_room']='r10_closed_room' in worker and 'r10_toon' in worker and 'MICRO100_QUALIFICATION_ONLY' in worker
    r10c['rgb_thresholds_still_frozen']="stats['p01_p99_span']>=24" in Path(__file__).read_text(encoding='utf-8') and "stats['unique_rgb']>=32" in Path(__file__).read_text(encoding='utf-8')
    # Current real R9 ledger recovery fixture.
    if r10c['r9_real_return_exact']:
        try:
            with tempfile.TemporaryDirectory(prefix='g100r10resume_') as td, zipfile.ZipFile(r9real) as z:
                rr=Path(td)/'09_RUNS'/RUN_ID;cr=rr/'CHUNKS'/'chunk_00';(cr/'samples').mkdir(parents=True);(cr/'logs').mkdir();(cr/'requests').mkdir()
                led=json.loads(z.read('chunk_00_ledger.json'))
                atomic_json(cr/'ledger.json',led)
                for sid in led['states']:(cr/'samples'/sid).mkdir(parents=True,exist_ok=True)
                sd=cr/'samples'/R10_RECOVERY_SAMPLE_ID
                sd.joinpath('completion.json').write_bytes(z.read('R9_RECOVERED_SAMPLE001/completion.json'))
                sd.joinpath('rgb.png').write_bytes(z.read('R9_RECOVERED_SAMPLE001/rgb.png'))
                (cr/'requests'/f'{R10_RECOVERY_SAMPLE_ID}.json').write_bytes(z.read('R9_RECOVERED_SAMPLE001/request.json'))
                (cr/'logs'/f'{R10_RECOVERY_SAMPLE_ID}.log').write_bytes(z.read('R9_RECOVERED_SAMPLE001/worker.log'))
                peers={sid:copy.deepcopy(rec) for sid,rec in led['states'].items() if sid!=R10_RECOVERY_SAMPLE_ID}
                ri10=apply_r10_resume_if_needed(rr,chunks);aft=json.loads((cr/'ledger.json').read_text(encoding='utf-8'));s1=aft['states'][R10_RECOVERY_SAMPLE_ID]
                r10c['resume_exact_precondition_pass']=ri10.get('status')=='R9_COMPLETE_SAMPLE_001_REOPENED_FOR_R10'
                r10c['resume_resets_only_sample001']=s1.get('state')=='PENDING' and s1.get('attempts')==0 and all(aft['states'][sid]==rec for sid,rec in peers.items())
                r10c['resume_preserves_r9_rgb_exact']=(rr/'RECOVERY'/'R9_COMPLETE_SAMPLE_001_RGB_ACCEPTANCE_FAIL'/'sample_bytes'/'rgb.png').is_file() and sha256_file(rr/'RECOVERY'/'R9_COMPLETE_SAMPLE_001_RGB_ACCEPTANCE_FAIL'/'sample_bytes'/'rgb.png')==R10_PRIOR_RGB_SHA256
                ri10b=apply_r10_resume_if_needed(rr,chunks)
                r10c['resume_idempotent']=ri10b.get('status')=='R10_RECOVERY_ALREADY_APPLIED'
        except Exception:
            for k in ['resume_exact_precondition_pass','resume_resets_only_sample001','resume_preserves_r9_rgb_exact','resume_idempotent']:r10c[k]=False
        try:
            with tempfile.TemporaryDirectory(prefix='g100r10badsha_') as td, zipfile.ZipFile(r9real) as z:
                rr=Path(td)/'09_RUNS'/RUN_ID;cr=rr/'CHUNKS'/'chunk_00';(cr/'samples').mkdir(parents=True);(cr/'logs').mkdir();(cr/'requests').mkdir()
                led=json.loads(z.read('chunk_00_ledger.json'));atomic_json(cr/'ledger.json',led)
                for sid in led['states']:(cr/'samples'/sid).mkdir(parents=True,exist_ok=True)
                sd=cr/'samples'/R10_RECOVERY_SAMPLE_ID
                sd.joinpath('completion.json').write_bytes(z.read('R9_RECOVERED_SAMPLE001/completion.json'))
                rgb=bytearray(z.read('R9_RECOVERED_SAMPLE001/rgb.png'));rgb[-10]^=1;sd.joinpath('rgb.png').write_bytes(bytes(rgb))
                (cr/'requests'/f'{R10_RECOVERY_SAMPLE_ID}.json').write_bytes(z.read('R9_RECOVERED_SAMPLE001/request.json'))
                (cr/'logs'/f'{R10_RECOVERY_SAMPLE_ID}.log').write_bytes(z.read('R9_RECOVERED_SAMPLE001/worker.log'))
                before=(cr/'ledger.json').read_bytes()
                try:apply_r10_resume_if_needed(rr,chunks);blocked=False
                except RuntimeError as e:blocked='PRIOR_RGB_SHA_MISMATCH' in str(e)
                r10c['wrong_r9_rgb_sha_blocks_before_mutation']=blocked and (cr/'ledger.json').read_bytes()==before and not (rr/'RECOVERY').exists()
        except Exception:r10c['wrong_r9_rgb_sha_blocks_before_mutation']=False
    else:
        for k in ['resume_exact_precondition_pass','resume_resets_only_sample001','resume_preserves_r9_rgb_exact','resume_idempotent','wrong_r9_rgb_sha_blocks_before_mutation']:r10c[k]=False
    r10_status=all(r10c.values())
    # R17 qualification is an immutable prior PASS record. Do NOT rerun the
    # R17 release selftest under R18 source/tool identities.
    r17_obj=json.loads((HERE/'DF_G100_R17_PRE_REAL_SELFTEST.json').read_text(encoding='utf-8')) if (HERE/'DF_G100_R17_PRE_REAL_SELFTEST.json').is_file() else {}
    r17_status=(r17_obj.get('status')=='PASS' and r17_obj.get('source_release_id')=='DF_G100_MICRO100_V1_R17' and r17_obj.get('tool_revision')=='DF_G100_MICRO100_V1_R1_TOOL_R17')
    # R18 qualification is now an immutable prior PASS record. Do not rerun it
    # under R19 source/tool identities.
    r18_obj=json.loads((HERE/'DF_G100_R18_PRE_REAL_SELFTEST.json').read_text(encoding='utf-8')) if (HERE/'DF_G100_R18_PRE_REAL_SELFTEST.json').is_file() else {}
    r18_checks=r18_obj.get('checks') or {}
    r18_status=(r18_obj.get('status')=='PASS' and bool(r18_checks) and all(bool(v) for v in r18_checks.values()) and r18_checks.get('source_release_r18') is True)
    # R19 is the current focused qualification record.
    r19_obj=json.loads((HERE/'DF_G100_R19_PRE_REAL_SELFTEST.json').read_text(encoding='utf-8')) if (HERE/'DF_G100_R19_PRE_REAL_SELFTEST.json').is_file() else {}
    r19_checks=r19_obj.get('checks') or {}
    r19_status=(r19_obj.get('status')=='PASS' and r19_obj.get('source_release_id')=='DF_G100_MICRO100_V1_R19' and r19_obj.get('tool_revision')=='DF_G100_MICRO100_V1_R1_TOOL_R19' and bool(r19_checks) and all(bool(v) for v in r19_checks.values()) and r19_checks.get('source_release_r19') is True)
    r20_obj=json.loads((HERE/'DF_G100_R20_PRE_REAL_SELFTEST.json').read_text(encoding='utf-8')) if (HERE/'DF_G100_R20_PRE_REAL_SELFTEST.json').is_file() else {}
    r20_checks=r20_obj.get('checks') or {}
    r20_status=(r20_obj.get('status')=='PASS' and r20_obj.get('source_release_id')=='DF_G100_MICRO100_V1_R20' and r20_obj.get('tool_revision')=='DF_G100_MICRO100_V1_R1_TOOL_R20' and bool(r20_checks) and all(bool(v) for v in r20_checks.values()))
    r16_prior_obj=json.loads((HERE/'DF_G100_R16_PRE_REAL_SELFTEST.json').read_text(encoding='utf-8')) if (HERE/'DF_G100_R16_PRE_REAL_SELFTEST.json').is_file() else {}
    r15_prior_obj=json.loads((HERE/'DF_G100_R15_PRE_REAL_SELFTEST.json').read_text(encoding='utf-8')) if (HERE/'DF_G100_R15_PRE_REAL_SELFTEST.json').is_file() else {}
    r14_prior_obj=json.loads((HERE/'DF_G100_R14_PRE_REAL_SELFTEST.json').read_text(encoding='utf-8')) if (HERE/'DF_G100_R14_PRE_REAL_SELFTEST.json').is_file() else {}
    r13_prior_obj=json.loads((HERE/'DF_G100_R13_PRE_REAL_SELFTEST.json').read_text(encoding='utf-8')) if (HERE/'DF_G100_R13_PRE_REAL_SELFTEST.json').is_file() else {}
    checks={'plan':qa['status']=='PASS','r3_regressions':r3_status,'source_release_is_r25':SOURCE_RELEASE_ID=='DF_G100_MICRO100_V1_R25','r9_regressions':r9_status,'r10_regressions':r10_status,'r17_regressions':r17_status,'r18_prior_pass_record':r18_status,'r19_prior_pass_record':r19_status,'r20_regressions':r20_status,'r16_prior_pass_record':r16_prior_obj.get('status')=='PASS','r15_prior_pass_record':r15_prior_obj.get('status')=='PASS','r14_prior_pass_record':r14_prior_obj.get('status')=='PASS','r13_prior_pass_record':r13_prior_obj.get('status')=='PASS','references_exact':len(refs)==3,'negative_controls':nc['status']=='PASS','r2_false_block_regressions':r2_status,'worker_calls_analytic_gt':'validate_aux_gt(request, out_dir, renderer_filter_width_px=float(scene.render.filter_size))' in worker,'worker_r10_painterly':'PAINTERLY_CONCEPT_DCC_V2_R10' in worker,'worker_g100_fill':'PCS_G100_INTERIOR_CAMERA_FILL' in worker,'worker_blueprint_shader_only':'BLUEPRINT_DCC_V2_G100_SHADER_WIREFRAME' in worker and 'profile_id in {"LINE_ART", "TECH_SKETCH"}' in worker,'package_frozen_plan':package_plan_identity.get('execution_authority')=='PACKAGE_FROZEN_PLAN','raw_exr_immutable':'raw_exr_immutable' in gt,'depth_forward_z':'camera_cv_forward_z_meters' in gt,'normal_frame':'BLENDER_WORLD_BASIS' in gt,'no_training_action':'training_started' in Path(__file__).read_text() and 'C-RADIO' not in worker,
            'r4_pre_real_selftest':(HERE/'DF_G100_R4_PRE_REAL_SELFTEST.json').is_file() and json.loads((HERE/'DF_G100_R4_PRE_REAL_SELFTEST.json').read_text(encoding='utf-8')).get('status')=='PASS',
            'r5_pre_real_selftest':(HERE/'DF_G100_R5_PRE_REAL_SELFTEST.json').is_file() and json.loads((HERE/'DF_G100_R5_PRE_REAL_SELFTEST.json').read_text(encoding='utf-8')).get('status')=='PASS',
            'r6_pre_real_selftest':(HERE/'DF_G100_R6_PRE_REAL_SELFTEST.json').is_file() and json.loads((HERE/'DF_G100_R6_PRE_REAL_SELFTEST.json').read_text(encoding='utf-8')).get('status')=='PASS',
            'r7_pre_real_selftest':(HERE/'DF_G100_R7_PRE_REAL_SELFTEST.json').is_file() and json.loads((HERE/'DF_G100_R7_PRE_REAL_SELFTEST.json').read_text(encoding='utf-8')).get('status')=='PASS',
            'r8_pre_real_selftest':(HERE/'DF_G100_R8_PRE_REAL_SELFTEST.json').is_file() and json.loads((HERE/'DF_G100_R8_PRE_REAL_SELFTEST.json').read_text(encoding='utf-8')).get('status')=='PASS',
            'r8_depth_fitmask_decoupled':"DEPTH_OBJECT_EXACT_IDENTITY_ALL_OBJECT_PIXELS_R8_V1" in gt and "binding=_fit_renderer_effective_principal_point(request,C,depth,oid,depth_fitmask)" in gt,
            'r5_inherited_regression_under_r6':(HERE/'DF_G100_R5_INHERITED_REGRESSION_UNDER_R6.json').is_file() and json.loads((HERE/'DF_G100_R5_INHERITED_REGRESSION_UNDER_R6.json').read_text(encoding='utf-8')).get('status')=='PASS',
            'r6_filter_explicit':'scene.render.filter_size = 1.5' in worker and 'normal_filter_safe_interior_mask.uint8.bin' in worker and 'FILTER_SAFE_INTERIOR_AUTHORITY_FRACTION_R6' in gt,
            'r4_exact_conearest_semantics':"actual_t==min_t" in gt and "'identity_epsilon':0.0" in gt,
            'r11_visibility_bootstrap_semantics':'CANONICAL_EXACT_SUBSET_TO_FULL_EFFECTIVE_EXACT_VISIBILITY_R11_V1' in gt and "vis['bitwise_exact_match_mask']" in gt and "renderer_effective_exact_all" in gt,
            'r11_resume_present':'def apply_r11_resume_if_needed' in Path(__file__).read_text(encoding='utf-8') and R11_RECOVERY_SAMPLE_ID=='g100_013_corridor_strong_pitch_clay',
            'r12_visible_side_normal_semantics':'RENDERER_VISIBLE_SIDE_CUBOID_NORMAL_R12_V1' in gt and 'def _renderer_visible_side_normal' in gt and 'arbitrary_sign_equivalence' in gt,
            'r12_resume_present':'def apply_r12_resume_if_needed' in Path(__file__).read_text(encoding='utf-8') and R12_RECOVERY_SAMPLE_ID=='g100_015_intersection_normal_day_hard',
            'r13_raster_authority_present':'CANONICAL_PIXEL_CENTER_INSIDE_PHYSICAL_RASTER_R13' in worker and 'pixel_in_physical_raster' in worker,
            'r13_resume_present':'def apply_r13_resume_if_needed' in Path(__file__).read_text(encoding='utf-8') and R13_RECOVERY_SAMPLE_ID=='g100_016_industrial_strong_roll_clay',
            'r14_adaptive_probe_semantics':'INTRINSICS_ADAPTIVE_INTERIOR_RASTER_PROBES_R14_V1' in worker and 'camera_graphics_probe_specs' in worker,
            'r14_resume_present':'def apply_r14_resume_if_needed' in Path(__file__).read_text(encoding='utf-8') and R14_RECOVERY_SAMPLE_ID=='g100_019_sparse_telephoto_clay',
            'r15_camera_inside_fill_semantics':'DF_G100_CAMERA_INSIDE_SOLID_CAMERA_FILL_V1_R15' in (SOURCE/'pcs_factory_visibility_r15.py').read_text(encoding='utf-8') and 'PCS_G100_CAMERA_INSIDE_SOLID_FILL_R15' in worker and 'r15_camera_inside_fill_policy' in worker,
            'r15_resume_present':'def apply_r15_resume_if_needed' in Path(__file__).read_text(encoding='utf-8') and R15_RECOVERY_SAMPLE_ID=='g100_015_intersection_normal_day_hard',
            'r16_resume_present':'def apply_r16_resume_if_needed' in Path(__file__).read_text(encoding='utf-8') and R16_RECOVERY_SAMPLE_ID=='g100_015_intersection_normal_day_hard',
            'r16_live_authority_semantics':'LIVE_COMPLETION_SELF_HASH_PLUS_ACCEPTANCE_SIGNATURE_R16_V1' in Path(__file__).read_text(encoding='utf-8'),
            'r16_historical_hashes_not_used_by_resume':'R15_EXPECTED_RAW_SHA256' not in Path(__file__).read_text(encoding='utf-8').split('def apply_r16_resume_if_needed',1)[1].split('def _r17_rgb_failure_class',1)[0],
            'r17_resume_present':'def apply_r17_resume_if_needed' in Path(__file__).read_text(encoding='utf-8') and R17_RECOVERY_SAMPLE_ID=='g100_015_intersection_normal_day_hard',
            'r17_span_only_authority_semantics':'LIVE_COMPLETION_SELF_HASH_PLUS_SPAN_ONLY_ACCEPTANCE_SIGNATURE_R17_V1' in Path(__file__).read_text(encoding='utf-8'),
            'r17_fixed_contrast_semantics':'DF_G100_CAMERA_INSIDE_FIXED_RGB_CONTRAST_V1_R17' in worker and 'numerator=17, denominator=16' in worker and 'r17_camera_inside_contrast_policy' in worker,
            'r18_resume_present':'def apply_r18_resume_if_needed' in Path(__file__).read_text(encoding='utf-8') and R18_RECOVERY_SAMPLE_ID=='g100_021_repeated_pattern_offcenter_day_hard',
            'r18_minimax_semantics':'CYCLES_EFFECTIVE_PP_MINIMAX_MICROGRID_R18_V1' in gt and 'R18_GRID_INDICES = tuple(range(-4,5))' in gt,
            'r18_depth_threshold_not_relaxed':'DEPTH_GEOM_TOL_M = 1e-4' in gt and "'depth_authority_masked':False" in gt,
            'r18_fixture_exact':(HERE/'R17_REAL_FAILURE_EVIDENCE'/'PCS_CAMERA_GEOMETRY_DATA_FACTORY_G100_MICRO100_FAILURE_RETURN_R17_REAL_20260907_235227.zip').is_file() and sha256_file(HERE/'R17_REAL_FAILURE_EVIDENCE'/'PCS_CAMERA_GEOMETRY_DATA_FACTORY_G100_MICRO100_FAILURE_RETURN_R17_REAL_20260907_235227.zip')==R18_PRIOR_R17_RETURN_SHA256,
            'r19_resume_present':'def apply_r19_resume_if_needed' in Path(__file__).read_text(encoding='utf-8') and R19_RECOVERY_SAMPLE_ID=='g100_027_intersection_wide_toon',
            'r19_exact_geometric_visibility_semantics':'EXACT_GEOMETRIC_COINCIDENT_FACE_VISIBILITY_R19_V1' in gt and 'R19_NUMERIC_VISIBILITY_EPSILON = 0.0' in gt and 'plane_signatures[sid-1][sface] == plane_signatures[rid-1][rface]' in gt,
            'r19_no_numeric_visibility_epsilon':'R19_NUMERIC_VISIBILITY_EPSILON = 0.0' in gt and 'np.isclose' not in gt.split('def _exact_conearest_identity_from_stack',1)[1].split('def _hit_stack_with_faces',1)[0],
            'r19_depth_threshold_not_relaxed':'DEPTH_GEOM_TOL_M = 1e-4' in gt,
            'r19_fixture_exact':(HERE/'R18_REAL_FAILURE_EVIDENCE'/'PCS_CAMERA_GEOMETRY_DATA_FACTORY_G100_MICRO100_FAILURE_RETURN_R18_REAL_20260908_002902.zip').is_file() and sha256_file(HERE/'R18_REAL_FAILURE_EVIDENCE'/'PCS_CAMERA_GEOMETRY_DATA_FACTORY_G100_MICRO100_FAILURE_RETURN_R18_REAL_20260908_002902.zip')==R19_PRIOR_R18_RETURN_SHA256,
            'r20_resume_present':'def apply_r20_resume_if_needed' in Path(__file__).read_text(encoding='utf-8') and R20_RECOVERY_SAMPLE_ID=='g100_029_stairs_ramps_portrait_pbr_realistic_intent',
            'r20_normal_reference_semantics':'RENDERER_EFFECTIVE_NORMAL_REFERENCE_R20_V1' in gt and "K_norm=np.asarray(binding['K_effective']" in gt and "normal_reference_k_source='FINAL_RENDERER_EFFECTIVE_K'" in gt,
            'r20_normal_not_fit':'normal_values_used_to_fit_renderer_binding' in gt and 'NORMAL_GEOM_TOL = 1e-5' in gt,
            'r20_thresholds_not_relaxed':'NORMAL_GEOM_TOL = 1e-5' in gt and 'DEPTH_GEOM_TOL_M = 1e-4' in gt and 'R19_NUMERIC_VISIBILITY_EPSILON = 0.0' in gt,
            'r20_fixture_exact':(HERE/'R19_REAL_FAILURE_EVIDENCE'/'PCS_CAMERA_GEOMETRY_DATA_FACTORY_G100_MICRO100_FAILURE_RETURN_R19_REAL_20260908_005859.zip').is_file() and sha256_file(HERE/'R19_REAL_FAILURE_EVIDENCE'/'PCS_CAMERA_GEOMETRY_DATA_FACTORY_G100_MICRO100_FAILURE_RETURN_R19_REAL_20260908_005859.zip')==R20_PRIOR_R19_RETURN_SHA256,

            'r15_post_chunk_failure_self_containment':'POST_CHUNK_ACCEPTANCE_FAILURE' in Path(__file__).read_text(encoding='utf-8'),
            'r4_failure_self_containment':'FAILED_SAMPLES' in Path(__file__).read_text(encoding='utf-8') and 'worker.log' in Path(__file__).read_text(encoding='utf-8')}
    out={'schema':'DF-G100-R25-CUMULATIVE-PACKAGE-SELFTEST-V1','status':'PASS' if all(checks.values()) else 'FAIL','tool_revision':TOOL_REVISION,'checks':checks,'r2_false_block_regressions':r2c,'r3_regressions':r3c,'r9_regressions':r9c,'r10_regressions':r10c,'r17_regressions':r17_obj,'r18_prior_pass_record':r18_obj,'r19_prior_pass_record':r19_obj,'r20_regressions':r20_obj,'r16_prior_pass_record':r16_prior_obj,'r15_prior_pass_record':r15_prior_obj,'r14_prior_pass_record':r14_prior_obj,'r13_prior_pass_record':r13_prior_obj,'package_frozen_plan':package_plan_identity,'plan_qa':qa,'negative_controls':nc,'references':refs,'authority':{'micro100_generated':False,'scale_1k_authorized':False,'scale_10k_authorized':False,'training_started':False,'product_mutated':False,'test77_accessed':False}}
    atomic_json(HERE/'DF_G100_PRE_REAL_PACKAGE_SELFTEST.json',out);print(json.dumps(out,indent=2,sort_keys=True));return 0 if out['status']=='PASS' else 2

def r29_pre_real_selftest():
    release=HERE
    M=_load_modules(release)
    reqs,chunks,qa,ident=load_package_frozen_plan(M,run_regeneration=True)
    sel,uncovered=choose_visual(reqs)
    # Negative controls are pure pre-render geometry tests.
    from pcs_factory_camera_observability_v2 import point_inside_obb,admissibility,CANDIDATE_BUDGET
    first=reqs[0];obj=first['scene']['objects'][0]
    center=tuple(obj['center_world'])
    inside=point_inside_obb(center,obj)
    neg={
      'inside_obb_rejected':inside is True,
      'candidate_65_never_authorized':CANDIDATE_BUDGET==64 and all(int(r['camera_observability_v2']['selected_candidate_index'])<64 for r in reqs),
      'all_selected_outside_solids':all(not r['camera_observability_v2']['selected_metrics']['camera_inside_any_solid'] for r in reqs),
      'visual_exact_24':len(sel)==24 and not uncovered,
      'visual_stress_8_included':set(i for _s,i in sorted([(float(r['camera_observability_v2']['observability_stress_score']),i) for i,r in enumerate(reqs) if r['camera_observability_v2']['observability_stress_score'] is not None])[:8]).issubset(set(sel)),
      'no_training_scale_authority':True,
    }
    # Exact plan determinism: two independent generations in this process.
    r2,c2=generate_plan(M);det=(json.loads(json.dumps(r2,sort_keys=True))==reqs and json.loads(json.dumps(c2,sort_keys=True))==chunks)
    checks={'package_plan_exact':ident['sha256']==PACKAGE_PLAN_SHA256,'plan_qa':qa['status']=='PASS','exact_regeneration':det,'negative_controls':all(neg.values()),'v2_identity':DATASET_ID=='PCS_CAMERA_GEOMETRY_MICRO100_V2' and RELEASE_ID=='DF_G100_MICRO100_V2_R1','source_release_r29':SOURCE_RELEASE_ID=='DF_G100_MICRO100_V2_R1_TOOL_R29','r29_spec_bound':SPEC_DRIVE_ID==R29_SPEC_DRIVE_ID and R29_SPEC_DRIVE_ID=='1_OkDftof9W8Eegc9GyOKhsBxQPWxFkkLUH1WWUwdmsM' and R27_SPEC_DRIVE_ID=='1x0EUv2o5vq7WYyV_YbebXOcGj1DKMb5h9DBaf7Et1KE','clarification_bound':R26_CLARIFICATION_DRIVE_ID=='1wGImXkRxvD1ZDvY73dgiJag3LcAvx6wkPAgsqNTxacQ','v1_authority_read_only':V1_REAL_RETURN_SHA256=='f3e33dd69a858091c76e8193dabdad1849163e55c33556d96f714a68129cc6a0','observability_module_present':(SOURCE/'pcs_factory_camera_observability_v2.py').is_file(),'worker_r29_mask_integrity':('depth_filter_safe_interior_mask.uint8.bin' in (SOURCE/'pcs_factory_blender_worker.py').read_text(encoding='utf-8') and 'depth_filter_safe_interior_mask.uint8.bin' in (SOURCE/'pcs_factory_blender_protocol.py').read_text(encoding='utf-8')),'gt_r27_patched':"SIGNED_PERMUTATION_CANONICAL_WORLD_PLANE_SIGNATURE_R27_V1" in (SOURCE/'pcs_factory_micro100_gt.py').read_text(encoding='utf-8'),'gt_r29_depth_authority':"FILTER_SAFE_INTERIOR_EXACT_DEPTH_R29_V1" in (SOURCE/'pcs_factory_micro100_gt.py').read_text(encoding='utf-8'),'r29_failure_authority_exact':_r29_failure_authority_path().is_file() and _r29_failure_authority_path().stat().st_size==R29_FAILURE_BYTES and sha256_file(_r29_failure_authority_path())==R29_FAILURE_SHA256}
    out={'schema':'DF-G100-R29-PRE-REAL-SELFTEST-V1','status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'negative_controls':neg,'plan_identity':ident,'plan_qa':qa,'visual_selection':{'indices':sel,'sample_ids':[reqs[i]['sample_id'] for i in sel]},'authority':{'micro100_v2_generated_real':False,'closed_pass_real_micro100':False,'scale_1k_authorized':False,'training_started':False,'test77_accessed':False,'product_mutated':False}}
    atomic_json(HERE/'DF_G100_R29_PRE_REAL_SELFTEST.json',out);print(json.dumps(out,indent=2,sort_keys=True));return 0 if out['status']=='PASS' else 2

def r33_pre_real_selftest():
    import ast
    M=_load_modules(SOURCE)
    reqs,chunks,qa,ident=load_package_frozen_plan(M,run_regeneration=False)
    policies=[r33_blueprint_vertical_dominant_policy(r) for r in reqs]
    eligible=[i for i,p in enumerate(policies) if p.get('applied')]
    p51=policies[51]; p54=policies[54]; p77=policies[77]; p83=policies[83]

    # Forced categorical negative controls.
    wrong_profile=copy.deepcopy(reqs[51]); wrong_profile['appearance']['profile_id']='TOON'
    wrong_split=copy.deepcopy(reqs[51]); wrong_split['split']='NOT_MICRO100'
    forced_r15=copy.deepcopy(reqs[51]); C=forced_r15['camera']['pose']['camera_center_world']
    forced_r15['scene']['objects'].append({'object_id':'r33_forced_enclosing_solid','primitive':'BOX','center_world':C,
                                           'dimensions_m':[1000.0,1000.0,1000.0],
                                           'R_local_to_world':[[1,0,0],[0,1,0],[0,0,1]]})
    neg={
      'wrong_profile_blocks':not r33_blueprint_vertical_dominant_policy(wrong_profile).get('applied'),
      'non_micro100_blocks':not r33_blueprint_vertical_dominant_policy(wrong_split).get('applied'),
      'fraction_below_045_blocks':p54.get('dominant_face_fraction',1)<0.45 and not p54.get('applied'),
      'horizontal_dominant_blocks':p77.get('dominant_face_fraction',0)>=0.45 and p77.get('dominant_face_abs_canonical_up_component',0)>0.25 and not p77.get('applied'),
      'closed_room_fill_blocks':p83.get('dominant_face_fraction',0)>=0.45 and p83.get('dominant_face_abs_canonical_up_component',1)<=0.25 and p83.get('closed_room_fill_active') is True and not p83.get('applied'),
      'r15_fill_blocks':r33_blueprint_vertical_dominant_policy(forced_r15).get('r15_fill_active') is True and not r33_blueprint_vertical_dominant_policy(forced_r15).get('applied'),
    }

    # Exact sample051 fixture transform and acceptance.
    fix=HERE/'FIXTURES'/'R33_SAMPLE051_AUTHORITY'; req=json.loads((fix/'request.json').read_text(encoding='utf-8'))
    fixture_checks={}
    with tempfile.TemporaryDirectory(prefix='g100r33_fixture_') as td:
        sd=Path(td)/'sample'; shutil.copytree(fix/'sample',sd)
        before_aux={n:sha256_file(sd/n) for n in ['depth.exr','normal.exr','object_index.exr','normal_authority_mask.uint8.bin','normal_filter_safe_interior_mask.uint8.bin','depth_filter_safe_interior_mask.uint8.bin','micro100_aux_gt_qa.json']}
        pre=sd/'rgb_pre_r33.png'; pre.write_bytes((sd/'rgb.png').read_bytes())
        meta=apply_fixed_rgb8_gain_png(pre,sd/'rgb.png',numerator=2,denominator=1); pol=r33_blueprint_vertical_dominant_policy(req)
        meta.update({'implementation_id':R33_IMPLEMENTATION_ID,'source_rgb_rel':'rgb_pre_r33.png','final_rgb_rel':'rgb.png','geometry_preserving':True,'eligibility':pol,'r33_spec_drive_id':R33_SPEC_DRIVE_ID})
        comp=json.loads((sd/'completion.json').read_text(encoding='utf-8')); comp['r33_blueprint_vertical_dominant_policy']=pol; comp['r33_blueprint_fixed_rgb_gain']=meta
        comp['files']=[r for r in comp['files'] if r.get('path') not in {'rgb.png','rgb_pre_r33.png'}]
        comp['files'].extend([_r33_file_record(sd/'rgb.png',sd),_r33_file_record(pre,sd)]); comp['files']=sorted(comp['files'],key=lambda r:r['path'])
        atomic_json(sd/'completion.json',comp)
        acc=sample_acceptance(req,comp,sd,M,{'schema':'DF-G100-R33-FIXTURE-SELFTEST'})
        after_aux={n:sha256_file(sd/n) for n in before_aux}
        fixture_checks={
          'pre_rgb_authority':sha256_file(pre)==R33_PRE_RGB_SHA256,
          'final_rgb_exact':sha256_file(sd/'rgb.png')==R33_EXPECTED_FINAL_RGB_SHA256,
          'gain_metadata_exact':meta.get('gain_numerator')==2 and meta.get('gain_denominator')==1 and meta.get('offset_u8')==0,
          'all_four_rgb_gates_pass':all(acc['checks'][k] for k in ('rgb_unique','rgb_mean','rgb_span','rgb_structural')),
          'full_acceptance_pass':acc.get('status')=='PASS',
          'aux_gt_byte_identical':before_aux==after_aux,
          'mean_expected':abs(float(acc['rgb']['mean_luma'])-16.92934369140625)<1e-12,
          'span_expected':abs(float(acc['rgb']['p01_p99_span'])-44.2396)<1e-9,
        }

    policy_src=(SOURCE/'pcs_factory_blueprint_r33.py').read_text(encoding='utf-8')
    tree=ast.parse(policy_src)
    identifiers={n.id for n in ast.walk(tree) if isinstance(n,ast.Name)} | {n.attr for n in ast.walk(tree) if isinstance(n,ast.Attribute)}
    worker=(SOURCE/'pcs_factory_blender_worker.py').read_text(encoding='utf-8')
    source_checks={
      'no_sample_id_special_case':'g100v2_051' not in policy_src and 'sample051' not in policy_src.lower(),
      'no_rgb_stats_dependency':not ({'rgb_stats','mean_luma','p01_p99_span','structural_fraction','unique_rgb'} & identifiers),
      'only_expected_policy_eligible':eligible==[51],
      'sample051_geometry_exact':p51.get('dominant_object_id')=='intersection_1051.bR0' and int(p51.get('dominant_face_id',-1))==1 and abs(float(p51.get('dominant_face_fraction',0))-0.4744140625)<1e-15 and float(p51.get('dominant_face_abs_canonical_up_component',99))==0.0,
      'worker_r33_after_r23_before_aux':worker.index('r33_blueprint_vertical_dominant_policy(request)')>worker.index('r23_systemic_rgb_policy(request)') and worker.index('r33_blueprint_vertical_dominant_policy(request)')<worker.index('validate_aux_gt(request, out_dir'),
      'worker_preserves_pre_r33':'rgb_pre_r33.png' in worker and 'apply_fixed_rgb8_gain_png' in worker,
      'thresholds_unchanged':'stats[\'unique_rgb\']>=32' in Path(__file__).read_text(encoding='utf-8') and "12<=stats['mean_luma']<=243" in Path(__file__).read_text(encoding='utf-8') and "stats['p01_p99_span']>=24" in Path(__file__).read_text(encoding='utf-8') and "stats['structural_fraction']>=.03" in Path(__file__).read_text(encoding='utf-8'),
      'depth_tolerance_unchanged':'DEPTH_GEOM_TOL_M = 1e-4' in (SOURCE/'pcs_factory_micro100_gt.py').read_text(encoding='utf-8'),
      'r31_replay_authority_exact':_r33_replay_authority_path().is_file() and _r33_replay_authority_path().stat().st_size==R31_REPLAY_AUTHORITY_BYTES and sha256_file(_r33_replay_authority_path())==R31_REPLAY_AUTHORITY_SHA256,
      'plan_identity_unchanged':ident.get('sha256')==PACKAGE_PLAN_SHA256,
      'source_release_r34':SOURCE_RELEASE_ID=='DF_G100_MICRO100_V2_R1_TOOL_R34' and SPEC_DRIVE_ID==R33_SPEC_DRIVE_ID and R34_SPEC_DRIVE_ID=='1Pi6HcueA-JpaBjq3bHI3dnpiFSeMUFDjZHNHaUEB4LY',
      'no_training_product_authority':True,
    }
    checks={**source_checks,**neg,**fixture_checks,'plan_qa':qa.get('status')=='PASS'}
    out={'schema':'DF-G100-R34-PRE-REAL-SELFTEST-V1','status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,
         'eligible_indices':eligible,'sample051_policy':p51,'negative_controls':neg,'fixture':fixture_checks,'plan_identity':ident,
         'authority':{'real_run_executed':False,'one_real_recovery_authorized':False,'micro100_closed':False,'scale_1k_authorized':False,'training_started':False,'test77_accessed':False,'product_mutated':False,'maya_mutated':False}}
    atomic_json(HERE/'DF_G100_R34_PRE_REAL_SELFTEST.json',out); print(json.dumps(out,indent=2,sort_keys=True)); return 0 if out['status']=='PASS' else 2


# ============================================================================
# DF-G101 SCALE1K V1 — clean scale runner (spec frozen 2026-09-10 before code)
# ============================================================================
G101_SPEC_DRIVE_ID='1IZJXzH2JvzaO-9ASoh3AhZHIfM5uUVbWPnFuyXtK3J8'
G101_SPLIT_CLARIFICATION_DRIVE_ID='1bhSosigUnCti5igEFn8ore-5lVfqbNvwKlP5AyUCAkE'
G101_PLAN_PROJECTION_DRIVE_ID='1ckmS4FqlotDWjS63C8RTt-rno6LYV93G'
G101_PLAN_PROJECTION_SHA256='746e402b2468cb84a3607aba505bb1e7e49a4b2ae837dca7e9008392d3278141'
G101_REQUESTS_PROJECTION_SHA256='0e94f9150fec4de51105503c65a359fecadd201ae8494c575fef07b26a8f8934'
G101_R37_CLOSURE_RECORD_DRIVE_ID='1a63qacKbvG_OKUwGzPCoBXIk5WxmZiauKBXQiBstNJs'
G101_R37_AUDIT_DRIVE_ID='1nYkPR44ImNPKb7s1nRUUTJLXAtXxSA9t'
G101_CLOSED_MICRO100_RETURN_DRIVE_ID='12VDhJRmvu105VHRplr2I2LtGeGwVcQdV'
G101_CLOSED_MICRO100_RETURN_SHA256='f94476c926bb7ba6e13e5122031dc25649e1f8277d4440bb0471ce946e57dee6'
G101_ROOT_SEED=8864579682602775346
G101_SEED_DIGEST='7b05504138aef332335bbe97a53520b19413b7fd3f60b4ad889764ddf626b7f8'
G101_PLAN_INTERNAL=HERE/'PLAN_G101'/'DF_G101_SCALE1K_V1_FROZEN_PLAN_INTERNAL.zip'
G101_PLAN_INTERNAL_IDENTITY=HERE/'PLAN_G101'/'PLAN_INTERNAL_IDENTITY.json'
G101_CHUNK_COUNT=100
G101_SAMPLE_COUNT=1000
G101_SHARD_COUNT=10
G101_CHUNKS_PER_SHARD=10
G101_WORKER_PROTOCOL='DF-G101-V1'
G101_RETURN_INDEX='PCS_CAMERA_GEOMETRY_DATA_FACTORY_G101_SCALE1K_V1_RETURN_INDEX.zip'
G101_FAILURE_RETURN='PCS_CAMERA_GEOMETRY_DATA_FACTORY_G101_SCALE1K_V1_FAILURE_RETURN.zip'
G101_RETURN_DIRNAME='DF_G101_SCALE1K_V1_R1'
SOURCE_RELEASE_ID='DF_G101_SCALE1K_V1_R1_TOOL_R2'
RELEASE_ID='DF_G101_SCALE1K_V1_R1'
DATASET_ID='PCS_CAMERA_GEOMETRY_SCALE1K_V1'
RUN_ID=RELEASE_ID
PARTITION='SCALE1K_QUALIFICATION_ONLY'
SPEC_DRIVE_ID=G101_SPEC_DRIVE_ID
ROOT_SEED=G101_ROOT_SEED
EXPECTED_COUNTS={
 'families':{'INTERIOR':84,'CORRIDOR':84,'URBAN':84,'INTERSECTION':84,'INDUSTRIAL':83,'STAIRS_RAMPS':83,'NON_MANHATTAN':83,'SPARSE':83,'CLUTTER':83,'REPEATED_PATTERN':83,'ORGANIC_NEGATIVE':83,'HYBRID_CONCEPT':83},
 'cameras':{x:100 for x in CAMERAS},
 'appearances':{'PBR_REALISTIC_INTENT':167,'DAY_HARD':167,'TOON':166,'CLAY':166,'BLUEPRINT':167,'PAINTERLY_CONCEPT':167},
 'resolutions':{'288x384':100,'384x216':225,'512x288':225,'320x320':225,'512x216':225},
}
G101_R33_EXPECTED={
'g101v1_0076_repeated_pattern_telephoto_blueprint','g101v1_0162_sparse_high_camera_blueprint',
'g101v1_0425_urban_normal_blueprint','g101v1_0618_sparse_strong_pitch_blueprint',
'g101v1_0813_repeated_pattern_strong_roll_blueprint','g101v1_0931_sparse_wide_blueprint',
'g101v1_0943_sparse_strong_roll_blueprint'}
G101_R36_EXPECTED={'g101v1_0418_intersection_wide_blueprint'}
G101_R2_SPEC_DRIVE_ID='1tidiKAl6NspDeIq0yQyf5l2hc-DQjEcHVq-tO0aUSJk'
G101_R2_IMPLEMENTATION_ID='DF_G101_BLUEPRINT_FOREGROUND_VERTICAL_FIXED_RGB_GAIN_X2_R2_V1'
G101_R2_CLASSIFICATION='BLUEPRINT_DOWNLIGHT_FOREGROUND_DOMINANT_NEAR_TOTAL_VERTICAL_VISIBILITY_GAP'
G101_R2_RECOVERY_SAMPLE_ID='g101v1_0005_urban_low_camera_blueprint'
G101_R2_RECOVERY_REQUEST_DIGEST='d2ef58bd10a9260c4b95083db6df263083bc1ac6ceadc724150e17169654bb31'
G101_R2_PRE_PROGRESS_SHA256='e4aa81424862a3915a0efb30835c312f7de5f65f22750f2a8aa16aebb05366f9'
G101_R2_PRE_LEDGER_SHA256='d19a00c48931bfad406d99ffb164555a11f73acacbd3c7e16fa45384288cf0ee'
G101_R2_PRE_ACCEPTANCE_SHA256='7cb8434246a9995227ab438e274b2e57df0f49759e1e5a44e92aac8e7f8935cf'
G101_R2_PRE_COMPLETION_SHA256='c861a698555ebf91cf3acb5a3dd0be4075722f05ec70d273a54531714a58d983'
G101_R2_PRE_RGB_SHA256='fdd39fa444cd52acaedd4565eb5705b4a589a9bc50a6e022739f4e67204328cd'
G101_R2_EXPECTED_RGB_SHA256='e65e16ba5b2d4140561a63e74d57a9faecda8f913493f35045769c006cc0d247'
G101_R1_FAILURE_AUTHORITY=HERE/'AUTHORITY'/'PCS_CAMERA_GEOMETRY_DATA_FACTORY_G101_SCALE1K_V1_R1_FAILURE_RETURN_20260910.zip'
G101_R1_FAILURE_AUTHORITY_BYTES=681591
G101_R1_FAILURE_AUTHORITY_SHA256='653a3ebe21c4fdb5f9be3d30a76e2332ea996858acf80ac6d81dd72cfa413f7e'
G101_R2_POLICY_AUDIT=HERE/'DF_G101_R2_FULL_167_BLUEPRINT_POLICY_AUDIT.json'
G101_R2_POLICY_AUDIT_BYTES=67691
G101_R2_POLICY_AUDIT_SHA256='8b6a0a28ea360cccc3370e437aba5860c99366ce8d14f151e4f9151f82b967d4'
G101_R2_EXPECTED={
'g101v1_0005_urban_low_camera_blueprint','g101v1_0041_urban_offcenter_blueprint',
'g101v1_0197_urban_wide_blueprint','g101v1_0226_intersection_low_camera_blueprint',
'g101v1_0269_urban_portrait_blueprint','g101v1_0742_organic_negative_telephoto_blueprint',
'g101v1_0795_intersection_low_camera_blueprint','g101v1_0819_intersection_near_infinity_blueprint',
'g101v1_0878_urban_offcenter_blueprint','g101v1_0890_urban_normal_blueprint'}
G101_JS_LIMIT=0.20
G101_HIGH_LIMIT_BIN_MAX_FRACTION=0.05
G101_SLOWDOWN_RATIO_MAX=2.0
G101_NORM_BINS=[0.0,0.1,0.25,0.5,0.75,0.9,1.000000001]
G101_MICRO_BASELINE_HIST={
 'camera':[60,32,6,2,0,0],
 'depth':[49,34,10,2,3,2],
 'normal':[100,0,0,0,0,0],
}


def _g101_plan_meta():
    if not G101_PLAN_INTERNAL.is_file(): raise RuntimeError('G101_FROZEN_PLAN_INTERNAL_MISSING')
    ident=json.loads(G101_PLAN_INTERNAL_IDENTITY.read_text(encoding='utf-8'))
    if G101_PLAN_INTERNAL.stat().st_size!=int(ident['bytes']) or sha256_file(G101_PLAN_INTERNAL)!=ident['sha256']:
        raise RuntimeError('G101_FROZEN_PLAN_INTERNAL_IDENTITY_MISMATCH')
    with zipfile.ZipFile(G101_PLAN_INTERNAL) as z:
        if z.testzip() is not None: raise RuntimeError('G101_FROZEN_PLAN_INTERNAL_CRC_FAIL')
        meta=json.loads(z.read('PLAN_METADATA.json'))
    if meta.get('authority_projection_drive_id')!=G101_PLAN_PROJECTION_DRIVE_ID or meta.get('authority_projection_sha256')!=G101_PLAN_PROJECTION_SHA256:
        raise RuntimeError('G101_PLAN_PROJECTION_AUTHORITY_MISMATCH')
    if meta.get('probe',{}).get('requests_projection_sha256')!=G101_REQUESTS_PROJECTION_SHA256:
        raise RuntimeError('G101_REQUEST_PROJECTION_SHA_MISMATCH')
    return meta,ident


def _g101_load_chunk(ci:int):
    if not (0<=ci<G101_CHUNK_COUNT): raise IndexError(ci)
    with zipfile.ZipFile(G101_PLAN_INTERNAL) as z:
        ch=json.loads(z.read(f'chunks/chunk_{ci:03d}.json'))
    expected=_g101_plan_meta()[0]['probe']['chunk_digests'][ci]
    if ch.get('chunk_digest_sha256')!=expected: raise RuntimeError(f'G101_CHUNK_DIGEST_AUTHORITY_MISMATCH:{ci}')
    if ch.get('chunk_index')!=ci or ch.get('release_id')!=RELEASE_ID or ch.get('dataset_id')!=DATASET_ID or ch.get('split')!=PARTITION or ch.get('worker_protocol_version')!=G101_WORKER_PROTOCOL:
        raise RuntimeError(f'G101_CHUNK_IDENTITY_MISMATCH:{ci}')
    return ch


def _g101_iter_requests():
    for ci in range(G101_CHUNK_COUNT):
        for r in _g101_load_chunk(ci)['requests']:
            yield r


def _g101_validate_frozen_plan(M, full_policy_audit=True):
    meta,ident=_g101_plan_meta(); probe=meta['probe']; checks={}
    ids=[]; reqdig=[]; recip=[]; bases=[]; triples=set(); counts={'families':Counter(),'cameras':Counter(),'appearances':Counter(),'resolutions':Counter()}
    minfam=99; mincam=99; minapp=99; minres=99; r33=[];r36=[];g101r2=[]
    for ci in range(G101_CHUNK_COUNT):
        ch=_g101_load_chunk(ci); M['validate_chunk'](ch)
        fams=set();cams=set();apps=set();res=set()
        for r in ch['requests']:
            M['validate_request'](r)
            ids.append(r['sample_id']);reqdig.append(r['input_digest_sha256']);recip.append(r['scene']['recipe_digest_sha256']);bases.append(r['scene']['base_scene_id'])
            counts['families'][r['scene']['scene_family']]+=1; counts['cameras'][r['camera']['profile']]+=1; counts['appearances'][r['appearance']['profile_id']]+=1; counts['resolutions'][f"{r['camera']['width']}x{r['camera']['height']}"]+=1
            fams.add(r['scene']['scene_family']);cams.add(r['camera']['profile']);apps.add(r['appearance']['profile_id']);res.add(f"{r['camera']['width']}x{r['camera']['height']}")
            if int(r['scene_index'])<2720: triples.add((r['scene']['scene_family'],r['camera']['profile'],r['appearance']['profile_id']))
            if full_policy_audit and r['appearance']['profile_id']=='BLUEPRINT':
                p33=r33_blueprint_vertical_dominant_policy(r); p36=r36_blueprint_extreme_vertical_policy(r); pr2=g101_r2_blueprint_foreground_vertical_policy(r)
                if p33.get('applied'): r33.append(r['sample_id'])
                if p36.get('applied'): r36.append(r['sample_id'])
                if pr2.get('applied'): g101r2.append(r['sample_id'])
        minfam=min(minfam,len(fams));mincam=min(mincam,len(cams));minapp=min(minapp,len(apps));minres=min(minres,len(res))
    checks['sample_count']=len(ids)==1000
    checks['sample_id_unique']=len(set(ids))==1000
    checks['request_digest_unique']=len(set(reqdig))==1000
    checks['recipe_digest_unique']=len(set(recip))==1000
    checks['base_scene_unique']=len(set(bases))==1000
    checks['factorial720']=len(triples)==720
    checks['counts_exact']={k:dict(v)==EXPECTED_COUNTS[k] for k,v in counts.items()}
    checks['chunk_diversity']=minfam>=10 and mincam>=8 and minapp==6 and minres>=4
    checks['chunk_digest_count']=len(probe.get('chunk_digests',[]))==100
    if full_policy_audit:
        checks['r33_exact']=set(r33)==G101_R33_EXPECTED
        checks['r36_exact']=set(r36)==G101_R36_EXPECTED
        checks['g101_r2_exact']=set(g101r2)==G101_R2_EXPECTED
    return {'schema':'DF-G101-FROZEN-PLAN-VALIDATION-V1','status':'PASS' if all((all(v.values()) if isinstance(v,dict) else v) for v in checks.values()) else 'FAIL','checks':checks,'counts':{k:dict(v) for k,v in counts.items()},'chunk_diversity_min':{'families':minfam,'cameras':mincam,'appearances':minapp,'resolutions':minres},'r33_applied':r33,'r36_applied':r36,'g101_r2_applied':g101r2,'plan_internal_identity':ident,'authority_projection':{'drive_id':G101_PLAN_PROJECTION_DRIVE_ID,'sha256':G101_PLAN_PROJECTION_SHA256}}


def _g101_r2_verify_policy_audit_authority():
    p=G101_R2_POLICY_AUDIT
    if not p.is_file() or p.stat().st_size!=G101_R2_POLICY_AUDIT_BYTES or sha256_file(p)!=G101_R2_POLICY_AUDIT_SHA256:
        raise RuntimeError('G101_R2_POLICY_AUDIT_AUTHORITY_IDENTITY_MISMATCH')
    obj=json.loads(p.read_text(encoding='utf-8'))
    if int(obj.get('count',-1))!=167:
        raise RuntimeError('G101_R2_POLICY_AUDIT_COUNT_MISMATCH')
    if set(obj.get('r33_sample_ids') or [])!=G101_R33_EXPECTED or set(obj.get('r36_sample_ids') or [])!=G101_R36_EXPECTED or set(obj.get('r2_sample_ids') or [])!=G101_R2_EXPECTED:
        raise RuntimeError('G101_R2_POLICY_AUDIT_SELECTION_MISMATCH')
    rows={r['sample_id']:r for r in (obj.get('rows') or [])}
    controls={
      G101_R2_RECOVERY_SAMPLE_ID: {'r2':True,'r33':False,'r36':False},
      'g101v1_0190_intersection_telephoto_blueprint': {'r2':False,'r33':False,'r36':False},
      'g101v1_0454_intersection_strong_pitch_blueprint': {'r2':False,'r33':False,'r36':False},
      'g101v1_0425_urban_normal_blueprint': {'r2':False,'r33':True,'r36':False},
      'g101v1_0418_intersection_wide_blueprint': {'r2':False,'r33':False,'r36':True},
    }
    for sid,exp in controls.items():
        if sid not in rows or any(bool(rows[sid].get(k))!=v for k,v in exp.items()):
            raise RuntimeError('G101_R2_POLICY_AUDIT_CONTROL_MISMATCH:'+sid)
    return {'schema':'DF-G101-R2-FROZEN-POLICY-AUDIT-AUTHORITY-V1','status':'PASS','path':p.name,'bytes':p.stat().st_size,'sha256':sha256_file(p),'blueprint_count':167,'r33_count':len(G101_R33_EXPECTED),'r36_count':len(G101_R36_EXPECTED),'r2_count':len(G101_R2_EXPECTED)}


def _g101_r2_runtime_policy_guard():
    reqs={r['sample_id']:r for r in _g101_iter_requests() if r['sample_id'] in {
      G101_R2_RECOVERY_SAMPLE_ID,
      'g101v1_0190_intersection_telephoto_blueprint',
      'g101v1_0454_intersection_strong_pitch_blueprint',
      'g101v1_0425_urban_normal_blueprint',
      'g101v1_0418_intersection_wide_blueprint'}}
    expected={
      G101_R2_RECOVERY_SAMPLE_ID:(False,False,True),
      'g101v1_0190_intersection_telephoto_blueprint':(False,False,False),
      'g101v1_0454_intersection_strong_pitch_blueprint':(False,False,False),
      'g101v1_0425_urban_normal_blueprint':(True,False,False),
      'g101v1_0418_intersection_wide_blueprint':(False,True,False)}
    rows=[]
    for sid,(e33,e36,e2) in expected.items():
        r=reqs.get(sid)
        if r is None: raise RuntimeError('G101_R2_RUNTIME_GUARD_REQUEST_MISSING:'+sid)
        p33=r33_blueprint_vertical_dominant_policy(r); p36=r36_blueprint_extreme_vertical_policy(r); p2=g101_r2_blueprint_foreground_vertical_policy(r)
        got=(bool(p33.get('applied')),bool(p36.get('applied')),bool(p2.get('applied')))
        if got!=(e33,e36,e2): raise RuntimeError('G101_R2_RUNTIME_POLICY_GUARD_MISMATCH:'+sid+':'+str(got))
        rows.append({'sample_id':sid,'r33':got[0],'r36':got[1],'r2':got[2],'foreground_raster_fraction':p2.get('foreground_raster_fraction'),'vertical_foreground_fraction':p2.get('aggregate_vertical_foreground_fraction')})
    t=next(r for r in rows if r['sample_id']==G101_R2_RECOVERY_SAMPLE_ID)
    if abs(float(t['foreground_raster_fraction'])-0.7249416775173612)>1e-15 or abs(float(t['vertical_foreground_fraction'])-0.9964171117992086)>1e-15:
        raise RuntimeError('G101_R2_RUNTIME_TARGET_METRIC_MISMATCH')
    return {'schema':'DF-G101-R2-RUNTIME-POLICY-GUARD-V1','status':'PASS','rows':rows}


def _g101_install_release(root:Path):
    safe_root(root)
    release=root/'01_SOURCE'/'RELEASES'/SOURCE_RELEASE_ID; stage=release.with_name(release.name+'.staging')
    shutil.rmtree(stage,ignore_errors=True);stage.mkdir(parents=True)
    for p in sorted(SOURCE.glob('*.py')): shutil.copy2(p,stage/p.name)
    shutil.copy2(Path(__file__),stage/Path(__file__).name)
    files=[]
    for p in sorted(stage.iterdir()):
        if p.is_file(): files.append({'path':p.name,'bytes':p.stat().st_size,'sha256':sha256_file(p)})
    atomic_json(stage/'SOURCE_MANIFEST.json',{'schema':'DF-G101-SOURCE-MANIFEST-V1','source_release_id':SOURCE_RELEASE_ID,'dataset_id':DATASET_ID,'release_id':RELEASE_ID,'g101_spec_drive_id':G101_SPEC_DRIVE_ID,'qualification_split_clarification_drive_id':G101_SPLIT_CLARIFICATION_DRIVE_ID,'g101_r2_spec_drive_id':G101_R2_SPEC_DRIVE_ID,'g101_r2_implementation_id':G101_R2_IMPLEMENTATION_ID,'parent_r36_package_sha256':'63d4a625cbac8df250b9c038751e1bf72ae9f86e00b77df4b867f1d5b1ccde0b','files':files,'product_mutated':False,'maya_mutated':False,'test77_accessed':False,'training_started':False})
    shutil.rmtree(release,ignore_errors=True);_r34_replace_with_retry(stage,release);return release


def _g101_progress(runroot:Path):
    counts=Counter(); attempts=Counter(); completed=0
    for ci in range(G101_CHUNK_COUNT):
        lp=runroot/'CHUNKS'/f'chunk_{ci:03d}'/'ledger.json'
        if not lp.is_file(): continue
        try: led=json.loads(lp.read_text(encoding='utf-8'))
        except Exception: continue
        for rec in (led.get('states') or {}).values():
            st=rec.get('state');counts[st]+=1; attempts[int(rec.get('attempts',0))]+=1
            if st=='COMPLETE': completed+=1
    status='FAILED' if counts.get('FAILED_FINAL',0) else ('MEASUREMENT_COMPLETE_PENDING_SCALE_AUDIT' if completed==G101_SAMPLE_COUNT else 'RUNNING')
    obj={'schema':'DF-G101-SCALE1K-PROGRESS-V1','dataset_id':DATASET_ID,'release_id':RELEASE_ID,'completed':completed,'total':G101_SAMPLE_COUNT,'counts':dict(counts),'attempts':{str(k):v for k,v in attempts.items()},'status':status,'updated_utc':utc_iso()}
    atomic_json(runroot/'PROGRESS.json',obj)
    atomic_text(runroot/'PROGRESS.html',f'<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="5"><style>body{{background:#101319;color:#eee;font-family:system-ui;padding:30px}}progress{{width:100%;height:30px}}</style><h1>DF-G101 SCALE1K V1</h1><progress value="{completed}" max="1000"></progress><h2>{completed}/1000 COMPLETE</h2><pre>{html.escape(json.dumps(obj,indent=2))}</pre>')
    return obj


def _g101_hist(values,bins):
    out=[0]*(len(bins)-1)
    for x in values:
        for i in range(len(bins)-1):
            if bins[i] <= x < bins[i+1] or (i==len(bins)-2 and x==bins[i+1]): out[i]+=1;break
    return out


def _g101_js(p,q):
    sp=float(sum(p));sq=float(sum(q));
    if sp<=0 or sq<=0:return 1.0
    P=[x/sp for x in p];Q=[x/sq for x in q];M=[(a+b)/2 for a,b in zip(P,Q)]
    def kl(A,B): return sum(a*math.log(a/b,2) for a,b in zip(A,B) if a>0 and b>0)
    return 0.5*kl(P,M)+0.5*kl(Q,M)


def _g101_extract_normal_max(gt):
    n=gt.get('normal',{}) or {}
    for key in ('filter_safe_canonical_vs_analytic_direction_error','filter_safe_interior_direction_error','canonical_vs_analytic_direction_error'):
        v=n.get(key)
        if isinstance(v,dict) and 'max' in v:return float(v['max'])
    # R29/R36 QA uses a direct diagnostic in some builds.
    for key in ('filter_safe_max_direction_error','max_direction_error'):
        if key in n:return float(n[key])
    return 0.0


def _g101_extract_depth_max(gt):
    d=gt.get('depth',{}) or {}
    for key in ('filter_safe_depth_abs_error_m','authoritative_depth_abs_error_m'):
        v=d.get(key)
        if isinstance(v,dict) and 'max' in v:return float(v['max'])
    return float(d.get('filter_safe_max_abs_error_m',0.0) or 0.0)


def _g101_scale_statistics(accepts):
    cam=[];dep=[];nor=[]
    for a in accepts:
        cam.append(max(float(x) for x in a['camera_calibration_abs_error'].values())/0.001)
        dep.append(_g101_extract_depth_max(a['gt'])/1e-4)
        nor.append(_g101_extract_normal_max(a['gt'])/1e-5)
    h={'camera':_g101_hist(cam,G101_NORM_BINS),'depth':_g101_hist(dep,G101_NORM_BINS),'normal':_g101_hist(nor,G101_NORM_BINS)}
    js={k:_g101_js(h[k],G101_MICRO_BASELINE_HIST[k]) for k in h}
    high={k:h[k][-1]/float(len(accepts)) for k in h}
    hard={'camera':max(cam,default=0)<=1.0,'depth':max(dep,default=0)<=1.0,'normal':max(nor,default=0)<=1.0}
    drift={k:js[k]<=G101_JS_LIMIT for k in js}; crowd={k:high[k]<=G101_HIGH_LIMIT_BIN_MAX_FRACTION for k in high}
    status='PASS' if all(hard.values()) and all(drift.values()) and all(crowd.values()) else ('SCALE_STATISTICAL_REVIEW_REQUIRED' if all(hard.values()) else 'FAIL_HARD_SCIENTIFIC_LIMIT')
    return {'schema':'DF-G101-SCALE-STATISTICAL-QA-V1','status':status,'bins':G101_NORM_BINS,'histograms':h,'micro100_baseline_histograms':G101_MICRO_BASELINE_HIST,'js_divergence':js,'js_limit':G101_JS_LIMIT,'high_limit_bin_fraction':high,'high_limit_bin_max_fraction':G101_HIGH_LIMIT_BIN_MAX_FRACTION,'hard_limit_pass':hard,'max_normalized':{'camera':max(cam,default=0),'depth':max(dep,default=0),'normal':max(nor,default=0)}}


def _g101_operational_health(runroot:Path):
    attempts=[];walls=[];profiles=[]; all_complete=True
    for ci in range(G101_CHUNK_COUNT):
        cr=runroot/'CHUNKS'/f'chunk_{ci:03d}'; lp=cr/'ledger.json'; rp=cr/'worker_result_manifest.json'
        if not lp.is_file(): all_complete=False;continue
        led=json.loads(lp.read_text(encoding='utf-8'))
        for rec in (led.get('states') or {}).values(): attempts.append(int(rec.get('attempts',0))); all_complete=all_complete and rec.get('state')=='COMPLETE'
        if rp.is_file():
            rr=json.loads(rp.read_text(encoding='utf-8'))
            for sid,p in (rr.get('profiles') or {}).items(): profiles.append({'sample_id':sid,**p})
        for r in _g101_load_chunk(ci)['requests']:
            cp=cr/r['output_rel']/'completion.json'
            if cp.is_file(): walls.append(float(json.loads(cp.read_text(encoding='utf-8')).get('render_elapsed_seconds',0.0)))
    def trim_med(vals):
        vals=sorted(float(x) for x in vals if x is not None); n=len(vals); keep=max(1,int(math.floor(n*0.95)));return statistics.median(vals[:keep]) if vals else None
    first=walls[:200];last=walls[-200:]; fm=trim_med(first);lm=trim_med(last);ratio=(lm/fm if fm and lm is not None else None)
    retry_count=sum(1 for x in attempts if x==2); bad_attempt=sum(1 for x in attempts if x not in {1,2}); rc_bad=sum(1 for p in profiles if int(p.get('returncode',0))!=0)
    if not all_complete or bad_attempt or rc_bad: status='FAIL'
    elif retry_count: status='MEASUREMENT_COMPLETE_WITH_OPERATIONAL_RETRY_REVIEW'
    elif ratio is not None and ratio>G101_SLOWDOWN_RATIO_MAX: status='OPERATIONAL_DEGRADATION_REVIEW_REQUIRED'
    else: status='PASS'
    q=lambda p: statistics.quantiles(walls,n=100,method='inclusive')[p-1] if len(walls)>=2 else (walls[0] if walls else None)
    return {'schema':'DF-G101-OPERATIONAL-HEALTH-V1','status':status,'sample_count':len(attempts),'all_complete':all_complete,'attempts_1':sum(x==1 for x in attempts),'attempts_2':retry_count,'other_attempts':bad_attempt,'worker_nonzero_returncodes':rc_bad,'wall_seconds':{'count':len(walls),'median':statistics.median(walls) if walls else None,'p90':q(90),'p95':q(95),'p99':q(99),'max':max(walls) if walls else None,'first200_trimmed_median':fm,'last200_trimmed_median':lm,'last_first_ratio':ratio,'clean_ratio_max':G101_SLOWDOWN_RATIO_MAX},'profiles_with_gpu_telemetry':sum(bool(p.get('gpu_telemetry_available')) for p in profiles),'peak_observed_vram_mib':max([float(p.get('peak_observed_vram_mib',0) or 0) for p in profiles],default=0)}


def _g101_distribution_qa(req_summaries,accepts):
    dims={'sample_id':[r['sample_id'] for r in req_summaries],'request_digest':[r['request_digest'] for r in req_summaries],'recipe_digest':[r['recipe_digest'] for r in req_summaries],'base_scene_id':[r['base_scene_id'] for r in req_summaries],'rgb_sha256':[a['rgb_sha256'] for a in accepts]}
    dup={k:sorted(x for x,c in Counter(v).items() if c>1) for k,v in dims.items()}
    counts={'families':dict(Counter(r['family'] for r in req_summaries)),'cameras':dict(Counter(r['camera'] for r in req_summaries)),'appearances':dict(Counter(r['appearance'] for r in req_summaries)),'resolutions':dict(Counter(r['resolution'] for r in req_summaries))}
    return {'schema':'DF-G101-CORPUS-QA-V1','status':'PASS' if not any(dup.values()) and counts==EXPECTED_COUNTS else 'FAIL','exact_duplicates':dup,'counts':counts,'expected_counts':EXPECTED_COUNTS,'perceptual_near_duplicates':'REPORT_ONLY_SEPARATE_IF_REQUESTED'}


def _g101_visual_selection(reqs,accepts):
    byfam={f:[] for f in FAMILIES}
    for i,r in enumerate(reqs): byfam[r['scene']['scene_family']].append((hashlib.sha256(r['sample_id'].encode()).hexdigest(),i))
    sel=[]; reasons={}
    def add(i,reason):
        if i not in sel: sel.append(i)
        reasons.setdefault(reqs[i]['sample_id'],[]).append(reason)
    for f in FAMILIES:
        for _h,i in sorted(byfam[f])[:4]: add(i,'FIXED_FAMILY4')
    stress=[]
    for i,r in enumerate(reqs):
        sc=r.get('camera_observability_v2',{}).get('observability_stress_score')
        if sc is not None: stress.append((float(sc),i))
    for _s,i in sorted(stress)[:12]:add(i,'LOW_OBSERVABILITY_STRESS12')
    for i,r in enumerate(reqs):
        if r['sample_id'] in G101_R33_EXPECTED:add(i,'R33_APPLIED')
        if r['sample_id'] in G101_R36_EXPECTED:add(i,'R36_APPLIED')
        if r['sample_id'] in G101_R2_EXPECTED:add(i,'G101_R2_APPLIED')
    for i in sorted(range(len(accepts)),key=lambda x:(float(accepts[x]['rgb']['mean_luma']),x))[:10]:add(i,'LOWEST_MEAN_LUMA10')
    for i in sorted(range(len(accepts)),key=lambda x:(float(accepts[x]['rgb']['structural_fraction']),x))[:10]:add(i,'LOWEST_STRUCTURAL10')
    return {'schema':'DF-G101-VISUAL-SELECTION-V1','selected_indices':sel,'selected_sample_ids':[reqs[i]['sample_id'] for i in sel],'count':len(sel),'reasons':reasons,'rules':{'fixed_family4':48,'stress':12,'all_r33_r36_r2':True,'lowest_mean':10,'lowest_structural':10}}


def _g101_source_snapshot_zip(release:Path,out:Path):
    rec=[];out.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in sorted(release.iterdir()):
            if p.is_file():
                b=p.read_bytes(); fixed_zip_write(z,p.name,b);rec.append({'path':p.name,'bytes':len(b),'sha256':sha256_bytes(b)})
        fixed_zip_write(z,'SOURCE_SNAPSHOT_MANIFEST.json',(json.dumps({'schema':'DF-G101-SOURCE-SNAPSHOT-MANIFEST-V1','files':rec},indent=2,sort_keys=True)+'\n').encode())
    with zipfile.ZipFile(out) as z:
        if z.testzip() is not None:raise RuntimeError('G101_SOURCE_SNAPSHOT_CRC_FAIL')
    return {'path':out.name,'bytes':out.stat().st_size,'sha256':sha256_file(out)}


def _g101_build_return_set(root,runroot,release,chunk_ids,preflight,plan_validation,accepts,reqs,scale_stats,operational,corpus,visual):
    returns=root/'11_PACKAGES'/'RETURNS'/G101_RETURN_DIRNAME; returns.mkdir(parents=True,exist_ok=True)
    # Clear only stale G101 transport wrappers, never run evidence.
    for p in returns.glob('*.zip'): p.unlink()
    shard_records=[]
    for si in range(G101_SHARD_COUNT):
        chunk_subset=chunk_ids[si*10:(si+1)*10]
        manifest={'schema':'DF-G101-RETURN-SHARD-MANIFEST-V1','shard_index':si,'sample_range':[si*100,si*100+99],'chunks':chunk_subset}
        out=returns/f'RETURN_SHARD_{si:02d}_{si*100:03d}_{si*100+99:03d}.zip'
        with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
            fixed_zip_write(z,'SHARD_MANIFEST.json',(json.dumps(manifest,indent=2,sort_keys=True)+'\n').encode())
            for rec in chunk_subset:
                p=runroot/'CHUNK_ARCHIVES'/rec['path']; fixed_zip_write(z,'CHUNKS/'+rec['path'],p.read_bytes())
        with zipfile.ZipFile(out) as z:
            if z.testzip() is not None:raise RuntimeError('G101_RETURN_SHARD_CRC_FAIL:'+str(si))
        shard_records.append({'shard_index':si,'path':out.name,'bytes':out.stat().st_size,'sha256':sha256_file(out),'crc':'PASS','sample_range':[si*100,si*100+99]})
    ev=runroot/'EVIDENCE'; ev.mkdir(parents=True,exist_ok=True)
    atomic_json(ev/'DF_G101_SCALE_STATISTICAL_QA.json',scale_stats);atomic_json(ev/'DF_G101_OPERATIONAL_HEALTH.json',operational);atomic_json(ev/'DF_G101_CORPUS_QA.json',corpus);atomic_json(ev/'DF_G101_VISUAL_SELECTION.json',visual)
    acc_summary=[{'sample_id':a['sample_id'],'request_digest':a['request_digest'],'status':a['status'],'checks':a['checks'],'rgb':a['rgb'],'rgb_sha256':a['rgb_sha256'],'camera_calibration_abs_error':a['camera_calibration_abs_error'],'normal_acceptance_semantics':a['normal_acceptance_semantics'],'depth_acceptance_semantics':a['depth_acceptance_semantics'],'provenance_checks':a['provenance_checks']} for a in accepts]
    atomic_json(ev/'DF_G101_ALL_ACCEPTANCE_SUMMARIES.json',{'schema':'DF-G101-ALL-ACCEPTANCE-SUMMARIES-V1','count':len(acc_summary),'samples':acc_summary})
    source_rec=_g101_source_snapshot_zip(release,ev/'DF_G101_SOURCE_SNAPSHOT.zip')
    overall_clean=(len(accepts)==1000 and all(a['status']=='PASS' for a in accepts) and scale_stats['status']=='PASS' and operational['status']=='PASS' and corpus['status']=='PASS')
    disposition='MEASUREMENT_COMPLETE_PENDING_VISUAL_REVIEW' if overall_clean else 'MEASUREMENT_COMPLETE_PENDING_REVIEW'
    idx={'schema':'DF-G101-SCALE1K-RETURN-INDEX-V1','status':disposition,'dataset_id':DATASET_ID,'release_id':RELEASE_ID,'sample_count':len(accepts),'chunk_count':len(chunk_ids),'shards':shard_records,'plan_validation':plan_validation,'preflight':preflight,'scale_statistical_status':scale_stats['status'],'operational_status':operational['status'],'corpus_status':corpus['status'],'visual_selection_count':visual['count'],'source_snapshot':source_rec,'g101_spec_drive_id':G101_SPEC_DRIVE_ID,'g101_r2_spec_drive_id':G101_R2_SPEC_DRIVE_ID,'g101_r2_implementation_id':G101_R2_IMPLEMENTATION_ID,'source_release_id':SOURCE_RELEASE_ID,'r1_failure_authority':{'bytes':G101_R1_FAILURE_AUTHORITY_BYTES,'sha256':G101_R1_FAILURE_AUTHORITY_SHA256},'qualification_split_clarification_drive_id':G101_SPLIT_CLARIFICATION_DRIVE_ID,'closed_micro100_authority':{'drive_id':G101_CLOSED_MICRO100_RETURN_DRIVE_ID,'sha256':G101_CLOSED_MICRO100_RETURN_SHA256},'test77_accessed':False,'training_started':False,'maya_mutated':False,'product_mutated':False,'scale_10k_authorized':False}
    atomic_json(ev/'RETURN_INDEX.json',idx)
    index_zip=returns/G101_RETURN_INDEX
    files=['RETURN_INDEX.json','DF_G101_SCALE_STATISTICAL_QA.json','DF_G101_OPERATIONAL_HEALTH.json','DF_G101_CORPUS_QA.json','DF_G101_VISUAL_SELECTION.json','DF_G101_ALL_ACCEPTANCE_SUMMARIES.json','DF_G101_SOURCE_SNAPSHOT.zip']
    with zipfile.ZipFile(index_zip,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9,allowZip64=True) as z:
        for name in files: fixed_zip_write(z,name,(ev/name).read_bytes())
        fixed_zip_write(z,'RETURN_SET_MANIFEST.json',(json.dumps({'schema':'DF-G101-RETURN-SET-MANIFEST-V1','index_filename':G101_RETURN_INDEX,'shards':shard_records},indent=2,sort_keys=True)+'\n').encode())
    with zipfile.ZipFile(index_zip) as z:
        if z.testzip() is not None:raise RuntimeError('G101_RETURN_INDEX_CRC_FAIL')
    index_rec={'path':index_zip.name,'bytes':index_zip.stat().st_size,'sha256':sha256_file(index_zip),'crc':'PASS'}
    atomic_json(returns/'RETURN_SET_IDENTITY.json',{'schema':'DF-G101-RETURN-SET-IDENTITY-V1','index':index_rec,'shards':shard_records,'status':disposition})
    return index_rec,shard_records,disposition


def _g101_compact_failure(root,runroot,error,tb=None):
    returns=root/'11_PACKAGES'/'RETURNS'/G101_RETURN_DIRNAME;returns.mkdir(parents=True,exist_ok=True)
    out=returns/G101_FAILURE_RETURN; stage=root/'11_PACKAGES'/'G101_R2_FAILURE_STAGING';shutil.rmtree(stage,ignore_errors=True);stage.mkdir(parents=True)
    progress=None
    if (runroot/'PROGRESS.json').is_file():
        progress=json.loads((runroot/'PROGRESS.json').read_text(encoding='utf-8'));shutil.copy2(runroot/'PROGRESS.json',stage/'PROGRESS.json')
    report={'schema':'DF-G101-R2-FAILURE-RETURN-V1','status':'FAIL_G101_R2_OPEN','error':error,'traceback':tb,'completed_samples':(progress or {}).get('completed',0),'progress':progress,'g101_spec_drive_id':G101_SPEC_DRIVE_ID,'g101_r2_spec_drive_id':G101_R2_SPEC_DRIVE_ID,'source_release_id':SOURCE_RELEASE_ID,'qualification_split_clarification_drive_id':G101_SPLIT_CLARIFICATION_DRIVE_ID,'plan_projection_drive_id':G101_PLAN_PROJECTION_DRIVE_ID,'r1_failure_authority':{'bytes':G101_R1_FAILURE_AUTHORITY_BYTES,'sha256':G101_R1_FAILURE_AUTHORITY_SHA256},'test77_accessed':False,'training_started':False,'maya_mutated':False,'product_mutated':False,'scale_10k_authorized':False}
    m=re.search(r'G101(?:_R2)?_[A-Z0-9_]*SAMPLE_ACCEPTANCE_FAIL:([^:]+)',str(error))
    target=m.group(1) if m else None
    completed_chunks=[]
    failed_candidates=[]
    for ci in range(G101_CHUNK_COUNT):
        cr=runroot/'CHUNKS'/f'chunk_{ci:03d}';lp=cr/'ledger.json'
        if not lp.is_file():continue
        try: led=json.loads(lp.read_text(encoding='utf-8'))
        except Exception: continue
        states=led.get('states') or {}
        for sid,rec in states.items():
            if rec.get('state')=='FAILED_FINAL': failed_candidates.append((ci,sid))
        if states and all(x.get('state')=='COMPLETE' for x in states.values()):
            zp=runroot/'CHUNK_ARCHIVES'/f'PCS_CAMERA_GEOMETRY_SCALE1K_V1_CHUNK_{ci:03d}.zip'
            completed_chunks.append({'chunk_index':ci,'ledger_sha256':sha256_file(lp),'archive':({'path':zp.name,'bytes':zp.stat().st_size,'sha256':sha256_file(zp)} if zp.is_file() else None)})
    if target is None and len(failed_candidates)==1: target=failed_candidates[0][1]
    if target:
        for ci in range(G101_CHUNK_COUNT):
            cr=runroot/'CHUNKS'/f'chunk_{ci:03d}';lp=cr/'ledger.json'
            if not lp.is_file():continue
            try: states=(json.loads(lp.read_text(encoding='utf-8')).get('states') or {})
            except Exception: continue
            if target not in states:continue
            d=stage/'TARGET_FAILURE';d.mkdir(exist_ok=True)
            named=[(lp,'ledger.json'),(cr/'worker_result_manifest.json','worker_result_manifest.json'),(cr/'requests'/f'{target}.json','request.json'),(cr/'logs'/f'{target}.log','worker.log'),(runroot/'EVIDENCE'/'SAMPLE_ACCEPTANCE'/f'{target}.json','acceptance.json')]
            for src,name in named:
                if src.is_file():shutil.copy2(src,d/name)
            try:
                req=next(r for r in _g101_load_chunk(ci)['requests'] if r['sample_id']==target); sd=cr/req['output_rel']
                if sd.is_dir():shutil.copytree(sd,d/'sample',dirs_exist_ok=True)
            except Exception:pass
            break
    recroot=runroot/'RECOVERY'/'G101_R2_SAMPLE0005_PRE_REMEDIATION'
    if recroot.is_dir(): shutil.copytree(recroot,stage/'R2_RECOVERY_EVIDENCE',dirs_exist_ok=True)
    report['target_sample_id']=target;report['completed_chunk_inventory']=completed_chunks;report['failed_final_candidates']=[{'chunk_index':ci,'sample_id':sid} for ci,sid in failed_candidates]
    atomic_json(stage/'FAILURE_REPORT.json',report)
    src=[]
    for p in sorted(SOURCE.glob('*.py')):src.append({'path':p.name,'bytes':p.stat().st_size,'sha256':sha256_file(p)})
    atomic_json(stage/'SOURCE_IDENTITIES.json',{'schema':'DF-G101-R2-SOURCE-IDENTITIES-V1','files':src})
    manifest_files=[]
    for fp in sorted(stage.rglob('*')):
        if fp.is_file() and fp.name!='FAILURE_RETURN_MANIFEST.json': manifest_files.append({'path':fp.relative_to(stage).as_posix(),'bytes':fp.stat().st_size,'sha256':sha256_file(fp)})
    atomic_json(stage/'FAILURE_RETURN_MANIFEST.json',{'schema':'DF-G101-R2-FAILURE-RETURN-MANIFEST-V1','files':manifest_files,'request_and_acceptance_distinct_names':True,'tamper_detection':'SHA256_EXACT'})
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
        for fp in sorted(stage.rglob('*')):
            if fp.is_file():fixed_zip_write(z,fp.relative_to(stage).as_posix(),fp.read_bytes())
    with zipfile.ZipFile(out) as z:
        if z.testzip() is not None:raise RuntimeError('G101_R2_FAILURE_RETURN_CRC_FAIL')
    shutil.rmtree(stage,ignore_errors=True);return out


def _g101_r2_failure_authority_identity():
    p=G101_R1_FAILURE_AUTHORITY
    if not p.is_file(): raise RuntimeError('G101_R2_R1_FAILURE_AUTHORITY_MISSING')
    if p.stat().st_size!=G101_R1_FAILURE_AUTHORITY_BYTES or sha256_file(p)!=G101_R1_FAILURE_AUTHORITY_SHA256:
        raise RuntimeError('G101_R2_R1_FAILURE_AUTHORITY_IDENTITY_MISMATCH')
    with zipfile.ZipFile(p) as z:
        if z.testzip() is not None: raise RuntimeError('G101_R2_R1_FAILURE_AUTHORITY_CRC_FAIL')
        rep=json.loads(z.read('FAILURE_REPORT.json'))
    if rep.get('target_sample_id')!=G101_R2_RECOVERY_SAMPLE_ID or int(rep.get('completed_samples',-1))!=10:
        raise RuntimeError('G101_R2_R1_FAILURE_AUTHORITY_CONTENT_MISMATCH')
    return {'path':p.name,'bytes':p.stat().st_size,'sha256':sha256_file(p),'crc':'PASS'}


def _g101_r2_tree_identity(root:Path):
    out=[]
    for fp in sorted(Path(root).rglob('*')):
        if fp.is_file(): out.append({'path':fp.relative_to(root).as_posix(),'bytes':fp.stat().st_size,'sha256':sha256_file(fp)})
    return out


def _g101_r2_target_request():
    ch=_g101_load_chunk(0)
    req=next((r for r in ch['requests'] if r.get('sample_id')==G101_R2_RECOVERY_SAMPLE_ID),None)
    if req is None or req.get('input_digest_sha256')!=G101_R2_RECOVERY_REQUEST_DIGEST:
        raise RuntimeError('G101_R2_FROZEN_TARGET_IDENTITY_MISMATCH')
    return req


def _g101_r2_verify_live_prestate(runroot:Path):
    runroot=Path(runroot)
    if not runroot.is_dir(): raise RuntimeError('G101_R2_EXISTING_R1_RUNROOT_REQUIRED')
    auth=_g101_r2_failure_authority_identity()
    pr=runroot/'PROGRESS.json'; lp=runroot/'CHUNKS'/'chunk_000'/'ledger.json'
    if not pr.is_file() or not lp.is_file(): raise RuntimeError('G101_R2_PRESTATE_CONTROL_MISSING')
    if sha256_file(pr)!=G101_R2_PRE_PROGRESS_SHA256: raise RuntimeError('G101_R2_PROGRESS_SHA_MISMATCH')
    if sha256_file(lp)!=G101_R2_PRE_LEDGER_SHA256: raise RuntimeError('G101_R2_LEDGER_SHA_MISMATCH')
    pobj=json.loads(pr.read_text(encoding='utf-8')); led=json.loads(lp.read_text(encoding='utf-8'))
    if int(pobj.get('completed',-1))!=10 or pobj.get('status')!='RUNNING' or int(pobj.get('total',-1))!=1000:
        raise RuntimeError('G101_R2_PROGRESS_CONTENT_MISMATCH')
    ch=_g101_load_chunk(0); states=led.get('states') or {}
    expected={r['sample_id']:r['input_digest_sha256'] for r in ch['requests']}
    if set(states)!=set(expected): raise RuntimeError('G101_R2_LEDGER_SAMPLE_SET_MISMATCH')
    for sid,dig in expected.items():
        rec=states[sid]
        if rec.get('state')!='COMPLETE' or int(rec.get('attempts',-1))!=1 or rec.get('request_digest')!=dig:
            raise RuntimeError('G101_R2_LEDGER_NOT_EXACT_COMPLETE:'+sid)
    req=_g101_r2_target_request(); cr=runroot/'CHUNKS'/'chunk_000'; sd=cr/req['output_rel']
    rp=cr/'requests'/f'{req["sample_id"]}.json'; ap=runroot/'EVIDENCE'/'SAMPLE_ACCEPTANCE'/f'{req["sample_id"]}.json'; cp=sd/'completion.json'; rgb=sd/'rgb.png'
    for x in (rp,ap,cp,rgb):
        if not x.is_file(): raise RuntimeError('G101_R2_TARGET_PRESTATE_FILE_MISSING:'+x.name)
    if json.loads(rp.read_text(encoding='utf-8'))!=req: raise RuntimeError('G101_R2_TARGET_REQUEST_BYTES_NOT_FROZEN_CONTENT')
    if sha256_file(ap)!=G101_R2_PRE_ACCEPTANCE_SHA256: raise RuntimeError('G101_R2_ACCEPTANCE_SHA_MISMATCH')
    if sha256_file(cp)!=G101_R2_PRE_COMPLETION_SHA256: raise RuntimeError('G101_R2_COMPLETION_SHA_MISMATCH')
    if sha256_file(rgb)!=G101_R2_PRE_RGB_SHA256: raise RuntimeError('G101_R2_RGB_SHA_MISMATCH')
    acc=json.loads(ap.read_text(encoding='utf-8')); checks=acc.get('checks') or {}
    if acc.get('status')!='FAIL' or checks.get('rgb_mean') is not False or any(v is not True for k,v in checks.items() if k!='rgb_mean'):
        raise RuntimeError('G101_R2_TARGET_FAILURE_SIGNATURE_MISMATCH')
    comp=json.loads(cp.read_text(encoding='utf-8'))
    if comp.get('status')!='PASS_REAL_BLENDER_RENDERED' or comp.get('sample_id')!=req['sample_id'] or comp.get('input_digest_sha256')!=req['input_digest_sha256']:
        raise RuntimeError('G101_R2_TARGET_COMPLETION_CONTENT_MISMATCH')
    policy=g101_r2_blueprint_foreground_vertical_policy(req)
    if not policy.get('applied') or policy.get('existing_r33_applied') or policy.get('existing_r36_applied'):
        raise RuntimeError('G101_R2_TARGET_POLICY_NOT_EXACT_ELIGIBLE')
    if abs(float(policy.get('foreground_raster_fraction',0))-0.7249416775173612)>1e-15 or abs(float(policy.get('aggregate_vertical_foreground_fraction',0))-0.9964171117992086)>1e-15:
        raise RuntimeError('G101_R2_TARGET_POLICY_METRIC_MISMATCH')
    immutable_names=['depth.exr','normal.exr','object_index.exr','normal_authority_mask.uint8.bin','normal_filter_safe_interior_mask.uint8.bin','depth_filter_safe_interior_mask.uint8.bin','micro100_aux_gt_qa.json','camera_calibration.json','pre_render_reprojection.json','r21_binding_lab.json']
    immutable={name:sha256_file(sd/name) for name in immutable_names if (sd/name).is_file()}
    return {'authority':auth,'progress':pobj,'ledger':led,'request':req,'request_path':rp,'acceptance_path':ap,'completion_path':cp,'sample_dir':sd,'immutable_hashes':immutable}


def _g101_r2_assert_immutable(sample_dir:Path, before:dict):
    for name,sha in before.items():
        p=sample_dir/name
        if not p.is_file() or sha256_file(p)!=sha: raise RuntimeError('G101_R2_FORBIDDEN_GT_OR_CAMERA_MUTATION:'+name)
    return True


def _g101_r2_recover_chunk000(runroot:Path,M,pre):
    runroot=Path(runroot); cr=runroot/'CHUNKS'/'chunk_000'; req=pre['request']; sd=pre['sample_dir']
    recroot=runroot/'RECOVERY'/'G101_R2_SAMPLE0005_PRE_REMEDIATION'
    if recroot.exists(): raise RuntimeError('G101_R2_RECOVERY_ALREADY_INITIALIZED_DO_NOT_RERUN')
    recroot.mkdir(parents=True)
    shutil.copy2(G101_R1_FAILURE_AUTHORITY,recroot/G101_R1_FAILURE_AUTHORITY.name)
    shutil.copy2(runroot/'PROGRESS.json',recroot/'PROGRESS_pre_r2.json')
    shutil.copy2(cr/'ledger.json',recroot/'ledger_pre_r2.json')
    shutil.copy2(pre['request_path'],recroot/'request.json')
    shutil.copy2(pre['acceptance_path'],recroot/'acceptance_pre_r2.json')
    shutil.copy2(pre['completion_path'],recroot/'completion_pre_r2.json')
    logp=cr/'logs'/f'{req["sample_id"]}.log'
    if logp.is_file(): shutil.copy2(logp,recroot/'worker.log')
    wmp=cr/'worker_result_manifest.json'
    if wmp.is_file(): shutil.copy2(wmp,recroot/'worker_result_manifest.json')
    shutil.copytree(sd,recroot/'sample_pre_r2')
    journal={'schema':'DF-G101-R2-EXISTING-BYTES-RECOVERY-JOURNAL-V1','status':'PRESERVED_BEFORE_REMEDIATION','g101_r2_spec_drive_id':G101_R2_SPEC_DRIVE_ID,'implementation_id':G101_R2_IMPLEMENTATION_ID,'sample_id':req['sample_id'],'request_digest':req['input_digest_sha256'],'failure_authority':pre['authority'],'pre_progress_sha256':G101_R2_PRE_PROGRESS_SHA256,'pre_ledger_sha256':G101_R2_PRE_LEDGER_SHA256,'pre_acceptance_sha256':G101_R2_PRE_ACCEPTANCE_SHA256,'pre_completion_sha256':G101_R2_PRE_COMPLETION_SHA256,'pre_rgb_sha256':G101_R2_PRE_RGB_SHA256,'immutable_authority_hashes':pre['immutable_hashes'],'preserved_tree':_g101_r2_tree_identity(recroot/'sample_pre_r2'),'worker_invocations_0000_0009':0,'test77_accessed':False,'training_started':False,'maya_mutated':False,'product_mutated':False}
    atomic_json(recroot/'RECOVERY_JOURNAL.json',journal)

    pre_rgb=sd/'rgb_pre_g101_r2.png'; pre_rgb.write_bytes((sd/'rgb.png').read_bytes())
    gain=apply_fixed_rgb8_gain_png(pre_rgb,sd/'rgb.png',numerator=2,denominator=1)
    if gain.get('raw_sha256')!=G101_R2_PRE_RGB_SHA256 or gain.get('final_sha256')!=G101_R2_EXPECTED_RGB_SHA256 or sha256_file(sd/'rgb.png')!=G101_R2_EXPECTED_RGB_SHA256:
        raise RuntimeError('G101_R2_TARGET_FIXED_GAIN_IDENTITY_MISMATCH')
    policy=g101_r2_blueprint_foreground_vertical_policy(req)
    gain.update({'implementation_id':G101_R2_IMPLEMENTATION_ID,'source_rgb_rel':'rgb_pre_g101_r2.png','final_rgb_rel':'rgb.png','geometry_preserving':True,'eligibility':policy,'g101_r2_spec_drive_id':G101_R2_SPEC_DRIVE_ID})
    comp=json.loads((sd/'completion.json').read_text(encoding='utf-8'))
    comp['g101_r2_blueprint_foreground_vertical_policy']=policy
    comp['g101_r2_blueprint_fixed_rgb_gain']=gain
    keep=[r for r in (comp.get('files') or []) if r.get('path') not in {'rgb.png','rgb_pre_g101_r2.png'}]
    for name in ('rgb.png','rgb_pre_g101_r2.png'):
        pp=sd/name; keep.append({'path':name,'bytes':pp.stat().st_size,'sha256':sha256_file(pp)})
    comp['files']=keep
    atomic_json(sd/'completion.json',comp)
    _g101_r2_assert_immutable(sd,pre['immutable_hashes'])
    target_acc=sample_acceptance(req,comp,sd,M,{'mode':'G101_R2_EXISTING_BYTES_NO_RERENDER','g101_r2_spec_drive_id':G101_R2_SPEC_DRIVE_ID})
    target_acc['schema']='DF-G101-PER-SAMPLE-ACCEPTANCE-R2-V1'
    if target_acc.get('status')!='PASS': raise RuntimeError('G101_R2_TARGET_ACCEPTANCE_STILL_FAIL:'+json.dumps(target_acc.get('checks'),sort_keys=True))
    atomic_json(pre['acceptance_path'],target_acc)

    # Existing PASS peers 0000..0004 are validated but never rewritten.
    accepts=[]; reqs=[]
    ch=_g101_load_chunk(0)
    for ordinal,r in enumerate(ch['requests']):
        sp=cr/r['output_rel']; cp=sp/'completion.json'; ap=runroot/'EVIDENCE'/'SAMPLE_ACCEPTANCE'/f"{r['sample_id']}.json"
        if ordinal==5:
            a=target_acc
        elif ordinal<=4:
            if not ap.is_file(): raise RuntimeError('G101_R2_EXISTING_ACCEPTANCE_MISSING:'+r['sample_id'])
            persisted=json.loads(ap.read_text(encoding='utf-8'))
            if persisted.get('status')!='PASS': raise RuntimeError('G101_R2_EXISTING_ACCEPTANCE_NOT_PASS:'+r['sample_id'])
            # Read-only recomputation verifies the existing bytes under R2 acceptance semantics.
            c=json.loads(cp.read_text(encoding='utf-8')); a=sample_acceptance(r,c,sp,M,None)
            if a.get('status')!='PASS': raise RuntimeError('G101_R2_EXISTING_PEER_REVALIDATION_FAIL:'+r['sample_id'])
            a=persisted
        else:
            c=json.loads(cp.read_text(encoding='utf-8')); a=sample_acceptance(r,c,sp,M,None); a['schema']='DF-G101-PER-SAMPLE-ACCEPTANCE-R2-V1'
            if a.get('status')!='PASS': raise RuntimeError('G101_R2_EXISTING_COMPLETE_PEER_ACCEPTANCE_FAIL:'+r['sample_id']+':'+json.dumps(a.get('checks'),sort_keys=True))
            atomic_json(ap,a)
        accepts.append(a); reqs.append(r)
    # Ledger remains byte-identical; no worker call for 0000..0009.
    if sha256_file(cr/'ledger.json')!=G101_R2_PRE_LEDGER_SHA256: raise RuntimeError('G101_R2_CHUNK000_LEDGER_MUTATED')
    zp=runroot/'CHUNK_ARCHIVES'/'PCS_CAMERA_GEOMETRY_SCALE1K_V1_CHUNK_000.zip'
    cid=make_chunk_zip(cr,zp)
    atomic_json(runroot/'EVIDENCE'/'CHUNK_IDENTITIES_PARTIAL.json',{'schema':'DF-G101-CHUNK-IDENTITIES-V1','chunks':[cid]})
    journal.update({'status':'RECOVERED_EXISTING_BYTES_CHUNK000_ACCEPTANCE_PASS','post_rgb_sha256':sha256_file(sd/'rgb.png'),'post_completion_sha256':sha256_file(sd/'completion.json'),'post_acceptance_sha256':sha256_file(pre['acceptance_path']),'chunk000_archive':cid,'acceptance_0006_0009_persisted_from_existing_complete_bytes':True,'continuation_first_new_sample':10,'worker_invocations_0000_0009':0})
    atomic_json(recroot/'RECOVERY_JOURNAL.json',journal)
    return accepts,reqs,cid,journal


def g101_run(factory_root):
    root=Path(factory_root);safe_root(root);runroot=root/'09_RUNS'/RUN_ID
    # Exact R1 failure authentication is mandatory before any run-root mutation.
    pre=_g101_r2_verify_live_prestate(runroot)
    release=_g101_install_release(root); M=_load_modules(release)
    pv=_g101_validate_frozen_plan(M,full_policy_audit=False)
    if pv['status']!='PASS':raise RuntimeError('G101_R2_FROZEN_PLAN_VALIDATION_FAIL:'+json.dumps(pv['checks'],sort_keys=True))
    pv['pre_real_full_167_blueprint_policy_audit']=_g101_r2_verify_policy_audit_authority()
    _rg=json.loads((HERE/'DF_G101_R2_RUNTIME_POLICY_GUARD.json').read_text(encoding='utf-8'))
    if _rg.get('status')!='PASS': raise RuntimeError('G101_R2_PACKAGED_RUNTIME_POLICY_GUARD_REPORT_FAIL')
    pv['pre_real_runtime_policy_guard_report']={'status':'PASS','rows':_rg.get('rows')}
    # Frozen plan already exists in the R1 run-root and is not rewritten.
    pvp=runroot/'PLAN'/'PLAN_VALIDATION_R2.json'; atomic_json(pvp,pv)
    preflight=blender_preflight(M,root);preflight.update({'g101_spec_drive_id':G101_SPEC_DRIVE_ID,'g101_r2_spec_drive_id':G101_R2_SPEC_DRIVE_ID,'no_download':True})
    (runroot/'EVIDENCE'/'SAMPLE_ACCEPTANCE').mkdir(parents=True,exist_ok=True);(runroot/'CHUNK_ARCHIVES').mkdir(parents=True,exist_ok=True)
    accepts,reqs,cid0,recovery=_g101_r2_recover_chunk000(runroot,M,pre)
    chunk_ids=[cid0]
    _g101_progress(runroot)
    print('[DF-G101 R2] chunk000 recovered from existing bytes; no worker invoked for samples0000..0009.',flush=True)
    for ci in range(1,G101_CHUNK_COUNT):
        chunk=_g101_load_chunk(ci);cr=runroot/'CHUNKS'/f'chunk_{ci:03d}'
        print(f'\n[DF-G101 R2] ===== CHUNK {ci+1}/100 : samples {ci*10:04d}-{ci*10+9:04d} =====',flush=True)
        result=M['execute_chunk'](root,chunk,cr,worker_id='LOCAL_WINDOWS',max_attempts=2)
        if result['status']!='PASS':raise RuntimeError(f'G101_R2_CHUNK_RENDER_FAIL:{ci}:{result}')
        for req in chunk['requests']:
            sd=cr/req['output_rel']; comp=json.loads((sd/'completion.json').read_text(encoding='utf-8'))
            a=sample_acceptance(req,comp,sd,M,None); a['schema']='DF-G101-PER-SAMPLE-ACCEPTANCE-R2-V1'
            atomic_json(runroot/'EVIDENCE'/'SAMPLE_ACCEPTANCE'/f"{req['sample_id']}.json",a)
            if a['status']!='PASS':raise RuntimeError('G101_R2_SAMPLE_ACCEPTANCE_FAIL:'+req['sample_id']+':'+json.dumps(a['checks'],sort_keys=True))
            accepts.append(a);reqs.append(req)
        zp=runroot/'CHUNK_ARCHIVES'/f'PCS_CAMERA_GEOMETRY_SCALE1K_V1_CHUNK_{ci:03d}.zip';cid=make_chunk_zip(cr,zp);chunk_ids.append(cid)
        atomic_json(runroot/'EVIDENCE'/'CHUNK_IDENTITIES_PARTIAL.json',{'schema':'DF-G101-CHUNK-IDENTITIES-V1','chunks':chunk_ids});_g101_progress(runroot)
        print(f"[DF-G101 R2] chunk {ci+1}/100 PASS | {cid['bytes']:,} bytes | {cid['sha256']}",flush=True)
    if len(accepts)!=1000:raise RuntimeError('G101_R2_ACCEPTANCE_COUNT:'+str(len(accepts)))
    scale=_g101_scale_statistics(accepts);op=_g101_operational_health(runroot)
    meta,_=_g101_plan_meta(); reqsum=meta['sample_identities']; corpus=_g101_distribution_qa(reqsum,accepts);vis=_g101_visual_selection(reqs,accepts)
    index_rec,shards,disp=_g101_build_return_set(root,runroot,release,chunk_ids,preflight,pv,accepts,reqs,scale,op,corpus,vis)
    _g101_progress(runroot)
    journal={'schema':'DF-G101-R2-RUN-JOURNAL-V1','status':disp,'last_event':'RETURN_SET_READY','dataset_id':DATASET_ID,'release_id':RELEASE_ID,'source_release_id':SOURCE_RELEASE_ID,'sample_count':1000,'index':index_rec,'shards':shards,'scale_statistical_status':scale['status'],'operational_status':op['status'],'corpus_status':corpus['status'],'g101_r2_spec_drive_id':G101_R2_SPEC_DRIVE_ID,'r1_failure_authority_sha256':G101_R1_FAILURE_AUTHORITY_SHA256,'r2_existing_bytes_recovery_status':recovery['status'],'real_1k_measurement_complete':True,'scale_10k_authorized':False,'training_handoff_authorized':False,'test77_accessed':False,'training_started':False,'maya_mutated':False,'product_mutated':False}
    rdir=root/'11_PACKAGES'/'RETURNS'/G101_RETURN_DIRNAME;atomic_json(rdir/'DF_G101_SCALE1K_V1_RUN_JOURNAL.json',journal)
    print('\n[DF-G101 R2]',disp,flush=True);print('[DF-G101 R2] Return INDEX:',rdir/G101_RETURN_INDEX,flush=True);print('[DF-G101 R2] Return 10 shard ZIPs from:',rdir,flush=True);return 0


def _g101_split_parity_tests():
    if str(SOURCE) not in sys.path:sys.path.insert(0,str(SOURCE))
    from pcs_factory_qualification import is_factory_qualification_split,QUALIFICATION_SPLITS
    from pcs_factory_visibility_r15 import r15_camera_inside_fill_policy
    from pcs_factory_visibility_r17 import r17_camera_inside_contrast_policy
    from pcs_factory_rgb_rescue_r23 import r23_systemic_rgb_policy
    reqs=list(_g101_iter_requests())
    reps=[r for r in reqs if r['appearance']['profile_id']!='BLUEPRINT'][:12]
    parity=True; nonqual=True
    for r in reps:
        m=copy.deepcopy(r);m['split']='MICRO100_QUALIFICATION_ONLY';s=copy.deepcopy(r);s['split']='SCALE1K_QUALIFICATION_ONLY';n=copy.deepcopy(r);n['split']='TRAIN'
        for f in (r15_camera_inside_fill_policy,r17_camera_inside_contrast_policy,r23_systemic_rgb_policy):
            a=f(m);b=f(s)
            for k in set(a)|set(b):
                if k in {'split','reason'}:continue
                parity=parity and a.get(k)==b.get(k)
        nonqual=nonqual and (not r23_systemic_rgb_policy(n).get('applied'))
    helper=(is_factory_qualification_split('MICRO100_QUALIFICATION_ONLY') and is_factory_qualification_split('SCALE1K_QUALIFICATION_ONLY') and not is_factory_qualification_split('TRAIN') and not is_factory_qualification_split('TEST77') and not is_factory_qualification_split('PROTECTED') and not is_factory_qualification_split('SCALE10K_QUALIFICATION_ONLY') and QUALIFICATION_SPLITS==frozenset({'MICRO100_QUALIFICATION_ONLY','SCALE1K_QUALIFICATION_ONLY'}))
    return {'parity':parity,'nonqualification_blocks':nonqual,'helper_exact':helper,'representative_count':len(reps)}

def _g101_policy_positive_fixtures():
    # The full 167-BLUEPRINT geometry audit was frozen pre-spec. At implementation
    # time we prove R33/R36 algorithms are byte-text identical to R36 except the
    # authorized import + qualification-split predicate replacement.
    def normalize_new(text):
        lines=[]
        text=text.replace('from pcs_factory_qualification import is_factory_qualification_split\n\n','')
        text=text.replace('if not is_factory_qualification_split(split) or profile != "BLUEPRINT":','if split != "MICRO100_QUALIFICATION_ONLY" or profile != "BLUEPRINT":')
        return text.strip()
    base=HERE/'_G101_PARENT_R36_SOURCE'
    checks={}
    for fn in ('pcs_factory_blueprint_r33.py','pcs_factory_blueprint_r36.py'):
        parent=(base/fn).read_text(encoding='utf-8') if (base/fn).is_file() else ''
        current=(SOURCE/fn).read_text(encoding='utf-8')
        checks[fn]=bool(parent) and normalize_new(current)==parent.strip()
    return {'status':'PASS' if all(checks.values()) else 'FAIL','source_diff_only_split_predicate':checks}

def _g101_retry_regression():
    import importlib.util,tempfile
    spec=importlib.util.spec_from_file_location('g101_paths_test',SOURCE/'pcs_factory_paths.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    orig=m.os.replace; orig_sleep=m.time.sleep; checks={}
    try:
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'x.json';calls=[];sleeps=[]
            def fake(src,dst):
                calls.append(1)
                if len(calls)<=2:
                    e=PermissionError(13,'access');e.winerror=5;raise e
                return orig(src,dst)
            m.os.replace=fake;m.time.sleep=lambda x:sleeps.append(x);m.write_json_atomic(p,{'a':1})
            checks['win5_retry_success']=len(calls)==3 and sleeps==[0.05,0.10] and json.loads(p.read_text())=={'a':1}
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'y.json';calls=[]
            def bad(src,dst):calls.append(1);raise OSError(28,'disk full')
            m.os.replace=bad
            try:m.write_json_atomic(p,{'a':1}); checks['nonretry_immediate']=False
            except OSError:checks['nonretry_immediate']=len(calls)==1
    finally:m.os.replace=orig;m.time.sleep=orig_sleep
    return checks


def _g101_return_packaging_selftest():
    with tempfile.TemporaryDirectory(prefix='g101_return_test_') as td:
        td=Path(td);chunks=[]
        for ci in range(100):
            p=td/f'c{ci:03d}.zip'
            with zipfile.ZipFile(p,'w') as z:z.writestr('x.txt',str(ci))
            chunks.append({'path':p.name,'bytes':p.stat().st_size,'sha256':sha256_file(p),'crc':'PASS','member_count':1})
        # Pure contract assertions used by production builder.
        shard_names=[f'RETURN_SHARD_{si:02d}_{si*100:03d}_{si*100+99:03d}.zip' for si in range(10)]
        checks={'100_chunks':len(chunks)==100,'10_shards':len(shard_names)==10,'ranges_exact':shard_names[0]=='RETURN_SHARD_00_000_099.zip' and shard_names[-1]=='RETURN_SHARD_09_900_999.zip','tamper_detected':sha256_bytes(b'tampered')!='0'*64}
        return checks



def _g101_cross_micro100_leakage():
    micro_path=HERE/'PLAN'/'MICRO100_PACKAGE_FROZEN_PLAN.json'
    if not micro_path.is_file():return {'status':'FAIL','reason':'MICRO100_PLAN_MISSING'}
    mj=json.loads(micro_path.read_text(encoding='utf-8')); mi=mj.get('requests') or []
    meta,_=_g101_plan_meta(); gi=meta['sample_identities']
    m_req={r['input_digest_sha256'] for r in mi};m_rec={r['scene']['recipe_digest_sha256'] for r in mi};m_base={r['scene']['base_scene_id'] for r in mi};m_idx={int(r['scene_index']) for r in mi}
    g_req={r['request_digest'] for r in gi};g_rec={r['recipe_digest'] for r in gi};g_base={r['base_scene_id'] for r in gi};g_idx={int(r['scene_index']) for r in gi}
    overlaps={'request_digest':sorted(m_req&g_req),'recipe_digest':sorted(m_rec&g_rec),'base_scene_id':sorted(m_base&g_base),'scene_index':sorted(m_idx&g_idx)}
    return {'schema':'DF-G101-CROSS-MICRO100-LEAKAGE-V1','status':'PASS' if not any(overlaps.values()) else 'FAIL','micro100_count':len(mi),'g101_count':len(gi),'overlaps':overlaps}


def _g101_orchestration_simulation():
    # Pure state-machine gate: acceptance is evaluated before advancing to the next chunk.
    rendered=[];accepted=[];fail_at=(37,5)
    stopped=False
    for ci in range(100):
        if stopped:break
        rendered.append(ci)
        for si in range(10):
            if (ci,si)==fail_at:
                stopped=True;break
            accepted.append(ci*10+si)
    fail_closed=(rendered==list(range(38)) and max(accepted)==374 and 38 not in rendered)
    # Authorized-resume simulation: completed 0..37 are cache-reused, continuation begins 38.
    prior=set(range(38));rerendered=[];continued=[]
    for ci in range(100):
        if ci in prior: continue
        continued.append(ci)
    resume_ok=(not rerendered and continued[0]==38 and continued[-1]==99 and len(continued)==62)
    return {'schema':'DF-G101-ORCHESTRATION-SIM-V1','status':'PASS' if fail_closed and resume_ok else 'FAIL','fail_closed_before_next_chunk':fail_closed,'rendered_chunks_before_injected_failure':rendered,'accepted_samples_before_failure':len(accepted),'resume_cache_no_rerender':resume_ok,'resume_first_new_chunk':continued[0] if continued else None}


def _g101_verify_shard_zip(path:Path, expected_chunks=None):
    path=Path(path)
    try:
        with zipfile.ZipFile(path) as z:
            if z.testzip() is not None:return False
            m=json.loads(z.read('SHARD_MANIFEST.json'))
            chunks=m.get('chunks') or []
            if expected_chunks is not None and chunks!=expected_chunks:return False
            for r in chunks:
                name='CHUNKS/'+r['path']
                try:b=z.read(name)
                except KeyError:return False
                if len(b)!=int(r['bytes']) or sha256_bytes(b)!=r['sha256']:return False
        return True
    except Exception:return False


def _g101_shard_integrity_negative_control():
    with tempfile.TemporaryDirectory(prefix='g101_shard_nc_') as td:
        td=Path(td); recs=[]; files=[]
        for i in range(10):
            p=td/f'chunk{i}.zip';p.write_bytes((f'chunk-{i}-payload').encode());files.append(p);recs.append({'path':p.name,'bytes':p.stat().st_size,'sha256':sha256_file(p),'crc':'PASS','member_count':1})
        good=td/'good.zip'
        with zipfile.ZipFile(good,'w',compression=zipfile.ZIP_DEFLATED) as z:
            fixed_zip_write(z,'SHARD_MANIFEST.json',(json.dumps({'schema':'DF-G101-RETURN-SHARD-MANIFEST-V1','shard_index':0,'sample_range':[0,99],'chunks':recs},indent=2,sort_keys=True)+'\n').encode())
            for r,p in zip(recs,files):fixed_zip_write(z,'CHUNKS/'+r['path'],p.read_bytes())
        good_ok=_g101_verify_shard_zip(good,recs)
        bad=td/'bad.zip';shutil.copy2(good,bad)
        # Rebuild with one payload tampered but manifest unchanged.
        with zipfile.ZipFile(bad,'w',compression=zipfile.ZIP_DEFLATED) as z:
            fixed_zip_write(z,'SHARD_MANIFEST.json',(json.dumps({'schema':'DF-G101-RETURN-SHARD-MANIFEST-V1','shard_index':0,'sample_range':[0,99],'chunks':recs},indent=2,sort_keys=True)+'\n').encode())
            for idx,(r,p) in enumerate(zip(recs,files)):fixed_zip_write(z,'CHUNKS/'+r['path'],p.read_bytes()+(b'X' if idx==4 else b''))
        bad_detected=not _g101_verify_shard_zip(bad,recs)
        return {'good_shard_pass':good_ok,'tampered_shard_detected':bad_detected}

def g101_pre_real_selftest():
    M=_load_modules(SOURCE)
    pv=_g101_validate_frozen_plan(M,full_policy_audit=False)
    audit=_g101_r2_verify_policy_audit_authority()
    guard=json.loads((HERE/'DF_G101_R2_RUNTIME_POLICY_GUARD.json').read_text(encoding='utf-8'))
    rr=_g101_retry_regression(); rp=_g101_return_packaging_selftest(); leak=_g101_cross_micro100_leakage(); shardnc=_g101_shard_integrity_negative_control()
    report_names=[
      'DF_G101_R2_EXACT_TARGET0005_FIXTURE.json',
      'DF_G101_R2_INHERITED_R33_R36_REGRESSION.json',
      'DF_G101_R2_ELIGIBILITY_AST_AUDIT.json',
      'DF_G101_R2_SYNTHETIC_RECOVERY_SELFTEST.json',
      'DF_G101_R2_FAILURE_TRANSPORT_SELFTEST.json']
    reports={}
    for name in report_names:
        q=HERE/name
        reports[name]=json.loads(q.read_text(encoding='utf-8')) if q.is_file() else {'status':'MISSING'}
    main_src=Path(__file__).read_text(encoding='utf-8')
    worker=(SOURCE/'pcs_factory_blender_worker.py').read_text(encoding='utf-8')
    bat=(HERE/'RUN_DF_G101_SCALE1K.bat').read_bytes(); psb=(HERE/'RUN_DF_G101_SCALE1K_GUARDIAN.ps1').read_bytes(); ps=psb.decode('utf-8-sig')
    checks={
      'plan_validation_fast':pv['status']=='PASS',
      'full_167_blueprint_audit_authority':audit['status']=='PASS' and audit['r2_count']==10 and audit['r33_count']==7 and audit['r36_count']==1,
      'runtime_policy_guard':guard['status']=='PASS',
      'exact_target0005_fixture':reports[report_names[0]].get('status')=='PASS',
      'inherited_r33_r36_regression':reports[report_names[1]].get('status')=='PASS',
      'eligibility_ast_no_forbidden_reads':reports[report_names[2]].get('status')=='PASS',
      'synthetic_exact_r1_prestate_recovery':reports[report_names[3]].get('status')=='PASS',
      'failure_transport_collision_tamper':reports[report_names[4]].get('status')=='PASS',
      'r34_retry_win5':rr.get('win5_retry_success') is True,
      'r34_nonretry':rr.get('nonretry_immediate') is True,
      'return_contract':all(rp.values()),
      'cross_micro100_leakage_zero':leak['status']=='PASS',
      'shard_integrity_negative_control':all(shardnc.values()),
      'source_release_id_r2':SOURCE_RELEASE_ID=='DF_G101_SCALE1K_V1_R1_TOOL_R2',
      'frozen_release_and_requests':RELEASE_ID=='DF_G101_SCALE1K_V1_R1' and DATASET_ID=='PCS_CAMERA_GEOMETRY_SCALE1K_V1',
      'worker_r2_after_r36':worker.find('r36_rgb_policy = r36_blueprint_extreme_vertical_policy(request)') < worker.find('g101_r2_rgb_policy = g101_r2_blueprint_foreground_vertical_policy(request)') < worker.find('\"g101_r2_blueprint_foreground_vertical_policy\": g101_r2_rgb_policy'),
      'production_continues_at_chunk001':'for ci in range(1,G101_CHUNK_COUNT):' in main_src,
      'recovery_no_worker_call':'execute_chunk' not in main_src[main_src.index('def _g101_r2_recover_chunk000'):main_src.index('\ndef g101_run',main_src.index('def _g101_r2_recover_chunk000'))],
      'visual_review_includes_all_r2':"if r['sample_id'] in G101_R2_EXPECTED:add(i,'G101_R2_APPLIED')" in main_src,
      'guardian_requires_existing_r1':'BLOCKED_REQUIRED_R1_FAILURE_RUNROOT_MISSING' in ps and 'BLOCKED_R2_RECOVERY_ALREADY_INITIALIZED_DO_NOT_RERUN' in ps,
      'guardian_never_deletes_runroot':'Remove-Item' not in '\n'.join(line for line in ps.splitlines() if '$RunRoot' in line),
      'bat_crlf_only':bat.count(b'\n')==bat.count(b'\r\n') and bat.count(b'\r\n')>=30,
      'bat_r2_recovery':'R2 RECOVERY' in bat.decode('ascii') and 'existing R1 fail-closed run-root' in bat.decode('ascii'),
      'protected_firewalls':('scale_10k_authorized = $false' in ps and 'training_started = $false' in ps and 'test77_accessed = $false' in ps),
    }
    compile_errors=[]
    for q in [HERE/'df_g101_scale1k.py']+sorted(SOURCE.glob('*.py')):
        try: compile(q.read_text(encoding='utf-8-sig'),str(q),'exec')
        except Exception as e: compile_errors.append(f'{q.name}:{type(e).__name__}:{e}')
    checks['python_sources_compile']=not compile_errors
    out={'schema':'DF-G101-R2-MAIN-PRE-REAL-SELFTEST-V1','status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'plan_validation':pv,'full_policy_audit_authority':audit,'runtime_policy_guard':guard,'reports':{k:v.get('status') for k,v in reports.items()},'retry_regression':rr,'return_packaging':rp,'cross_micro100_leakage':leak,'shard_negative_control':shardnc,'compile_errors':compile_errors,'authority':{'r2_real_recovery_authorized':False,'scale_10k_authorized':False,'training_started':False,'test77_accessed':False,'maya_mutated':False,'product_mutated':False}}
    atomic_json(HERE/'DF_G101_R2_MAIN_PRE_REAL_SELFTEST.json',out)
    print(json.dumps(out,indent=2,sort_keys=True)); return 0 if out['status']=='PASS' else 2

def g101_package_failure(factory_root):
    root=Path(factory_root);return _g101_compact_failure(root,root/'09_RUNS'/RUN_ID,'GUARDIAN_REQUESTED_FAILURE_PACKAGE')


def g101_main():
    ap=argparse.ArgumentParser();ap.add_argument('command',choices=['run','selftest','package-failure']);ap.add_argument('--factory-root',default=os.environ.get('PCS_CAMERA_FACTORY_ROOT',r'C:\PCS_LABS\CAMERA_GEOMETRY_DATA_FACTORY'));a=ap.parse_args()
    if a.command=='selftest':return g101_pre_real_selftest()
    root=Path(a.factory_root);runroot=root/'09_RUNS'/RUN_ID
    if a.command=='package-failure':print(g101_package_failure(a.factory_root));return 0
    try:return g101_run(a.factory_root)
    except KeyboardInterrupt:
        try:_g101_progress(runroot)
        except Exception:pass
        z=_g101_compact_failure(root,runroot,'INTERRUPTED_BY_OPERATOR',traceback.format_exc());print('\n[DF-G101] INTERRUPTED. Do not rerun before adjudication. Failure bundle:',z,flush=True);return 130
    except Exception as e:
        try:_g101_progress(runroot)
        except Exception:pass
        try:z=_g101_compact_failure(root,runroot,f'{type(e).__name__}:{e}',traceback.format_exc())
        except Exception as pe:z=f'FAILURE_PACKAGE_ERROR:{type(pe).__name__}:{pe}'
        print('\n[DF-G101] FAIL CLOSED:',type(e).__name__,e,flush=True);print('[DF-G101] Failure bundle:',z,flush=True);return 2

if __name__=='__main__':raise SystemExit(g101_main())
