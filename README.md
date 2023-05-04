## 3D Dicom Viewer Project

### Before run the application

You need edit the path to your dicom directory (server/vtkpython/vtk_protocol.py).

### Run the application

```
$ git clone https://github.com/dobatruong1111/3dviewer-web-project.git
```

```
$ cd 3dviewer-web-project
```

```
$ git checkout myproject
```

```
$ npm run build
```

```
$ poetry run python .\server\vtkpython\vtk_server.py --port 1234 --content .\dist\

Open your browser to http://localhost:1234/
```

Or you can live development

```
$ npm run serve & poetry run python .\server\vtkpython\vtk_server.py --port 1234

Open your browser to http://localhost:1234/
```
