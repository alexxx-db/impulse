"""Configuration for the query engine.

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
"""

import json
from enum import Enum, StrEnum

from pydantic import BaseModel, model_validator


class RawEncoder(StrEnum):
    """Encoder used to convert RAW point data into intervals for solving.

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
    """

    RLE = "RLE"
    INTERVAL = "INTERVAL"


class DataType(StrEnum):
    RAW = "RAW"
    RLE = "RLE"


class Solvers(Enum):
    """
    Enumeration of available solver types for the query engine.

    ``DEFAULT_SOLVER`` is the single, unified solver. ``DELTA_SOLVER`` and
    ``KEY_VALUE_STORE_SOLVER`` are **deprecated aliases** kept so that existing
    report configs continue to deserialize; both now resolve to the same
    ``DefaultSolver``. They will be removed in a future release.

    Attributes
    ----------
    DEFAULT_SOLVER : str
    DELTA_SOLVER : str
        Deprecated alias for ``DEFAULT_SOLVER``.
    KEY_VALUE_STORE_SOLVER : str
        Deprecated alias for ``DEFAULT_SOLVER``.
    """

    DEFAULT_SOLVER = "DefaultSolver"
    DELTA_SOLVER = "DeltaSolver"
    KEY_VALUE_STORE_SOLVER = "KeyValueStoreSolver"


class TableConfig(BaseModel):
    """Per-table configuration for column renaming and equality filters.

    Attributes
    ----------
    column_name_mapping : dict[str, str]
        Mapping from physical column names on the table to internal
        names used by the solver.  An empty dict means no renaming
        (physical names already match internal names).
    filters : dict[str, str]
        Equality filters applied to the table **after** column renaming.
        Keys are internal column names; values are the literal values
        to match.
    """

    column_name_mapping: dict[str, str] = {}
    filters: dict[str, str] = {}


class JoinKey(BaseModel):
    """A single column pair in the ``channel_mapping`` → ``channel_metrics`` join.

    Used by :class:`ChannelMappingConfig.join_keys` to override the default
    alias-resolution composite key.

    Both fields reference column names **after** ``column_name_mapping`` has
    been applied on the respective table; the two sides are independent, so
    a column may appear under different names on the two tables.

    Attributes
    ----------
    mapping_col : str
        Column name on ``channel_mapping`` after its ``column_name_mapping``
        has been applied.
    metrics_col : str
        Column name on ``channel_metrics`` after its ``column_name_mapping``
        has been applied.
    """

    mapping_col: str
    metrics_col: str


class ChannelMappingConfig(TableConfig):
    """``TableConfig`` plus an optional alias-resolution join-key spec.

    Attributes
    ----------
    join_keys : list[JoinKey] or None
        Custom composite key for the ``channel_mapping`` → ``channel_metrics``
        join performed by ``DefaultSolver.filter_aliased_channel_metrics``.
        When ``None`` (the default), the solver uses the backward-compatible
        pair ``[(source_channel, channel_name), (data_key, data_key)]``
        sourced from :class:`SolverConfig` internal-name properties.
        Provide a custom list to change the join arity or column choice
        (e.g. a single-column join when ``data_key`` is not part of the
        channel identity in your silver layout).
    """

    join_keys: list[JoinKey] | None = None


