<template>
    <div class="shadow-box mb-2">
        <div class="list-header">
            <div class="header-top py-1 px-2">
                <button class="btn btn-sm btn-outline-normal" :class="{ 'active': selectMode }" type="button" @click="selectMode = !selectMode">
                    {{ $t("Select") }}
                </button>

                <MonitorListFilter :filterState="filterState" @update-filter="updateFilter" />

                <div class="search-wrapper">
                    <a v-if="searchText == ''" class="search-icon">
                        <font-awesome-icon icon="search" size="sm" />
                    </a>
                    <a v-if="searchText != ''" class="search-icon" @click="clearSearchText">
                        <font-awesome-icon icon="times" size="sm" />
                    </a>
                    <form class="compact-form">
                        <input
                            v-model="searchText"
                            class="form-control form-control-sm search-input"
                            :placeholder="$t('Search...')"
                            :aria-label="$t('Search monitored sites')"
                            autocomplete="off"
                        />
                    </form>
                </div>
            </div>

            <!-- Selection Controls -->
            <div v-if="selectMode" class="selection-controls px-2 py-1">
                <input
                    v-model="selectAll"
                    class="form-check-input select-input"
                    type="checkbox"
                />

                <button class="btn btn-sm btn-outline-normal" @click="pauseDialog">
                    <font-awesome-icon icon="pause" size="sm" /> {{ $t("Pause") }}
                </button>
                <button class="btn btn-sm btn-outline-normal" @click="resumeSelected">
                    <font-awesome-icon icon="play" size="sm" /> {{ $t("Resume") }}
                </button>

                <span v-if="selectedMonitorCount > 0" class="small">
                    {{ $t("selectedMonitorCount", [ selectedMonitorCount ]) }}
                </span>
            </div>
            
            <!-- Header Table -->
            <div class="header-table px-2">
                <table class="table table-borderless table-sm mb-0">
                    <thead>
                        <tr>
                            <th v-if="selectMode" class="select-column"></th>
                            <th class="name-column">{{ $t("Name") }}</th>
                            <th class="client-column">{{ $t("Client") }}</th>
                            <th class="location-column">{{ $t("Location") }}</th>
                            <th v-if="$root.userHeartbeatBar == 'normal'" class="heartbeat-column">{{ $t("Heartbeat") }}</th>
                            <th class="uptime-column">{{ $t("Uptime") }}</th>
                        </tr>
                    </thead>
                </table>
            </div>
        </div>
        
        <!-- Content Table with Scrollbar -->
        <div ref="monitorList" class="table shadow-box py-2 px-3" style="overflow-x: hidden; overflow-y: auto;">
            <table class="table table-borderless table-hover table-sm mb-0">
                <thead>
                    <tr>
                        <th v-if="selectMode" class="select-column"></th>
                        <th class="name-column"></th>
                        <th class="client-column"></th>
                        <th class="location-column"></th>
                        <th v-if="$root.userHeartbeatBar == 'normal'" class="heartbeat-column"></th>
                        <th class="uptime-column"></th>
                    </tr>
                </thead>
                <tbody>
                    <template v-if="Object.keys($root.monitorList).length === 0">
                        <tr>
                            <td :colspan="selectMode ? 6 : 5" class="text-center">
                                {{ $t("No Monitors, please") }} <router-link to="/add">{{ $t("add one") }}</router-link>
                            </td>
                        </tr>
                    </template>
                    <template v-else>
                        <MonitorListItem
                            v-for="(item, index) in sortedMonitorList"
                            :key="index"
                            :monitor="item"
                            :isSelectMode="selectMode"
                            :isSelected="isSelected"
                            :select="select"
                            :deselect="deselect"
                            :filter-func="filterFunc"
                            :sort-func="sortFunc"
                        />
                    </template>
                </tbody>
            </table>
        </div>
    </div>

    <Confirm ref="confirmPause" :yes-text="$t('Yes')" :no-text="$t('No')" @yes="pauseSelected">
        {{ $t("pauseMonitorMsg") }}
    </Confirm>
