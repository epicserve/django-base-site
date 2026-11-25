import '../css/app.css';
import { createApp } from 'vue';
import { createRouter } from './router';
import { initAppStore } from './stores/app';
import { startVersionWatcher } from './composables/useVersionWatcher';
import { onUnauthorized } from './utils/api';
import { sessionEnded, signInAgainUrl } from './utils/sessionExpiry';
import App from './App.vue';

const appStore = initAppStore(),
  app = createApp(App),
  router = createRouter(appStore);

appStore.contextReady = appStore.fetchContext().catch(() => {
  appStore.loading = false;
});

let signingInAgain = false;
onUnauthorized((url) => {
  if (signingInAgain || !sessionEnded(url, appStore.isAuthenticated)) return;
  // Requests made at the same time each get a 401, but only the first sends the browser anywhere. A full page load,
  // not a router push, so nothing from the ended session lingers, including any error toast from the failed call.
  signingInAgain = true;
  window.location.assign(signInAgainUrl(router.currentRoute.value.fullPath));
});

app.use(router);
app.mount('#app');

startVersionWatcher(appStore);
