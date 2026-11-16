#!/usr/bin/env python3
"""
Entrypoint for the Buildozer GitHub Action (fork: tareasmiranda/buildozer-action).

Patches applied on top of upstream:
  1. change_owner(): falls back to numeric UID:GID if the requested user
     does not exist in /etc/passwd (Ubuntu 26.04 base image issue).
  2. install_buildozer(): adds --break-system-packages so pip can install
     Buildozer on PEP 668 "externally managed" environments.
  3. run_command(): exports PIP_BREAK_SYSTEM_PACKAGES=1 and
     PIP_IGNORE_INSTALLED=1 so python-for-android's internal pip calls
     bypass PEP 668 and do not try to uninstall Debian-managed packages
     (e.g. wheel) that lack a RECORD file.
"""

import os
import pwd
import subprocess
import sys


def change_owner(user, path):
    """chown -R <user> <path>, falling back to numeric UID:GID."""
    try:
        pwd.getpwnam(user)
    except KeyError:
        # The named user does not exist in this container. chown accepts
        # numeric IDs, so use the current process's UID/GID instead.
        user = f"{os.getuid()}:{os.getgid()}"
    subprocess.check_call(["sudo", "chown", "-R", user, path])


def install_buildozer(version):
    """Install Buildozer from PyPI or a specific Git ref."""
    # PEP 668: pip refuses global installs on Ubuntu 24.04+ / 26.04.
    # --break-system-packages is safe inside an ephemeral CI container.
    pip_install = [
        sys.executable, "-m", "pip", "install",
        "--user", "--upgrade", "--break-system-packages",
    ]

    if version == "stable":
        target = "buildozer"
    elif version == "master":
        target = "git+https://github.com/kivy/buildozer.git@master"
    else:
        # Numeric version (e.g. "1.5.0") -> install from PyPI or Git tag.
        # Try PyPI first; if it's a 4-part version, use the Git tag.
        target = f"buildozer=={version}"

    subprocess.check_call(pip_install + [target])


def run_command(command):
    """Run the Buildozer command with pip-related env vars set."""
    env = os.environ.copy()
    # Make every pip invocation (including python-for-android's internal
    # ones) bypass PEP 668.
    env["PIP_BREAK_SYSTEM_PACKAGES"] = "1"
    # Prevent pip from trying to uninstall Debian-managed packages that
    # have no RECORD file (e.g. wheel on Ubuntu 26.04).
    env["PIP_IGNORE_INSTALLED"] = "1"
    # Silence Buildozer's "running as root" interactive prompt.
    env["BUILDOZER_WARN_ON_ROOT"] = "0"

    retcode = subprocess.check_call(command, shell=True, env=env)
    return retcode


def main():
    env = os.environ

    repository_root = env.get("INPUT_REPOSITORY_ROOT", ".")
    workdir = env.get("INPUT_WORKDIR", ".")
    buildozer_version = env.get("INPUT_BUILDOZER_VERSION", "stable")
    command = env.get("INPUT_COMMAND", "buildozer android debug")

    # 1. Fix ownership so the non-root user can write to the workspace.
    change_owner(env["USER"], repository_root)

    # 2. Install the requested Buildozer version.
    install_buildozer(buildozer_version)

    # 3. Change into the buildozer.spec directory (if needed).
    if workdir and workdir != ".":
        os.chdir(os.path.join(repository_root, workdir))
    else:
        os.chdir(repository_root)

    # 4. Run the build.
    run_command(command)


if __name__ == "__main__":
    main()