#!/usr/bin/env python3
"""
dashboard_designer.py — Design and modify dashboard layouts.

Used by the Pathos faculty to shape how engine data appears on screen.
Takes a vessel's aesthetic profile and generates a dashboard config
that matches the established visual language.

Usage:
    python dashboard_designer.py --engine yanmar_4lh-ste --display 7inch_tft --style hermit_steampunk
    python dashboard_designer.py --engine cummins_6bta --display 3.5_oled --style cargo_institutional
"""

import json
import argparse
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DASHBOARDS_DIR = REPO_ROOT / "dashboards"

# Style presets — Pathos uses these to shape the dashboard's personality
STYLE_PRESETS = {
    "hermit_steampunk": {
        "description": "Warm amber on dark teal. Brass bezels. Gentle animations. A tiny hermit crab at the gauge pivot.",
        "palette": {
            "background": "#0D2828",
            "primary": "#D4A574",
            "secondary": "#8B6914",
            "accent": "#5EEAD4",
            "warning": "#F59E0B",
            "danger": "#B7410E",
            "text": "#E8D5B7",
        },
        "gauge_style": {
            "bezel": "brass_gradient",
            "needle": "thin_dark_with_crab",
            "font": "serif_maritime",
            "animation": "tween_smooth",
            "corners": "rounded",
        },
        "alert_personality": {
            "yellow": "warm_glow",
            "red": "heating_metal",
            "sound": "gentle_chime",
        },
    },
    "cargo_institutional": {
        "description": "High contrast white on black. Clean geometric. Built for the next operator.",
        "palette": {
            "background": "#000000",
            "primary": "#FFFFFF",
            "secondary": "#888888",
            "accent": "#00AAFF",
            "warning": "#FFAA00",
            "danger": "#FF0000",
            "text": "#FFFFFF",
        },
        "gauge_style": {
            "bezel": "none",
            "needle": "thin_white",
            "font": "sans_serif_mono",
            "animation": "instant",
            "corners": "square",
        },
        "alert_personality": {
            "yellow": "solid_amber",
            "red": "flashing_red",
            "sound": "buzzer",
        },
    },
    "research_clean": {
        "description": "Minimal. Data-forward. No ornamentation. For vessels where the data IS the mission.",
        "palette": {
            "background": "#1A1A2E",
            "primary": "#E94560",
            "secondary": "#0F3460",
            "accent": "#16FFD0",
            "warning": "#FFD700",
            "danger": "#FF1744",
            "text": "#EEEEEE",
        },
        "gauge_style": {
            "bezel": "thin_line",
            "needle": "neon_thin",
            "font": "mono_data",
            "animation": "tween_fast",
            "corners": "sharp",
        },
    },
}


def design_dashboard(engine: str, display: str, style: str) -> dict:
    """Generate a dashboard configuration from style preset."""
    preset = STYLE_PRESETS.get(style, STYLE_PRESETS["hermit_steampunk"])
    
    dashboard = {
        "engine": engine,
        "display": display,
        "style": style,
        "description": preset["description"],
        "palette": preset["palette"],
        "gauge_style": preset["gauge_style"],
        "alerts": preset.get("alert_personality", {}),
        "gauges": [],
    }
    
    # Default gauge set depends on display size
    display_sizes = {
        "7inch_tft": "large",
        "5_ips": "large",
        "2.4_lcd": "small",
        "3.5_oled": "compact",
        "led_matrix": "minimal",
    }
    
    size = display_sizes.get(display, "medium")
    
    if size == "large":
        dashboard["gauges"] = [
            {"name": "rpm", "type": "analog_arc", "position": [120, 80], "size": [200, 200], "range": [0, 4000], "redline": 3600},
            {"name": "coolant_temp", "type": "analog_arc", "position": [340, 80], "size": [120, 120], "range": [40, 120], "red": 95},
            {"name": "oil_pressure", "type": "analog_arc", "position": [340, 210], "size": [120, 120], "range": [0, 80], "red": 60},
            {"name": "fuel", "type": "bar_vertical", "position": [20, 80], "size": [40, 200], "range": [0, 100]},
            {"name": "voltage", "type": "digital", "position": [200, 280], "size": [80, 30]},
            {"name": "hours", "type": "digital", "position": [200, 300], "size": [80, 20]},
        ]
    elif size == "compact":
        dashboard["gauges"] = [
            {"name": "rpm", "type": "bar_horizontal", "position": [0, 0], "size": [128, 16], "range": [0, 4000]},
            {"name": "coolant_temp", "type": "digital", "position": [0, 20], "size": [64, 16]},
            {"name": "oil_pressure", "type": "digital", "position": [64, 20], "size": [64, 16]},
            {"name": "fuel", "type": "bar_horizontal", "position": [0, 40], "size": [128, 8]},
            {"name": "warnings", "type": "icon_row", "position": [0, 52], "size": [128, 12]},
        ]
    elif size == "minimal":
        dashboard["gauges"] = [
            {"name": "rpm", "type": "led_bar", "position": [0, 0], "size": [32, 4], "range": [0, 4000]},
            {"name": "temp", "type": "led_color", "position": [0, 5], "size": [8, 1]},
            {"name": "oil", "type": "led_color", "position": [10, 5], "size": [8, 1]},
            {"name": "fuel", "type": "led_bar", "position": [0, 6], "size": [32, 2]},
        ]
    
    return dashboard


def main():
    parser = argparse.ArgumentParser(description="Design engine dashboard layouts")
    parser.add_argument("--engine", required=True, help="Engine identifier")
    parser.add_argument("--display", required=True, help="Display type")
    parser.add_argument("--style", default="hermit_steampunk", 
                        choices=list(STYLE_PRESETS.keys()),
                        help="Visual style preset")
    parser.add_argument("--output", help="Output file path")
    
    args = parser.parse_args()
    
    dashboard = design_dashboard(args.engine, args.display, args.style)
    
    output = Path(args.output) if args.output else DASHBOARDS_DIR / f"{args.engine}_{args.display}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output, "w") as f:
        json.dump(dashboard, f, indent=2)
    
    print(f"Dashboard designed for {args.engine} ({args.display}, {args.style}):")
    print(f"  Output: {output}")
    print(f"  Gauges: {len(dashboard['gauges'])}")
    print(f"  Style: {dashboard['description']}")


if __name__ == "__main__":
    main()
