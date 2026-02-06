"""
QueryLib Core Module
====================
Core functions for the Query Library notebook.
Provides initialization, status display, and error handling.

This module follows ADR-015: Each notebook has its own *_core.py module.

Architecture Requirements:
- UI framework: ipywidgets (ADR-007)
- Data access: PatstatClient only (NFR11)
- Error messages: User-friendly, no tracebacks (FR35, NFR7)
- Colors: EPO_COLORS palette (Phase 1)

Author: BMad
Version: 0.1.0
"""

from typing import Tuple, Optional, Any, List, Dict
from dataclasses import dataclass, field

# IPython and widgets for display
import ipywidgets as widgets
from IPython.display import display, HTML

# PATSTAT connection
from epo.tipdata.patstat import PatstatClient

# =============================================================================
# Module-level Connection State
# =============================================================================

patstat_client: Optional[PatstatClient] = None
db: Optional[Any] = None  # SQLAlchemy Session

# =============================================================================
# EPO Brand Colors (from existing tip4patlibs_core.py)
# =============================================================================

EPO_COLORS = {
    'primary_blue': '#003399',
    'secondary_blue': '#0055A5',
    'light_blue': '#66B3FF',
    'orange': '#FF6600',
    'green': '#009933',
    'red': '#C8102E',
    'gray': '#666666',
    'light_gray': '#F5F5F5',
    'error_bg': '#FFF5F5',  # Light red background for errors
}

# =============================================================================
# Module Exports
# =============================================================================

__all__ = [
    # Main entry point
    'initialize',
    'timed_query',
    # Connection management
    'init_patstat',
    'display_status',
    'display_error',
    'show_progress',
    'patstat_client',
    'db',
    'EPO_COLORS',
    # Query Registry (Story 1.2)
    'ParameterSpec',
    'QueryMetadata',
    'QueryRegistry',
    'QUERY_CATEGORIES',
    # Query Browser Widgets (Story 1.3)
    'QueryBrowser',
    'QueryPreview',
    'SQLViewer',
    'highlight_parameters',
    'create_query_browser',
    # Parameter Form (Story 1.4)
    'ParameterForm',
    'create_parameter_widget',
    'get_jurisdiction_options',
    'get_wipo_field_options',
    'VALIDATION_MESSAGES',
    # Query Execution (Story 1.5)
    'QueryExecutor',
    'ProgressIndicator',
    'substitute_parameters',
    'QueryTimeoutError',
    'TIMEOUT_SECONDS',
    # Results Display and Export (Story 1.6)
    'ResultsDisplay',
    'ResultsPanel',
    'format_number',
    'display_zero_results',
    'export_to_csv',
    'export_to_png',
    'copy_sql_to_clipboard',
]


# =============================================================================
# PATSTAT Connection Management
# =============================================================================

def init_patstat() -> Tuple[PatstatClient, Any]:
    """
    Initialize PATSTAT connection.

    Establishes connection to PATSTAT database via EPO's PatstatClient.
    Stores the client and ORM session in module-level variables for
    access by subsequent notebook cells.

    Returns:
        tuple: (PatstatClient, SQLAlchemy session) on success

    Raises:
        ConnectionError: If PATSTAT is unavailable

    Example:
        >>> client, session = init_patstat()
        >>> print(session)  # Access the session
    """
    global patstat_client, db
    try:
        patstat_client = PatstatClient(env='PROD')
        db = patstat_client.orm()
        return patstat_client, db
    except Exception as e:
        raise ConnectionError(f"Could not connect to PATSTAT: {e}") from e


# =============================================================================
# Status Display Helpers (FR34, FR35)
# =============================================================================

def display_status(message: str, success: bool = True) -> None:
    """
    Display status message with emoji indicator.

    Shows a styled status message with green checkmark (success) or
    red X (failure) emoji. Uses EPO brand colors for styling.

    Args:
        message: The status message to display
        success: True for success (green), False for failure (red)

    Example:
        >>> display_status("Connection established", success=True)
        >>> display_status("Query failed", success=False)
    """
    emoji = "✅" if success else "❌"
    color = EPO_COLORS['green'] if success else EPO_COLORS['red']

    html_content = f"""
    <div style="padding: 10px; border-left: 4px solid {color}; background-color: {EPO_COLORS['light_gray']}; margin: 5px 0;">
        <span style="font-size: 1.2em;">{emoji}</span>
        <span style="color: {color}; font-weight: bold; margin-left: 8px;">{message}</span>
    </div>
    """
    display(HTML(html_content))


def display_error(title: str, message: str, details: Optional[str] = None) -> None:
    """
    Display user-friendly error with optional technical details.

    Shows a red-styled error box with helpful message for users.
    Technical details are printed below for troubleshooting but
    kept separate from the user-facing message.

    Args:
        title: Short error title (e.g., "Connection Error")
        message: User-friendly description with suggested actions
        details: Optional technical details for debugging

    Example:
        >>> display_error(
        ...     "Connection Error",
        ...     "Unable to connect to PATSTAT. Please check your network.",
        ...     details="TimeoutError: Connection timed out after 30s"
        ... )
    """
    html_content = f"""
    <div style="color: {EPO_COLORS['red']}; padding: 15px; border: 1px solid {EPO_COLORS['red']};
                border-radius: 4px; background-color: {EPO_COLORS['error_bg']}; margin: 10px 0;">
        <b style="font-size: 1.1em;">❌ {title}</b><br><br>
        {message}
    </div>
    """
    display(HTML(html_content))

    # Technical details printed below for debugging (visible in notebook output)
    if details:
        print(f"\nTechnical details: {details}")


def show_progress(message: str = "Loading...") -> widgets.HTML:
    """
    Create and display a progress indicator.

    Returns the widget so caller can update its value when the
    operation completes.

    Args:
        message: Initial progress message (default: "Loading...")

    Returns:
        widgets.HTML: The progress widget for later updates

    Example:
        >>> progress = show_progress("Connecting to PATSTAT...")
        >>> # ... do work ...
        >>> progress.value = "✅ Connected!"
    """
    progress = widgets.HTML(
        value=f"""
        <div style="padding: 10px; background-color: {EPO_COLORS['light_gray']};
                    border-left: 4px solid {EPO_COLORS['primary_blue']};">
            <span style="font-size: 1.2em;">⏳</span>
            <span style="color: {EPO_COLORS['primary_blue']}; margin-left: 8px;">{message}</span>
        </div>
        """
    )
    display(progress)
    return progress


# =============================================================================
# Query Execution Helper
# =============================================================================

import time
import pandas as pd


def timed_query(sql: str) -> pd.DataFrame:
    """
    Execute a SQL query and return results as DataFrame with timing.

    Requires initialize() to be called first.

    Args:
        sql: SQL query string to execute against PATSTAT

    Returns:
        pandas.DataFrame with query results

    Raises:
        RuntimeError: If PATSTAT not initialized

    Example:
        >>> initialize()
        >>> df = timed_query("SELECT COUNT(*) FROM tls201_appln")
    """
    if patstat_client is None:
        raise RuntimeError("PATSTAT not initialized. Run initialize() first.")
    start = time.time()
    res = patstat_client.sql_query(sql, use_legacy_sql=False)
    elapsed = time.time() - start
    print(f"Query took {elapsed:.2f}s ({len(res)} rows)")
    return pd.DataFrame(res)


# =============================================================================
# Main Initialization Function
# =============================================================================

# Module-level query registry (set by initialize())
query_registry: Optional['QueryRegistry'] = None


