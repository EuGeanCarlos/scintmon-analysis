"""Registro único de parâmetros e perfis científicos."""
import json
from math import isfinite
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REGISTRY = json.loads((ROOT / "config/scientific_rules.yaml").read_text(encoding="utf-8"))
APP_CONFIG = json.loads((ROOT / "config/app_config.yaml").read_text(encoding="utf-8"))


def rule_value(identifier):
    return next(rule["value"] for rule in REGISTRY["rules"] if rule["id"] == identifier)


def profile(name="project_default", *, lower=None, upper=None, minimum_elevation=None):
    result = dict(REGISTRY["profiles"][name], name=name)
    if name == "custom":
        result.update(lower=lower, upper=upper, minimum_elevation=minimum_elevation)
        if not all(isinstance(v, (int, float)) and isfinite(v) for v in (lower, upper, minimum_elevation)):
            raise ValueError("Parâmetros personalizados devem ser finitos")
        if not 0 <= lower < upper or not 0 <= minimum_elevation <= 90:
            raise ValueError("Limiares exigem 0 <= inferior < superior; elevação de 0 a 90°")
    return result


def classify_s4(s4, selected_profile):
    if not isfinite(s4) or s4 < 0:
        return "inválido"
    if selected_profile["name"] == "kintner_fig8":
        return "acima do critério S4" if s4 > selected_profile["s4_gt"] else "fora do critério S4"
    return "fraca" if s4 < selected_profile["lower"] else "moderada" if s4 < selected_profile["upper"] else "forte"
