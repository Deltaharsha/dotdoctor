# 🩺 dotdoctor

A checkup for your Linux desktop. dotdoctor scans your Hyprland setup and dotfiles and tells you what's broken and how to fix it.

```
$ ./dotdoctor.py
▲ WARN   SUPER + E fires 3 actions at once
  • Files (nautilus) — default
  • Files (thunar) — yours
  • Emoji picker — old config
  fix: add  hl.unbind("SUPER + E")  in ~/.config/hypr/bindings.lua before re-binding it.
```

## What it checks

- **Hyprland config errors** that Hyprland logs but you never see
- **Keybind conflicts**, read from your *live* binds (works with Lua and classic configs, including Omarchy)
- **Shortcuts that launch missing programs**
- **Broken symlinks** in `~/.config` (old dotfiles repos, stow leftovers)
- **Backup clutter** (`.bak` files piling up)

It only reads. It never changes your files.

## Usage

```sh
git clone https://github.com/Deltaharsha/dotdoctor
cd dotdoctor
./dotdoctor.py          # scan your system
./dotdoctor.py --demo   # see it on a deliberately broken example setup
```

Needs Python 3.9+. No dependencies.

## Pro (coming soon)

AI explanations, one-command fixes with undo, and warnings before an update breaks your config. [Join the waitlist](https://deltaharsha.github.io/dotdoctor/) for half price for life.

## License

MIT
