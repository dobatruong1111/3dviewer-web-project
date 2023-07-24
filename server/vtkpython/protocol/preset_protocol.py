from wslink import register as exportRpc

from protocol.vtk_protocol import Dicom3D
from models.presets import *

class Preset3D(Dicom3D):
    def __init__(self):
        super().__init__()

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