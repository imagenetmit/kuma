<template>
  <v-app>
    <v-app-bar color="surface" :elevation="2" theme="dark" class="app-bar">
      <v-app-bar-title>
        <div class="d-flex align-center">
          <v-img alt="Logo" max-height="36" max-width="36" src="/icon.svg" class="mr-2"></v-img>
          <span class="text-h6 font-weight-medium">Monitor Dashboard</span>
        </div>
      </v-app-bar-title>
      <v-spacer></v-spacer>
      <v-btn icon variant="text" color="primary" @click="logout">
        <v-icon>mdi-logout</v-icon>
      </v-btn>
    </v-app-bar>

    <v-main>
      <v-container fluid class="fill-height pa-0">
        <router-view></router-view>
      </v-container>
    </v-main>
  </v-app>
</template>

<script>
import socketMixin from './mixins/socket';
import themeMixin from './mixins/theme';

export default {
  name: 'App',
  mixins: [socketMixin, themeMixin],
  data() {
    return {
      appName: 'Monitor Dashboard',
      isMobile: false,
    };
  },
  mounted() {
    this.checkMobile();
    window.addEventListener('resize', this.checkMobile);
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.checkMobile);
  },
  methods: {
    logout() {
      // TODO: Implement logout
      console.log('Logout clicked');
    },
    checkMobile() {
      this.isMobile = window.innerWidth < 768;
    },
  },
};
</script>

<style lang="scss">
// Global styles
:root {
  --v-theme-overlay-multiplier: 1;
}

html {
  overflow-y: auto;
}

// Reset default styles
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

// App-specific styles
.app-bar {
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  
  &:hover {
    border-bottom-color: rgba(255, 255, 255, 0.1);
  }
}

// Global Vuetify overrides
:deep(.v-btn) {
  text-transform: none;
  letter-spacing: normal;
  font-weight: 500;
}

:deep(.v-card-title) {
  font-weight: 500;
  letter-spacing: 0.0125em;
}

:deep(.v-toolbar) {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
</style> 