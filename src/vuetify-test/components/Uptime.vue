<template>
    <v-chip
        :color="color"
        :size="pill ? 'x-small' : 'small'"
        :variant="pill ? 'flat' : undefined"
        theme="dark"
        class="uptime"
    >
        {{ uptimeText }}
    </v-chip>
</template>

<script>
export default {
    props: {
        monitor: {
            type: Object,
            required: true,
        },
        type: {
            type: String,
            default: '24',
        },
        pill: {
            type: Boolean,
            default: false,
        },
    },
    data() {
        return {
            uptimeValue: 0,
        };
    },
    computed: {
        uptimeText() {
            return `${(this.uptimeValue * 100).toFixed(2)}%`;
        },
        color() {
            if (this.uptimeValue >= 0.99) {
                return 'success';
            }
            if (this.uptimeValue >= 0.95) {
                return 'warning';
            }
            return 'error';
        },
    },
    mounted() {
        // Listen for uptime updates
        this.$root.getSocket().on('uptime', (monitorId, duration, uptime) => {
            if (monitorId === this.monitor.id && duration === this.type) {
                this.uptimeValue = uptime;
            }
        });
    },
    beforeUnmount() {
        // Clean up socket listener
        this.$root.getSocket().off('uptime');
    },
};
</script>

<style lang="scss" scoped>
.uptime {
    font-weight: 500;
    letter-spacing: 0.0125em;
    min-width: 52px;
    justify-content: center;
}
</style> 