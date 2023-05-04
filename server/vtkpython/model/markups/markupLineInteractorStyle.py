import vtk
from typing import List
import numpy as np

class MarkupLineInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self, pipeline):
        self.pipeline = pipeline
        self.AddObserver("LeftButtonPressEvent", self.leftButtonDown)
        # self.AddObserver("MouseMoveEvent", self.mouseMove)
        self.AddObserver("LeftButtonReleaseEvent", self.leftButtonUp)

    def get3dCoordsFrom2dCoord(self, point2d: tuple) -> List:
        render = self.GetInteractor().GetRenderWindow().GetRenderers().GetFirstRenderer()
        camera = render.GetActiveCamera()
        focalPoint = camera.GetFocalPoint()
        
        # Get coords of z-axis when convert focal point from world coords to display coords
        render.SetWorldPoint(focalPoint[0], focalPoint[1], focalPoint[2], 1)
        render.WorldToDisplay()
        displayCoords = render.GetDisplayPoint()
        selectionZ = displayCoords[2]

        # Get world coords when convert from display coords
        render.SetDisplayPoint(point2d[0], point2d[1], selectionZ)
        render.DisplayToWorld()
        worldCoords = render.GetWorldPoint()
        posi = [0, 0, 0]
        for i in range(3):
            posi[i] = worldCoords[i] / worldCoords[3] if worldCoords[3] else worldCoords[i]
        return posi
    
    def euclideanDist(self, firstPoint: tuple, secondPoint: tuple) -> float:
        return np.linalg.norm(np.array(secondPoint) - np.array(firstPoint))
    
    def createGlyph(self, eventPosition: tuple) -> None:
        if self.pipeline.isDragging:
            render = self.GetInteractor().GetRenderWindow().GetRenderers().GetFirstRenderer()
            pickPosition = None
            cellPicker = vtk.vtkCellPicker()
            check = cellPicker.Pick(eventPosition[0], eventPosition[1], 0, render)
            if check:
                pickPosition = cellPicker.GetPickedPositions().GetPoint(0)
            else:
                pickPosition = self.get3dCoordsFrom2dCoord(eventPosition)

            self.pipeline.firstSphereActor.SetPosition(pickPosition)
            self.pipeline.firstSphereActor.VisibilityOn()

            points = vtk.vtkPoints()
            line = vtk.vtkCellArray()
            self.pipeline.polyData.SetPoints(points)
            self.pipeline.polyData.SetLines(line)

            points.InsertNextPoint(pickPosition)
            points.InsertNextPoint([0, 0, 0]) # Set defauld

            self.pipeline.actor.VisibilityOn()
        else:
            self.pipeline.actor.VisibilityOff()
            self.pipeline.showLength.VisibilityOff()
            self.pipeline.firstSphereActor.VisibilityOff()

    def updateGlyph(self, eventPosition: tuple) -> None:
        if self.pipeline.isDragging:
            render = self.GetInteractor().GetRenderWindow().GetRenderers().GetFirstRenderer()
            pickPosition = None
            cellPicker = vtk.vtkCellPicker()
            check = cellPicker.Pick(eventPosition[0], eventPosition[1], 0, render)
            if check:
                pickPosition = cellPicker.GetPickedPositions().GetPoint(0)
            else:
                pickPosition = self.get3dCoordsFrom2dCoord(eventPosition)

            self.pipeline.secondSphereActor.SetPosition(pickPosition)
            self.pipeline.secondSphereActor.VisibilityOn()

            points = self.pipeline.polyData.GetPoints()
            points.SetPoint(1, pickPosition)

            idList = vtk.vtkIdList()
            idList.InsertNextId(0); idList.InsertNextId(1)

            self.pipeline.polyData.InsertNextCell(vtk.VTK_LINE, idList)
            points.Modified()

            eucliDist = self.euclideanDist(points.GetPoint(0), points.GetPoint(1))
            self.pipeline.showLength.SetInput(f"{round(eucliDist, 1)}mm")
            self.pipeline.showLength.SetPosition(points.GetPoint(1))

            self.pipeline.showLength.VisibilityOn()
        else:
            self.pipeline.actor.VisibilityOff()
            self.pipeline.showLength.VisibilityOff()
            self.pipeline.secondSphereActor.VisibilityOff()

    def mouseMove(self, obj, event) -> None:
        render = self.GetInteractor().GetRenderWindow().GetRenderers().GetFirstRenderer()
        eventPosition = self.GetInteractor().GetEventPosition()
        cellPicker = vtk.vtkCellPicker()
        check = cellPicker.Pick(eventPosition[0], eventPosition[1], 0, render)
        pickPosition = None
        if check:
            pickPosition = cellPicker.GetPickedPositions().GetPoint(0)
        else:
            pickPosition = self.get3dCoordsFrom2dCoord(eventPosition)

        self.pipeline.firstSphereActor.SetPosition(pickPosition)
        self.pipeline.firstSphereActor.VisibilityOn()

        self.GetInteractor().Render()
        # print("mouse move")
    
    def leftButtonDown(self, obj, event) -> None:
        self.pipeline.isDragging = True # Start to paint
        eventPosition = self.GetInteractor().GetEventPosition()
        self.createGlyph(eventPosition)
        if not self.HasObserver("MouseMoveEvent"):
            self.AddObserver("MouseMoveEvent", self.leftMouseMove)
        self.OnLeftButtonDown()
        # print("left button down")

    def leftMouseMove(self, obj, event) -> None:
        eventPosition = self.GetInteractor().GetEventPosition()
        self.updateGlyph(eventPosition)
        self.GetInteractor().Render()

    def leftButtonUp(self, obj, event) -> None:
        self.pipeline.isDragging = False # Stop to paint
        if self.HasObserver("MouseMoveEvent"):
            self.RemoveObservers("MouseMoveEvent")
        self.OnLeftButtonUp()
        self.GetInteractor().SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())
