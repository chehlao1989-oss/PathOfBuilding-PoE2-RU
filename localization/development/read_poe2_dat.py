from pathlib import Path
import re
from struct import unpack_from


WORK = Path(__file__).resolve().parent
BALANCE = WORK / "PoE2-game-extract" / "data" / "balance"
SCHEMA = (WORK / "upstream-downloads" / "reference" / "spec.lua").read_text(encoding="utf-8")
TYPES = {
    "Bool": 1, "Int": 4, "UInt": 4, "UInt16": 2, "Float": 4, "Enum": 4,
    "Interval": 8, "String": 8, "ShortKey": 8, "Key": 16,
}
SCALARS = {"Bool": "<?", "Int": "<i", "UInt": "<I", "UInt16": "<H", "Enum": "<i"}


def layout(table):
    block = re.search(rf"\n\t{re.escape(table)}=\{{(.*?)\n\t\}},?", SCHEMA, re.S)
    if not block:
        raise ValueError(f"No schema for {table}")
    offsets = {}
    offset = 0
    for is_list, key, kind in re.findall(
        r'list=(true|false),\s*name="([^"]*)",\s*refTo="[^"]*",\s*type="([^"]+)"', block[1]
    ):
        offsets[key] = offset, kind, is_list == "true"
        offset += 16 if is_list == "true" else TYPES[kind]
    return offsets


def read_rows(table, columns, language=None):
    schema = layout(table)
    path = (BALANCE / language if language else BALANCE) / f"{table}.datc64"
    file = path.read_bytes()
    row_count = unpack_from("<I", file)[0]
    marker = file.find(b"\xbb" * 8, 4)
    row_size, remainder = divmod(marker - 4, row_count)
    if marker < 0 or remainder or row_size <= 0:
        raise ValueError(f"Invalid DAT row layout: {path}")

    def string_at(offset):
        start = marker + offset
        if not marker <= start < len(file) - 1:
            raise ValueError(f"Invalid string offset {offset} in {path}")
        end = file.index(b"\x00\x00", start)
        while (end - start) % 2:
            end = file.index(b"\x00\x00", end + 1)
        return file[start:end].decode("utf-16-le")

    def scalar_at(kind, pos):
        if kind == "String":
            return string_at(unpack_from("<Q", file, pos)[0])
        if kind == "Interval":
            return unpack_from("<ii", file, pos)
        if kind in ("Key", "ShortKey"):
            return unpack_from("<Q", file, pos)[0]
        return unpack_from(SCALARS[kind], file, pos)[0]

    for row in range(row_count):
        fields = {}
        for key in columns:
            offset, kind, is_list = schema[key]
            if offset + (16 if is_list else TYPES[kind]) > row_size:
                raise ValueError(f"{table}.{key} exceeds row size {row_size}")
            pos = 4 + row * row_size + offset
            if is_list:
                count, start = unpack_from("<QQ", file, pos)
                if count > len(file) // TYPES[kind] or (count and marker + start + count * TYPES[kind] > len(file)):
                    raise ValueError(f"Invalid list for {table}.{key}, row {row}")
                fields[key] = [scalar_at(kind, marker + start + i * TYPES[kind]) for i in range(count)]
            else:
                fields[key] = scalar_at(kind, pos)
        yield fields
