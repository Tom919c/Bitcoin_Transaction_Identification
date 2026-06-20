# Problem Definition

## Task Formulation

The task is NOT binary illicit/clicit classification. It is **11-class Bitcoin entity identification** on a directed heterogeneous transaction graph, with downstream **sensitive risk ranking** for AML applications.

## Label Space

11 supervised classes (INDIVIDUAL=0 through BRIDGE=10), plus unlabeled background nodes (label=-1) that provide transaction context but do not participate in supervised training or evaluation.

## Graph Properties

- 252M+ raw nodes, 785M+ raw edges in the full Bitcoin transaction graph
- 34,098 labeled entity nodes across 11 classes
- Severe class imbalance: INDIVIDUAL has 23K+ nodes, MIXER has only 80
- Directed edges representing fund flow (sender -> receiver)
- Edge attributes: 11-dimensional features including temporal, frequency, and monetary features

## Key Challenges

1. **Severe heterophily**: Most classes have <10% same-label neighbors (MIXER: 0.4%)
2. **Unlabeled neighbor dominance**: 77-95% of in-edge neighbors are unlabeled
3. **Temporal distribution shift**: Model performance degrades significantly under temporal split vs random split
4. **Extreme class imbalance**: 290:1 ratio between largest and smallest classes
5. **Directional semantics**: In-edge and out-edge carry fundamentally different information (receiving vs sending funds)