</template>

<script>
import Confirm from "../components/Confirm.vue";
import MonitorListItem from "../components/MonitorListItem.vue";
import MonitorListFilter from "./MonitorListFilter.vue";
import { getMonitorRelativeURL } from "../util.ts";

export default {
    components: {
        Confirm,
        MonitorListItem,
        MonitorListFilter,
    },
    props: {
        /** Should the scrollbar be shown */
        scrollbar: {
            type: Boolean,
        },
    },
    data() {
        return {
            searchText: "",
            selectMode: false,
            selectAll: false,
            disableSelectAllWatcher: false,
            selectedMonitors: {},
            windowTop: 0,
            filterState: {
                status: null,
                active: null,
                tags: null,
            }
        };
    },
    computed: {
        /**
         * Improve the sticky appearance of the list by increasing its
         * height as user scrolls down.
         * Not used on mobile.
         * @returns {object} Style for monitor list
         */
        boxStyle() {
            if (window.innerWidth > 550) {
                return {
                    height: `calc(100vh - 80px + ${this.windowTop}px)`,
                };
            } else {
                return {
                    height: "calc(100vh - 160px)",
                };
            }

        },

        /**
         * Returns a sorted list of monitors based on the applied filters and search text.
         * @returns {Array} The sorted list of monitors.
         */
        sortedMonitorList() {
            let result = Object.values(this.$root.monitorList);

            result = result.filter(monitor => {
                // The root list does not show children
                if (monitor.parent !== null) {
                    return false;
                }
                return true;
            });

            result = result.filter(this.filterFunc);

            result.sort(this.sortFunc);

            return result;
        },

        isDarkTheme() {
            return document.body.classList.contains("dark");
        },

        monitorListStyle() {
            let listHeaderHeight = this.selectMode ? 107 : 65;
            return {
                height: `calc(100% - ${listHeaderHeight}px)`
            };
        },

        selectedMonitorCount() {
            return Object.keys(this.selectedMonitors).length;
        },

        /**
         * Determines if any filters are active.
         * @returns {boolean} True if any filter is active, false otherwise.
         */
        filtersActive() {
            return this.filterState.status != null || this.filterState.active != null || this.filterState.tags != null || this.searchText !== "";
        }
    },
    watch: {
        searchText() {
            for (let monitor of this.sortedMonitorList) {
                if (!this.selectedMonitors[monitor.id]) {
                    if (this.selectAll) {
                        this.disableSelectAllWatcher = true;
                        this.selectAll = false;
                    }
                    break;
                }
            }
        },
        selectAll() {
            if (!this.disableSelectAllWatcher) {
                this.selectedMonitors = {};

                if (this.selectAll) {
                    this.sortedMonitorList.forEach((item) => {
                        this.selectedMonitors[item.id] = true;
                    });
                }
            } else {
                this.disableSelectAllWatcher = false;
            }
        },
        selectMode() {
            if (!this.selectMode) {
                this.selectAll = false;
                this.selectedMonitors = {};
            }
        },
    },
    mounted() {
        window.addEventListener("scroll", this.onScroll);
    },
    beforeUnmount() {
        window.removeEventListener("scroll", this.onScroll);
    },
    methods: {
        /**
         * Handle user scroll
         * @returns {void}
         */
        onScroll() {
            if (window.top.scrollY <= 133) {
                this.windowTop = window.top.scrollY;
            } else {
                this.windowTop = 133;
            }
        },
        /**
         * Get URL of monitor
         * @param {number} id ID of monitor
         * @returns {string} Relative URL of monitor
         */
        monitorURL(id) {
            return getMonitorRelativeURL(id);
        },
        /**
         * Clear the search bar
         * @returns {void}
         */
        clearSearchText() {
            this.searchText = "";
        },
        /**
         * Update the MonitorList Filter
         * @param {object} newFilter Object with new filter
         * @returns {void}
         */
        updateFilter(newFilter) {
            this.filterState = newFilter;
        },
        /**
         * Deselect a monitor
         * @param {number} id ID of monitor
         * @returns {void}
         */
        deselect(id) {
            delete this.selectedMonitors[id];
        },
        /**
         * Select a monitor
         * @param {number} id ID of monitor
         * @returns {void}
         */
        select(id) {
            this.selectedMonitors[id] = true;
        },
        /**
         * Determine if monitor is selected
         * @param {number} id ID of monitor
         * @returns {bool} Is the monitor selected?
         */
        isSelected(id) {
            return id in this.selectedMonitors;
        },
        /**
         * Disable select mode and reset selection
         * @returns {void}
         */
        cancelSelectMode() {
            this.selectMode = false;
            this.selectedMonitors = {};
        },
        /**
         * Show dialog to confirm pause
         * @returns {void}
         */
        pauseDialog() {
            this.$refs.confirmPause.show();
        },
        /**
         * Pause each selected monitor
         * @returns {void}
         */
        pauseSelected() {
            Object.keys(this.selectedMonitors)
                .filter(id => this.$root.monitorList[id].active)
                .forEach(id => this.$root.getSocket().emit("pauseMonitor", id, () => {}));

            this.cancelSelectMode();
        },
        /**
         * Resume each selected monitor
         * @returns {void}
         */
        resumeSelected() {
            Object.keys(this.selectedMonitors)
                .filter(id => !this.$root.monitorList[id].active)
                .forEach(id => this.$root.getSocket().emit("resumeMonitor", id, () => {}));

            this.cancelSelectMode();
        },
        /**
         * Whether a monitor should be displayed based on the filters
         * @param {object} monitor Monitor to check
         * @returns {boolean} Should the monitor be displayed
         */
        filterFunc(monitor) {
            // Group monitors bypass filter if at least 1 of children matched
            if (monitor.type === "group") {
                const children = Object.values(this.$root.monitorList).filter(m => m.parent === monitor.id);
                if (children.some((child, index, children) => this.filterFunc(child))) {
                    return true;
                }
            }

            // filter by search text
            // finds monitor name, tag name or tag value
            let searchTextMatch = true;
            if (this.searchText !== "") {
                const loweredSearchText = this.searchText.toLowerCase();
                searchTextMatch =
                    monitor.name.toLowerCase().includes(loweredSearchText)
                    || monitor.tags.find(tag => tag.name.toLowerCase().includes(loweredSearchText)
                        || tag.value?.toLowerCase().includes(loweredSearchText));
            }

            // filter by status
            let statusMatch = true;
            if (this.filterState.status != null && this.filterState.status.length > 0) {
                if (monitor.id in this.$root.lastHeartbeatList && this.$root.lastHeartbeatList[monitor.id]) {
                    monitor.status = this.$root.lastHeartbeatList[monitor.id].status;
                }
                statusMatch = this.filterState.status.includes(monitor.status);
            }

            // filter by active
            let activeMatch = true;
            if (this.filterState.active != null && this.filterState.active.length > 0) {
                activeMatch = this.filterState.active.includes(monitor.active);
            }

            // filter by tags
            let tagsMatch = true;
            if (this.filterState.tags != null && this.filterState.tags.length > 0) {
                tagsMatch = monitor.tags.map(tag => tag.tag_id) // convert to array of tag IDs
                    .filter(monitorTagId => this.filterState.tags.includes(monitorTagId)) // perform Array Intersaction between filter and monitor's tags
                    .length > 0;
            }

            return searchTextMatch && statusMatch && activeMatch && tagsMatch;
        },
        /**
         * Function used in Array.sort to order monitors in a list.
         * @param {*} m1 monitor 1
         * @param {*} m2 monitor 2
         * @returns {number} -1, 0 or 1
         */
        sortFunc(m1, m2) {
            if (m1.active !== m2.active) {
                if (m1.active === false) {
                    return 1;
                }

                if (m2.active === false) {
                    return -1;
                }
            }

            if (m1.weight !== m2.weight) {
                if (m1.weight > m2.weight) {
                    return -1;
                }

                if (m1.weight < m2.weight) {
                    return 1;
                }
            }

            return m1.name.localeCompare(m2.name);
        }
    },
};
</script>

