# build_deb# Linux Tar.gz → Debian Package Builder

A reusable Python utility for converting pre-built Linux applications distributed as `.tar.gz` archives into installable `.deb` packages for Ubuntu/Debian.

This is especially useful for applications such as Electron/Chromium-based software that are distributed as an extracted application directory rather than a native Debian package.

## Features

- Extracts `.tar.gz` application archives
- Packages the complete application under `/opt`
- Creates a command in `/usr/bin`
- Creates an Ubuntu application-menu `.desktop` entry
- Installs an application icon
- Supports `--no-sandbox` for Electron/Chromium applications
- Configurable package name, executable, command, icon, version, and architecture
- Preserves application symlinks
- Automatically cleans temporary build files
- Produces a standard `.deb` package installable with `apt`

## Requirements

The script requires:

- Python 3
- `dpkg-deb`
- Ubuntu or another Debian-based Linux distribution

Check Python:

```bash
python3 --version
```

Check `dpkg-deb`:

```bash
dpkg-deb --version
```

If required, install Debian packaging utilities:

```bash
sudo apt update
sudo apt install dpkg-dev
```

## Project Structure

A simple project directory can look like:

```text
deb-builder/
├── build_deb.py
├── README.md
└── Antigravity IDE.tar.gz
```

Make the script executable:

```bash
chmod +x build_deb.py
```

## Basic Usage

The minimum required arguments are the archive and application version:

```bash
./build_deb.py application.tar.gz --version 1.0.0
```

For applications requiring Chromium's `--no-sandbox` argument:

```bash
./build_deb.py application.tar.gz \
  --version 1.0.0 \
  --no-sandbox
```

## Antigravity IDE Example

For Antigravity IDE:

```bash
./build_deb.py "Antigravity IDE.tar.gz" \
  --version 1.107.0 \
  --no-sandbox
```

The script will generate:

```text
antigravity-ide_1.107.0_amd64.deb
```

Install it with:

```bash
sudo apt install ./antigravity-ide_1.107.0_amd64.deb
```

After installation, launch Antigravity from the Ubuntu Applications menu or run:

```bash
antigravity
```

The generated launcher automatically executes:

```text
/opt/antigravity-ide/antigravity-ide --no-sandbox
```

## Package Layout

The generated `.deb` installs files approximately as follows:

```text
/
├── opt/
│   └── antigravity-ide/
│       ├── antigravity-ide
│       ├── resources/
│       ├── locales/
│       └── ...
│
└── usr/
    ├── bin/
    │   └── antigravity
    │
    └── share/
        ├── applications/
        │   └── antigravity-ide.desktop
        │
        └── icons/
            └── hicolor/
                └── 256x256/
                    └── apps/
                        └── antigravity-ide.png
```

The application itself is stored in:

```text
/opt/antigravity-ide/
```

while `/usr/bin/antigravity` acts as a convenient launcher.

## Command-Line Options

View all available options:

```bash
./build_deb.py --help
```

Available options include:

```text
archive
    Path to the .tar.gz application archive.

--version
    Application/package version.
    Required.

--package-name
    Debian package name.
    Default: antigravity-ide

--app-name
    Display name shown in Ubuntu.
    Default: Antigravity IDE

--executable
    Main executable inside the archive.
    Default: antigravity-ide

--command
    Command created under /usr/bin.
    Default: antigravity

--icon
    Icon path relative to the extracted application.
    Default: resources/app/resources/linux/code.png

--maintainer
    Package maintainer name.
    Default: Mohit Bansal

--architecture
    Debian architecture.
    Default: amd64

--no-sandbox
    Add --no-sandbox when starting the application.

--output
    Directory where the resulting .deb will be saved.
    Default: current directory
```

## Packaging Another Application

The builder is not limited to Antigravity IDE.

For example, suppose you have:

```text
my-editor.tar.gz
```

containing:

```text
my-editor
resources/
locales/
icon.png
```

You can build it using:

```bash
./build_deb.py my-editor.tar.gz \
  --version 2.1.0 \
  --package-name my-editor \
  --app-name "My Editor" \
  --executable my-editor \
  --command myeditor \
  --icon icon.png
```

The resulting package will be:

```text
my-editor_2.1.0_amd64.deb
```

and after installation the application can be launched with:

```bash
myeditor
```

## Custom Output Directory

To put generated packages into a separate directory:

```bash
mkdir -p dist
```

