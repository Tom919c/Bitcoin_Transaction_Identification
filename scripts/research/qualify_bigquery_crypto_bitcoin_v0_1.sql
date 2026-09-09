-- BigQuery source qualification for the as-of entity-graph study.
-- Protocol: Gate 3A v0.1. This is a source audit, not an S0 effect query.
--
-- Preconditions before any execution:
--   1. Record explicit billing authorization in the companion manifest.
--   2. Dry-run this exact file with start_height=0 and a frozen end_height.
--   3. Record estimated bytes and set maximum_bytes_billed no higher than the
--      approved cap. Abort if the estimate exceeds that cap.
--   4. Never place credentials or connection material in this file or manifest.
--
-- The formal range must start at genesis. A bounded range is not a valid proxy
-- for C_t because common-input unions accumulate over the full chain prefix.

DECLARE start_height INT64 DEFAULT @start_height;
DECLARE end_height INT64 DEFAULT @end_height;

ASSERT start_height = 0 AS
  'Formal source qualification must start at genesis (height 0).';
ASSERT end_height >= start_height AS
  'end_height must be greater than or equal to start_height.';

WITH
  selected_blocks AS (
    SELECT
      hash,
      number,
      timestamp,
      transaction_count
    FROM `bigquery-public-data.crypto_bitcoin.blocks`
    WHERE number BETWEEN start_height AND end_height
  ),
  selected_transactions AS (
    SELECT
      hash,
      block_hash,
      block_number,
      `index` AS transaction_index,
      is_coinbase,
      inputs,
      outputs
    FROM `bigquery-public-data.crypto_bitcoin.transactions`
    WHERE block_number BETWEEN start_height AND end_height
  ),
  child_inputs AS (
    SELECT
      transaction.hash AS child_transaction_hash,
      transaction.block_hash AS child_block_hash,
      transaction.block_number AS child_block_number,
      transaction.transaction_index AS child_transaction_index,
      input.index AS input_index,
      input.spent_transaction_hash,
      input.spent_output_index
    FROM selected_transactions AS transaction
    CROSS JOIN UNNEST(transaction.inputs) AS input
    WHERE NOT transaction.is_coinbase
  ),
  parent_outputs AS (
    SELECT
      transaction.hash AS parent_transaction_hash,
      transaction.block_hash AS parent_block_hash,
      transaction.block_number AS parent_block_number,
      transaction.transaction_index AS parent_transaction_index,
      output.index AS output_index,
      output.script_hex,
      output.value
    FROM selected_transactions AS transaction
    CROSS JOIN UNNEST(transaction.outputs) AS output
  ),
  -- BIP30 permits historical duplicate txids in narrowly defined cases. Resolve
  -- an input to the latest strictly earlier tx position, while reporting how
  -- often more than one historical candidate existed. A tie at the latest
  -- position remains a required failure because it indicates duplicate rows.
  parent_candidates AS (
    SELECT
      child.child_transaction_hash,
      child.child_block_hash,
      child.child_transaction_index,
      child.input_index,
      parent.parent_transaction_hash,
      COUNT(parent.parent_transaction_hash) OVER (
        PARTITION BY
          child.child_block_hash,
          child.child_transaction_index,
          child.input_index
      ) AS historical_parent_match_count,
      DENSE_RANK() OVER (
        PARTITION BY
          child.child_block_hash,
          child.child_transaction_index,
          child.input_index
        ORDER BY
          parent.parent_block_number DESC,
          parent.parent_transaction_index DESC
      ) AS parent_position_rank
    FROM child_inputs AS child
    LEFT JOIN parent_outputs AS parent
      ON child.spent_transaction_hash = parent.parent_transaction_hash
      AND child.spent_output_index = parent.output_index
      AND (
        parent.parent_block_number < child.child_block_number
        OR (
          parent.parent_block_number = child.child_block_number
          AND parent.parent_transaction_index < child.child_transaction_index
        )
      )
  ),
  parent_match_counts AS (
    SELECT
      child_transaction_hash,
      child_block_hash,
      child_transaction_index,
      input_index,
      MAX(historical_parent_match_count) AS historical_parent_match_count,
      COUNTIF(
        parent_position_rank = 1 AND parent_transaction_hash IS NOT NULL
      ) AS nearest_parent_position_count
    FROM parent_candidates
    GROUP BY
      child_transaction_hash,
      child_block_hash,
      child_transaction_index,
      input_index
  ),
  metrics AS (
    SELECT
      'missing_block_height' AS check_name,
      end_height - start_height + 1 - COUNT(DISTINCT number) AS observed_count,
      0 AS expected_count
    FROM selected_blocks

    UNION ALL

    SELECT
      'duplicate_block_height',
      COUNT(*) - COUNT(DISTINCT number),
      0
    FROM selected_blocks

    UNION ALL

    SELECT
      'duplicate_block_hash',
      COUNT(*) - COUNT(DISTINCT hash),
      0
    FROM selected_blocks

    UNION ALL

    SELECT
      'transaction_without_exact_block_match',
      COUNTIF(block_match_count != 1),
      0
    FROM (
      SELECT
        transaction.hash,
        transaction.block_hash,
        transaction.block_number,
        transaction.transaction_index,
        COUNT(block.hash) AS block_match_count
      FROM selected_transactions AS transaction
      LEFT JOIN selected_blocks AS block
        ON transaction.block_hash = block.hash
        AND transaction.block_number = block.number
      GROUP BY
        transaction.hash,
        transaction.block_hash,
        transaction.block_number,
        transaction.transaction_index
    )

    UNION ALL

    SELECT
      'block_transaction_count_mismatch',
      COUNTIF(block.transaction_count != IFNULL(transaction.actual_transaction_count, 0)),
      0
    FROM selected_blocks AS block
    LEFT JOIN (
      SELECT block_hash, block_number, COUNT(*) AS actual_transaction_count
      FROM selected_transactions
      GROUP BY block_hash, block_number
    ) AS transaction
      ON block.hash = transaction.block_hash
      AND block.number = transaction.block_number

    UNION ALL

    SELECT
      'block_coinbase_count_mismatch',
      COUNTIF(IFNULL(transaction.coinbase_count, 0) != 1),
      0
    FROM selected_blocks AS block
    LEFT JOIN (
      SELECT block_hash, block_number, COUNTIF(is_coinbase) AS coinbase_count
      FROM selected_transactions
      GROUP BY block_hash, block_number
    ) AS transaction
      ON block.hash = transaction.block_hash
      AND block.number = transaction.block_number

    UNION ALL

    SELECT
      'coinbase_position_mismatch',
      COUNTIF(is_coinbase AND transaction_index != 0),
      0
    FROM selected_transactions

    UNION ALL

    SELECT
      'noncoinbase_without_input',
      COUNTIF(NOT is_coinbase AND IFNULL(ARRAY_LENGTH(inputs), 0) = 0),
      0
    FROM selected_transactions

    UNION ALL

    SELECT
      'transaction_without_output',
      COUNTIF(IFNULL(ARRAY_LENGTH(outputs), 0) = 0),
      0
    FROM selected_transactions

    UNION ALL

    SELECT
      'duplicate_transaction_position',
      COUNT(*) - COUNT(DISTINCT CONCAT(block_hash, ':', CAST(transaction_index AS STRING))),
      0
    FROM selected_transactions

    UNION ALL

    SELECT
      'negative_transaction_position',
      COUNTIF(transaction_index < 0),
      0
    FROM selected_transactions

    UNION ALL

    SELECT
      'duplicate_input_position',
      COUNT(*) - COUNT(
        DISTINCT CONCAT(
          child_block_hash,
          ':',
          CAST(child_transaction_index AS STRING),
          ':',
          CAST(input_index AS STRING)
        )
      ),
      0
    FROM child_inputs

    UNION ALL

    SELECT
      'negative_input_or_prevout_position',
      COUNTIF(input_index < 0 OR spent_output_index < 0),
      0
    FROM child_inputs

    UNION ALL

    SELECT
      'missing_input_position_or_parent_key',
      COUNTIF(
        input_index IS NULL
        OR spent_transaction_hash IS NULL
        OR spent_output_index IS NULL
      ),
      0
    FROM child_inputs

    UNION ALL

    SELECT
      'duplicate_output_position',
      COUNT(*) - COUNT(
        DISTINCT CONCAT(
          parent_block_hash,
          ':',
          CAST(parent_transaction_index AS STRING),
          ':',
          CAST(output_index AS STRING)
        )
      ),
      0
    FROM parent_outputs

    UNION ALL

    SELECT
      'missing_output_position',
      COUNTIF(output_index IS NULL),
      0
    FROM parent_outputs

    UNION ALL

    SELECT
      'negative_output_position',
      COUNTIF(output_index < 0),
      0
    FROM parent_outputs

    UNION ALL

    SELECT
      'missing_or_negative_output_value',
      COUNTIF(value IS NULL OR value < 0),
      0
    FROM parent_outputs

    UNION ALL

    SELECT
      'missing_parent_outpoint',
      COUNTIF(historical_parent_match_count = 0),
      0
    FROM parent_match_counts

    UNION ALL

    SELECT
      'duplicate_nearest_parent_position',
      COUNTIF(nearest_parent_position_count > 1),
      0
    FROM parent_match_counts

    UNION ALL

    SELECT
      'reused_parent_outpoint_history',
      COUNTIF(historical_parent_match_count > 1),
      0
    FROM parent_match_counts

    UNION ALL

    SELECT
      'missing_output_script',
      COUNTIF(script_hex IS NULL),
      0
    FROM parent_outputs

    UNION ALL

    SELECT
      'invalid_output_script_hex',
      COUNTIF(
        script_hex IS NOT NULL
        AND (
          MOD(LENGTH(script_hex), 2) != 0
          OR NOT REGEXP_CONTAINS(script_hex, r'^[0-9A-Fa-f]*$')
        )
      ),
      0
    FROM parent_outputs
  )
SELECT
  check_name,
  observed_count,
  expected_count,
  CASE
    WHEN check_name = 'reused_parent_outpoint_history' THEN 'diagnostic'
    WHEN observed_count = expected_count THEN 'pass'
    ELSE 'fail'
  END AS status
FROM metrics
ORDER BY check_name;

-- A successful BigQuery job is not a successful qualification. Every row
-- except reused_parent_outpoint_history must have status='pass'; the diagnostic
-- count and any exception resolution must be recorded in the manifest.

-- Save this result separately. The selected tip hash must also be checked
-- against an independent Bitcoin node or explorer at the recorded audit time.
SELECT
  number AS selected_tip_height,
  hash AS selected_tip_hash,
  timestamp AS selected_tip_timestamp
FROM `bigquery-public-data.crypto_bitcoin.blocks`
WHERE number = end_height
ORDER BY hash;