<style lang="scss" scoped>
@import "../assets/vars.scss";

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

.header-table {
    margin-bottom: 2px;
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
    
    tr {
        transition: all ease-in-out 0.2ms;
        border-style: none;
    }
}

.selection-controls {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 4px 8px;
    margin: 0;
    background-color: rgba(0, 0, 0, 0.02);
    border-top: 1px solid rgba(0, 0, 0, 0.05);
    
    .dark & {
        background-color: $dark-header-bg;
        border-top-color: rgba(255, 255, 255, 0.05);
    }
}

/* Column widths */
.select-column { width: 40px; }
.name-column { width: 25%; }
.client-column { width: 15%; }
.location-column { width: 15%; }
.heartbeat-column { width: 35%; min-width: 300px; }
.uptime-column { 
    width: 8%; 
    min-width: 70px; 
    text-align: left;
}

/* Remove the deep selector since we're aligning left now */
:deep(.uptime-column) {
    text-align: left;
}

.search-wrapper {
    display: flex;
    align-items: center;
    margin-left: auto; /* Push the search to the right */
}

.search-icon {
    padding: 6px;  // Reduced from 10px
    color: #c0c0c0;

    svg[data-icon="times"] {
        cursor: pointer;
        transition: all ease-in-out 0.1s;

        &:hover {
            opacity: 0.5;
        }
    }
}

