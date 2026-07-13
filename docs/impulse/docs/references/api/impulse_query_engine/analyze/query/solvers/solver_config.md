---
sidebar_label: solver_config
title: impulse_query_engine.analyze.query.solvers.solver_config
---

Configuration for the query engine.

Provides the Pydantic models that configure the query-engine solvers:

- :class:`QueryEngineConfig` — the top-level engine configuration: which solver to
  use, the input data format (:class:`DataType`: RLE intervals vs. RAW point
  samples), how RAW data is converted to intervals (:class:`RawEncoder`),
  implausible-data filtering, batching, and the embedded
  :class:`SolverConfig`.
- :class:`SolverConfig` — per-table column-name mappings and equality
  filters.  Each input table has its own :class:`TableConfig` section with an
  optional ``column_name_mapping`` (physical column → internal name) and
  ``filters`` (internal column → equality value).  Solvers apply the mapping
  when reading a table; all subsequent processing uses the framework-internal
  column names exposed as properties on :class:`SolverConfig`.

``impulse_reporting`` composes :class:`QueryEngineConfig` into its top-level
``ImpulseConfig`` (and re-exports these names from
``impulse_reporting.config.config_parser`` for backward compatibility), so
the user-facing JSON schema is defined here while the query engine remains
usable standalone, without importing the reporting layer.


## RawEncoder

```python
class RawEncoder(StrEnum)
```

Encoder used to convert RAW point data into intervals for solving.

Only relevant when the query engine operates on RAW (point) data; RLE input
is passed through unchanged regardless of this setting.

Values
------
RLE
    Run-length encode: collapse consecutive samples that share the same
    ``value`` within a container/channel into a single interval (see
    :class:`~impulse_query_engine.analyze.query.solvers.utils.rle_encoder.RleEncoder`).
INTERVAL
    Derive ``tend`` from the following sample's timestamp and drop exact
    duplicate points, *without* merging equal-valued runs (see
    :class:`~impulse_query_engine.analyze.query.solvers.utils.interval_encoder.IntervalEncoder`).


## Solvers

```python
class Solvers(Enum)
```

Enumeration of available solver types for the query engine.

``DEFAULT_SOLVER`` is the single, unified solver. ``DELTA_SOLVER`` and
``KEY_VALUE_STORE_SOLVER`` are **deprecated aliases** kept so that existing
report configs continue to deserialize; both now resolve to the same
``DefaultSolver``. They will be removed in a future release.

**Arguments**:

- `DEFAULT_SOLVER` (`str`): None
- `DELTA_SOLVER` (`str`): Deprecated alias for ``DEFAULT_SOLVER``.
- `KEY_VALUE_STORE_SOLVER` (`str`): Deprecated alias for ``DEFAULT_SOLVER``.

## TableConfig

```python
class TableConfig(BaseModel)
```

Per-table configuration for column renaming and equality filters.

**Arguments**:

- `column_name_mapping` (`dict[str, str]`): Mapping from physical column names on the table to internal
names used by the solver.  An empty dict means no renaming
(physical names already match internal names).
- `filters` (`dict[str, str]`): Equality filters applied to the table **after** column renaming.
Keys are internal column names; values are the literal values
to match.

## JoinKey

```python
class JoinKey(BaseModel)
```

A single column pair in the ``channel_mapping`` → ``channel_metrics`` join.

Used by :class:`ChannelMappingConfig.join_keys` to override the default
alias-resolution composite key.

Both fields reference column names **after** ``column_name_mapping`` has
been applied on the respective table; the two sides are independent, so
a column may appear under different names on the two tables.

**Arguments**:

- `mapping_col` (`str`): Column name on ``channel_mapping`` after its ``column_name_mapping``
has been applied.
- `metrics_col` (`str`): Column name on ``channel_metrics`` after its ``column_name_mapping``
has been applied.

## ChannelMappingConfig

```python
class ChannelMappingConfig(TableConfig)
```

``TableConfig`` plus an optional alias-resolution join-key spec.

**Arguments**:

- `join_keys` (`list[JoinKey] or None`): Custom composite key for the ``channel_mapping`` → ``channel_metrics``
join performed by ``DefaultSolver.filter_aliased_channel_metrics``.
When ``None`` (the default), the solver uses the backward-compatible
pair ``[(source_channel, channel_name), (data_key, data_key)]``
sourced from :class:`SolverConfig` internal-name properties.
Provide a custom list to change the join arity or column choice
(e.g. a single-column join when ``data_key`` is not part of the
channel identity in your silver layout).

