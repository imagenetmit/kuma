import { createApp } from 'vue';
import { createRouter, createWebHistory } from 'vue-router';
import { createVuetify } from 'vuetify';
import * as components from 'vuetify/components';
import * as directives from 'vuetify/directives';
import { aliases, mdi } from 'vuetify/iconsets/mdi';
import App from './App.vue';
import Dashboard from './pages/Dashboard.vue';

// Vuetify
import 'vuetify/styles';
import '@mdi/font/css/materialdesignicons.css';

// Create vuetify instance
const vuetify = createVuetify({
  components,
  directives,
  icons: {
    defaultSet: 'mdi',
    aliases,
    sets: {
      mdi,
    },
  },
  theme: {
    defaultTheme: 'dark',
    themes: {
      dark: {
        colors: {
          primary: '#8ab4f8',
          secondary: '#89d4fe',
          accent: '#f08db9',
          error: '#f55b5e',
          info: '#59c8df',
          success: '#5dd879',
          warning: '#ffd454',
          surface: '#1e1e1e',
          background: '#121212',
        },
      },
    },
  },
  defaults: {
    VCard: {
      rounded: 'lg',
    },
    VBtn: {
      rounded: 'lg',
      height: 38,
    },
    VTextField: {
      variant: 'outlined',
      density: 'comfortable',
      color: 'primary',
    },
  },
});

// Create router
const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: Dashboard,
    },
  ],
});

// Create app
const app = createApp(App);

// Use plugins
app.use(vuetify);
app.use(router);

// Mount app
app.mount('#app'); 