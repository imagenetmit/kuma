<template>
    <template v-for="(item, index) in [monitor, ...sortedChildMonitorList]" :key="index">
        <tr :class="{ 'child-row': item !== monitor }" :style="item !== monitor ? depthMargin : {}">
            <!-- Select Column -->
            <td v-if="isSelectMode" class="select-column">
                <input
                    v-if="item === monitor"
                    class="form-check-input select-input form-check-input-sm"
                    type="checkbox"
                    :aria-label="$t('Check/Uncheck')"
                    :checked="isSelected(item.id)"
                    @click.stop="toggleSelection"
                />
            </td>

            <!-- Name Column -->
            <td class="name-column">
                <div class="d-flex align-items-center">
                    <span v-if="item === monitor && hasChildren" class="collapse-padding me-2" @click.prevent="changeCollapsed">
                        <font-awesome-icon icon="chevron-down" class="animated" :class="{ collapsed: isCollapsed}" size="sm" />
                    </span>
                    <router-link :to="monitorURL(item.id)" class="monitor-name" :class="{ 'disabled': !item.active }">
                        {{ item.name }}
                    </router-link>
                </div>
                <div v-if="item.tags.length > 0" class="tags">
                    <Tag v-for="tag in item.tags" :key="tag" :item="tag" :size="'sm'" class="compact-tag" />
                </div>
            </td>

            <!-- Client Column -->
            <td class="client-column">
                <span v-if="item.client" class="client-info" :title="'Client: ' + item.client.name">
                    {{ item.client.name }}
                </span>
            </td>

            <!-- Location Column -->
            <td class="location-column">
                <span v-if="item.location" class="location-info" :title="'Location: ' + item.location.name">
                    {{ item.location.name }}
                </span>
            </td>

            <!-- Heartbeat Column -->
            <td v-if="$root.userHeartbeatBar == 'normal'" class="heartbeat-column">
                <HeartbeatBar ref="heartbeatBar" size="small" :monitor-id="item.id" />
            </td>

            <!-- Uptime Column -->
            <td class="uptime-column">
                <Uptime :monitor="item" type="24" :pill="true" class="compact-uptime" />
            </td>
        </tr>

        <!-- Bottom Heartbeat Bar Row -->
        <tr v-if="item === monitor && $root.userHeartbeatBar == 'bottom'" class="bottom-heartbeat-row">
            <td :colspan="isSelectMode ? 6 : 5">
                <HeartbeatBar ref="heartbeatBar" size="small" :monitor-id="item.id" />
            </td>
        </tr>
    </template>

    <!-- Child Items -->
    <template v-if="!isCollapsed">
        <MonitorListItem
            v-for="(childItem, index) in sortedChildMonitorList"
            :key="'child-' + index"
            :monitor="childItem"
            :isSelectMode="isSelectMode"
            :isSelected="isSelected"
            :select="select"
            :deselect="deselect"
            :depth="depth + 1"
            :filter-func="filterFunc"
            :sort-func="sortFunc"
        />
    </template>
</template>

<script>
import HeartbeatBar from "../components/HeartbeatBar.vue";
import Tag from "../components/Tag.vue";
import Uptime from "../components/Uptime.vue";
import { getMonitorRelativeURL } from "../util.ts";

export default {
    name: "MonitorListItem",
    components: {
        Uptime,
        HeartbeatBar,
        Tag,
    },
    props: {
        /** Monitor this represents */
        monitor: {
            type: Object,
            default: null,
        },
        /** If the user is in select mode */
        isSelectMode: {
            type: Boolean,
            default: false,
        },
        /** How many ancestors are above this monitor */
        depth: {
            type: Number,
            default: 0,
        },
        /** Callback to determine if monitor is selected */
        isSelected: {
            type: Function,
            default: () => {}
        },
        /** Callback fired when monitor is selected */
        select: {
            type: Function,
            default: () => {}
        },
        /** Callback fired when monitor is deselected */
        deselect: {
            type: Function,
            default: () => {}
        },
        /** Function to filter child monitors */
        filterFunc: {
            type: Function,
            default: () => {}
        },
        /** Function to sort child monitors */
        sortFunc: {
            type: Function,
            default: () => {},
        }
    },
    data() {
        return {
            isCollapsed: false,
        };
    },
    computed: {
        sortedChildMonitorList() {
            let result = Object.values(this.$root.monitorList);

            // Get children
            result = result.filter(childMonitor => childMonitor.parent === this.monitor.id);

            // Run filter on children
            result = result.filter(this.filterFunc);

            result.sort(this.sortFunc);

            return result;
        },
        hasChildren() {
            return this.sortedChildMonitorList.length > 0;
        },
        depthMargin() {
            return {
                marginLeft: `${20 * this.depth}px`,
            };
        },
    },
    watch: {
        isSelectMode() {
            // TODO: Resize the heartbeat bar, but too slow
            // this.$refs.heartbeatBar.resize();
        }
    },
    methods: {
        /**
         * Get URL of monitor
         * @param {number} id ID of monitor
         * @returns {string} Relative URL of monitor
         */
        monitorURL(id) {
            return getMonitorRelativeURL(id);
        },
        /**
         * Toggle selection of monitor
         * @returns {void}
         */
        toggleSelection() {
            if (this.isSelected(this.monitor.id)) {
                this.deselect(this.monitor.id);
            } else {
                this.select(this.monitor.id);
            }
        },
    },
};
</script>

