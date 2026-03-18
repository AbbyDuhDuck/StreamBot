#! /usr/bin/env python3

# managing storing general stream data and global values

"""
Single sentence description.

This package provides functionality for... [TODO - add description] 

Modules & Subpackages:
----------------------
- TODO

Usage:
------
TODO
"""

# -=-=- Imports & Globals -=-=- #

from dataclasses import dataclass, field
import enum
from typing import Any, Callable

from .. import ConfigClass, configclass, BaseService, serviceclass
from ...signals import EventBus, EventData, QueryBus, QueryData, Response
import asyncio

import sqlite3
import datetime


TABLE_USERS = "USERS"
TABLE_EVENTS = "EVENTS"
COLUMN_USER_ID = "user_id"
COLUMN_EVENT_ID = "event_id"

SCHEMA:dict[str, dict[str, tuple]] = {
    TABLE_USERS: {
        COLUMN_USER_ID: ("TEXT", None, "PK"),   # primary key        
        # "grapes": ("INTEGER", 0),
    },
    TABLE_EVENTS: {
        COLUMN_EVENT_ID: ("INTEGER", None, "PK", "INC"), # primary key        
        "event_type": ("TEXT", None),
        "event_data": ("TEXT", "{}")   # JSON data
    },
}

# -=-=- Functions & Classes -=-=- #

def infer_schema(value:Any) -> tuple[str, Any]:
    if isinstance(value, bool):
        return ("BOOL", 0)

    if isinstance(value, int):
        return ("INTEGER", None)

    if isinstance(value, float):
        return ("REAL", None)

    # if isinstance(value, (dict, list)):
    #     return ("JSON", {})

    if isinstance(value, datetime.date):
        return ("DATE", None)
    
    if isinstance(value, datetime.datetime):
        return ("DATETIME", None)

    if isinstance(value, str):
        return ("TEXT", None)

    if value is None:
        return ("TEXT", None)

    return ("TEXT", None)


def coerce_from_db(key:str, value:Any, schema: dict) -> tuple[Any, tuple]:
    """
    Returns:
        coerced_value, (col_type, default)
    """
    # --- ensure schema exists ---
    if key not in schema: schema[key] = infer_schema(value)
    column_schema = schema[key]
    ctype, default = column_schema[:2]
    # -=-=- #
    if value is None: value = default

    # --- INTEGER ---
    if ctype == "INTEGER":
        if value is None: return None, column_schema
        return int(value), column_schema
    
    if ctype == "BOOL":
        return bool(value), column_schema

    if ctype == "DATE":
        if value is None: return None, column_schema
        int_value = int(value)
        if isinstance(value, datetime.date):
            return datetime.datetime.fromtimestamp(int_value).date, column_schema

    if ctype == "DATETIME":
        if value is None: return None, column_schema
        int_value = int(value)
        # datetime detection via default type
        if isinstance(value, datetime.datetime):
            return datetime.datetime.fromtimestamp(int_value), column_schema

    # --- REAL ---
    if ctype == "REAL":
        if value is None: return None, column_schema
        return float(value), column_schema

    # --- TEXT ---
    if ctype == "TEXT":
        if value is None: return None, column_schema
        return str(value), column_schema

    # # --- JSON ---
    # if ctype == "JSON":
    #     if isinstance(value, str):
    #         return json.loads(value), column_schema
    #     return value, column_schema
    

    return value, column_schema


def coerce_to_db(key:str, value:Any, schema: dict[str, tuple]) -> tuple[Any, tuple]:
    """
    Returns:
        coerced_value, (col_type, default)
    """
    # --- ensure schema exists ---
    if key not in schema: schema[key] = infer_schema(value)
    column_schema = schema[key]
    ctype, _default = column_schema[:2]
    # -=-=- #
    if value is None: return None, column_schema

    # --- INTEGER ---
    if ctype == "INTEGER":
        if isinstance(value, (datetime.datetime, datetime.date)):
            return int(value.timestamp()), column_schema
        return int(value), column_schema

    # --- REAL ---
    if ctype == "REAL":
        return float(value), column_schema

    # --- TEXT ---
    if ctype == "TEXT":
        return str(value), column_schema

    # # --- JSON ---
    # if ctype == "JSON":
    #     return json.dumps(value), column_schema

    return value, column_schema

# -=-=- # 

