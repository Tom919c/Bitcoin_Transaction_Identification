# Case Study: EGS Prediction Analysis

## Model: EdgeGatedSAGE (seed=3407, class_balanced_khop)

- Test nodes: 6820
- Correctly identified sensitive: 1767
- False positives: 207
- False negatives (missed): 77

## Correctly Identified Sensitive Entities

### BET (1339 correct)
- Node 27003: true=BET, pred=BET, conf=0.928
- Node 28491: true=BET, pred=PONZI, conf=0.588
- Node 29331: true=BET, pred=BET, conf=0.783
- Node 29333: true=BET, pred=BET, conf=0.860
- Node 29381: true=BET, pred=BET, conf=0.532

### BRIDGE (14 correct)
- Node 237446: true=BRIDGE, pred=BRIDGE, conf=0.608
- Node 238817: true=BRIDGE, pred=BRIDGE, conf=0.989
- Node 239225: true=BRIDGE, pred=BRIDGE, conf=0.987
- Node 239272: true=BRIDGE, pred=BRIDGE, conf=0.938
- Node 239279: true=BRIDGE, pred=BRIDGE, conf=0.989

### GAMBLING (236 correct)
- Node 10875: true=GAMBLING, pred=GAMBLING, conf=0.655
- Node 12233: true=GAMBLING, pred=GAMBLING, conf=0.990
- Node 13271: true=GAMBLING, pred=GAMBLING, conf=0.984
- Node 13320: true=GAMBLING, pred=MARKETPLACE, conf=0.685
- Node 14349: true=GAMBLING, pred=GAMBLING, conf=0.822

### MARKETPLACE (15 correct)
- Node 49499: true=MARKETPLACE, pred=MARKETPLACE, conf=0.870
- Node 220470: true=MARKETPLACE, pred=GAMBLING, conf=0.477
- Node 224898: true=MARKETPLACE, pred=RANSOMWARE, conf=0.983
- Node 227443: true=MARKETPLACE, pred=RANSOMWARE, conf=0.350
- Node 228566: true=MARKETPLACE, pred=RANSOMWARE, conf=0.805

### MIXER (12 correct)
- Node 53172: true=MIXER, pred=GAMBLING, conf=0.597
- Node 99303: true=MIXER, pred=GAMBLING, conf=0.724
- Node 224767: true=MIXER, pred=RANSOMWARE, conf=0.981
- Node 233880: true=MIXER, pred=RANSOMWARE, conf=0.626
- Node 235705: true=MIXER, pred=MIXER, conf=0.935

### PONZI (104 correct)
- Node 2629: true=PONZI, pred=PONZI, conf=0.884
- Node 2639: true=PONZI, pred=PONZI, conf=0.444
- Node 3827: true=PONZI, pred=PONZI, conf=0.800
- Node 16846: true=PONZI, pred=GAMBLING, conf=0.452
- Node 20479: true=PONZI, pred=GAMBLING, conf=0.352

### RANSOMWARE (47 correct)
- Node 24082: true=RANSOMWARE, pred=RANSOMWARE, conf=0.367
- Node 29806: true=RANSOMWARE, pred=RANSOMWARE, conf=0.981
- Node 30398: true=RANSOMWARE, pred=RANSOMWARE, conf=0.989
- Node 30859: true=RANSOMWARE, pred=RANSOMWARE, conf=0.989
- Node 31732: true=RANSOMWARE, pred=RANSOMWARE, conf=0.992

## False Positives

### Predicted as BET (12 FP)
- Node 26300: true=INDIVIDUAL, pred=BET, conf=0.773
- Node 45506: true=EXCHANGE, pred=BET, conf=0.442
- Node 46453: true=INDIVIDUAL, pred=BET, conf=0.703
- Node 52626: true=INDIVIDUAL, pred=BET, conf=0.870
- Node 88215: true=INDIVIDUAL, pred=BET, conf=0.344

### Predicted as BRIDGE (2 FP)
- Node 239557: true=EXCHANGE, pred=BRIDGE, conf=0.784
- Node 241720: true=MINING, pred=BRIDGE, conf=0.910

### Predicted as GAMBLING (69 FP)
- Node 5302: true=INDIVIDUAL, pred=GAMBLING, conf=0.350
- Node 8206: true=FAUCET, pred=GAMBLING, conf=0.809
- Node 11310: true=INDIVIDUAL, pred=GAMBLING, conf=0.903
- Node 13569: true=INDIVIDUAL, pred=GAMBLING, conf=0.465
- Node 14568: true=INDIVIDUAL, pred=GAMBLING, conf=0.968

