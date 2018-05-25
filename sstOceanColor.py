import numpy as np
import netCDF4
import calendar
import datetime
import cmocean
import matplotlib.pyplot as plt


class windfield(object):
    """
    SST field is made of coordinates (lon, lat) and Sea Surface Temperature
    """

    def __init__(self):
        self.lon = None
        self.lat = None
        self.u = None
        self.v = None
        self.datetime = None
        self.utime = None
        self.vtime = None
        self.speed = None
        self.latregion = None
        self.lonregion = None
        self.uregion = None
        self.vregion = None

    def readfile(self, filename):
        with netCDF4.Dataset(filename, 'r') as nc:
            lonvar = nc.get_variables_by_attributes(long_name="longitude")[0]
            latvar = nc.get_variables_by_attributes(long_name="latitude")[0]
            uvar = nc.get_variables_by_attributes(long_name="10 metre U wind component")[0]
            vvar = nc.get_variables_by_attributes(long_name="10 metre V wind component")[0]
            timevar = nc.get_variables_by_attributes(long_name="time")[0]
            self.lon = nc.variables[lonvar.name][:]
            self.lat = nc.variables[latvar.name][:]
            self.u = nc.variables[uvar.name][:]
            self.v = nc.variables[vvar.name][:]
            self.datetime = netCDF4.num2date(nc.variables[timevar.name][:],
                                             nc.variables[timevar.name].units)

            self.lon[self.lon > 180.] -= 360.

        return self

    def extractime(self, year, month):
        """

        :param year: year of interest
        :param month: month of interest
        :return:
        """
        timeindex = np.where(self.datetime == datetime.datetime(year, month, 1, 0, 0))[0][0]
        self.utime = self.u[timeindex, :, :]
        self.vtime = self.v[timeindex, :, :]
        self.speed = np.sqrt(self.utime * self.utime +
                             self.vtime * self.vtime)
        return self

    def extractdomain(self, domain):
        """
        Extract the field and coordinate values in the specified region
        :param domain: domain of interest: tuple (lonmin lonmax latmin latmax)
        :type domain: tuple
        """
        goodlon = np.where((self.lon >= domain[0]) & (self.lon <= domain[1]))[0]
        goodlat = np.where((self.lat >= domain[2]) & (self.lat <= domain[3]))[0]
        self.lonregion = self.lon[goodlon]
        self.latregion = self.lat[goodlat]
        self.uregion = self.utime[goodlat, :]
        self.uregion = self.uregion[:, goodlon]
        self.vregion = self.vtime[goodlat, :]
        self.vregion = self.vregion[:, goodlon]
        self.speedregion = self.speed[goodlat, :]
        self.speedregion = self.speedregion[:, goodlon]

    def plot_global(self, m, **kwargs):
        fig = plt.figure(figsize=(10, 10))
        llon, llat = np.meshgrid(self.lon, self.lat)
        long, latg = m(llon, llat)
        # Mask bad values
        long[long == long.max()] = np.nan
        latg[latg == latg.max()] = np.nan

        m.quiver(long, latg, self.utime, self.vtime, self.speed, **kwargs)
        m.drawcoastlines(linewidth=.2)
        m.fillcontinents(color="k")


class SSTfield(object):
    """
    SST field is made of coordinates (lon, lat) and Sea Surface Temperature
    """

    def __init__(self):
        self.lon = None
        self.lat = None
        self.sst = None
        self.lonregion = None
        self.latregion = None
        self.sstregion = None

    def readfile(self, filename):
        with netCDF4.Dataset(filename) as nc:
            sstvar = nc.get_variables_by_attributes(standard_name="sea_surface_temperature")[0]
            sstvarname = sstvar.name
            self.lon = nc.variables['lon'][:]
            self.lat = nc.variables['lat'][:]
            self.sst = nc.variables[sstvarname][:]
        return self

    def extractdomain(self, domain):
        """
        Extract the field and coordinate values in the specified region
        :param domain: domain of interest: tuple (lonmin lonmax latmin latmax)
        :type domain: tuple
        """
        goodlon = np.where((self.lon >= domain[0]) & (self.lon <= domain[1]))[0]
        goodlat = np.where((self.lat >= domain[2]) & (self.lat <= domain[3]))[0]
        self.lonregion = self.lon[goodlon]
        self.latregion = self.lat[goodlat]
        self.sstregion = self.sst[goodlat, :]
        self.sstregion = self.sstregion[:, goodlon]

        return self

    def plotfield(self, map, domain, figtitle=None):

        llon, llat = np.meshgrid(self.lonregion, self.latregion)
        lonp, latp = map(llon, llat)

        plt.figure(figsize=(10, 8))
        pcm = map.pcolormesh(lonp, latp, self.sstregion, cmap=cmocean.cm.thermal)
        plt.colorbar(pcm, extend='both', orientation='horizontal', shrink=0.95, pad=0.06)
        plt.title(figtitle)
        map.drawcoastlines(linewidth=0.2)
        map.fillcontinents(color=".2")
        map.drawmeridians(np.arange(domain[0], domain[1], domain[-2]),
                            labels=[0, 0, 0, 1], linewidth=0.2)
        map.drawparallels(np.arange(domain[2], domain[3], domain[-1]),
                            labels=[1, 0, 0, 0], linewidth=0.2)
        return plt

    def plotanom(self, map, domain, figtitle=None):

        llon, llat = np.meshgrid(self.lonregion, self.latregion)
        lonp, latp = map(llon, llat)

        plt.figure(figsize=(10, 8))
        pcm = map.pcolormesh(lonp, latp, self.sstregion, cmap=plt.cm.RdBu_r, vmin=-3, vmax=3)
        plt.colorbar(pcm, extend='both', orientation='horizontal', shrink=0.95, pad=0.06)
        plt.title(figtitle)
        map.drawcoastlines(linewidth=0.2)
        map.fillcontinents(color=".2")
        map.drawmeridians(np.arange(domain[0], domain[1], domain[-2]),
                            labels=[0, 0, 0, 1], linewidth=0.2)
        map.drawparallels(np.arange(domain[2], domain[3], domain[-1]),
                            labels=[1, 0, 0, 0], linewidth=0.2)
        return plt


def makemonthfilename(yy, mm, sat):
    """
    Create the monthly Ocean Color netCDF file name according to the year, month and satellite
    :param yy: year
    :type yy: int
    :param mm: month
    :type mm: int
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
    :type yy: int
    :param mm: month
    :type mm: int
    :param sat: satellite ("Terra" or "Aqua")
    :type sat: str
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
