import netCDF4
import sstOceanColor
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
from matplotlib import rcParams
from matplotlib import rc
import datetime
import calendar
import logging
import warnings
import matplotlib.cbook
warnings.filterwarnings("ignore", category=matplotlib.cbook.mplDeprecation)


# The data files in netCDF format are obtained from https://oceandata.sci.gsfc.nasa.gov/.<br>
# The plots are created using the 9 km resolution file, which are sufficient for our purpose.

# Configuration
logging.basicConfig(format='%(asctime)s | %(levelname)s : %(message)s',
                    level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Font size
rcParams.update({'font.size': 22})

# Period and directories
year = 2017
monthlist = [1, 2, 3, 4, 5, 6, 7, 8]
# monthlist = [1]
satellite = 'Terra'
datamonthdir = "/home/ctroupin/Data/SST/Global/monthly/"
dataclimdir = "/home/ctroupin/Data/SST/Global/monthly_clim/"
figdir = ["/home/ctroupin/Data/SST/figures/MedSea",
          "/home/ctroupin/Data/SST/figures/Canary",
          "/home/ctroupin/Data/SST/figures/Global"]

# Domains
domainlist = [(-7.0, 36.0, 30.0, 47.0, 8., 4.),
              (-80, 0, 0., 40., 15., 10.)]


# Create the projections
m = []
for domain in domainlist:
    m.append(Basemap(projection='merc', llcrnrlon=domain[0], llcrnrlat=domain[2],
                     urcrnrlon=domain[1], urcrnrlat=domain[3], lat_ts=0.5*(domain[0] + domain[2]),
                     resolution='h'))

mg = Basemap(projection='ortho', lon_0=-15, lat_0=20, resolution='i')


for month in monthlist:
    logger.info("Working on month {0}".format(month))

    # Create file names and check if they exist
    MonthlyFileName = sstOceanColor.makemonthfilename(year, month, satellite)
    MonthlyClimFileName = sstOceanColor.makeclimfilename(year, month, satellite)

    # Create figure names
    fignameregion = 'SST_anomaly_{0}_{1}_{2}'.format(satellite, year, month)
    fignameglob = 'SST_anomaly_global_{0}_{1}_{2}'.format(satellite, year, month)
    logger.info(fignameregion)

    # Read SST
    with netCDF4.Dataset(os.path.join(datamonthdir, MonthlyFileName)) as nc:
        sstvar = nc.get_variables_by_attributes(standard_name="sea_surface_temperature")[0]
        sstvarname = sstvar.name
        lon = nc.variables['lon'][:]
        lat = nc.variables['lat'][:]
        sst = nc.variables[sstvarname][:]

    with netCDF4.Dataset(os.path.join(dataclimdir, MonthlyClimFileName)) as nc:
        sstclim = nc.variables[sstvarname][:]

    # Compute anomalies
    sstanom = sst - sstclim
    logger.debug(sstanom.shape)

    figtitle = "SST anomalies ($^\circ$C) $-$ Satellite {0} \n{1} {2}".format(satellite,
                                                                                  calendar.month_name[month],
                                                                                  str(year))
    # Loop on domains
    for ii, domain in enumerate(domainlist):
        goodlon = np.where((lon >= domain[0]) & (lon <= domain[1]))[0]
        goodlat = np.where((lat >= domain[2]) & (lat <= domain[3]))[0]
        lond = lon[goodlon]
        latd = lat[goodlat]
        sstanomplot = sstanom[goodlat, :]
        sstanomplot = sstanomplot[:, goodlon]

        llon, llat = np.meshgrid(lond, latd)
        lonp, latp = m[ii](llon, llat)

        print(llon.shape)

        plt.figure(figsize=(10, 8))
        pcm = m[ii].pcolormesh(lonp, latp, sstanomplot, cmap=plt.cm.RdBu_r, vmin=-3, vmax=3)
        plt.colorbar(pcm, extend='both', orientation='horizontal', shrink=0.95, pad=0.06)
        plt.title(figtitle)
        m[ii].drawcoastlines(linewidth=0.2)
        m[ii].fillcontinents(color=".2")
        m[ii].drawmeridians(np.arange(domain[0], domain[1], domain[-2]), labels=[0, 0, 0, 1], linewidth=0.2)
        m[ii].drawparallels(np.arange(domain[2], domain[3], domain[-1]), labels=[1, 0, 0, 0], linewidth=0.2)
        plt.savefig(os.path.join(figdir[ii], "".join((fignameregion, '_', str(ii), ".png"))), dpi=300, bbox_inches='tight')
        plt.close()

    # Global map

    llon, llat = np.meshgrid(lon, lat)
    long, latg = mg(llon, llat)
    long[long == long.max()] = np.nan
    latg[latg == latg.max()] = np.nan

    plt.figure(figsize=(10, 10))
    pcm = mg.pcolormesh(long, latg, sstanom, cmap=plt.cm.RdBu_r, vmin=-3, vmax=3)
    plt.colorbar(pcm, extend='both', orientation='horizontal', shrink=0.85, pad=0.02)
    plt.title(figtitle)
    mg.drawcoastlines(linewidth=0.2)
    mg.fillcontinents(color=".2")
    plt.savefig(os.path.join(figdir[-1], fignameglob), dpi=300, bbox_inches='tight')
    plt.show()
    plt.close()
