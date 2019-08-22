# -*- coding: utf-8 -*-

"""
/***************************************************************************
 WaterNets
                                 A QGIS plugin
 This plugin calculates flowpaths
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2019-07-26
        copyright            : (C) 2019 by Jannik Schilling
        email                : jannik.schilling@uni-rostock.de
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = 'Jannik Schilling'
__date__ = '2019-07-26'
__copyright__ = '(C) 2019 by Jannik Schilling'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import *
import processing
import numpy as np
from collections import Counter

class WaterNetwConstructor(QgsProcessingAlgorithm):
    INPUT_LAYER = 'INPUT_LAYER'
    OUTPUT = 'OUTPUT'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_LAYER,
                self.tr('Line Layer representing a water network'),
                [QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Water network')
            )
        )
          
    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(
            parameters,
            self.INPUT_LAYER,
            context
        )

        rawLayer = self.parameterAsVectorLayer(
            parameters,
            self.INPUT_LAYER,
            context
        )
        if rawLayer is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))
        raw_fields = rawLayer.fields()


        '''check if one feature is selected'''
        selFeat = rawLayer.selectedFeatures() #selected Feature
        if not selFeat:
            feedback.reportError(self.tr('{0}: No segment selected. Please select outlet in layer "{1}" ').format(self.displayName(), parameters[self.INPUT_LAYER]))
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT_LAYER))
        if len(selFeat) > 1:
            feedback.reportError(self.tr('{0}: Too many segments selected. Please select outlet in layer "{1}" ').format(self.displayName(), parameters[self.INPUT_LAYER]))
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT_LAYER))
        sel_feat_id = str(selFeat[0].id())


        '''add new fields'''
        #define new fields
        out_fields = QgsFields()
        #append fields
        for field in raw_fields:
            out_fields.append(QgsField(field.name(), field.type()))
        out_fields.append(QgsField('NET_ID', QVariant.String))
        out_fields.append(QgsField('NET_TO', QVariant.String))
        out_fields.append(QgsField('NET_FROM', QVariant.String))

        '''get features'''
        rawFt = rawLayer.getFeatures()
        Data = []
        for ft in rawFt:
            if feedback.isCanceled():
                break
            ge = ft.geometry()
            if ge.isMultipart():
                vert1 = ge.asMultiPolyline()[0][0]
                vert1x = [round(vert1.x()),"_",round(vert1.y())]
                vert2 = ge.asMultiPolyline()[0][-1]
                vert2x = [round(vert2.x()),"_",round(vert2.y())]
            else: 
                pass
            SP1 = "".join(str(x) for x in vert1x)
            SP2 = "".join(str(x) for x in vert2x)
            Data=Data+[[SP1,SP2]+[ft.id(),"NULL"]]
        data_arr = np.array(Data)
        feedback.setProgressText(self.tr("Data loaded without problems\n "))


        '''first segment'''
        act_segm = data_arr[np.where(data_arr[:,2]==sel_feat_id)][0]


        '''id of actual/first segment'''
        act_id = act_segm[2]

        '''mark segment as outlet'''
        Marker = "Out"
        data_arr[np.where(data_arr[:,2] == act_segm[2])[0][0],3] = Marker

        '''store first segment and delete from data_arr'''
        finished_segm = data_arr[np.where(data_arr[:,2]==sel_feat_id)]
        data_arr = np.delete(data_arr, np.where(data_arr[:,2]==act_id)[0],0)


        '''function to find the next segment upstream'''
        def nextftsConstr (a_segm):
            all_pts = np.concatenate((data_arr[:,0],data_arr[:,1]))
            vert1 = a_segm[0]
            vert2 = a_segm[1]
            if np.isin(vert1,all_pts):
                conn_vert = vert1
                n_segm = np.concatenate((data_arr[data_arr[:,1] == conn_vert],data_arr[data_arr[:,0] == conn_vert]))
            elif np.isin(vert2,all_pts):
                conn_vert = vert2
                n_segm = np.concatenate((data_arr[data_arr[:,1] == conn_vert],data_arr[data_arr[:,0] == conn_vert]))
            else:
                n_segm=n_segm = np.array([])
                conn_vert = 'None'
            return([n_segm,conn_vert])




        '''this function will find circles'''
        def checkForCircles (ne_segm, conn_v):
            all_finished_pts = np.concatenate((finished_segm[:,0],finished_segm[:,1]))
            all_act_pts = np.concatenate((ne_segm[:,0],ne_segm[:,1]))
            pts_count = Counter(all_act_pts)
            count_arr = np.array(list(pts_count.items()))
            '''Option 1: any vertex of ne_segm already is in finished_segm'''
            count_arr2 = np.delete(count_arr, np.where(count_arr[:,0] == conn_v)[0],0)
            circ_segm1 = ne_segm[np.all(np.isin(ne_segm[:,:2],all_finished_pts),axis = 1)]
            circ_segm2 = finished_segm[np.any(np.isin(finished_segm[:,:2],count_arr2[:,0]), axis= 1)]
            circ_segm = np.array(circ_segm2.tolist()+circ_segm1.tolist())
            if len (circ_segm) > 0:
                circ_id = [circ_segm[:,2].tolist()]
            else: 
                circ_id = []
            '''Option 2: two (or more) segments of ne_segm form a circle'''
            if len(ne_segm) > 1:
                count_arr3 = np.delete(count_arr, np.where(count_arr[:,1] == '1')[0],0)
                circ_segm = ne_segm[np.all(np.isin(ne_segm[:,:2],count_arr3[:,0]),axis = 1)]
                circ_id = circ_id + [circ_segm[:,2].tolist()]
            circ_ids = [x for x in circ_id if x]
            return (circ_ids)

        '''list to save circles if the algothm finds one'''
        circ_list = list() 


        ''' "do later list" with 'X' as marker'''
        do_later=np.array([['X','X','X','X']])


        i=1
        while len(data_arr) != 0:
            '''id of next segment'''
            next_data = nextftsConstr(act_segm)
            next_fts = next_data[0]
            conn_vertex = next_data[1]
            '''check for circles'''
            if len(next_fts)>0:
                circ_segments = checkForCircles(next_fts, conn_vertex)
                circ_list = circ_list + circ_segments
            '''handle next features'''
            if len(next_fts) == 1:
                next_fts[:,3] = str(act_id)
                '''store first segment and delete from data_arr'''
                finished_segm = np.concatenate((finished_segm,next_fts))
                data_arr = np.delete(data_arr,np.where(data_arr[:,2] == next_fts[:,2]),0)
                ''' upstream segment'''
                next_segm = next_fts[0]
            if len(next_fts) == 0:
                ''' upstream segment'''
                next_segm = do_later[0]
                do_later = do_later[1:]
            if len(next_fts) > 1:
                next_fts[:,3] = str(act_id)
                '''store first segment and delete from data_arr'''
                finished_segm = np.concatenate((finished_segm,next_fts))
                data_arr = np.delete(data_arr,np.where(np.isin(data_arr[:,2],next_fts[:,2])),0)
                ''' upstream segment'''
                do_later = np.concatenate((next_fts[1:],do_later))
                next_segm = next_fts[0]
            if next_segm[0] == 'X':
                break
            '''changing actual segment'''
            act_segm = next_segm
            act_id = act_segm[2]


        '''unconnected features'''
        data_arr[:,3] = 'unconnected'
        finished_segm = np.concatenate((finished_segm,data_arr))


        '''sort finished segments for output'''
        fin_order = [int(f) for f in finished_segm[:,2]]
        finished_segm = finished_segm[np.array(fin_order).argsort()]
        finished_segm = np.c_[finished_segm, finished_segm[:,2]]
        finished_segm[np.where(finished_segm[:,3] == 'unconnected'),4] = 'unconnected'


        '''feedback for circles'''
        if len (circ_list)>0:
            feedback.reportError("Warning: Circle closed at NET_ID = ")
            for c in circ_list:
                feedback.reportError(self.tr('{0}, ').format(str(c)))

        '''sink definition'''
        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            out_fields,
            rawLayer.wkbType(),
            rawLayer.sourceCrs())


        '''add features to sink'''
        features = rawLayer.getFeatures()
        for (i,feature) in enumerate(features):
            if feedback.isCanceled():
                break # Stop the algorithm if cancel button has been clicked
            outFt = QgsFeature() # Add a feature
            outFt.setGeometry(feature.geometry())
            outFt.setAttributes(feature.attributes()+finished_segm[i,2:].tolist())
            sink.addFeature(outFt, QgsFeatureSink.FastInsert)

        
        del i
        del outFt
        del features
        del checkForCircles
        del nextftsConstr        
        return {self.OUTPUT: dest_id}


    def tr(self, string):
        return QCoreApplication.translate('Processing', string)


    def createInstance(self):
        return WaterNetwConstructor()

    def name(self):
        return '1 Water Network Constructor'

    def displayName(self):
        return self.tr(self.name())

    def group(self):
        return self.tr()

    def groupId(self):
        return ''

    def shortHelpString(self):
        return self.tr("""This tool creates a water network. 
        Workflow: 
        1. chose your layer in the drop-down list 
        2. select the undermost line segment/outlet in that layer (by clicking on it) 
        3. choose a directory to save the resulting layer (the other tools in this plugin won´t work with temporary layers)
        4. click on \"Run\"
        Please note: Connections will only be created at the beginning and at the end of line segments. Intersecting lines will not be connected
        The script will create three new columns in the attribute table: 
        \"NET_ID\" -- an individual identification number for every line segment, 
        \"NET_TO\" -- the NET_ID-number of the next segment (and node)
        \"NET_FROM\" -- the identification number of the previous node (which is the same as NET_ID)
        """)
