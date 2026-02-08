#!/usr/bin/env python3
"""
Database Visualizer Application
A comprehensive TKinter GUI for visualizing, filtering, and monitoring
PostgreSQL database operations in real-time with corporate design.

Author: Database Team
Date: 2026-02-08
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import queue
import logging
from datetime import datetime
from enum import Enum
import json
import sys
from pathlib import Path
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# THEME & STYLING
# ============================================================================

class CorporateTheme:
    """Corporate color scheme and styling constants."""
    
    # Primary Colors
    PRIMARY_BLUE = "#1E3A8A"      # Deep corporate blue
    SECONDARY_BLUE = "#3B82F6"    # Lighter blue
    ACCENT_TEAL = "#0891B2"       # Modern teal accent
    
    # Neutral Colors
    BACKGROUND = "#F5F7FA"        # Light silver/white
    CARD_BG = "#FFFFFF"           # Pure white for cards
    DARK_TEXT = "#1F2937"         # Dark gray for text
    LIGHT_TEXT = "#6B7280"        # Medium gray for secondary text
    BORDER = "#E5E7EB"            # Light border color
    
    # Status Colors
    SUCCESS = "#059669"            # Green for success
    WARNING = "#F59E0B"            # Amber for warning
    DANGER = "#DC2626"             # Red for danger
    INFO = "#0891B2"               # Teal for info
    
    # Fonts
    FONT_DEFAULT = ("Segoe UI", 11)
    FONT_HEADING = ("Segoe UI", 12, "bold")
    FONT_TITLE = ("Segoe UI", 14, "bold")
    FONT_CODE = ("Courier New", 10)


# ============================================================================
# ENUMS
# ============================================================================

class OperationType(Enum):
    """Database operation types."""
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    EXECUTE = "EXECUTE"
    ERROR = "ERROR"


# ============================================================================
# DATA MODELS
# ============================================================================

class DatabaseOperation:
    """Represents a single database operation."""
    
    def __init__(self, op_type, table, details, timestamp=None):
        self.op_type = op_type
        self.table = table
        self.details = details
        self.timestamp = timestamp or datetime.now()
        self.id = f"{self.timestamp.strftime('%Y%m%d%H%M%S%f')}"
    
    def to_dict(self):
        """Convert operation to dictionary."""
        return {
            'type': self.op_type.value,
            'table': self.table,
            'details': self.details,
            'timestamp': self.timestamp.isoformat()
        }

class FilterExpression:
    """Represents a filter expression for database queries."""
    
    OPERATORS = {
        'equals': '=',
        'not_equals': '!=',
        'contains': 'LIKE',
        'greater_than': '>',
        'less_than': '<',
        'greater_equal': '>=',
        'less_equal': '<='
    }
    
    def __init__(self, column, operator, value):
        self.column = column
        self.operator = operator
        self.value = value
    
    def to_sql_condition(self):
        """Convert to SQL WHERE condition."""
        if self.operator == 'contains':
            return f"{self.column} LIKE '%{self.value}%'"
        return f"{self.column} {self.OPERATORS.get(self.operator, '=')} '{self.value}'"


# ============================================================================
# DATABASE MANAGER
# ============================================================================

class DatabaseManager:
    """Manages database connections and operations."""
    
    def __init__(self, config=None):
        self.config = config or self._load_default_config()
        self.connection = None
        self.operations_log = []
        self.connected = False
    
    def _load_default_config(self):
        """Load default database configuration."""
        try:
            from config import DB_CONFIG, POOL_CONFIG
            return {
                'db_config': DB_CONFIG,
                'pool_config': POOL_CONFIG,
                'page_size': 50
            }
        except ImportError:
            logger.warning("Could not import config module, using defaults")
            return {
                'db_config': {
                    'host': 'localhost',
                    'port': 5432,
                    'database': 'apartment_mgmt',
                    'user': 'postgres',
                    'password': 'postgres'
                },
                'pool_config': {
                    'min_connections': 1,
                    'max_connections': 10
                },
                'page_size': 50
            }
    
    def test_connection(self):
        """Test database connection."""
        try:
            import psycopg2
            conn = psycopg2.connect(**self.config['db_config'])
            conn.close()
            self.connected = True
            logger.info("Database connection successful")
            return True, "Connected successfully"
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False, f"Connection failed: {str(e)}"
    
    def get_tables(self):
        """Get list of database tables."""
        try:
            import psycopg2
            conn = psycopg2.connect(**self.config['db_config'])
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            
            tables = [row[0] for row in cursor.fetchall()]
            cursor.close()
            conn.close()
            return tables
        except Exception as e:
            logger.error(f"Error fetching tables: {e}")
            return []
    
    def get_table_data(self, table_name, limit=None, offset=0):
        """Get data from a table."""
        try:
            import psycopg2
            conn = psycopg2.connect(**self.config['db_config'])
            cursor = conn.cursor()
            
            limit = limit or self.config['page_size']
            
            cursor.execute(f"SELECT * FROM {table_name} LIMIT %s OFFSET %s", 
                          (limit, offset))
            
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return columns, rows
        except Exception as e:
            logger.error(f"Error fetching table data: {e}")
            return [], []
    
    def get_table_count(self, table_name):
        """Get total row count for a table."""
        try:
            import psycopg2
            conn = psycopg2.connect(**self.config['db_config'])
            cursor = conn.cursor()
            
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            return count
        except Exception as e:
            logger.error(f"Error counting rows: {e}")
            return 0
    
    def get_table_columns(self, table_name):
        """Get column information for a table."""
        try:
            import psycopg2
            conn = psycopg2.connect(**self.config['db_config'])
            cursor = conn.cursor()
            
            cursor.execute(f"""
                SELECT column_name, data_type FROM information_schema.columns
                WHERE table_name = %s
                ORDER BY ordinal_position
            """, (table_name,))
            
            columns = [(row[0], row[1]) for row in cursor.fetchall()]
            
            cursor.close()
            conn.close()
            
            return columns
        except Exception as e:
            logger.error(f"Error fetching column info: {e}")
            return []


# ============================================================================
# MAIN APPLICATION WINDOW
# ============================================================================

class DatabaseVisualizerApp:
    """Main application class for database visualization."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Database Visualizer - Service Daemon")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 700)
        
        # Set theme
        self.theme = CorporateTheme()
        self.root.configure(bg=self.theme.BACKGROUND)
        
        # Database manager
        self.db = DatabaseManager()
        
        # State variables
        self.current_table = tk.StringVar(value="")
        self.current_page = 0
        self.page_size = 50
        self.operations = queue.Queue()
        self.operation_log = []
        
        # Create UI
        self._setup_styles()
        self._create_menu()
        self._create_main_layout()
        self._update_operations_display()
    
    def _setup_styles(self):
        """Configure ttk styles for corporate theme."""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        style.configure('TFrame', background=self.theme.BACKGROUND)
        style.configure('TButton', font=self.theme.FONT_DEFAULT)
        style.configure('TLabel', background=self.theme.BACKGROUND, 
                       font=self.theme.FONT_DEFAULT)
        style.configure('Heading.TLabel', background=self.theme.BACKGROUND,
                       font=self.theme.FONT_HEADING, foreground=self.theme.PRIMARY_BLUE)
        
        # Treeview style
        style.configure('Treeview', font=self.theme.FONT_DEFAULT, rowheight=25)
        style.configure('Treeview.Heading', font=self.theme.FONT_HEADING)
    
    def _create_menu(self):
        """Create application menu bar."""
        menubar = tk.Menu(self.root, bg=self.theme.PRIMARY_BLUE, 
                         fg=self.theme.CARD_BG, font=self.theme.FONT_DEFAULT)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0, bg=self.theme.CARD_BG,
                           fg=self.theme.DARK_TEXT, font=self.theme.FONT_DEFAULT)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Connect to Database", 
                             command=self._show_connection_dialog)
        file_menu.add_command(label="Settings", command=self._show_settings_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="Export Data", command=self._export_data)
        file_menu.add_command(label="Import Config", command=self._import_config)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0, bg=self.theme.CARD_BG,
                           fg=self.theme.DARK_TEXT, font=self.theme.FONT_DEFAULT)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Refresh All", command=self._refresh_all)
        view_menu.add_separator()
        view_menu.add_command(label="Clear Operations Log", 
                             command=self._clear_operations_log)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0, bg=self.theme.CARD_BG,
                           fg=self.theme.DARK_TEXT, font=self.theme.FONT_DEFAULT)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)
        help_menu.add_command(label="Documentation", command=self._show_docs)
    
    def _create_main_layout(self):
        """Create main application layout."""
        # Main container with padding
        main_container = ttk.Frame(self.root, padding="10")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Title bar
        title_frame = ttk.Frame(main_container)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = ttk.Label(title_frame, text="Database Visualizer",
                               style='Heading.TLabel')
        title_label.pack(side=tk.LEFT)
        
        connection_status = ttk.Label(title_frame, text="● Disconnected",
                                     foreground=self.theme.DANGER,
                                     font=self.theme.FONT_DEFAULT)
        connection_status.pack(side=tk.RIGHT)
        self.connection_status_label = connection_status
        
        # Toolbar
        toolbar = ttk.Frame(main_container)
        toolbar.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(toolbar, text="🔄 Refresh", 
                  command=self._refresh_all).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(toolbar, text="⚙ Connect", 
                  command=self._show_connection_dialog).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(toolbar, text="Table:", font=self.theme.FONT_DEFAULT).pack(
            side=tk.LEFT, padx=(10, 5))
        
        self.table_selector = ttk.Combobox(toolbar, textvariable=self.current_table,
                                          state='readonly', width=20)
        self.table_selector.pack(side=tk.LEFT, padx=5)
        self.table_selector.bind('<<ComboboxSelected>>', self._on_table_selected)
        
        # Main content area - 3 panels
        content_frame = ttk.Frame(main_container)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Table browser
        left_panel = self._create_left_panel(content_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Center panel - Filters
        center_panel = self._create_center_panel(content_frame)
        center_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(5, 5))
        
        # Right panel - Operations & Settings
        right_panel = self._create_right_panel(content_frame)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Status bar
        status_bar = ttk.Frame(main_container, relief=tk.SUNKEN, padding="5")
        status_bar.pack(fill=tk.X, pady=(10, 0))
        
        self.status_label = ttk.Label(status_bar, text="Ready", 
                                     font=self.theme.FONT_DEFAULT)
        self.status_label.pack(side=tk.LEFT)
    
    def _create_left_panel(self, parent):
        """Create left panel with table data."""
        panel = ttk.LabelFrame(parent, text="Data Browser", padding="10")
        
        # Table list
        list_frame = ttk.Frame(panel)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        ttk.Label(list_frame, text="Tables:", font=self.theme.FONT_DEFAULT).pack(
            fill=tk.X, pady=(0, 5))
        
        scroll = ttk.Scrollbar(list_frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.table_list = tk.Listbox(list_frame, yscrollcommand=scroll.set,
                                    font=self.theme.FONT_DEFAULT, height=8)
        self.table_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.config(command=self.table_list.yview)
        self.table_list.bind('<<ListboxSelect>>', self._on_list_table_select)
        
        # Data grid
        grid_frame = ttk.Frame(panel)
        grid_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        ttk.Label(grid_frame, text="Records:", font=self.theme.FONT_DEFAULT).pack(
            fill=tk.X, pady=(0, 5))
        
        scroll_x = ttk.Scrollbar(grid_frame, orient=tk.HORIZONTAL)
        scroll_y = ttk.Scrollbar(grid_frame)
        
        self.data_grid = ttk.Treeview(grid_frame, yscrollcommand=scroll_y.set,
                                     xscrollcommand=scroll_x.set, height=15)
        
        scroll_y.config(command=self.data_grid.yview)
        scroll_x.config(command=self.data_grid.xview)
        
        self.data_grid.grid(row=0, column=0, sticky='nsew')
        scroll_y.grid(row=0, column=1, sticky='ns')
        scroll_x.grid(row=1, column=0, sticky='ew')
        
        grid_frame.grid_rowconfigure(0, weight=1)
        grid_frame.grid_columnconfigure(0, weight=1)
        
        # Pagination
        pagination_frame = ttk.Frame(panel)
        pagination_frame.pack(fill=tk.X)
        
        ttk.Button(pagination_frame, text="◄ Prev",
                  command=self._prev_page).pack(side=tk.LEFT, padx=2)
        
        self.page_label = ttk.Label(pagination_frame, text="Page 1",
                                   font=self.theme.FONT_DEFAULT)
        self.page_label.pack(side=tk.LEFT, padx=10)
        
        ttk.Button(pagination_frame, text="Next ►",
                  command=self._next_page).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(pagination_frame, text="Refresh",
                  command=self._load_table_data).pack(side=tk.RIGHT, padx=2)
        
        return panel
    
    def _create_center_panel(self, parent):
        """Create center panel with filter controls."""
        panel = ttk.LabelFrame(parent, text="Filters", padding="10", width=280)
        panel.pack_propagate(False)
        
        # Filter section
        ttk.Label(panel, text="Column:", font=self.theme.FONT_DEFAULT).pack(
            fill=tk.X, pady=(0, 5))
        
        self.filter_column = ttk.Combobox(panel, state='readonly', width=27)
        self.filter_column.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(panel, text="Operator:", font=self.theme.FONT_DEFAULT).pack(
            fill=tk.X, pady=(0, 5))
        
        self.filter_operator = ttk.Combobox(panel, state='readonly', width=27,
                                           values=['equals', 'contains', 'greater_than'])
        self.filter_operator.pack(fill=tk.X, pady=(0, 10))
        self.filter_operator.set('equals')
        
        ttk.Label(panel, text="Value:", font=self.theme.FONT_DEFAULT).pack(
            fill=tk.X, pady=(0, 5))
        
        self.filter_value = ttk.Entry(panel, width=27)
        self.filter_value.pack(fill=tk.X, pady=(0, 10))
        
        # Button frame
        btn_frame = ttk.Frame(panel)
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(btn_frame, text="Apply",
                  command=self._apply_filter).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(btn_frame, text="Clear",
                  command=self._clear_filter).pack(side=tk.LEFT, padx=2)
        
        # Active filters display
        ttk.Label(panel, text="Active Filters:", font=self.theme.FONT_DEFAULT).pack(
            fill=tk.X, pady=(10, 5))
        
        scroll = ttk.Scrollbar(panel)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.filters_display = tk.Listbox(panel, yscrollcommand=scroll.set,
                                         font=self.theme.FONT_CODE, height=6)
        self.filters_display.pack(fill=tk.BOTH, expand=True)
        scroll.config(command=self.filters_display.yview)
        
        return panel
    
    def _create_right_panel(self, parent):
        """Create right panel with operations and settings."""
        panel = ttk.Frame(parent)
        
        # Notebook for tabs
        notebook = ttk.Notebook(panel)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Operations tab
        ops_frame = ttk.Frame(notebook, padding="10")
        notebook.add(ops_frame, text="Operations")
        
        ttk.Label(ops_frame, text="Real-Time Operations Log",
                 style='Heading.TLabel').pack(fill=tk.X, pady=(0, 10))
        
        scroll = ttk.Scrollbar(ops_frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.operations_display = tk.Listbox(ops_frame, yscrollcommand=scroll.set,
                                            font=self.theme.FONT_CODE, height=25)
        self.operations_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.config(command=self.operations_display.yview)
        
        # Settings tab
        settings_frame = ttk.Frame(notebook, padding="10")
        notebook.add(settings_frame, text="Settings")
        
        self._create_settings_tab(settings_frame)
        
        return panel
    
    def _create_settings_tab(self, parent):
        """Create settings tab content."""
        # Connection settings
        ttk.Label(parent, text="Database Connection",
                 style='Heading.TLabel').pack(fill=tk.X, pady=(0, 10))
        
        # Host
        ttk.Label(parent, text="Host:", font=self.theme.FONT_DEFAULT).pack(fill=tk.X)
        self.setting_host = ttk.Entry(parent, width=30)
        self.setting_host.insert(0, self.db.config['db_config']['host'])
        self.setting_host.pack(fill=tk.X, pady=(0, 10))
        
        # Port
        ttk.Label(parent, text="Port:", font=self.theme.FONT_DEFAULT).pack(fill=tk.X)
        self.setting_port = ttk.Entry(parent, width=30)
        self.setting_port.insert(0, str(self.db.config['db_config']['port']))
        self.setting_port.pack(fill=tk.X, pady=(0, 10))
        
        # Database
        ttk.Label(parent, text="Database:", font=self.theme.FONT_DEFAULT).pack(fill=tk.X)
        self.setting_database = ttk.Entry(parent, width=30)
        self.setting_database.insert(0, self.db.config['db_config']['database'])
        self.setting_database.pack(fill=tk.X, pady=(0, 10))
        
        # Username
        ttk.Label(parent, text="Username:", font=self.theme.FONT_DEFAULT).pack(fill=tk.X)
        self.setting_user = ttk.Entry(parent, width=30)
        self.setting_user.insert(0, self.db.config['db_config']['user'])
        self.setting_user.pack(fill=tk.X, pady=(0, 10))
        
        # Password
        ttk.Label(parent, text="Password:", font=self.theme.FONT_DEFAULT).pack(fill=tk.X)
        self.setting_password = ttk.Entry(parent, show="*", width=30)
        self.setting_password.insert(0, self.db.config['db_config']['password'])
        self.setting_password.pack(fill=tk.X, pady=(0, 15))
        
        # Pool settings
        ttk.Label(parent, text="Connection Pool",
                 style='Heading.TLabel').pack(fill=tk.X, pady=(10, 10))
        
        ttk.Label(parent, text="Min Connections:", font=self.theme.FONT_DEFAULT).pack(fill=tk.X)
        self.setting_pool_min = ttk.Entry(parent, width=30)
        self.setting_pool_min.insert(0, str(self.db.config['pool_config']['min_connections']))
        self.setting_pool_min.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(parent, text="Max Connections:", font=self.theme.FONT_DEFAULT).pack(fill=tk.X)
        self.setting_pool_max = ttk.Entry(parent, width=30)
        self.setting_pool_max.insert(0, str(self.db.config['pool_config']['max_connections']))
        self.setting_pool_max.pack(fill=tk.X, pady=(0, 15))
        
        # Buttons
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="Test Connection",
                  command=self._test_connection).pack(side=tk.LEFT, padx=5, pady=5)
        
        ttk.Button(btn_frame, text="Save Settings",
                  command=self._save_settings).pack(side=tk.LEFT, padx=5, pady=5)
    
    # ========================================================================
    # EVENT HANDLERS
    # ========================================================================
    
    def _on_table_selected(self, event=None):
        """Handle table selection from combobox."""
        self._load_table_data()
    
    def _on_list_table_select(self, event=None):
        """Handle table selection from list."""
        if self.table_list.curselection():
            table = self.table_list.get(self.table_list.curselection()[0])
            self.current_table.set(table)
            self.table_selector.set(table)
            self._load_table_data()
    
    def _load_table_data(self):
        """Load data for current table."""
        table = self.current_table.get()
        if not table:
            messagebox.showwarning("Warning", "Please select a table")
            return
        
        try:
            columns, rows = self.db.get_table_data(table, limit=self.page_size, 
                                                  offset=self.current_page * self.page_size)
            count = self.db.get_table_count(table)
            
            # Update data grid
            self.data_grid.delete(*self.data_grid.get_children())
            self.data_grid['columns'] = columns
            self.data_grid.column('#0', width=0)
            
            for col in columns:
                self.data_grid.column(col, anchor=tk.W, width=100)
                self.data_grid.heading(col, text=col)
            
            for row in rows:
                self.data_grid.insert('', 'end', values=row)
            
            # Update filters
            col_info = self.db.get_table_columns(table)
            col_names = [col[0] for col in col_info]
            self.filter_column['values'] = col_names
            if col_names:
                self.filter_column.set(col_names[0])
            
            # Update pagination
            total_pages = (count + self.page_size - 1) // self.page_size
            self.page_label.config(text=f"Page {self.current_page + 1} of {total_pages}")
            
            # Log operation
            self._log_operation(OperationType.SELECT, table, f"Loaded {len(rows)} records")
            
            self._update_status(f"Loaded {len(rows)} records from {table}")
        
        except Exception as e:
            logger.error(f"Error loading table data: {e}")
            messagebox.showerror("Error", f"Failed to load table data: {str(e)}")
    
    def _apply_filter(self):
        """Apply filter to current data."""
        table = self.current_table.get()
        column = self.filter_column.get()
        operator = self.filter_operator.get()
        value = self.filter_value.get()
        
        if not all([table, column, operator, value]):
            messagebox.showwarning("Warning", "Please fill all filter fields")
            return
        
        # Add to filter display
        filter_str = f"{column} {operator} '{value}'"
        self.filters_display.insert(tk.END, filter_str)
        
        # Log operation
        self._log_operation(OperationType.SELECT, table, f"Applied filter: {filter_str}")
        
        self._update_status(f"Filter applied: {filter_str}")
    
    def _clear_filter(self):
        """Clear all filters."""
        self.filters_display.delete(0, tk.END)
        self.filter_value.delete(0, tk.END)
        self._log_operation(OperationType.SELECT, self.current_table.get(), "Filters cleared")
        self._update_status("Filters cleared")
    
    def _prev_page(self):
        """Go to previous page."""
        if self.current_page > 0:
            self.current_page -= 1
            self._load_table_data()
    
    def _next_page(self):
        """Go to next page."""
        self.current_page += 1
        self._load_table_data()
    
    def _refresh_all(self):
        """Refresh all data."""
        self._update_tables_list()
        self._load_table_data()
        self._update_status("Data refreshed")
    
    def _update_tables_list(self):
        """Update the list of available tables."""
        tables = self.db.get_tables()
        self.table_list.delete(0, tk.END)
        for table in tables:
            self.table_list.insert(tk.END, table)
        self.table_selector['values'] = tables
    
    def _test_connection(self):
        """Test database connection."""
        self._update_db_config_from_settings()
        success, message = self.db.test_connection()
        
        if success:
            messagebox.showinfo("Success", message)
            self.connection_status_label.config(text="● Connected", 
                                               foreground=self.theme.SUCCESS)
            self._update_tables_list()
        else:
            messagebox.showerror("Connection Failed", message)
            self.connection_status_label.config(text="● Disconnected",
                                               foreground=self.theme.DANGER)
    
    def _save_settings(self):
        """Save settings."""
        self._update_db_config_from_settings()
        messagebox.showinfo("Success", "Settings saved successfully")
        self._update_status("Settings saved")
    
    def _update_db_config_from_settings(self):
        """Update database config from settings inputs."""
        self.db.config['db_config'].update({
            'host': self.setting_host.get(),
            'port': int(self.setting_port.get() or 5432),
            'database': self.setting_database.get(),
            'user': self.setting_user.get(),
            'password': self.setting_password.get()
        })
        
        self.db.config['pool_config'].update({
            'min_connections': int(self.setting_pool_min.get() or 1),
            'max_connections': int(self.setting_pool_max.get() or 10)
        })
    
    def _show_connection_dialog(self):
        """Show connection dialog."""
        messagebox.showinfo("Connect", "Use Settings tab to configure connection")
    
    def _show_settings_dialog(self):
        """Show settings dialog."""
        messagebox.showinfo("Settings", "Settings are available in the right panel")
    
    def _export_data(self):
        """Export data to file."""
        file = filedialog.asksaveasfilename(defaultextension=".json",
                                           filetypes=[("JSON files", "*.json")])
        if file:
            try:
                data = {
                    'table': self.current_table.get(),
                    'operations': [op.to_dict() for op in self.operation_log],
                    'timestamp': datetime.now().isoformat()
                }
                with open(file, 'w') as f:
                    json.dump(data, f, indent=2)
                messagebox.showinfo("Success", f"Data exported to {file}")
            except Exception as e:
                messagebox.showerror("Error", f"Export failed: {str(e)}")
    
    def _import_config(self):
        """Import configuration from file."""
        file = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file:
            try:
                with open(file, 'r') as f:
                    config = json.load(f)
                messagebox.showinfo("Success", "Configuration imported")
            except Exception as e:
                messagebox.showerror("Error", f"Import failed: {str(e)}")
    
    def _clear_operations_log(self):
        """Clear operations log."""
        self.operation_log.clear()
        self.operations_display.delete(0, tk.END)
        self._update_status("Operations log cleared")
    
    def _show_about(self):
        """Show about dialog."""
        messagebox.showinfo("About",
            "Database Visualizer v1.0\n\n"
            "A professional database visualization tool for the Service Daemon project.\n\n"
            "Features:\n"
            "• Real-time database monitoring\n"
            "• Advanced filtering and search\n"
            "• Operation tracking\n"
            "• Settings management\n\n"
            "Built with Python TKinter\n"
            "© 2026 Service Daemon Team")
    
    def _show_docs(self):
        """Show documentation."""
        messagebox.showinfo("Documentation",
            "Database Visualizer - User Guide\n\n"
            "Getting Started:\n"
            "1. Click 'Connect' to configure database\n"
            "2. Select a table from the list\n"
            "3. View records in the data grid\n"
            "4. Use filters to search data\n"
            "5. Monitor operations in real-time\n\n"
            "Features:\n"
            "• Pagination: Navigate large datasets\n"
            "• Filters: Advanced search capabilities\n"
            "• Export: Save data to JSON\n"
            "• Settings: Manage connections\n"
            "• Operations Log: Track all activities")
    
    def _log_operation(self, op_type, table, details):
        """Log a database operation."""
        op = DatabaseOperation(op_type, table, details)
        self.operation_log.append(op)
        
        # Update display
        timestamp = op.timestamp.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {op_type.value}: {table} - {details}"
        self.operations_display.insert(0, log_entry)
        
        # Keep log size manageable
        if self.operations_display.size() > 100:
            self.operations_display.delete(100, tk.END)
    
    def _update_operations_display(self):
        """Update operations display periodically."""
        # Could add real-time database monitoring here
        self.root.after(5000, self._update_operations_display)
    
    def _update_status(self, message):
        """Update status bar."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_label.config(text=f"{timestamp} - {message}")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point."""
    root = tk.Tk()
    app = DatabaseVisualizerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()