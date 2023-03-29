import Vue from 'vue';
import Vuex from 'vuex';

import App from 'dicom3d-web-project/src/components/core/App';
import vuetify from 'dicom3d-web-project/src/plugins/vuetify.js';
import store from 'dicom3d-web-project/src/store';

import 'typeface-roboto';
import 'vuetify/dist/vuetify.min.css';

Vue.use(Vuex);

new Vue({
  vuetify,
  store,
  render: (h) => h(App),
}).$mount('#app');
