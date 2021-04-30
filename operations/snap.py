from pyinfra import api
from pyinfra.facts.files import Directory


@api.operation
def package(package, present=True, state=None, host=None):
    is_present = host.get_fact(Directory, path=f"/snap/{package}")

    if present and is_present:
        host.noop(f"{package} snap is installed")
    elif not present and not is_present:
        host.noop(f"{package} snap is not installed")
    else:
        verb = "install" if present else "remove"
        yield f"snap {verb} {package}"
