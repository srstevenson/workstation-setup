import os

from pyinfra import host
from pyinfra.operations import apt, files, server

from operations import gsettings, snap

USE_SUDO_PASSWORD = True

is_headless = not host.fact.file("/usr/bin/Xwayland")

if host.fact.file("/etc/default/motd-news"):
    files.line(
        name="Disable dynamic MOTD news service",
        path="/etc/default/motd-news",
        line="ENABLED=1",
        replace="ENABLED=0",
        sudo=True,
    )

release_codename = host.fact.lsb_release["codename"]

apt.key(
    name="Add Tarsnap package signing key",
    src="https://pkg.tarsnap.com/tarsnap-deb-packaging-key.asc",
    sudo=True,
)

tarsnap_repo = apt.repo(
    name="Add Tarsnap package repository",
    src=f"deb http://pkg.tarsnap.com/deb/{release_codename} ./",
    filename="tarsnap",
    sudo=True,
)

if tarsnap_repo.changed:
    apt.update(name="Update package indices")

apt.packages(
    name="Install system packages",
    update=True,
    cache_time=3600,
    upgrade=True,
    packages=[
        "black",
        "fd-find",
        "flake8",
        "git",
        "mypy",
        "neovim",
        "pipx",
        "pylint",
        "rcm",
        "restic",
        "ripgrep",
        "shellcheck",
        "tarsnap",
        "tmux",
        "zsh",
    ],
    sudo=True,
)

if not host.fact.file("/usr/bin/fd"):
    server.shell(
        name="Install fd under its correct name",
        commands=[
            "dpkg-divert --local --divert /usr/bin/fd --rename --add /usr/bin/fdfind"
        ],
        sudo=True,
    )

server.user(
    name="Set shell to zsh",
    user=host.fact.user,
    shell="/usr/bin/zsh",
    sudo=True,
)

if not is_headless:
    apt.packages(
        name="Install system packages for workstations",
        update=True,
        cache_time=3600,
        upgrade=True,
        packages=["anki", "calibre", "ddcutil", "gnome-tweaks", "keepassxc"],
        sudo=True,
    )

    files.template(
        name="Install local sudoers configuration",
        src="templates/sudoers.j2",
        dest="/etc/sudoers.d/local",
        mode="440",
        user="root",
        group="root",
        sudo=True,
        username=host.fact.user,
    )

    files.line(
        name="Enable dual mode Bluetooth",
        path="/etc/bluetooth/main.conf",
        line="#ControllerMode = dual",
        replace="ControllerMode = dual",
        sudo=True,
    )

snap.remove(name="Remove lxd snap", snap="lxd", sudo=True)

snap.install(name="Install starship snap", snap="starship", sudo=True)

if not host.fact.directory(
    os.path.join(host.fact.home, ".local/pipx/venvs/pyinfra")
):
    server.shell(
        name="Install pyinfra with pipx", commands=["pipx install pyinfra"]
    )

server.shell(
    name="Upgrade packages installed with pipx", commands=["pipx upgrade-all"]
)

if not is_headless:
    for path in ["autohide", "dock-fixed", "intellihide"]:
        gsettings.set(
            name="Permanently hide dock",
            schema="org.gnome.shell.extensions.dash-to-dock",
            path=path,
            key="false",
        )
