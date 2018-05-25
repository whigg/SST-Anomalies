import os
import unittest
import sstOceanColor


class TestDivaData(unittest.TestCase):
    @classmethod
    def setUp(cls):
        cls.datadir = "./data/"
        cls.domain = (-80, 0, 0., 40.)
        cls.monthlyfile = os.path.join(cls.datadir, "T20170322017059.L3m_MO_SST4_sst4_9km.nc")

    def test_init_sst(self):

        sst = sstOceanColor.SSTfield()
        self.assertTrue(sst.lon is None)
        self.assertTrue(sst.lat is None)
        self.assertTrue(sst.sst is None)

    def test_read_file(self):

        sst = sstOceanColor.SSTfield().readfile(self.monthlyfile)
        self.assertEqual(len(sst.lon), 4320)
        self.assertEqual(len(sst.lat), 2160)
        self.assertEqual(sst.lat.mean(), 0.0)
        self.assertEqual(abs(sst.lat.min()), sst.lat.max())
        self.assertEqual(sst.sst.mean(), 17.504069701519477)

    def test_extract_domain(self):
        sst = sstOceanColor.SSTfield().readfile(self.monthlyfile).extractdomain(self.domain)
        self.assertEqual(len(sst.lonregion), 960)
        self.assertEqual(len(sst.latregion), 480)
        self.assertTrue(sst.lonregion.min() >= self.domain[0])
        self.assertTrue(sst.lonregion.max() <= self.domain[1])
        self.assertTrue(sst.latregion.min() >= self.domain[2])
        self.assertTrue(sst.latregion.max() <= self.domain[3])
        self.assertEqual(sst.sstregion.mean(), 23.036363178045974)

class TestFileNames(unittest.TestCase):
    @classmethod
    def setUp(cls):
        cls.year = 2017
        cls.month = 2
        cls.satelite = "Terra"
        cls.satelite2 = "Aqua"

    def test_month_file(self):
        filename = sstOceanColor.makemonthfilename(self.year, self.month, self.satelite)
        self.assertEqual(filename, "T20170322017059.L3m_MO_SST4_sst4_9km.nc")

        filename = sstOceanColor.makemonthfilename(self.year, self.month, self.satelite2)
        self.assertEqual(filename, "A20170322017059.L3m_MO_SST4_sst4_9km.nc")


if __name__ == '__main__':
    unittest.main()
