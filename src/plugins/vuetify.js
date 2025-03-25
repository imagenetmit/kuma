import { createVuetify } from 'vuetify';
import * as components from 'vuetify/components';
import * as directives from 'vuetify/directives';
import 'vuetify/styles';
import '@mdi/font/css/materialdesignicons.css';

// Create vuetify instance
const vuetify = createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: 'dark',
    themes: {
      light: {
        colors: {
          primary: '#1a73e8',
          secondary: '#5CBBF6',
          accent: '#e83e8c',
          error: '#dc3545',
          info: '#17a2b8',
          success: '#28a745',
          warning: '#ffc107',
        },
      },
      dark: {
        colors: {
          primary: '#8ab4f8',
          secondary: '#89d4fe',
          accent: '#f08db9',
          error: '#f55b5e',
          info: '#59c8df',
          success: '#5dd879',
          warning: '#ffd454',
        },
      },
    },
  },
});

export default vuetify; 