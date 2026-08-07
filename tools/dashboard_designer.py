#!/usr/bin/env python3
"""
dashboard_designer.py — Modify dashboard layouts programmatically.

Lets the agent (or a human) modify dashboard JSON configs without
hand-editing JSON. Supports swapping gauges, changing themes,
adding/removing gauges, and adjusting positions.

Usage:
    python tools/dashboard_designer.py --list
    python tools/dashboard_designer.py --dashboard yanmar_7inch_tft --show
    python tools/dashboard_designer.py --dashboard yanmar_7inch_tft --swap rpm oil_pressure
    python tools/dashboard_designer.py --dashboard yanmar_7inch_tft --theme night
    python tools/dashboard_designer.py --dashboard yanmar_7inch_tft --add-gauge '{"type":"bar","label":"Boost",...}'
    python tools/dashboard_designer.py --dashboard yanmar_7inch_tft --remove-gauge boost
    python tools/dashboard_designer.py --dashboard yanmar_7inch_tft --move rpm --x 200 --y 200
    python tools/dashboard_designer.py --dashboard yanmar_7inch_tft --resize rpm --width 100
    python tools/dashboard_designer.py --dashboard yanmar_7inch_tft --set-threshold rpm --yellow 3000 --red 3300
"""

import argparse
import json
import sys
from pathlib import Path

DASHBOARDS_DIR = Path(__file__).parent.parent / "dashboards"


def load_dashboard(name: str) -> dict:
    """Load a dashboard JSON by name (without path or extension)."""
    # Try exact filename
    path = DASHBOARDS_DIR / f"{name}.json"
    if not path.exists():
        # Try with underscores
        path = DASHBOARDS_DIR / name.replace(" ", "_").lower()
        if not path.suffix:
            path = path.with_suffix(".json")
    if not path.exists():
        # Search all JSON files
        matches = list(DASHBOARDS_DIR.glob("*.json"))
        for m in matches:
            data = json.loads(m.read_text())
            if data.get("name", "").lower() == name.lower():
                path = m
                break
        else:
            print(f"Error: dashboard '{name}' not found in {DASHBOARDS_DIR}", file=sys.stderr)
            print(f"Available: {', '.join(f.stem for f in DASHBOARDS_DIR.glob('*.json'))}", file=sys.stderr)
            sys.exit(1)
    return json.loads(path.read_text())


def save_dashboard(name: str, data: dict):
    """Save dashboard JSON."""
    path = DASHBOARDS_DIR / f"{name}.json"
    path.write_text(json.dumps(data, indent=2) + '\n')
    print(f"  ✓ Saved {path}")


def find_gauge(data: dict, gauge_id: str) -> dict | None:
    """Find a gauge by ID."""
    for g in data.get("gauges", []):
        if g.get("id") == gauge_id:
            return g
    return None


def cmd_list(args):
    """List available dashboards."""
    files = sorted(DASHBOARDS_DIR.glob("*.json"))
    if not files:
        print("No dashboards found.")
        return
    print(f"Dashboards in {DASHBOARDS_DIR}/:")
    for f in files:
        data = json.loads(f.read_text())
        name = data.get("name", "(unnamed)")
        n_gauges = len(data.get("gauges", []))
        n_readouts = len(data.get("readouts", []))
        disp = data.get("display", {})
        disp_type = disp.get("type", "?")
        dims = f"{disp.get('width', '?')}x{disp.get('height', '?')}"
        theme = data.get("current_theme", "?")
        print(f"  {f.stem:<30} {name:<40} {disp_type} {dims}  {n_gauges} gauges, {n_readouts} readouts  theme={theme}")


def cmd_show(args):
    """Show dashboard details."""
    data = load_dashboard(args.dashboard)
    print(json.dumps(data, indent=2))


def cmd_swap(args):
    """Swap positions of two gauges."""
    data = load_dashboard(args.dashboard)
    g1 = find_gauge(data, args.gauge1)
    g2 = find_gauge(data, args.gauge2)
    if not g1:
        print(f"Error: gauge '{args.gauge1}' not found", file=sys.stderr); sys.exit(1)
    if not g2:
        print(f"Error: gauge '{args.gauge2}' not found", file=sys.stderr); sys.exit(1)
    g1["position"], g2["position"] = g2["position"], g1["position"]
    save_dashboard(args.dashboard, data)
    print(f"  ✓ Swapped positions of '{args.gauge1}' and '{args.gauge2}'")


