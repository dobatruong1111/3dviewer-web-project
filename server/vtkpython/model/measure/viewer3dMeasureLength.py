import vtk
from utils import measure as util

class Viewer3dMeasureLengthPipeline():
    def __init__(self) -> None:
        self.colors = vtk.vtkNamedColors()
        self.isDragging = False

        # Line
        self.polyData = vtk.vtkPolyData()
        self.tubeFilter = vtk.vtkTubeFilter()
        self.tubeFilter.SetInputData(self.polyData)
        self.tubeFilter.SetNumberOfSides(20)
        self.tubeFilter.SetRadius(1)
        self.lineMaper = vtk.vtkPolyDataMapper()
        self.lineMaper.SetInputConnection(self.tubeFilter.GetOutputPort())
        self.lineActor = vtk.vtkActor()
        self.lineActor.SetMapper(self.lineMaper)
        lineActorProperty = self.lineActor.GetProperty()
        lineActorProperty.SetColor(self.colors.GetColor3d("Tomato"))
        lineActorProperty.SetLineWidth(2)
        self.lineActor.VisibilityOff()

        # Display the length of two points (in world coordinate system)
        self.showLength = vtk.vtkTextActor()
        lengthProperty = self.showLength.GetTextProperty()
        lengthProperty.SetColor(self.colors.GetColor3d("Tomato"))
        lengthProperty.SetFontSize(15)
        lengthProperty.SetOpacity(1)
        lengthProperty.SetBackgroundOpacity(0)
        lengthProperty.ShadowOn()
        lengthProperty.BoldOn()
        self.showLength.VisibilityOff()

        # Two spheres to mark two points (in world coordinate system)
        self.firstSphere = vtk.vtkSphereSource()
        self.firstSphere.SetRadius(5)
        self.firstSphereMapper = vtk.vtkPolyDataMapper()
        self.firstSphereMapper.SetInputConnection(self.firstSphere.GetOutputPort())
        self.firstSphereActor = vtk.vtkActor()
        self.firstSphereActor.GetProperty().SetColor(1, 0, 0)
        self.firstSphereActor.SetMapper(self.firstSphereMapper)
        self.firstSphereActor.VisibilityOff()

        self.secondSphere = vtk.vtkSphereSource()
        self.secondSphere.SetRadius(5)
        self.secondSphereMapper = vtk.vtkPolyDataMapper()
        self.secondSphereMapper.SetInputConnection(self.secondSphere.GetOutputPort())
        self.secondSphereActor = vtk.vtkActor()
        self.secondSphereActor.GetProperty().SetColor(1, 0, 0)
        self.secondSphereActor.SetMapper(self.secondSphereMapper)
        self.secondSphereActor.VisibilityOff()

class Viewer3dAfterMeasureLengthInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self) -> None:
        self.pipelines = []
        self.AddObserver("MouseMoveEvent", self.mouseMoveEvent)

    def addPipeline(self, pipeline) -> None:
        self.pipelines.append(pipeline)

    def mouseMoveEvent(self, obj: vtk.vtkInteractorStyleTrackballCamera, event: str) -> None:
        if len(self.pipelines):
            for pipeline in self.pipelines:
                renderer = self.GetInteractor().GetRenderWindow().GetRenderers().GetFirstRenderer()
                points = pipeline.polyData.GetPoints()
                midPoint = list(map(lambda i,j: (i+j)/2, points.GetPoint(0), points.GetPoint(1)))
                displayCoords = util.convertFromWorldCoords2DisplayCoords(renderer, midPoint)
                pipeline.showLength.SetDisplayPosition(round(displayCoords[0]), round(displayCoords[1]))
            self.GetInteractor().Render()
        self.OnMouseMove()

class Viewer3dMeasureLengthInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self, pipeline: Viewer3dMeasureLengthPipeline, afterMeasureLengthInteractorStyle: Viewer3dAfterMeasureLengthInteractorStyle) -> None:
        self.pipeline = pipeline
        self.afterMeasureLengthInteractorStyle = afterMeasureLengthInteractorStyle
        self.AddObserver("LeftButtonPressEvent", self.leftButtonDownEvent)
        self.AddObserver("MouseMoveEvent", self.mouseMoveEvent)
        self.AddObserver("LeftButtonReleaseEvent", self.leftButtonUpEvent)

    def mouseMoveEvent(self, obj: vtk.vtkInteractorStyleTrackballCamera, event: str) -> None:
        print("mouse move")
        renderer = self.GetInteractor().GetRenderWindow().GetRenderers().GetFirstRenderer()
        camera = renderer.GetActiveCamera()
        eventPosition = self.GetInteractor().GetEventPosition()
        cellPicker = self.GetInteractor().GetPicker()
        if self.pipeline.isDragging:
            points = self.pipeline.polyData.GetPoints()
            pickPosition = util.getPickPosition(cellPicker, eventPosition, renderer, camera, True, points.GetPoint(0))
            
            self.pipeline.secondSphereActor.SetPosition(pickPosition)
            self.pipeline.secondSphereActor.VisibilityOn()
            
            points.SetPoint(1, pickPosition)
            points.Modified()
            
            idList = vtk.vtkIdList()
            idList.InsertNextId(0)
            idList.InsertNextId(1)
            self.pipeline.polyData.InsertNextCell(vtk.VTK_LINE, idList)

            midPoint = list(map(lambda i,j: (i+j)/2, points.GetPoint(0), points.GetPoint(1)))
            displayCoords = util.convertFromWorldCoords2DisplayCoords(renderer, midPoint)
            euclideDistance = util.getEuclideDistanceBetween2Points(points.GetPoint(0), points.GetPoint(1))
            self.pipeline.showLength.SetInput(f"{round(euclideDistance, 1)}mm")
            self.pipeline.showLength.SetDisplayPosition(round(displayCoords[0]), round(displayCoords[1]))
            self.pipeline.showLength.VisibilityOn()
        else:
            pickPosition = util.getPickPosition(cellPicker, eventPosition, renderer, camera)
            self.pipeline.firstSphereActor.SetPosition(pickPosition)
            self.pipeline.firstSphereActor.VisibilityOn()
        self.GetInteractor().Render()

    def leftButtonDownEvent(self, obj: vtk.vtkInteractorStyleTrackballCamera, event: str) -> None:
        # print("left button down")
        self.pipeline.isDragging = True
        renderer = self.GetInteractor().GetRenderWindow().GetRenderers().GetFirstRenderer()
        camera = renderer.GetActiveCamera()
        eventPosition = self.GetInteractor().GetEventPosition()
        cellPicker = self.GetInteractor().GetPicker()
        pickPosition = util.getPickPosition(cellPicker, eventPosition, renderer, camera)
        
        self.pipeline.firstSphereActor.SetPosition(pickPosition)
        self.pipeline.firstSphereActor.VisibilityOn()

        points = vtk.vtkPoints()
        line = vtk.vtkCellArray()
        self.pipeline.polyData.SetPoints(points)
        self.pipeline.polyData.SetLines(line)

        points.InsertNextPoint(pickPosition)
        points.InsertNextPoint(0, 0, 0) # Set defauld

        self.pipeline.lineActor.VisibilityOn()
        self.OnLeftButtonDown()

    def leftButtonUpEvent(self, obj: vtk.vtkInteractorStyleTrackballCamera, event: str) -> None:
        # print("left button up")
        self.pipeline.isDragging = False
        self.OnLeftButtonUp()

        self.afterMeasureLengthInteractorStyle.addPipeline(self.pipeline)
        self.GetInteractor().SetInteractorStyle(self.afterMeasureLengthInteractorStyle)