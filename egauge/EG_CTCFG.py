# The following table is obtained from
# http://egauge1910.egaug.es/Setting.cjs
# javascript variable 'w =' the following

CT_CFG_TABLE=[["5A",None,241.323,"","5.6@1:3@10:2.5@100"],
["10A",None,121.873,"","5.6@1:3@10:2.5@100"],
["15A",None,81.519,"","5.6@1:3@10:2.5@100"],
["20A",None,61.25,"","5.6@1:3@10:2.5@100"],
["25A",None,49.039,"","5.6@1:3@10:2.5@100"],
["30A",None,40.897,"","5.6@1:3@10:2.5@100"],
["50A",None,24.509,"","5.6@1:3@10:2.5@100"],
["60A",None,20.485,"","5.6@1:3@10:2.5@100"],
["70A",None,17.5,"","5.6@1:3@8:1.5@100"],
["75A",None,16.409,"","5.6@1:3@10:2.5@100"],
["100A",None,12.281,"","5.6@1:3@8:1.5@100"],
["150A",None,8.194,"","5.6@1:3@8:1.5@100"],
["200A",None,6.148,"","5.6@1:3@8:1.5@100"],
["300A",None,4.101,"","5.6@1:3@8:1.5@100"],
["400A",None,3.075,"","5.6@1:3@8:1.5@100"],
["600A",None,2.051,"","5.6@1:3@8:1.5@100"],
["800A",None,1.538,"","5.6@1:3@8:1.5@100"],
["1000A",None,1.231,"","5.6@1:3@8:1.5@100"],
["1200A",None,1.026,"","5.6@1:3@8:1.5@100"],
["1500A",None,0.821,"","5.6@1:3@8:1.5@100"],
["2000A",None,0.616,"","5.6@1:3@8:1.5@100"],
["3000A",None,0.411,"","5.6@1:3@8:1.5@100"],
["AccuCT  50A",None,24.642,"","0@50"],
["AccuCT 100A",None,12.33,"","0@50"],
["250A rope",None,4.925,"",""],
['Rope 6',None,1.709,"int","5@0:1@0.4:0@100"],
[" 10A DC",359,-137.4,"","0@50"],
[" 20A DC",359,-68.7,"","0@50"],
[" 50A DC",359,-27.48,"","0@50"],
["100A DC",359,-13.74,"","0@50"],
["150A DC",359,-9.16,"","0@50"],
["custom",None,0.000,"",""],
]
# firmware version 2.01 use new calibration factors
CT_CFG_TABLE2=[["5A",None,241.323,"","5.6@1:3@10:2.5@100"],
["10A",None,121.873,"","5.6@1:3@10:2.5@100"],
["15A",None,81.519,"","5.6@1:3@10:2.5@100"],
["20A",None,61.25,"","5.6@1:3@10:2.5@100"],
["25A",None,49.039,"","5.6@1:3@10:2.5@100"],
["30A",None,40.897,"","5.6@1:3@10:2.5@100"],
["50A",None,24.509,"","5.6@1:3@10:2.5@100"],
["60A",None,20.485,"","5.6@1:3@10:2.5@100"],
["70A",None,17.5,"","4.5@0:2.9@3:2.4@30:2.1@100"],
["75A",None,16.409,"","5.6@1:3@10:2.5@100"],
["100A",None,12.281,"","4.5@0:2.9@3:2.4@30:2.1@100"],
["150A",None,8.194,"","4.5@0:2.9@3:2.4@30:2.1@100"],
["200A",None,6.148,"","5.6@1:3@8:1.5@100"],
["300A",None,4.101,"","5.6@1:3@8:1.5@100"],
["400A",None,3.075,"","5.6@1:3@8:1.5@100"],
["600A",None,2.051,"","5.6@1:3@8:1.5@100"],
["800A",None,1.538,"","5.6@1:3@8:1.5@100"],
["1000A",None,1.231,"","5.6@1:3@8:1.5@100"],
["1200A",None,1.026,"","5.6@1:3@8:1.5@100"],
["1500A",None,0.821,"","5.6@1:3@8:1.5@100"],
["2000A",None,0.616,"","5.6@1:3@8:1.5@100"],
["3000A",None,0.411,"","5.6@1:3@8:1.5@100"],
["4000A",None,0.308,"","5.6@1:3@8:1.5@100"],
["AccuCT  50A",None,24.642,"","0.33@3:0.262@6:0.007@50:-0.192@100"],
["AccuCT 100A",None,12.33,"",".27@1.5:.24@3:.20@6:.08@15:-.09@50:-.27@100"],
["AccuCT 200A",None,6.165,"",".3@.1:.32@1:.33@1.5:.31@3:.28@6:.19@15:0@50:-.16@100"],
["250A rope",None,4.925,"",""],
['Rope 6',None,0.191,"int","6@50"],
[" 10A DC",359,-137.4,"","0@50"],
[" 20A DC",359,-68.7,"","0@50"],
[" 50A DC",359,-27.48,"","0@50"],
["100A DC",359,-13.74,"","0@50"],
["150A DC",359,-9.16,"","0@50"],
["custom",None,0.000,"",""],
]

