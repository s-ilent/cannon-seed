-- pcsx_coverage.lua - PCSX-Redux coverage + indirect-target tracer.
--
-- Loaded with -dofile on a generated driver (build/cov.<target>.lua) that
-- defines the COV table:
--   COV = { target, entries = { vram, ... },
--           indirect = { { a = vram, rs = N }, ... },
--           stopAt   = { vram, ... }, markAt = { vram, ... } }
--
-- Emits one COV| line the FIRST time each address is reached. Parsed by
-- tools/coverage_vs_fragments.py.
--
-- Set COV_AUTOPAD=1 to pulse START/CROSS/CIRCLE so a headless run advances
-- past the title screen unattended; leave it unset when a human is driving.
--
-- Requires -debugger. Exec breakpoints are evaluated only on the interpreter's
-- debug path, gated on DebugSettings::Debug (psxinterpreter.cc), off by
-- default; without -debugger no breakpoint fires. Each callback returns true
-- to keep its breakpoint (returning false removes it permanently).
--
-- All native wrappers live in the global PCSXCOV table. A breakpoint or event
-- listener whose Lua wrapper is collected has its native side torn down
-- mid-run, so a local table is not enough: the chunk's locals are collectible
-- as soon as it finishes, which silently drops every breakpoint. Reference
-- projects keep them global for this reason.

PCSXCOV = PCSXCOV or {}
local R = PCSXCOV
R.bps = {}
R.entered = {}
R.itarget = {}
R.listeners = {}
R.cfg = COV
R.missed = 0
local DEBUG = os.getenv("COV_DEBUG") == "1"

local cfg = R.cfg
if not cfg then error("pcsx_coverage: COV table not set") end

local function emit(tag, ...)
  print(string.format("COV|%s|%s", tag, table.concat({ ... }, "|")))
end

local function guard(fn)
  local ok, err = pcall(fn)
  -- A throwing callback makes PCSX delete its breakpoint, silently weakening
  -- the probe, so every callback body is guarded.
  if not ok then print("COV|ERR|" .. tostring(err)) end
end

local ffi = require("ffi")

-- Live instruction word at a VRAM address (2 MiB RAM is mirrored).
local function readU32(address)
  local base = ffi.cast("uint8_t*", PCSX.getMemPtr())
  return tonumber(ffi.cast("uint32_t*", base + (address % 0x200000))[0])
end

-- Unattended pad: hold the start-ish buttons for a few frames, release, repeat.
-- GPU::Vsync does not fire headless, so the clock is the CPU cycle counter and
-- the tick is driven from breakpoint callbacks.
local pad, padButtons
if os.getenv("COV_AUTOPAD") == "1" then
  guard(function()
    pad = PCSX.SIO0.slots[1].pads[1]
    padButtons = PCSX.CONSTS.PAD.BUTTON
    emit("AUTOPAD", "start=" .. tostring(padButtons.START))
  end)
end

local AXIS = { "START", "CROSS", "CIRCLE" }
local HOLD = 3000000     -- ~5 frames at 33.8688 MHz
local REST = 3000000
R.pad = { untilCycle = 0, held = false }
local hits = 0

local function tick()
  if not pad then return end
  hits = hits + 1
  if hits % 32 ~= 0 then return end
  guard(function()
    local c = tonumber(PCSX.getCPUCycles()) or 0
    if c < R.pad.untilCycle then return end
    if R.pad.held then
      for _, n in ipairs(AXIS) do pad.clearOverride(padButtons[n]) end
      R.pad.held = false
      R.pad.untilCycle = c + REST
    else
      for _, n in ipairs(AXIS) do pad.setOverride(padButtons[n]) end
      R.pad.held = true
      R.pad.untilCycle = c + HOLD
    end
  end)
end

-- Build (or rebuild) every breakpoint. Rebuilt on reset; hits are deduped.
local function arm()
  R.bps = {}
  for _, e in ipairs(cfg.entries) do
    local ent = e
    R.bps[#R.bps + 1] = PCSX.addBreakpoint(ent.a, "Exec", 4, "entry", function(addr)
      guard(function()
        if R.entered[addr] then return end
        -- Count only when the resident bytes are this stage's image, so code
        -- from a different stage at the same address is never miscounted.
        local live = readU32(addr)
        local stage
        for i = 1, #ent.w do
          if ent.w[i] ~= 0 and ent.w[i] == live then stage = cfg.stages[i]; break end
        end
        if stage == nil then
          if DEBUG and R.missed < 60 then
            R.missed = R.missed + 1
            local ws = {}
            for i = 1, #ent.w do ws[i] = string.format("%08X", ent.w[i]) end
            emit("MISS", string.format("0x%08X", addr), string.format("%08X", live),
                 table.concat(ws, ","))
          end
          return
        end
        R.entered[addr] = true
        emit("ENTERED", string.format("0x%08X", addr), stage)
      end)
      tick()
      return true
    end)
  end

  for _, s in ipairs(cfg.indirect) do
    local rs = s.rs
    R.bps[#R.bps + 1] = PCSX.addBreakpoint(s.a, "Exec", 4, "indirect", function(addr)
      guard(function()
        local t = PCSX.getRegisters().GPR.r[rs]
        if not R.itarget[t] then
          R.itarget[t] = true
          emit("ITARGET", string.format("0x%08X", t))
        end
      end)
      tick()
      return true
    end)
  end

  if cfg.stopAt then
    for _, a in ipairs(cfg.stopAt) do
      R.bps[#R.bps + 1] = PCSX.addBreakpoint(a, "Exec", 4, "stop", function(addr)
        guard(function()
          emit("STOP", string.format("0x%08X", addr))
          PCSX.quit(0)
        end)
        return false
      end)
    end
  end

  -- Phase marker: emit MARK and keep running, so the log splits by stage.
  if cfg.markAt then
    for _, a in ipairs(cfg.markAt) do
      R.bps[#R.bps + 1] = PCSX.addBreakpoint(a, "Exec", 4, "mark", function(addr)
        guard(function() emit("MARK", string.format("0x%08X", addr)) end)
        return true
      end)
    end
  end
end

arm()
emit("READY", cfg.target,
     "entries=" .. tostring(#cfg.entries),
     "indirect=" .. tostring(#cfg.indirect))

R.listeners.reset = PCSX.Events.createEventListener("ExecutionFlow::Reset", function(ev)
  guard(function()
    emit("RESET", ev and tostring(ev.hard) or "?")
    arm()
  end)
end)

-- A first-chance CPU exception is a reliable sign the run went wrong.
R.listeners.pause = PCSX.Events.createEventListener("ExecutionFlow::Pause", function(ev)
  guard(function()
    if ev and ev.exception then emit("EXC", "first-chance") end
  end)
end)
