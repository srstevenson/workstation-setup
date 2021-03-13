from pyinfra import api


class GsettingsKey(api.FactBase):
    def command(self, schema, path):
        return f"gsettings get {schema} {path}"


@api.operation
def set(schema, path, key, state=None, host=None):
    if host.fact.gsettings_key(schema, path) == key:
        host.noop(f"{schema} {path} already set to {key}")
    else:
        yield f"gsettings set {schema} {path} {key}"
