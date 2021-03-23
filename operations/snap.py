from pyinfra import api


@api.operation
def package(package, present=True, state=None, host=None):
    is_present = host.fact.directory(f"/snap/{package}")

    if present and is_present:
        host.noop(f"{package} snap is installed")
    elif not present and not is_present:
        host.noop(f"{package} snap is not installed")
    else:
        verb = "install" if present else "remove"
        yield f"snap {verb} {package}"
