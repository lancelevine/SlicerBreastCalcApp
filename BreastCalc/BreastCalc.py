import os
import unittest
import logging
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin

#
# BreastCalc
#

class BreastCalc(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "BreastCalc"  # TODO: make this more human readable by adding spaces
    self.parent.categories = ["Quantification"]  # TODO: set categories (folders where the module shows up in the module selector)
    self.parent.dependencies = []  # TODO: add here list of module names that this module requires
    self.parent.contributors = ["Lance Levine"]  # TODO: replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
This program calculates breast volume from MRI data. For more info, visit www.BreastCalc.com
"""  # TODO: update with short description of the module
    #self.parent.helpText += self.getDefaultModuleDocumentationLink()  # TODO: verify that the default URL is correct or change it to the actual documentation
    self.parent.acknowledgementText = """
This program was developed by Lance Levine with the help of Dr. Jikaria, Dr. Kassira, and Dr. Singh at the University of Miami Miller School of Medicine.
"""  # TODO: replace with organization, grant and thanks.

#
# BreastCalcWidget
#

class BreastCalcWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent=None):
    """
    Called when the user opens the module the first time and the widget is initialized.
    """
    ScriptedLoadableModuleWidget.__init__(self, parent)
    VTKObservationMixin.__init__(self)  # needed for parameter node observation
    self.logic = None

  def setup(self):
    """
    Called when the user opens the module the first time and the widget is initialized.
    """
    ScriptedLoadableModuleWidget.setup(self)

    # Load widget from .ui file (created by Qt Designer)
    uiWidget = slicer.util.loadUI(self.resourcePath('UI/BreastCalc.ui'))
    self.layout.addWidget(uiWidget)
    self.ui = slicer.util.childWidgetVariables(uiWidget)

    # Set scene in MRML widgets. Make sure that in Qt designer
    # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
    # "setMRMLScene(vtkMRMLScene*)" slot.
    uiWidget.setMRMLScene(slicer.mrmlScene)

    # Example of adding widgets dynamically (without Qt designer).
    # This approach is not recommended, but only shown as an illustrative example.
    self.invertedOutputSelector = slicer.qMRMLNodeComboBox()
    self.invertedOutputSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.invertedOutputSelector.addEnabled = True
    self.invertedOutputSelector.removeEnabled = True
    self.invertedOutputSelector.noneEnabled = True
    self.invertedOutputSelector.setMRMLScene(slicer.mrmlScene)
    self.invertedOutputSelector.setToolTip("Result with inverted threshold will be written into this volume")

    # Create a new parameterNode
    # This parameterNode stores all user choices in parameter values, node selections, etc.
    # so that when the scene is saved and reloaded, these settings are restored.
    self.logic = BreastCalcLogic()

    # Connections
    #self.ui.applyButton.connect('clicked(bool)', self.onApplyButton)
    self.ui.confirmButton.connect('clicked(bool)', self.onConfirmButton)
    self.ui.imageThresholdSliderWidget.connect('valueChanged(double)', self.onThresholdSlider)

    self.segmentationNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode")
    self.segmentationNode.CreateDefaultDisplayNodes() # only needed for display
    
    # Create temporary segment editor to get access to effects
    self.segmentEditorWidget = slicer.qMRMLSegmentEditorWidget()
    self.segmentEditorWidget.setMRMLScene(slicer.mrmlScene)
    self.segmentEditorNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentEditorNode")
    self.segmentEditorWidget.setMRMLSegmentEditorNode(self.segmentEditorNode)
    self.segmentEditorWidget.setSegmentationNode(self.segmentationNode)
    
    self.mode = 0
    
    #self.ui.img.setPixmap(qt.QPixmap("BreastCalc.png"))

  def cleanup(self):
    """
    Called when the application closes and the module widget is destroyed.
    """
    self.removeObservers()
    #if self.observerTag is not None:
    #    self.segmentationNode.RemoveObserver(self.observerTag)
    """
    This method is called when the user makes any change in the GUI.
    The changes are saved into the parameter node (so that they are restored when the scene is saved and loaded).
    """

  def onThresholdSlider(self):
    #self.effect.setParameter("MinimumThreshold",str(self.ui.imageThresholdSliderWidget.value))
    #self.effect.self().preview()
    effect = self.segmentEditorWidget.activeEffect()
    effect.setParameter("MinimumThreshold",str(self.ui.imageThresholdSliderWidget.value))
    effect.self().preview()
    
  def onConfirmButton(self):
    logging.info('Processing started')
        
    if self.mode is 0:
        masterVolumeNode = self.ui.inputSelector.currentNode()

        logging.info('Processing started')
        self.segmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(masterVolumeNode)
        self.segmentEditorWidget.setMasterVolumeNode(masterVolumeNode)
        
        self.segmentationNode.GetSegmentation().RemoveAllSegments()


        self.addedSegmentID = self.segmentationNode.GetSegmentation().AddEmptySegment("Breast", "Breast", [1.0,0.0,0.0])
        self.segmentEditorNode.SetSelectedSegmentID(self.addedSegmentID)
        
        #self.observerTag = self.segmentEditorNode.AddObserver('ModifiedEvent', self.printStatus)
        #self.observerTag = self.segmentationNode.GetSegmentation().GetSegment(self.addedSegmentID).AddObserver('RepresentationModified', self.printStatus)
        self.observerTag = self.segmentationNode.AddObserver('MasterRepresentationModified', self.printStatus)
        #self.observerTag = self.segmentEditorNode.AddObserver('onSegmentationDisplayModified', self.printStatus)

            
        displayNode = masterVolumeNode.GetDisplayNode()
        displayNode.AutoThresholdOn()
        #displayNode.SetThreshold(0,100)
        logging.info(str(displayNode.GetUpperThreshold()))
        logging.info(str(displayNode.GetLowerThreshold()))

        # Fill by thresholding
        self.segmentEditorWidget.setActiveEffectByName("Threshold")
        effect = self.segmentEditorWidget.activeEffect()
        effect.setParameter("MinimumThreshold",str(self.ui.imageThresholdSliderWidget.value))
        effect.setParameter("MaximumThreshold",str("1000000"))
        effect.self().preview()
        self.ui.imageThresholdSliderWidget.maximum = displayNode.GetUpperThreshold()
        self.ui.imageThresholdSliderWidget.value = displayNode.GetUpperThreshold() / 4


        
        self.ui.imageThresholdSliderWidget.setEnabled("true")

        # Delete temporary segment editor
        #self.segmentEditorWidget = None
        #slicer.mrmlScene.RemoveNode(self.segmentEditorNode)
        
        layoutManager = slicer.app.layoutManager()
        layoutManager.setLayout(6) #red slice
        
        self.ui.basicCollapsibleButton.collapsed = False
        
        self.ui.resultLabel.text = "Move the slider until the breast is maximally highlighted and the background is minimally highlighted. Then press confirm."
        
        self.ui.confirmButton.text = "Confirm"
        
        self.mode = 1
    
    elif self.mode is 1:
        masterVolumeNode = self.ui.inputSelector.currentNode()
        
        self.ui.basicCollapsibleButton.collapsed = True

        effect = self.segmentEditorWidget.activeEffect()
        effect.self().onApply()
        self.segmentEditorWidget.setActiveEffectByName("Scissors")
        effect = self.segmentEditorWidget.activeEffect()
        effect.setParameter("Operation", "EraseOutside")
        self.ui.resultLabel.text = "Circle the outside of the breast while tracing the anterior border of pec major. Then press confirm."
        self.mode = 2
    elif self.mode is 2:
        logging.info("mode 1")
        center = self.segmentationNode.GetSegmentCenterRAS(self.addedSegmentID)
        layoutManager = slicer.app.layoutManager()
        #layoutManager.setLayout(8) #green slice        
        layoutManager.setLayout(7) #yellow slice
        layoutManager.sliceWidget('Yellow').sliceLogic().SetSliceOffset(center[0])
        self.ui.resultLabel.text = "Click and hold, circle the breast, and release. Then press confirm."
        self.mode = 3
    elif self.mode is 3:
        logging.info("mode 2")
        self.segmentEditorWidget.setActiveEffectByName("Margin")
        effect = self.segmentEditorWidget.activeEffect()
        #effect.setParameter("Operation", "Shrink")
        effect.setParameter("MarginSizeMm", "-3")
        effect = self.segmentEditorWidget.activeEffect()
        effect.self().onApply()
        
        try:
          implantVolumeCc = self.logic.computeImplantVolumeCc(self.ui.inputSelector.currentNode(), self.segmentationNode, self.addedSegmentID)
          self.ui.resultLabel.text = "Implant Volume: " + '{:.2f}'.format(implantVolumeCc)
        except Exception as e:
          slicer.util.errorDisplay("Failed to compute results: "+str(e))
          self.ui.resultLabel.text = ""
          import traceback
          traceback.print_exc()
          
        #self.segmentationNode.AddSegmentFromClosedSurfaceRepresentation(self.addedSegmentID, "Breast Tissue", [0.0,0.0,1.0])  
        #self.segmentationNode.GetSegmentation().GetSegment(self.addedSegmentID).CreateClosedSurfaceRepresentation()
        self.segmentationNode.CreateClosedSurfaceRepresentation()
        center = self.segmentationNode.GetSegmentCenterRAS(self.addedSegmentID)
        logging.info("center:" + str(center[0]) + "center:" + str(center[1]) + "center:" + str(center[2]))
        
        layoutManager = slicer.app.layoutManager()
        layoutManager.setLayout(2) #conventional
        
        self.mode = 0
        self.ui.confirmButton.text = "Run"

        
    logging.info('Processing completed')
    
  def printStatus(caller, event, t):
    logging.info("segmentation modified")  


#
# BreastCalcLogic
#

class BreastCalcLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def computeImplantVolumeCc(self, inputVolume, segmentationNode, implantSegmentId):
    """
    Run the processing algorithm.
    Can be used without GUI widget.
    :param inputVolume: volume to be thresholded
    :param outputVolume: thresholding result
    :param imageThreshold: values above/below this threshold will be set to 0
    :param invert: if True then values above the threshold will be set to 0, otherwise values below are set to 0
    :param showResult: show output volume in slice viewers
    """
    if not inputVolume:
      raise ValueError("Input volume is invalid")
      
    masterVolumeNode = inputVolume
      
        # Compute segment volumes
    import SegmentStatistics
    segStatLogic = SegmentStatistics.SegmentStatisticsLogic()
    segStatLogic.getParameterNode().SetParameter("Segmentation", segmentationNode.GetID())
    segStatLogic.getParameterNode().SetParameter("ScalarVolume", masterVolumeNode.GetID())
    segStatLogic.getParameterNode().SetParameter("LabelmapSegmentStatisticsPlugin.enabled","False")
    segStatLogic.getParameterNode().SetParameter("ScalarVolumeSegmentStatisticsPlugin.voxel_count.enabled","False")
    segStatLogic.getParameterNode().SetParameter("ScalarVolumeSegmentStatisticsPlugin.volume_mm3.enabled","False")
    segStatLogic.computeStatistics()
    # print(segStatLogic.getStatistics())  # prints all computed metrics
    implantVolumeCc = segStatLogic.getStatistics()[implantSegmentId,"ScalarVolumeSegmentStatisticsPlugin.volume_cm3"]
    logging.info("Processing result: " + str(implantVolumeCc))

    return implantVolumeCc
    

    """
    if not inputVolume:
      raise ValueError("Input volume is invalid")
      
    masterVolumeNode = inputVolume

    logging.info('Processing started')
    
    # Create segmentation
    segmentationNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode")
    segmentationNode.CreateDefaultDisplayNodes() # only needed for display
    segmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(masterVolumeNode)
    
    # Create temporary segment editor to get access to effects
    segmentEditorWidget = slicer.qMRMLSegmentEditorWidget()
    segmentEditorWidget.setMRMLScene(slicer.mrmlScene)
    segmentEditorNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentEditorNode")
    segmentEditorWidget.setMRMLSegmentEditorNode(segmentEditorNode)
    segmentEditorWidget.setSegmentationNode(segmentationNode)
    segmentEditorWidget.setMasterVolumeNode(masterVolumeNode)

# Create segments by thresholding
    segmentsFromHounsfieldUnits = [
        ["fat", 0, 20],
        ["muscle", 25, 80],
        ["bone", 130, 3000] ]   
    for segmentName, thresholdMin, thresholdMax in segmentsFromHounsfieldUnits:
        # Create segment
        addedSegmentID = segmentationNode.GetSegmentation().AddEmptySegment(segmentName)
        segmentEditorNode.SetSelectedSegmentID(addedSegmentID)
        # Fill by thresholding
        segmentEditorWidget.setActiveEffectByName("Threshold")
        effect = segmentEditorWidget.activeEffect()
        effect.setParameter("MinimumThreshold",str(thresholdMin))
        effect.setParameter("MaximumThreshold",str(thresholdMax))
        effect.self().onApply()

    # Delete temporary segment editor
    segmentEditorWidget = None
    slicer.mrmlScene.RemoveNode(segmentEditorNode)

    logging.info('Processing completed')
    """

#
# BreastCalcTest
#

class BreastCalcTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_BreastCalc1()

  def test_BreastCalc1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests should exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    self.delayDisplay("Starting the test")

    # Get/create input data

    import SampleData
    inputVolume = SampleData.downloadFromURL(
      nodeNames='MRHead',
      fileNames='MR-Head.nrrd',
      uris='https://github.com/Slicer/SlicerTestingData/releases/download/MD5/39b01631b7b38232a220007230624c8e',
      checksums='MD5:39b01631b7b38232a220007230624c8e')[0]
    self.delayDisplay('Finished with download and loading')

    inputScalarRange = inputVolume.GetImageData().GetScalarRange()
    self.assertEqual(inputScalarRange[0], 0)
    self.assertEqual(inputScalarRange[1], 279)

    threshold = 50

    # Test the module logic

    logic = BreastCalcLogic()

    # Test algorithm with non-inverted threshold
    logic.run(inputVolume, threshold, True)

    # Test algorithm with inverted threshold
    logic.run(inputVolume, threshold, False)


    self.delayDisplay('Test passed')
    
class CustomDialog(qt.QDialog):
    def __init__(self, parent = None):
        qt.QDialog.__init__(self, parent)
        self.connect('accepted()', self.myCustomSlot)
        self.r = slicer.ctkSliderWidget()
        #self.invertedOutputSelector.setMRMLScene(slicer.mrmlScene)
        self.layout.addWidget(self.r)
    def myCustomSlot(self):
        pass

