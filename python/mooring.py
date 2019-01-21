#!/usr/bin/python
# coding: utf-8

"""
Module to manipulate more or less cleanly the measurements from the mooring.

Plot sea water temperature and salinity at "Bahia de Palma" and "Canal de
Ibiza buoys.
The time series are represented for selected months and years,
the months are overlaid in order to make easier the comparison for
consecutive years.
"""

import glob
import os
import shutil
import numpy as np
import netCDF4
import matplotlib as mpl
# mpl.use('Agg')      # Necessary for running it with crontab
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
from matplotlib import colors
from matplotlib import dates
import datetime, time, calendar
import locale
import matplotlib.font_manager as fm
import matplotlib.image as image
import logging

locale.setlocale(locale.LC_ALL, 'en_US.utf8')
mpl.rcParams.update({'font.size': 20})
# Use the famous SOCIB font: cube!
prop = fm.FontProperties(fname='/home/ctroupin/.fonts/Cube-Regular2.ttf')
prop = fm.FontProperties(fname="/home/ctroupin/.fonts/Aileron-Regular.otf")

def configure_logging(fname="mooring.log"):
    logger = logging.getLogger("timeseries_logger")
    logger.setLevel(logging.DEBUG)
    # Format for our loglines
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    # Setup console logging
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    # Setup file logging as well
    fh = logging.FileHandler(fname)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger


class Mooring(object):
    """
    Stores the mooring properties and allows for advanced plotting functions
    """

    def __init__(self):
        """
        Initialise with empty arrays
        """
        self.temperature = np.array([])
        self.salinity = np.array([])
        self.date = np.array([])
        self.temperatureQF = np.array([])
        self.salinityQF = np.array([])

    def get_from_nc(self, filename):
        """
        Read the variables from the specified netCDF file
        """
        logger = logging.getLogger("timeseries_logger")
        logger.info('Working on {0}'.format(filename))
        try:
            with netCDF4.Dataset(filename) as nc:
                # Get the variable names based on the standard names
                Tvar = nc.get_variables_by_attributes(standard_name="sea_water_temperature")[0]
                TQFvar = nc.variables[Tvar.ancillary_variables]
                Svar = nc.get_variables_by_attributes(standard_name="sea_water_salinity")[0]
                SQFvar = nc.variables[Svar.ancillary_variables]
                timevar = nc.get_variables_by_attributes(standard_name="time")[0]
                # Get the values
                self.temperature = Tvar[:]
                self.temperatureQF = TQFvar[:]
                self.salinity = Svar[:]
                self.salinityQF = SQFvar[:]
                self.dates = netCDF4.num2date(timevar[:], timevar.units)
        except RuntimeError:
            logger.error('File {0} does not exist (yet)'.format(filename))

        return self

    def apply_qc(self, qf=1):
        """
        Apply quality control to the data by masking the measurements
        of which the QF is different from the specified value
        """
        logger = logging.getLogger("timeseries_logger")
        logger.info('Applying mask to the data')
        self.temperature = np.ma.masked_where(self.temperatureQF != qf, self.temperature)
        self.salinity = np.ma.masked_where(self.salinityQF !=qf, self.salinity)

    def special_qc(self):
        self.temperature = np.ma.masked_where((self.dates >= datetime.datetime(2018, 6, 12)) &
                                           (self.dates <= datetime.datetime(2018, 6, 14, 12, 0, 0)),
                                            self.temperature, copy=True)

    def transf_dates(self, yearmin):
        transfdates = np.array([dd.replace(year=int(yearmin)) for dd in self.dates])
        return transfdates

    def addT_to_plot(self, yearmin, label=None, color="k", linewidth=2, linestyle="-"):
        transfdates = self.transf_dates(yearmin)
        plt.plot(transfdates, self.temperature, label=label,
                color=color, linewidth=linewidth, linestyle=linestyle)
        
    def addS_to_plot(self, yearmin, label=None, color="k", linewidth=2, linestyle="-"):
        transfdates = self.transf_dates(yearmin)
        plt.plot(transfdates, self.salinity, label=label,
                color=color, linewidth=linewidth, linestyle=linestyle)

    def format_plot(self, ax, yearmin, monthmin, monthmax, title=None, prop=None):
        """
        Format the figure to have a cleaner style
        """
        hfmt = dates.DateFormatter('%B')
        ax.xaxis.set_major_locator(dates.MonthLocator())
        ax.xaxis.set_minor_locator(dates.DayLocator())
        ax.xaxis.set_major_formatter(hfmt)
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        for label in ax.get_xticklabels():
            label.set_fontproperties(prop)
        for label in ax.get_yticklabels():
            label.set_fontproperties(prop)

        plt.title(title, fontproperties=prop, fontsize=20)
        transfdates = self.transf_dates(yearmin)
        ax.set_xlim(datetime.datetime(yearmin, monthmin, 1),
                    datetime.datetime(yearmin, monthmax + 1, 1))
        plt.tick_params(axis='both', which='major', labelsize=16)
        plt.tick_params(axis='both', which='minor', labelsize=16)
        #fig.autofmt_xdate()
        hl = plt.legend(loc=4, prop=prop)
        plt.grid()

    def get_max_value(self, maxT=0.0, datemax=datetime.datetime(1900, 1, 1)):
        indmax = np.argmax(self.temperature)
        if self.temperature[indmax] > maxT:
            maxT = self.temperature[indmax]
            datemax = self.dates[indmax]
        return maxT, datemax
    
    def get_max_valueS(self, maxS=0.0, datemax=datetime.datetime(1900, 1, 1)):
        indmax = np.argmax(self.salinity)
        if self.salinity[indmax] > maxS:
            maxS = self.salinity[indmax]
            datemax = self.dates[indmax]
        return maxS, datemax