.search-input {
    max-width: 15em;
    height: 30px;  // Added to make input smaller
    font-size: 0.875rem;  // Added for smaller text
}

.small-padding {
    padding-left: 4px !important;
    padding-right: 4px !important;
}

.px-2 {
    padding: 0 !important;
}

// Adjust for mobile
@media (max-width: 770px) {
    .list-header {
        margin: -12px;  // Reduced from -20px
        margin-bottom: 8px;
        padding: 4px;  // Reduced from 5px
    }
}

.filter-area {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 4px 8px;
    background-color: rgba(0, 0, 0, 0.02);
    border-radius: 4px;
    margin-bottom: 6px;

    .dark & {
        background-color: $dark-header-bg;
    }

    input {
        border: 1px solid rgba(0, 0, 0, 0.1);
        border-radius: 4px;
        padding: 4px 8px;
        font-size: 14px;
        background: transparent;
        
        &:focus {
            outline: none;
            border-color: rgba(0, 0, 0, 0.2);
        }

        .dark & {
            border-color: rgba(255, 255, 255, 0.1);
            color: $dark-font-color;

            &:focus {
                border-color: rgba(255, 255, 255, 0.2);
            }
        }
    }
}

.table > :not(caption) > * > * {
    padding: 0.5rem;
    background-color: transparent;
    border-bottom-width: 0;
    box-shadow: none;
    border: none;
}

.table.shadow-box {
    height: calc(100% - 100px);
    overflow-x: hidden;
    overflow-y: auto;
    
    table {
        thead {
            tr {
                border: none;
            }
            
            th {
                border: none;
                background-color: transparent;
                padding: 0;
                height: 0;
                overflow: hidden;
            }
        }
        
        td {
            border: none;
        }
    }
}

// Override Bootstrap table styles
.table-borderless > :not(caption) > * > * {
    border-bottom-width: 0;
}

// Added compact form styles
.compact-form {
    margin: 0;
    
    input {
        padding: 0.25rem 0.5rem;
    }
}
</style>
