import vtk
from vtkmodules.vtkCommonCore import vtkMath, vtkCommand
from vtk.util.numpy_support import vtk_to_numpy, numpy_to_vtk

from models.cropping.operationMode import OperationMode

from enum import Enum
import math
from typing import List, Tuple

from utils import utils

class Contour2Dpipeline():
    def __init__(self) -> None:
        self.isDragging = False
        self.polyData = vtk.vtkPolyData()
        self.mapper2D = vtk.vtkPolyDataMapper2D()
        self.mapper2D.SetInputData(self.polyData)
        self.actor2D = vtk.vtkActor2D()
        self.actor2D.SetMapper(self.mapper2D)
        self.actor2D.GetProperty().SetColor(1, 1, 0)
        self.actor2D.GetProperty().SetLineWidth(2)
        self.actor2D.VisibilityOff()
        # Thin
        self.polyDataThin = vtk.vtkPolyData()
        self.mapper2DThin = vtk.vtkPolyDataMapper2D()
        self.mapper2DThin.SetInputData(self.polyDataThin)
        self.actor2DThin = vtk.vtkActor2D()
        self.actor2DThin.SetMapper(self.mapper2DThin)
        outlinePropertyThin = self.actor2DThin.GetProperty()
        outlinePropertyThin.SetColor(0.7, 0.7, 0)
        outlinePropertyThin.SetLineStipplePattern(0xff00)
        outlinePropertyThin.SetLineWidth(1)
        self.actor2DThin.VisibilityOff()
        # Test
        colors = vtk.vtkNamedColors()
        self.polyData3D = vtk.vtkPolyData()
        # Mappers
        self.polyData3Dmapper = vtk.vtkPolyDataMapper()
        self.polyData3Dmapper.SetInputData(self.polyData3D)
        # Actors
        property = vtk.vtkProperty()
        property.SetColor(colors.GetColor3d("Tomato"))
        self.polyData3Dactor = vtk.vtkActor()
        self.polyData3Dactor.SetMapper(self.polyData3Dmapper)
        self.polyData3Dactor.SetProperty(property)
        self.polyData3Dactor.VisibilityOff()

class CroppingFreehandInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self, contour2Dpipeline: Contour2Dpipeline, originImageData: vtk.vtkImageData, modifierLabelmap: vtk.vtkImageData, operationMode: Enum, mapper: vtk.vtkSmartVolumeMapper) -> None:
        self.contour2Dpipeline = contour2Dpipeline
        self.originImageData = originImageData
        self.modifierLabelmap = modifierLabelmap
        self.operationMode = operationMode
        self.mapper = mapper

        self.AddObserver(vtkCommand.LeftButtonPressEvent, self.__leftButtonPressEvent)
        self.AddObserver(vtkCommand.MouseMoveEvent, self.__mouseMoveEvent)
        self.AddObserver(vtkCommand.LeftButtonReleaseEvent, self.__leftButtonReleaseEvent)

        self.brushPolyDataNormals = vtk.vtkPolyDataNormals()
        self.brushPolyDataNormals.AutoOrientNormalsOn()

        self.worldToModifierLabelmapIjkTransformer = vtk.vtkTransformPolyDataFilter()
        self.worldToModifierLabelmapIjkTransform = vtk.vtkTransform()
        self.worldToModifierLabelmapIjkTransformer.SetTransform(self.worldToModifierLabelmapIjkTransform)
        self.worldToModifierLabelmapIjkTransformer.SetInputConnection(self.brushPolyDataNormals.GetOutputPort())

        self.brushPolyDataToStencil = vtk.vtkPolyDataToImageStencil()
        self.brushPolyDataToStencil.SetOutputOrigin(0, 0, 0)
        self.brushPolyDataToStencil.SetOutputSpacing(1, 1, 1)
        self.brushPolyDataToStencil.SetInputConnection(self.worldToModifierLabelmapIjkTransformer.GetOutputPort())
        
    def __createGlyph(self, eventPosition: Tuple) -> None:
        if self.contour2Dpipeline.isDragging:
            points = vtk.vtkPoints()
            lines = vtk.vtkCellArray()
            self.contour2Dpipeline.polyData.SetPoints(points)
            self.contour2Dpipeline.polyData.SetLines(lines)

            points.InsertNextPoint(eventPosition[0], eventPosition[1], 0)

            # Thin
            pointsThin = vtk.vtkPoints()
            linesThin = vtk.vtkCellArray()
            self.contour2Dpipeline.polyDataThin.SetPoints(pointsThin)
            self.contour2Dpipeline.polyDataThin.SetLines(linesThin)

            pointsThin.InsertNextPoint(eventPosition[0], eventPosition[1], 0)
            pointsThin.InsertNextPoint(eventPosition[0], eventPosition[1], 0)

            idList = vtk.vtkIdList()
            idList.InsertNextId(0)
            idList.InsertNextId(1)
            self.contour2Dpipeline.polyDataThin.InsertNextCell(vtk.VTK_LINE, idList)

            self.contour2Dpipeline.actor2DThin.VisibilityOn()
            self.contour2Dpipeline.actor2D.VisibilityOn()
        else:
            self.contour2Dpipeline.actor2D.VisibilityOff()
            self.contour2Dpipeline.actor2DThin.VisibilityOff()

    def __updateGlyphWithNewPosition(self, eventPosition: Tuple, finalize: bool) -> None:
        if self.contour2Dpipeline.isDragging:
            points = self.contour2Dpipeline.polyData.GetPoints()
            newPointIndex = points.InsertNextPoint(eventPosition[0], eventPosition[1], 0)
            points.Modified()

            idList = vtk.vtkIdList()
            if finalize:
                idList.InsertNextId(newPointIndex)
                idList.InsertNextId(0)
            else:
                idList.InsertNextId(newPointIndex - 1)
                idList.InsertNextId(newPointIndex)

            self.contour2Dpipeline.polyData.InsertNextCell(vtk.VTK_LINE, idList)

            self.contour2Dpipeline.polyDataThin.GetPoints().SetPoint(1, eventPosition[0], eventPosition[1], 0)
            self.contour2Dpipeline.polyDataThin.GetPoints().Modified()
        else:
            self.contour2Dpipeline.actor2D.VisibilityOff()
            self.contour2Dpipeline.actor2DThin.VisibilityOff()

    def __leftButtonPressEvent(self, obj: vtk.vtkInteractorStyleTrackballCamera, event: str) -> None:
        self.contour2Dpipeline.isDragging = True
        eventPosition = self.GetInteractor().GetEventPosition()
        self.__createGlyph(eventPosition)

        self.OnLeftButtonDown()

    def __mouseMoveEvent(self, obj: vtk.vtkInteractorStyleTrackballCamera, event: str) -> None:
        if self.contour2Dpipeline.isDragging:
            eventPosition = self.GetInteractor().GetEventPosition()
            self.__updateGlyphWithNewPosition(eventPosition, False)
            self.GetInteractor().Render()
        else:
            self.OnMouseMove()

    def __leftButtonReleaseEvent(self, obj: vtk.vtkInteractorStyleTrackballCamera, event: str) -> None:
        if self.contour2Dpipeline.isDragging:
            eventPosition = self.GetInteractor().GetEventPosition()
            self.contour2Dpipeline.isDragging = False
            self.__updateGlyphWithNewPosition(eventPosition, True)
            self.__paintApply()
            self.OnLeftButtonUp()

            style = vtk.vtkInteractorStyleTrackballCamera()
            self.GetInteractor().SetInteractorStyle(style)

    def __updateBrushModel(self):
        renderer = self.GetInteractor().GetRenderWindow().GetRenderers().GetFirstRenderer()
        camera = renderer.GetActiveCamera()

        pointsXY = self.contour2Dpipeline.polyData.GetPoints()
        numberOfPoints = pointsXY.GetNumberOfPoints()

        segmentationToWorldMatrix = vtk.vtkMatrix4x4()
        segmentationToWorldMatrix.Identity()

        closedSurfacePoints = vtk.vtkPoints()

        # Camera position
        cameraPos = list(camera.GetPosition())
        cameraPos.append(1.0)
        # Camera focal point
        cameraFP = list(camera.GetFocalPoint())
        cameraFP.append(1.0)
        # Direction of projection
        cameraDOP = [0, 0, 0]
        for i in range(3):
            cameraDOP[i] = cameraFP[i] - cameraPos[i]
        vtkMath.Normalize(cameraDOP)
        # Camera view up
        cameraViewUp = list(camera.GetViewUp())
        vtkMath.Normalize(cameraViewUp)

        cameraToWorldMatrix = vtk.vtkMatrix4x4()
        cameraViewRight = [1, 0, 0]
        vtkMath.Cross(cameraDOP, cameraViewUp, cameraViewRight) # Tích có hướng
        for i in range(3):
            cameraToWorldMatrix.SetElement(i, 0, cameraViewUp[i])
            cameraToWorldMatrix.SetElement(i, 1, cameraViewRight[i])
            cameraToWorldMatrix.SetElement(i, 2, cameraDOP[i])
            cameraToWorldMatrix.SetElement(i, 3, cameraPos[i])

        worldToCameraMatrix = vtk.vtkMatrix4x4()
        vtk.vtkMatrix4x4().Invert(cameraToWorldMatrix, worldToCameraMatrix)

        segmentationToCameraTransform = vtk.vtkTransform()
        segmentationToCameraTransform.Concatenate(worldToCameraMatrix)
        segmentationToCameraTransform.Concatenate(segmentationToWorldMatrix)

        clipRange = utils.calcClipRange(self.modifierLabelmap, segmentationToCameraTransform, camera)

        for pointIndex in range(numberOfPoints):
            pointXY = pointsXY.GetPoint(pointIndex)
            worldCoords = utils.convertFromDisplayCoords2WorldCoords(pointXY, cameraFP, renderer)
            if worldCoords[3] == 0:
                print("Bad homogeneous coordinates")
                return False
            
            pickPosition = [0, 0, 0]
            for i in range(3):
                pickPosition[i] = worldCoords[i] / worldCoords[3]

            ray = [0, 0, 0]
            for i in range(3):
                ray[i] = pickPosition[i] - cameraPos[i]
            rayLength = vtkMath.Dot(cameraDOP, ray)
            if rayLength == 0:
                print("Cannot process points")
                return False
            
            p1World = [0, 0, 0]
            p2World = [0, 0, 0]
            tF = 0
            tB = 0
            if camera.GetParallelProjection():
                tF = clipRange[0] - rayLength
                tB = clipRange[1] - rayLength
                for i in range(3):
                    p1World[i] = pickPosition[i] + tF * cameraDOP[i]
                    p2World[i] = pickPosition[i] + tB * cameraDOP[i]
            else:
                tF = clipRange[0] / rayLength
                tB = clipRange[1] / rayLength
                for i in range(3):
                    p1World[i] = cameraPos[i] + tF * ray[i]
                    p2World[i] = cameraPos[i] + tB * ray[i]
                closedSurfacePoints.InsertNextPoint(p1World)
                closedSurfacePoints.InsertNextPoint(p2World)

        # Skirt
        closedSurfaceStrips = vtk.vtkCellArray() # object to represent cell connectivity
        # Create cells by specifying a count of total points to be inserted,
        # and then adding points one at a time using method InsertCellPoint()
        closedSurfaceStrips.InsertNextCell(numberOfPoints * 2 + 2)
        for i in range(numberOfPoints * 2):
            closedSurfaceStrips.InsertCellPoint(i)
        closedSurfaceStrips.InsertCellPoint(0)
        closedSurfaceStrips.InsertCellPoint(1)

        # Front cap
        closedSurfacePolys = vtk.vtkCellArray() # object to represent cell connectivity
        closedSurfacePolys.InsertNextCell(numberOfPoints)
        for i in range(numberOfPoints):
            closedSurfacePolys.InsertCellPoint(i * 2)

        # Back cap
        closedSurfacePolys.InsertNextCell(numberOfPoints)
        for i in range(numberOfPoints):
            closedSurfacePolys.InsertCellPoint(i * 2 + 1)
        
        # Construct polydata
        # closedSurfacePolyData = self.contour2Dpipeline.polyData3D
        closedSurfacePolyData = vtk.vtkPolyData()
        closedSurfacePolyData.SetPoints(closedSurfacePoints)
        closedSurfacePolyData.SetStrips(closedSurfaceStrips)
        closedSurfacePolyData.SetPolys(closedSurfacePolys)

        # self.contour2Dpipeline.polyData3Dactor.VisibilityOn()
        # self.GetInteractor().Render()

        self.brushPolyDataNormals.SetInputData(closedSurfacePolyData)
        self.brushPolyDataNormals.Update()

        return True
    
    def __updateBrushStencil(self) -> None:
        self.worldToModifierLabelmapIjkTransform.Identity()

        segmentationToSegmentationIjkTransformMatrix = vtk.vtkMatrix4x4()
        utils.GetImageToWorldMatrix(self.modifierLabelmap, segmentationToSegmentationIjkTransformMatrix)
        segmentationToSegmentationIjkTransformMatrix.Invert()
        self.worldToModifierLabelmapIjkTransform.Concatenate(segmentationToSegmentationIjkTransformMatrix)

        worldToSegmentationTransformMatrix = vtk.vtkMatrix4x4()
        worldToSegmentationTransformMatrix.Identity()
        self.worldToModifierLabelmapIjkTransform.Concatenate(worldToSegmentationTransformMatrix)

        self.worldToModifierLabelmapIjkTransformer.Update()

        self.brushPolyDataToStencil.SetOutputWholeExtent(self.modifierLabelmap.GetExtent())

    def __paintApply(self) -> None:
        if not self.__updateBrushModel():
            return
        self.__updateBrushStencil()

        self.brushPolyDataToStencil.Update()
    
        # vtkImageStencilToImage will convert an image stencil into a binary image
        # The default output will be an 8-bit image with a value of 1 inside the stencil and 0 outside
        stencilToImage = vtk.vtkImageStencilToImage()
        stencilToImage.SetInputData(self.brushPolyDataToStencil.GetOutput())

        stencilToImage.SetInsideValue(self.operationMode == OperationMode.INSIDE)
        stencilToImage.SetOutsideValue(self.operationMode != OperationMode.INSIDE)

        stencilToImage.SetOutputScalarType(self.modifierLabelmap.GetScalarType()) # vtk.VTK_SHORT: [-32768->32767], vtk.VTK_UNSIGNED_CHAR: [0->255]
        stencilToImage.Update()

        orientedBrushPositionerOutput = vtk.vtkImageData()
        orientedBrushPositionerOutput.DeepCopy(stencilToImage.GetOutput())

        imageToWorld = vtk.vtkMatrix4x4()
        utils.GetImageToWorldMatrix(self.modifierLabelmap, imageToWorld)

        utils.SetImageToWorldMatrix(orientedBrushPositionerOutput, imageToWorld)

        utils.modifyImage(self.modifierLabelmap, orientedBrushPositionerOutput)
        self.__maskVolume(0)

    def __maskVolume(self, softEdgeMm) -> None:
        if not softEdgeMm:
            # Hard edge
            maskToStencil = vtk.vtkImageToImageStencil()
            maskToStencil.ThresholdByLower(0)
            maskToStencil.SetInputData(self.modifierLabelmap)
            maskToStencil.Update()
            
            stencil = vtk.vtkImageStencil()
            stencil.SetInputData(self.originImageData)
            stencil.SetStencilConnection(maskToStencil.GetOutputPort())
            stencil.SetBackgroundValue(-1000) # default value
            stencil.Update()
            # Render the new volume
            self.mapper.SetInputData(stencil.GetOutput())
        else:
            # Soft edge
            thresh = vtk.vtkImageThreshold()
            maskMin = 0
            maskMax = 255
            thresh.SetOutputScalarTypeToUnsignedChar() # vtk.VTK_UNSIGNED_CHAR: 0-255
            thresh.SetInputData(self.modifierLabelmap)
            thresh.ThresholdByLower(0) # <= 0
            thresh.SetInValue(maskMin)
            thresh.SetOutValue(maskMax)
            thresh.Update()
    
            # Bộ lọc gaussian được sử dụng để làm mờ ảnh
            gaussianFilter = vtk.vtkImageGaussianSmooth()
            gaussianFilter.SetInputData(thresh.GetOutput())
            spacing = self.modifierLabelmap.GetSpacing()
            standardDeviationPixel = [1, 1, 1]
            for index in range(3):
                standardDeviationPixel[index] = softEdgeMm / spacing[index]
            # Sử dụng để thiết lập các độ lệch chuẩn (standard deviations) của bộ lọc Gaussian trong quá trình làm mờ ảnh.
            # Các độ lệch chuẩn này xác định mức độ làm mờ của bộ lọc Gaussian theo từng chiều. 
            # Khi giá trị độ lệch chuẩn càng lớn, hiệu ứng làm mờ càng mạnh.
            gaussianFilter.SetStandardDeviations(standardDeviationPixel)
            # Sử dụng để thiết lập hệ số bán kính (radius factor) cho bộ lọc Gaussian. 
            # Hệ số này ảnh hưởng đến kích thước của bán kính thực tế của bộ lọc.
            gaussianFilter.SetRadiusFactor(3)
            gaussianFilter.Update() # bộ lọc sẽ thực hiện convolution (tích chập)
            maskImage = gaussianFilter.GetOutput() # vtkImageData

            nshape = tuple(reversed(maskImage.GetDimensions())) # (z, y, x)
            maskArray = vtk_to_numpy(maskImage.GetPointData().GetScalars()).reshape(nshape)
            # Normalize mask
            maskMin = maskArray.min()
            maskMax = maskArray.max()
            mask = (maskArray.astype(float) - maskMin) / float(maskMax - maskMin)

            inputArray = vtk_to_numpy(self.imageData.GetPointData().GetScalars()).reshape(nshape)

            mask = 1.0 - mask # reverse mask
            resultArray = inputArray[:] * mask[:] + float(-1000) * (1 - mask[:]) # -1000 HU: air

            result = numpy_to_vtk(resultArray.astype(inputArray.dtype).reshape(1, -1)[0])

            maskedImageData = vtk.vtkImageData()
            maskedImageData.SetExtent(self.modifierLabelmap.GetExtent())
            maskedImageData.SetOrigin(self.modifierLabelmap.GetOrigin())
            maskedImageData.SetSpacing(self.modifierLabelmap.GetSpacing())
            maskedImageData.SetDirectionMatrix(self.modifierLabelmap.GetDirectionMatrix())
            maskedImageData.GetPointData().SetScalars(result)
            # Render the new volume
            self.mapper.SetInputData(maskedImageData)