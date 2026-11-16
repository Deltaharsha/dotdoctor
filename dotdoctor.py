#!/usr/bin/env python3
"""dotdoctor — diagnose your Linux desktop dotfiles (prototype).

Checks:
  1. Hyprland config errors           (hyprctl configerrors)
  2. Conflicting keybindings          (same keys bound more than once)
  3. Bindings that launch missing commands
  4. Broken symlinks in ~/.config
  5. Stale backup clutter in ~/.config
"""
import json
import os
import re
import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

HOME = Path.home()
CONFIG = HOME / ".config"
OMARCHY = Path(os.environ.get("OMARCHY_PATH", "/usr/share/omarchy"))

MODS = [(64, "SUPER"), (4, "CTRL"), (8, "ALT"), (1, "SHIFT"), (2, "CAPS"),
        (16, "MOD2"), (32, "MOD3"), (128, "MOD5")]

C = sys.stdout.isatty()
def col(code, s): return f"\033[{code}m{s}\033[0m" if C else s
RED, YEL, GRN, DIM, BOLD = (lambda s: col(31, s)), (lambda s: col(33, s)), \
    (lambda s: col(32, s)), (lambda s: col(2, s)), (lambda s: col(1, s))

findings = []  # (severity, title, detail, fix)

def add(sev, title, detail="", fix=""):
    findings.append((sev, title, detail, fix))

DEMO_HYPR = {}  # filled by --demo: fake hyprctl output

def run(cmd):
    if DEMO_HYPR and cmd[0] == "hyprctl":
        return DEMO_HYPR.get(cmd[1], "")
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=10).stdout
    except (OSError, subprocess.TimeoutExpired):
        return None

def tilde(p):
    p = str(p)
    return "~" + p[len(str(HOME)):] if p.startswith(str(HOME)) else p

def plural(n, word):
    return f"{n} {word}{'' if n == 1 else 's'}"

def keyname(b):
    mods = [n for bit, n in MODS if b["modmask"] & bit]
    return " + ".join(mods + [b["key"] or f"code:{b['keycode']}"])

# 1. config errors ---------------------------------------------------------
def check_config_errors():
    out = run(["hyprctl", "configerrors"])
    if out is None:
        add("info", "Hyprland not running — skipped live checks")
        return False
    # Lua errors come with "stack traceback:" and indented frame lines.
    # Group those under the error they belong to instead of counting each one.
    errs = []
    for line in re.sub(r"\x1b\[[0-9;]*m", "", out).splitlines():
        if not line.strip():
            continue
        if errs and (line[0].isspace() or line.startswith("stack traceback")):
            continue  # traceback detail: the first line already says where
        errs.append(line.strip())
    for e in errs:
        add("error", "Hyprland config error", f"  {tilde(e)}", lua_hint(e))
    return True

SECTIONS = {"general", "decoration", "animations", "input", "gestures", "misc",
            "binds", "dwindle", "master", "group", "cursor", "xwayland", "render", "ecosystem"}

def lua_hint(err):
    m = re.search(r"attempt to index a nil value \(global '(\w+)'\)", err)
    if m and m.group(1) in SECTIONS:
        s = m.group(1)
        return (f"'{s}.something = ...' is old-style syntax. In Lua configs, options go inside "
                f"hl.config():\n       hl.config({{ {s} = {{ rounding = 8 }} }})"
                if s == "decoration" else
                f"'{s}.something = ...' is old-style syntax. In Lua configs, write:\n"
                f"       hl.config({{ {s} = {{ ... }} }})")
    m = re.match(r"(.+?):(\d+):", err)
    if m:
        return f"Open {tilde(m.group(1))} at line {m.group(2)} and fix the problem described above."
    return "Run  Hyprland --verify-config  to see the full error."

