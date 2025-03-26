<template>
    <transition ref="tableContainer" name="slide-fade" appear>
        <div v-if="$route.name === 'DashboardHome'">
            <div class="shadow-box mb-2">
                <div class="list-header">
                    <div class="header-top py-1 px-2">
                        <table class="table table-borderless table-sm mb-0">
                            <thead>
                                <tr>
                                    <th class="client-column">{{ $t("Client") }}</th>
                                    <th class="location-column">{{ $t("Location") }}</th>
                                    <th class="status-column">{{ $t("Status") }}</th>
                                    <th class="datetime-column">{{ $t("DateTime") }}</th>
                                </tr>
                            </thead>
                        </table>
                    </div>
                </div>
                
                <div class="table-shadow-box py-2 px-3" style="overflow-x: hidden;">
                    <table class="table table-borderless table-hover table-sm">
                        <thead>
                            <tr>
                                <th class="client-column"></th>
                                <th class="location-column"></th>
                                <th class="status-column"></th>
                                <th class="datetime-column"></th>
                            </tr>
                        </thead>
                        <tbody>
                            <template v-for="(beat, index) in displayedRecords" :key="index">
                                <tr :class="{ 'shadow-box': $root.windowWidth <= 550}">
                                    <td class="client-column">{{ getMonitor(beat.monitorID)?.client?.name || '-' }}</td>
                                    <td class="location-column">{{ getMonitor(beat.monitorID)?.location?.name || '-' }}</td>
                                    <td class="status-column"><Status :status="beat.status" /></td>
                                    <td class="datetime-column"><Datetime :value="beat.time" /></td>
                                </tr>
                                <tr v-if="beat.msg" class="message-row">
                                    <td colspan="4">
                                        <router-link :to="`/dashboard/${beat.monitorID}`" class="monitor-name">
                                            {{ getMonitor(beat.monitorID)?.name || '-' }}
                                        </router-link>
                                        {{ beat.msg }}
                                    </td>
                                </tr>
                            </template>

                            <tr v-if="importantHeartBeatListLength === 0">
                                <td colspan="4">
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
            monitorListLoaded: false,
        };
    },
    computed: {
        hasMonitorData() {
            return this.$root.monitorList && Object.keys(this.$root.monitorList).length > 0;
        }
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

        hasMonitorData(newVal) {
            if (newVal && !this.monitorListLoaded) {
                this.monitorListLoaded = true;
                this.getImportantHeartbeatListLength();
            }
        }
    },

    mounted() {
        // Ensure socket is initialized before using it
        if (!this.$root.socket.initedSocketIO) {
            this.$root.initSocketIO();
        }
        
        this.$root.emitter.on("newImportantHeartbeat", this.onNewImportantHeartbeat);
        this.initialPerPage = this.perPage;
        window.addEventListener("resize", this.updatePerPage);
        this.updatePerPage();

        // Ensure monitorList is loaded
        if (!this.hasMonitorData) {
            this.$root.getMonitorList();
        }
    },

    beforeUnmount() {
        this.$root.emitter.off("newImportantHeartbeat", this.onNewImportantHeartbeat);

        window.removeEventListener("resize", this.updatePerPage);
    },

    methods: {
        /**
         * Get monitor data by ID
         * @param {number} monitorID - The ID of the monitor to get
         * @returns {object|null} The monitor object or null if not found
         */
        getMonitor(monitorID) {
            return this.$root.monitorList?.[monitorID] || null;
        },

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

.shadow-box {
    height: calc(100vh - 130px);
    position: sticky;
    top: 5px;
    padding: 0 !important;
    margin: 0;
}

.list-header {
    border-bottom: 1px solid #dee2e6;
    border-radius: 4px 4px 0 0;
    margin: 0 0 6px 0;
    padding: 4px 4px 2px 4px;

    .dark & {
        background-color: $dark-header-bg;
        border-bottom: 0;
    }
}

.header-top {
    padding: 2px;
    margin: 0;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
}

table {
    font-size: 13px;
    width: 100%;
    table-layout: fixed;

    th, td {
        padding: 0.3rem;
        font-size: 12px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    th {
        text-align: left;
        font-weight: normal;
        color: inherit;
    }

    .client-column {
        width: 45%;
    }

    .location-column {
        width: 20%;
    }

    .status-column {
        width: 15%;
    }

    .datetime-column {
        width: 20%;
    }

    .datetime-column:not(th) {
        text-align: left;
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

        .monitor-name {
            color: $primary;
            text-decoration: none;
            margin-right: 8px;
            font-weight: 500;

            &:hover {
                text-decoration: underline;
            }
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

// Adjust for mobile
@media (max-width: 770px) {
    .list-header {
        margin: -12px;
        margin-bottom: 8px;
        padding: 4px;
    }
}
</style>
