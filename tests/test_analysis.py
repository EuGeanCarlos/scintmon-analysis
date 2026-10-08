"""Testes de decisões científicas, estatísticas e preservação do conjunto."""
from io import BytesIO
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile
import pandas as pd
from scintmon.analysis.context import attach_context
from scintmon.analysis.pipeline import Options, build_dataset, filter_data
from scintmon.analysis.statistics import summarize
from scintmon.core.geodesy import ecef_to_geodetic, infer_unit
from scintmon.core.rules import classify_s4, profile
from scintmon.core.time import convert_time
from scintmon.io.demo import demo_files
from scintmon.reporting.report_builder import export_bundle, report
from scintmon.visualization.charts import make_charts


class RulesTests(unittest.TestCase):
    def test_boundaries_and_invalid_s4(self):
        p = profile()
        self.assertEqual([classify_s4(v, p) for v in [0, .2999, .3, .5999, .6, 1.2, -1, float('inf')]],
                         ["fraca", "fraca", "moderada", "moderada", "forte", "forte", "inválido", "inválido"])

    def test_custom_validation(self):
        with self.assertRaises(ValueError):
            profile("custom", lower=.6, upper=.3, minimum_elevation=30)
        with self.assertRaises(ValueError):
            profile("custom", lower=.3, upper=.6, minimum_elevation=float('nan'))
        self.assertEqual(classify_s4(.5, profile("custom", lower=.2, upper=.4, minimum_elevation=20)), "forte")

    def test_kintner_is_strict_selection_not_strength(self):
        self.assertEqual(classify_s4(.5, profile("kintner_fig8")), "fora do critério S4")
        self.assertEqual(classify_s4(.6, profile("kintner_fig8")), "acima do critério S4")

    def test_time_basis(self):
        self.assertEqual(convert_time("2002-12-02T01:00:00", "raw"), (None, None))
        utc, local = convert_time("2002-12-02T01:00:00", "utc")
        self.assertEqual(local, "2002-12-01T22:00:00-03:00")
        self.assertEqual(convert_time("2002-12-01T22:00:00", "local")[0], utc)
        with self.assertRaises(ValueError):
            convert_time("2002-12-01T22:00:00", "guess")

    def test_units_inference(self):
        self.assertEqual(infer_unit((6378, 0, 0)), "km")
        self.assertEqual(infer_unit((6378000, 0, 0)), "m")
        self.assertEqual(infer_unit((20000, 0, 0), "satellite"), "km")
        with self.assertRaises(ValueError):
            infer_unit((1, 2, 3))

    def test_geodetic_against_pyproj(self):
        from pyproj import Transformer
        forward = Transformer.from_crs(4979, 4978, always_xy=True)
        inverse = Transformer.from_crs(4978, 4979, always_xy=True)
        for longitude, latitude, height in [(-44.3, -2.5, 20), (120, 60, 1000), (0, 0, 0), (0, 90, 0), (0, -90, 100)]:
            xyz = forward.transform(longitude, latitude, height)
            lat, lon, h = ecef_to_geodetic(xyz, "m")
            expected_lon, expected_lat, expected_h = inverse.transform(*xyz)
            self.assertAlmostEqual(lat, expected_lat, delta=1e-8)
            if abs(latitude) < 90:
                self.assertAlmostEqual(lon, expected_lon, delta=1e-8)
            self.assertAlmostEqual(h, expected_h, delta=1e-3)


class DatasetTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        paths = []
        for name, content in demo_files():
            path = Path(self.folder.name) / name
            path.write_bytes(content)
            paths.append(path)
        self.paths = paths
        self.dataset = build_dataset(paths, Options(geometry_enabled=True, input_time_basis="utc"))

    def test_canonical_geometry_and_midnight(self):
        data = self.dataset.data
        self.assertEqual(len(data), 480)
        self.assertTrue(data["geometry_valid"].all())
        self.assertTrue(data["coordinate_unit_inferred"].all())
        self.assertEqual(data["night"].nunique(), 4)
        self.assertEqual(data["observation_date"].nunique(), 5)
        self.assertEqual(set(data["quadrant"]), {"NE", "SE", "SO", "NO"})
        self.assertTrue(data["s4_above_one"].any())

    def test_filters_preserve_full_dataset(self):
        selected = filter_data(self.dataset.data, nights=["2002-12-01"], prns=[1], mask=True)
        self.assertTrue(selected["passes_active_selection"].all())
        self.assertEqual(len(self.dataset.data), 480)
        self.assertTrue(filter_data(self.dataset.data, nights=[]).empty)
        selected = filter_data(self.dataset.data, hour_range=(23, 0))
        self.assertEqual(len(selected), 480)

    def test_kintner_predicate(self):
        dataset = build_dataset(self.paths[:1], Options(geometry_enabled=True, selected_profile=profile("kintner_fig8")))
        selected = filter_data(dataset.data, mask=True)
        self.assertTrue(selected["s4"].gt(.5).all())
        self.assertTrue(selected["elevation_deg"].gt(10).all())
        self.assertTrue(pd.isna(summarize(selected, ["night"]).iloc[0]["percent_strong"]))

    def test_statistics_denominator_and_percentiles(self):
        data = self.dataset.data.iloc[:4].copy()
        data["s4"] = [.1, .3, .6, -1]
        data["s4_valid"] = [True, True, True, False]
        row = summarize(data, ["night"]).iloc[0]
        self.assertEqual(row["n_total"], 4)
        self.assertEqual(row["n_valid"], 3)
        self.assertAlmostEqual(row["mean"], 1 / 3)
        self.assertAlmostEqual(row["fraction_ge_06"], 1 / 3)
        self.assertAlmostEqual(row["p95"], .57)
        self.assertAlmostEqual(row["std"], .2516611478)

    def test_context_exact_time_and_interval(self):
        time = self.dataset.data.iloc[0]["datetime_utc"]
        context = pd.DataFrame([dict(datetime_utc=time, kp=3, dst=-5, source="TESTE SINTÉTICO")])
        result = attach_context(self.dataset.data, geomagnetic=context)
        self.assertEqual(result["kp"].notna().sum(), 4)
        context["interval_end_utc"] = "2002-12-01T23:57:00Z"
        result = attach_context(self.dataset.data, geomagnetic=context)
        self.assertEqual(result["kp"].notna().sum(), 8)
        self.assertTrue((result[result["kp"].notna()]["geomagnetic_condition"] == "calma pelo critério do plano").all())

    def test_context_without_confirmed_time_is_not_fabricated(self):
        dataset = build_dataset(self.paths[:1])
        context = pd.DataFrame([dict(datetime_utc="2002-12-01T23:55:00Z", kp=1, dst=0, source="TESTE")])
        result = attach_context(dataset.data, geomagnetic=context)
        self.assertTrue(result["kp"].isna().all())

    def test_invalid_context_rejected(self):
        with self.assertRaises(ValueError):
            attach_context(self.dataset.data, geomagnetic=pd.DataFrame({"kp": [1]}))
        context = pd.DataFrame([dict(datetime_utc="2002-12-01T23:55:00Z", kp=10, dst=0, source="TESTE")])
        with self.assertRaises(ValueError):
            attach_context(self.dataset.data, geomagnetic=context)

    def test_solar_context_utc_date(self):
        context = pd.DataFrame([dict(date="2002-12-01", f107=100, sunspot_number=50,
                                     solar_cycle_class="teste", source="TESTE SINTÉTICO")])
        result = attach_context(self.dataset.data, solar=context)
        self.assertEqual(result["f107"].notna().sum(), 20)
        self.assertTrue(result["solar_cycle_period_from_plan"].eq("máximo").all())

    def test_report_escapes_filter_text(self):
        md, html = report(self.dataset, filter_data(self.dataset.data), "<script>alert(1)</script>")
        self.assertIn("15. Referências", md)
        self.assertIn("&lt;script&gt;", html)
        self.assertNotIn("<script>alert(1)</script>", html)

    def test_all_figures_and_export_bundle(self):
        selected = filter_data(self.dataset.data, mask=True)
        figures = make_charts(selected, note="DADOS SINTÉTICOS · máscara do projeto")
        self.assertGreaterEqual(len(figures), 14)
        bundle = export_bundle(self.dataset, selected, "SINTÉTICO", figures)
        with ZipFile(BytesIO(bundle)) as archive:
            self.assertIsNone(archive.testzip())
            self.assertIn("tables/complete.parquet", archive.namelist())
            self.assertIn("reports/report.html", archive.namelist())
            for name in figures:
                self.assertTrue(archive.read(f"figures/{name}.png").startswith(b'\x89PNG'))
                self.assertIn(b"<svg", archive.read(f"figures/{name}.svg"))

    def test_empty_data_export(self):
        dataset = build_dataset([])
        bundle = export_bundle(dataset, dataset.data, "sem dados", {})
        with ZipFile(BytesIO(bundle)) as archive:
            self.assertIn("reports/report.md", archive.namelist())

    def test_individual_prn_products(self):
        selected = filter_data(self.dataset.data, nights=["2002-12-01"], prns=[1])
        bundle = export_bundle(self.dataset, selected, "SINTÉTICO", {}, individual_prns=True)
        with ZipFile(BytesIO(bundle)) as archive:
            for field in ["s4", "signal_power_raw", "elevation_deg", "azimuth_deg", "skyplot"]:
                self.assertIn(f"figures/prn/2002-12-01/PRN_1_{field}.png", archive.namelist())
