import vtk
from vtkmodules.vtkCommonCore import vtkMath
from vtk.util.numpy_support import vtk_to_numpy, numpy_to_vtk

import math
from typing import List, Tuple

def GetImageToWorldMatrix(imageData: vtk.vtkImageData, mat: vtk.vtkMatrix4x4) -> None:
    mat.Identity()
    origin = imageData.GetOrigin()
    spacing = imageData.GetSpacing()
    directionMatrix = imageData.GetDirectionMatrix()
    for row in range(3):
        for col in range(3):
            mat.SetElement(row, col, spacing[col] * directionMatrix.GetElement(row, col))
        mat.SetElement(row, 3, origin[row])

def SetImageToWorldMatrix(imageData: vtk.vtkImageData, argMat: vtk.vtkMatrix4x4) -> None:
    mat = vtk.vtkMatrix4x4()
    mat.DeepCopy(argMat)

    isModified = False
    spacing = list(imageData.GetSpacing())
    origin = list(imageData.GetOrigin())
    directionMatrix = imageData.GetDirectionMatrix()

    for col in range(3):
        len = 0
        for row in range(3):
            len += mat.GetElement(row, col) * mat.GetElement(row, col)
        len = math.sqrt(len)
        # Set spacing
        if spacing[col] != len:
            spacing[col] = len
            isModified = True
        for row in range(3):
            mat.SetElement(row, col, mat.GetElement(row, col) / len)
    for row in range(3):
        for col in range(3):
            # Set directions
            if directionMatrix.GetElement(row, col) != mat.GetElement(row, col):
                directionMatrix.SetElement(row, col, mat.GetElement(row, col))
                isModified = True
            # Set origin
            if origin[row] != mat.GetElement(row, 3):
                origin[row] = mat.GetElement(row, 3)
                isModified = True
    if isModified:
        imageData.SetSpacing(spacing)
        imageData.SetOrigin(origin)
        imageData.Modified()

def calcClipRange(imageData: vtk.vtkImageData, segmentationToCameraTransform: vtk.vtkTransform, camera: vtk.vtkCamera) -> List:
    segmentationBounds_Camera = [0, -1, 0, -1, 0, -1]
    vtkMath.UninitializeBounds(segmentationBounds_Camera)

    imageExtentCenter = imageData.GetExtent()
    if imageExtentCenter[0]  > imageExtentCenter[0] or imageExtentCenter[2] > imageExtentCenter[3] or imageExtentCenter[4] > imageExtentCenter[5]:
        # Empty image
        return
    
    imageToWorldMatrix = vtk.vtkMatrix4x4()
    GetImageToWorldMatrix(imageData, imageToWorldMatrix)

    imageExtent = [
        imageExtentCenter[0] - 0.5, imageExtentCenter[1] + 0.5,
        imageExtentCenter[2] - 0.5, imageExtentCenter[3] + 0.5,
        imageExtentCenter[4] - 0.5, imageExtentCenter[5] + 0.5
    ]

    appendPolyData = vtk.vtkAppendPolyData()

    for i in range(6):
        normalAxis = int(i/2) # 0, 0, 1, 1, 2, 2
        currentPlaneOriginImage = [imageExtent[0], imageExtent[2], imageExtent[4], 1.0]
        currentPlaneOriginImage[normalAxis] += (imageExtent[i] - imageExtent[normalAxis * 2])
        currentPlaneOriginWorld = [0, 0, 0, 1]
        imageToWorldMatrix.MultiplyPoint(currentPlaneOriginImage, currentPlaneOriginWorld)

        currentPlanePoint1Image = [currentPlaneOriginImage[0], currentPlaneOriginImage[1], currentPlaneOriginImage[2], 1.0]
        point1Axis = (normalAxis + 1) % 3 # 1, 1, 2, 2, 0, 0
        currentPlanePoint1Image[point1Axis] = imageExtent[point1Axis * 2 + 1]
        currentPlanePoint1World = [0, 0, 0, 1]
        imageToWorldMatrix.MultiplyPoint(currentPlanePoint1Image, currentPlanePoint1World)

        currentPlanePoint2Image = [currentPlaneOriginImage[0], currentPlaneOriginImage[1], currentPlaneOriginImage[2], 1.0]
        point2Axis = 3 - normalAxis - point1Axis # 2, 2, 0, 0, 1, 1
        currentPlanePoint2Image[point2Axis] = imageExtent[point2Axis * 2 + 1]
        currentPlanePoint2World = [0, 0, 0, 1]
        imageToWorldMatrix.MultiplyPoint(currentPlanePoint2Image, currentPlanePoint2World)

        planeSource = vtk.vtkPlaneSource()
        planeSource.SetOrigin(currentPlaneOriginWorld[0], currentPlaneOriginWorld[1], currentPlaneOriginWorld[2])
        planeSource.SetPoint1(currentPlanePoint1World[0], currentPlanePoint1World[1], currentPlanePoint1World[2])
        planeSource.SetPoint2(currentPlanePoint2World[0], currentPlanePoint2World[1], currentPlanePoint2World[2])
        planeSource.SetResolution(5, 5)
        planeSource.Update()

        appendPolyData.AddInputData(planeSource.GetOutput())
    
    transformFilter = vtk.vtkTransformPolyDataFilter()
    transformFilter.SetInputConnection(appendPolyData.GetOutputPort())
    transformFilter.SetTransform(segmentationToCameraTransform)
    transformFilter.Update()
    transformFilter.GetOutput().ComputeBounds()
    segmentationBounds_Camera = transformFilter.GetOutput().GetBounds()

    clipRangeFromModifierLabelmap = [
        min(segmentationBounds_Camera[4], segmentationBounds_Camera[5]),
        max(segmentationBounds_Camera[4], segmentationBounds_Camera[5])
    ]
    clipRangeFromModifierLabelmap[0] -= 0.5
    clipRangeFromModifierLabelmap[1] += 0.5

    clipRangeFromCamera = camera.GetClippingRange()
    clipRange = [
        max(clipRangeFromModifierLabelmap[0], clipRangeFromCamera[0]),
        min(clipRangeFromModifierLabelmap[1], clipRangeFromCamera[1])
    ]
    return clipRange

def modifyImage(baseImage: vtk.vtkImageData, modifierImage: vtk.vtkImageData) -> None:
    sourceArray = vtk_to_numpy(modifierImage.GetPointData().GetScalars())
    targetArray = vtk_to_numpy(baseImage.GetPointData().GetScalars())

    result = sourceArray + targetArray

    baseImage.GetPointData().SetScalars(numpy_to_vtk(result))
    baseImage.Modified()

def convertFromDisplayCoords2WorldCoords(point: Tuple[int], focalPoint: List[float], renderer: vtk.vtkRenderer) -> Tuple[float]:
    # Select z-axis when convert the focal point from homogeneous coordinates to display coordinates
    renderer.SetWorldPoint(focalPoint[0], focalPoint[1], focalPoint[2], focalPoint[3]) 
    renderer.WorldToDisplay()
    displayCoord = renderer.GetDisplayPoint()
    selectionz = displayCoord[2] # the distance from the position of camera to screen

    # Convert from display coordinates to world coordinates
    renderer.SetDisplayPoint(point[0], point[1], selectionz)
    renderer.DisplayToWorld()
    worldPoint = renderer.GetWorldPoint()

    return worldPoint