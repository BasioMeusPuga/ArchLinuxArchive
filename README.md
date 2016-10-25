# ArchLinuxArchive
Download and install packages from the Arch Linux Archive (previously the Arch Rollback Machine)

## Requirements

`sudo pacman -S python-beautifulsoup4 python-requests`

## Usage
    ./pyALA.py package_name
        [-d <download directory>]       Download packages to specified directory (Defaults to current working dir)
        [--log]                         Parse pacman.log to show package history
        [--sig]                         Download .sig files from the archive
        
    ./pyALA.py -Syu <n>                 Show the last n full system updates

    ./pyALA.py --help
