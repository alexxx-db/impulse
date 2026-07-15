---
sidebar_label: interval_encoder
title: impulse_query_engine.analyze.query.solvers.utils.interval_encoder
---

## IntervalEncoder

```python
class IntervalEncoder()
```

Convert RAW point samples into ``[tstart, tend)`` intervals, keeping every sample.

Within each ``(container_id, channel_id)`` the samples are ordered by
timestamp and each sample's ``tend`` is set to the *next* sample's
timestamp (via a ``LEAD`` window function).  The last sample has no
successor, so its ``tend`` coalesces to its own timestamp -- a
zero-length interval that carries no duration.

Only **duplicate points** are dropped: a row is a duplicate when both its
``value`` and ``timestamp`` equal the next row's (compared with
``eqNullSafe``, so two ``NULL`` values count as equal).  Every other
sample is kept as its own interval, so the original timestamps are
preserved.  Contrast with


#### \_\_init\_\_

```python
def __init__(config: SolverConfig | None = None,
             drop_implausible_data_points: bool = False)
```

Initialize the IntervalEncoder.

**Arguments**:

- `config` (`SolverConfig`): Solver configuration providing the internal column names.
- `drop_implausible_data_points` (`bool`): Whether to drop implausible data points before returning.  If True, data points where ``is_plausible``
is not True will be removed.  Default is False.

#### prepare\_channels\_df

```python
def prepare_channels_df(df: DataFrame) -> DataFrame
```

Normalize a channels DataFrame to interval format.

If the DataFrame already contains a ``tend`` column it is returned
unchanged.  Otherwise ``tend`` is derived from ``timestamp`` using
the ``LEAD`` window function and the column is renamed to ``tstart``.

**Arguments**:

- `df` (`pyspark.sql.DataFrame`): Channel data.  Must contain ``container_id``, ``channel_id``,
``value`` and either ``tend`` (already RLE) or ``timestamp``
(raw point data).

**Raises**:

- `ValueError`: If the DataFrame has neither ``tend`` nor ``timestamp``.

**Returns**:

`pyspark.sql.DataFrame`: DataFrame with columns ``container_id``, ``channel_id``,
``tstart``, ``tend``, ``value``.

