#!/usr/bin/env python3
"""Turnkey launcher for SAT-Frontier Enterprise Interactive Web Visualizer & SLA Dashboard."""
import sys
from pathlib import Path

# Add project root to sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sat_frontier.enterprise.desktop import main

if __name__ == "__main__":
    main()

