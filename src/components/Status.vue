<template>
    <span
        class="badge status-badge"
        :class="{
            'bg-danger': status === 0,
            'bg-success': status === 1,
            'bg-warning': status === 2,
            'bg-secondary': status === 3,
            'bg-secondary': status === 4
        }"
    >{{ text }}</span>
</template>

<script>
export default {
    props: {
        /** Current status of monitor */
        status: {
            type: Number,
            default: 0,
        }
    },

    computed: {
        text() {
            if (this.status === 0) {
                return this.$t("Down");
            }

            if (this.status === 1) {
                return this.$t("Up");
            }

            if (this.status === 2) {
                return this.$t("Pending");
            }

            if (this.status === 3) {
                return this.$t("statusMaintenance");
            }

            return this.$t("Unknown");
        },
    },
};
</script>

<style scoped>
.status-badge {
    display: inline-flex;
    justify-content: center;
    align-items: center;
    min-width: 60px;
    width: 60px;
    height: 20px;
    padding: 0 8px;
    font-size: 0.75rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
</style>
