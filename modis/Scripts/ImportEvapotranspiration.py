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
date_string = arcpy.GetParameterAsText(0)  #MM/YYYY
tile_name = arcpy.GetParameterAsText(1)    #hXXvYY
save_path = arcpy.GetParameterAsText(2)    #output location and filename
area = arcpy.GetParameter(3)               #area of interest
units = arcpy.GetParameterAsText(4)        #output units

#Parse Date
d = date_string.split("/")
m = d[0].rjust(2,'0')                                       #month
yr = d[1]                                                   #year
dm = calendar.monthrange(int(yr),int(d[0].lstrip("0")))[1]  #days in month

#Download HDF File
arcpy.AddMessage("Finding File")
ftp_addr = "ftp.ntsg.umt.edu"
ftp = ftplib.FTP(ftp_addr)
ftp.login()

dir_path = "pub/MODIS/Mirror/MOD16/MOD16A2_MONTHLY.MERRA_GMAO_1kmALB/Y" + yr + "/M" + m + "/"

try:
        ftp.cwd(dir_path)
except:
        arcpy.AddMessage("[ERROR] No data for that date")
        sys.exit(0)     #Quit if there is an error in tile or date

try:
        files = ftp.nlst()
except:
        arcpy.AddMessage("[ERROR] Unable to access FTP server")
        sys.exit(0)    #Quit if there is an error with FTP server

hdf_pattern = re.compile('MOD16A2.A'+yr+'M' + m + '.'+tile_name+'.105.*.hdf$', re.IGNORECASE)

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

#Extract Actual Evapotranspiration
arcpy.AddMessage("Converting to Raster")
tile = arcpy.ExtractSubDataset_management(str(L + "/" + matched_file), L + "\\" + tile_name+m+yr, "0")

#Multiply by Scale Factor
arcpy.AddMessage("Converting to Correct Units")
arcpy.env.mask = area                                 #Extract area of interest
tile1 = SetNull(Raster(tile) > 32760, Raster(tile))   #Remove Anomalies

if units == "mm/day":
        tile2 = tile1 * .1 / dm
        
elif units == "mm/month":
        tile2 = tile1 * .1

elif units == "in/month":
        tile2 = tile1 * .1 / 25.4      

#Reproject into Global Coordinate System
arcpy.AddMessage("Projecting into Goode Homolosine")

try:
        home = os.path.expanduser("~")    
        open(home + '\AppData\Roaming\ESRI\Desktop10.0\ArcToolbox\CustomTransformations\MODIS_SINUSOIDAL to GOODE_HOMOLOSINE.gtf')
        output = arcpy.ProjectRaster_management(tile2, save_path, "PROJCS['World_Goode_Homolosine_Land',GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],\
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
        output = arcpy.ProjectRaster_management(tile2, save_path, "PROJCS['World_Goode_Homolosine_Land',GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],\
                                       PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Goode_Homolosine'],PARAMETER['False_Easting',0.0],PARAMETER\
                                       ['False_Northing',0.0],PARAMETER['Central_Meridian',0.0],PARAMETER['Option',1.0],UNIT['Meter',1.0]]", "CUBIC", "#",
                                       "MODIS_SINUSOIDAL to GOODE_HOMOLOSINE", "#", "#")

arcpy.SetParameter(2, output)
