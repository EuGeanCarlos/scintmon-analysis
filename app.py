"""Entrada fina do dashboard; cálculos pertencem aos módulos científicos."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from scintmon.ui.dashboard import main

main()
