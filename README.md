# Nextcloud command-line tool for querying client sync status

This is a python script that reports the current status of synchronization of the [nextcloud-desktop-client](https://github.com/nextcloud/desktop) (Linux only).

This is done by connecting to the nextcloud client socket, which is also used by the official [syncstate nautilus-extension](https://github.com/nextcloud/desktop/blob/master/shell_integration/nautilus/syncstate.py) to show icon overlays that indicate sync status.\
Much of the code is borrowed there.

To test if it works for you, just run:
```
python nextcloud-status.py
```
Will print either `Up to date` or `Syncing..` to stdout (or warnings/errors).\
For now, I decided to match the behavior of `dropbox status`, because I formerly used the Dropbox cloud service and integrated their command-line tool in many of my personal scripts.\
This is also, why I decided to build this tool in the first place.

You can also list all files that are currently syncing (`-r`) or query files explicitly:
```
$ python nextcloud-status.py --help
USAGE: ./nextcloud-status.py [-h|--help] [--debug] [-r|-R|--recursive] [files..]
```

## Install
To install it globally, mark it executable and copy it to `/usr/bin`.
```
chmod +x nextcloud-status.py
cp nextcloud-status.py /usr/bin/nextcloud-status
```
Then run `nextcloud-status` in your terminal.

If you have any questions, find bugs or have ideas for new featues, feel free to open an issue! \
I also opened a [discussion at the official nextcloud issue tracker](https://github.com/nextcloud/desktop/issues/6345).

## Roadmap

-[x] Add command-line usage info (`-h/--help`)
-[x] Add feature to check sync status recursively
-[ ] Add other socket queries (e.g. ). All possible socket requests are listed [here](https://github.com/nextcloud/desktop/blob/master/src/gui/socketapi/socketapi.h).
-[ ] Clean up code (currently, the logic of recursive mode and print messages is a bit confusing, which is bad when bugs occur or new features are to be added)

