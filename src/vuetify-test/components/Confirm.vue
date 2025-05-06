<template>
    <v-dialog v-model="dialog" max-width="400" theme="dark">
        <v-card>
            <v-card-title class="text-h6">
                <slot></slot>
            </v-card-title>

            <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn color="primary" variant="text" @click="no">
                    {{ noText }}
                </v-btn>
                <v-btn color="primary" variant="flat" @click="yes">
                    {{ yesText }}
                </v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>
</template>

<script>
export default {
    props: {
        yesText: {
            type: String,
            default: "Yes",
        },
        noText: {
            type: String,
            default: "No",
        },
    },
    emits: ["yes"],
    data() {
        return {
            dialog: false,
        };
    },
    methods: {
        show() {
            this.dialog = true;
        },
        yes() {
            this.dialog = false;
            this.$emit("yes");
        },
        no() {
            this.dialog = false;
        },
    },
};
</script> 