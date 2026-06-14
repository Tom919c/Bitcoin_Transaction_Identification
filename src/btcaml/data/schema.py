from __future__ import annotations

NODE_TABLE_DEFAULT = 'node_features'
EDGE_TABLE_DEFAULT = 'transaction_edges'

NODE_COLUMNS = [
    'alias', 'degree', 'degree_in', 'degree_out',
    'total_transactions_in', 'total_transactions_out',
    'min_sent', 'max_sent', 'total_sent',
    'min_received', 'max_received', 'total_received',
    'cluster_size',
    'first_transaction_in', 'last_transaction_in',
    'first_transaction_out', 'last_transaction_out',
    'cluster_num_edges', 'cluster_num_cc', 'cluster_num_nodes_in_cc',
    'label',
]

NODE_NUMERIC_COLUMNS = [c for c in NODE_COLUMNS if c not in {'alias', 'label'}]

EDGE_COLUMNS = ['a', 'b', 'reveal', 'last_seen', 'total', 'min_sent', 'max_sent', 'total_sent']
EDGE_NUMERIC_COLUMNS = ['reveal', 'last_seen', 'total', 'min_sent', 'max_sent', 'total_sent']

AMOUNT_COLUMNS_NODE = [
    'min_sent', 'max_sent', 'total_sent', 'min_received', 'max_received', 'total_received',
]

COUNT_COLUMNS_NODE = [
    'degree', 'degree_in', 'degree_out', 'total_transactions_in', 'total_transactions_out',
    'cluster_size', 'cluster_num_edges', 'cluster_num_cc', 'cluster_num_nodes_in_cc',
]

TIME_COLUMNS_NODE = [
    'first_transaction_in', 'last_transaction_in', 'first_transaction_out', 'last_transaction_out',
]

AMOUNT_COLUMNS_EDGE = ['min_sent', 'max_sent', 'total_sent']
COUNT_COLUMNS_EDGE = ['total']
TIME_COLUMNS_EDGE = ['reveal', 'last_seen']