class SolverConfig(BaseModel):
    """Per-table configuration for solver column name mappings and filters.

    The framework uses a fixed set of internal column names (e.g.
    ``container_id``, ``channel_id``, ``tstart``, ``tend``, ``value``).
    When a silver-layer table uses different physical column names, the
    per-table ``column_name_mapping`` renames them to the internal names
    so that solver code can always reference the same constants.

    Attributes
    ----------
    project_id : str or None
        Optional project identifier applied as a filter on relevant tables
        (container_tags, channel_mapping) by solvers that support it.
    container_tags : TableConfig
        Column mappings and filters for the container tags (narrow/EAV) table.
    container_metrics : TableConfig
        Column mappings and filters for the container metrics table.
    channel_tags : TableConfig
        Column mappings and filters for the channel tags table.
    channel_metrics : TableConfig
        Column mappings and filters for the channel metrics table.
    channel_mapping : ChannelMappingConfig
        Column mappings, filters, and the alias-resolution ``join_keys``
        override for the channel mapping (alias) table.
    channels : TableConfig
        Column mappings and filters for the channel data table.
    unit_conversion : TableConfig
        Column mappings and filters for the unit conversion table.
    """

    project_id: str | None = None

    container_tags: TableConfig = TableConfig()
    container_metrics: TableConfig = TableConfig()
    channel_tags: TableConfig = TableConfig()
    channel_metrics: TableConfig = TableConfig()
    channel_mapping: ChannelMappingConfig = ChannelMappingConfig()
    channels: TableConfig = TableConfig()
    unit_conversion: TableConfig = TableConfig()

    # ------------------------------------------------------------------
    # Class methods
    # ------------------------------------------------------------------

    @classmethod
    def from_json(cls, json_path: str) -> "SolverConfig":
        """
        Load a SolverConfig from a JSON file.

        Parameters
        ----------
        json_path : str
            Path to the JSON configuration file.

        Returns
        -------
        SolverConfig
            A new SolverConfig instance populated from the file.
        """
        with open(json_path) as f:
            data = json.load(f)
        return cls.model_validate(data)

    @classmethod
    def from_dict(cls, data: dict) -> "SolverConfig":
        """
        Create a SolverConfig from a dictionary.

        This is a convenience alias for ``model_validate(data)``.

        Parameters
        ----------
        data : dict
            Dictionary with configuration keys.

        Returns
        -------
        SolverConfig
            A new SolverConfig instance populated from *data*.
        """
        return cls.model_validate(data)

    # ------------------------------------------------------------------
    # Framework-internal column names (constants)
    # ------------------------------------------------------------------

    @property
    def container_id_col(self) -> str:
        """Internal column name for the container identifier."""
        return "container_id"

    @property
    def channel_id_col(self) -> str:
        """Internal column name for the channel identifier."""
        return "channel_id"

    @property
    def channel_id_cols(self) -> list[str]:
        """Composite key ``[container_id, channel_id]``."""
        return [self.container_id_col, self.channel_id_col]

    @property
    def tstart_col(self) -> str:
        """Internal column name for the start timestamp."""
        return "tstart"

    @property
    def tend_col(self) -> str:
        """Internal column name for the end timestamp."""
        return "tend"

    @property
    def start_ts_col(self) -> str:
        """Internal column name for the measurement-start epoch timestamp on container_metrics."""
        return "start_ts"

    @property
    def stop_ts_col(self) -> str:
        """Internal column name for the measurement-stop epoch timestamp on container_metrics."""
        return "stop_ts"

    @property
    def value_col(self) -> str:
        """Internal column name for the signal value on the channels table."""
        return "value"

    @property
    def tag_key_col(self) -> str:
        """Internal column name for the attribute key on the container_tags (EAV) table."""
        return "key"

    @property
    def tag_value_col(self) -> str:
        """Internal column name for the attribute value on the container_tags (EAV) table."""
        return "value"

    @property
    def alias_priority_col(self) -> str:
        """Internal column name for the alias priority on the channel_mapping table."""
        return "priority"

    @property
    def source_channel_col(self) -> str:
        """Internal column name for the source-channel identifier on the channel_mapping table."""
        return "source_channel"

    @property
    def data_key_col(self) -> str:
        """Internal column name for the data-key identifier.

        Default present on both ``channel_mapping`` and ``channel_metrics``;
        used by the default :meth:`effective_alias_join_keys` for both sides.
        Layouts where the two tables carry the data-key column under different
        physical names can either rename both to ``"data_key"`` via per-table
        ``column_name_mapping`` or override
        :attr:`ChannelMappingConfig.join_keys` with explicit
        ``mapping_col`` / ``metrics_col`` values.
        """
        return "data_key"

    @property
    def channel_alias_col(self) -> str:
        """Internal column name for the alias identifier on the channel_mapping table.

        Referenced by the dedup window in
        :meth:`DefaultSolver.filter_aliased_channel_metrics` and is the
        conventional kwarg name passed to
        :meth:`QueryBuilder.channel_with_alias` (e.g.
        ``channel_with_alias(channel_alias="vehicle_speed")``).  The kwarg name
        must match the column name as seen by the solver after
        ``column_name_mapping`` is applied.
        """
        return "channel_alias"

    @property
    def channel_name_col(self) -> str:
        """Internal column name for the channel-name identifier on the channel_metrics table."""
        return "channel_name"

    @property
    def project_id_col(self) -> str:
        """Internal column name for the project identifier."""
        return "project_id"

    @property
    def parent_id_col(self) -> str:
        """Internal column name for the parent/scope identifier."""
        return "parent_id"

    @property
    def conversion_factor_col(self) -> str:
        """Internal column name for the conversion factor on the unit_conversion table.

        Also used as the column that carries the per-channel combined factor
        downstream from :meth:`DefaultSolver._compute_conversion_factors`
        into the grouped-map UDF.
        """
        return "conversion_factor"

    @property
    def source_unit_col(self) -> str:
        """Internal column name for the source unit on the channel_mapping table."""
        return "source_unit"

    @property
    def target_unit_col(self) -> str:
        """Internal column name for the target unit on the channel_mapping table."""
        return "target_unit"

    @property
    def unit_col(self) -> str:
        """Internal column name for the unit identifier.

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
        """
        return "unit"

    @property
    def group_id_col(self) -> str:
        """Internal column name for the unit group id on the unit_conversion table."""
        return "group_id"

    @property
    def timestamp_col(self) -> str:
        """Internal column name for the timestamp on the channels table for raw encoded channel data."""
        return "timestamp"

    @property
    def is_plausible_col(self) -> str:
        """Internal column name for the plausibility flag on the channels table for raw encoded channel data."""
        return "is_plausible"

    @property
    def effective_alias_join_keys(self) -> list[tuple[str, str]]:
        """Return the resolved alias-resolution join keys as ``(mapping_col, metrics_col)`` tuples.

        Falls back to the default composite key
        ``[(source_channel_col, channel_name_col), (data_key_col, data_key_col)]``
        when :attr:`ChannelMappingConfig.join_keys` is ``None``.  Otherwise
        returns the configured list.

        Both members of each tuple are column names **after**
        ``column_name_mapping`` has been applied on the respective table.
        """
        if self.channel_mapping.join_keys is None:
            return [
                (self.source_channel_col, self.channel_name_col),
                (self.data_key_col, self.data_key_col),
            ]
        return [(jk.mapping_col, jk.metrics_col) for jk in self.channel_mapping.join_keys]

    @property
    def col_map(self) -> dict[str, str]:
        """Short-key → internal-column-name mapping for UDFs and caches."""
        return {
            "cid": self.container_id_col,
            "ch": self.channel_id_col,
            "ts": self.tstart_col,
            "te": self.tend_col,
            "val": self.value_col,
            "conv": self.conversion_factor_col,
        }