Then:

```bash
./build_deb.py "Antigravity IDE.tar.gz" \
  --version 1.107.0 \
  --no-sandbox \
  --output dist
```

The package will be created at:

```text
dist/antigravity-ide_1.107.0_amd64.deb
```

## Inspecting the Package

Before installing, inspect the package metadata:

```bash
dpkg-deb --info antigravity-ide_1.107.0_amd64.deb
```

Inspect the files that will be installed:

```bash
dpkg-deb --contents antigravity-ide_1.107.0_amd64.deb
```

Or show only the first few entries:

```bash
dpkg-deb --contents antigravity-ide_1.107.0_amd64.deb | head -50
```

## Installing

Install the generated package using `apt`:

```bash
sudo apt install ./antigravity-ide_1.107.0_amd64.deb
```

Using `apt` instead of directly using `dpkg -i` is generally preferable because `apt` can handle package dependencies when they are declared.

## Verify Installation

Check whether the package is installed:

```bash
dpkg -l | grep antigravity
```

For Antigravity, you should see something similar to:

```text
ii  antigravity-ide  1.107.0  amd64
```

Check the launcher:

```bash
which antigravity
```

Expected:

```text
/usr/bin/antigravity
```

## Upgrading

If a new application version is released, build it with a higher version number:

```bash
./build_deb.py "Antigravity IDE.tar.gz" \
  --version 1.108.0 \
  --no-sandbox
```

Then install:

```bash
sudo apt install ./antigravity-ide_1.108.0_amd64.deb
```

Because the package name remains:

```text
antigravity-ide
```

and the version increased, Ubuntu will treat it as an upgrade of the existing package rather than an unrelated application.

## Uninstalling

Remove Antigravity IDE with:

```bash
sudo apt remove antigravity-ide
```

You can verify removal with:

```bash
dpkg -l | grep antigravity
```

## How It Works

The script performs the following process:

```text
.tar.gz
   │
   ▼
Extract archive
   │
   ▼
Find application executable
   │
   ▼
Create Debian directory structure
   │
   ├── /opt/<package>
   ├── /usr/bin/<command>
   ├── /usr/share/applications
   └── /usr/share/icons
   │
   ▼
Generate DEBIAN/control
   │
   ▼
Generate launcher
   │
   ▼
Generate .desktop entry
   │
   ▼
Copy application icon
   │
   ▼
Fix permissions
   │
   ▼
dpkg-deb --build
   │
   ▼
<package>_<version>_<architecture>.deb
```

## Important Notes

This utility packages an **already compiled Linux application**.

It does not compile source code.

The archive should therefore already contain a Linux executable, such as:

```text
antigravity-ide
```

You can inspect an executable with:

```bash
file antigravity-ide
```

For an amd64 application, you will typically see something containing:

```text
ELF 64-bit LSB ... x86-64
```

Do not label an ARM binary as `amd64`, or vice versa.

## Electron Applications

Many Electron applications include Chromium and may have sandbox-related requirements.

If an application only works when started as:

```bash
./application --no-sandbox
```

build it with:

```bash
--no-sandbox
```

For example:

```bash
./build_deb.py app.tar.gz \
  --version 1.0.0 \
  --no-sandbox
```

The generated `/usr/bin` launcher will then automatically supply that argument.

Note that disabling Chromium's sandbox reduces process isolation. If the application can run correctly with its sandbox enabled, that configuration is preferable.

## Troubleshooting

### Executable not found

If you receive:

```text
ERROR: Executable not found
```

check the extracted archive:

```bash
tar -tzf application.tar.gz | head -50
```

Then specify the correct executable:

```bash
--executable correct-executable-name
```

### Icon not found

An icon is optional. If the configured icon cannot be found, the script will print a warning and continue building the package.

Find available PNG files with:

```bash
find extracted-directory -iname "*.png"
```

Then provide the appropriate relative path:

```bash
--icon path/to/icon.png
```

### Package architecture

Check the executable architecture:

```bash
file application
```

For standard Intel/AMD 64-bit Ubuntu systems, use:

```bash
--architecture amd64
```

For ARM64 applications, use:

```bash
--architecture arm64
```

The architecture option should describe the application binary, not simply the computer on which the package is being built.

## Disclaimer

This utility only repackages existing application binaries. Make sure you have permission to redistribute or package the software you are using.

The generated `.deb` does not modify or rebuild the application's source code.