# 2. keybinding conflicts --------------------------------------------------
def check_bind_conflicts():
    try:
        binds = json.loads(run(["hyprctl", "binds", "-j"]) or "[]")
    except json.JSONDecodeError:
        return
    groups = defaultdict(list)
    for b in binds:
        if b.get("catch_all") or (not b["key"] and not b["keycode"]):
            continue  # unidentifiable key: can't judge
        k = (b["modmask"], b["key"], b["keycode"], b["submap"], b["release"],
             b["mouse"], b.get("longPress", False))
        groups[k].append(b)
    for k, bs in groups.items():
        if len(bs) > 1:
            descs = [b.get("description") or f"{b['dispatcher']} {b['arg']}" for b in bs]
            where = f" (submap {k[3]})" if k[3] else ""
            # Hyprland runs every bind on a key. 2 actions is usually a deliberate
            # chain; 3+ is usually an override someone forgot to unbind.
            sev = "warn" if len(bs) >= 3 else "info"
            add(sev, f"{keyname(bs[0])}{where} fires {len(bs)} actions at once",
                "\n".join(f"  • {d}" for d in descs),
                "Fine if intentional. Otherwise add  "
                f'hl.unbind("{keyname(bs[0])}")  in ~/.config/hypr/bindings.lua before re-binding it.')
    return len(binds)

# 3. bindings launching missing commands -----------------------------------
BIND_RE = re.compile(r'o\.bind\(\s*"([^"]+)"\s*,\s*(?:"([^"]*)"|nil)\s*,\s*"([^"]+)"')
def check_missing_commands():
    files = list((CONFIG / "hypr").glob("*.lua"))
    files += list((OMARCHY / "default" / "hypr").rglob("*.lua"))
    seen = set()
    for f in files:
        try:
            text = f.read_text(errors="ignore")
        except OSError:
            continue
        for line in text.splitlines():
            if line.lstrip().startswith("--"):
                continue
            m = BIND_RE.search(line)
            if not m:
                continue
            keys, desc, cmd = m.groups()
            exe = cmd.split()[0]
            if exe in seen or not re.match(r"^[\w./-]+$", exe) or "." in exe and "/" not in exe:
                continue
            seen.add(exe)
            if not shutil.which(exe) and not Path(os.path.expanduser(exe)).exists():
                short = tilde(f)
                add("warn", f"{keys} runs '{exe}', which isn't installed",
                    f"  {desc or ''}  ({short})",
                    f"Install the package that provides '{exe}', or unbind {keys}.")

# 4. broken symlinks -------------------------------------------------------
# Apps create dangling lock/runtime symlinks on purpose; ignore those.
RUNTIME = re.compile(r"^(Singleton\w*|lock|\.?parentlock)$|-runtime$")
def check_broken_links():
    for root, dirs, files in os.walk(CONFIG):
        depth = Path(root).relative_to(CONFIG).parts
        if len(depth) > 3:
            dirs[:] = []
            continue
        for name in dirs + files:
            p = Path(root) / name
            if p.is_symlink() and not p.exists() and not RUNTIME.search(name):
                add("warn", f"Broken symlink: ~/{p.relative_to(HOME)}",
                    f"  points to {tilde(os.readlink(p))}",
                    "Remove it or re-point it at the right file.")

# 5. backup clutter --------------------------------------------------------
BAK = re.compile(r"\.(bak|backup|orig)(\.|$)|~$")  # not .old: apps rotate their own logs
def check_backups():
    baks = []
    for root, dirs, files in os.walk(CONFIG):
        if len(Path(root).relative_to(CONFIG).parts) > 2:
            dirs[:] = []
            continue
        baks += [Path(root) / f for f in files if BAK.search(f)]
    if len(baks) >= 3:
        listing = "\n".join(f"  ~/{b.relative_to(HOME)}" for b in sorted(baks)[:8])
        add("info", f"{len(baks)} old backup files cluttering ~/.config", listing,
            "Move them to ~/.config-backups/ or delete ones you no longer need.")