def initialize() -> 'QueryRegistry':
    """
    Initialize the Query Library notebook.

    Connects to PATSTAT and loads the Query Registry.
    Displays progress and status messages.

    Returns:
        QueryRegistry: The initialized query registry

    Example:
        >>> from querylib_core import initialize, timed_query
        >>> registry = initialize()
        >>> query = registry.get_query("Q01")
        >>> df = timed_query(query.sql_template)

    Note:
        After calling initialize(), you can also use:
        - timed_query(sql) to execute queries
        - create_query_browser(registry) to display the browser widget
    """
    global patstat_client, db, query_registry

    # Show progress
    progress = show_progress("Connecting to PATSTAT...")

    try:
        # Initialize PATSTAT connection
        client, session = init_patstat()
        progress.value = ""  # Clear progress indicator
        display_status("PATSTAT connection established successfully!", success=True)

        # Initialize Query Registry
        query_registry = QueryRegistry()
        all_queries = query_registry.get_all_queries()
        categories = query_registry.get_categories()
        display_status(
            f"Query Registry loaded: {len(all_queries)} queries in {len(categories)} categories",
            success=True
        )

        return query_registry

    except Exception as e:
        progress.value = ""  # Clear progress indicator
        display_error(
            "Connection Error",
            "Unable to connect to PATSTAT. Please check your network connection and try again.",
            details=str(e)
        )
        return None


# =============================================================================
# Query Registry Data Structures (Story 1.2 - FR1, FR2, FR3)
# =============================================================================

@dataclass
class ParameterSpec:
    """
    Specification for a query parameter.

    Defines the metadata needed to render appropriate UI controls
    and validate parameter values.

    Attributes:
        name: Parameter name (used in SQL template as @name)
        type: Parameter type ('year', 'year_range', 'select', 'multiselect', 'text', 'slider')
        label: Human-readable label for UI
        default: Default value
        required: Whether parameter is required
        options: List of valid options (for select/multiselect types)
    """
    name: str
    type: str
    label: str
    default: Any
    required: bool = True
    options: Optional[List[Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "type": self.type,
            "label": self.label,
            "default": self.default,
            "required": self.required,
            "options": self.options,
        }


@dataclass
class QueryMetadata:
    """
    Complete metadata for a PATSTAT query.

    Contains all information needed to display, configure, and execute
    a query in the Query Library notebook.

    Attributes:
        id: Unique query identifier (e.g., 'Q01')
        title: Human-readable query title
        description: Detailed description of what the query does
        category: Query category (e.g., 'Regional', 'Trends')
        sql_template: SQL query with @parameter placeholders
        parameters: List of parameter specifications
        output_columns: Expected output column names
        tags: Stakeholder tags (e.g., ['PATLIB', 'BUSINESS'])
        explanation: Optional detailed explanation of methodology
        key_outputs: Optional list of key output descriptions
    """
    id: str
    title: str
    description: str
    category: str
    sql_template: str
    parameters: List[ParameterSpec]
    output_columns: List[str]
    tags: List[str]
    explanation: Optional[str] = None
    key_outputs: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "sql_template": self.sql_template,
            "parameters": [p.to_dict() for p in self.parameters],
            "output_columns": self.output_columns,
            "tags": self.tags,
            "explanation": self.explanation,
            "key_outputs": self.key_outputs,
        }


# =============================================================================
# Query Categories (Story 1.2 - AC2)
# =============================================================================

QUERY_CATEGORIES: Dict[str, Dict[str, str]] = {
    "Trends": {
        "description": "Time-series analysis, growth patterns, and historical trends",
        "icon": "📈",
    },
    "Competitors": {
        "description": "Competitor analysis, applicant rankings, and market landscape",
        "icon": "🏆",
    },
    "Regional": {
        "description": "Geographic analysis, country comparisons, and NUTS regions",
        "icon": "🌍",
    },
    "Technology": {
        "description": "IPC/CPC/WIPO field analysis and technology sector breakdown",
        "icon": "🔬",
    },
}


# =============================================================================
# Import queries from single source of truth: TIP_for_PATLIBs_QueryLib_queries.py
# =============================================================================

import sys
import os

try:
    from TIP_for_PATLIBs_QueryLib_queries import QUERIES as _RAW_QUERIES, STAKEHOLDERS
except ImportError:
    # Fallback: empty dict if queries file not found
    _RAW_QUERIES = {}
    STAKEHOLDERS = {}


# =============================================================================
# Query Registry (Story 1.2 - FR1, FR2, FR3)
# Loads queries from TIP_for_PATLIBs_QueryLib_queries.py (single source of truth)
# =============================================================================

class QueryRegistry:
    """
    Registry of all available PATSTAT queries.

    Loads queries from TIP_for_PATLIBs_QueryLib_queries.py which contains 42 queries
    with full metadata (title, description, parameters, sql_template, etc.).

    Provides methods to browse, search, and retrieve queries
    by ID, category, or keyword search.

    Example:
        >>> registry = QueryRegistry()
        >>> all_queries = registry.get_all_queries()
        >>> regional = registry.get_queries_by_category("Regional")
        >>> q01 = registry.get_query("Q01")
    """

    def __init__(self):
        """Initialize the query registry by loading from TIP_for_PATLIBs_QueryLib_queries.py."""
        self._queries: Dict[str, QueryMetadata] = {}
        self._load_queries_from_source()

    def _convert_parameter(self, name: str, param_def: Dict[str, Any]) -> ParameterSpec:
        """Convert a parameter definition from queries_bq.py format to ParameterSpec."""
        param_type = param_def.get("type", "text")
        label = param_def.get("label", name)
        required = param_def.get("required", False)
        options = param_def.get("options")

        # Handle default values based on parameter type
        if param_type == "year_range":
            # For year_range, use default_start as the default
            default = param_def.get("default_start", 2015)
        elif param_type == "multiselect":
            default = param_def.get("defaults", [])
        else:
            default = param_def.get("defaults", param_def.get("default", None))

        return ParameterSpec(
            name=name,
            type=param_type,
            label=label,
            default=default,
            required=required,
            options=options if isinstance(options, list) else None
        )

    def _load_queries_from_source(self) -> None:
        """Load all queries from TIP_for_PATLIBs_QueryLib_queries.py into the registry."""
        for query_id, query_data in _RAW_QUERIES.items():
            # Convert parameters
            params_raw = query_data.get("parameters", {})
            parameters = [
                self._convert_parameter(name, param_def)
                for name, param_def in params_raw.items()
            ]

            # Get SQL template (prefer sql_template, fallback to sql)
            sql_template = query_data.get("sql_template") or query_data.get("sql", "")

            # Extract output columns from key_outputs or leave empty
            key_outputs = query_data.get("key_outputs", [])

            # Build QueryMetadata
            self._queries[query_id] = QueryMetadata(
                id=query_id,
                title=query_data.get("title", f"Query {query_id}"),
                description=query_data.get("description", ""),
                category=query_data.get("category", "Uncategorized"),
                sql_template=sql_template,
                parameters=parameters,
                output_columns=[],  # Will be populated from actual query results
                tags=query_data.get("tags", []),
                explanation=query_data.get("explanation"),
                key_outputs=key_outputs,
            )
    def get_all_queries(self) -> List[QueryMetadata]:
        """
        Get all queries in the registry.

        Returns:
            List of all QueryMetadata objects
        """
        return list(self._queries.values())

    def get_query(self, query_id: str) -> Optional[QueryMetadata]:
        """
        Get a specific query by ID.

        Args:
            query_id: Query identifier (e.g., 'Q01')

        Returns:
            QueryMetadata if found, None otherwise
        """
        return self._queries.get(query_id)

    def get_queries_by_category(self, category: str) -> List[QueryMetadata]:
        """
        Get all queries in a specific category.

        Args:
            category: Category name (e.g., 'Regional')

        Returns:
            List of QueryMetadata in the category
        """
        return [q for q in self._queries.values() if q.category == category]

    def get_categories(self) -> List[str]:
        """
        Get list of all categories that have queries.

        Returns:
            List of category names
        """
        return list(set(q.category for q in self._queries.values()))

    def search_queries(self, keyword: str) -> List[QueryMetadata]:
        """
        Search queries by keyword in title, description, or tags.

        Args:
            keyword: Search term (case-insensitive)

        Returns:
            List of matching QueryMetadata
        """
        keyword_lower = keyword.lower()
        results = []
        for query in self._queries.values():
            # Search in title
            if keyword_lower in query.title.lower():
                results.append(query)
                continue
            # Search in description
            if keyword_lower in query.description.lower():
                results.append(query)
                continue
            # Search in tags
            if any(keyword_lower in tag.lower() for tag in query.tags):
                results.append(query)
                continue
        return results


