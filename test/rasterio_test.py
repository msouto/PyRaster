"""Unit tests for pyraster.RasterIO module

reference: https://docs.python.org/3.3/library/unittest.html
"""

import sys
import struct
#from pyraster import rasterio as rio
import unittest
import pyraster
from mock import MagicMock, patch
import osgeo
import numpy.ma as ma

class test_open(unittest.TestCase):
    '''Test error catching of open method'''

    def testOpen(self):
        '''Test ability to parse file name'''

        def new_open(filename, GA_ReadOnly):
            return filename

        with patch('osgeo.gdal.Open', new_open):
            self.assertEquals('foo', pyraster.RasterIO().open('foo'))

    def testIOError(self):
        '''Test ability to catch erroneous file name '''

        def null_open(self, file):
            return None

        with patch('osgeo.gdal.Open', null_open):
            self.assertRaises(IOError, pyraster.RasterIO().open, 'foo')

class test_read_metadata(unittest.TestCase):
    '''Test values returned from RasterIO.read_metadata with mock dataset'''

    def setUp(self):
        '''Setup mock dataset'''
        self.dataset = MagicMock()
        self.dataset.GetDriver().ShortName = 'short name'
        self.dataset.GetDriver().LongName = 'long name'
        self.dataset.GetProjection = MagicMock(return_value='projection')
        self.dataset.GetGeoTransform = MagicMock(return_value='geotransformation')
        self.dataset.RasterXSize = 1
        self.dataset.RasterYSize = 1
        self.dataset.RasterCount = 1


    def testReturns(self):
        '''Test returned values against expected'''
        expected = {'driver': 'short name',
                'xsize': 1,
                'ysize': 1,
                'num_bands': 1,
                'projection': 'projection',
                'geotranslation': 'geotransformation'
                }

        self.assertDictEqual(expected,pyraster.RasterIO().read_metadata(self.dataset))

class test_mask_band(unittest.TestCase):
    '''Test NumPy masking'''

    def testIntegerCheck(self):
        #setup mocked data
        self.datarray = MagicMock()
        self.datarray.dtype.name = 'int32'
        #setup mocked functions
        ma.masked_equal = MagicMock(return_value=1)
        ma.masked_invalid = MagicMock(return_value=2)
        #check correct value returned
        self.assertEqual(2, pyraster.RasterIO().mask_band(self.datarray, 9999))
        #check masked_equal called
        ma.masked_equal.assert_called_with(self.datarray, 9999, copy=False)
        #check masked_invalid called with output from masked_equal
        ma.masked_invalid.assert_called_with(1, copy=False)

class test_read_band(unittest.TestCase):
    '''Test read_band method'''

    def setUp(self):
        '''Setup mock dataset'''
        self.band = MagicMock()
        self.band.DataType = 1
        self.band.SetNoDataValue = MagicMock(return_value=1)

        self.dataset = MagicMock()
        self.dataset.RasterCount = 1
        self.dataset.GetRasterBand = MagicMock(return_value=self.band)

        struct.unpack = MagicMock(return_value=(1))

    def testCheckNumBands(self):
        self.assertRaises(ValueError, pyraster.RasterIO().read_band, self.dataset, 2)

    def testSetNoDataValue(self):
        #test read with NoDataVal set
        pyraster.RasterIO().read_band(self.dataset, 1, NoDataVal=9991)
        self.band.SetNoDataValue.assert_called_with(9991)

        #test read with NoDataVal not set
        self.band.GetNoDataValue = MagicMock(return_value=None)
        pyraster.RasterIO().read_band(self.dataset, 1)
        self.band.SetNoDataValue.assert_called_with(9999)

        #test read with NoDataVal set in band
        self.band.GetNoDataValue = MagicMock(return_value=1234)
        pyraster.RasterIO().read_band(self.dataset, 1)
        self.band.SetNoDataValue.assert_called_with(1234)

    def testMaskedOutput(self):

        def null_mask(self, array, NoDataVal):
            return 0
        #test with mask flag
        with patch('pyraster.RasterIO.mask_band', null_mask):
            self.assertEqual(0, pyraster.RasterIO().read_band(self.dataset, 1, masked=True))

        #test without mask flag
        self.assertEqual([[1]], pyraster.RasterIO().read_band(self.dataset, 1, masked=False))

    def testFloatCheck(self):
        #setup mocked data
        self.datarray = MagicMock()
        self.datarray.dtype.name = 'float32'
        #setup mocked functions
        ma.masked_values = MagicMock(return_value=3)
        ma.masked_invalid = MagicMock(return_value=4)
        #check correct value returned
        self.assertEqual(4, pyraster.RasterIO().mask_band(self.datarray, 9999))
        #check masked_equal called
        ma.masked_values.assert_called_with(self.datarray, 9999, copy=False)
        #check masked_invalid called with output from masked_equal
        ma.masked_invalid.assert_called_with(3, copy=False)

class test_new_raster(unittest.TestCase):
    '''Test creation method'''

    def setUp(self):
        self.outfile = MagicMock()
        self.format = MagicMock()
        self.xsize = MagicMock()
        self.ysize = MagicMock()
        self.geotranslation = MagicMock()
        self.epsg = MagicMock()
        self.num_bands = MagicMock()
        self.gdal_dtype = MagicMock()

        self.metadata = MagicMock()
        self.metadata.GetMetaData = MagicMock(return_value=1)

        self.driver = MagicMock()
        self.driver.GetMetadata = MagicMock(return_value=self.metadata)

    def testCreateError(self):

        self.assertRaises(SyntaxError, pyraster.RasterIO().new_raster, self.outfile, self.format,
                    self.xsize, self.ysize, self.geotranslation, self.epsg, self.num_bands,
                    self.gdal_dtype)

        def null_name(name):
            return 0

        def null_driver():
            return 0
        """
        with patch('osgeo.gdal.GetDriverByName', null_name):
            self.assertRaises(SyntaxError, pyraster.RasterIO().new_raster, self.outfile, self.format,
                        self.xsize, self.ysize, self.geotranslation, self.epsg, self.num_bands,
                        self.gdal_dtype)
        """

if __name__ == "__main__":
    unittest.main()
