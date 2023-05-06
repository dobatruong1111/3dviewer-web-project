from typing import Any
from vtk.web import protocols as vtk_protocols
from wslink import register as exportRpc

import vtk
from model.colormap import CUSTOM_COLORMAP
from model.presets import *
from model.measure.viewer3dMeasureLength import Viewer3dMeasureLengthPipeline, Viewer3dMeasureLengthInteractorStyle, Viewer3dAfterMeasureLengthInteractorStyle

# -------------------------------------------------------------------------
# 3D Viewer Manager
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
        # cropping
        self.boxRep = vtk.vtkBoxRepresentation()
        self.widget = vtk.vtkBoxWidget2()
        self.planes = vtk.vtkPlanes()
        # outline
        self.outline = vtk.vtkOutlineFilter()
        self.outlineMapper = vtk.vtkPolyDataMapper()
        self.outlineActor = vtk.vtkActor()
        # cell picker
        self.cellPicker = vtk.vtkCellPicker()
        # measure length
        self.afterMeasureLengthInteractorStyle = Viewer3dAfterMeasureLengthInteractorStyle()

    @exportRpc("vtk.initialize")
    def createVisualization(self):
        renderWindowInteractor = self.getApplication().GetObjectIdMap().GetActiveObject("INTERACTOR")
        renderWindow = self.getView('-1')
        renderer = renderWindow.GetRenderers().GetFirstRenderer()
      
        # reader
        path = "C:/Users/DELL E5540/Desktop/Python/dicom-data/64733 NGUYEN TAN THANH/DONG MACH CHI DUOI CTA/CT CTA iDose 5"
        self.reader.SetDirectoryName(path)
        self.reader.Update()

        # outline
        self.outline.SetInputConnection(self.reader.GetOutputPort())
        self.outlineMapper.SetInputConnection(self.outline.GetOutputPort())
        self.outlineActor.SetMapper(self.outlineMapper)
        self.outlineActor.GetProperty().SetColor(0, 0, 0)

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

        # muscle CT
        self.scalarOpacity.RemoveAllPoints()
        scalarOpacityRange = MUSCLE_CT.get("transferFunction").get("scalarOpacityRange")
        self.scalarOpacity.AddPoint(scalarOpacityRange[0], 0)
        self.scalarOpacity.AddPoint(scalarOpacityRange[1], 1)
        self.volProperty.SetScalarOpacity(self.scalarOpacity)

        # volume
        self.volume.SetMapper(self.mapper)
        self.volume.SetProperty(self.volProperty)

        # cropping
        self.boxRep.GetOutlineProperty().SetColor(0, 0, 0)
        self.boxRep.SetInsideOut(True)

        self.widget.SetRepresentation(self.boxRep)
        self.widget.SetInteractor(renderWindowInteractor)
        self.widget.GetRepresentation().SetPlaceFactor(1)
        self.widget.GetRepresentation().PlaceWidget(self.reader.GetOutput().GetBounds())
        self.widget.SetEnabled(True)

        ipwcallback = IPWCallback(self.planes, self.mapper)
        self.widget.AddObserver(vtk.vtkCommand.InteractionEvent, ipwcallback)
        self.widget.Off()

        # render
        renderer.AddVolume(self.volume)
        renderer.AddActor(self.outlineActor)

        # render window

        # render window interactor
        self.cellPicker.AddPickList(self.volume)
        self.cellPicker.PickFromListOn()
        renderWindowInteractor.SetPicker(self.cellPicker)
        # style = InteractorStyle()
        # renderWindowInteractor.SetInteractorStyle(style)
        # renderWindowInteractor.Render()
        # renderWindow.Render()
        # renderWindowInteractor.Start()

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
        self.outlineActor.GetProperty().SetColor(1, 1, 1)
        self.checkLight = False
      else:
        renderer.SetBackground(self.colors.GetColor3d("White"))
        self.boxRep.GetOutlineProperty().SetColor(0, 0, 0)
        self.outlineActor.GetProperty().SetColor(0, 0, 0)
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

    @exportRpc("vtk.dicom3d.measure.length")
    def measureLength(self):
      renderWindowInteractor = self.getApplication().GetObjectIdMap().GetActiveObject("INTERACTOR")
      renderWindow = self.getView('-1')
      renderer = renderWindow.GetRenderers().GetFirstRenderer()

      measureLengthPipeline = Viewer3dMeasureLengthPipeline()
      renderer.AddActor(measureLengthPipeline.lineActor)
      renderer.AddActor(measureLengthPipeline.showLength)
      renderer.AddActor(measureLengthPipeline.firstSphereActor)
      renderer.AddActor(measureLengthPipeline.secondSphereActor)

      style = Viewer3dMeasureLengthInteractorStyle(measureLengthPipeline, self.afterMeasureLengthInteractorStyle)
      renderWindowInteractor.SetInteractorStyle(style)

      self.getApplication().InvokeEvent('UpdateEvent')
      print("measure length")

class IPWCallback():
  def __init__(self, planes, mapper) -> None:
    self.planes = planes
    self.mapper = mapper

  def __call__(self, obj: vtk.vtkBoxWidget2, event: str) -> None:
    obj.GetRepresentation().GetPlanes(self.planes)
    self.mapper.SetClippingPlanes(self.planes)

class InteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
  def __init__(self) -> None:
    self.AddObserver("LeftButtonPressEvent", self.leftButtonDownEvent)
    self.AddObserver("MouseMoveEvent", self.mouseMoveEvent)
    self.AddObserver("LeftButtonReleaseEvent", self.leftButtonUpEvent)

  def leftButtonDownEvent(self, obj, event) -> None:
    print("lefft button down")
    self.OnLeftButtonDown()

  def mouseMoveEvent(self, obj, event) -> None:
    print("mouse move")
    self.GetInteractor().Render()
    self.OnMouseMove()

  def leftButtonUpEvent(self, obj, event) -> None:
    print("left button up")
    self.OnLeftButtonUp()