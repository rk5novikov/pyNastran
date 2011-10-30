import os
import sys
import copy
from math import ceil
from pyNastran.general.general import ListPrint

# 3rd party
import numpy
from numpy import any,cross

# my code
from fieldWriter import printCard
from cards import * # reads all the card types - GRID, CQUAD4, FORCE, PSHELL, etc.
#from mathFunctions import *

from BDF_Card import BDF_Card
from bdf_helper import getMethods,addMethods,writeMesh,cardMethods,XrefMesh
from caseControlDeck import CaseControlDeck

class BDF(getMethods,addMethods,writeMesh,cardMethods,XrefMesh):
    modelType = 'nastran'
    isStructured = False
    
    #def setCardsToInclude():
    #    pass

    def __init__(self,infilename,includeDir=None,log=None,debug=True):
        ## allows the BDF variables to be scoped properly (i think...)
        getMethods.__init__(self)
        addMethods.__init__(self)
        writeMesh.__init__(self)
        cardMethods.__init__(self)
        XrefMesh.__init__(self)

        self.debug = debug
        self._setInfile(infilename,includeDir,log)

        #self.n = 0
        #self.nCards = 0
        self._initStructuralDefaults()
        self._initThermalDefaults()

        self.rejects = []
        self.rejectCards = []
        self.executiveControlLines = []
        self.caseControlLines = []

        self.cardsToRead = set([
        'PARAM','=','INCLUDE',
        'GRID','GRDSET',
        
        'CONM2',
        'CELAS1','CELAS2',
        'CBAR','CROD','CTUBE','CBEAM',
        'CTRIA3','CQUAD4',
        'CHEXA','CPENTA','CTETRA',
        'RBAR','RBAR1','RBE1','RBE2','RBE3',
        
        'PELAS',
        'PROD','PBAR','PBEAM',#'PBEAM3','PBEAML'
        'PSHELL','PCOMP', # 'PCOMPG',
        'PSOLID','PLSOLID',
        'MAT1','MAT2','MAT3','MAT4','MAT5','MAT8','MAT9','MAT10',
         #'MATT1','MATT2','MATT3','MATT4','MATT5','MATT8','MATT9',
         #'MATS1',

        'SPC','SPC1','SPCD','SPCADD','SUPORT1',
        'MPC','MPCADD',

        'LOAD',
        'FORCE',#'FORCE1','FORCE2',
        'PLOAD','PLOAD2','PLOAD4',#'PLOAD1',
        'MOMENT',#'MOMENT1','MOMENT2',

        'FLFACT','AERO','AEROS','GUST','FLUTTER',
        #'CAERO1','CAERO2','CAERO3','CAERO4','CAERO5',
        #'SPLINE1','SPLINE2','SPLINE3','SPLINE4','SPLINE5','SPLINE6','SPLINE7',
        #'NLPARM',

        'CORD1R','CORD1C','CORD1S',
        'CORD2R','CORD2C','CORD2S',
        'ENDDATA',
        
        'TEMP',#'TEMPD',
        'QBDY1','QBDY2','QBDY3','QHBDY',

        'CHBDYE','CHBDYG','CHBDYP',

        'PCONV','PCONVM','PHBDY',

        'RADBC','CONV',
        ])
        self.cardsToWrite = self.cardsToRead

    def _initStructuralDefaults(self):
        # main structural block
        self.params = {}
        self.nodes = {}
        self.gridSet = None
        self.elements = {}
        self.properties = {}
        self.materials = {}
        self.loads = {}
        self.coords = {0: CORD2R() }

        # constraints
        self.constraints = {} # suport1, anything else???
        self.spcObject = constraintObject()
        self.mpcObject = constraintObject()

        # aero cards
        self.aeros    = {}
        self.gusts    = {}  # can this be simplified ???
        self.flfacts  = {}  # can this be simplified ???
        self.flutters = {}

    def _initThermalDefaults(self):
        # BCs
        self.bcs   = {}  # e.g. RADBC
        
        # elements
        # see self.elements

        # properties
        self.thermalProperties    = {}
        self.phbdys               = {}
        self.convectionProperties = {}

    def _setInfile(self,infilename,includeDir=None,log=None):
        """
        sets up the basic file/lines/cardCounting operations
        """
        if log is None:
            from pyNastran.general.logger import dummyLogger
            loggerObj = dummyLogger()
            log = loggerObj.startLog('debug') # or info
        self.log = log

        self.autoReject   = False # automatically rejects every parsable card
        self.doneReading  = False
        self.foundEndData = False

        if includeDir is None:
            includeDir = os.path.dirname(infilename)
        self.infilename = infilename
        self.includeDir = includeDir
        self.infilesPack     = []
        self.linesPack       = []
        self.activeFileNames = []
        self.lineNumbers     = []
        self.isOpened = {self.infilename: False}
        self.cardCount = {}

    def openFile(self,infileName):
        """
        Takes a filename and opens the file.  
        This method is used in order to support INCLUDE files.
        """
        #print self.isOpened
        if self.isOpened[infileName]==False:
            self.activeFileNames.append(infileName)
            #self.log().info("*FEM_Mesh bdf=|%s|  pwd=|%s|" %(infileName,os.getcwd()))
            infile = open(infileName,'r')
            self.infilesPack.append(infile)
            self.lineNumbers.append(0)
            self.isOpened[infileName]=True
            self.linesPack.append([])
        ###
        else:
            print "is already open...skipping"
        ###

    def getFileStats(self):
        filename   = self.activeFileNames[-1]
        return (filename,self.getLineNumber())

    def getLineNumber(self):
        lineNumber = self.lineNumbers[-1]
        return lineNumber

    def getNextLine(self):
        self.lineNumbers[-1]+=1
        return self.infilesPack[-1].readline()

        infile = self.infilesPack[-1]
        #print "infile = |%s|" %(infile),type(infile)
        line = infile.readline()
        print "line = |%r|" %(line)
        return line

    def closeFile(self):
        """
        Closes the active file object.
        If no files are open, the function is skipped.
        This method is used in order to support INCLUDE files.
        """
        if len(self.infilesPack)==0:
            return
        print "*closing"
        infile = self.infilesPack.pop()
        infile.close()

        lineNumbers = self.lineNumbers.pop()
        activeFileName = self.activeFileNames.pop()
        linesPack = self.linesPack.pop()
        self.isOpened[activeFileName] = False
        nlines = len(self.linesPack[-1])
        self.doneReading = False
        print "activeFileName=|%s| infilename=%s len(pack)=%s\n" %(os.path.relpath(activeFileName),os.path.relpath(self.infilename),nlines)
        #print "\n\n"

    def read(self,debug=False,xref=True):
        self.log().info('---starting FEM_Mesh.read of %s---' %(os.path.relpath(self.infilename)))
        sys.stdout.flush()
        self.debug = debug
        if self.debug:
            self.log().info("*FEM_Mesh.read")
        self.readExecutiveControlDeck()
        self.readCaseControlDeck()
        self.readBulkDataDeck()
        #self.closeFile()
        self.crossReference(xref=xref)
        if self.debug:
            self.log().debug("***FEM_Mesh.read")
        self.log().info('---finished FEM_Mesh.read of %s---' %(os.path.relpath(self.infilename)))
        sys.stdout.flush()

        isDone = self.foundEndData
        return ('BulkDataDeck',isDone)

    def isExecutiveControlDeck(self,line):
        return True

    def readExecutiveControlDeck(self):
        self.openFile(self.infilename)
        line = ''
        #self.executiveControlLines = []
        while 'CEND' not in line:
            lineIn = self.getNextLine()
            line = lineIn.strip()
            if self.debug:
                (n) = self.getLineNumber()
                print "line[%s]*= |%r|" %(n,line.upper())
            self.executiveControlLines.append(lineIn)
        return self.executiveControlLines
    def isCaseControlDeck(self,line):
            return True

    def readCaseControlDeck(self):
        self.openFile(self.infilename)
        #self.log().info("reading Case Control Deck...")
        line = ''
        #self.caseControlControlLines = []

        i = 0
        while 'BEGIN BULK' not in line:
            lineIn = self.getNextLine()
            line = lineIn.strip().split('$')[0].strip()
            #print "*line = |%s|" %(line)
            self.caseControlLines.append(lineIn)
            if i>200:
                raise RuntimeError('there are too many lines in the Case Control Deck < 200')
            i+=1
        #self.log().info("finished with Case Control Deck..")
        #print "self.caseControlLines = ",self.caseControlLines
        
        #for line in self.caseControlLines:
        #    print "** line=|%r|" %(line)

        self.caseControlDeck = CaseControlDeck(self.caseControlLines,self.log)
        #print "done w/ case control..."
        return self.caseControlLines

    def Is(self,card,cardCheck):
        #print "card=%s" %(card)
        #return cardCheck in card[0][0:8]
        return any([cardCheck in field[0:8].lstrip().rstrip(' *') for field in card])

    def isPrintable(self,cardName):
        """can the card be printed"""
        #cardName = self.getCardName(card)
        
        if cardName in self.cardsToWrite:
            #print "*card = ",card
            #print "WcardName = |%s|" %(cardName)
            return False
        return True

    def getCardName(self,cardLines):
        """
        Given a list of card lines, determines the cardName.
        @param self the object pointer
        @retval cardName the name of the card
        @note
            Parses the first 8 characters of a card, splits bassed on a comma,
            pulls off any spaces or asterisks and returns what is left.
        """
        #self.log().debug("getting cardName...")
        cardName = cardLines[0][0:8].strip()
        if ',' in cardName:
            cardName = cardName.split(',')[0].strip()

        cardName = cardName.lstrip().rstrip(' *')
        #self.log().debug("getCardName cardName=|%s|" %(cardName))
        return cardName
    
    def isReject(self,cardName):
        """can the card be read"""
        #cardName = self.getCardName(card)
        if cardName.startswith('='):
            return False
        elif cardName in self.cardsToRead:
            #print "*card = ",card
            #print "RcardName = |%s|" %(cardName)
            return False
        if cardName.strip():
            print "RcardName = |%s|" %(cardName)
        return True

    def getIncludeFileName(self,cardLines,cardName):
        """parses an INCLUDE file split into multiple lines (as a list)"""
        cardLines2 = []
        for line in cardLines:
            line = line.strip('\t\r\n ')
            cardLines2.append(line)

        #print "cardLinesRaw = ",cardLines2
        cardLines2[0] = cardLines2[0][7:].strip() # truncate the cardname
        filename = ''.join(cardLines2)
        filename = filename.strip('"').strip("'")
        #print 'filename = |%s|' %(filename)
        filename = os.path.join(self.includeDir,filename)
        return filename

    def addIncludeFile(self,infileName):
        """
        This method must be called before opening an INCLUDE file.
        """
        self.isOpened[infileName] = False

    def readBulkDataDeck(self):
        debug = self.debug
        #debug = False
        
        if self.debug:
            self.log().debug("*readBulkDataDeck")
        self.openFile(self.infilename)
        #self.nodes = {}
        #self.elements = {}
        #self.rejects = []
        
        #oldCardObj = BDF_Card()
        while len(self.activeFileNames)>0: # keep going until finished
            (card,cardName) = self.getCard(debug=False) # gets the cardLines
            #print "outcard = ",card
            #if cardName=='CQUAD4':
            #    print "card = ",card
            
            if cardName=='INCLUDE':
                filename = self.getIncludeFileName(card,cardName)
                self.addIncludeFile(filename)
                self.openFile(filename)
                reject = '$ INCLUDE processed:  %s\n' %(filename)
                self.rejects.append([reject])
                continue

            if not self.isReject(cardName):
                #print ""
                #print "not a reject"
                card = self.processCard(card) # parse the card into fields
                #print "processedCard = ",card
            elif card[0].strip()=='':
                #print "funny strip thing..."
                pass
            else:
                #print "reject!"
                self.rejects.append(card)
                continue
                #print " rejecting card = ",card
                #card = self.processCard(card)
                #sys.exit()
            

            #print "card2 = ",ListPrint(card)
            #print "card = ",card
            cardName = self.getCardName(card)
            
            if 'ENDDATA' in cardName:
                print cardName
                break # exits while loop
            #self.log().debug('cardName = |%s|' %(cardName))
            
            #cardObj = BDF_Card(card,oldCardObj)
            cardObj = BDF_Card(card)

            nCards = 1
            #special = False
            if '=' in cardName:
                nCards = cardName.strip('=()')
                if nCards:
                    nCards = int(nCards)
                else:
                    nCards = 1
                    #special = True
                #print "nCards = ",nCards
                cardName = oldCardObj.field(0)
            ###

            for iCard in range(nCards):
                #print "----------------------------"
                #if special:
                #    print "iCard = ",iCard
                self.addCard(card,cardName,iCard=0,oldCardObj=None)
                #if self.foundEndData:
                #    break
            ### iCard
            if self.doneReading or len(self.linesPack[-1])==0:
                #print "doneReading=%s len(pack)=%s" %(self.doneReading,len(self.linesPack[-1]))
                self.closeFile()
            ###
            #oldCardObj = copy.deepcopy(cardObj) # used for =(*1) stuff
            #print ""
            
            #print "self.linesPack[-1] = ",len(self.linesPack[-1])
            #print "self.activeFileNames = ",self.activeFileNames
        ### end of while loop

        #self.debug = True
        if self.debug:
            #for nid,node in self.nodes.items():
            #    print node
            #for eid,element in self.elements.items():
            #    print element
            
            self.log().debug("\n$REJECTS")
            #for reject in self.rejects:
                #print printCard(reject)
                #print ''.join(reject)
            self.log().debug("***readBulkDataDeck")
        ###

    def addCard(self,card,cardName,iCard=0,oldCardObj=None):
        #if cardName != 'CQUAD4':
        #    print cardName
        cardObj = BDF_Card(card,oldCardObj=None)
        if self.debug:
            print "*oldCardObj = \n",oldCardObj
            print "*cardObj = \n",cardObj
        #cardObj.applyOldFields(iCard)

        try:
            if self.autoReject==True:
                print 'rejecting processed %s' %(card)
                self.rejectCards.append(card)
            elif card==[] or cardName=='':
                pass
            elif cardName=='PARAM':
                param = PARAM(cardObj)
                self.addParam(param)
            elif cardName=='GRDSET':
                self.gridSet = GRDSET(cardObj)
            elif cardName=='GRID':
                node = GRID(cardObj)
                self.addNode(node)
            #elif cardName=='SPOINT':
            #    node = SPOINT(cardObj)
            #    self.addNode(node)

            elif cardName=='CQUAD4':
                elem = CQUAD4(cardObj)
                self.addElement(elem)
            elif cardName=='CQUAD8':
                elem = CQUAD8(cardObj)
                self.addElement(elem)

            elif cardName=='CTRIA3':
                elem = CTRIA3(cardObj)
                self.addElement(elem)
            elif cardName=='CTRIA6':
                elem = CTRIA6(cardObj)
                self.addElement(elem)

            elif cardName=='CTETRA':
                nFields = cardObj.nFields()
                if   nFields==7:    elem = CTETRA4(cardObj) # 4+3
                else:               elem = CTETRA10(cardObj)# 10+3
                #elif nFields==13:   elem = CTETRA10(cardObj)# 10+3
                #else: raise Exception('invalid number of CTETRA nodes=%s card=%s' %(nFields-3,str(cardObj)))
                self.addElement(elem)
            elif cardName=='CHEXA':
                nFields = cardObj.nFields()
                if   nFields==11: elem = CHEXA8(cardObj)  # 8+3
                else:             elem = CHEXA20(cardObj) # 20+3
                #elif nFields==23: elem = CHEXA20(cardObj) # 20+3
                #else: raise Exception('invalid number of CPENTA nodes=%s card=%s' %(nFields-3,str(cardObj)))
                self.addElement(elem)
            elif cardName=='CPENTA': # 6/15
                nFields = cardObj.nFields()
                if   nFields==9:  elem = CPENTA6(cardObj)  # 6+3
                else:             elem = CPENTA15(cardObj) # 15+3
                #elif nFields==18: elem = CPENTA15(cardObj) # 15+3
                #else: raise Exception('invalid number of CPENTA nodes=%s card=%s' %(nFields-3,str(cardObj)))
                self.addElement(elem)

            elif cardName=='CBAR':
                elem = CBAR(cardObj)
                self.addElement(elem)
            elif cardName=='CBEAM':
                elem = CBEAM(cardObj)
                self.addElement(elem)
            elif cardName=='CROD':
                elem = CROD(cardObj)
                print "crod...."
                self.addElement(elem)
            elif cardName=='CONROD':
                elem = CONROD(cardObj)
                self.addElement(elem)
                #print str(elem).strip()
            elif cardName=='CTUBE':
                elem = CBAR(cardObj)
                self.addElement(elem)

            elif cardName=='CELAS1':
                elem = CELAS1(cardObj)
                self.addElement(elem)
            elif cardName=='CELAS2':
                (elem) = CELAS2(cardObj)  # removed prop from outputs...
                self.addElement(elem)
                #self.addProperty(prop)
            elif cardName=='CONM2': # not done...
                elem = CONM2(cardObj)
                self.addElement(elem)


            elif cardName=='RBAR':
                (elem) = RBAR(cardObj)
                self.addElement(elem)
            elif cardName=='RBAR1':
                (elem) = RBAR1(cardObj)
                self.addElement(elem)

            elif cardName=='RBE1':
                (elem) = RBE1(cardObj)
                self.addElement(elem)
            elif cardName=='RBE2':
                (elem) = RBE2(cardObj)
                self.addElement(elem)
            elif cardName=='RBE3':
                (elem) = RBE3(cardObj)
                self.addElement(elem)

            elif cardName=='PELAS':
                prop = PELAS(cardObj)
                if cardObj.field(5):
                    prop = PELAS(cardObj,1) # makes 2nd PELAS card
                self.addProperty(prop)

            elif cardName=='PBAR':
                prop = PBAR(cardObj)
                self.addProperty(prop)
            #elif cardName=='PBARL':
            #    prop = PBARL(cardObj)
            #    self.addProperty(prop)
            elif cardName=='PBEAM':
                prop = PBEAM(cardObj)
                self.addProperty(prop)
            #elif cardName=='PBEAM3':
            #    prop = PBEAM3(cardObj)
            #    self.addProperty(prop)
            #elif cardName=='PBEAML':
            #    prop = PBEAML(cardObj)
            #    self.addProperty(prop)
            elif cardName=='PROD':
                prop = PROD(cardObj)
                self.addProperty(prop)
            elif cardName=='PTUBE':
                prop = PTUBE(cardObj)
                self.addProperty(prop)

            elif cardName=='PSHELL':
                prop = PSHELL(cardObj)
                self.addProperty(prop)
            elif cardName=='PCOMP':
                prop = PCOMP(cardObj)
                self.addProperty(prop)
            #elif cardName=='PCOMPG':
            #    prop = PCOMPG(cardObj)
            #    self.addProperty(prop)

            elif cardName=='PSOLID':
                prop = PSOLID(cardObj)
                self.addProperty(prop)
            elif cardName=='PLSOLID':
                prop = PLSOLID(cardObj)
                self.addProperty(prop)

            elif cardName=='MAT1':
                material = MAT1(cardObj)
                self.addMaterial(material)
            elif cardName=='MAT2':
                material = MAT2(cardObj)
                self.addMaterial(material)
            elif cardName=='MAT3':
                material = MAT3(cardObj)
                self.addMaterial(material)
            elif cardName=='MAT4':
                material = MAT4(cardObj)
                self.addMaterial(material) # maybe addThermalMaterial
            elif cardName=='MAT5':
                material = MAT5(cardObj)
                self.addMaterial(material) # maybe addThermalMaterial
            elif cardName=='MAT8':  # note there is no MAT6 or MAT7
                material = MAT8(cardObj)
                self.addMaterial(material)
            elif cardName=='MAT9':
                material = MAT9(cardObj)
                self.addMaterial(material)
            elif cardName=='MAT10':
                material = MAT9(cardObj)
                self.addMaterial(material)

            #elif cardName=='MATS1':
            #    material = MATS1(cardObj)
            #    self.addStressMaterial(material)
            #elif cardName=='MATT1':
            #    material = MATT1(cardObj)
            #    self.addTempMaterial(material)
            #elif cardName=='MATT2':
            #    material = MATT2(cardObj)
            #    self.addTempMaterial(material)
            #elif cardName=='MATT3':
            #    material = MATT3(cardObj)
            #    self.addTempMaterial(material)
            #elif cardName=='MATT4':
            #    material = MATT4(cardObj)
            #    self.addTempMaterial(material)
            #elif cardName=='MATT5':
            #    material = MATT5(cardObj)
            #    self.addTempMaterial(material)
            #elif cardName=='MATT8':
            #    material = MATT8(cardObj)
            #    self.addTempMaterial(material)
            #elif cardName=='MATT9':
            #    material = MATT9(cardObj)
            #    self.addTempMaterial(material)

            elif cardName=='FORCE':
                force = FORCE(cardObj)
                self.addLoad(force)
            #elif cardName=='FORCE1':
            #    force = FORCE1(cardObj)
            #    self.addLoad(force)
            #elif cardName=='FORCE':
            #    force = FORCE1(cardObj)
            #    self.addLoad(force)
            elif cardName=='MOMENT':
                moment = MOMENT(cardObj)
                self.addLoad(moment)
            #elif cardName=='MOMENT1':
            #    moment = MOMENT1(cardObj)
            #    self.addLoad(force)
            #elif cardName=='MOMENT2':
            #    moment = MOMENT2(cardObj)
            #    self.addLoad(force)
            elif cardName=='LOAD':
                load = LOAD(cardObj)
                self.addLoad(load)

            elif cardName=='TEMP':
                load = TEMP(cardObj)
                self.addThermalLoad(load)
            #elif cardName=='TEMPD':
            #    load = TEMPD(cardObj)
            #    self.addThermalLoad(load)

            elif cardName=='QBDY1':
                load = QBDY1(cardObj)
                self.addThermalLoad(load)
            elif cardName=='QBDY2':
                load = QBDY2(cardObj)
                self.addThermalLoad(load)
            elif cardName=='QBDY3':
                load = QBDY3(cardObj)
                self.addThermalLoad(load)
            elif cardName=='QHBDY':
                load = QHBDY(cardObj)
                self.addThermalLoad(load)

            elif cardName=='CHBDYE':
                element = CHBDYE(cardObj)
                self.addThermalElement(element)
            elif cardName=='CHBDYG':
                element = CHBDYG(cardObj)
                self.addThermalElement(element)
            elif cardName=='CHBDYP':
                element = CHBDYP(cardObj)
                self.addThermalElement(element)

            elif cardName=='PCONV':
                prop = PCONV(cardObj)
                self.addConvectionProperty(prop)
            elif cardName=='PCONVM':
                prop = PCONVM(cardObj)
                self.addConvectionProperty(prop)
            elif cardName=='PHBDY':
                prop = PHBDY(cardObj)
                self.addPHBDY(prop)

            elif cardName=='CONV':
                bc = CONV(cardObj)
                self.addThermalBC(bc,bc.eid)
            elif cardName=='RADBC':
                bc = RADBC(cardObj)
                self.addThermalBC(bc,bc.nodamb)

            #elif cardName=='TABLEH1':
            #    load = TABLEH1(cardObj)
            #    self.addTable(load)

            elif cardName=='MPC':
                constraint = MPC(cardObj)
                self.addConstraint_MPC(constraint)
            elif cardName=='MPCADD':
                constraint = MPCADD(cardObj)
                assert not isinstance(constraint,SPCADD)
                self.addConstraint_MPCADD(constraint)

            elif cardName=='SPC':
                constraint = SPC(cardObj)
                self.addConstraint_SPC(constraint)
            elif cardName=='SPC1':
                constraint = SPC1(cardObj)
                self.addConstraint_SPC(constraint)
            elif cardName=='SPCD':
                constraint = SPC1(cardObj)
                self.addConstraint_SPC(constraint)
            elif cardName=='SPCADD':
                constraint = SPCADD(cardObj)
                self.addConstraint_SPCADD(constraint)
            elif cardName=='SUPORT1':
                constraint = SUPORT1(cardObj)
                self.addConstraint(constraint)
                #print "constraint = ",constraint

            #elif cardName=='CAERO1':
            #    aero = CAERO1(cardObj)
            #    self.addCAero(aero)
            elif cardName=='AERO':
                aero = AERO(cardObj)
                self.addAero(aero)
            elif cardName=='AEROS':
                aeros = AEROS(cardObj)
                self.addAero(aeros)
            elif cardName=='FLFACT':
                flfact = FLFACT(cardObj)
                self.addFLFACT(flfact)
            elif cardName=='GUST':
                gust = GUST(cardObj)
                self.addGust(gust)
            elif cardName=='FLUTTER':
                flutter = FLUTTER(cardObj)
                self.addFlutter(flutter)

            elif cardName=='CORD2R':
                coord = CORD2R(cardObj)
                self.addCoord(coord)
            #elif cardName=='CORD2C':
            #    coord = CORD2C(cardObj)
            #    self.addCoord(coord)
            #elif cardName=='CORD2S':
            #    coord = CORD2S(cardObj)
            #    self.addCoord(coord)
            #elif 'CORD' in cardName:
            #    raise Exception('unhandled coordinate system...cardName=%s' %(cardName))
            elif 'ENDDATA' in cardName:
                self.foundEndData = True
                #break
            else:
                print 'rejecting processed %s' %(card)
                self.rejectCards.append(card)
            ###
        except:
            print "failed! Unreduced Card=%s\n" %(ListPrint(card))
            print "filename = %s\n" %(self.infilename)
            raise
        ### try-except block


