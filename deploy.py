import functools
import os

import requests
from pyinfra import host
from pyinfra.operations import apt, files, git, server

from operations import gsettings, snap

USE_SUDO_PASSWORD = True


home = functools.partial(os.path.join, host.fact.home)


is_headless = not host.fact.file("/usr/bin/Xwayland")

if is_headless:
    server.shell(
        name="Allow incoming SSH traffic",
        commands=["ufw allow ssh"],
        sudo=True,
    )

server.shell(name="Enable firewall", commands=["ufw enable"], sudo=True)

if host.fact.file("/etc/default/motd-news"):
    files.line(
        name="Disable dynamic MOTD news service",
        path="/etc/default/motd-news",
        line="ENABLED=1",
        replace="ENABLED=0",
        sudo=True,
    )

apt.key(
    name="Add Tarsnap package signing key",
    src="https://pkg.tarsnap.com/tarsnap-deb-packaging-key.asc",
    sudo=True,
)

# TODO(srstevenson): Restore when Tarsnap repository is available for Hirsute.
# release_codename = host.fact.lsb_release["codename"]
release_codename = "groovy"

tarsnap_repo = apt.repo(
    name="Add Tarsnap package repository",
    src=f"deb http://pkg.tarsnap.com/deb/{release_codename} ./",
    filename="tarsnap",
    sudo=True,
)

if tarsnap_repo.changed:
    apt.update(name="Update package indices", sudo=True)

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
        "htop",
        "ipython3",
        "isort",
        "mypy",
        "neovim",
        "npm",
        "pipx",
        "pylint",
        "python3",
        "rcm",
        "restic",
        "ripgrep",
        "shellcheck",
        "tarsnap",
        "tmux",
        "tree",
        "zsh",
    ],
    sudo=True,
)


def jump_deb_url() -> str:
    response = requests.get(
        "https://api.github.com/repos/gsamokovarov/jump/releases/latest",
        headers={"Accept": "application/vnd.github.v3+json"},
    )
    response.raise_for_status()
    body = response.json()
    for asset in body["assets"]:
        if asset["name"].endswith("amd64.deb"):
            return asset["browser_download_url"]


apt.deb(name="Install jump from GitHub", src=jump_deb_url(), sudo=True)


if not host.fact.link("/usr/bin/fd"):
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
        packages=[
            "anki",
            "calibre",
            "ddcutil",
            "gnome-tweaks",
            "keepassxc",
            "kitty",
            "wl-clipboard",
        ],
        sudo=True,
    )

    files.line(
        name="Set kitty icon",
        path="/usr/share/applications/kitty.desktop",
        line="Icon=kitty",
        replace="Icon=terminal",
        sudo=True,
    )

    server.shell(
        name="Set default terminal emulator to kitty",
        commands=[
            "update-alternatives --set x-terminal-emulator /usr/bin/kitty"
        ],
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

    files.sync(
        name="Install JetBrains Mono font",
        src="files/jetbrains-mono",
        dest=home(".local/share/fonts/jetbrains-mono"),
    )

snap.package(name="Remove lxd snap", package="lxd", present=False, sudo=True)

snap.package(name="Install starship snap", package="starship", sudo=True)

if not host.fact.directory(home(".local/pipx/venvs/pyinfra")):
    server.shell(
        name="Install pyinfra with pipx", commands=["pipx install pyinfra"]
    )

server.shell(
    name="Upgrade packages installed with pipx", commands=["pipx upgrade-all"]
)

if not host.fact.directory(home(".poetry")):
    files.download(
        name="Download Poetry installer",
        src="https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py",
        dest="/tmp/get-poetry.py",
    )

    server.shell(
        name="Install Poetry",
        commands=["/usr/bin/python3 /tmp/get-poetry.py --no-modify-path"],
    )

server.shell(name="Upgrade Poetry", commands=["poetry self update"])

if not is_headless:
    gsettings.set(
        name="Map CapsLock to Ctrl",
        schema="org.gnome.desktop.input-sources",
        path="xkb-options",
        key="['ctrl:nocaps']",
    )

    gsettings.set(
        name="Enable natural scrolling for mouse",
        schema="org.gnome.desktop.peripherals.mouse",
        path="natural-scroll",
        key="true",
    )

    for path in ["autohide", "dock-fixed", "intellihide"]:
        gsettings.set(
            name="Permanently hide dock",
            schema="org.gnome.shell.extensions.dash-to-dock",
            path=path,
            key="false",
        )

git.repo(
    name="Clone dotfiles",
    src="https://github.com/srstevenson/dotfiles.git",
    dest=home("dotfiles"),
    branch="main",
    pull=False,
)

server.shell(
    name="Install dotfiles",
    commands=[f"env RCRC={host.fact.home}/dotfiles/tag-rcm/rcrc rcup"],
)
