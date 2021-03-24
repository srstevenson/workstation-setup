from pyinfra import api

import facts.gsettings  # noqa


@api.operation
def set(schema, path, key, state=None, host=None):
    if host.fact.gsettings_key(schema, path) == key:
        host.noop(f"{schema} {path} already set to {key}")
    else:
        yield f"gsettings set {schema} {path} {key}"
