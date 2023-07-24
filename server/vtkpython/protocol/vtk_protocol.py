from vtk.web import protocols as vtk_protocols
from wslink import register as exportRpc

import vtk
from models.colormap import CUSTOM_COLORMAP
from models.presets import *

from models.cropping.operationMode import OperationMode
from models.cropping.freehand import Contour2Dpipeline, CroppingFreehandInteractorStyle

# -------------------------------------------------------------------------
# ViewManager
# -------------------------------------------------------------------------

class Dicom3D(vtk_protocols.vtkWebProtocol):
    def __init__(self):
        self.colors = vtk.vtkNamedColors()
        # Pipeline
        self.reader = vtk.vtkDICOMImageReader()
        self.mapper = vtk.vtkSmartVolumeMapper()
        self.volProperty = vtk.vtkVolumeProperty()
        self.volume = vtk.vtkVolume()
        self.color = vtk.vtkColorTransferFunction()
        self.scalarOpacity = vtk.vtkPiecewiseFunction()
        # Outline
        self.outline = vtk.vtkOutlineFilter()
        self.outlineMapper = vtk.vtkPolyDataMapper()
        self.outlineActor = vtk.vtkActor()
        # Checking
        self.checkLight = True
        self.checkBox = True
        # Cropping
        self.boxRep = vtk.vtkBoxRepresentation()
        self.widget = vtk.vtkBoxWidget2()
        self.planes = vtk.vtkPlanes()
        # Image data
        self.modifierLabelmap = vtk.vtkImageData()

    @exportRpc("vtk.initialize")
    def createVisualization(self):
        interactor = self.getApplication().GetObjectIdMap().GetActiveObject("INTERACTOR")
        renderWindow = self.getView('-1')
        renderer = renderWindow.GetRenderers().GetFirstRenderer()

        # Reader
        path = "C:/Users/DELL E5540/Desktop/Python/dicom-data/Ankle"
        self.reader.SetDirectoryName(path)
        self.reader.Update()

        originImageData = self.reader.GetOutput()
        self.modifierLabelmap.SetOrigin(originImageData.GetOrigin())
        self.modifierLabelmap.SetExtent(originImageData.GetExtent())
        self.modifierLabelmap.SetSpacing(originImageData.GetSpacing())
        self.modifierLabelmap.SetDirectionMatrix(originImageData.GetDirectionMatrix())
        self.modifierLabelmap.AllocateScalars(originImageData.GetScalarType(), 1)
        self.modifierLabelmap.GetPointData().GetScalars().Fill(0)

        # Outline
        self.outline.SetInputConnection(self.reader.GetOutputPort())
        self.outlineMapper.SetInputConnection(self.outline.GetOutputPort())
        self.outlineActor.SetMapper(self.outlineMapper)
        self.outlineActor.GetProperty().SetColor(0, 0, 0)

        # Mapper
        self.mapper.SetInputData(self.reader.GetOutput())
        # Volume property
        self.volProperty.ShadeOn()
        self.volProperty.SetAmbient(0.1)
        self.volProperty.SetDiffuse(0.9)
        self.volProperty.SetSpecular(0.2)
        self.color.RemoveAllPoints()
        rgbPoints = CUSTOM_COLORMAP.get("STANDARD_CT").get("rgbPoints")
        for point in rgbPoints:
          self.color.AddRGBPoint(point[0], point[1], point[2], point[3])
        self.volProperty.SetColor(self.color)

        # Muscle CT
        self.scalarOpacity.RemoveAllPoints()
        scalarOpacityRange = MUSCLE_CT.get("transferFunction").get("scalarOpacityRange")
        self.scalarOpacity.AddPoint(scalarOpacityRange[0], 0)
        self.scalarOpacity.AddPoint(scalarOpacityRange[1], 1)
        self.volProperty.SetScalarOpacity(self.scalarOpacity)

        # Volume
        self.volume.SetMapper(self.mapper)
        self.volume.SetProperty(self.volProperty)

        # Cropping
        self.boxRep.GetOutlineProperty().SetColor(0, 0, 0)
        self.boxRep.SetInsideOut(True)

        self.widget.SetRepresentation(self.boxRep)
        self.widget.SetInteractor(interactor)
        self.widget.GetRepresentation().SetPlaceFactor(1)
        self.widget.GetRepresentation().PlaceWidget(self.reader.GetOutput().GetBounds())
        self.widget.SetEnabled(True)

        ipwcallback = IPWCallback(self.planes, self.mapper)
        self.widget.AddObserver(vtk.vtkCommand.InteractionEvent, ipwcallback)
        self.widget.Off()

        # Render
        renderer.AddVolume(self.volume)
        renderer.AddActor(self.outlineActor)
        renderer.ResetCamera()

        # Render window
        renderWindow.Render()
        return self.resetCamera()

    @exportRpc("vtk.camera.reset")
    def resetCamera(self):
        renderWindow = self.getView('-1')

        originImageData = self.reader.GetOutput()
        self.mapper.SetInputData(originImageData)
        self.modifierLabelmap.GetPointData().GetScalars().Fill(0)

        renderWindow.GetRenderers().GetFirstRenderer().ResetCamera()
        renderWindow.Render()

        self.getApplication().InvalidateCache(renderWindow)
        self.getApplication().InvokeEvent('UpdateEvent')

        return -1
    
    @exportRpc("vtk.cone.resolution.update")
    def updateResolution(self, resolution):
        # self.cone.SetResolution(resolution)
        renderWindow = self.getView('-1')
        # renderWindow.Modified() # either modified or render
        renderWindow.Render()
        self.getApplication().InvokeEvent('UpdateEvent')

    @exportRpc("viewport.mouse.zoom.wheel")
    def updateZoomFromWheel(self, event):
      print("zoom")
      if 'Start' in event["type"]:
        self.getApplication().InvokeEvent('StartInteractionEvent')

      renderWindow = self.getView(event['view'])
      if renderWindow and 'spinY' in event:
        zoomFactor = 1.0 - event['spinY'] / 10.0

        camera = renderWindow.GetRenderers().GetFirstRenderer().GetActiveCamera()
        fp = camera.GetFocalPoint()
        pos = camera.GetPosition()
        delta = [fp[i] - pos[i] for i in range(3)]
        camera.Zoom(zoomFactor)

        pos2 = camera.GetPosition()
        camera.SetFocalPoint([pos2[i] + delta[i] for i in range(3)])
        renderWindow.Modified()

      if 'End' in event["type"]:
        self.getApplication().InvokeEvent('EndInteractionEvent')

    @exportRpc("vtk.dicom3d.light")
    def light(self):
      renderWindow = self.getView('-1')
      renderer = renderWindow.GetRenderers().GetFirstRenderer()

      if self.checkLight:
        renderer.SetBackground(self.colors.GetColor3d("Black"))
        self.outlineActor.GetProperty().SetColor(1, 1, 1)
        self.boxRep.GetOutlineProperty().SetColor(1, 1, 1)
        self.checkLight = False
      else:
        renderer.SetBackground(self.colors.GetColor3d("White"))
        self.outlineActor.GetProperty().SetColor(0, 0, 0)
        self.boxRep.GetOutlineProperty().SetColor(0, 0, 0)
        self.checkLight = True

      renderWindow.Render()
      self.getApplication().InvokeEvent('UpdateEvent')

    @exportRpc("vtk.dicom3d.crop")
    def crop3d(self):
      # self.getApplication() -> vtkWebApplication()
      renderWindow = self.getView('-1')

      if self.checkBox:
        self.widget.On()
        self.checkBox = False
      else:
        self.widget.Off()
        self.checkBox = True

      renderWindow.Render()
      self.getApplication().InvokeEvent('UpdateEvent') # Create event after send to object

    @exportRpc("vtk.dicom3d.crop.freehand")
    def cropfreehand3d(self):
      # print(self.getApplication())
      renderWindowInteractor = self.getApplication().GetObjectIdMap().GetActiveObject("INTERACTOR")
      renderWindow = self.getView('-1')
      renderer = renderWindow.GetRenderers().GetFirstRenderer()
    
      contour2Dpipeline = Contour2Dpipeline()
      renderer.AddActor(contour2Dpipeline.actor2D)
      renderer.AddActor(contour2Dpipeline.actor2DThin)
      renderer.AddActor(contour2Dpipeline.polyData3Dactor)
      
      originImageData = self.reader.GetOutput()

      style = CroppingFreehandInteractorStyle(
        contour2Dpipeline, 
        originImageData, 
        self.modifierLabelmap, 
        OperationMode.INSIDE,
        self.mapper
      )

      renderWindowInteractor.SetInteractorStyle(style)
      self.getApplication().InvokeEvent('UpdateEvent')

class IPWCallback():
  def __init__(self, planes, mapper) -> None:
    self.planes = planes
    self.mapper = mapper

  def __call__(self, obj: vtk.vtkBoxWidget2, event: str) -> None:
    obj.GetRepresentation().GetPlanes(self.planes)
    self.mapper.SetClippingPlanes(self.planes)