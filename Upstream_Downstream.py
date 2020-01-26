# -*- coding: utf-8 -*-

"""
/***************************************************************************
 WaterNets
                                 A QGIS plugin
 This plugin calculates flowpaths
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2019-07-26
        copyright            : (C) 2020 by Jannik Schilling
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
__date__ = '2020-01-26'
__copyright__ = '(C) 2020 by Jannik Schilling'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import *
import processing
import numpy as np

class UpstreamDownstream(QgsProcessingAlgorithm):
    INPUT_LAYER = 'INPUT_LAYER'
    INPUT_Sect = 'INPUT_Sect'
    INPUT_FIELD_ID = 'INPUT_FIELD_ID'
    INPUT_FIELD_NEXT = 'INPUT_FIELD_NEXT'
    INPUT_FIELD_PREV = 'INPUT_FIELD_PREV'
    def name(self):
        return '2 Flow path upstream/downstream'

    def displayName(self):
        return self.tr(self.name())

    def group(self):
        return self.tr(self.groupId())

    def groupId(self):
        return ''

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return UpstreamDownstream()

    def shortHelpString(self):
        return self.tr(""" Workflow: 
        1. select one line segment.
        2. Choose between \"upstream\" or \"downstream"\. 
        3. In the drop-down lists chose the columns in the attribute table created by the tool \"1 Water Network Constructor\".
        4. Click on \"Run\"
         
        """)

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_LAYER,
                self.tr('Water Network Layer'),
                [QgsProcessing.TypeVectorLine]
            )
        )
        
        self.addParameter(
            QgsProcessingParameterEnum(
                self.INPUT_Sect, 
                self.tr("What do you want to display"), 
                ['Upstream','Downstream'],
            )
        )
        
        self.addParameter(
            QgsProcessingParameterField(
                self.INPUT_FIELD_ID,
                self.tr("ID Field/NET_ID"),
                parentLayerParameterName = self.INPUT_LAYER,
                type = QgsProcessingParameterField.Any,
            )
        )
        
        self.addParameter(
            QgsProcessingParameterField(
                self.INPUT_FIELD_PREV,
                self.tr("Prev Node Field/NET_FROM"),
                parentLayerParameterName = self.INPUT_LAYER,
                type = QgsProcessingParameterField.Any,
            )
        )
        
        self.addParameter(
            QgsProcessingParameterField(
                self.INPUT_FIELD_NEXT,
                self.tr("Next Node Field/NET_TO"),
                parentLayerParameterName = self.INPUT_LAYER,
                type = QgsProcessingParameterField.Any,
            )
        )


    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(
            parameters,
            self.INPUT_LAYER,
            context
        )
        if source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))

        
        '''loading the network'''
        feedback.setProgressText(self.tr("Loading network\n "))
        waternet = self.parameterAsVectorLayer(parameters, self.INPUT_LAYER, context)
        allFt = waternet.getFeatures()

        '''names of fields for id,next segment, previous segment'''
        id_field = self.parameterAsString(parameters, self.INPUT_FIELD_ID, context)
        next_field = self.parameterAsString(parameters, self.INPUT_FIELD_NEXT, context)
        prev_field = self.parameterAsString(parameters, self.INPUT_FIELD_PREV, context)
        
        '''field index for id,next segment, previous segment'''
        idxId = waternet.fields().indexFromName(id_field) 
        idxPrev = waternet.fields().indexFromName(prev_field)
        idxNext = waternet.fields().indexFromName(next_field)

        '''getting the selected segment'''
        if waternet.selectedFeatureCount() != 1:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))
        else: 
            startF = waternet.selectedFeatures()  # feature to start with
            startId = startF[0].id() # id of startF
            if startF[0].attributes()[idxId] != NULL:
                StartMarker =  startF[0].attributes()[idxId]
            if startF[0].attributes()[idxNext] == 'unconnected':
                feedback.reportError(self.tr('{0}: Unconnected segment selected. Please select another segment in layer "{1}" ').format(self.displayName(), parameters[self.INPUT_LAYER]))
                raise QgsProcessingException()
            #the error messages have to be revised
            
        '''selection: flow path upstream/downstream
        downstream: 1
        upstream: 0
        '''
        catchOrPathNum = self.parameterAsString(parameters, self.INPUT_Sect, context)
        if catchOrPathNum == "0":
            Section = 'U'
            Section_long = 'upstream'
        if catchOrPathNum == "1":
            Section = 'D'
            Section_long = 'downstream'
        total = 100.0 / source.featureCount() if source.featureCount() else 0 #the feedback-bar has to be set up properly!!!
        
        '''load data from layer "waternet" '''
        Data = []
        for (i,ft) in enumerate(allFt):
            if feedback.isCanceled():
                break
            column_ID = str(ft.attributes()[idxId])
            column_from = str(ft.attributes()[idxPrev])
            column_to = str(ft.attributes()[idxNext])
            qgis_ID = ft.id()
            Data = Data+[[column_ID,column_from,column_to,qgis_ID]]
            feedback.setProgress(total*i)
        DataArr = np.array(Data, dtype= 'object') # safe Data as numpy array
        feedback.setProgressText(self.tr("Data loaded\n Calculating {0}\n").format(str(Section_long)))

        '''this was planned as an option: should the first selected segment be part of the final selection?
        at the moment it´s permanently part of the final selection'''
        first_in_selection = True
        if first_in_selection==False:
            net_route=list()
        else:
            net_route = [startId]


        '''find flow path upstream or downstream'''
        MARKER=str(StartMarker) # NET_ID of first segment
        safe=["X"] #a list to safe segments when the net separates; "X" indicates an empty list and works as a MARKER for the while loop below
        forks = [] # a list for forks in flow path...because forks are interesting....
        origins = [] # a list for origins/river heads upstream

        def nextFtsSel (Sect, MARKER2):
            if Sect == 'U':
                clm_current = 1
                clm_search = 2
            if Sect == 'D':
                clm_current = 2
                clm_search = 1
            vtx_connect = DataArr[np.where(DataArr[:,0] == MARKER2)[0].tolist(),clm_current][0] # connecting vertex of actual segment
            rows_connect = np.where(DataArr[:,clm_search] == vtx_connect)[0].tolist() # find rows in DataArr with matching vertices to vtx_connect
            return(rows_connect)

        i=1
        while str(MARKER) != 'X':
            if feedback.isCanceled():
                break
            next_rows = nextFtsSel (Section, MARKER)
            if len (next_rows) > 0: # sometimes segments are saved in net_route...then they are deleted
                for Z in next_rows: 
                    if DataArr[Z,3] in net_route:
                        next_rows.remove(Z)
                net_route = net_route + DataArr[next_rows,3].tolist()
            if len(next_rows) > 1:
                if Section == 'D':
                    forks = forks + [MARKER]
                MARKER=DataArr[next_rows[0],0]# change MARKER to the NET_ID of one of the next segments
                safe=safe + DataArr[next_rows[1:],0].tolist()
            if len(next_rows) == 1:
                MARKER=DataArr[next_rows[0],0]
            if len(next_rows) == 0:
                if Section == 'U':
                    origins = origins + [MARKER]
                MARKER = safe[-1] #change MARKER to the last "saved" NET_ID
                safe=safe[:-1] #delete used NET_ID from "safe"-list
            feedback.setProgress(total*i)
            i+=1
        del i

        ''' the route is now separated into blocks of 200 segments to make the selection process faster'''
        sel=[]
        while len(net_route) != 0:
            if feedback.isCanceled():
                break
            set1=net_route[:200]
            sel=sel+[set1]
            net_route=net_route[200:]


        waternet.removeSelection() # current selection is removed before new selection
        if len(sel) != 0:
            total2 = 100/len(sel)
        else:
            total2 = 99
        i=1
        for selSet in sel:
            if feedback.isCanceled():
                break
            waternet.selectByIds(selSet, waternet.SelectBehavior(1))
            feedback.setProgress(total2*i)
            i +=1
        
        ''' "Cleaning" my storage....don´t know if necessary'''
        del i  
        del Data
        del DataArr
        del allFt
        del net_route
        del safe
        del forks
        del origins
        del nextFtsSel
        del MARKER 
        del StartMarker
        
        return {}
