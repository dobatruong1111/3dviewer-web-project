from vtk.web import protocols as vtk_protocols
from wslink import register as exportRpc

import vtk
from model.colormap import CUSTOM_COLORMAP
from model.presets import *
from typing import List
import time

# -------------------------------------------------------------------------
# ViewManager
# -------------------------------------------------------------------------

class Dicom3D(vtk_protocols.vtkWebProtocol):
    def __init__(self):
        self.colors = vtk.vtkNamedColors()
        # pipeline
        self.reader = vtk.vtkDICOMImageReader()
        self.mapper = vtk.vtkSmartVolumeMapper()
        self.volProperty = vtk.vtkVolumeProperty()
        self.volume = vtk.vtkVolume()
        self.color = vtk.vtkColorTransferFunction()
        self.scalarOpacity = vtk.vtkPiecewiseFunction()
        # ---
        self.checkLight = True
        self.checkBox = True
        # Cropping
        self.boxRep = vtk.vtkBoxRepresentation()
        self.widget = vtk.vtkBoxWidget2()
        self.planes = vtk.vtkPlanes()
        # Cropping freehand
        self.checkBtCropFreehand = True

    @exportRpc("vtk.initialize")
    def createVisualization(self):
        interactor = self.getApplication().GetObjectIdMap().GetActiveObject("INTERACTOR")
        renderWindow = self.getView('-1')
        renderer = renderWindow.GetRenderers().GetFirstRenderer()

        # reader
        path = "C:/Users/DELL E5540/Desktop/Python/dicom-data/220277460 Nguyen Thanh Dat/Unknown Study/CT 1.25mm Stnd KHONG TIEM"
        self.reader.SetDirectoryName(path)
        self.reader.Update()

        # mapper
        self.mapper.SetInputData(self.reader.GetOutput())

        # volume property
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

        # volume
        self.volume.SetMapper(self.mapper)
        self.volume.SetProperty(self.volProperty)
        # center = self.volume.GetCenter()
        # self.volume.SetPosition(-center[0], -center[1], -center[2])

        # cropping
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

        # render
        renderer.AddVolume(self.volume)
        renderer.ResetCamera()

        # render window
        renderWindow.Render()
        return self.resetCamera()

    @exportRpc("vtk.camera.reset")
    def resetCamera(self):
        renderWindow = self.getView('-1')

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
      # print("zoom")
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
        self.boxRep.GetOutlineProperty().SetColor(1, 1, 1)
        self.checkLight = False
      else:
        renderer.SetBackground(self.colors.GetColor3d("White"))
        self.boxRep.GetOutlineProperty().SetColor(0, 0, 0)
        self.checkLight = True

      renderWindow.Render()
      self.getApplication().InvokeEvent('UpdateEvent')
        
    @exportRpc("vtk.dicom3d.presets.bone.ct")
    def showBoneCT(self):
      self.color.RemoveAllPoints()
      rgbPoints = BONE_CT.get("colorMap").get("rgbPoints")
      for point in rgbPoints:
         self.color.AddRGBPoint(point[0], point[1], point[2], point[3])

      self.scalarOpacity.RemoveAllPoints()
      scalarOpacityRange = BONE_CT.get("transferFunction").get("scalarOpacityRange")
      self.scalarOpacity.AddPoint(scalarOpacityRange[0], 0)
      self.scalarOpacity.AddPoint(scalarOpacityRange[1], 1)

      renderWindow = self.getView('-1')
      renderWindow.Render()
      self.getApplication().InvokeEvent('UpdateEvent')
      
    @exportRpc("vtk.dicom3d.presets.angio.ct")
    def showAngioCT(self):
      self.color.RemoveAllPoints()
      rgbPoints = ANGIO_CT.get("colorMap").get("rgbPoints")
      for point in rgbPoints:
        self.color.AddRGBPoint(point[0], point[1], point[2], point[3])

      self.scalarOpacity.RemoveAllPoints()
      scalarOpacityRange = ANGIO_CT.get("transferFunction").get("scalarOpacityRange")
      self.scalarOpacity.AddPoint(scalarOpacityRange[0], 0)
      self.scalarOpacity.AddPoint(scalarOpacityRange[1], 1)

      renderWindow = self.getView('-1')
      renderWindow.Render()
      self.getApplication().InvokeEvent('UpdateEvent')

    @exportRpc("vtk.dicom3d.presets.muscle.ct")
    def showMuscleCT(self):
      self.color.RemoveAllPoints()
      rgbPoints = MUSCLE_CT.get("colorMap").get("rgbPoints")
      for point in rgbPoints:
        self.color.AddRGBPoint(point[0], point[1], point[2], point[3])

      self.scalarOpacity.RemoveAllPoints()
      scalarOpacityRange = MUSCLE_CT.get("transferFunction").get("scalarOpacityRange")
      self.scalarOpacity.AddPoint(scalarOpacityRange[0], 0)
      self.scalarOpacity.AddPoint(scalarOpacityRange[1], 1)

      renderWindow = self.getView('-1')
      renderWindow.Render()
      self.getApplication().InvokeEvent('UpdateEvent')

    @exportRpc("vtk.dicom3d.presets.mip")
    def showMip(self):
      self.color.RemoveAllPoints()
      rgbPoints = MIP.get("colorMap").get("rgbPoints")
      if len(rgbPoints):
        for point in rgbPoints:
          self.color.AddRGBPoint(point[0], point[1], point[2], point[3])

      self.scalarOpacity.RemoveAllPoints()
      scalarOpacityRange = MIP.get("transferFunction").get("scalarOpacityRange")
      self.scalarOpacity.AddPoint(scalarOpacityRange[0], 0)
      self.scalarOpacity.AddPoint(scalarOpacityRange[1], 1)

      renderWindow = self.getView('-1')
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
      self.getApplication().InvokeEvent('UpdateEvent') # create event after send to object

    @exportRpc("vtk.dicom3d.cropfreehand")
    def cropFreehand3d(self):
      # print("crop freehand")
      interactor = self.getApplication().GetObjectIdMap().GetActiveObject("INTERACTOR")
      renderWindow = self.getView('-1')
      renderer = renderWindow.GetRenderers().GetFirstRenderer()
      if self.checkBtCropFreehand:
        pipeline = ScissorPipeline()
        renderer.AddActor(pipeline.actor)
        renderer.AddActor(pipeline.actorThin)
        style = CropFreehandInteractorStyle(pipeline)
        interactor.SetInteractorStyle(style)
        self.checkBtCropFreehand = False
      else:
        style = vtk.vtkInteractorStyleTrackballCamera()
        interactor.SetInteractorStyle(style)
        self.checkBtCropFreehand = True

