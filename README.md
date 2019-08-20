# WaterNetPlugin
....is a QGIS3 plugin to create a water network (sewer network, river network) from a line layer (shapefile). So far the plugin provides three tools. 

## 1 Water Network Constructor
The first one adds information about connections in the network to the attribute table (the simple algorithm is shown in the figure below). You just have to select the undermost line segment (e.g. in a sewage system it´s the last one before entering a treatment plant, in a river system it´s the river mouth) and click on "Run". 

![Network Algorithm](/help/images/Netz_erstellen1.png)

The tool will create three new columns in the attribute table: 
* "NET_ID"  an individual identification number for every line segment
* "NET_TO"  the NET_ID-number of the next segment (and node)
* "NET_FROM" the identification number of the previous node (which is the same as NET_ID)

## 2 Select catchment or flow path
The second tool uses the columns created by *1 Water Network Constructor* to find the catchment or flow path of a selected line segment in the water network. As the algorithm uses the QGIS feature id, it doesn´t work with temporary layers. So you´ll have to save the result from *1 Water Network Constructor* somewhere before running *2 Select catchment or flow path*

## Calculate along flow path
This tool can calculate how amounts of water or other loads are accumulated along the flow path. As well as *2 Select catchment or flow path* this doesn´t work with temporary layers
