<template>
    <div class="heartbeat-bar" :class="{ 'is-small': size === 'small' }">
        <div 
            v-for="index in 12"
            :key="index"
            class="beat up"
        ></div>
    </div>
</template>

<script>
export default {
    props: {
        monitorId: {
            type: Number,
            required: true,
        },
        size: {
            type: String,
            default: 'normal',
        }
    },
    data() {
        return {};
    },
    mounted() {
        console.log("HeartbeatBar mounted for monitor:", this.monitorId);
    }
};
</script>

<style lang="scss" scoped>
.heartbeat-bar {
    display: flex;
    gap: 2px;
    height: 12px;
    margin: 0;
    padding: 0;
    list-style: none;
    width: 100%;
    min-width: 100px;
    
    &.is-small {
        height: 10px;
        gap: 1px;
    }
}

.beat {
    flex: 1;
    height: 100%;
    background: rgba(200, 200, 200, 0.2);
    border-radius: 2px;
    
    &.up {
        background: #4CAF50;
    }
    
    &.down {
        background: #F44336;
    }
    
    &.pending {
        background: #FFC107;
    }
    
    &.maintenance {
        background: #9E9E9E;
    }
}
</style> 