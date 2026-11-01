# Native starter 1.1

- Configure the title bar and hide the status bar before creating the content window. Wait for the native acknowledgement and a short window-manager settling period; fall back once if no acknowledgement arrives.
- Cancel pending window creation when the app pauses or unloads. Ignore obsolete callbacks and create at most one window for each activation.
- Wait for SQLite registration locks using the old CLI-compatible timeout command.
- Return to Home before optional registration removal. A locked registry keeps the entry for a later retry instead of blocking Home.

This starter update is copied over USB. Home Assistant app updates alone do not install it.
