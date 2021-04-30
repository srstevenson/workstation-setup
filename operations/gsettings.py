from pyinfra import api

from facts.gsettings import GsettingsKey


@api.operation
def set(schema, path, key, state=None, host=None):
    if host.get_fact(GsettingsKey, schema=schema, path=path) == key:
        host.noop(f"{schema} {path} already set to {key}")
    else:
        yield f"gsettings set {schema} {path} {key}"
