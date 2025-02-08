<template>
    <transition name="slide-fade" appear>
        <div class="list-container">
            <MonitorList 
                :scrollbar="true" 
                class="compact-list" 
            />
        </div>
    </transition>
</template>

<script>
import MonitorList from "../components/MonitorList.vue";

export default {
    components: {
        MonitorList,
    },
};
</script>

<style lang="scss" scoped>
@import "../assets/vars";

.list-container {
    padding: 0.5rem;
}

.shadow-box {
    padding: 0.75rem;
}

.compact-list {
    :deep(.monitor-list-item) {
        margin-bottom: 0.5rem;
    }
}
</style>