def cmd_theme(args):
    """Set the current theme."""
    data = load_dashboard(args.dashboard)
    themes = data.get("themes", {})
    if args.theme not in themes:
        print(f"Error: theme '{args.theme}' not defined. Available: {', '.join(themes.keys())}", file=sys.stderr)
        sys.exit(1)
    data["current_theme"] = args.theme
    save_dashboard(args.dashboard, data)
    print(f"  ✓ Theme set to '{args.theme}'")


def cmd_add_gauge(args):
    """Add a new gauge."""
    data = load_dashboard(args.dashboard)
    try:
        gauge = json.loads(args.spec)
    except json.JSONDecodeError as e:
        print(f"Error parsing gauge JSON: {e}", file=sys.stderr); sys.exit(1)
    if "id" not in gauge:
        gauge["id"] = gauge.get("label", "gauge").lower().replace(" ", "_")
    if find_gauge(data, gauge["id"]):
        print(f"Error: gauge '{gauge['id']}' already exists. Use --remove-gauge first.", file=sys.stderr)
        sys.exit(1)
    data.setdefault("gauges", []).append(gauge)
    save_dashboard(args.dashboard, data)
    print(f"  ✓ Added gauge '{gauge['id']}'")


def cmd_remove_gauge(args):
    """Remove a gauge."""
    data = load_dashboard(args.dashboard)
    before = len(data.get("gauges", []))
    data["gauges"] = [g for g in data.get("gauges", []) if g.get("id") != args.gauge_id]
    after = len(data["gauges"])
    if before == after:
        print(f"Warning: gauge '{args.gauge_id}' not found", file=sys.stderr)
    else:
        save_dashboard(args.dashboard, data)
        print(f"  ✓ Removed gauge '{args.gauge_id}'")


def cmd_move(args):
    """Move a gauge to new coordinates."""
    data = load_dashboard(args.dashboard)
    gauge = find_gauge(data, args.gauge_id)
    if not gauge:
        print(f"Error: gauge '{args.gauge_id}' not found", file=sys.stderr); sys.exit(1)
    pos = gauge.setdefault("position", {})
    if args.x is not None:
        pos["x"] = args.x
    if args.y is not None:
        pos["y"] = args.y
    save_dashboard(args.dashboard, data)
    print(f"  ✓ Moved '{args.gauge_id}' to ({pos.get('x')}, {pos.get('y')})")


def cmd_resize(args):
    """Resize a gauge."""
    data = load_dashboard(args.dashboard)
    gauge = find_gauge(data, args.gauge_id)
    if not gauge:
        print(f"Error: gauge '{args.gauge_id}' not found", file=sys.stderr); sys.exit(1)
    if "radius" in gauge:
        if args.width:
            gauge["radius"] = args.width // 2
    elif "size" in gauge:
        if args.width:
            gauge["size"]["width"] = args.width
        if args.height:
            gauge["size"]["height"] = args.height
    else:
        if args.width:
            gauge["radius"] = args.width // 2
    save_dashboard(args.dashboard, data)
    print(f"  ✓ Resized '{args.gauge_id}'")


def cmd_set_threshold(args):
    """Set yellow/red threshold zones for a gauge."""
    data = load_dashboard(args.dashboard)
    gauge = find_gauge(data, args.gauge_id)
    if not gauge:
        print(f"Error: gauge '{args.gauge_id}' not found", file=sys.stderr); sys.exit(1)
    if args.yellow is not None:
        yz = gauge.setdefault("yellow_zone", {})
        yz["start"] = args.yellow
    if args.red is not None:
        rz = gauge.setdefault("red_zone", {})
        rz["start"] = args.red
        if args.yellow is not None:
            yz = gauge.setdefault("yellow_zone", {})
            yz["end"] = args.red
    save_dashboard(args.dashboard, data)
    print(f"  ✓ Threshold updated for '{args.gauge_id}'")


def cmd_set_backlight(args):
    """Set backlight brightness values."""
    data = load_dashboard(args.dashboard)
    bl = data.setdefault("backlight", {})
    if args.day is not None:
        bl["day_brightness"] = args.day
    if args.night is not None:
        bl["night_brightness"] = args.night
    if args.dim is not None:
        bl["dim_brightness"] = args.dim
    save_dashboard(args.dashboard, data)
    print(f"  ✓ Backlight updated")


