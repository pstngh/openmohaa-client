# Client Improvement Backlog

This backlog records client-side improvements that can give OpenMoHAA players a fair competitive benefit through lower latency, steadier performance, and clearer presentation.

## Guardrails

- Client-only: remain compatible with ordinary OpenMoHAA servers.
- Keep the existing network protocol, user-command format, server commands, and gameplay rules unchanged.
- Add zero steady-state overhead where possible; prefer replacing or removing work over adding per-frame work.
- Use only information the server already intends the player to receive.
- Do not add aim/trigger automation, movement automation, recoil suppression, wall visibility, smoke/fog removal, bright enemy models, or enemy tracking through hidden information.

## Completed baseline

- [x] `644710e2` - make stopwatch HUD transitions event-driven and cache objective configstrings.
- [x] `c4971068` - cache frame-path render resources.
- [x] `e35cab8f` - make scoreboard and countdown work change-driven.
- [x] `a3772bcd` - streamline packet-entity traversal and remove discarded renderer lookups.

## Priority 1: low-latency mouse input

Target files: `code/sdl/sdl_input.c`, `code/client/cl_input.cpp`, and `code/client/cl_main.cpp`.

- [ ] Coalesce all SDL relative-motion events collected in one frame into one accumulated mouse delta.
- [ ] Preserve button, wheel, focus, console, and menu behavior exactly.
- [ ] Investigate consuming mouse motion as close as safely possible to `CL_CreateCmd` without polling SDL twice.
- [ ] Re-evaluate the macOS default of `m_filter 1` with modern SDL relative mouse mode; use `0` when input remains stable.
- [ ] Verify that coalescing produces the exact same total X/Y movement and reduces queued-event work.
- [ ] Measure input-to-command latency before and after. Disabling the two-frame filter should recover roughly half a rendered frame of mouse response.

Expected result: lower mouse latency and less input-event overhead, with no protocol or gameplay change.

## Priority 2: precise frame pacing

Target file: `code/qcommon/common.c` and the platform timing layer.

- [ ] Replace integer-millisecond FPS scheduling with an absolute, high-resolution frame deadline.
- [ ] Carry fractional frame time forward instead of truncating it.
- [ ] Retain network wakeups, timedemo behavior, minimized/unfocused limits, and dedicated-server behavior.
- [ ] Avoid a permanent busy-spin; sleep for the coarse portion and use the smallest practical final wait.
- [ ] Compare average frame time, standard deviation, 1% lows, and CPU use at 60, 85, 120, 125, 144, and 240 FPS caps.

Expected result: steadier presentation and more consistent input-to-photon latency without additional rendering work.

## Priority 3: competitive presentation without added draw work

- [ ] Expose the existing `cg_drawviewmodel 0` option clearly in the multiplayer UI; hiding the viewmodel also removes its rendering work.
- [ ] Provide a high-contrast crosshair preset by replacing the normal crosshair draw, not adding another overlay pass.
- [ ] Add separately configurable scoped sensitivity with monitor-distance/FOV calibration.
- [ ] Recompute and cache sensitivity scaling only when its cvars or FOV change.
- [ ] Keep all defaults visually compatible unless a player explicitly enables a competitive option.

Expected result: less visual obstruction and more consistent aim, with equal or lower rendering cost.

## Optional changes with explicit tradeoffs

These can provide a larger latency benefit, but they do not meet a literal zero-resource-cost rule and should remain opt-in.

- [ ] Packet-rate preset: raise `cl_maxpackets` from 30 toward 60 or 125 on suitable connections. At 125 FPS or higher, 30 to 125 packets per second can reduce average command-send waiting time from about 16.5 ms to about 4 ms, at the cost of more network traffic.
- [ ] Low-latency interpolation preset: test a conservative `cl_timeNudge`, such as `-10`, with a clear warning about extrapolation and jitter.
- [ ] Low-latency audio preset: reduce `s_mixahead` and SDL device samples while detecting or documenting underruns, crackling, and device-specific limits.
- [ ] Adaptive interpolation: derive the smallest safe render delay from recent snapshot jitter, with strict bounds and immediate fallback when packets become unstable.

## Measurement and acceptance criteria

- [ ] Establish a repeatable A/B scene or demo before changing each subsystem.
- [ ] Measure CPU frame time, frame-time percentiles, input-to-command delay, packet cadence, extrapolated-frame rate, and audio underruns as applicable.
- [ ] Add behavioral tests for every state transition or timing policy.
- [ ] Ensure diagnostic instrumentation performs no work when disabled.
- [ ] Build all directly affected client targets and run the complete client test suite.
- [ ] Audit every commit to confirm it touches no server gameplay code and changes no wire-format behavior.

## Recommended next commit

Start with SDL mouse-motion coalescing. It is small, measurable, compatible with regular servers, and should lower both latency-related queueing and CPU overhead without changing what the player can do.