# demo ---------------------------------------------------------------------
def setup_demo():
    """Build a realistic broken setup in a temp dir, so demos and screencasts
    show the same output on any machine without touching the real config."""
    global HOME, CONFIG, OMARCHY
    import tempfile
    base = Path(tempfile.mkdtemp(prefix="dotdoctor-demo-"))
    HOME, CONFIG, OMARCHY = base, base / ".config", base / "no-omarchy"
    hypr = CONFIG / "hypr"
    hypr.mkdir(parents=True)
    (hypr / "bindings.lua").write_text(
        'o.bind("SUPER + E", "Files", "thunar")\n'
        'o.bind("SUPER + B", "Browser", "firefox")\n'
        'o.bind("SUPER + SHIFT + W", "Wallpaper picker", "waypaper")\n')
    # A classic migration mistake: old-style "section.option = value" in a Lua config.
    looknfeel = hypr / "looknfeel.lua"
    looknfeel.write_text(
        "-- Look and feel overrides\n\n"
        "hl.config({\n  general = {\n    gaps_in = 5,\n    gaps_out = 10,\n"
        "    border_size = 2,\n  },\n})\n\n"
        "-- Copied from an old blog post:\n"
        "-- rounded corners\n\n"
        "decoration.rounding = 8\n")
    for i, ts in enumerate(["20260301", "20260412", "20260520", "20260611"]):
        (hypr / f"hyprland.lua.bak.{ts}").write_text("")
    (CONFIG / "waybar").mkdir()
    (CONFIG / "waybar" / "style.css").symlink_to(HOME / "dotfiles/waybar/style.css")
    (CONFIG / "nvim").symlink_to(HOME / "old-dotfiles/nvim")

    # Fake PATH: only these programs "exist" in the demo world.
    bindir = base / "bin"
    bindir.mkdir()
    for prog in ["thunar", "hyprctl"]:
        f = bindir / prog
        f.write_text("#!/bin/sh\n")
        f.chmod(0o755)
    os.environ["PATH"] = str(bindir)

    def b(mod, key, desc):
        return {"modmask": mod, "key": key, "keycode": 0, "submap": "", "release": False,
                "mouse": False, "longPress": False, "catch_all": False,
                "description": desc, "dispatcher": "exec", "arg": ""}
    binds = [b(64, "E", "Files (nautilus) — default"), b(64, "E", "Files (thunar) — yours"),
             b(64, "E", "Emoji picker — old config"),
             b(64, "B", "Browser"), b(65, "W", "Wallpaper picker"),
             b(8, "TAB", "Focus next window"), b(8, "TAB", "Bring window to top")]
    binds += [b(64, str(n), f"Workspace {n}") for n in range(1, 10)]
    DEMO_HYPR["binds"] = json.dumps(binds)
    # Same shape as real Hyprland 0.56 output, traceback included.
    DEMO_HYPR["configerrors"] = (
        f"{looknfeel}:14: attempt to index a nil value (global 'decoration')\n"
        "stack traceback:\n"
        f"\t{looknfeel}:14: in main chunk\n"
        "\t[C]: in function 'require'\n")

# report -------------------------------------------------------------------
def main():
    if "--demo" in sys.argv:
        setup_demo()
        import atexit
        atexit.register(shutil.rmtree, HOME, True)
    print(BOLD("🩺 dotdoctor") + DIM("  — scanning your desktop config...\n"))
    live = check_config_errors()
    nbinds = check_bind_conflicts() if live else None
    check_missing_commands()
    check_broken_links()
    check_backups()

    icon = {"error": RED("✖ ERROR"), "warn": YEL("▲ WARN "), "info": DIM("ℹ INFO ")}
    order = {"error": 0, "warn": 1, "info": 2}
    for sev, title, detail, fix in sorted(findings, key=lambda f: order[f[0]]):
        print(f"{icon[sev]}  {BOLD(title)}")
        if detail:
            print(DIM(detail))
        if fix:
            print(GRN("  fix: ") + fix)
        print()

    n = {s: sum(1 for f in findings if f[0] == s) for s in order}
    scanned = f"{nbinds} keybindings, " if nbinds else ""
    print(f"Scanned {scanned}~/.config.  "
          f"{RED(plural(n['error'], 'error'))}, {YEL(plural(n['warn'], 'warning'))}, "
          f"{plural(n['info'], 'note')}.")
    if not findings:
        print(GRN("✔ All healthy."))
    return 1 if n["error"] else 0

if __name__ == "__main__":
    sys.exit(main())
