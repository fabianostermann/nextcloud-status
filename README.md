# Nextcloud command-line tool for querying client sync status

This is a python script that reports the current status of synchronization of the [nextcloud-desktop-client](https://github.com/nextcloud/desktop) (Linux only).

This is done by connecting to the nextcloud client socket, which is also used by the official [syncstate nautilus-extension](https://github.com/nextcloud/desktop/blob/master/shell_integration/nautilus/syncstate.py) to show icon overlays that indicate sync status.\
Much of the code is borrowed there.

To test it, just run:
```
python nextcloud-status.py
```
Will print either `Up to date` or `Syncing..` to stdout (or warnings/errors).\
For now, I decided to match the behavior of `dropbox status`, because I formerly used the Dropbox cloud service and integrated their command-line tool in many of my personal scripts.\
This is also, why I decided to build this tool in the first place.

## Install
To install it globally, just make it executable and copy it to `/usr/bin` (or alternatively to `~/bin`)
```
chmod +x nextcloud-status.py
cp nextcloud-status.py /usr/bin/nextcloud-status
```
Then you should be able to run `nextcloud-status` in your terminal.

If you have any questions, find bugs or have enhancement ideas, feel free to open an issue and ask for help. I cannot guarantee to find a solution, but I will try to work on this from time to time. \
I also opened a [discussion at the official nextcloud issue tracker](https://github.com/nextcloud/desktop/issues/6345).

## Roadmap

- Add command-line usage info (`-h/--help`)
- Clean up code
- Add other info queries, e.g. sync status of subfolders. All possible socket requests are listed [here](https://github.com/nextcloud/desktop/blob/master/src/gui/socketapi/socketapi.h).
