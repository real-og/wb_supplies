import json, os, tempfile


def write_atomic_json(path: str, data: dict):
    d = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(dir=d, prefix="cfg_", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)  # атомарно
    finally:
        try: os.unlink(tmp)
        except FileNotFoundError: pass


def update_key(key: str, value: str, path: str = "config.json"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}
    data[key] = value
    write_atomic_json(path, data)


def get_value(key: str, path: str = "config.json", default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get(key, default)
    except FileNotFoundError:
        return default
    except json.JSONDecodeError:
        return default