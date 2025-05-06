<template>
  <v-card 
    class="shadow-box mb-2" 
    :style="boxStyle" 
    :elevation="3" 
    rounded="lg" 
    theme="dark"
    :loading="loading"
  >
    <div class="list-header">
      <v-toolbar density="comfortable" color="surface" flat theme="dark" class="px-4 toolbar">
        <v-btn
          size="small"
          variant="outlined"
          :color="selectMode ? 'primary' : undefined"
          @click="selectMode = !selectMode"
          class="mr-3"
          theme="dark"
          density="comfortable"
        >
          <v-icon start size="small">mdi-checkbox-multiple-outline</v-icon>
          {{ $t("Select") }}
        </v-btn>

        <MonitorListFilter :filterState="filterState" @update-filter="updateFilter" />

        <v-spacer></v-spacer>
        
        <v-text-field
          v-model="searchText"
          density="compact"
          variant="outlined"
          hide-details
          :placeholder="$t('Search...')"
          :aria-label="$t('Search monitored sites')"
          prepend-inner-icon="mdi-magnify"
          :append-inner-icon="searchText ? 'mdi-close' : ''"
          @click:append-inner="clearSearchText"
          class="search-input ml-auto"
          style="max-width: 240px;"
          theme="dark"
          bg-color="surface"
        ></v-text-field>
      </v-toolbar>

      <!-- Selection Controls -->
      <v-expand-transition>
        <v-toolbar v-if="selectMode" density="comfortable" color="surface" flat theme="dark" class="px-4 mt-1 toolbar">
          <v-checkbox
            v-model="selectAll"
            density="compact"
            hide-details
            theme="dark"
            color="primary"
          ></v-checkbox>
          
          <v-btn size="small" variant="outlined" class="mx-2" @click="pauseDialog" theme="dark" density="comfortable">
            <v-icon start size="small">mdi-pause</v-icon>
            {{ $t("Pause") }}
          </v-btn>
          <v-btn size="small" variant="outlined" class="mx-2" @click="resumeSelected" theme="dark" density="comfortable">
            <v-icon start size="small">mdi-play</v-icon>
            {{ $t("Resume") }}
          </v-btn>
          
          <v-chip v-if="selectedMonitorCount > 0" size="small" color="primary" variant="flat" class="ml-2" theme="dark">
            {{ $t("selectedMonitorCount", [ selectedMonitorCount ]) }}
          </v-chip>
        </v-toolbar>
      </v-expand-transition>
    </div>
    
    <v-divider v-if="selectMode" class="my-0" color="surface" thickness="thin"></v-divider>
    
    <v-list
      ref="monitorList"
      class="monitor-list pa-2"
      :class="{ scrollbar: scrollbar }"
      :style="monitorListStyle"
      data-testid="monitor-list"
      theme="dark"
      bg-color="background"
      density="compact"
    >
      <v-slide-y-transition group>
        <v-list-item v-if="Object.keys($root.monitorList).length === 0" class="text-center rounded empty-state" theme="dark">
          <v-icon size="48" color="primary" class="mb-4">mdi-monitor-dashboard</v-icon>
          <div class="text-h6 mb-2">{{ $t("No Monitors") }}</div>
          <div class="text-body-2 text-medium-emphasis mb-4">{{ $t("Add your first monitor to get started") }}</div>
          <v-btn color="primary" :to="'/add'" prepend-icon="mdi-plus">
            {{ $t("add one") }}
          </v-btn>
        </v-list-item>

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
      </v-slide-y-transition>
    </v-list>
    
    <Confirm ref="confirmPause" :yes-text="$t('Yes')" :no-text="$t('No')" @yes="pauseSelected">
      {{ $t("pauseMonitorMsg") }}
    </Confirm>
  </v-card>
</template>

<script>
import Confirm from "./Confirm.vue";
import MonitorListItem from "./MonitorListItem.vue";
import MonitorListFilter from "./MonitorListFilter.vue";
import { getMonitorRelativeURL } from "../util";

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
      loading: false,
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
          height: `calc(100vh - 160px + ${this.windowTop}px)`,
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
      let listHeaderHeight = 65;

      if (this.selectMode) {
        listHeaderHeight += 48;
      }

      return {
        "height": `calc(100% - ${listHeaderHeight}px)`
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
@import "../../assets/vars.scss";

.shadow-box {
  height: calc(100vh - 130px);
  position: sticky;
  top: 5px;
  margin: 0;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.05);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  
  &:hover {
    border-color: rgba(255, 255, 255, 0.1);
  }
}

.toolbar {
  border-radius: 0;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.list-header {
  border-bottom: none;
}

.monitor-list {
  display: flex;
  flex-direction: column;
  margin: 0;
  gap: 8px;

  :deep(.v-list-item) {
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    
    &:hover {
      transform: translateX(4px);
      background: rgba(255, 255, 255, 0.05);
    }
  }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 48px 24px;
  border: 2px dashed rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  
  &:hover {
    transform: none !important;
    background: transparent !important;
  }
}

:deep(.v-btn) {
  text-transform: none;
  letter-spacing: normal;
  font-weight: 500;
}

:deep(.v-toolbar) {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.text-primary {
  color: rgb(var(--v-theme-primary)) !important;
  text-decoration: none;
  transition: all 0.2s ease;
  
  &:hover {
    text-decoration: underline;
    opacity: 0.9;
  }
}

:deep(.v-text-field) {
  .v-field__input {
    min-height: 36px;
    padding-top: 0;
    padding-bottom: 0;
  }
}
</style> 