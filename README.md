# WaterNetAnalyzer
....is a QGIS3 plugin to create a water network (sewer network, river network) from a line layer (shapefile). So far the plugin provides three tools. An instructional video can be found [on youtube](https://www.youtube.com/watch?v=3GBr57evQPI) (thanks to Hans van der Kwast)

**Installation:** 
* *Option 1: from zip-File (latest Versions will appear here first)*
  * Download the Git repository as zip-File 
  * In QGIS3 go to Plugins > Manage and install Plugins > Install from ZIP
  * select downloaded zip-File
* *Option 2: from Qgis Plugin Manager*
  * In QGIS3 go to Plugins > Manage and install Plugins 
  * search for 'WaterNetAnalyzer' and directly install by clicking on 'install plugin' 

The plugin should appear in your Processing Toolbox. 
An example line layer can be found in [the testdata folder](/testdata).

## 1 Water Network Constructor
The first tool adds information about connections in the network to the attribute table (the simple algorithm is shown in the figure below). Worflow / Options
1. Select the undermost line segment (e.g. in a sewage system it´s the last one before entering a treatment plant, in a river system it´s the river mouth). New in version 1.99 (experimental): select multiple line segments for multiple independent networks at once.
2. The tool can automatically change line directions according to or against flow directions (new in version 1.10) if you choose this option
3. From version 1.4 on, you can choose an already existing column of the attribute table as "NET_ID" (se below) or generate a new one.
4. To ignore small gaps between vertices you can define a search radius (new in version 1.99)

![Network Algorithm](/help/images/Netz_erstellen2.png)

The tool will create three new columns in the attribute table: 
* "NET_ID"  an individual identification number for every line segment
* "NET_TO"  the NET_ID-number of the next segment (and node)
* "NET_FROM" the identification number of the previous node (which is the same as NET_ID)

If the algorithm finds circles, you´ll get a warning in the processing feedback with information about the segments which closed the circle. You can edit "NET_TO" and "NET_FROM" manually to change flow directions an even ad "forks" to your network.

## 2 Flow path upstream/downstream
The second tool uses the columns created by *1 Water Network Constructor* to find the flow path upstream or downstream of a selected line segment in the water network. 
You can also choose other columns than "NET_ID","NET_TO" and "NET_FROM", if you have this information already in your attribute table.

## 3 Calculate along flow path
This tool can calculate how amounts of water or other loads are accumulated along the flow path. Select a column in the attribute table to accumulate (it has to be numeric). The tool will create a new column with the result.


## Developement / Funding
If you have any suggestions for improvements feel free to write an issue or create a fork. 
First versions of this plugin have been developed within the project PROSPER-RO, funded by BMBF, grant number 033L212
