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
                    <div class="col-9 col-md-8 small-padding" :class="{ 'monitor-item': $root.userHeartbeatBar == 'bottom' || $root.userHeartbeatBar == 'none' }">
                        <div class="info">
                            <Uptime :monitor="monitor" type="24" :pill="true" class="compact-uptime" />
                            <span v-if="hasChildren" class="collapse-padding" @click.prevent="changeCollapsed">
                                <font-awesome-icon icon="chevron-down" class="animated" :class="{ collapsed: isCollapsed}" size="sm" />
                            </span>
                            <span class="monitor-name">{{ monitor.name }}</span>
                        </div>
                        <div v-if="monitor.tags.length > 0" class="tags">
                            <Tag v-for="tag in monitor.tags" :key="tag" :item="tag" :size="'sm'" class="compact-tag" />
                        </div>
                    </div>
                    <div v-show="$root.userHeartbeatBar == 'normal'" :key="$root.userHeartbeatBar" class="col-3 col-md-4 pe-2">
                        <HeartbeatBar ref="heartbeatBar" size="small" :monitor-id="monitor.id" />
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
            isCollapsed: true,
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
    beforeMount() {

        // Always unfold if monitor is accessed directly
        if (this.monitor.childrenIDs.includes(parseInt(this.$route.params.id))) {
            this.isCollapsed = false;
            return;
        }

        // Set collapsed value based on local storage
        let storage = window.localStorage.getItem("monitorCollapsed");
        if (storage === null) {
            return;
        }

        let storageObject = JSON.parse(storage);
        if (storageObject[`monitor_${this.monitor.id}`] == null) {
            return;
        }

        this.isCollapsed = storageObject[`monitor_${this.monitor.id}`];
    },
    methods: {
        /**
         * Changes the collapsed value of the current monitor and saves
         * it to local storage
         * @returns {void}
         */
        changeCollapsed() {
            this.isCollapsed = !this.isCollapsed;

            // Save collapsed value into local storage
            let storage = window.localStorage.getItem("monitorCollapsed");
            let storageObject = {};
            if (storage !== null) {
                storageObject = JSON.parse(storage);
            }
            storageObject[`monitor_${this.monitor.id}`] = this.isCollapsed;

            window.localStorage.setItem("monitorCollapsed", JSON.stringify(storageObject));
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

.collapse-padding {
    padding: 0 1px !important;
}

.tags {
    margin: 0;
    padding-left: 20px;
    display: flex;
    flex-wrap: wrap;
    gap: 1px;
}

.collapsed {
    transform: rotate(-90deg);
}

.animated {
    transition: all 0.15s $easing-in;
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
    padding: 1px 2px;
    text-decoration: none;
    color: inherit;
    //border-radius: 1px;
    margin: 0;
    
    &:hover {
        background-color: rgba(0, 0, 0, 0.03);
        outline: 1px rgb(26, 41, 20);  /* Debug outline */
    }

    &.disabled {
        opacity: 0.6;
    }
}

.info {
    display: flex;
    align-items: center;
    font-size: 0.9rem;
    gap: 10px;
    padding: 0;
    margin: 0;
}

.monitor-name {
    //outline: 1px dashed purple;  /* Debug outline */
    margin: 0;
    padding: 0 2px;
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
    //outline: 2px solid green;  /* Debug outline */
    //background: rgba(0, 255, 0, 0.05);  /* Light green background */
    display: flex !important;  // Override block display
    flex-direction: column;
    //padding: 0 !important;
    margin: 0;
}

.row {
    //outline: 1px dashed purple;  /* Debug outline */
    //background: rgba(128, 0, 128, 0.05);  /* Light purple background */
    --bs-gutter-x: 0;
    --bs-gutter-y: 0;  //this was the bastard that was causing the issue
    margin: 0;
    padding: 0;
    display: flex;
    align-items: center;
}

.col-9, .col-md-8, .col-3, .col-md-4 {
    padding: 0;
    //width: auto;  // Let content determine width
    //flex: 0 0 auto;  // Don't grow or shrink
}

.col-3, .col-md-4 {
    margin-left: auto;  // Push to right
}

.compact-item {
    padding: 1px !important;
    text-decoration: none;
    color: inherit;
    margin: 0;
    //line-height: 1;
    
    &:hover {
        background-color: rgba(0, 0, 0, 0.473);
        //outline: 1px rgb(26, 41, 20);  /* Debug outline */
    }

    &.disabled {
        opacity: 0.6;
    }
}

</style>
