r"""
    This module is a ParaViewWeb server application.
    The following command line illustrates how to use it::

        $ vtkpython .../server.py

    Any ParaViewWeb executable script comes with a set of standard arguments that can be overrides if need be::

        --port 8080
            Port number on which the HTTP server will listen.

        --content /path-to-web-content/
            Directory that you want to serve as static web content.
            By default, this variable is empty which means that we rely on another
            server to deliver the static content and the current process only
            focuses on the WebSocket connectivity of clients.

        --authKey vtkweb-secret
            Secret key that should be provided by the client to allow it to make
            any WebSocket communication. The client will assume if none is given
            that the server expects "vtkweb-secret" as secret key.

"""
import os
import sys
import argparse

# Try handle virtual env if provided
if '--virtual-env' in sys.argv:
  virtualEnvPath = sys.argv[sys.argv.index('--virtual-env') + 1]
  virtualEnv = virtualEnvPath + '/bin/activate_this.py'
  with open(virtualEnv) as venv:
    exec(venv.read(), dict(__file__=virtualEnv))

# from __future__ import absolute_import, division, print_function

from wslink import server

from vtk.web import wslink as vtk_wslink
from vtk.web import protocols as vtk_protocols

import vtk
from protocol.vtk_protocol import Dicom3D
from protocol.preset_protocol import Preset3D

# =============================================================================
# Server class
# =============================================================================

class _Server(vtk_wslink.ServerProtocol):
    # Defaults
    authKey = "wslink-secret"
    view = None

    @staticmethod
    def add_arguments(parser):
        parser.add_argument("--virtual-env", default=None,
                            help="Path to virtual environment to use")

    @staticmethod
    def configure(args):
        # Standard args
        _Server.authKey = args.authKey

    def initialize(self):
        # Bring used components
        self.registerVtkWebProtocol(vtk_protocols.vtkWebMouseHandler()) # append a list of LinkProtocol
        self.registerVtkWebProtocol(vtk_protocols.vtkWebViewPort()) # append a list of LinkProtocol
        self.registerVtkWebProtocol(vtk_protocols.vtkWebPublishImageDelivery(decode=False)) # append a list of LinkProtocol

        # Custom API
        self.registerVtkWebProtocol(Dicom3D()) # append a list of LinkProtocol
        self.registerVtkWebProtocol(Preset3D())

        # a list of LinkProtocol provide rpc and publish functionality

        # tell the C++ web app to use no encoding.
        # ParaViewWebPublishImageDelivery must be set to decode=False to match.
        self.getApplication().SetImageEncoding(0)

        # Update authentication key to use
        self.updateSecret(_Server.authKey)

        if not _Server.view:
            colors = vtk.vtkNamedColors()
            
            renderer = vtk.vtkRenderer()
            renderer.SetBackground(colors.GetColor3d("White"))
            
            renderWindow = vtk.vtkRenderWindow()
            renderWindow.AddRenderer(renderer)
            renderWindow.OffScreenRenderingOn()

            renderWindowInteractor = vtk.vtkRenderWindowInteractor()
            renderWindowInteractor.SetRenderWindow(renderWindow)
            renderWindowInteractor.GetInteractorStyle().SetCurrentStyleToTrackballCamera()
            renderWindowInteractor.EnableRenderOff()

            # self.getApplication() -> vtkWebApplication()
            self.getApplication().GetObjectIdMap().SetActiveObject("VIEW", renderWindow)
            self.getApplication().GetObjectIdMap().SetActiveObject("INTERACTOR", renderWindowInteractor)

# =============================================================================
# Main: Parse args and start serverviewId
# =============================================================================

if __name__ == "__main__":
    # Create argument parser
    parser = argparse.ArgumentParser(description="Cone example")

    # Add arguments
    server.add_arguments(parser)
    _Server.add_arguments(parser)
    args = parser.parse_args()
    _Server.configure(args)

    # Start server
    server.start_webserver(options=args, protocol=_Server, disableLogging=True)
