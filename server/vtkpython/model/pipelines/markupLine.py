import vtk

class MarkupLinePipeline():
    def __init__(self) -> None:
        colors = vtk.vtkNamedColors()
        self.isDragging = False
        self.polyData = vtk.vtkPolyData()

        self.tubeFilter = vtk.vtkTubeFilter()
        self.tubeFilter.SetInputData(self.polyData)
        self.tubeFilter.SetNumberOfSides(20)
        self.tubeFilter.SetRadius(2)

        self.mapper = vtk.vtkPolyDataMapper()
        self.mapper.SetInputConnection(self.tubeFilter.GetOutputPort())
        
        self.actor = vtk.vtkActor()
        self.actor.SetMapper(self.mapper)
        self.actor.GetProperty().SetColor(colors.GetColor3d("Tomato"))
        self.actor.GetProperty().SetLineWidth(3)
        self.actor.VisibilityOff()

        # show the length of two points in world coordinates
        self.showLength =  vtk.vtkTextActor3D()
        self.showLength.GetTextProperty().SetColor(colors.GetColor3d("Tomato"))
        self.showLength.GetTextProperty().BoldOn()
        self.showLength.GetTextProperty().SetFontSize(16)
        self.showLength.GetTextProperty().SetOpacity(1)
        self.showLength.GetTextProperty().FrameOn()
        self.showLength.VisibilityOff()

        # Draw/update the pick marker
        self.firstSphere = vtk.vtkSphereSource()
        self.firstSphere.SetRadius(5)

        self.firstSphereMapper = vtk.vtkPolyDataMapper()
        self.firstSphereMapper.SetInputConnection(self.firstSphere.GetOutputPort())

        self.firstSphereActor = vtk.vtkActor()
        self.firstSphereActor.GetProperty().SetColor(1, 0, 0)
        self.firstSphereActor.SetMapper(self.firstSphereMapper)
        self.firstSphereActor.VisibilityOff()
        # ---
        self.secondSphere = vtk.vtkSphereSource()
        self.secondSphere.SetRadius(5)

        self.secondSphereMapper = vtk.vtkPolyDataMapper()
        self.secondSphereMapper.SetInputConnection(self.secondSphere.GetOutputPort())

        self.secondSphereActor = vtk.vtkActor()
        self.secondSphereActor.GetProperty().SetColor(1, 0, 0)
        self.secondSphereActor.SetMapper(self.secondSphereMapper)
        self.secondSphereActor.VisibilityOff()