## SolverConfig

```python
class SolverConfig(BaseModel)
```

Per-table configuration for solver column name mappings and filters.

The framework uses a fixed set of internal column names (e.g.
``container_id``, ``channel_id``, ``tstart``, ``tend``, ``value``).
When a silver-layer table uses different physical column names, the
per-table ``column_name_mapping`` renames them to the internal names
so that solver code can always reference the same constants.

**Arguments**:

- `project_id` (`str or None`): Optional project identifier applied as a filter on relevant tables
(container_tags, channel_mapping) by solvers that support it.
- `container_tags` (`TableConfig`): Column mappings and filters for the container tags (narrow/EAV) table.
- `container_metrics` (`TableConfig`): Column mappings and filters for the container metrics table.
- `channel_tags` (`TableConfig`): Column mappings and filters for the channel tags table.
- `channel_metrics` (`TableConfig`): Column mappings and filters for the channel metrics table.
- `channel_mapping` (`ChannelMappingConfig`): Column mappings, filters, and the alias-resolution ``join_keys``
override for the channel mapping (alias) table.
- `channels` (`TableConfig`): Column mappings and filters for the channel data table.
- `unit_conversion` (`TableConfig`): Column mappings and filters for the unit conversion table.

#### from\_json

```python
def from_json(cls, json_path: str) -> "SolverConfig"
```

Load a SolverConfig from a JSON file.

**Arguments**:

- `json_path` (`str`): Path to the JSON configuration file.

**Returns**:

`SolverConfig`: A new SolverConfig instance populated from the file.

#### from\_dict

```python
def from_dict(cls, data: dict) -> "SolverConfig"
```

Create a SolverConfig from a dictionary.

This is a convenience alias for ``model_validate(data)``.

**Arguments**:

- `data` (`dict`): Dictionary with configuration keys.

**Returns**:

`SolverConfig`: A new SolverConfig instance populated from *data*.

#### container\_id\_col

```python
def container_id_col() -> str
```

Internal column name for the container identifier.


#### channel\_id\_col

```python
def channel_id_col() -> str
```

Internal column name for the channel identifier.


#### channel\_id\_cols

```python
def channel_id_cols() -> list[str]
```

Composite key ``[container_id, channel_id]``.


#### tstart\_col

```python
def tstart_col() -> str
```

Internal column name for the start timestamp.


#### tend\_col

```python
def tend_col() -> str
```

Internal column name for the end timestamp.


#### start\_ts\_col

```python
def start_ts_col() -> str
```

Internal column name for the measurement-start epoch timestamp on container_metrics.


#### stop\_ts\_col

```python
def stop_ts_col() -> str
```

Internal column name for the measurement-stop epoch timestamp on container_metrics.


#### value\_col

```python
def value_col() -> str
```

Internal column name for the signal value on the channels table.


#### tag\_key\_col

```python
def tag_key_col() -> str
```

Internal column name for the attribute key on the container_tags (EAV) table.


#### tag\_value\_col

```python
def tag_value_col() -> str
```

Internal column name for the attribute value on the container_tags (EAV) table.


#### alias\_priority\_col

```python
def alias_priority_col() -> str
```

Internal column name for the alias priority on the channel_mapping table.


#### source\_channel\_col

```python
def source_channel_col() -> str
```

Internal column name for the source-channel identifier on the channel_mapping table.


#### data\_key\_col

```python
def data_key_col() -> str
```

Internal column name for the data-key identifier.

Default present on both ``channel_mapping`` and ``channel_metrics``;
used by the default :meth:`effective_alias_join_keys` for both sides.
Layouts where the two tables carry the data-key column under different
physical names can either rename both to ``"data_key"`` via per-table
``column_name_mapping`` or override


#### channel\_alias\_col

```python
def channel_alias_col() -> str
```

Internal column name for the alias identifier on the channel_mapping table.

Referenced by the dedup window in


#### channel\_name\_col

```python
def channel_name_col() -> str
```

Internal column name for the channel-name identifier on the channel_metrics table.


#### project\_id\_col

```python
def project_id_col() -> str
```

Internal column name for the project identifier.


#### parent\_id\_col

