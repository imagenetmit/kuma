<template>
    <div class="container-fluid px-2">
        <div class="row g-2">
            <div v-if="!$root.isMobile" class="col-12 col-md-5 col-xl-4">
                
                <MonitorList :scrollbar="true" />
            </div>

            <div ref="container" class="col-12 col-md-7 col-xl-8 mb-2">
                <router-view :key="$route.fullPath" :calculatedHeight="height" />
            </div>
        </div>
    </div>
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
        this.height = this.$refs.container.offsetHeight;
    },
};
</script>

<style lang="scss" scoped>
.container-fluid {
    width: 99%;
    max-width: 2000px;
}
</style>
