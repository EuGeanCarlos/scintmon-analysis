"""Navegação da interface real com motor de testes do Streamlit."""
import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest


class DashboardTests(unittest.TestCase):
    def test_geometry_disabled_and_custom_profile(self):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=60).run()
        app.radio(key="source_mode").set_value("Demonstração sintética").run()
        next(item for item in app.selectbox if item.label == "Perfil científico").set_value("custom")
        next(item for item in app.checkbox if item.label == "Calcular geometria WGS84").set_value(False)
        next(item for item in app.button if item.label == "Aplicar critérios").click().run()
        next(item for item in app.checkbox if item.label == "Aplicar seleção do perfil").set_value(False).run()
        self.assertEqual(len(app.exception), 0)
        self.assertTrue(any("Critério personalizado" in message.value for message in app.warning))
        app.radio(key="section").set_value("Quadrantes").run()
        self.assertEqual(len(app.exception), 0)

    def test_empty_state_and_all_demo_sections(self):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=60).run()
        self.assertEqual(len(app.exception), 0)
        self.assertTrue(any("Importe seus arquivos" in message.value for message in app.info))
        app.radio(key="source_mode").set_value("Demonstração sintética").run()
        self.assertEqual(len(app.exception), 0)
        self.assertTrue(any("DEMONSTRAÇÃO SINTÉTICA" in message.value for message in app.warning))
        for section in ["PRNs", "Geometria", "Quadrantes", "Comparação de Noites",
                        "Controle de Qualidade", "Metodologia e Fontes", "Exportações"]:
            app.radio(key="section").set_value(section).run()
            self.assertEqual(len(app.exception), 0, section)
