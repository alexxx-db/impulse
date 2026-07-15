---
sidebar_label: rle_encoder
title: impulse_query_engine.analyze.query.solvers.utils.rle_encoder
---

## RleEncoder

```python
class RleEncoder()
```

Run-length encode RAW point samples into ``[tstart, tend)`` intervals.

Within each ``(container_id, channel_id)`` the samples are ordered by
timestamp and a new interval starts whenever ``value`` changes.  Each
resulting **run** -- one or more consecutive samples sharing the same
value -- becomes a single interval spanning from the run's first
timestamp (``tstart``) to the timestamp at which the value next changes
(``tend``).  This removes redundant points from signals that stay
constant over time.


#### \_\_init\_\_

```python
def __init__(config: SolverConfig | None = None,
             drop_implausible_data_points: bool = False)
```

Initialize the RleEncoder.

**Arguments**:

- `config` (`SolverConfig`): Solver configuration providing the internal column names.
- `drop_implausible_data_points` (`bool`): Whether to drop implausible data points before encoding.  If True, rows
where ``is_plausible`` is not True are removed.  Default is False.

#### prepare\_channels\_df

```python
def prepare_channels_df(df: DataFrame) -> DataFrame
```

Run-length encode a raw channels DataFrame.

Consecutive rows within the same container/channel that carry an identical
``value`` are merged into one interval spanning from the first timestamp of
the interval (``tstart``) to the timestamp at which the value next changes
(``tend``).

**Arguments**:

- `df` (`pyspark.sql.DataFrame`): Channel data.  Must contain the configured container id and channel id
columns, ``value`` and the timestamp column (``timestamp_col_name``).

**Returns**:

`pyspark.sql.DataFrame`: DataFrame with the container id and channel id columns, ``tstart``,
``tend`` and ``value`` -- one row per constant-value interval.

