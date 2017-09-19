import os
import unittest
import sstOceanColor


class TestDivaData(unittest.TestCase):
    @classmethod
    def setUp(cls):
        # Create lists and arrays
        cls.datadir = "./data/"
        cls.monthlyfile = os.path.join(cls.datadir, "T20170322017059.L3m_MO_SST4_sst4_9km.nc")

    def test_init_sst(self):

        sst = sstOceanColor.SSTfield()
        self.assertTrue(sst.lon is None)
        self.assertTrue(sst.lat is None)
        self.assertTrue(sst.sst is None)

    def test_read_file(self):

        sst = sstOceanColor.SSTfield()
        sst.readfile(self.monthlyfile)
        self.assertEqual(len(sst.lon), 4320)
        self.assertEqual(len(sst.lat), 2160)
        self.assertEqual(sst.lat.mean(), 0.0)
        self.assertAlmostEqual(sst.lat.max(), 89.958336)

