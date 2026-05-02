import '../css/app.css';
import { createApp } from 'vue';
import { createRouter } from './router';
import { initAppStore } from './stores/app';
import { startVersionWatcher } from './composables/useVersionWatcher';
import App from './App.vue';

const appStore = initAppStore(),
  app = createApp(App),
  router = createRouter(appStore);

appStore.contextReady = appStore.fetchContext().catch(() => {
  appStore.loading = false;
});

app.provide('appStore', appStore);
app.use(router);
app.mount('#app');

startVersionWatcher(appStore);