<style lang="scss" scoped>
@import "../assets/vars.scss";

.child-row {
    background-color: rgba(0, 0, 0, 0.01) !important;
}

.bottom-heartbeat-row {
    background-color: rgba(0, 0, 0, 0.01);
    
    td {
        padding: 0.25rem 0.5rem;
    }
}

.monitor-name {
    color: inherit;
    text-decoration: none;
    font-weight: 500;
    
    &:hover {
        text-decoration: underline;
    }
    
    &.disabled {
        opacity: 0.6;
    }
}

.tags {
    margin-top: 0.25rem;
    display: flex;
    flex-wrap: wrap;
    gap: 0.25rem;
}

.uptime-column {
    text-align: left;
}

td.uptime-column {
    text-align: left;
    padding-right: 0 !important;
}

.compact-uptime {
    display: inline-block;
}

/* Remove all duplicate and conflicting styles */
.uptime-wrapper {
    display: none;
}

.select-input {
    margin: 0;
}

td {
    padding: 0.5rem !important;
}

.small-padding {
    padding: 0 1px !important;
}

.tags {
    margin: 0;
    padding-left: 20px;
    display: flex;
    flex-wrap: wrap;
    gap: 1px;
}

.select-input-wrapper {
    float: left;
    margin: 1px;
    padding: 0;
    position: relative;
    z-index: 15;
}

.compact-item {
    display: block;
    // padding: 1px 1px;
    text-decoration: none;
    color: inherit;
    margin: 0;
    
    &:hover {
        background-color: rgba(0, 0, 0, 0.03);
    }

    &.disabled {
        opacity: 0.6;
    }
}

.info {
    display: flex;
    align-items: center;
    font-size: 1rem;
    gap: 0;
    padding: 0;
    margin: 0;
    width: 100%;
    overflow: hidden;
}

.monitor-name {
    margin: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    flex: 1;
    min-width: 0; /* Allows flex item to shrink below its content size */
}

.compact-uptime {
    :deep(.badge) {
        padding: 0.2em 0.4em;
        font-size: 0.75em;
    }
}

.compact-tag {
    :deep(.badge) {
        padding: 0.2em 0.4em;
        font-size: 0.7em;
    }
}

.item {
    display: flex !important;  // Override block display
    flex-direction: column;
    margin: 0;
}

.row {
    --bs-gutter-x: 0;
    --bs-gutter-y: 0;  
    margin: 0 4px 0 0;
    padding: 0 4px 0 0;
    display: flex;
    align-items: center;
}

.col-9, .col-md-8, .col-3, .col-md-4 {
    padding: 0 4px;
}

.col-3, .col-md-4 {
    margin-left: auto;  // Push to right
}

/* New styling for the uptime pill container */
.uptime-pill-container {
    display: flex;
    align-items: flex-end;
    justify-content: flex-end; /* Align to the right of its column */
    padding-right: 5px;
    font-size: 0.8rem;
}

.heartbeat-bar-container {
    padding-right: 0;
    align-items: flex-end;
    justify-content: flex-end;
    
}

/* Make the uptime badge more compact if needed */
.compact-uptime :deep(.badge) {
    min-width: 50px;  /* Reduce minimum width */
    padding: 0.2em 0.35em;
    font-size: 0.7em;
    background-color: #28a745;  /* Bootstrap's success green */
    color: white;
}

.debug-grid {
    .row {
        background-color: rgba(255, 0, 0, 0.1);  /* Light red */
        border: 1px dashed red;
    }

    .col-9, .col-md-8, .col-6, .col-md-4, .col-1, .col-md-1 {
        background-color: rgba(0, 0, 255, 0.1);  /* Light blue */
        border: 1px solid blue;
    }

    .uptime-pill-container {
        background-color: rgba(0, 255, 0, 0.1);  /* Light green */
        border: 1px solid green;
    }
}

.client-info, .location-info, .type-info {
    font-size: 0.8rem;
    color: #666;
    margin-left: 4px;
    display: inline-flex;
    align-items: center;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    width: 120px; /* Fixed width for both client and location */
    flex-shrink: 0; /* Prevent shrinking */
}

.dark {
    .client-info, .location-info {
        color: #999;
    }
}

.monitor-name {
    color: inherit;
    text-decoration: none;
    
    &:hover {
        text-decoration: underline;
    }
    
    &.disabled {
        opacity: 0.6;
    }
}

.tags {
    margin-top: 0.25rem;
    display: flex;
    flex-wrap: wrap;
    gap: 0.25rem;
}

.uptime-column {
    text-align: right;
    
    .d-flex {
        justify-content: flex-end;
        width: 100%;
    }
}
</style>
