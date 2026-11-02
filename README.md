# Kindle Home Assistant Panel

A small Home Assistant app (add-on) that translates Home Assistant dashboards into a touch-friendly, monochrome Kindle client. Each Kindle can display a different room or area. Entity values update in place every two seconds; the dashboard layout is edited in Home Assistant.

Physically tested with a **Kindle Paperwhite 1 (2012), firmware 5.6.1.1**, already jailbroken with KUAL installed. Fullscreen and automatic frontlight off/on work on that device. Other models and firmware versions are untested. This project does not flash Linux or install a jailbreak.

## Home Assistant installation

1. Add `https://github.com/michis0806/kindle-homeassistant-panel` as an app repository in Home Assistant OS / Supervised.
2. Install **Kindle Panel**, start it, and open its web interface through Home Assistant.
3. Open `http://YOUR_HA_HOST:8098` on the Kindle. Approve its pairing code in the app's web interface.
4. Give the Kindle a name and select its dashboard under **Kindles und Dashboards**.

The device port defaults to **8098**. Configuration is available only through authenticated Home Assistant ingress. Avoid exposing either port to the internet. An existing local development installation and this repository installation have different app identities and separate data; stop one before starting the other on the same port.

On first start, the app creates a separate **Kindle** dashboard (`kindle-panel`) if it does not exist. Upgrades seed it from the previous entity selection. Existing dashboards are never overwritten. Create additional dashboards in Home Assistant for other rooms, then assign them in the app. Several Kindles can also share a dashboard. Changing a device's assignment does not affect the others.

## Layout in Home Assistant

Edit the assigned dashboard with Home Assistant's dashboard editor. Sections, headings, tile, thermostat, entity, button, sensor, entities lists, and grid/horizontal/vertical stacks are translated. Supported domains: sensor, binary_sensor, climate, light, switch, input_boolean, scene, weather, cover, script and fan. Entity badges (including legacy entity-ID strings) appear as compact read-only pills with the HA icon, value and unit above the cards and update live. Existing cards take precedence over duplicate badges. Mushroom template badges translate `content`, `label` and static MDI icons. Templates are evaluated by Home Assistant with entity/area variables and cached for ten seconds; changes update without reloading. Dynamic template icons, pictures and badge actions are not yet translated and produce warnings. Other custom/conditional badges and badge attribute displays are skipped with a warning.

The Kindle uses a **four-column base grid** implemented with explicit card positions compatible with old WebKit. HA card widths map from 12 columns to 4, while card row spans, order and section boundaries are retained. A climate card with `grid_options: {columns: 6, rows: 4}` occupies the left half; two cover cards with half-width and two rows each stack to its right. Half-width light, fan and script tiles then follow in the order you arranged them in Home Assistant. Larger sections paginate only along complete visual row boundaries.

Lights use a filled bulb for on and a crossed-out bulb for off. Cover cards provide ↑ open, ■ stop and ↓ close buttons according to the entity capabilities and respect `hide_state`; there are no position sliders. Touching a script button runs that script via `script.turn_on` without arguments. Already-running scripts are disabled. Fan cards provide basic on/off control. Climate mode buttons respect the dashboard feature’s `hvac_modes` subset, intersected with entity capabilities; an explicitly empty list hides all mode buttons. Icons and next actions follow confirmed HA state. Sensor values use HA display precision, including trailing zeroes. Explicit card names and entity names are preserved; the climate title retains its compact name handling.

A small, isolated layout helper reads the actual available height once per document and selects a matching row size. Live view and read-only preview use the same helper. All cards share the same row unit, with fitting steps up to 76 pixels; explicit `grid_options.rows` set the card height without a separate climate height cap. Badges share the top row with the exit button; the dashboard title is omitted in the overview. Badge height is measured separately and does not count twice during pagination or grow with grid rows. Cover and climate control buttons stay more compact than their card footprints. It never writes measured widths into the page or resizes during commands. Card positions are calculated explicitly, avoiding browser differences in table rowspan spacing. The preview defaults to the selected Kindle’s reported window dimensions when available; fixed sizes remain selectable. Only numeric display dimensions and control heights are written to the local app log for layout diagnosis.

The Kindle viewport uses a fixed initial scale with user scaling disabled. The client does not write measured viewport pixel widths back into the page during polling or commands. The preview uses the same renderer. This is a compact monochrome translation rather than a pixel-identical copy of the HA editor.

The dashboard remains the source for layout, names, icons and actions. Explicit `more-info` opens a local entity detail page; `navigate` can open another translated view of the assigned dashboard. Different icon actions and confirmations lock the card with a warning. Hold/double-tap gestures, arbitrary service calls, URL actions, custom cards and conditional visibility are not executed. Nested stacks, card defaults and presentation options are approximated; unsupported features produce translation warnings. A script card may explicitly call that same script without arguments; requests targeting other scripts or passing parameters remain unsupported. The app shows translation warnings. Conditional cards/sections/views are omitted. Use a dedicated dashboard with ordinary supported cards for each room. A dashboard assignment limits this client's displayed and controllable entities; it is not a replacement for Home Assistant user permissions.

