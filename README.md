# WaterNetAnalyzer
....is a QGIS3 plugin to create a water network (sewer network, river network) from a line layer (shapefile). So far the plugin provides three tools. 
**Installation:** 
* Download the Git repository as zip-File 
* In QGIS3 go to Plugins > Manage and install Plugins > Install from ZIP
* select downloaded zip-File

The plugin should appear in your Processing Toolbox. 
An example line layer can be found in [the testdata folder](/testdata)

## 1 Water Network Constructor
The first tool adds information about connections in the network to the attribute table (the simple algorithm is shown in the figure below). You just have to select the undermost line segment (e.g. in a sewage system it´s the last one before entering a treatment plant, in a river system it´s the river mouth) and click on "Run". 

![Network Algorithm](/help/images/Netz_erstellen1.png)

The tool will create three new columns in the attribute table: 
* "NET_ID"  an individual identification number for every line segment
* "NET_TO"  the NET_ID-number of the next segment (and node)
* "NET_FROM" the identification number of the previous node (which is the same as NET_ID)

If the algorithm find circles you´ll get a warning in the processing feedback with information about the segments which closed the circle. 

## 2 Select catchment or flow path
The second tool uses the columns created by *1 Water Network Constructor* to find the catchment or flow path of a selected line segment in the water network. 
You can also choose other columns than "NET_ID","NET_TO" and "NET_FROM" if you have this information already in your attribute table.

## 3 Calculate along flow path
This tool can calculate how amounts of water or other loads are accumulated along the flow path. 
