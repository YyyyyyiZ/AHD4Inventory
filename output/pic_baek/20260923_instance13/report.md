# PIC instance 13: Jackie-style Level 1 / Level 2

Excel specification: purchase coefficient 9.025, 200 paths × 1000 periods, discount 0.95. Lower cost is better.
L1 and the main L2 are separate from ten additional L2 draws. L2 ranges are explicitly adapted to PIC.

| Run | Status | Excel mean | SE | 95% t interval | Setup seconds | API USD |
|---|---|---:|---:|---|---:|---:|
| l1_main | valid | 1300.654729 | 17.898837 | [1265.359001, 1335.950457] | 2.306 | 0.354660 |
| l2_main | valid | 1314.170972 | 16.864204 | [1280.915495, 1347.426449] | 1.405 | 0.315071 |
| l2_repeat_01 | valid | 1320.206297 | 21.395360 | [1278.015578, 1362.397017] | 0.930 | 0.218878 |
| l2_repeat_02 | valid | 1317.953513 | 21.374719 | [1275.803496, 1360.103529] | 0.794 | 0.254581 |
| l2_repeat_03 | valid | 1307.657959 | 17.474473 | [1273.199059, 1342.116860] | 2.013 | 0.307678 |
| l2_repeat_04 | valid | 1298.550203 | 13.412097 | [1272.102130, 1324.998276] | 3.492 | 0.303605 |
| l2_repeat_05 | valid | 1315.449158 | 22.341955 | [1271.391795, 1359.506522] | 4.412 | 0.278666 |
| l2_repeat_06 | valid | 1302.489356 | 15.298833 | [1272.320722, 1332.657989] | 0.915 | 0.221340 |
| l2_repeat_07 | valid | 1305.519129 | 17.625684 | [1270.762046, 1340.276211] | 9.706 | 0.274281 |
| l2_repeat_08 | valid | 1324.410832 | 19.533251 | [1285.892110, 1362.929553] | 1.799 | 0.233284 |
| l2_repeat_09 | valid | 1306.277238 | 17.429562 | [1271.906899, 1340.647578] | 0.918 | 0.319958 |
| l2_repeat_10 | valid | 1316.942695 | 21.993844 | [1273.571790, 1360.313600] | 1.583 | 0.303632 |

Actual charges plus unresolved conservative reservations: $4.312225.
Selected using the independent validation set: l2_repeat_07.
All generated artifacts, including invalid ones, are retained. No policy is tuned using Excel test costs.
These are policy costs, not certified optimality gaps. The paper's original PIC numerical settings differ.

Main L2 minus L1 paired cost difference: 13.516243, 95% t CI [3.518626, 23.513860].
Main L2 cost reduction relative to L1: -1.039%.

Additional L2 draws: 10/10 valid so far; mean 1311.545638, median 1311.553559, range [1298.550203, 1324.410832].
Between-draw variation is separate from each policy's demand-path standard error.

Independently trained simple references:
- constant (parameter 6): 1416.033764, SE 29.178274, 95% CI [1358.495476, 1473.572053].
- base_stock (parameter 31): 1328.627027, SE 17.828349, 95% CI [1293.470298, 1363.783756].
