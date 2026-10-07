#!/usr/bin/env python3

import argparse
import os
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path


def run(command):
    print(f"\n→ {' '.join(map(str, command))}")
    subprocess.run(command, check=True)


def main():
    parser = argparse.ArgumentParser(
        description="Package a pre-built Linux tar.gz application as a Debian .deb"
    )

    parser.add_argument(
        "archive",
        help="Path to the application .tar.gz archive",
    )

    parser.add_argument(
        "--version",
        required=True,
        help="Application version, e.g. 1.107.0",
    )

    parser.add_argument(
        "--package-name",
        default="antigravity-ide",
        help="Debian package name (default: antigravity-ide)",
    )

    parser.add_argument(
        "--app-name",
        default="Antigravity IDE",
        help="Application display name",
    )

    parser.add_argument(
        "--executable",
        default="antigravity-ide",
        help="Executable inside the extracted archive",
    )

    parser.add_argument(
        "--command",
        default="antigravity",
        help="Command created in /usr/bin",
    )

    parser.add_argument(
        "--icon",
        default="resources/app/resources/linux/code.png",
        help="Icon path relative to application directory",
    )

    parser.add_argument(
        "--maintainer",
        default="Mohit Bansal",
        help="Package maintainer",
    )

    parser.add_argument(
        "--architecture",
        default="amd64",
        help="Debian architecture (default: amd64)",
    )

    parser.add_argument(
        "--no-sandbox",
        action="store_true",
        help="Automatically add --no-sandbox when launching",
    )

    parser.add_argument(
        "--output",
        default=".",
        help="Directory where the .deb will be created",
    )

    args = parser.parse_args()

    archive = Path(args.archive).expanduser().resolve()
    output_dir = Path(args.output).expanduser().resolve()

    if not archive.exists():
        raise SystemExit(f"Archive not found: {archive}")

    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = (
        output_dir
        / f"{args.package_name}_{args.version}_{args.architecture}.deb"
    )

    print("=" * 60)
    print(f"Building:     {args.app_name}")
    print(f"Version:      {args.version}")
    print(f"Architecture: {args.architecture}")
    print(f"Archive:      {archive}")
    print(f"Output:       {output_file}")
    print("=" * 60)

    with tempfile.TemporaryDirectory(prefix="deb-builder-") as temp:
        temp_dir = Path(temp)

        extracted = temp_dir / "extracted"
        package = temp_dir / "package"

        extracted.mkdir()

        print("\n[1/8] Extracting archive...")

        with tarfile.open(archive, "r:gz") as tar:
            tar.extractall(extracted)

        #
        # Detect whether tar contains one top-level directory.
        #
        items = list(extracted.iterdir())

        if len(items) == 1 and items[0].is_dir():
            app_source = items[0]
        else:
            app_source = extracted

        executable = app_source / args.executable

        if not executable.exists():
            print("\nERROR: Executable not found:")
            print(executable)

            print("\nTop-level extracted files:")
            for item in list(app_source.iterdir())[:30]:
                print(" -", item.name)

            raise SystemExit(1)

        print(f"Found executable: {executable}")

        #
        # Package directories
        #
        print("\n[2/8] Creating Debian package structure...")

        debian_dir = package / "DEBIAN"
        opt_dir = package / "opt" / args.package_name
        bin_dir = package / "usr" / "bin"
        desktop_dir = package / "usr" / "share" / "applications"
        icon_dir = (
            package
            / "usr"
            / "share"
            / "icons"
            / "hicolor"
            / "256x256"
            / "apps"
        )

        for directory in [
            debian_dir,
            opt_dir,
            bin_dir,
            desktop_dir,
            icon_dir,
        ]:
            directory.mkdir(parents=True, exist_ok=True)

        #
        # Copy application
        #
        print("\n[3/8] Copying application files...")

        shutil.copytree(
            app_source,
            opt_dir,
            dirs_exist_ok=True,
            symlinks=True,
        )

        installed_executable = opt_dir / args.executable
        installed_executable.chmod(
            installed_executable.stat().st_mode | 0o111
        )

        #
        # Debian control file
        #
        print("\n[4/8] Creating package metadata...")

        control = f"""Package: {args.package_name}
Version: {args.version}
Section: devel
Priority: optional
Architecture: {args.architecture}
Maintainer: {args.maintainer}
Description: {args.app_name}
 {args.app_name} packaged for Ubuntu/Debian.
"""

        control_file = debian_dir / "control"
        control_file.write_text(control)
        control_file.chmod(0o644)

        #
        # Launcher
        #
        print("\n[5/8] Creating command launcher...")

        sandbox_argument = " --no-sandbox" if args.no_sandbox else ""

        launcher = f"""#!/bin/bash
exec /opt/{args.package_name}/{args.executable}{sandbox_argument} "$@"
"""

        launcher_file = bin_dir / args.command
        launcher_file.write_text(launcher)
        launcher_file.chmod(0o755)

        #
        # Icon
        #
        print("\n[6/8] Adding application icon...")

        source_icon = opt_dir / args.icon
        icon_name = args.package_name

        if source_icon.exists():
            destination_icon = icon_dir / f"{icon_name}.png"

            shutil.copy2(
                source_icon,
                destination_icon,
            )

            print(f"Icon: {source_icon}")

        else:
            print(f"WARNING: Icon not found: {source_icon}")
            print("Package will still be created.")

        #
        # Desktop launcher
        #
        print("\n[7/8] Creating desktop entry...")

        desktop = f"""[Desktop Entry]
Name={args.app_name}
Comment={args.app_name}
Exec=/usr/bin/{args.command} %F
Icon={icon_name}
Terminal=false
Type=Application
Categories=Development;IDE;
StartupNotify=true
"""

        desktop_file = desktop_dir / f"{args.package_name}.desktop"
        desktop_file.write_text(desktop)
        desktop_file.chmod(0o644)

        #
        # Fix package directory permissions
        #
        debian_dir.chmod(0o755)

        # Remove setuid/setgid bits from directories.
        for root, directories, _ in os.walk(package):
            for directory in directories:
                path = Path(root) / directory
                mode = path.stat().st_mode
                path.chmod(mode & ~0o6000)

        #
        # Build
        #
        print("\n[8/8] Building .deb package...")

        run([
            "dpkg-deb",
            "--build",
            "--root-owner-group",
            str(package),
            str(output_file),
        ])

    print("\n" + "=" * 60)
    print("SUCCESS")
    print("=" * 60)
    print(f"\nPackage created:\n{output_file}")

    size_mb = output_file.stat().st_size / (1024 * 1024)

    print(f"\nSize: {size_mb:.1f} MB")

    print("\nInstall using:")
    print(f"sudo apt install ./{output_file.name}")

    print("\nLaunch using:")
    print(args.command)

    print("\nUninstall using:")
    print(f"sudo apt remove {args.package_name}")


if __name__ == "__main__":
    main()