# =============================================================================
# Reference Data Loaders (Story 1.4 - Task 4)
# =============================================================================

# Module-level caches for reference data
_jurisdiction_cache: Optional[List[Tuple[str, str]]] = None
_wipo_fields_cache: Optional[List[Tuple[str, int]]] = None


def get_jurisdiction_options() -> List[Tuple[str, str]]:
    """
    Get jurisdiction options for country selection dropdowns.

    Returns list of (display_name, code) tuples for use in ipywidgets
    Select/Dropdown controls.

    Returns:
        List of tuples: [(display_name, country_code), ...]

    Example:
        >>> options = get_jurisdiction_options()
        >>> options[0]
        ('European Patent Office (EP)', 'EP')
    """
    global _jurisdiction_cache
    if _jurisdiction_cache is None:
        _jurisdiction_cache = [
            ('European Patent Office (EP)', 'EP'),
            ('United States (US)', 'US'),
            ('China (CN)', 'CN'),
            ('Japan (JP)', 'JP'),
            ('Germany (DE)', 'DE'),
            ('France (FR)', 'FR'),
            ('United Kingdom (GB)', 'GB'),
            ('Korea (KR)', 'KR'),
            ('World (WO)', 'WO'),
            ('Austria (AT)', 'AT'),
            ('Belgium (BE)', 'BE'),
            ('Switzerland (CH)', 'CH'),
            ('Spain (ES)', 'ES'),
            ('Italy (IT)', 'IT'),
            ('Netherlands (NL)', 'NL'),
            ('Poland (PL)', 'PL'),
            ('Sweden (SE)', 'SE'),
        ]
    return _jurisdiction_cache


def get_wipo_field_options() -> List[Tuple[str, int]]:
    """
    Get WIPO 35 technology field options.

    Returns list of (field_name, field_number) tuples for use in
    ipywidgets Select/Dropdown controls.

    Returns:
        List of tuples: [(field_name, field_number), ...]

    Example:
        >>> options = get_wipo_field_options()
        >>> options[0]
        ('Electrical machinery', 1)
    """
    global _wipo_fields_cache
    if _wipo_fields_cache is None:
        _wipo_fields_cache = [
            ('Electrical machinery', 1),
            ('Audio-visual technology', 2),
            ('Telecommunications', 3),
            ('Digital communication', 4),
            ('Basic communication processes', 5),
            ('Computer technology', 6),
            ('IT methods for management', 7),
            ('Semiconductors', 8),
            ('Optics', 9),
            ('Measurement', 10),
            ('Analysis of biological materials', 11),
            ('Control', 12),
            ('Medical technology', 13),
            ('Organic fine chemistry', 14),
            ('Biotechnology', 15),
            ('Pharmaceuticals', 16),
            ('Macromolecular chemistry', 17),
            ('Food chemistry', 18),
            ('Basic materials chemistry', 19),
            ('Materials, metallurgy', 20),
            ('Surface technology, coating', 21),
            ('Micro-structure and nano-technology', 22),
            ('Chemical engineering', 23),
            ('Environmental technology', 24),
            ('Handling', 25),
            ('Machine tools', 26),
            ('Engines, pumps, turbines', 27),
            ('Textile and paper machines', 28),
            ('Other special machines', 29),
            ('Thermal processes and apparatus', 30),
            ('Mechanical elements', 31),
            ('Transport', 32),
            ('Furniture, games', 33),
            ('Other consumer goods', 34),
            ('Civil engineering', 35),
        ]
    return _wipo_fields_cache


# =============================================================================
# Parameter Widget Factory (Story 1.4 - Task 1)
# =============================================================================

def create_parameter_widget(param: ParameterSpec) -> widgets.Widget:
    """
    Create appropriate ipywidget for a parameter type.

    Factory function that generates the correct widget type based on
    the parameter specification. Applies default values and styling.

    Args:
        param: ParameterSpec defining the parameter

    Returns:
        ipywidget appropriate for the parameter type

    Supported types:
        - year_range: IntRangeSlider (min=1980, max=2024)
        - multiselect: SelectMultiple with options
        - select: Dropdown with options
        - text: Text input with placeholder
        - slider: IntSlider for numeric values (e.g., top_n)

    Example:
        >>> spec = ParameterSpec(name='years', type='year_range', label='Year Range',
        ...                      default=2015, required=True)
        >>> widget = create_parameter_widget(spec)
        >>> type(widget).__name__
        'IntRangeSlider'
    """
    style = {'description_width': '0px'}  # Use separate label
    layout = widgets.Layout(width='100%')

    if param.type == 'year_range':
        # Determine start/end values from default
        if isinstance(param.default, (list, tuple)) and len(param.default) == 2:
            start_val, end_val = param.default
        else:
            start_val = param.default if param.default else 2015
            end_val = 2024
        return widgets.IntRangeSlider(
            value=[start_val, end_val],
            min=1980,
            max=2024,
            step=1,
            description='',
            continuous_update=False,
            style=style,
            layout=layout
        )

    elif param.type == 'multiselect':
        options = param.options or get_jurisdiction_options()
        default_val = param.default if param.default else []
        # Ensure default values are valid
        valid_values = [v for _, v in options] if options and isinstance(options[0], tuple) else options
        default_val = [v for v in default_val if v in valid_values] if default_val else []
        return widgets.SelectMultiple(
            options=options,
            value=default_val,
            description='',
            rows=5,
            style=style,
            layout=layout
        )

    elif param.type == 'select':
        options = param.options or []
        default_val = param.default
        # Validate default is in options
        valid_values = [v for _, v in options] if options and isinstance(options[0], tuple) else options
        if default_val not in valid_values:
            default_val = valid_values[0] if valid_values else None
        return widgets.Dropdown(
            options=options,
            value=default_val,
            description='',
            style=style,
            layout=layout
        )

    elif param.type == 'text':
        return widgets.Text(
            value=param.default or '',
            description='',
            placeholder=f'Enter {param.label.lower()}...',
            style=style,
            layout=layout
        )

    elif param.type == 'slider':
        default_val = param.default if param.default else 10
        return widgets.IntSlider(
            value=default_val,
            min=1,
            max=100,
            step=1,
            description='',
            continuous_update=False,
            style=style,
            layout=layout
        )

    else:
        # Fallback to text input for unknown types
        return widgets.Text(
            value=str(param.default) if param.default else '',
            description='',
            placeholder=f'Enter value...',
            style=style,
            layout=layout
        )


# =============================================================================
# Validation Error Messages (Story 1.4 - Task 3)
# =============================================================================

VALIDATION_MESSAGES = {
    'required': "{label} is required",
    'year_range_invalid': "{label}: Start year must be before or equal to end year",
    'year_out_of_bounds': "{label}: Year must be between 1980 and 2024",
    'empty_multiselect': "{label}: Please select at least one option",
    'invalid_format': "{label}: Invalid format. Example: {example}",
}


# =============================================================================
# Parameter Form Widget (Story 1.4 - Task 2)
# =============================================================================

