from typing import TypeAlias

from riag import Connection, Database

ConnDB: TypeAlias = tuple[Connection, Database]
