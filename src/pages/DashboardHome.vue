<template>
    <transition ref="tableContainer" name="slide-fade" appear>
        <div v-if="$route.name === 'DashboardHome'">
            

            
            <div class="shadow-box table-shadow-box py-2 px-3" style="overflow-x: hidden;">
                <table class="table table-borderless table-hover table-sm">
                    <thead>
                        <tr>
                            <th>{{ $t("Name") }}</th>
                            <th>{{ $t("Status") }}</th>
                            <th>{{ $t("DateTime") }}</th>
                        </tr>
                    </thead>
                    <tbody>
                        <template v-for="(beat, index) in displayedRecords" :key="index">
                            <tr :class="{ 'shadow-box': $root.windowWidth <= 550}">
                                <td class="name-column"><router-link :to="`/dashboard/${beat.monitorID}`">{{ $root.monitorList[beat.monitorID]?.name }}</router-link></td>
                                <td><Status :status="beat.status" /></td>
                                <td><Datetime :value="beat.time" /></td>
                            </tr>
                            <tr v-if="beat.msg" class="message-row">
                                <td colspan="3">{{ beat.msg }}</td>
                            </tr>
                        </template>

                        <tr v-if="importantHeartBeatListLength === 0">
                            <td colspan="3">
                                {{ $t("No important events") }}
                            </td>
                        </tr>
                    </tbody>
                </table>

                <div class="d-flex justify-content-center kuma_pagination">
                    <pagination
                        v-model="page"
                        :records="importantHeartBeatListLength"
                        :per-page="perPage"
                        :options="paginationConfig"
                    />
                </div>
            </div>
        </div>
    </transition>
    <router-view ref="child" />
</template>

<script>
import Status from "../components/Status.vue";
import Datetime from "../components/Datetime.vue";
import Pagination from "v-pagination-3";

export default {
    components: {
        Datetime,
        Status,
        Pagination,
    },
    props: {
        calculatedHeight: {
            type: Number,
            default: 0
        }
    },
    data() {
        return {
            page: 1,
            perPage: 25,
            initialPerPage: 25,
            paginationConfig: {
                hideCount: true,
                chunksNavigation: "scroll",
            },
            importantHeartBeatListLength: 0,
            displayedRecords: [],
        };
    },
    watch: {
        perPage() {
            this.$nextTick(() => {
                this.getImportantHeartbeatListPaged();
            });
        },

        page() {
            this.getImportantHeartbeatListPaged();
        },
    },

    mounted() {
        this.getImportantHeartbeatListLength();

        this.$root.emitter.on("newImportantHeartbeat", this.onNewImportantHeartbeat);

        this.initialPerPage = this.perPage;

        window.addEventListener("resize", this.updatePerPage);
        this.updatePerPage();
    },

    beforeUnmount() {
        this.$root.emitter.off("newImportantHeartbeat", this.onNewImportantHeartbeat);

        window.removeEventListener("resize", this.updatePerPage);
    },

    methods: {
        /**
         * Updates the displayed records when a new important heartbeat arrives.
         * @param {object} heartbeat - The heartbeat object received.
         * @returns {void}
         */
        onNewImportantHeartbeat(heartbeat) {
            if (this.page === 1) {
                this.displayedRecords.unshift(heartbeat);
                if (this.displayedRecords.length > this.perPage) {
                    this.displayedRecords.pop();
                }
                this.importantHeartBeatListLength += 1;
            }
        },

        /**
         * Retrieves the length of the important heartbeat list for all monitors.
         * @returns {void}
         */
        getImportantHeartbeatListLength() {
            this.$root.getSocket().emit("monitorImportantHeartbeatListCount", null, (res) => {
                if (res.ok) {
                    this.importantHeartBeatListLength = res.count;
                    this.getImportantHeartbeatListPaged();
                }
            });
        },

        /**
         * Retrieves the important heartbeat list for the current page.
         * @returns {void}
         */
        getImportantHeartbeatListPaged() {
            const offset = (this.page - 1) * this.perPage;
            this.$root.getSocket().emit("monitorImportantHeartbeatListPaged", null, offset, this.perPage, (res) => {
                if (res.ok) {
                    this.displayedRecords = res.data;
                }
            });
        },

        /**
         * Updates the number of items shown per page based on the available height.
         * @returns {void}
         */
        updatePerPage() {
            const tableContainer = this.$refs.tableContainer;
            const tableContainerHeight = tableContainer.offsetHeight;
            const availableHeight = window.innerHeight - tableContainerHeight;
            const additionalPerPage = Math.floor(availableHeight / 58);

            if (additionalPerPage > 0) {
                this.perPage = Math.max(this.initialPerPage, this.perPage + additionalPerPage);
            } else {
                this.perPage = this.initialPerPage;
            }

        },
    },
};
</script>

<style lang="scss" scoped>
@import "../assets/vars";

.num {
    font-size: 24px;
    line-height: 1.2;
    color: $primary;
    font-weight: bold;
    display: block;
}

.shadow-box {
    padding: 12px;
}

table {
    font-size: 13px;

    th {
        padding: 0.3rem;
        font-size: 12px;
    }

    td {
        padding: 0.3rem;
    }

    tr {
        transition: all ease-in-out 0.2ms;
    }

    .message-row {
        background-color: rgba(0, 0, 0, 0.02);
        font-size: 12px;
        color: #666;
        
        td {
            padding: 0.3rem 0.3rem 0.3rem 1rem;
        }
    }

    @media (max-width: 550px) {
        table-layout: fixed;
        overflow-wrap: break-word;
    }
}

@media screen and (max-width: 1280px) {
    .name-column {
        min-width: 150px;
    }
}

@media screen and (min-aspect-ratio: 4/3) {
    .name-column {
        min-width: 200px;
    }
}
</style>
