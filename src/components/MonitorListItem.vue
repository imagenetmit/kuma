<template>
    <div>
        <div :style="depthMargin">
            <!-- Checkbox -->
            <div v-if="isSelectMode" class="select-input-wrapper">
                <input
                    class="form-check-input select-input form-check-input-sm"
                    type="checkbox"
                    :aria-label="$t('Check/Uncheck')"
                    :checked="isSelected(monitor.id)"
                    @click.stop="toggleSelection"
                />
            </div>

            <router-link :to="monitorURL(monitor.id)" class="item compact-item" :class="{ 'disabled': ! monitor.active }">
                <div class="row g-1">
                    <div class="col-8 col-md-7 small-padding" :class="{ 'monitor-item': $root.userHeartbeatBar == 'bottom' || $root.userHeartbeatBar == 'none' }">
                        <div class="info">
                            
                            <span v-if="hasChildren" class="collapse-padding" @click.prevent="changeCollapsed">
                                <font-awesome-icon icon="chevron-down" class="animated" :class="{ collapsed: isCollapsed}" size="sm" />
                            </span>
                            <span class="monitor-name">{{ monitor.name }}</span>
                        </div>
                        <div v-if="monitor.tags.length > 0" class="tags">
                            <Tag v-for="tag in monitor.tags" :key="tag" :item="tag" :size="'sm'" class="compact-tag" />
                        </div>
                    </div>
                    <div v-show="$root.userHeartbeatBar == 'normal'" :key="$root.userHeartbeatBar" class="col-3 col-md-4 pe-3">
                        <HeartbeatBar ref="heartbeatBar" size="small" :monitor-id="monitor.id" />
                    </div>
                    <div class="col-1 col-md-1uptime-pill-container">
                        <Uptime :monitor="monitor" type="24" :pill="true" class="compact-uptime" />
                    </div>
                </div>

                <div v-if="$root.userHeartbeatBar == 'bottom'" class="row g-1">
                    <div class="col-12 bottom-style">
                        <HeartbeatBar ref="heartbeatBar" size="small" :monitor-id="monitor.id" />
                    </div>
                </div>
            </router-link>
        </div>

        <transition name="slide-fade-up">
            <div v-if="!isCollapsed" class="childs">
                <MonitorListItem
                    v-for="(item, index) in sortedChildMonitorList"
                    :key="index"
                    :monitor="item"
                    :isSelectMode="isSelectMode"
                    :isSelected="isSelected"
                    :select="select"
                    :deselect="deselect"
                    :depth="depth + 1"
                    :filter-func="filterFunc"
                    :sort-func="sortFunc"
                />
            </div>
        </transition>
    </div>
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
}

.monitor-name {
    margin: 0;
    // padding: 0 2px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
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
</style>
