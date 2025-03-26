<template>
    <div>
        <router-view />
        <div v-if="$root.isLoadingData" class="loading-overlay">
            <div class="loading-content">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <div class="mt-3">{{ $t("Loading your data...") }}</div>
            </div>
        </div>
    </div>
</template>

<script>
import { setPageLocale } from "./util-frontend";
export default {
    created() {
        setPageLocale();
    },
};
</script>

<style lang="scss">
.loading-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(255, 255, 255, 0.9);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9999;
}

.loading-content {
    text-align: center;
}
</style>
