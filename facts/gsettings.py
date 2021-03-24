from pyinfra import api


class GsettingsKey(api.FactBase):
    def command(self, schema, path):
        return f"gsettings get {schema} {path}"