class ParameterForm:
    """
    Dynamic parameter form widget for query configuration.

    Generates a form with appropriate widgets for each query parameter.
    Provides validation, value extraction, and error highlighting.

    Attributes:
        widget: Composed VBox containing the form
        execute_button: Button to execute query (disabled until valid)

    Example:
        >>> query = registry.get_query('Q01')
        >>> form = ParameterForm(query)
        >>> display(form.widget)
        >>> values = form.get_values()
        >>> is_valid, errors = form.validate()
    """

    def __init__(self, query: Optional[QueryMetadata] = None):
        """
        Initialize ParameterForm.

        Args:
            query: QueryMetadata to generate form for, or None
        """
        self._query = query
        self._widgets: Dict[str, widgets.Widget] = {}
        self._param_specs: Dict[str, ParameterSpec] = {}
        self._labels: Dict[str, widgets.HTML] = {}
        self._hints: Dict[str, widgets.HTML] = {}
        self._error_output = widgets.HTML(value="")

        # Execute button
        self.execute_button = widgets.Button(
            description="Execute Query",
            button_style='success',
            icon='play',
            disabled=True,
            layout=widgets.Layout(width='150px', margin='10px 0')
        )

        # Form container
        self._form_container = widgets.VBox([])

        # Build form if query provided
        if query:
            self._build_form(query)

        # Main widget
        self.widget = widgets.VBox([
            self._form_container,
            self._error_output,
            self.execute_button
        ], layout=widgets.Layout(padding='10px'))

    def _build_form(self, query: QueryMetadata) -> None:
        """Build form widgets for query parameters."""
        self._query = query
        self._widgets.clear()
        self._param_specs.clear()
        self._labels.clear()
        self._hints.clear()

        if not query.parameters:
            self._form_container.children = [
                widgets.HTML(f"<i style='color: {EPO_COLORS['gray']};'>No parameters required</i>")
            ]
            self.execute_button.disabled = False
            return

        form_rows = []
        for param in query.parameters:
            self._param_specs[param.name] = param

            # Create label with required indicator
            required_marker = " <span style='color: red;'>*</span>" if param.required else ""
            label = widgets.HTML(
                value=f"<b>{param.label}</b>{required_marker}",
                layout=widgets.Layout(width='100%', margin='5px 0 2px 0')
            )
            self._labels[param.name] = label

            # Create widget
            widget = create_parameter_widget(param)
            self._widgets[param.name] = widget

            # Create default hint
            hint_text = ""
            if param.default is not None:
                if param.type == 'year_range':
                    hint_text = f"Default: {param.default}-2024"
                elif param.type == 'multiselect' and param.default:
                    hint_text = f"Default: {', '.join(str(v) for v in param.default[:3])}"
                else:
                    hint_text = f"Default: {param.default}"
            hint = widgets.HTML(
                value=f"<span style='font-size: 0.85em; color: {EPO_COLORS['gray']};'>{hint_text}</span>",
                layout=widgets.Layout(margin='0 0 10px 0')
            )
            self._hints[param.name] = hint

            # Add to form
            form_rows.append(label)
            form_rows.append(widget)
            form_rows.append(hint)

        self._form_container.children = form_rows
        self.execute_button.disabled = False

    def update(self, query: Optional[QueryMetadata]) -> None:
        """
        Update form with new query parameters.

        Args:
            query: QueryMetadata to generate form for, or None to clear
        """
        if query is None:
            self._query = None
            self._widgets.clear()
            self._param_specs.clear()
            self._form_container.children = []
            self.execute_button.disabled = True
            self._error_output.value = ""
            return

        self._build_form(query)
        self._error_output.value = ""

    def get_values(self) -> Dict[str, Any]:
        """
        Get current parameter values from form widgets.

        Returns:
            Dict mapping parameter names to their current values
        """
        values = {}
        for param_name, widget in self._widgets.items():
            param_spec = self._param_specs[param_name]

            if param_spec.type == 'year_range':
                # IntRangeSlider returns tuple
                values[param_name] = widget.value
            elif param_spec.type == 'multiselect':
                # SelectMultiple returns tuple
                values[param_name] = list(widget.value)
            else:
                values[param_name] = widget.value

        return values

    def validate(self) -> Tuple[bool, List[str]]:
        """
        Validate all parameter values.

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []
        self._clear_highlights()

        for param_name, widget in self._widgets.items():
            param_spec = self._param_specs[param_name]
            value = self._get_widget_value(widget, param_spec.type)

            # Required check
            if param_spec.required:
                if value is None or value == '' or value == [] or value == ():
                    errors.append(VALIDATION_MESSAGES['required'].format(label=param_spec.label))
                    self.highlight_invalid(param_name)
                    continue

            # Type-specific validation
            if param_spec.type == 'year_range' and value:
                start, end = value
                if start > end:
                    errors.append(VALIDATION_MESSAGES['year_range_invalid'].format(label=param_spec.label))
                    self.highlight_invalid(param_name)
                elif start < 1980 or end > 2024:
                    errors.append(VALIDATION_MESSAGES['year_out_of_bounds'].format(label=param_spec.label))
                    self.highlight_invalid(param_name)

            elif param_spec.type == 'multiselect' and param_spec.required:
                if not value or len(value) == 0:
                    errors.append(VALIDATION_MESSAGES['empty_multiselect'].format(label=param_spec.label))
                    self.highlight_invalid(param_name)

        # Display errors
        if errors:
            error_html = "<br>".join([f"❌ {e}" for e in errors])
            self._error_output.value = f"""
            <div style="color: {EPO_COLORS['red']}; padding: 10px; margin: 5px 0;
                        background-color: {EPO_COLORS['error_bg']}; border-radius: 4px;">
                {error_html}
            </div>
            """
        else:
            self._error_output.value = ""

        return len(errors) == 0, errors

    def _get_widget_value(self, widget: widgets.Widget, param_type: str) -> Any:
        """Extract value from widget based on parameter type."""
        if param_type == 'year_range':
            return widget.value  # tuple
        elif param_type == 'multiselect':
            return list(widget.value)
        else:
            return widget.value

    def highlight_invalid(self, param_name: str) -> None:
        """Add red border to invalid field."""
        widget = self._widgets.get(param_name)
        if widget:
            widget.layout.border = f'2px solid {EPO_COLORS["red"]}'

    def _clear_highlights(self) -> None:
        """Clear all error highlights."""
        for widget in self._widgets.values():
            widget.layout.border = ''


# =============================================================================
# Query Execution (Story 1.5 - FR5, FR11, FR12, FR39, FR40, FR41)
# =============================================================================

import re
import threading
import time as time_module

# Timeout constant (NFR1: Standard queries complete within 120 seconds)
TIMEOUT_SECONDS = 120


class QueryTimeoutError(Exception):
    """Raised when a query exceeds the timeout limit."""
    pass


def substitute_parameters(sql_template: str, params: Dict[str, Any]) -> str:
    """
    Replace @param placeholders with actual values.

    Handles different parameter types:
    - Tuples (year_range): Substitutes @year_start and @year_end separately
    - Lists (multiselect): Converts to BigQuery array format for UNNEST or SQL IN clause
    - Strings: Properly quoted
    - Numbers: Converted to string

    Args:
        sql_template: SQL with @parameter placeholders
        params: Dict mapping parameter names to values

    Returns:
        SQL string with parameters substituted

    Example:
        >>> substitute_parameters(
        ...     "SELECT * WHERE year >= @year_start AND year <= @year_end",
        ...     {"year_range": (2015, 2020)}
        ... )
        "SELECT * WHERE year >= 2015 AND year <= 2020"
    """
    result = sql_template

    for param_name, value in params.items():
        # Handle year_range tuples specially
        if isinstance(value, tuple) and len(value) == 2:
            # Year range - substitute both start and end
            result = result.replace(f"@{param_name}_start", str(value[0]))
            result = result.replace(f"@{param_name}_end", str(value[1]))
            # Also handle simple @year_start/@year_end pattern
            result = result.replace("@year_start", str(value[0]))
            result = result.replace("@year_end", str(value[1]))
            result = result.replace("@start_year", str(value[0]))
            result = result.replace("@end_year", str(value[1]))
            continue

        placeholder = f"@{param_name}"

        if isinstance(value, list):
            # Check if this parameter is used with UNNEST (BigQuery array syntax)
            # Pattern: UNNEST(@param_name) requires array format ['a', 'b']
            unnest_pattern = f"UNNEST({placeholder})"
            if unnest_pattern.lower() in result.lower():
                # Use BigQuery array format for UNNEST
                if all(isinstance(v, str) for v in value):
                    quoted = [f"'{v}'" for v in value]
                else:
                    quoted = [str(v) for v in value]
                sql_value = f"[{', '.join(quoted)}]"
            else:
                # Standard SQL IN clause format
                if all(isinstance(v, str) for v in value):
                    quoted = [f"'{v}'" for v in value]
                else:
                    quoted = [str(v) for v in value]
                sql_value = f"({', '.join(quoted)})"
        elif isinstance(value, str):
            # Quote strings
            sql_value = f"'{value}'"
        elif isinstance(value, (int, float)):
            sql_value = str(value)
        else:
            sql_value = str(value)

        result = result.replace(placeholder, sql_value)

    return result


class ProgressIndicator:
    """
    Progress indicator widget with elapsed time tracking.

    Shows a styled progress message with spinner that updates every 5 seconds
    (NFR5) to show elapsed time. Supports success and error completion states.

    Attributes:
        widget: The ipywidgets.HTML widget to display

    Example:
        >>> progress = ProgressIndicator()
        >>> display(progress.widget)
        >>> progress.start("Executing query...")
        >>> # ... query runs ...
        >>> progress.complete(True, "Found 150 results")
    """

    def __init__(self):
        """Initialize ProgressIndicator."""
        self._widget = widgets.HTML(value="")
        self._start_time: Optional[float] = None
        self._timer: Optional[threading.Timer] = None
        self._running = False

    @property
    def widget(self) -> widgets.HTML:
        """Get the HTML widget for display."""
        return self._widget

    def start(self, message: str = "Executing query...") -> None:
        """
        Start the progress indicator.

        Args:
            message: Initial progress message to display
        """
        self._start_time = time_module.time()
        self._running = True
        self._update_display(f"⏳ {message}", "running")
        self._schedule_update()

    def _schedule_update(self) -> None:
        """Schedule the next elapsed time update (every 5 seconds per NFR5)."""
        if self._running:
            self._timer = threading.Timer(5.0, self._on_timer)
            self._timer.daemon = True
            self._timer.start()

    def _on_timer(self) -> None:
        """Handle timer tick - update elapsed time display."""
        if self._running and self._start_time:
            elapsed = int(time_module.time() - self._start_time)
            if elapsed < 60:
                time_str = f"{elapsed}s"
            else:
                minutes = elapsed // 60
                seconds = elapsed % 60
                time_str = f"{minutes}m {seconds}s"
            self._update_display(f"⏳ Running... ({time_str})", "running")
            self._schedule_update()

    def complete(self, success: bool, message: str) -> None:
        """
        Mark the progress as complete.

        Args:
            success: True for success (green), False for error (red)
            message: Completion message to display
        """
        self._running = False
        if self._timer:
            self._timer.cancel()
            self._timer = None

        elapsed = 0
        if self._start_time:
            elapsed = int(time_module.time() - self._start_time)

        status = "success" if success else "error"
        emoji = "✅" if success else "❌"
        full_message = f"{emoji} {message} ({elapsed}s)"
        self._update_display(full_message, status)

    def reset(self) -> None:
        """Reset the progress indicator to empty state."""
        self._running = False
        if self._timer:
            self._timer.cancel()
            self._timer = None
        self._start_time = None
        self._widget.value = ""

    def _update_display(self, message: str, status: str) -> None:
        """Update the HTML widget display with appropriate styling."""
        colors = {
            "running": (EPO_COLORS['primary_blue'], EPO_COLORS['light_gray']),
            "success": (EPO_COLORS['green'], "#E8F5E9"),
            "error": (EPO_COLORS['red'], EPO_COLORS['error_bg']),
        }
        border_color, bg_color = colors.get(status, colors["running"])

        self._widget.value = f'''
        <div style="padding: 12px; border-left: 4px solid {border_color};
                    background-color: {bg_color}; margin: 8px 0; border-radius: 0 4px 4px 0;">
            <span style="color: {border_color}; font-weight: bold;">
                {message}
            </span>
        </div>
        '''


class QueryExecutor:
    """
    Executes PATSTAT queries with timeout handling.

    Uses PatstatClient for database access and implements NFR1's 120-second
    timeout requirement. Provides clean error handling and cancellation.

    Attributes:
        TIMEOUT_SECONDS: Maximum execution time (120 seconds per NFR1)

    Example:
        >>> executor = QueryExecutor()
        >>> df = executor.execute(query, {"year_range": (2015, 2020)})
    """

    TIMEOUT_SECONDS = TIMEOUT_SECONDS  # NFR1

    def __init__(self, client: Optional[PatstatClient] = None):
        """
        Initialize QueryExecutor.

        Args:
            client: Optional PatstatClient instance. If None, uses module-level patstat_client.
        """
        self._client = client

    @property
    def client(self) -> PatstatClient:
        """Get the PatstatClient to use for queries."""
        if self._client is not None:
            return self._client
        if patstat_client is None:
            raise RuntimeError("PATSTAT not initialized. Call initialize() first.")
        return patstat_client

    def execute(self, query: 'QueryMetadata', params: Dict[str, Any]) -> 'pd.DataFrame':
        """
        Execute a query with the given parameters.

        Substitutes parameters into the SQL template and executes via
        PatstatClient. Implements 120-second timeout (NFR1).

        Args:
            query: QueryMetadata containing the sql_template
            params: Dict of parameter values from ParameterForm.get_values()

        Returns:
            pandas DataFrame with query results

        Raises:
            QueryTimeoutError: If query exceeds 120 seconds
            Exception: Other errors from query execution
        """
        # Substitute parameters
        sql = substitute_parameters(query.sql_template, params)

        # Execute with timeout using threading
        result_holder = [None]
        error_holder = [None]

        def run_query():
            try:
                res = self.client.sql_query(sql, use_legacy_sql=False)
                result_holder[0] = pd.DataFrame(res)
            except Exception as e:
                error_holder[0] = e

        thread = threading.Thread(target=run_query, daemon=True)
        thread.start()
        thread.join(timeout=self.TIMEOUT_SECONDS)

        if thread.is_alive():
            # Query is still running - timeout occurred
            raise QueryTimeoutError(
                f"Query exceeded {self.TIMEOUT_SECONDS} second timeout.\n\n"
                "Suggestions to reduce query time:\n"
                "- Narrow the date range (e.g., last 5 years instead of 20)\n"
                "- Select fewer jurisdictions\n"
                "- Use more specific technology field filters\n"
                "- Try a simpler query first to verify your criteria"
            )

        if error_holder[0] is not None:
            raise error_holder[0]

        return result_holder[0]


# =============================================================================
# SQL Parameter Highlighting (Story 1.3 - Task 3.3)
# =============================================================================


def highlight_parameters(sql: str) -> str:
    """
    Highlight @parameter placeholders in SQL.

    Wraps @param placeholders in colored spans for visual distinction
    in the SQL viewer.

    Args:
        sql: SQL template with @parameter placeholders

    Returns:
        HTML string with highlighted parameters

    Example:
        >>> highlight_parameters("SELECT * WHERE year >= @start_year")
        'SELECT * WHERE year >= <span style="...">@start_year</span>'
    """
    def replace_param(match):
        param = match.group(0)
        return f'<span style="color: {EPO_COLORS["orange"]}; font-weight: bold;">{param}</span>'

    return re.sub(r'@\w+', replace_param, sql)


# =============================================================================
# Query Browser Widgets (Story 1.3 - FR1, FR2, FR3, FR9)
# =============================================================================

class QueryPreview:
    """
    Widget to preview selected query details.

    Displays query title, category badge, description, tags, key outputs,
    and a "View SQL" button. Part of the Query Browser composition.

    Attributes:
        title_html: HTML widget showing query title and category
        description_html: HTML widget showing query description
        tags_html: HTML widget showing stakeholder tags
        outputs_html: HTML widget showing key outputs
        view_sql_button: Button to trigger SQL display
        widget: Composed VBox container

    Example:
        >>> preview = QueryPreview()
        >>> preview.update(query)
        >>> display(preview.widget)
    """

    def __init__(self):
        """Initialize QueryPreview widget."""
        # Title with category badge
        self.title_html = widgets.HTML(value="<i>Select a query to see details</i>")

        # Description
        self.description_html = widgets.HTML(value="")

        # Tags display
        self.tags_html = widgets.HTML(value="")

        # Key outputs display
        self.outputs_html = widgets.HTML(value="")

        # View SQL button (initially disabled)
        self.view_sql_button = widgets.Button(
            description="View SQL",
            button_style='info',
            disabled=True,
            icon='code',
            layout=widgets.Layout(width='120px')
        )

        # Compose widget
        self.widget = widgets.VBox([
            self.title_html,
            self.description_html,
            self.tags_html,
            self.outputs_html,
            self.view_sql_button,
        ], layout=widgets.Layout(
            padding='10px',
            border=f'1px solid {EPO_COLORS["light_gray"]}',
            margin='5px 0'
        ))

        # Current query reference
        self._current_query: Optional[QueryMetadata] = None

    def update(self, query: Optional[QueryMetadata]) -> None:
        """
        Update preview with selected query details.

        Args:
            query: QueryMetadata to display, or None to clear
        """
        self._current_query = query

        if query is None:
            self.title_html.value = "<i>Select a query to see details</i>"
            self.description_html.value = ""
            self.tags_html.value = ""
            self.outputs_html.value = ""
            self.view_sql_button.disabled = True
            return

        # Title with category badge
        category_color = EPO_COLORS['secondary_blue']
        self.title_html.value = f"""
        <div style="margin-bottom: 8px;">
            <span style="font-size: 1.2em; font-weight: bold; color: {EPO_COLORS['primary_blue']};">
                {query.title}
            </span>
            <span style="background-color: {category_color}; color: white; padding: 2px 8px;
                         border-radius: 4px; font-size: 0.8em; margin-left: 10px;">
                {query.category}
            </span>
        </div>
        """

        # Description
        self.description_html.value = f"""
        <div style="color: {EPO_COLORS['gray']}; margin-bottom: 8px;">
            {query.description}
        </div>
        """

        # Tags as badges
        if query.tags:
            tags_html = " ".join([
                f'<span style="background-color: {EPO_COLORS["light_gray"]}; color: {EPO_COLORS["gray"]};'
                f' padding: 2px 6px; border-radius: 3px; font-size: 0.85em; margin-right: 5px;">'
                f'{tag}</span>'
                for tag in query.tags
            ])
            self.tags_html.value = f'<div style="margin-bottom: 8px;">{tags_html}</div>'
        else:
            self.tags_html.value = ""

        # Key outputs
        if query.key_outputs:
            outputs_list = "<br>".join([f"• {output}" for output in query.key_outputs])
            self.outputs_html.value = f"""
            <div style="margin-top: 8px; padding: 8px; background-color: {EPO_COLORS['light_gray']};
                        border-radius: 4px;">
                <b>Key Outputs:</b><br>
                <span style="font-size: 0.9em;">{outputs_list}</span>
            </div>
            """
        else:
            self.outputs_html.value = ""

        # Enable View SQL button
        self.view_sql_button.disabled = False


class SQLViewer:
    """
    Collapsible SQL viewer widget.

    Displays formatted SQL with parameter highlighting in a collapsible
    accordion panel.

    Attributes:
        sql_content: HTML widget showing formatted SQL
        accordion: Accordion container for collapsible display
        widget: Main widget container

    Example:
        >>> viewer = SQLViewer()
        >>> viewer.show_sql("SELECT * FROM table WHERE year >= @start_year")
        >>> display(viewer.widget)
    """

    def __init__(self):
        """Initialize SQLViewer widget."""
        # SQL content display
        self.sql_content = widgets.HTML(value="")

        # Accordion for collapsible display
        self.accordion = widgets.Accordion(
            children=[self.sql_content],
            selected_index=None,  # Start collapsed
            layout=widgets.Layout(margin='5px 0')
        )
        self.accordion.set_title(0, "SQL Query")

        self.widget = self.accordion

    def show_sql(self, sql: str) -> None:
        """
        Display SQL with formatting and parameter highlighting.

        Args:
            sql: SQL template to display
        """
        # Highlight parameters
        highlighted_sql = highlight_parameters(sql)

        # Format with preserved indentation
        self.sql_content.value = f"""
        <pre style="background-color: {EPO_COLORS['light_gray']}; padding: 15px;
                    border-radius: 4px; overflow-x: auto; font-family: monospace;
                    font-size: 0.9em; line-height: 1.4; white-space: pre-wrap;
                    word-wrap: break-word;">{highlighted_sql}</pre>
        """

        # Expand accordion to show SQL
        self.accordion.selected_index = 0

    def hide(self) -> None:
        """Collapse the SQL viewer."""
        self.accordion.selected_index = None


class QueryBrowser:
    """
    Main Query Browser widget for browsing and searching queries.

    Provides a visual interface with category dropdown, search input,
    and query list for finding and selecting queries.

    Attributes:
        category_dropdown: Dropdown for filtering by category
        search_input: Text input for keyword search
        query_list: Select widget showing matching queries
        selected_query: Currently selected QueryMetadata
        widget: Composed VBox container

    Example:
        >>> registry = QueryRegistry()
        >>> browser = QueryBrowser(registry)
        >>> display(browser.widget)
    """

    def __init__(self, registry: QueryRegistry):
        """
        Initialize QueryBrowser with a registry.

        Args:
            registry: QueryRegistry containing all available queries
        """
        self._registry = registry
        self._search_timer: Optional[threading.Timer] = None
        self._search_delay = 0.3  # 300ms debounce

        # Current state
        self._current_queries: List[QueryMetadata] = []
        self.selected_query: Optional[QueryMetadata] = None

        # Category dropdown
        categories = ["All Categories"] + sorted(registry.get_categories())
        self.category_dropdown = widgets.Dropdown(
            options=categories,
            value="All Categories",
            description="Category:",
            layout=widgets.Layout(width='200px')
        )
        self.category_dropdown.observe(self._on_category_change, names='value')

        # Search input
        self.search_input = widgets.Text(
            placeholder="Search queries...",
            layout=widgets.Layout(width='250px')
        )
        self.search_input.observe(self._on_search_change, names='value')

        # Query list
        self.query_list = widgets.Select(
            options=[],
            rows=8,
            layout=widgets.Layout(width='100%')
        )
        self.query_list.observe(self._on_query_select, names='value')

        # Initialize with all queries
        self._update_query_list(registry.get_all_queries())

        # Compose widget
        controls = widgets.HBox([
            self.category_dropdown,
            self.search_input
        ], layout=widgets.Layout(margin='0 0 10px 0'))

        self.widget = widgets.VBox([
            controls,
            self.query_list
        ])

    def _on_category_change(self, change: Dict[str, Any]) -> None:
        """Handle category dropdown change."""
        category = change['new']
        search_term = self.search_input.value.strip()

        if category == "All Categories":
            queries = self._registry.get_all_queries()
        else:
            queries = self._registry.get_queries_by_category(category)

        # Apply search filter if present
        if search_term:
            queries = [q for q in queries if self._matches_search(q, search_term)]

        self._update_query_list(queries)

    def _on_search_change(self, change: Dict[str, Any]) -> None:
        """Handle search input change with debouncing."""
        # Cancel previous timer
        if self._search_timer:
            self._search_timer.cancel()

        # Start new timer
        self._search_timer = threading.Timer(
            self._search_delay,
            self._execute_search,
            args=[change['new']]
        )
        self._search_timer.start()

    def _execute_search(self, keyword: str) -> None:
        """Execute search after debounce delay."""
        category = self.category_dropdown.value
        keyword = keyword.strip()

        # Get base queries based on category
        if category == "All Categories":
            queries = self._registry.get_all_queries()
        else:
            queries = self._registry.get_queries_by_category(category)

        # Apply search filter
        if keyword:
            queries = [q for q in queries if self._matches_search(q, keyword)]

        self._update_query_list(queries)

    def _matches_search(self, query: QueryMetadata, keyword: str) -> bool:
        """Check if query matches search keyword."""
        keyword_lower = keyword.lower()
        return (
            keyword_lower in query.title.lower() or
            keyword_lower in query.description.lower() or
            any(keyword_lower in tag.lower() for tag in query.tags)
        )

    def _update_query_list(self, queries: List[QueryMetadata]) -> None:
        """Update the query list with given queries."""
        self._current_queries = queries

        # Create options as (display_label, query_id) tuples
        options = [(f"{q.id}: {q.title}", q.id) for q in queries]
        self.query_list.options = options

        # Clear selection
        self.selected_query = None
        if options:
            self.query_list.value = None

    def _on_query_select(self, change: Dict[str, Any]) -> None:
        """Handle query selection."""
        query_id = change['new']
        if query_id:
            self.selected_query = self._registry.get_query(query_id)
        else:
            self.selected_query = None


# =============================================================================
# Results Display and Export (Story 1.6 - FR6, FR7, FR8, FR10)
# =============================================================================

from datetime import datetime
from IPython.display import FileLink, Javascript


def format_number(val) -> Any:
    """
    Format large numbers with thousand separators.

    Integers get formatted as "1,234,567".
    Floats get formatted as "1,234,567.89" (2 decimal places).
    Non-numeric values pass through unchanged.

    Args:
        val: Value to format (int, float, or other)

    Returns:
        Formatted string for numbers, original value otherwise

    Example:
        >>> format_number(1234567)
        '1,234,567'
        >>> format_number(1234567.89)
        '1,234,567.89'
        >>> format_number("text")
        'text'
    """
    if isinstance(val, (int, float)) and not pd.isna(val):
        if isinstance(val, float):
            return f"{val:,.2f}"
        return f"{val:,}"
    return val


def display_zero_results() -> None:
    """
    Display helpful message when query returns no results.

    Shows a styled warning box with:
    - Clear "No results found" message
    - Possible reasons for empty results
    - Suggestions for broadening the search

    Per AC4: Zero results handling with helpful suggestions.
    """
    display(HTML(f'''
        <div style="padding: 20px; border: 1px solid {EPO_COLORS['orange']};
                    border-radius: 4px; background-color: #FFF8E1; margin: 10px 0;">
            <h4 style="color: {EPO_COLORS['orange']}; margin-top: 0;">
                No results found
            </h4>
            <p style="color: {EPO_COLORS['gray']};">
                Your query returned no matching records. This could be because:
            </p>
            <ul style="color: {EPO_COLORS['gray']};">
                <li>The date range is too narrow</li>
                <li>The selected jurisdictions have limited data for this query type</li>
                <li>The technology field filter is too specific</li>
                <li>The data may not yet be available for recent years</li>
            </ul>
            <p style="color: {EPO_COLORS['gray']}; margin-bottom: 0;">
                <strong>Suggestions:</strong> Try expanding the date range,
                adding more jurisdictions, or using broader technology filters.
            </p>
        </div>
    '''))


def export_to_csv(df: pd.DataFrame, query_title: str) -> str:
    """
    Export DataFrame to CSV file.

    Uses semicolon delimiter and UTF-8 with BOM per architecture spec.
    Creates exports directory if needed.

    Args:
        df: DataFrame to export
        query_title: Query title for filename

    Returns:
        Path to created CSV file

    Example:
        >>> filepath = export_to_csv(df, "Country Patent Activity")
        >>> # Creates: exports/Country_Patent_Activity_20260201_143052.csv
    """
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = "".join(c if c.isalnum() else "_" for c in query_title)[:50]
    filename = f"{safe_title}_{timestamp}.csv"

    # Create exports directory if needed
    export_dir = "exports"
    os.makedirs(export_dir, exist_ok=True)
    filepath = os.path.join(export_dir, filename)

    # Export with semicolon delimiter and UTF-8 BOM
    df.to_csv(
        filepath,
        sep=';',
        encoding='utf-8-sig',  # UTF-8 with BOM
        index=False
    )

    return filepath


def export_to_png(fig, query_title: str) -> str:
    """
    Export Plotly figure to PNG file.

    Exports at 300 DPI resolution suitable for presentations.
    Creates exports directory if needed.

    Args:
        fig: Plotly figure object
        query_title: Query title for filename

    Returns:
        Path to created PNG file

    Example:
        >>> filepath = export_to_png(fig, "Patent Trends")
        >>> # Creates: exports/Patent_Trends_20260201_143052.png
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = "".join(c if c.isalnum() else "_" for c in query_title)[:50]
    filename = f"{safe_title}_{timestamp}.png"

    export_dir = "exports"
    os.makedirs(export_dir, exist_ok=True)
    filepath = os.path.join(export_dir, filename)

    # Export at 300 DPI for presentations
    # scale=2.5 at 1200x800 results in ~300 DPI
    fig.write_image(
        filepath,
        width=1200,
        height=800,
        scale=2.5
    )

    return filepath


