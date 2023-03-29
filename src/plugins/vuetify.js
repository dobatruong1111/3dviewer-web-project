import '@mdi/font/css/materialdesignicons.css';
import Vue from 'vue';
import Vuetify from 'vuetify';

Vue.use(Vuetify, {});

export default new Vuetify({
  icons: {
    iconfont: 'mdi',
    values: {
      resetCamera: 'mdi-camera',
      showBoneCT: 'mdi-bone',
      light: 'mdi-brightness-6',
      logo: 'mdi-cube-outline',
      reset: 'mdi-reload',
    },
  },
});