### FEM_Mesh

def runA():
    import sys
    #basepath = os.getcwd()
    #configpath = os.path.join(basepath,'inputs')
    #workpath   = os.path.join(basepath,'outputs')
    #os.chdir(workpath)
    

    #bdfModel   = os.path.join(configpath,'fem.bdf.txt')
    #bdfModel   = os.path.join(configpath,'aeroModel.bdf')
    #bdfModel   = os.path.join('aeroModel_mod.bdf')
    bdfModel   = os.path.join('aeroModel_2.bdf')
    #bdfModel   = os.path.join('hard.bdf')
    #bdfModel   = os.path.join(configpath,'aeroModel_Loads.bdf')
    #bdfModel   = os.path.join(configpath,'test_mesh.bdf')
    #bdfModel   = os.path.join(configpath,'test_tet10.bdf')
    assert os.path.exists(bdfModel),'|%s| doesnt exist' %(bdfModel)
    fem = BDF(bdfModel,log=None)
    fem.read()
    #fem.sumForces()
    #fem.sumMoments()
    
    #print "----------"
    #deck = fem.caseControlDeck #.subcases[1]
    #print "deck = \n",deck
    #print str()
    fem.write('fem.out.bdf')
    #fem.writeAsCTRIA3('fem.out.bdf')


if __name__=='__main__':
    runA()

