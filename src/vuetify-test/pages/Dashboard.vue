<template>
  <v-container fluid>
    <v-row dense>
      <v-col v-if="!$root.isMobile" cols="12" md="8" xl="8">
        <MonitorList :scrollbar="true" />
      </v-col>
      <v-col ref="container" cols="12" md="4" xl="4" class="mb-2">
        <router-view :key="$route.fullPath" :calculatedHeight="height" />
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import MonitorList from "../components/MonitorList.vue";

export default {
  components: {
    MonitorList,
  },
  data() {
    return {
      height: 0
    };
  },
  mounted() {
    this.height = this.$refs.container?.offsetHeight || 0;
  },
};
</script> 