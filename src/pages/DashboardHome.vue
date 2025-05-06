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
                
                <div ref="logContainer" class="table shadow-box py-2 px-3" style="overflow-x: hidden; overflow-y: auto;">
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
                            <template v-for="(beat, index) in heartbeatRecords" :key="index">
                                <tr :class="{ 'shadow-box': $root.windowWidth <= 550, 'new-entry': beat.isNew }">
                                    <td class="client-column px-3">{{ getMonitor(beat.monitorID)?.client?.name || '-' }}</td>
                                    <td class="location-column px-3">{{ getMonitor(beat.monitorID)?.location?.name || '-' }}</td>
                                    <td class="status-column px-3"><Status :status="beat.status" /></td>
                                    <td class="datetime-column px-3"><Datetime :value="beat.time" /></td>
                                </tr>
                                <tr v-if="beat.msg" class="message-row px-4">
                                    <td colspan="4">
                                        <router-link :to="`/dashboard/${beat.monitorID}`" class="monitor-name">
                                            {{ getMonitor(beat.monitorID)?.name || '-' }}
                                        </router-link>
                                        {{ beat.msg }}
                                    </td>
                                </tr>
                            </template>

                            <tr v-if="heartbeatRecords.length === 0">
                                <td colspan="4">
                                    {{ $t("No important events") }}
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </transition>
    <router-view ref="child" />
</template>

<script>
import Status from "../components/Status.vue";
import Datetime from "../components/Datetime.vue";

export default {
    components: {
        Datetime,
        Status,
    },
    props: {
        calculatedHeight: {
            type: Number,
            default: 0
        }
    },
    data() {
        return {
            maxRecords: 100, // Maximum number of records to display
            heartbeatRecords: [],
            monitorListLoaded: false,
            autoScroll: true, // Auto scroll is always on
            socketInitialized: false,
        };
    },
    computed: {
        hasMonitorData() {
            return this.$root.monitorList && Object.keys(this.$root.monitorList).length > 0;
        }
    },
    watch: {
        hasMonitorData(newVal) {
            if (newVal && !this.monitorListLoaded) {
                this.monitorListLoaded = true;
                this.getRecentHeartbeats();
            }
        },
        
        heartbeatRecords() {
            this.$nextTick(() => {
                this.scrollToTop();
            });
        },

        // Add route watcher to reload data when returning to dashboard
        '$route'(to) {
            if (to.name === 'DashboardHome') {
                this.getRecentHeartbeats();
            }
        }
    },

    mounted() {
        this.initializeComponent();
    },

    activated() {
        this.initializeComponent();
    },

    beforeUnmount() {
        this.$root.emitter.off("newImportantHeartbeat", this.onNewImportantHeartbeat);
    },

    methods: {
        /**
         * Initialize the component and set up socket events
         */
        initializeComponent() {
            // Ensure socket is initialized before using it
            if (!this.$root.socket.initedSocketIO) {
                this.$root.initSocketIO();
            }
            
            // Only set up socket events once
            if (!this.socketInitialized) {
                this.$root.emitter.on("newImportantHeartbeat", this.onNewImportantHeartbeat);
                this.socketInitialized = true;
            }

            // Ensure monitorList is loaded
            if (!this.hasMonitorData) {
                this.$root.getMonitorList();
            }

            // Always reload heartbeats when component is mounted or activated
            this.getRecentHeartbeats();
        },

        /**
         * Get monitor data by ID
         * @param {number} monitorID - The ID of the monitor to get
         * @returns {object|null} The monitor object or null if not found
         */
        getMonitor(monitorID) {
            return this.$root.monitorList?.[monitorID] || null;
        },

        /**
         * Adds a new heartbeat to the records and handles record limit
         * @param {object} heartbeat - The heartbeat object received
         * @returns {void}
         */
        onNewImportantHeartbeat(heartbeat) {
            // Mark the heartbeat as new for highlighting
            heartbeat.isNew = true;
            
            // Add to beginning of array
            this.heartbeatRecords.unshift(heartbeat);
            
            // Remove highlight after a delay
            setTimeout(() => {
                const index = this.heartbeatRecords.findIndex(beat => beat === heartbeat);
                if (index >= 0) {
                    this.heartbeatRecords[index].isNew = false;
                }
            }, 3000);
            
            // Limit the number of records
            if (this.heartbeatRecords.length > this.maxRecords) {
                this.heartbeatRecords = this.heartbeatRecords.slice(0, this.maxRecords);
            }
        },

        /**
         * Fetches recent heartbeats to initially populate the dynamic log
         * @returns {void}
         */
        getRecentHeartbeats() {
            // Get the most recent heartbeats to populate the log initially
            this.$root.getSocket().emit("monitorImportantHeartbeatListPaged", null, 0, this.maxRecords, (res) => {
                if (res.ok) {
                    // Backend already returns newest first with ORDER BY time DESC
                    this.heartbeatRecords = res.data;
                    
                    this.$nextTick(() => {
                        this.scrollToTop();
                    });
                }
            });
        },
        
        /**
         * Scrolls the log container to the top to show newest entries
         * @returns {void}
         */
        scrollToTop() {
            const container = this.$refs.logContainer;
            if (container) {
                container.scrollTop = 0;
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
        width: 40%;
    }

    .location-column {
        width: 20%;
    }

    .status-column {
        width: 15%;
    }

    .datetime-column {
        width: 25%;
    }

    .datetime-column:not(th) {
        text-align: left;
    }

    tr {
        transition: all ease-in-out 0.2ms;
        border-style: none;
    }
    
    tr.new-entry {
        animation: highlight-new 3s ease-out;
    }

    .message-row {
        background-color: rgba(0, 0, 0, 0.02);
        font-size: 12px;
        color: #666;
        
        td {
            padding: 0rem 0rem 0rem 2rem;
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

@keyframes highlight-new {
    0% {
        background-color: rgba(0, 123, 255, 0.2);
    }
    100% {
        background-color: transparent;
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