class ScissorPipeline():
  def __init__(self) -> None:
    self.isDragging = False
    self.polyData = vtk.vtkPolyData()
    self.mapper = vtk.vtkPolyDataMapper2D()
    self.mapper.SetInputData(self.polyData)
    self.actor = vtk.vtkActor2D()
    self.actor.SetMapper(self.mapper)
    self.actor.GetProperty().SetColor(1, 1, 0)
    self.actor.GetProperty().SetLineWidth(2)
    self.actor.VisibilityOff()

    self.polyDataThin = vtk.vtkPolyData()
    self.mapperThin = vtk.vtkPolyDataMapper2D()
    self.mapperThin.SetInputData(self.polyDataThin)
    self.actorThin = vtk.vtkActor2D()
    self.actorThin.SetMapper(self.mapperThin)
    self.actorThin.VisibilityOff()
    outlinePropertyThin = self.actorThin.GetProperty()
    outlinePropertyThin.SetColor(0.7, 0.7, 0)
    outlinePropertyThin.SetLineStipplePattern(0xff00)
    outlinePropertyThin.SetLineWidth(1)

class CropFreehandInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
  def __init__(self, pipeline) -> None:
    super().__init__()
    self.pipeline = pipeline
    self.AddObserver("LeftButtonPressEvent", self.leftButtonDown)
    self.AddObserver("LeftButtonReleaseEvent", self.leftButtonUp)

  @staticmethod
  def createGlyph(pipeline: ScissorPipeline, eventPosition: List) -> None:
    if pipeline.isDragging:
      # numberOfPoints = 1
      points = vtk.vtkPoints()
      lines = vtk.vtkCellArray()
      pipeline.polyData.SetPoints(points)
      pipeline.polyData.SetLines(lines)

      points.InsertNextPoint(eventPosition[0], eventPosition[1], 0)

      pointsThin = vtk.vtkPoints()
      linesThin = vtk.vtkCellArray()
      pipeline.polyDataThin.SetPoints(pointsThin)
      pipeline.polyDataThin.SetLines(linesThin)

      pointsThin.InsertNextPoint(eventPosition[0], eventPosition[1], 0)
      pointsThin.InsertNextPoint(eventPosition[0], eventPosition[1], 0)

      idList = vtk.vtkIdList()
      idList.InsertNextId(0)
      idList.InsertNextId(1)
      pipeline.polyDataThin.InsertNextCell(vtk.VTK_LINE, idList)

      pipeline.actorThin.VisibilityOn()
      pipeline.actor.VisibilityOn()
    else:
      pipeline.actor.VisibilityOff()
      pipeline.actorThin.VisibilityOff()

  @staticmethod
  def updateGlyphWithNewPosition(pipeline: ScissorPipeline, eventPosition: List, finalize: bool) -> None:
    if pipeline.isDragging:
      points = pipeline.polyData.GetPoints() # vtkPoints()
      newPointIndex = points.InsertNextPoint(eventPosition[0], eventPosition[1], 0)
      idList = vtk.vtkIdList()
      if finalize:
        idList.InsertNextId(newPointIndex)
        idList.InsertNextId(0)
      else:
        idList.InsertNextId(newPointIndex - 1)
        idList.InsertNextId(newPointIndex)
      pipeline.polyData.InsertNextCell(vtk.VTK_LINE, idList)
      points.Modified()
      pipeline.polyDataThin.GetPoints().SetPoint(1, eventPosition[0], eventPosition[1], 0)
      pipeline.polyDataThin.GetPoints().Modified()
    else:
      pipeline.actor.VisibilityOff()
      pipeline.actorThin.VisibilityOff()

  def leftButtonDown(self, obj, event):
    self.pipeline.isDragging = True
    eventPosition = self.GetInteractor().GetEventPosition()
    self.createGlyph(self.pipeline, eventPosition)
    if not self.HasObserver("MouseMoveEvent"):
      self.AddObserver("MouseMoveEvent", self.mouseMoveEvent)
    self.OnLeftButtonDown()
  
  def mouseMoveEvent(self, obj, event):
    if self.pipeline.isDragging:
      eventPosition = self.GetInteractor().GetEventPosition()
      self.updateGlyphWithNewPosition(self.pipeline, eventPosition, False)
      self.GetInteractor().Render()

  def leftButtonUp(self, obj, event):
    if self.pipeline.isDragging:
      eventPosition = self.GetInteractor().GetEventPosition()
      self.updateGlyphWithNewPosition(self.pipeline, eventPosition, True)
      self.pipeline.isDragging = False
      self.updateGlyphWithNewPosition(self.pipeline, eventPosition, True)
      if self.HasObserver("MouseMoveEvent"):
        self.RemoveObservers("MouseMoveEvent")
      self.OnLeftButtonUp()

class IPWCallback():
  def __init__(self, planes, mapper) -> None:
    self.planes = planes
    self.mapper = mapper

  def __call__(self, obj: vtk.vtkBoxWidget2, event: str) -> None:
    obj.GetRepresentation().GetPlanes(self.planes)
    self.mapper.SetClippingPlanes(self.planes)