### Predicted as MARKETPLACE (11 FP)
- Node 11208: true=INDIVIDUAL, pred=MARKETPLACE, conf=0.410
- Node 19118: true=INDIVIDUAL, pred=MARKETPLACE, conf=0.557
- Node 110795: true=MINING, pred=MARKETPLACE, conf=0.319
- Node 223668: true=INDIVIDUAL, pred=MARKETPLACE, conf=0.892
- Node 232175: true=EXCHANGE, pred=MARKETPLACE, conf=0.682

### Predicted as MIXER (18 FP)
- Node 27893: true=INDIVIDUAL, pred=MIXER, conf=0.895
- Node 82106: true=INDIVIDUAL, pred=MIXER, conf=0.335
- Node 101219: true=INDIVIDUAL, pred=MIXER, conf=0.361
- Node 111939: true=INDIVIDUAL, pred=MIXER, conf=0.383
- Node 213167: true=INDIVIDUAL, pred=MIXER, conf=0.553

### Predicted as PONZI (62 FP)
- Node 1394: true=INDIVIDUAL, pred=PONZI, conf=0.592
- Node 3100: true=EXCHANGE, pred=PONZI, conf=0.615
- Node 4014: true=INDIVIDUAL, pred=PONZI, conf=0.529
- Node 5399: true=EXCHANGE, pred=PONZI, conf=0.811
- Node 5928: true=EXCHANGE, pred=PONZI, conf=0.537

### Predicted as RANSOMWARE (33 FP)
- Node 16548: true=INDIVIDUAL, pred=RANSOMWARE, conf=0.722
- Node 21175: true=INDIVIDUAL, pred=RANSOMWARE, conf=0.609
- Node 34451: true=EXCHANGE, pred=RANSOMWARE, conf=0.423
- Node 40602: true=INDIVIDUAL, pred=RANSOMWARE, conf=0.860
- Node 57281: true=INDIVIDUAL, pred=RANSOMWARE, conf=0.884

## False Negatives (Missed Sensitive)

### BET (5 missed)
- Node 215696: true=BET, pred=INDIVIDUAL, conf=0.796
- Node 215736: true=BET, pred=INDIVIDUAL, conf=0.687
- Node 217865: true=BET, pred=INDIVIDUAL, conf=0.634
- Node 218024: true=BET, pred=INDIVIDUAL, conf=0.659
- Node 218253: true=BET, pred=INDIVIDUAL, conf=0.631

### GAMBLING (46 missed)
- Node 2112: true=GAMBLING, pred=EXCHANGE, conf=0.884
- Node 4709: true=GAMBLING, pred=EXCHANGE, conf=0.898
- Node 4912: true=GAMBLING, pred=EXCHANGE, conf=0.616
- Node 8669: true=GAMBLING, pred=EXCHANGE, conf=0.684
- Node 9532: true=GAMBLING, pred=MINING, conf=0.848

### MARKETPLACE (8 missed)
- Node 6525: true=MARKETPLACE, pred=EXCHANGE, conf=0.909
- Node 8046: true=MARKETPLACE, pred=INDIVIDUAL, conf=0.594
- Node 15621: true=MARKETPLACE, pred=EXCHANGE, conf=0.584
- Node 18344: true=MARKETPLACE, pred=EXCHANGE, conf=0.454
- Node 32063: true=MARKETPLACE, pred=INDIVIDUAL, conf=0.904

### MIXER (4 missed)
- Node 31697: true=MIXER, pred=EXCHANGE, conf=0.713
- Node 38257: true=MIXER, pred=EXCHANGE, conf=0.418
- Node 233782: true=MIXER, pred=EXCHANGE, conf=0.471
- Node 239803: true=MIXER, pred=EXCHANGE, conf=0.982

### PONZI (14 missed)
- Node 5625: true=PONZI, pred=FAUCET, conf=0.728
- Node 26454: true=PONZI, pred=EXCHANGE, conf=0.747
- Node 29032: true=PONZI, pred=INDIVIDUAL, conf=0.608
- Node 32718: true=PONZI, pred=MINING, conf=0.370
- Node 37121: true=PONZI, pred=FAUCET, conf=0.327

