<template>
  <div>
    <div :style="depthMargin">
      <v-list-item
        :to="monitorURL(monitor.id)"
        :disabled="!monitor.active"
        link
        class="monitor-item rounded"
        rounded="lg"
        lines="one"
        :active="false"
        :color="monitor.active ? undefined : 'grey-darken-3'"
        density="compact"
      >
        <template v-if="isSelectMode" v-slot:prepend>
          <v-checkbox
            density="compact"
            :model-value="isSelected(monitor.id)"
            @click.stop="toggleSelection"
            hide-details
            color="primary"
          ></v-checkbox>
        </template>
        
        <v-list-item-title class="d-flex align-center monitor-content">
          <div class="d-flex align-center monitor-info">
            <v-icon
              v-if="hasChildren"
              size="small"
              :icon="isCollapsed ? 'mdi-chevron-right' : 'mdi-chevron-down'"
              @click.stop.prevent="changeCollapsed"
              class="mr-2 flex-shrink-0"
              :class="{ 'rotate-icon': !isCollapsed }"
            ></v-icon>
            <span class="monitor-name text-truncate">{{ monitor.name }}</span>
            <v-chip
              v-if="!monitor.active"
              size="x-small"
              color="grey"
              variant="flat"
              class="ml-2 flex-shrink-0"
            >{{ $t("Paused") }}</v-chip>
          </div>
            
          <div v-if="monitor.tags.length > 0" class="tags-container">
            <Tag v-for="tag in monitor.tags.slice(0, 3)" :key="tag" :item="tag" :size="'sm'" class="mr-1" />
            <v-chip v-if="monitor.tags.length > 3" size="x-small" color="grey" variant="flat" class="more-tags">+{{ monitor.tags.length - 3 }}</v-chip>
          </div>
          
          <div class="d-flex align-center gap-3 ml-auto flex-shrink-0">
            <div class="heartbeat-container">
              <HeartbeatBar ref="heartbeatBar" size="small" :monitor-id="monitor.id" />
            </div>
            <div class="uptime-container">
              <Uptime :monitor="monitor" type="24" :pill="true" class="compact-uptime" />
            </div>
          </div>
        </v-list-item-title>
      </v-list-item>
    </div>

    <v-expand-transition>
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
    </v-expand-transition>
  </div>
</template>

<script>
import HeartbeatBar from "./HeartbeatBar.vue";
import Tag from "./Tag.vue";
import Uptime from "./Uptime.vue";
import { getMonitorRelativeURL } from "../util";

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
    userHeartbeatBarValue() {
      console.log("userHeartbeatBar in MonitorListItem:", this.$root.userHeartbeatBar);
      return this.$root.userHeartbeatBar || 'normal';
    }
  },
  watch: {
    isSelectMode() {
      // TODO: Resize the heartbeat bar, but too slow
      // this.$refs.heartbeatBar.resize();
    }
  },
  mounted() {
    console.log("MonitorListItem mounted for monitor:", this.monitor.name);
    console.log("userHeartbeatBar:", this.$root.userHeartbeatBar);
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
    /**
     * Change the collapsed state
     * @returns {void}
     */
    changeCollapsed() {
      this.isCollapsed = !this.isCollapsed;
    },
  },
};
</script>

<style lang="scss" scoped>
@import "../../assets/vars.scss";

.monitor-item {
  min-height: 36px !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid transparent;
  
  &:hover {
    background-color: rgba(255, 255, 255, 0.05);
    border-color: rgba(255, 255, 255, 0.1);
  }

  &:not(:hover) {
    background-color: transparent !important;
  }
}

.monitor-content {
  width: 100%;
  display: flex !important;
  align-items: center !important;
  padding: 2px 0;
}

.monitor-info {
  min-width: 150px;
  max-width: 250px;
  width: 25%;
  flex-shrink: 0;
}

.monitor-name {
  margin: 0;
  font-size: 0.9rem;
  font-weight: 500;
  letter-spacing: 0.0125em;
}

.tags-container {
  display: flex;
  flex-wrap: nowrap;
  overflow: hidden;
  align-items: center;
  flex: 1;
  padding: 0 12px;
}

.more-tags {
  height: 18px !important;
  font-size: 0.7em !important;
}

.heartbeat-container {
  width: 110px;
  min-width: 110px;
  max-width: 110px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 3px;
  border-radius: 4px;
  background-color: rgba(0, 0, 0, 0.2);
}

.rotate-icon {
  transform: rotate(90deg);
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.gap-3 {
  gap: 8px;
}
</style> 