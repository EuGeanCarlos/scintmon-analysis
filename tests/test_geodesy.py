"""Geometrias analíticas independentes de observações reais."""
import unittest
from scintmon.core.geodesy import passes_elevation, quadrant, satellite_geometry


class GeometryTests(unittest.TestCase):
    def geometry(self, satellite, **kwargs):
        return satellite_geometry((6378000, 0, 0), satellite,
                                  station_unit="m", satellite_unit="m",
                                  latitude_deg=0, longitude_deg=0, **kwargs)

    def test_cardinal_directions_at_equator(self):
        for satellite, azimuth in [((6378000, 0, 100), 0), ((6378000, 100, 0), 90),
                                   ((6378000, 0, -100), 180), ((6378000, -100, 0), 270)]:
            result = self.geometry(satellite)
            self.assertAlmostEqual(result.azimuth_deg, azimuth)
            self.assertAlmostEqual(result.elevation_deg, 0)
            self.assertAlmostEqual(result.range_m, 100)

    def test_zenith_and_nadir_have_no_quadrant(self):
        for x, elevation in [(6378100, 90), (6377900, -90)]:
            result = self.geometry((x, 0, 0))
            self.assertEqual(result.elevation_deg, elevation)
            self.assertIsNone(result.azimuth_deg)
            self.assertIsNone(result.quadrant)

    def test_mixed_units(self):
        result = satellite_geometry((6378000, 0, 0), (6378.1, .1, 0),
                                    station_unit="m", satellite_unit="km",
                                    latitude_deg=0, longitude_deg=0)
        self.assertAlmostEqual(result.elevation_deg, 45)
        self.assertAlmostEqual(result.east_m, 100)

    def test_longitude_rotates_local_axes(self):
        result = satellite_geometry((0, 6378000, 0), (-100, 6378000, 0),
                                    station_unit="m", satellite_unit="m",
                                    latitude_deg=0, longitude_deg=90)
        self.assertAlmostEqual(result.azimuth_deg, 90)
        self.assertAlmostEqual(result.east_m, 100)

    def test_zero_range_and_nonfinite_rejected(self):
        with self.assertRaises(ValueError):
            self.geometry((6378000, 0, 0))
        with self.assertRaises(ValueError):
            self.geometry((float('nan'), 0, 0))

    def test_quadrant_boundaries(self):
        self.assertEqual([quadrant(a) for a in [0, 89.999, 90, 180, 270, 360]],
                         ["NE", "NE", "SE", "SO", "NO", "NE"])
        with self.assertRaises(ValueError):
            quadrant(-1)

    def test_mask_is_inclusive(self):
        self.assertTrue(passes_elevation(30, 30))
        self.assertFalse(passes_elevation(29.99, 30))
        self.assertFalse(passes_elevation(float('nan'), 30))