def get_column_schema(column:tuple) -> str:
    ctype, default = column[:2]
    pk = "PRIMARY KEY " if len(column) > 2 and "PK" in column[2:] else ""
    ai = "AUTOINCREMENT " if len(column) > 2 and "INC" in column[2:] else ""
    df = f"DEFAULT {repr(default)} " if default is not None else ""
    # -=-=- #
    if pk and df: 
        print("Cannot make column schema Primary key and provide a default")
        return f"{ctype}"
    # -=-=- #
    return f"{ctype} {pk}{ai}{df}"

def get_where_clause(where:dict|None) -> tuple[str, list]:
    if where:
        where_clause = " AND ".join(f"{k} = ?" for k in where)
        values = tuple(where.values())
        return f"WHERE {where_clause}", values
    # -=-=- #
    return f"", ()

# -=-=- Config Class -=-=- #

@configclass
class DataConfig(ConfigClass):
    path: str

# -=-=- Data Classes -=-=- #

@dataclass
class UserValueData(EventData, QueryData):
    user_id: str
    key: str|None = None
    value: Any|None = None
    default: Any|None = None

@dataclass
class TableColumnData(QueryData):
    table: str
    column: str|None = None
    where: dict|None = field(default_factory=None)
     
@dataclass
class TableValueData(EventData):
    table: str
    values: dict
    where: dict|None = field(default_factory=None)
    ignore:bool = True


class DataResponse(Response):
    value:Any|None
    row:dict|None


# -=-=- Service Class -=-=- #

