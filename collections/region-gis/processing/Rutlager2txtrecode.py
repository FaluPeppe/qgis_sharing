# -*- coding: utf-8 -*-

"""
***************************************************************************
    Rutlager2txtrecode.py
    ---------------------
    Date                 : December 2020
    Copyright            : (C) 2020 by Kristian Bergstrand
    Email                : kristian dot bergstrand at sweco dot se
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************

Skriptet är finansierat av Region Dalarna för att användas fritt av alla
som så önskar. Det står också alla fritt att förbättra skriptet för att på 
så sätt bidra till det gemensammas bästa. Uppdraget att skriva skriptet
gick till Sweco och Kristian Bergstrand enligt informationen ovan.

"""

__author__ = 'Kristian Bergstrand'
__date__ = 'December 2020'
__copyright__ = '(C) 2020, Kristian Bergstrand'

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterField,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterString,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterFileDestination)
from qgis import processing

class Rutlager2txtrecode(QgsProcessingAlgorithm):

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    INPUT = 'INPUT'
    RUTID = 'RUTID'
    COSTLEVEL = 'COSTLEVEL'
    RADER = 'RADER'
    PREFIXRUTID = 'PREFIXRUTID'
    RUTSTORLEK = 'RUTSTORLEK'
    DATABAS = 'DATABAS'
    OUTPUT = 'OUTPUT'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return Rutlager2txtrecode()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'skapatxtrecode'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Rutlager till recode-fil')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr('Supercross i regionerna')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'dalarnascripts'

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        return  "<b>Instruktioner</b><br>"\
                "Denna algoritm skapar en recode-fil i textformat (.txt) från ett rutlager (polygon). Nya geografiska områden kan skapas av rutorna i ett rutlager och dessa områden måste sparas i en egen kolumn.<br>"\
                "Således krävs två kolumner i ett polygonlager för att algoritmen ska kunna köras, en med <i>RutID</i> och en med de <i>områden</i> som ska bli recodes i Supercross. Några inställningar behöver göras för att textrecode-filen ska fungera att ladda in i Supercross på Mona.<br><br>"\
                "<b>Inställningar</b><br>"\
                "Följande inställningar måste göras för att algoritmen ska kunna köras:"\
                "<ul><li>Rutlager (polygon)</li><li>RutID-kolumn (i rutlagret)</li><li>Kolumn med områden som ska göras recode på (i rutlagret)</li><li>Rutstorlek</li><li>Typ av databas i Supercross</li><li>Första raderna i recode-filen (ska normalt sett inte ändras)</li><li>Prefix för RutID som används i recode-filen (normalt sett länskoden)</li><li>Utdatafil (välj var den skapade recodefilen ska heta och i vilken mapp den ska sparas)</li></ul><br>"\
                "<b>Output</b><br>"\
                "Utdata från algoritmen är en fil med en textrecode som kan laddas upp på Mona genom att välja sidan <i>My Files</i> från Monas inloggningsmeny och därefter <i>Upload</i>. När filen har laddats upp kan den hämtas i mappen <i>InBox</i> i <i>Documents</i> på den egna Mona-lagringsytan. Filen kan kopieras därifrån till valfri mapp och därifrån laddas in i Supercross som en textrecode via knappen <i>Load</i> som finns i <i>Fields</i>-dialogrutan."\

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """
                
        self.isoconfig = { 
            "squaresizes" : ['1000','500','100'], 
            "mapDatabases" : {
                "Syss belägenhet" : { 
                    "NamnRad7_0" : "Rutid ",
                    "NamnRad7_1" : " m SWEREF99",
                    "FACTTABLE" : "Personer",
                    "VALUESET_0" : "kSaRutid",
                    "VALUESET_1" : "_SWEREF99"
                },
                "Bef belägenhet" : { 
                    "NamnRad7_0" : "Rutid ",
                    "NamnRad7_1" : " m SWEREF99",
                    "FACTTABLE" : "fBBefolkning",
                    "VALUESET_0" : "kBRutid",
                    "VALUESET_1" : "_SWEREF99"
                },
                "Flytt belägenhet" : { 
                    "NamnRad7_0" : "Rutid ",
                    "NamnRad7_1" : " m SWEREF99",
                    "FACTTABLE" : "fFlyttning",
                    "VALUESET_0" : "kFRutid",
                    "VALUESET_1" : "_SWEREF99"
                },
                "Syss relationsbelägenhet" : { 
                    "NamnRad7_0" : "RelationsRutid ",
                    "NamnRad7_1" : " m SWEREF99",
                    "FACTTABLE" : "Personer",
                    "VALUESET_0" : "kSaRutid",
                    "VALUESET_1" : "_SWEREF99"
                },
                "Flytt relationsbelägenhet" : { 
                    "NamnRad7_0" : "Rutid ",
                    "NamnRad7_1" : " m SWEREF99 flyttningsrelation",
                    "FACTTABLE" : "fFlyttning",
                    "VALUESET_0" : "kFRutid",
                    "VALUESET_1" : "_SWEREF99"
                }
            }
        }
        
        # Input file
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('Rutlager att skapa recodes från'),
                [QgsProcessing.TypeVectorPolygon]
            )
        )

        # Rutid field
        self.addParameter(
            QgsProcessingParameterField(
                self.RUTID,
                self.tr('RutID-kolumn'),
                'Rutid_txt',
                self.INPUT
            )
        )
        
        # Cost_level field
        self.addParameter(
            QgsProcessingParameterField(
                self.COSTLEVEL,
                self.tr('Kolumn som innehåller kategorier för recode'),
                'cost_level',
                self.INPUT
            )
        )
        
        # Rutstorlek options
        #name,description,options,allowMultiple,defaultValue
        self.addParameter(
            QgsProcessingParameterEnum(
                self.RUTSTORLEK,
                self.tr('Rutstorlek'),
                self.isoconfig["squaresizes"],
                False,
                0
            )
        )
        
        # Database options
        self.addParameter(
            QgsProcessingParameterEnum(
                self.DATABAS,
                self.tr('Typ av databas i Supercross'),
                [k for k in self.isoconfig["mapDatabases"]],
                False,
                0
            )
        )
        
        # Add rad 1-6 input
        self.addParameter(
            QgsProcessingParameterString(
                self.RADER,
                self.tr('Första raderna i recode-filen (ska normalt inte behöva ändras)'),
                'HEADER\n	VERSION 2\n	UNICODE\n	ESCAPE_CHAR & ITEM_BY_CODE\nEND HEADER\n',
                True
            )
        )
        
        # Optional prefix for rutid.
        self.addParameter(
            QgsProcessingParameterString(
                self.PREFIXRUTID,
                self.tr('Prefix för RutID som används i recodefilen (vanligtvis är det länskoden)'),
                20,
                False,
                False
            )
        )
        
        # Output file destination
        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT,
                self.tr('Utdatafil'), 
                'Text file(*.txt)',
                'C:\\Lokalt\\GIS\\Outputfil.txt' 
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        
        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.
        source = self.parameterAsSource(
            parameters,
            self.INPUT,
            context
        )

        # If source was not found, throw an exception to indicate that the algorithm
        # encountered a fatal error. The exception text can be any string, but in this
        # case we use the pre-built invalidSourceError method to return a standard
        # helper text for when a source cannot be evaluated
        if source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))

        # SquareId field
        sq_id_name = self.parameterAsFields(parameters, self.RUTID, context)
        
        # Cost_level field
        costlevelname = self.parameterAsFields(parameters, self.COSTLEVEL, context)

        # Header rows
        headerrows = self.parameterAsString(parameters, self.RADER, context)
        prefix_rutid = self.parameterAsString(parameters, self.PREFIXRUTID, context)
        
        # Square sizes
        sq_size_Index = self.parameterAsEnum(parameters, self.RUTSTORLEK, context)
        sq_size = self.isoconfig["squaresizes"][sq_size_Index]
        
        # Mapping depending on database used
        dbIndex = self.parameterAsEnum(parameters, self.DATABAS, context)
        keysDatabaser = [k for k in self.isoconfig["mapDatabases"]]
        used_databas = keysDatabaser[dbIndex]
        databas_config = self.isoconfig["mapDatabases"][used_databas]
        row7_0 = databas_config["NamnRad7_0"]
        row7_1 = databas_config["NamnRad7_1"]
        ftable = databas_config["FACTTABLE"]
        vset_0 = databas_config["VALUESET_0"]
        vset_1 = databas_config["VALUESET_1"]
        
        # Output file
        textfile = self.parameterAsFileOutput(parameters, self.OUTPUT, context)
        
        # Compute the number of steps to display within the progress bar and
        # get features from source
        total = 100.0 / source.featureCount() if source.featureCount() else 0
        features = source.getFeatures()
        output_content = []
        output_content.append(headerrows)
       
        headerrow_7 = 'RECODE "{0}" FROM "{1}{2}{3}" FACTTABLE "{4}"\n'.format(costlevelname[0], row7_0, sq_size, row7_1, ftable)
        output_content.append('\n')
        output_content.append(headerrow_7)
        main_content = ''
        headerrows_lastpart = []
        costlevel_cats = ''
        
        for current, feature in enumerate(features):
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():
                break
                
            f_costVal = feature[costlevelname[0]]
            f_costValCat = feature[costlevelname[0]]
            
            if(f_costVal):
                if (f_costValCat not in headerrows_lastpart):
                    headerrows_lastpart.append(f_costValCat)
                    
                sq_id = feature[sq_id_name[0]]
                if ( len(sq_id) <= 13 ):
                    sq_id = prefix_rutid + sq_id
                
                line_string = 'MAP CODE "{0}" VALUESET "{1}{2}{3}" TO "{4}"'.format(sq_id,vset_0,sq_size,vset_1,f_costVal)
                line_string += '\n'
                main_content += line_string
            
            # Update the progress bar
            feedback.setProgress(int(current * total))
        headerrows_lastpart.sort()
        for i,row in enumerate(headerrows_lastpart):
            thestring = 'RESULT "{0}"'.format(headerrows_lastpart[i])
            thestring += '\n'
            costlevel_cats += thestring
            
        output_content.append(costlevel_cats)
        output_content.append(main_content)
        output_content.append('END RECODE')
        
        with open(textfile, 'w') as output_file:
            output_file.writelines(output_content)
            
        return {self.OUTPUT: textfile}