def copy_sql_to_clipboard(sql: str) -> None:
    """
    Copy SQL to clipboard using JavaScript.

    Uses navigator.clipboard API for modern browser support.
    Shows confirmation message after copy.

    Args:
        sql: SQL query string to copy
    """
    # Escape for JavaScript string
    escaped_sql = sql.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n')

    js_code = f'''
        navigator.clipboard.writeText('{escaped_sql}').then(function() {{
            console.log('SQL copied to clipboard');
        }}).catch(function(err) {{
            console.error('Failed to copy: ', err);
        }});
    '''
    display(Javascript(js_code))
    display_status("SQL copied to clipboard. Paste in a new cell to customize.", success=True)


class ResultsDisplay:
    """
    Widget for displaying query results as formatted DataFrame.

    Provides:
    - Styled table with EPO colors
    - Thousand separators for large numbers
    - Row count display
    - Pagination for large results (>100 rows)

    Per AC1: DataFrame display with formatting.

    Attributes:
        widget: The output widget container

    Example:
        >>> rd = ResultsDisplay()
        >>> rd.show(df, title="Patent Counts")
        >>> display(rd.widget)
    """

    def __init__(self):
        """Initialize ResultsDisplay widget."""
        self._output = widgets.Output()
        self.widget = self._output

    def show(self, df: pd.DataFrame, title: str) -> None:
        """
        Display query results as formatted table.

        Args:
            df: Results DataFrame
            title: Query title for display
        """
        with self._output:
            self._output.clear_output()

            if df.empty:
                display_zero_results()
                return

            # Show row count
            display(HTML(f'''
                <div style="color: {EPO_COLORS['gray']}; margin-bottom: 8px;">
                    Showing <strong>{len(df):,}</strong> results
                </div>
            '''))

            # Determine how many rows to show
            display_df = df.head(100) if len(df) > 100 else df

            # Format and display DataFrame with styling
            styled = display_df.style \
                .format(format_number) \
                .set_table_styles([
                    {'selector': 'th', 'props': [
                        ('background-color', EPO_COLORS['primary_blue']),
                        ('color', 'white'),
                        ('padding', '8px'),
                        ('text-align', 'left')
                    ]},
                    {'selector': 'td', 'props': [
                        ('padding', '6px'),
                        ('text-align', 'left')
                    ]},
                    {'selector': 'tr:nth-child(even)', 'props': [
                        ('background-color', EPO_COLORS['light_gray'])
                    ]}
                ])

            display(styled)

            # Show pagination message for large results
            if len(df) > 100:
                display(HTML(f'''
                    <div style="color: {EPO_COLORS['orange']}; margin-top: 8px;">
                        Showing first 100 of {len(df):,} results.
                        Export to CSV for complete data.
                    </div>
                '''))


