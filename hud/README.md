# Compact HUD override

The files under `hud/ui/` are editable OpenMoHAA URC layouts. They override
the stock Allied Assault HUD layouts without modifying the original game PK3s.

## Build the PK3

From the repository root:

```sh
python3 hud/build_pk3.py
```

The deterministic builder sorts every entry and fixes ZIP metadata, so identical
layout sources produce a byte-for-byte identical
`artifacts/zzz_openmohaa-hud.pk3`.

## Build the affected module

Only the client-game module contains the timer and score behavior changes:

```sh
cmake -S . -B build-hud \
  -DBUILD_CLIENT=OFF \
  -DBUILD_SERVER=ON \
  -DBUILD_GAME_LIBRARIES=ON \
  -DBUILD_GAME_QVMS=OFF
cmake --build build-hud --target cgame --parallel
```

Enabling the server at configure time initializes the repository's shared
include paths; only the requested `cgame` target is built. The Linux artifact
is `build-hud/Release/cgame.so` (the exact output
subdirectory can differ for multi-config generators).

## Install

1. Back up the currently installed client-game module.
2. Copy `artifacts/zzz_openmohaa-hud.pk3` into the game's `main/` directory. Keep
   the filename late in PK3 sort order if renaming it, so it wins over `Pak0.pk3`.
3. Copy the newly built `cgame.so` next to the `openmohaa` executable, replacing
   the matching module for this client build. On other platforms, use the
   corresponding CMake-produced client-game library.
4. Restart OpenMoHAA; a live `vid_restart` is not sufficient to reload the
   client-game module reliably.

Remove the override PK3 and restore the backed-up module to uninstall.

## Validate

```sh
python3 -m unittest discover -s hud/tests -p 'test_*.py' -v
python3 -m unittest discover -s code/cgame/tests -p 'test_*.py' -v
```

Every populated ammo menu reserves 24 virtual units beneath the bullet graphic
or animation. The count stays at the bottom edge, centered under the graphic
with at least 5 units of vertical clearance. The empty ammo menu is unchanged.
`artifacts/hud-before-ammo-layout.jpg` records the previous side-by-side layout.
