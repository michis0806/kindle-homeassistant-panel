# Third-party notices

- Material Design Icons (Pictogrammers), Apache License 2.0: curated SVG paths in `kindle_panel/icons.py`; license in `kindle_panel/ICON-LICENSE.txt`.
- `websocket-client` 1.9.0, Apache License 2.0, installed by the container build from PyPI with a pinned SHA-256.
- The native Kindle launch approach follows [PaulFreund/WebLaunch](https://github.com/PaulFreund/WebLaunch). The local scripts register a separate application and use the Kindle's existing JavaScript runtime.
- Runtime binaries are **not distributed in this repository**. `runtime-sources.json` identifies the exact Debian ARMEL packages and NiLuJe USBNetwork upstream archive used by the preparation script. SQLite is public domain; readline and ncurses/libgcc and the USBNetwork tools/libraries retain their upstream terms. The builder copies Debian copyright files and the USBNetwork source-location notice into the generated runtime. Consult those notices and upstream sources before redistributing a generated runtime.