class ResultsPanel:
    """
    Composite widget for displaying query results and export options.

    Combines ResultsDisplay with export buttons (CSV, PNG, Copy SQL).
    Manages state for the current query and visualization.

    Per AC1-5: Complete results display with all export functionality.

    Attributes:
        widget: The composed VBox container

    Example:
        >>> panel = ResultsPanel()
        >>> panel.show_results(df, query, fig=chart)
        >>> display(panel.widget)
    """

    def __init__(self):
        """Initialize ResultsPanel with all components."""
        self._df: Optional[pd.DataFrame] = None
        self._query: Optional['QueryMetadata'] = None
        self._fig = None  # Visualization figure (if any)
        self._sql: str = ""

        # Create results display
        self._results_display = ResultsDisplay()

        # Create export buttons
        self._export_csv_btn = widgets.Button(
            description="Export CSV",
            button_style='primary',
            icon='download',
            layout=widgets.Layout(width='120px')
        )
        self._export_png_btn = widgets.Button(
            description="Export PNG",
            button_style='info',
            icon='image',
            disabled=True,  # Enabled when visualization exists
            layout=widgets.Layout(width='120px')
        )
        self._copy_sql_btn = widgets.Button(
            description="Copy SQL",
            button_style='',
            icon='copy',
            layout=widgets.Layout(width='120px')
        )

        # Status output for messages
        self._status_output = widgets.Output()

        # Wire up handlers
        self._export_csv_btn.on_click(self._on_export_csv)
        self._export_png_btn.on_click(self._on_export_png)
        self._copy_sql_btn.on_click(self._on_copy_sql)

        # Compose layout
        self._button_bar = widgets.HBox([
            self._export_csv_btn,
            self._export_png_btn,
            self._copy_sql_btn
        ], layout=widgets.Layout(margin='10px 0'))

        self.widget = widgets.VBox([
            self._results_display.widget,
            self._button_bar,
            self._status_output
        ])

    def show_results(
        self,
        df: pd.DataFrame,
        query: 'QueryMetadata',
        fig=None,
        sql: str = ""
    ) -> None:
        """
        Display results and enable export buttons.

        Args:
            df: Results DataFrame
            query: QueryMetadata for title and SQL
            fig: Optional Plotly figure for PNG export
            sql: Optional executed SQL (if different from template)
        """
        self._df = df
        self._query = query
        self._fig = fig
        self._sql = sql or query.sql_template

        # Clear status
        with self._status_output:
            self._status_output.clear_output()

        # Display results
        self._results_display.show(df, query.title)

        # Enable/disable PNG button based on figure
        self._export_png_btn.disabled = (fig is None)

    def _on_export_csv(self, b) -> None:
        """Handle Export CSV button click."""
        if self._df is None or self._query is None:
            return

        with self._status_output:
            self._status_output.clear_output()
            try:
                filepath = export_to_csv(self._df, self._query.title)
                display(FileLink(filepath, result_html_prefix="Download: "))
                display_status(f"Exported to {filepath}", success=True)
            except Exception as e:
                display_error("Export Error", "Failed to export CSV file.", details=str(e))

    def _on_export_png(self, b) -> None:
        """Handle Export PNG button click."""
        if self._fig is None or self._query is None:
            return

        with self._status_output:
            self._status_output.clear_output()
            try:
                filepath = export_to_png(self._fig, self._query.title)
                display(FileLink(filepath, result_html_prefix="Download: "))
                display_status(f"Exported to {filepath}", success=True)
            except Exception as e:
                display_error("Export Error", "Failed to export PNG file.", details=str(e))

    def _on_copy_sql(self, b) -> None:
        """Handle Copy SQL button click."""
        with self._status_output:
            self._status_output.clear_output()
            copy_sql_to_clipboard(self._sql)


