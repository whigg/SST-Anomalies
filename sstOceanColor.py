import netCDF4
import calendar
import datetime


class SSTfield(object):
    """
    SST field is made of coordinates (lon, lat) and Sea Surface Temperature
    """

    def __init__(self):
        self.lon = None
        self.lat = None
        self.sst = None

    def readfile(self, filename):
        with netCDF4.Dataset(filename) as nc:
            sstvar = nc.get_variables_by_attributes(standard_name="sea_surface_temperature")[0]
            sstvarname = sstvar.name
            self.lon = nc.variables['lon'][:]
            self.lat = nc.variables['lat'][:]
            self.sst = nc.variables[sstvarname][:]


def makemonthfilename(yy, mm, sat):
    """
    Create the monthly Ocean Color netCDF file name according to the year, month and satellite
    :param yy: year
    :type yy: str
    :param mm: month
    :type mm: str
    :param sat: satellite ("Terra" or "Aqua")
    :return: filename
    """

    daysinmonth = calendar.monthrange(yy, mm)[-1]
    dayyearinit = datetime.datetime(yy, mm, 1).timetuple().tm_yday
    dayyearend = datetime.datetime(yy, mm, daysinmonth).timetuple().tm_yday
    filename = "{0}{1}{2}{1}{3}.L3m_MO_SST4_sst4_9km.nc".format(sat[0], yy,
                                                                str(dayyearinit).zfill(3),
                                                                str(dayyearend).zfill(3))
    return filename


def makeclimfilename(yy, mm, sat):
    """
    Create the monthly climatology Ocean Color netCDF file name
    according to the year, month and satellite
    :param yy: year
    :type yy: str
    :param mm: month
    :type mm: str
    :param sat: satellite ("Terra" or "Aqua")
    :return: filename
    """
    yearclimend = yy
    if sat == 'Terra':
        if mm < 2:
            yearcliminit = 2001
        else:
            yearcliminit = 2000
    elif sat == 'Aqua':
        yearcliminit = 2002
    else:
        yearcliminit = 2000

    daysinmonthclim = calendar.monthrange(yearclimend, mm)[-1]
    dayyearinitclim = datetime.datetime(yearcliminit, mm, 1).timetuple().tm_yday
    dayyearendclim = datetime.datetime(yearclimend, mm, daysinmonthclim).timetuple().tm_yday

    filename = "{0}{1}{2}{3}{4}.L3m_MC_SST4_sst4_9km.nc".format(sat[0],
                                                               yearcliminit,
                                                               str(dayyearinitclim).zfill(3),
                                                               yearclimend, str(dayyearendclim).zfill(3))

    return filename