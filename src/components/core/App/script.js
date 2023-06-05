import { mapGetters, mapActions } from 'vuex';
import logo from 'dicom3d-web-project/src/assets/logo.png';
import RemoteRenderingView from 'dicom3d-web-project/src/components/widgets/RemoteRenderingView';

// ----------------------------------------------------------------------------
// Component API
// ----------------------------------------------------------------------------

export default {
  name: 'App',
  components: {
    RemoteRenderingView,
  },
  data() {
    return {
      logo,
    };
  },
  computed: {
    ...mapGetters({
      client: 'WS_CLIENT',
      busy: 'WS_BUSY',
      resolution: 'CONE_RESOLUTION',
    }),
  },
  methods: {
    ...mapActions({
      resetCamera: 'WS_RESET_CAMERA',
      connect: 'WS_CONNECT',
      showBoneCT: 'WS_SHOW_BONE_CT',
      showAngioCT: 'WS_SHOW_ANGIO_CT',
      showMuscleCT: 'WS_SHOW_MUSCLE_CT',
      showMip: 'WS_SHOW_MIP',
      light: 'WS_LIGHT',
      crop3d: 'WS_CROP3D',
    }),
  },
  mounted() {
    this.connect();
  },
};
