<template>
    <v-chip
        :color="color"
        size="small"
        class="status-chip"
        theme="dark"
        density="compact"
    >{{ text }}</v-chip>
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
        color() {
            if (this.status === 0) {
                return "error";
            }

            if (this.status === 1) {
                return "success";
            }

            if (this.status === 2) {
                return "warning";
            }

            if (this.status === 3) {
                return "grey";
            }

            return "secondary";
        },

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
.status-chip {
    justify-content: center;
    min-width: 50px;
    text-align: center;
    height: 20px !important;
    padding: 0 8px !important;
}
</style>
