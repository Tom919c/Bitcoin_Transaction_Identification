# PONZI -> EXCHANGE Confusion Case Study

Total misclassified: 7
Total correctly classified: 95

## Misclassified Cases

### Case 1: Node 225362
- True: PONZI, Predicted: EXCHANGE, Confidence: 0.8431
- In-degree: 5, Out-degree: 1, Total: 6
- Same-label ratio: 0.0000
- Unlabeled ratio: 0.6667
- Top in-neighbors: {3: 1}
- Top out-neighbors: {2: 1}
- In-amount mean: -0.52
- Out-amount mean: -0.05
- Supernode (>100): False

### Case 2: Node 26454
- True: PONZI, Predicted: EXCHANGE, Confidence: 0.7465
- In-degree: 28, Out-degree: 19, Total: 47
- Same-label ratio: 0.0000
- Unlabeled ratio: 0.9149
- Top in-neighbors: {}
- Top out-neighbors: {0: 3, 2: 1}
- In-amount mean: -0.49
- Out-amount mean: -0.52
- Supernode (>100): False

### Case 3: Node 40152
- True: PONZI, Predicted: EXCHANGE, Confidence: 0.7279
- In-degree: 37, Out-degree: 55, Total: 92
- Same-label ratio: 0.0870
- Unlabeled ratio: 0.7500
- Top in-neighbors: {3: 1, 5: 1, 2: 1}
- Top out-neighbors: {0: 16, 6: 2, 5: 1}
- In-amount mean: -0.11
- Out-amount mean: 0.22
- Supernode (>100): False

## Correctly Classified Cases

### Case 1: Node 91763
- True: PONZI, Predicted: PONZI, Confidence: 0.9897
- In-degree: 2, Out-degree: 2, Total: 4
- Same-label ratio: 1.0000
- Unlabeled ratio: 0.7500
- Top in-neighbors: {}
- Top out-neighbors: {5: 1}

### Case 2: Node 106403
- True: PONZI, Predicted: PONZI, Confidence: 0.9896
- In-degree: 23, Out-degree: 8, Total: 31
- Same-label ratio: 0.6667
- Unlabeled ratio: 0.8065
- Top in-neighbors: {5: 2, 2: 1}
- Top out-neighbors: {5: 2, 0: 1}

### Case 3: Node 95621
- True: PONZI, Predicted: PONZI, Confidence: 0.9891
- In-degree: 35, Out-degree: 28, Total: 63
- Same-label ratio: 0.5455
- Unlabeled ratio: 0.8254
- Top in-neighbors: {0: 3, 5: 3, 2: 1}
- Top out-neighbors: {5: 3, 0: 1}
