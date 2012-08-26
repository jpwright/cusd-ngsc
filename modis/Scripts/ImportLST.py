#Import modules
import ftplib
import re
import arcpy
arcpy.CheckOutExtension("spatial")
from arcpy import env 
from arcpy.sa import *
import os
import sys
import calendar
import datetime
from datetime import date

#Set Parameters
sat_name = arcpy.GetParameterAsText(0)     #Terra or Aqua
date_string = arcpy.GetParameterAsText(1)  #MM/YYYY
tile_name = arcpy.GetParameterAsText(2)    #hXXvYY
save_path = arcpy.GetParameterAsText(3)    #output location and filename
area = arcpy.GetParameter(4)               #area of interest

#Parse Date
d = date_string.split("/")
m = d[0].rjust(2,'0')                                       #month
DOM = str(d[1].rjust(2,'0'))                                #day of month
yr = d[2]                                                   #year
f = date(int(yr),int(m),int(DOM))
DOY = str(f.timetuple().tm_yday).rjust(3,'0')               #day of year

#Convert into NASA terminology
if sat_name == "Terra":
        sat_prefix = "MOD"
        sat_folder = "MOLT"
elif sat_name == "Aqua":
        sat_prefix = "MYD"
        sat_folder = "MOLA"

#Download HDF File
arcpy.AddMessage("Finding File")
ftp_addr = "e4ftl01.cr.usgs.gov"
ftp = ftplib.FTP(ftp_addr)
ftp.login()

dir_path = sat_folder+"/"+sat_prefix+"11A1.005/" +yr+ "." +m+ "." + DOM + "/"

try:
        ftp.cwd(dir_path)
except:
        arcpy.AddMessage("[ERROR] NO Data for that date")
        sys.exit(0)     #Quit if there is an error in tile or date

try:
        files = ftp.nlst()
except:
        arcpy.AddMessage("[ERROR] Unable to access FTP server")
        sys.exit(0)    #Quit if there is an error with FTP server

hdf_pattern = re.compile(sat_prefix + '11A1.A'+yr+DOY+'.'+tile_name+'.005.*.hdf$', re.IGNORECASE)

matched_file = ''

for f in files:
	if re.match(hdf_pattern,f):
		matched_file = f
		break
	
if matched_file == '':
        arcpy.AddMessage("[ERROR] No data for that tile")
        sys.exit(0)     #Quit if there is an error in tile or date                                       

arcpy.AddMessage("Found: " + matched_file)

arcpy.AddMessage("Downloading File")

l = sys.path[0]                      #Find script location
ll = os.path.dirname(l)
L = ll + "\\Scratch"
arcpy.env.scratchWorkspace = L       #Save location for intermediate files

save_file = open(L + "/" + matched_file,'wb')
ftp.retrbinary("RETR "+matched_file, save_file.write)
save_file.close()

ftp.close()

#Extract Daytime Teperature
arcpy.AddMessage("Converting to Raster")
tile = arcpy.ExtractSubDataset_management(str(L + "/" + matched_file), L + "\\" + sat_prefix+DOY+tile_name, "0")

#Multiply by Scale Factor
arcpy.env.mask = area                               #Extract area of interest
arcpy.AddMessage("Converting to Degrees Celsius")
tile1 = Raster(tile) * .02 - 273.15

#Reproject into Global Coordinate System
arcpy.AddMessage("Projecting into Goode Homolosine")

try:
        home = os.path.expanduser("~")    
        open(home + '\AppData\Roaming\ESRI\Desktop10.0\ArcToolbox\CustomTransformations\MODIS_SINUSOIDAL to GOODE_HOMOLOSINE.gtf')
        output = arcpy.ProjectRaster_management(tile1, save_path, "PROJCS['World_Goode_Homolosine_Land',GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],\
                                       PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Goode_Homolosine'],PARAMETER['False_Easting',0.0],PARAMETER\
                                       ['False_Northing',0.0],PARAMETER['Central_Meridian',0.0],PARAMETER['Option',1.0],UNIT['Meter',1.0]]", "CUBIC", "#",
                                       "MODIS_SINUSOIDAL to GOODE_HOMOLOSINE", "#", "#")
except:
        arcpy.CreateCustomGeoTransformation_management("MODIS_SINUSOIDAL to GOODE_HOMOLOSINE",
                                               "PROJCS['Unknown_datum_based_upon_the_custom_spheroid_Sinusoidal',GEOGCS['GCS_Unknown_datum_based_upon_the_custom_spheroid',\
                                               DATUM['D_Not_specified_based_on_custom_spheroid',SPHEROID['Custom_spheroid',6371007.181,0.0]],PRIMEM['Greenwich',0.0],UNIT\
                                               ['Degree',0.0174532925199433]],PROJECTION['Sinusoidal'],PARAMETER['false_easting',0.0],PARAMETER['false_northing',0.0],\
                                               PARAMETER['central_meridian',0.0],UNIT['Meter',1.0]]",
                                               "PROJCS['World_Goode_Homolosine_Land',GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],\
                                               PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Goode_Homolosine'],PARAMETER['False_Easting',0.0],PARAMETER\
                                               ['False_Northing',0.0],PARAMETER['Central_Meridian',0.0],PARAMETER['Option',1.0],UNIT['Meter',1.0]]", "GEOGTRAN[METHOD['Null']]")
        output = arcpy.ProjectRaster_management(tile1, save_path, "PROJCS['World_Goode_Homolosine_Land',GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],\
                                       PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Goode_Homolosine'],PARAMETER['False_Easting',0.0],PARAMETER\
                                       ['False_Northing',0.0],PARAMETER['Central_Meridian',0.0],PARAMETER['Option',1.0],UNIT['Meter',1.0]]", "CUBIC", "#",
                                       "MODIS_SINUSOIDAL to GOODE_HOMOLOSINE", "#", "#")

arcpy.SetParameter(2, output)
