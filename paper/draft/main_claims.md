# Main Claims

## A. Strong Claims (Well-Supported)

1. **Activity-biased sampling distorts label space**: The old TopK/Z-score sampling protocol loses 6 critical AML classes and inflates performance metrics. Label-preserving protocols are essential.

2. **class_balanced_khop enables graph structure utilization**: GraphSAGE achieves 0.5785 Macro-F1 on CBK vs 0.4627 on label_preserving, demonstrating that proper sampling enables GNN message passing.

3. **Direction-aware aggregation is the core driver**: EGS with direction separation achieves +0.082 Macro-F1 over no-direction variant on CBK. Without direction split, edge gating alone provides no benefit.

4. **Temporal generalization is a major unsolved challenge**: All models suffer 50-70% Macro-F1 drop from CBK to temporal_balanced, revealing genuine temporal distribution shift.

5. **Conservative sensitive ranking is meaningful**: EGS achieves AUPRC 0.748 for PONZI/RANSOMWARE/MIXER ranking, demonstrating practical AML value despite imperfect classification.

## B. Challenges / Limitations (Cannot Overstate)

1. **Temporal OOD gap remains unresolved**: Topology-aware reweighting does not pass the method-contribution gate (delta +0.005, threshold +0.03).

2. **Raw temporal edge features cannot be a method contribution**: They drift severely (KS>0.5) under temporal split and are pseudo-correlated with the target under random split.

3. **MIXER node-level classification is fundamentally limited**: Only 0.4% same-label neighbor ratio, 80 total nodes, 10 test samples. Subgraph reasoning may be needed.

4. **Extended ranking is inflated by easy classes**: BET/GAMBLING dominate extended sensitive ranking, masking the real difficulty of high-sensitivity classes.

## C. Requires Further Validation

1. Whether causal decoupling or environment-invariant learning can address temporal OOD
2. Whether MIXER can benefit from subgraph/motif-level reasoning
3. Whether the benchmark protocol can be adopted by the community
4. Whether direction-aware aggregation generalizes to other cryptocurrency graphs
