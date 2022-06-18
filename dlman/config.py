import mimetypes
from dataclasses import field, dataclass
from pathlib import Path
from typing import Optional

from marshmallow_dataclass import class_schema
from tomlkit import loads as tomlloads

mimetypes.init()
mimetypes.add_type('application/javascript', '.js')


@dataclass
class Config:
    name: Optional[str]
    url_prefix: Optional[str]
    route_prefix: Optional[str]


config_schema = class_schema(Config)()


def load(path):
    path = Path(path)
    data = tomlloads(path.read_text())
    return config_schema.load(data)