def create_query_browser(
    registry: QueryRegistry,
    on_execute: Optional[callable] = None,
    on_results: Optional[callable] = None
) -> widgets.VBox:
    """
    Factory function to create a complete Query Browser widget with execution.

    Creates and composes all browser components (browser, preview, SQL viewer,
    parameter form, progress indicator, results panel) into a single VBox widget
    ready for display. Includes full query execution with progress tracking,
    error handling, and results display with export capabilities.

    Args:
        registry: QueryRegistry containing available queries
        on_execute: Optional callback(query, params) called before execution starts
        on_results: Optional callback(query, params, df) called with results DataFrame.
                   If not provided, uses built-in ResultsPanel for display.

    Returns:
        widgets.VBox: Composed browser widget with execution capability

    Example:
        >>> registry = QueryRegistry()
        >>> browser = create_query_browser(registry)
        >>> display(browser)
    """
    # Create components
    browser = QueryBrowser(registry)
    preview = QueryPreview()
    sql_viewer = SQLViewer()
    param_form = ParameterForm()
    progress = ProgressIndicator()
    executor = QueryExecutor()

    # Results panel with export buttons (Story 1.6)
    results_panel = ResultsPanel()

    # Track current SQL for copy functionality
    current_sql = {'value': ''}

    # Wire up interactions
    def on_query_select(change):
        query_id = change['new']
        if query_id:
            query = registry.get_query(query_id)
            preview.update(query)
            param_form.update(query)
            browser.selected_query = query
            progress.reset()
            current_sql['value'] = query.sql_template
        else:
            preview.update(None)
            param_form.update(None)
            browser.selected_query = None
            sql_viewer.hide()
            progress.reset()
            current_sql['value'] = ''

    browser.query_list.observe(on_query_select, names='value')

    def on_view_sql_click(button):
        if preview._current_query:
            sql_viewer.show_sql(preview._current_query.sql_template)

    preview.view_sql_button.on_click(on_view_sql_click)

    def on_execute_click(button):
        """Handle Execute button click with full execution flow."""
        # Validate first
        is_valid, errors = param_form.validate()
        if not is_valid:
            return

        query = param_form._query
        if not query:
            return

        params = param_form.get_values()

        # Get the substituted SQL for copy functionality
        executed_sql = substitute_parameters(query.sql_template, params)
        current_sql['value'] = executed_sql

        # Call pre-execute callback if provided
        if on_execute:
            on_execute(query, params)

        # Disable button and show progress
        param_form.execute_button.disabled = True
        progress.start(f"Executing {query.id}...")

        try:
            # Execute the query (synchronous - widget updates don't work from threads)
            df = executor.execute(query, params)

            # Success - update UI
            progress.complete(True, f"Found {len(df)} results")

            # Display results using ResultsPanel (Story 1.6)
            results_panel.show_results(df, query, sql=executed_sql)

            # Also call custom callback if provided
            if on_results:
                on_results(query, params, df)

        except QueryTimeoutError as e:
            # Timeout
            progress.complete(False, "Query timed out")
            with results_panel._results_display._output:
                results_panel._results_display._output.clear_output()
                display_error(
                    "Query Timeout",
                    str(e),
                    details=f"Query exceeded {TIMEOUT_SECONDS}s limit"
                )

        except Exception as e:
            # Other errors
            progress.complete(False, "Query failed")
            with results_panel._results_display._output:
                results_panel._results_display._output.clear_output()
                display_error(
                    "Query Error",
                    "Unable to execute the query. Please check your parameters and try again.",
                    details=str(e)
                )

        finally:
            # Re-enable button
            param_form.execute_button.disabled = False

    param_form.execute_button.on_click(on_execute_click)

    # Header
    header = widgets.HTML(f"""
    <div style="padding: 10px; background-color: {EPO_COLORS['primary_blue']}; color: white;
                border-radius: 4px 4px 0 0; margin-bottom: 10px;">
        <span style="font-size: 1.3em; font-weight: bold;">Query Browser</span>
        <span style="font-size: 0.9em; margin-left: 10px;">Browse and search available queries</span>
    </div>
    """)

    # Parameters section header
    params_header = widgets.HTML(f"""
    <div style="padding: 8px; background-color: {EPO_COLORS['light_gray']};
                border-radius: 4px; margin: 10px 0 5px 0;">
        <b style="color: {EPO_COLORS['primary_blue']};">Query Parameters</b>
    </div>
    """)

    # Results section header
    results_header = widgets.HTML(f"""
    <div style="padding: 8px; background-color: {EPO_COLORS['light_gray']};
                border-radius: 4px; margin: 10px 0 5px 0;">
        <b style="color: {EPO_COLORS['primary_blue']};">Results</b>
    </div>
    """)

    # Compose all components
    return widgets.VBox([
        header,
        browser.widget,
        preview.widget,
        sql_viewer.widget,
        params_header,
        param_form.widget,
        progress.widget,
        results_header,
        results_panel.widget,
    ], layout=widgets.Layout(
        border=f'1px solid {EPO_COLORS["light_gray"]}',
        border_radius='4px',
        padding='10px'
    ))
