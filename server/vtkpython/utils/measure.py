import vtk
import numpy as np
from typing import List

"""
    description:
        1: convert the focal point to homogenous coordinate system.
        2: convert the focal point to display coordinate system then select the z element.
        3: convert the input point (in display coordinate system) with the z element selected above to world coordinate system
    params:
        focalPoint: a point (in world coordinate system)
        renderer: vtkRenderer object
        point: a point (in display coordinate system) with the z element is None
    return: a point (in world coordinate system)
"""
def convertFromDisplayCoords2WorldCoords(focalPoint: List[float], renderer: vtk.vtkRenderer, point: List[int]) -> List[float]:
    # get z when convert the focal point from homogeneous coords (4D) to display coords (3D)
    renderer.SetWorldPoint(focalPoint[0], focalPoint[1], focalPoint[2], 1) 
    renderer.WorldToDisplay() # 4D -> 3D
    displayCoord = renderer.GetDisplayPoint()
    selectionz = displayCoord[2] # (the distance from the camera position to the screen)

    # get 3D coords when convert from display coords (3D) to world coords (4D)
    renderer.SetDisplayPoint(point[0], point[1], selectionz)
    renderer.DisplayToWorld() # 3D -> 4D
    worldPoint = renderer.GetWorldPoint()
    pickPosition = [0, 0, 0]
    for i in range(3):
        pickPosition[i] = worldPoint[i] / worldPoint[3] if worldPoint[3] else worldPoint[i]
    return pickPosition

def convertFromWorldCoords2DisplayCoords(renderer: vtk.vtkRenderer, point: List[float]) -> List[float]:
    renderer.SetWorldPoint(point[0], point[1], point[2], 1)
    renderer.WorldToDisplay()
    return list(renderer.GetDisplayPoint())

def getEuclideDistanceBetween2Points(firstPoint: List[float], secondPoint: List[float]) -> float:
    return np.linalg.norm(np.array(secondPoint) - np.array(firstPoint))

"""
    description: 
        building a plane by the first point and the direction vector of projection.
        after finding the projection point of the second point.
    params:
        firstPoint: a point (in world coordinate system)
        directionOfProjection: a vector (in world coordinate system)
        sencondPoint: a point (in world coordinate system)
    return: a projection point
"""
def findProjectionPoint(firstPoint: List[float], directionOfProjection: List[float], secondPoint: List[float]) -> List[float]:
    x1 = firstPoint[0]; y1 = firstPoint[1]; z1 = firstPoint[2]
    a = directionOfProjection[0]; b = directionOfProjection[1]; c = directionOfProjection[2]
    x2 = secondPoint[0]; y2 = secondPoint[1]; z2 = secondPoint[2]
    '''
        first point: [x1, y1, z1] (in world coordinate system)
        direction of projection: [a, b, c] (the normal vector of the plane, the direction vector of the straight line)
        second point: [x2, y2, z2] (in world coordinate system)
        the plane equation: 
            a(x - x1) + b(y - y1) + c(z - z1) = 0
        linear equations:
            x = x2 + at
            y = y2 + bt
            z = z2 + ct
    '''
    x = lambda t: x2 + a * t
    y = lambda t: y2 + b * t
    z = lambda t: z2 + c * t
    t = (a * x1 - a * x2 + b * y1 - b * y2 + c * z1 - c * z2) / (a*a + b*b + c*c)
    return [x(t), y(t), z(t)]

"""
    description:
        method returns a point (on surface or out in world coordinate system) through vtkCellPicker object.
        method can return a projection point (in case out).
    params:
        cellPicker: vtkCellPicker object
        eventPosition: a point (in display coordinate system)
        renderer: vtkRenderer object
        camera: vtkCamera object
        checkToGetProjectionPoint: default=False, type=bool
        firstPoint: a point (in world coordinate system) if return a projection point, default=None, type=List
    return: a point (in world coordinate system)
"""
def getPickPosition(cellPicker: vtk.vtkCellPicker, eventPosition: List[int], renderer: vtk.vtkRenderer, camera: vtk.vtkCamera, checkToGetProjectionPoint=False, firstPoint=None) -> List[float]:
    pickPosition = None
    check = cellPicker.Pick(eventPosition[0], eventPosition[1], 0, renderer)
    if check:
        pickPosition = list(cellPicker.GetPickPosition())
    else:
        pickPosition = convertFromDisplayCoords2WorldCoords(camera.GetFocalPoint(), renderer, eventPosition)
        if checkToGetProjectionPoint:
            projectionPoint = findProjectionPoint(firstPoint, camera.GetDirectionOfProjection(), pickPosition)
            pickPosition = projectionPoint
    return pickPosition