class QueryEngineConfig(BaseModel):
    """
    Configuration for the query engine solver.

    Parameters
    ----------
    solver : Solvers, default=Solvers.DEFAULT_SOLVER
        The solver type to use for query execution.
    raw_encoder : RawEncoder, optional, default=None
        Encoder used to convert RAW point data into intervals.  ``RLE``
        collapses consecutive equal-valued samples into runs; ``INTERVAL``
        only derives ``tend`` and drops exact duplicates.  Only takes effect
        when ``data_type=RAW``; ignored for RLE input.  When omitted and
        ``data_type=RAW``, it is resolved to ``RLE`` at validation time;
        for RLE input the field stays ``None`` and is never consulted.
    solver_config : SolverConfig, optional
        Per-table column name mappings and filter configuration for
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

    Notes
    -----
    The default solver is ``Solvers.DEFAULT_SOLVER``.  It selects channels
    from a narrow EAV ``channel_tags`` table when ``source.channel_tags_table``
    is configured, and otherwise directly from columns on ``channel_metrics``.
    It operates either with a narrow EAV ``container_tags`` table or in a
    wide-only data model when ``source.container_tags_table`` is not
    configured.  (``DELTA_SOLVER`` and ``KEY_VALUE_STORE_SOLVER`` are
    deprecated aliases that resolve to the same solver.)

    - RLE channel data must contain 'container_id', 'channel_id', 'tstart', 'tend', 'value' columns
    - RAW channel data must contain 'container_id', 'channel_id', 'timestamp', 'value' columns
    """

    solver: Solvers = Solvers.DEFAULT_SOLVER
    data_type: DataType = DataType.RLE
    drop_implausible_data: bool = False
    raw_encoder: RawEncoder | None = None
    solver_config: SolverConfig | None = None
    batch_size: int = 500

    @model_validator(mode="after")
    def validate_drop_implausible_data_requires_raw(self):
        """`drop_implausible_data=True` currently only takes effect with RAW data.

        The filter is applied inside the RAW -> interval conversion path by the
        selected ``raw_encoder`` (``RleEncoder`` / ``IntervalEncoder``).  RLE
        input short-circuits that path and the flag is silently ignored, so we
        reject the combination at config validation time.
        """
        if self.drop_implausible_data and self.data_type is not DataType.RAW:
            raise ValueError(
                "drop_implausible_data=True requires data_type=RAW. "
                "The implausible-data filter is only applied during the RAW -> RLE "
                "conversion path; RLE input is passed through unchanged."
            )
        return self

    @model_validator(mode="after")
    def default_raw_encoder_for_raw_data(self):
        """When ``data_type=RAW`` and ``raw_encoder`` is unset, default to RLE."""
        if self.data_type is DataType.RAW and self.raw_encoder is None:
            self.raw_encoder = RawEncoder.RLE
        return self
