# -*- coding: cp1252 -*-
# Author: Jason Parent
# Modified By: Robert McCann
# Date: May 3, 2008
# Modified: June 6, 2008
# Purpose: Convert kml file to shapefile with feature name and description as attributes
# Modified to read kml folder and attribute to shapefile

import arcgisscripting, os, sys

# create geoprocessor...
gp = arcgisscripting.create()

gp.OverwriteOutput = 1

# data management toolbox...
management_tbx = r"C:\Program Files\ArcGIS\ArcToolbox\Toolboxes\Data Management Tools.tbx"

# check if data management toolbox is found...
if not gp.exists(management_tbx):
    gp.AddError("ArcGIS Data Management Toolbox not found. Script cannot execute")
    sys.exit(1)

# load toolbox...
gp.AddToolbox (management_tbx)

# script parameters...

kmlFile = sys.argv[1]       # kml file
featureType = sys.argv[2]   # POLYGON, POLYLINE, POINT
outName = sys.argv[3]       # output file name


featureType = featureType.upper()   # convert to uppercase

#------------------------------------------------------------------------
# GET FEATURE DATA FROM KML FILE...

gp.AddMessage("Extracting %s feature data from KML file..." % featureType)
print "Extracting %s feature data from KML file..." % featureType

try:

    # list for feature data...
    fileDataLst = []

    # open kml file...
    openFile = open(kmlFile, "r")
    line = openFile.readline()

    #declare folder hierachy list
    folderlist = []
    folder = ""
    # read through each line and identify lines with data...

    while line:
        # If folder section exists, add it's name to folder list
        # <Folder> indicates a folder section
        if "<Folder>" in line:
            # get folder name...
            line = openFile.readline()
            if "/name" in line:
                start, end = line.find(">"), line.rfind("<")
                folderlist.append(line[start+1:end])
        
        # If folder section closes, remove it's value from the list
        if "</Folder>" in line:
            del folderlist[len(folderlist)-1]
            
        if "Placemark" in line:
            name = description = ""
            XYLst = []  # list for vertex coordinates

            # read line by line until the end of feature section (indicated by Placemark)
            while "/Placemark" not in line:

                # get feature type...
                if "Polygon" in line: feature = "POLYGON"
                elif "LineString" in line: feature = "POLYLINE"
                elif "Point" in line: feature = "POINT"

                # get feature name...
                if "/name" in line:
                    start, end = line.find(">"), line.rfind("<")
                    name = line[start+1:end]

                # get feature description...
                if "/description" in line:
                    start, end = line.find(">"), line.rfind("<")
                    description = line[start+1:end]

                # get coordinates of vertices...
                if "/coordinates" in line:
                    # extract coordinate section...
                    end = line.rfind("<")
                    line = line[:end]
                    start = line.find(">")

                    # if found (only found for point features)...
                    if start != -1:
                        line = line[start+1:]   # extract after > symbol

                    # list of XYZ strings for vertices...
                    coordinateLst = line.rstrip(" </coordinates>\n").split(" ")

                    # extract XY coordinates for each vertex
                    if coordinateLst[0] <> '':
                        for XYZ in coordinateLst:
                            XYZ = XYZ.split(",")
                            XYLst.append([float(XYZ[0]), float(XYZ[1])])
                    else:
                        XYLst = []

                line = openFile.readline()  # get next line

            # if feature is of specified type, add to data list...
            if feature == featureType:
                folder = '/'.join(folderlist) #join folder list to string seperated by '/'
                fileDataLst.append([name,description,XYLst,folder])
                
        line = openFile.readline()  # get next line

    # close kml file...
    openFile.close()

    # number of features added to shapefile...
    numFeatures = len(fileDataLst)

    gp.AddMessage("Feature data acquired for %s %s features." % (numFeatures,featureType))
    print "Feature data acquired for %s %s features." % (numFeatures,featureType)

    #------------------------------------------------------------------------
    # CREATE NEW SHAPEFILE TO CONTAIN FEATURE(S)

    if numFeatures > 0:

        gp.AddMessage("Creating shapefile")
        print "Creating shapefile"

        # geographic projection file (projection of google earth)...
        # spat_ref = r"C:\Program Files\ArcGIS\Coordinate Systems\Geographic Coordinate Systems\World\WGS 1984.prj"

        # factory code for GCS_WGS_1984...
        spat_ref = "4326"

        # get workspace and basename from output file name...
        outWksp = os.path.split(outName)[0]
        basename = os.path.split(outName)[-1]

        # create output shapefile...    
        gp.CreateFeatureClass_management (outWksp, basename, featureType, "", "", "", spat_ref)

        # add name and description fields...
        gp.addfield(outName, "NAME", "text", "", "", "50")
        gp.addfield(outName, "DESCR", "text", "", "", "200")
        gp.addfield(outName, "FOLDER", "text", "", "", "100")

        # create insert cursor and new row for output file...
        cur = gp.InsertCursor(outName)
        newRow = cur.newRow()

        cnt = 0            

        # for each feature...
        for feat in fileDataLst:

            #------------------------------------------------------------------------
            # CREATE FEATURE FROM COORDINATES AND ADD TO OUTPUT SHAPEFILE...

            name = feat[0]
            description = feat[1]
            XYLst = feat[2]
            folder = feat[3]

            if len(XYLst) == 0:
                gp.AddWarning("Cannot convert feature named %s to shapefile" % name)
                continue

            # create point object...
            pnt = gp.CreateObject("point")

            # if feature is a polygon or line...
            if featureType == "POLYGON" or featureType == "POLYLINE":
                array = gp.CreateObject("array")    # create an array

                # for each vertex...
                for XY in XYLst:
                    pnt.X, pnt.Y = XY[0], XY[1] # assign point coordinates
                    array.add(pnt)      # add point to array

                newRow.Shape = array    # set shape property for new row

            # if feature is a point...
            else:
                pnt.X, pnt.Y = XYLst[0][0], XYLst[0][1]     # assign point coordinates
                newRow.Shape = pnt          # set shape property for new row

            # set name and description field values...
            newRow.NAME = name
            newRow.DESCR = description
            newRow.FOLDER = folder

            # insert row into output shapefile    
            cur.InsertRow(newRow)

            cnt += 1
            if cnt % 50 == 0:                
                gp.AddMessage("Created %s %s feature" % (cnt,featureType))
                print "Created %s %s feature" % (cnt,featureType)

        # delete insert cursor and new row...
        del cur,newRow

        gp.AddMessage("KML to shapefile conversion complete")
        print "KML to shapefile conversion complete"

    else:
        gp.AddWarning("No %s features found - aborting kml to shapefile conversion...\n" % (featureType))

except:
    gp.AddError("Unexpected Error: %s" % sys.exc_info()[0])