CT_CFG = dict([(r[0].strip(), r) for r in CT_CFG_TABLE])
CT_CFG_BY_MULTIPLIER = dict([("{:.3f}".format(r[2]), r) for r in CT_CFG_TABLE])

CT_CFG2 = dict([(r[0].strip(), r) for r in CT_CFG_TABLE2])
CT_CFG_BY_MULTIPLIER2 = dict([("{:.3f}".format(r[2]), r) for r in CT_CFG_TABLE2])

CT_CFG['Rope CT'] = CT_CFG['Rope 6']
CT_CFG2['Rope CT'] = CT_CFG2['Rope 6']

# CT and PT configuration is ordered in a peculiar way.
CT_MAP = {
        0: 'L1',
        1: 'L2',
        2: 'CT1',
        3: 'CT2',
        4: 'CT3',
        5: 'CT4',
        6: 'CT5',
        7: 'CT6',
        9: 'L3',
        10: 'CT7',
        11: 'CT8',
        12: 'CT9',
        13: 'CT10',
        14: 'CT11',
        15: 'CT12',
        }
CT_MAP_REV = dict( ( val, key ) for (key, val) in CT_MAP.items() )


def get_ch_row(ct_type, calibration=None, mul=None, version="2.0"):
    """
    return a POST config row like 
    for a Rope 6" with calibration of 4.6200 
    ch12=1.7090,15,int,4.6200,5@0:1@0.4:0@100
    or for other CTS like a 200A CT
    ch7=6.1480,15,,, 
    or 400A and other CTS
    ch7=3.0750,15,,,5.6@1:3@8:1.5@100
    """
    _CT_CFG = CT_CFG
    if version >= "2.0":
        _CT_CFG = CT_CFG2
    # for potential transformers the following are the defaults
    if ct_type == 'PT':
        return "-4.0030,-2058,,,"

    if ct_type not in _CT_CFG:
        raise Exception("Unknown CT type {}".format(ct_type))

    if calibration is not None:
        calibration = float(calibration)

    if mul is not None:
        mul = float(mul)

    cfg = _CT_CFG[ct_type]
    # all CT_CFG_TABLE have this in the front
    if mul is None:
        mul = cfg[2]
    ch_row = "{:.4f},15,".format(mul)

    if ct_type in ['Rope 6', 'Rope CT']:
        if calibration is None:
            raise Exception('calibration is required for Rope 6" CT')
        ch_row += "{},{:.4f},{}".format(cfg[3], calibration, cfg[-1])
    elif ct_type == "200A":
        # just put 2 more commas
        ch_row += ",,"
    else:
        ch_row += ",,{}".format(cfg[-1])

    return ch_row


def get_ct_type_by_mul(mul_str, version="2.0"):
    """
    return a ct type version o
    """
    ct_type = None
    _CT_CFG_BY_MULTIPLIER = CT_CFG_BY_MULTIPLIER
    if version >= "2.0":
        _CT_CFG_BY_MULTIPLIER = CT_CFG_BY_MULTIPLIER2
    if mul_str in _CT_CFG_BY_MULTIPLIER:
        ct_type = _CT_CFG_BY_MULTIPLIER[mul_str][0]
    return ct_type


import unittest
class TestEGCTCFG(unittest.TestCase):
    def test_get_ch_row(self):
        test_data = {
                'Rope 6': "1.7090,15,int,4.6200,5@0:1@0.4:0@100",
                '200A': "6.1480,15,,,",
                '400A': "3.0750,15,,,5.6@1:3@8:1.5@100",
                'custom': "99.9900,15,,,"
                }

        for ct_type, ref_ch_row in test_data.items():
            calibration = None
            mul = None
            if ct_type == 'Rope 6':
                calibration = 4.62
            elif ct_type == 'custom':
                mul = 99.99

            ch_row = get_ch_row(ct_type, calibration, mul)
            self.assertEquals(ref_ch_row, ch_row)
