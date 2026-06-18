# MIXER -> EXCHANGE Confusion Case Study

Total misclassified: 4
Total correctly classified: 6

## Misclassified Cases

### Case 1: Node 239803
- True: MIXER, Predicted: EXCHANGE, Confidence: 0.9817
- In-degree: 32, Out-degree: 11, Total: 43
- Same-label ratio: 0.0000
- Unlabeled ratio: 0.8372
- Top in-neighbors: {0: 3, 3: 2, 8: 1}
- Top out-neighbors: {3: 1}
- In-amount mean: -0.40
- Out-amount mean: -0.33
- Supernode (>100): False

### Case 2: Node 31697
- True: MIXER, Predicted: EXCHANGE, Confidence: 0.7129
- In-degree: 28, Out-degree: 73, Total: 101
- Same-label ratio: 0.1111
- Unlabeled ratio: 0.8218
- Top in-neighbors: {0: 1, 9: 1}
- Top out-neighbors: {0: 10, 2: 2, 9: 1}
- In-amount mean: -0.16
- Out-amount mean: -0.05
- Supernode (>100): True

### Case 3: Node 233782
- True: MIXER, Predicted: EXCHANGE, Confidence: 0.4712
- In-degree: 1, Out-degree: 2, Total: 3
- Same-label ratio: 0.0000
- Unlabeled ratio: 1.0000
- Top in-neighbors: {}
- Top out-neighbors: {}
- In-amount mean: -0.52
- Out-amount mean: -0.52
- Supernode (>100): False

## Correctly Classified Cases

### Case 1: Node 237376
- True: MIXER, Predicted: MIXER, Confidence: 0.9769
- In-degree: 26, Out-degree: 9, Total: 35
- Same-label ratio: 0.0000
- Unlabeled ratio: 0.8857
- Top in-neighbors: {8: 1, 0: 1}
- Top out-neighbors: {8: 1, 0: 1}

### Case 2: Node 239400
- True: MIXER, Predicted: MIXER, Confidence: 0.9665
- In-degree: 31, Out-degree: 22, Total: 53
- Same-label ratio: 0.0000
- Unlabeled ratio: 0.8679
- Top in-neighbors: {3: 2, 8: 1, 0: 1}
- Top out-neighbors: {8: 1, 0: 1, 3: 1}

### Case 3: Node 237293
- True: MIXER, Predicted: MIXER, Confidence: 0.9662
- In-degree: 30, Out-degree: 27, Total: 57
- Same-label ratio: 0.0000
- Unlabeled ratio: 0.8070
- Top in-neighbors: {0: 2, 8: 1, 3: 1}
- Top out-neighbors: {0: 6, 8: 1}
