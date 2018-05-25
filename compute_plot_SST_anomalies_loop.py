import sstOceanColor
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
from matplotlib import rcParams
import calendar
import logging
import warnings
import cmocean
import datetime
import matplotlib.cbook
warnings.filterwarnings("ignore", category=matplotlib.cbook.mplDeprecation)

# Configuration
logging.basicConfig(format='%(asctime)s | %(levelname)s : %(message)s',
                    level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Font size
rcParams.update({'font.size': 22})

# Period and directories
year = 2018
now = datetime.datetime.now()
currentyear = now.year
# monthlist = [1, 2, 3, 4, 5, 6, 7, 8]
monthlist = [1]
satellite = 'Terra'
datamonthdir = "/home/ctroupin/Data/SST/Global/monthly/"
dataclimdir = "/home/ctroupin/Data/SST/Global/monthly_clim/"
figdir = ["/home/ctroupin/Data/SST/figures/MedSea",
          "/home/ctroupin/Data/SST/figures/Canary",
          "/home/ctroupin/Data/SST/figures/Global"]

# Domains: MedSea and North Atlantic
domainlist = [(-7.0, 36.0, 30.0, 47.0, 8., 4.),
              (-80, 0, 0., 40., 15., 10.)]

# Create the projections
m = []
i = 0
for domain in domainlist:
    i += 1
    logging.info("Preparing basemap for domain: {}".format(i))
    m.append(Basemap(projection='merc', llcrnrlon=domain[0], llcrnrlat=domain[2],
                     urcrnrlon=domain[1], urcrnrlat=domain[3], lat_ts=0.5*(domain[0] + domain[2]),
                     resolution='h'))

mg = Basemap(projection='ortho', lon_0=-15, lat_0=20, resolution='i')

for month in monthlist:
    logger.info("Working on month {0}".format(month))

    # Create file names and check if they exist
    MonthlyFileName = sstOceanColor.makemonthfilename(year, month, satellite)

    MonthlyClimFileName = sstOceanColor.makeclimfilename(currentyear, month, satellite)
    if not(os.path.exists(os.path.join(dataclimdir, MonthlyClimFileName))):
        logger.warn("No monthly climatology file for year {}".format(currentyear))
        logger.warn("Will use the file for year {}".format(currentyear-1))
        MonthlyClimFileName = sstOceanColor.makeclimfilename(currentyear-1, month, satellite)

    logger.info("Monthly file: {}".format(MonthlyFileName))
    logger.info("Monthly climatology file: {}".format(MonthlyClimFileName))

    # Create figure names
    mmonth = str(month).zfill(2)
    fignameregion = 'SST_anomaly_{0}_{1}_{2}'.format(satellite, year, mmonth)
    fignameregionfield = 'SST_{0}_{1}_{2}'.format(satellite, year, mmonth)
    fignameglob = 'SST_anomaly_global_{0}_{1}_{2}'.format(satellite, year, mmonth)
    fignameglobfield = 'SST_global_{0}_{1}_{2}'.format(satellite, year, mmonth)
    logger.info(fignameregion)

    # Read SST
    # (whole field, so that we can loop and perform extractions)
    fname = os.path.join(datamonthdir, MonthlyFileName)
    if os.path.exists(fname):
        sstmonth = sstOceanColor.SSTfield().readfile(fname)
    else:
        logger.error("The file {} does not exist".format(fname))

    fname = os.path.join(dataclimdir, MonthlyClimFileName)
    if os.path.exists(fname):
        sstclim = sstOceanColor.SSTfield().readfile(fname)
    else:
        logger.error("The file {} does not exist".format(fname))

    # Compute anomalies
    sstanom = sstOceanColor.SSTfield()
    sstanom.lon = sstmonth.lon
    sstanom.lat = sstmonth.lat
    sstanom.sst = sstmonth.sst - sstclim.sst
    logger.debug("Size of SST matrix: {}".format(sstanom.sst.shape))

    figtitleanom = "SST anomalies ($^\circ$C) $-$ Satellite {0} \n{1} {2}".format(satellite,
                                                                              calendar.month_name[month],
                                                                              str(year))
    figtitlefield = "SST ($^\circ$C) $-$ Satellite {0} \n{1} {2}".format(satellite,
                                                                             calendar.month_name[month],
                                                                             str(year))

    # Loop on domains
    for ii, domain in enumerate(domainlist):

        # Plot SST field
        sstmonth.extractdomain(domain)
        sstmonth.plotfield(m[ii], domain, figtitlefield)
        plt.savefig(os.path.join(figdir[ii], "".join((fignameregionfield, '_', str(ii), ".png"))),
                    dpi=300, bbox_inches='tight')


        # Plot anomalies
        sstanom.extractdomain(domain)
        sstanom.plotanom(m[ii], domain, figtitleanom)
        plt.savefig(os.path.join(figdir[ii], "".join((fignameregion, '_', str(ii), ".png"))),
                    dpi=300, bbox_inches='tight')
        plt.close()


    # Global map
    # (no domain extraction)
    llon, llat = np.meshgrid(sstanom.lon, sstanom.lat)
    long, latg = mg(llon, llat)
    long[long == long.max()] = np.nan
    latg[latg == latg.max()] = np.nan

    # Field
    plt.figure(figsize=(10, 10))
    pcm = mg.pcolormesh(long, latg, sstmonth.sst, cmap=cmocean.cm.thermal, vmin=0., vmax=30.)
    plt.colorbar(pcm, extend='both', orientation='horizontal', shrink=0.85, pad=0.02)
    plt.title(figtitlefield)
    mg.drawcoastlines(linewidth=0.2)
    mg.fillcontinents(color=".2")
    plt.savefig(os.path.join(figdir[-1], fignameglobfield), dpi=300, bbox_inches='tight')
    plt.close()


    # Anomalies
    plt.figure(figsize=(10, 10))
    pcm = mg.pcolormesh(long, latg, sstanom.sst, cmap=plt.cm.RdBu_r, vmin=-3, vmax=3)
    plt.colorbar(pcm, extend='both', orientation='horizontal', shrink=0.85, pad=0.02)
    plt.title(figtitleanom)
    mg.drawcoastlines(linewidth=0.2)
    mg.fillcontinents(color=".2")
    plt.savefig(os.path.join(figdir[-1], fignameglob), dpi=300, bbox_inches='tight')
    # plt.show()
    plt.close()
