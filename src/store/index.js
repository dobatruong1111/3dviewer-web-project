// import Vue from 'vue';
import Vuex from 'vuex';

import cone from 'dicom3d-web-project/src/store/cone';
import wslink from 'dicom3d-web-project/src/store/wslink';

/* eslint-enable no-param-reassign */

function createStore() {
  return new Vuex.Store({
    modules: {
      cone,
      wslink,
    },
  });
}

export default createStore;