def cmd_validate(args):
    """Validate a dashboard config for common issues."""
    data = load_dashboard(args.dashboard)
    issues = []
    display = data.get("display", {})
    width = display.get("width", 480)
    height = display.get("height", 320)

    for g in data.get("gauges", []):
        gid = g.get("id", "?")
        pos = g.get("position", {})
        px, py = pos.get("x", 0), pos.get("y", 0)
        radius = g.get("radius", 0)
        size = g.get("size", {})

        # Check bounds
        if radius:
            if px - radius < 0 or px + radius > width:
                issues.append(f"  ⚠ {gid}: x={px} r={radius} may overflow width={width}")
            if py - radius < 0 or py + radius > height:
                issues.append(f"  ⚠ {gid}: y={py} r={radius} may overflow height={height}")
        elif size:
            sw = size.get("width", 0)
            sh = size.get("height", 0)
            if px + sw > width:
                issues.append(f"  ⚠ {gid}: x={px} w={sw} overflows width={width}")
            if py + sh > height:
                issues.append(f"  ⚠ {gid}: y={py} h={sh} overflows height={height}")

        # Check data source
        if "data_source" not in g:
            issues.append(f"  ⚠ {gid}: no data_source specified")

        # Check thresholds
        yz = g.get("yellow_zone", {})
        rz = g.get("red_zone", {})
        if yz and rz:
            if yz.get("start", 0) >= rz.get("start", float('inf')):
                issues.append(f"  ⚠ {gid}: yellow zone start >= red zone start")

    for r in data.get("readouts", []):
        pos = r.get("position", {})
        if pos.get("x", 0) > width or pos.get("y", 0) > height:
            rid = r.get("id", "?")
            issues.append(f"  ⚠ readout {rid}: position may be off-screen")

    if issues:
        print(f"Validation issues in '{args.dashboard}':")
        for issue in issues:
            print(issue)
        sys.exit(1)
    else:
        print(f"  ✓ '{args.dashboard}' validates cleanly ({len(data.get('gauges', []))} gauges, {len(data.get('readouts', []))} readouts)")


def main():
    parser = argparse.ArgumentParser(
        description="Modify dashboard layouts programmatically."
    )
    parser.add_argument("--list", action="store_true", help="List available dashboards")
    parser.add_argument("--dashboard", help="Dashboard name (filename without .json)")
    parser.add_argument("--show", action="store_true", help="Show dashboard JSON")
    parser.add_argument("--swap", nargs=2, metavar=("G1", "G2"), help="Swap positions of two gauges")
    parser.add_argument("--theme", help="Set current theme (day/night)")
    parser.add_argument("--add-gauge", metavar="JSON", help="Add a gauge (JSON spec)")
    parser.add_argument("--remove-gauge", metavar="ID", help="Remove a gauge by ID")
    parser.add_argument("--move", metavar="ID", help="Move a gauge (use --x --y)")
    parser.add_argument("--resize", metavar="ID", help="Resize a gauge (use --width --height)")
    parser.add_argument("--set-threshold", metavar="ID", help="Set thresholds for a gauge (use --yellow --red)")
    parser.add_argument("--x", type=int, help="X coordinate for --move")
    parser.add_argument("--y", type=int, help="Y coordinate for --move")
    parser.add_argument("--width", type=int, help="Width/radius for --resize")
    parser.add_argument("--height", type=int, help="Height for --resize")
    parser.add_argument("--yellow", type=float, help="Yellow threshold value for --set-threshold")
    parser.add_argument("--red", type=float, help="Red threshold value for --set-threshold")
    parser.add_argument("--backlight", action="store_true", help="Set backlight (use --day --night --dim)")
    parser.add_argument("--day", type=int, help="Day brightness (0-255)")
    parser.add_argument("--night", type=int, help="Night brightness (0-255)")
    parser.add_argument("--dim", type=int, help="Dim brightness (0-255)")
    parser.add_argument("--validate", action="store_true", help="Validate dashboard for common issues")

    args = parser.parse_args()

    if args.list:
        cmd_list(args)
        return

    if not args.dashboard:
        parser.error("--dashboard is required for all operations except --list")

    if args.show:
        cmd_show(args)
    elif args.swap:
        cmd_swap(args)
    elif args.theme:
        cmd_theme(args)
    elif args.add_gauge:
        cmd_add_gauge(args)
    elif args.remove_gauge:
        cmd_remove_gauge(args)
    elif args.move:
        cmd_move(args)
    elif args.resize:
        cmd_resize(args)
    elif args.set_threshold:
        cmd_set_threshold(args)
    elif args.backlight:
        cmd_set_backlight(args)
    elif args.validate:
        cmd_validate(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
