export default function createMethods(session) {
  return {
    createVisualization: () => session.call('vtk.initialize', []),
    resetCamera: () => session.call('vtk.camera.reset', []),
    updateResolution: (resolution) =>
      session.call('vtk.cone.resolution.update', [resolution]),
    showBoneCT: () => session.call('vtk.dicom3d.presets.bone.ct', []),
    showAngioCT: () => session.call('vtk.dicom3d.presets.angio.ct', []),
    showMuscleCT: () => session.call('vtk.dicom3d.presets.muscle.ct', []),
    showMip: () => session.call('vtk.dicom3d.presets.mip', []),
    light: () => session.call('vtk.dicom3d.light', []),
    crop3d: () => session.call('vtk.dicom3d.crop', []),
    measureLength: () => session.call('vtk.dicom3d.measure.length', []),
  };
}
// RPC call
