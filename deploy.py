import functools
import os
from typing import Optional

import requests
from pyinfra import host
from pyinfra.facts.files import Directory, File, Link
from pyinfra.facts.server import Home, User
from pyinfra.operations import apt, files, git, server

from operations import gsettings, snap

with_sudo = {"sudo": True, "use_sudo_password": True}
username = host.get_fact(User)
home = functools.partial(os.path.join, host.get_fact(Home))


server.shell(name="Enable firewall", commands=["ufw enable"], **with_sudo)

if host.get_fact(File, path="/etc/default/motd-news"):
    files.line(
        name="Disable dynamic MOTD news service",
        path="/etc/default/motd-news",
        line="ENABLED=1",
        replace="ENABLED=0",
        **with_sudo,
    )

apt.key(
    name="Add Tarsnap package signing key",
    src="https://pkg.tarsnap.com/tarsnap-deb-packaging-key.asc",
    **with_sudo,
)

# TODO(srstevenson): Restore when Tarsnap repository is available for Hirsute.
# release_codename = host.get_fact(LsbRelease)["codename"]
release_codename = "groovy"

tarsnap_repo = apt.repo(
    name="Add Tarsnap package repository",
    src=f"deb https://pkg.tarsnap.com/deb/{release_codename} ./",
    filename="tarsnap",
    **with_sudo,
)

if tarsnap_repo.changed:
    apt.update(name="Update package indices", **with_sudo)

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
    **with_sudo,
)


def jump_deb_url() -> Optional[str]:
    response = requests.get(
        "https://api.github.com/repos/gsamokovarov/jump/releases/latest",
        headers={"Accept": "application/vnd.github.v3+json"},
    )
    response.raise_for_status()
    body = response.json()
    for asset in body["assets"]:
        if asset["name"].endswith("amd64.deb"):
            return asset["browser_download_url"]


apt.deb(name="Install jump from GitHub", src=jump_deb_url(), **with_sudo)


if not host.get_fact(Link, path="/usr/bin/fd"):
    server.shell(
        name="Install fd under its correct name",
        commands=[
            "dpkg-divert --local --divert /usr/bin/fd --rename --add /usr/bin/fdfind"
        ],
        **with_sudo,
    )

server.user(
    name="Set shell to zsh", user=username, shell="/usr/bin/zsh", **with_sudo
)

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
    **with_sudo,
)

files.line(
    name="Set kitty icon",
    path="/usr/share/applications/kitty.desktop",
    line="Icon=kitty",
    replace="Icon=terminal",
    **with_sudo,
)

server.shell(
    name="Set default terminal emulator to kitty",
    commands=["update-alternatives --set x-terminal-emulator /usr/bin/kitty"],
    **with_sudo,
)

files.template(
    name="Install local sudoers configuration",
    src="templates/sudoers.j2",
    dest="/etc/sudoers.d/local",
    mode="440",
    user="root",
    group="root",
    username=username,
    **with_sudo,
)

files.line(
    name="Enable dual mode Bluetooth",
    path="/etc/bluetooth/main.conf",
    line="#ControllerMode = dual",
    replace="ControllerMode = dual",
    **with_sudo,
)

files.sync(
    name="Install JetBrains Mono font",
    src="files/jetbrains-mono",
    dest=home(".local/share/fonts/jetbrains-mono"),
)

snap.package(name="Install starship snap", package="starship", **with_sudo)

if not host.get_fact(Directory, path=home(".local/pipx/venvs/pyinfra")):
    server.shell(
        name="Install pyinfra with pipx", commands=["pipx install pyinfra"]
    )

server.shell(
    name="Upgrade packages installed with pipx", commands=["pipx upgrade-all"]
)

if not host.get_fact(Directory, path=home(".poetry")):
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
    commands=[f"env RCRC={host.get_fact(Home)}/dotfiles/tag-rcm/rcrc rcup"],
)