The app offers a per-device preview at 600×800 or 758×1024. Preview controls cannot send commands. Choose the dashboard and save first, then choose a starting view if desired. Layout or assignment changes trigger one reload; entity changes update individual values without reloading. Actions wait for the state reported by Home Assistant and are never automatically retried.

## Prepare another Kindle

Python 3.10+ is needed on the computer. Jailbreak and KUAL must already work. The runtime builder extracts only required tools, **not** the USB networking service or update packages.

1. Obtain the upstream NiLuJe K5 archive `kindle-usbnet-0.22.N-r19297.tar.xz` from the [MobileRead snapshots thread](https://www.mobileread.com/forums/showthread.php?t=225030). Its exact checksum and the pinned Debian ARMEL sources are recorded in `runtime-sources.json`.
2. Build the runtime (Debian packages download automatically):

   ```sh
   python3 scripts/prepare_runtime.py --usbnet-archive /path/to/kindle-usbnet-0.22.N-r19297.tar.xz
   ```

3. Exit any running kiosk with its crossed-out Home Assistant icon. Connect the Kindle by USB, then install:

   ```sh
   python3 scripts/install_kindle.py --url http://YOUR_HA_HOST:8098 --volume /Volumes/Kindle
   ```

   For a reviewable folder without writing to a device, use `--output build/HAKiosk` instead of `--volume`.

4. Eject USB, enable Wi-Fi, open KUAL → Home Assistant → Home Assistant starten. Approve this Kindle's code and assign its room dashboard.

**Run the installer separately for each physical Kindle.** It creates a unique controller ID. Upgrades retain that ID; if cloning a prepared folder for another Kindle, run with `--new-device-id` on the new device. The ID routes the exit signal; it is not an API credential. Pairing cookies provide device authorization. Each Kindle has independent pairing, name, dashboard, start view, revocation and exit signal (up to 32 registered devices).

Home Assistant app updates do not update the USB extension; install starter updates separately on each Kindle. Starter 1.2 retains the fullscreen setup that configures the native title/status bars before creating the content window and waits for a native acknowledgement (with a bounded fallback). Returning Home occurs before optional registry cleanup, so a busy registration database cannot prevent it.

The native starter backs up its application registration before modifying it. The installer backs up an existing extension locally and refuses to overwrite saved active light/power state. Native registration and frontlight paths are firmware-specific; the version guard does not prove compatibility with other models. Do not use this starter on another model without adapting and testing those paths.

## Device behavior

Refresh remains manual through the bottom “Aktualisieren” button. With starter 1.2 it reloads the page, waits for the new page to report readiness, and asks only that Kindle to perform a flashing full display update through its native `eips` tool. The current pixels are retained; the framebuffer is not cleared. Older starters still reload the page but cannot perform the native refresh. No periodic full-refresh timer is installed. Physical full-refresh behavior still needs confirmation on the connected PW1.

The crossed-out HA icon exits to the Kindle home screen and restores frontlight and screensaver settings. Exit requires connectivity to the app. The hardware power button remains the normal Kindle sleep control. The tested PW1 starter turns the light fully off after 30 seconds without touch and restores it on touch; this uses touch events, not motion sensing. KUAL also provides diagnostic and recovery actions.

The server retains device approval and configuration in `/data/panel.json` across app updates. The Home Assistant API credential stays inside the app. Back up the app's data and the HA dashboard storage. Unpair a lost device in the app interface.

## Basic validation

After installing the app, check pairing, the Home Assistant dashboard, and device controls manually. Kindle startup, light and power behavior, and recovery actions require validation on the target device; simulator checks cannot establish compatibility with other Kindle models or firmware. Runtime binaries, personal configuration, backups, firmware and jailbreak downloads are excluded from Git.

## Wall-mount prototype

A compact bottom-support PW1 dock for a German installation box is in [hardware/wall-mount](hardware/wall-mount/). It includes STL exports in `print/`, the measured stepped lower-edge profile, a cable pocket for the existing straight Micro-USB lead and 60 mm mounting-hole spacing. Print the small profile sample first. The front contact area is 80 × 20 mm; the hidden box plate and local cable pocket extend beyond that area. This is prototype v0.2: rear-shell curvature, port depth, cable bend and physical fit remain unverified; read [the construction notes](hardware/wall-mount/hinweise.txt). It is a mechanical USB holder, not a rated electrical enclosure.

## License

Project source: MIT. Material Design Icons: Apache 2.0, see [third-party notices](THIRD_PARTY.md). Runtime tools are obtained separately from pinned upstream archives and retain their respective licenses.