```python
def parent_id_col() -> str
```

Internal column name for the parent/scope identifier.


#### conversion\_factor\_col

```python
def conversion_factor_col() -> str
```

Internal column name for the conversion factor on the unit_conversion table.

Also used as the column that carries the per-channel combined factor
downstream from :meth:`DefaultSolver._compute_conversion_factors`
into the grouped-map UDF.


#### source\_unit\_col

```python
def source_unit_col() -> str
```

Internal column name for the source unit on the channel_mapping table.


#### target\_unit\_col

```python
def target_unit_col() -> str
```

Internal column name for the target unit on the channel_mapping table.


#### unit\_col

```python
def unit_col() -> str
```

Internal column name for the unit identifier.

Used in two places that happen to share the same default name:

- On the ``unit_conversion`` table, as the key joined against
  ``channel_mapping.source_unit`` / ``target_unit`` to look up a
  conversion factor.
- On the ``channel_metrics`` table (optional), as the authoritative
  physical unit of a channel.  When present, takes precedence over
  ``channel_mapping.source_unit`` for aliased reads via the
  :meth:`DefaultSolver.filter_aliased_channel_metrics`
  coalesce.

Users with different internal names per table can rename physical
columns to ``unit`` on each table independently via the per-table
``column_name_mapping``.


#### group\_id\_col

```python
def group_id_col() -> str
```

Internal column name for the unit group id on the unit_conversion table.


#### timestamp\_col

```python
def timestamp_col() -> str
```

Internal column name for the timestamp on the channels table for raw encoded channel data.


#### is\_plausible\_col

```python
def is_plausible_col() -> str
```

Internal column name for the plausibility flag on the channels table for raw encoded channel data.


#### effective\_alias\_join\_keys

```python
def effective_alias_join_keys() -> list[tuple[str, str]]
```

Return the resolved alias-resolution join keys as ``(mapping_col, metrics_col)`` tuples.

Falls back to the default composite key
``[(source_channel_col, channel_name_col), (data_key_col, data_key_col)]``
when :attr:`ChannelMappingConfig.join_keys` is ``None``.  Otherwise
returns the configured list.

Both members of each tuple are column names **after**
``column_name_mapping`` has been applied on the respective table.


#### col\_map

```python
def col_map() -> dict[str, str]
```

Short-key → internal-column-name mapping for UDFs and caches.


## QueryEngineConfig

```python
class QueryEngineConfig(BaseModel)
```

Configuration for the query engine solver.

**Arguments**:

- `solver` (`Solvers, default=Solvers.DEFAULT_SOLVER`): The solver type to use for query execution.
- `raw_encoder` (`RawEncoder, optional, default=None`): Encoder used to convert RAW point data into intervals.  ``RLE``
collapses consecutive equal-valued samples into runs; ``INTERVAL``
only derives ``tend`` and drops exact duplicates.  Only takes effect
when ``data_type=RAW``; ignored for RLE input.  When omitted and
``data_type=RAW``, it is resolved to ``RLE`` at validation time;
for RLE input the field stays ``None`` and is never consulted.
- `solver_config` (`SolverConfig`): Per-table column name mappings and filter configuration for
the solver.  Use this when your silver-layer tables use
non-default column names or when you need project/toolbox
scoping.  Key sub-fields:

- ``project_id`` (str): Top-level project filter value applied
  to container_tags, container_metrics, and channel_mapping
  tables when the corresponding columns exist after column
  renaming.
- Per-table sections (``container_tags``, ``container_metrics``,
  ``channel_mapping``, ``channels``, etc.) each with
  ``column_name_mapping`` and ``filters`` dicts.

When omitted, all default column names are used and no
project/toolbox filtering is applied.

#### validate\_drop\_implausible\_data\_requires\_raw

```python
def validate_drop_implausible_data_requires_raw()
```

`drop_implausible_data=True` currently only takes effect with RAW data.

The filter is applied inside the RAW -> interval conversion path by the
selected ``raw_encoder`` (``RleEncoder`` / ``IntervalEncoder``).  RLE
input short-circuits that path and the flag is silently ignored, so we
reject the combination at config validation time.


#### default\_raw\_encoder\_for\_raw\_data

```python
def default_raw_encoder_for_raw_data()
```

When ``data_type=RAW`` and ``raw_encoder`` is unset, default to RLE.