def main():

    logger = configure_logging()
    logger.info('---Starting new run---')

    # File and directory names
    timenow = datetime.datetime.now().strftime('%Y%m%d_%H%M')

    figdir = "../plots"
    if not(os.path.exists(figdir)):
        os.makedirs(figdir)
        logger.debug("Creating figure directory: {}".format(figdir))
    # figdir2 = "/home/ctroupin/public_html/TemperatureTimeSeries"

    figname1T = "temp_bahiadepalma_" + timenow + '.png'
    figname1Tlatest = "temp_bahiadepalma_latest.png"
    figname2T = "temp_canaldeibiza_" + timenow + '.png'
    figname2Tlatest = "temp_canaldeibiza_latest.png"
    figname1S = "psal_bahiadepalma_" + timenow + '.png'
    figname1Slatest = "psal_bahiadepalma_latest.png"
    figname2S = "psal_canaldeibiza_" + timenow + '.png'
    figname2Slatest = "psal_canaldeibiza_latest.png"

    """
    Generate the file list
    probably a more clever way to do it, but there are several deployments
    for each of the platform and so the names have changed.
    Using new API would be better
    """

    file_basename = "http://thredds.socib.es/thredds/dodsC/mooring/conductivity_and_temperature_recorder/"
    file_list = ['buoy_bahiadepalma-scb_sbe37005/L1/2014/dep0002_buoy-bahiadepalma_scb-sbe37005_L1_2014-06.nc',
                 'buoy_bahiadepalma-scb_sbe37005/L1/2014/dep0002_buoy-bahiadepalma_scb-sbe37005_L1_2014-07.nc',
                 'buoy_bahiadepalma-scb_sbe37005/L1/2014/dep0002_buoy-bahiadepalma_scb-sbe37005_L1_2014-08.nc',
                 'buoy_bahiadepalma-scb_sbe37005/L1/2015/dep0002_buoy-bahiadepalma_scb-sbe37005_L1_2015-06.nc',
                 'buoy_bahiadepalma-scb_sbe37005/L1/2015/dep0002_buoy-bahiadepalma_scb-sbe37005_L1_2015-07.nc',
                 'buoy_bahiadepalma-scb_sbe37005/L1/2015/dep0002_buoy-bahiadepalma_scb-sbe37005_L1_2015-08.nc',
                 'buoy_bahiadepalma-scb_sbe37007/L1/2016/dep0001_buoy-bahiadepalma_scb-sbe37007_L1_2016-06.nc',
                 'buoy_bahiadepalma-scb_sbe37007/L1/2016/dep0001_buoy-bahiadepalma_scb-sbe37007_L1_2016-07.nc',
		         'buoy_bahiadepalma-scb_sbe37007/L1/2016/dep0001_buoy-bahiadepalma_scb-sbe37007_L1_2016-08.nc',
                 'buoy_bahiadepalma-scb_sbe37007/L1/2017/dep0001_buoy-bahiadepalma_scb-sbe37007_L1_2017-06.nc',
                 'buoy_bahiadepalma-scb_sbe37007/L1/2017/dep0001_buoy-bahiadepalma_scb-sbe37007_L1_2017-07.nc',
                 'buoy_bahiadepalma-scb_sbe37007/L1/2017/dep0001_buoy-bahiadepalma_scb-sbe37007_L1_2017-08.nc',
                 'buoy_bahiadepalma-scb_sbe37006/L1/2018/dep0004_buoy-bahiadepalma_scb-sbe37006_L1_2018-06.nc',
                 'buoy_bahiadepalma-scb_sbe37006/L1/2018/dep0004_buoy-bahiadepalma_scb-sbe37006_L1_2018-07.nc',
                 'buoy_bahiadepalma-scb_sbe37006/L1/2018/dep0004_buoy-bahiadepalma_scb-sbe37006_L1_2018-08.nc']
    file_list = [file_basename + s for s in file_list]


    file_list2 = ["buoy_canaldeibiza-scb_sbe37005/L1/2016/dep0003_buoy-canaldeibiza_scb-sbe37005_L1_2016-07.nc",
                  "buoy_canaldeibiza-scb_sbe37005/L1/2016/dep0003_buoy-canaldeibiza_scb-sbe37005_L1_2016-08.nc",
                  "buoy_canaldeibiza-scb_sbe37005/L1/2017/dep0004_buoy-canaldeibiza_scb-sbe37005_L1_2017-06.nc",
                  "buoy_canaldeibiza-scb_sbe37005/L1/2017/dep0004_buoy-canaldeibiza_scb-sbe37005_L1_2017-07.nc",
                  "buoy_canaldeibiza-scb_sbe37005/L1/2017/dep0004_buoy-canaldeibiza_scb-sbe37005_L1_2017-08.nc"
                  ]

    file_list2 = [file_basename + s for s in file_list2]

    colorlist = ["#FDB117", "#20BD00", "#6C5FBA", "#0FB5C4", "k"]
    # Bahia de Palma
    mooring = "Bahia de Palma"
    logger.info('Working on %s data' %(mooring))
    figtitleT = 'Sea water temperature ($^{\circ}$C)\n at %s buoy' %(mooring)
    figtitleS = 'Sea water salinity\n at %s buoy' %(mooring)
    logger.debug('Reading the files')
    buoytemperature, buoysalinity, buoytime, buoydate, buoyyear = read_time_temp_mooring(file_list)
    buoydate = np.array([dd.replace(year=int(buoyyear.min())) for dd in buoydate])
    logger.debug('Creating the plots')
    logger.debug('Temperature')
    plot_mooring_timeseries(buoyyear, buoydate, buoytemperature, figtitleT, os.path.join(figdir, figname1T), colorlist)
    logger.debug('Salinity')
    plot_mooring_timeseries(buoyyear, buoydate, buoysalinity, figtitleS, os.path.join(figdir, figname1S), colorlist)

    # Canal de Ibiza
    """
    mooring = "Canal de Ibiza"
    logger.info('Working on %s data' %(mooring))
    figtitleT = 'Sea water temperature ($^{\circ}$C)\n at %s buoy' %(mooring)
    figtitleS = 'Sea water salinity\n at %s buoy' %(mooring)
    logger.debug('Reading the files')
    buoytemperature, buoysalinity, buoytime, buoydate, buoyyear = read_time_temp_mooring(file_list2)
    buoydate = np.array([dd.replace(year=int(buoyyear.min())) for dd in buoydate])
    logger.debug('Creating the plots')
    logger.debug('Temperature')
    plot_mooring_timeseries(buoyyear, buoydate, buoytemperature, figtitleT, os.path.join(figdir, figname2T))
    logger.debug('Salinity')
    plot_mooring_timeseries(buoyyear, buoydate, buoysalinity, figtitleS, os.path.join(figdir, figname2S))
    """

    # Copy the figures in public html directory
    # logger.info('Making copies of figures into %s' %figdir2)
    # shutil.copy2(os.path.join(figdir, figname1T), os.path.join(figdir2, figname1Tlatest))
    # shutil.copy2(os.path.join(figdir, figname1S), os.path.join(figdir2, figname1Slatest))
    # shutil.copy2(os.path.join(figdir, figname2T), os.path.join(figdir2, figname2Tlatest))
    # shutil.copy2(os.path.join(figdir, figname2S), os.path.join(figdir2, figname2Slatest))

if __name__ == "__main__":
    main()