@serviceclass("data")
class DataService(BaseService[DataConfig]):
    connection:sqlite3.Connection
    cursor:sqlite3.Cursor

    async def start(self):
        # print(f"Starting Data Service")
        self.connection = sqlite3.connect(self.config.path, check_same_thread=False)
        self.cursor = self.connection.cursor()
        self._enforce_schema()

    async def stop(self):
        # print("Stopping Data Service")
        self.cursor.close()
        self.connection.close()
    
    # -=-=- #

    def __register_events__(self, event_bus):
        event_bus.register("DataSetUserValue", self.event_set_user_value)
        
        event_bus.register("DatabaseUpdate", self.event_db_update)
        event_bus.register("DatabaseInsert", self.event_db_insert)
        
    def __register_queries__(self, query_bus):
        query_bus.register("DataGetUserValue", self.query_get_user_value)
        query_bus.register("DataGetUserData", self.query_get_user_data)
        
        query_bus.register("DatabaseGetOne", self.query_db_get_one)
        query_bus.register("DatabaseGetRow", self.query_db_get_row)
        query_bus.register("DatabaseGetAll", self.query_db_get_all)

    # -=-=- #

    def _enforce_schema(self):
        for table in SCHEMA:
            self._enforce_table_schema(table, SCHEMA[table])

    def _enforce_table_schema(self, table:str, table_schema:dict[str, tuple]):
        # Create table if not exists
        col_defs = []
        for column, schema in table_schema.items():
            col_defs.append(f"{column} {get_column_schema(schema)}")
        # -=-=- #
        self.cursor.execute(f"CREATE TABLE IF NOT EXISTS {table} ({', '.join(col_defs)})")
        
        # Ensure all required columns exist
        self.cursor.execute(f"PRAGMA table_info({table})")
        existing_columns = {row[1] for row in self.cursor.fetchall()}
        for column, schema in table_schema.items():
            if column not in existing_columns:
                self.cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {get_column_schema(schema)}")
        self.connection.commit()

    def _enforce_column_schema(self, table:str, column:str, schema:tuple):
        self.cursor.execute(f"PRAGMA table_info({table})")
        existing_columns = {row[1] for row in self.cursor.fetchall()}
        if column not in existing_columns:
            self.cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {get_column_schema(schema)}")
            self.connection.commit()
            return True
        return False
            
    # -=-=- #

    def _enforce_exists_user(self, user_id:str):
        """Create the user if they don't exist."""
        self.cursor.execute(f"SELECT 1 FROM {TABLE_USERS} WHERE {COLUMN_USER_ID} = ?", (user_id,))
        if not self.cursor.fetchone(): self.create_user(user_id)

    def create_user(self, user_id:str, **kwargs):
        schema = SCHEMA[TABLE_USERS]
        # -=-=- #
        values = {
            col: (user_id if col == COLUMN_USER_ID else kwargs.get(col, default))
            for col, (_, default, *__) in schema.items()
        }
        # -=-=- #
        columns = ", ".join(values.keys())
        placeholders = ", ".join("?" for _ in values)
        self.cursor.execute(
            f"INSERT OR IGNORE INTO {TABLE_USERS} ({columns}) VALUES ({placeholders})",
            tuple(values.values()),
        )
        self.connection.commit()

    # -=-=- #

    def get_user_value(self, user_id:str, key:str, default:Any):
        value, schema = coerce_from_db(key, default, SCHEMA[TABLE_USERS])
        self._enforce_column_schema(TABLE_USERS, key, schema)
        # -=-=- #
        self._enforce_exists_user(user_id)
        resp = self.db_get_one(TABLE_USERS, key, where={COLUMN_USER_ID: user_id})
        if resp is not None: return resp
        # -=-=- #
        if value is not None: 
            self.set_user_value(user_id, key, value)
            return value

    def set_user_value(self, user_id:str, key:str, value:Any):
        value, schema = coerce_to_db(key, value, SCHEMA[TABLE_USERS])
        self._enforce_column_schema(TABLE_USERS, key, schema)
        # -=-=- #
        self._enforce_exists_user(user_id)
        self.db_update(TABLE_USERS, {key: value}, where={COLUMN_USER_ID: user_id})
        self.connection.commit()

    def get_user_data(self, user_id:str):
        """Return all data for the user as a dict."""
        self._enforce_exists_user(user_id)
        return self.db_get_row(TABLE_USERS, where={COLUMN_USER_ID: user_id}) or {}

    # -=-=- #

    def db_get_one(self, table: str, column: str, where:dict|None=None):
        where_clause, values = get_where_clause(where)
        self.cursor.execute(f"SELECT {column} FROM {table} {where_clause}", values)
        row = self.cursor.fetchone()
        return row[0] if row else None

    def db_get_row(self, table: str, where:dict|None=None) -> dict | None:
        where_clause, values = get_where_clause(where)
        self.cursor.execute(f"SELECT * FROM {table} {where_clause}", values)
        row = self.cursor.fetchone()
        if not row: return None
        # -=-=- #
        col_names = [desc[0] for desc in self.cursor.description]
        return dict(zip(col_names, row))
    
    def db_get_all(self, table:str, where:dict|None=None):
        where_clause, values = get_where_clause(where)
        self.cursor.execute(f"SELECT * FROM {table} {where_clause}", values)
        rows = self.cursor.fetchall()
        # -=-=- #
        col_names = [desc[0] for desc in self.cursor.description]
        return [dict(zip(col_names, row)) for row in rows]


    def db_update(self, table: str, values: dict, where:dict|None=None):
        set_clause = ", ".join(f"{k} = ?" for k in values)
        where_clause, where_values = get_where_clause(where)
        # -=-=- #
        params = tuple(values.values()) + tuple(where_values)
        self.cursor.execute(f"UPDATE {table} SET {set_clause} {where_clause}", params)

    def db_insert(self, table: str, values: dict, ignore=True):
        cols = ", ".join(values.keys())
        placeholders = ", ".join("?" for _ in values)
        # -=-=- #
        cmd = "INSERT OR IGNORE" if ignore else "INSERT"
        self.cursor.execute(f"{cmd} INTO {table} ({cols}) VALUES ({placeholders})", tuple(values.values()))

    # -=-=- Events -=-=- #

    async def query_get_user_value(self, data:UserValueData) -> DataResponse:
        resp = self.get_user_value(data.user_id, data.key, data.default if data.default is not None else data.value)
        return DataResponse(resp, value=resp)

    async def event_set_user_value(self, data:UserValueData):
        self.set_user_value(data.user_id, data.key, data.value if data.value is not None else data.default)

    async def query_get_user_data(self, data:UserValueData) -> DataResponse:
        resp = self.get_user_data(data.user_id)
        return DataResponse(resp, row=resp)

    async def query_db_get_one(self, data:TableColumnData) -> DataResponse:
        resp = self.db_get_one(data.table, data.column, data.where)
        return DataResponse(resp, value=resp)

    async def query_db_get_row(self, data:TableColumnData) -> DataResponse:
        resp = self.db_get_row(data.table, data.where)
        return DataResponse(resp, row=resp)

    async def query_db_get_all(self, data:TableColumnData) -> DataResponse:
        resp = self.db_get_all(data.table, data.where)
        return DataResponse(resp, row=resp)

    async def event_db_update(self, data:TableValueData):
        self.db_update(data.table, data.values, data.where)

    async def event_db_insert(self, data:TableValueData):
        self.db_insert(data.table, data.values, data.ignore)

# EOF #
