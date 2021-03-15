from pyinfra import api


@api.operation
def install(snap, state=None, host=None):
    if host.fact.directory(f"/snap/{snap}"):
        host.noop(f"{snap} snap is already installed")
    else:
        yield f"snap install {snap}"


@api.operation
def remove(snap, state=None, host=None):
    if not host.fact.directory(f"/snap/{snap}"):
        host.noop(f"{snap} snap is not installed")
    else:
        yield f"snap remove {snap}"
