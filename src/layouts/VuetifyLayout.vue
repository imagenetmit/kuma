<template>
  <v-app>
    <v-app-bar 
      color="surface" 
      :elevation="2"
      theme="dark"
      class="app-bar"
    >
      <v-app-bar-title>
        <div class="d-flex align-center">
          <v-img 
            alt="Logo" 
            max-height="36" 
            max-width="36" 
            src="/icon.svg" 
            class="mr-2"
          ></v-img>
          <span class="text-h6 font-weight-medium">{{ $root.appName }}</span>
        </div>
      </v-app-bar-title>
      <v-spacer></v-spacer>
      <v-btn 
        icon 
        @click="$root.logout" 
        variant="text"
        color="primary"
        class="logout-btn"
      >
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
export default {
  name: "VuetifyLayout",
};
</script>

<style lang="scss" scoped>
.app-bar {
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  
  &:hover {
    border-bottom-color: rgba(255, 255, 255, 0.1);
  }
}

.logout-btn {
  transition: all 0.2s ease;
  
  &:hover {
    transform: translateY(-1px);
  }
}

:deep(.v-app-bar-title) {
  font-weight: 500;
  letter-spacing: 0.0125em;
}
</style> 