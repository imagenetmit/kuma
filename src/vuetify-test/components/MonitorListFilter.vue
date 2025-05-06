<template>
  <div class="d-flex align-center filter-container">
    <v-btn
      size="small"
      variant="outlined"
      :color="numFiltersActive > 0 ? 'primary' : undefined"
      :disabled="numFiltersActive === 0"
      @click="clearFilters"
      class="mr-3"
      density="comfortable"
      theme="dark"
    >
      <v-badge
        v-if="numFiltersActive > 0"
        :content="numFiltersActive"
        color="primary"
        floating
        offset-x="12"
        offset-y="-8"
        theme="dark"
      ></v-badge>
      <v-icon start>mdi-filter-variant</v-icon>
      {{ $t('Filters') }}
      <v-icon v-if="numFiltersActive > 0" end>mdi-close</v-icon>
    </v-btn>

    <!-- Status Filter -->
    <v-menu
      min-width="240"
      theme="dark"
      transition="slide-y-transition"
      :close-on-content-click="false"
    >
      <template v-slot:activator="{ props }">
        <v-btn
          size="small"
          variant="outlined"
          :color="filterState.status?.length > 0 ? 'primary' : undefined"
          class="mr-3"
          v-bind="props"
          density="comfortable"
          theme="dark"
        >
          <template v-if="filterState.status?.length === 1">
            <Status v-if="filterState.status?.length === 1" :status="filterState.status[0]" />
          </template>
          <template v-else>
            <v-icon start>mdi-information-outline</v-icon>
            {{ $t('Status') }}
          </template>
        </v-btn>
      </template>
      
      <v-card theme="dark" elevation="3" class="filter-menu">
        <v-card-title class="text-subtitle-1 px-4 py-2">{{ $t('Filter by Status') }}</v-card-title>
        <v-divider></v-divider>
        <v-list density="comfortable" theme="dark" class="py-2">
          <v-list-item @click="toggleStatusFilter(1)" theme="dark" class="px-4">
            <v-list-item-title class="d-flex justify-space-between align-center">
              <Status :status="1" />
              <div class="d-flex align-center">
                {{ $root.stats.up }}
                <v-icon v-if="filterState.status?.includes(1)" class="ml-2" size="small" color="primary">mdi-check</v-icon>
              </div>
            </v-list-item-title>
          </v-list-item>
          
          <v-list-item @click="toggleStatusFilter(0)" theme="dark" class="px-4">
            <v-list-item-title class="d-flex justify-space-between align-center">
              <Status :status="0" />
              <div class="d-flex align-center">
                {{ $root.stats.down }}
                <v-icon v-if="filterState.status?.includes(0)" class="ml-2" size="small" color="primary">mdi-check</v-icon>
              </div>
            </v-list-item-title>
          </v-list-item>
          
          <v-list-item @click="toggleStatusFilter(2)" theme="dark" class="px-4">
            <v-list-item-title class="d-flex justify-space-between align-center">
              <Status :status="2" />
              <div class="d-flex align-center">
                {{ $root.stats.pending }}
                <v-icon v-if="filterState.status?.includes(2)" class="ml-2" size="small" color="primary">mdi-check</v-icon>
              </div>
            </v-list-item-title>
          </v-list-item>
        </v-list>
      </v-card>
    </v-menu>

    <!-- Active Filter -->
    <v-menu
      min-width="240"
      theme="dark"
      transition="slide-y-transition"
      :close-on-content-click="false"
    >
      <template v-slot:activator="{ props }">
        <v-btn
          size="small"
          variant="outlined"
          :color="filterState.active?.length > 0 ? 'primary' : undefined"
          class="mr-3"
          v-bind="props"
          density="comfortable"
          theme="dark"
        >
          <template v-if="filterState.active?.length === 1">
            <v-icon start>{{ filterState.active[0] ? 'mdi-play' : 'mdi-pause' }}</v-icon>
            <span>{{ filterState.active[0] ? $t("Running") : $t("filterActivePaused") }}</span>
          </template>
          <template v-else>
            <v-icon start>mdi-play-pause</v-icon>
            {{ $t('filterActive') }}
          </template>
        </v-btn>
      </template>
      
      <v-card theme="dark" elevation="3" class="filter-menu">
        <v-card-title class="text-subtitle-1 px-4 py-2">{{ $t('Filter by Status') }}</v-card-title>
        <v-divider></v-divider>
        <v-list density="comfortable" theme="dark" class="py-2">
          <v-list-item @click="toggleActiveFilter(true)" theme="dark" class="px-4">
            <v-list-item-title class="d-flex justify-space-between align-center">
              <div class="d-flex align-center">
                <v-icon size="small" color="success" class="mr-2">mdi-play</v-icon>
                <span>{{ $t("Running") }}</span>
              </div>
              <div class="d-flex align-center">
                {{ $root.stats.active }}
                <v-icon v-if="filterState.active?.includes(true)" class="ml-2" size="small" color="primary">mdi-check</v-icon>
              </div>
            </v-list-item-title>
          </v-list-item>
          
          <v-list-item @click="toggleActiveFilter(false)" theme="dark" class="px-4">
            <v-list-item-title class="d-flex justify-space-between align-center">
              <div class="d-flex align-center">
                <v-icon size="small" color="grey" class="mr-2">mdi-pause</v-icon>
                <span>{{ $t("filterActivePaused") }}</span>
              </div>
              <div class="d-flex align-center">
                {{ $root.stats.pause }}
                <v-icon v-if="filterState.active?.includes(false)" class="ml-2" size="small" color="primary">mdi-check</v-icon>
              </div>
            </v-list-item-title>
          </v-list-item>
        </v-list>
      </v-card>
    </v-menu>

    <!-- Tags Filter -->
    <v-menu
      min-width="240"
      theme="dark"
      transition="slide-y-transition"
      :close-on-content-click="false"
    >
      <template v-slot:activator="{ props }">
        <v-btn
          size="small"
          variant="outlined"
          :color="filterState.tags?.length > 0 ? 'primary' : undefined"
          v-bind="props"
          density="comfortable"
          theme="dark"
        >
          <template v-if="filterState.tags?.length === 1">
            <Tag :item="tagsList.find(tag => tag.id === filterState.tags[0])" :size="'sm'" class="mr-1" />
          </template>
          <template v-else>
            <v-icon start>mdi-tag-multiple</v-icon>
            {{ $t('Tags') }}
          </template>
        </v-btn>
      </template>
      
      <v-card theme="dark" elevation="3" class="filter-menu">
        <v-card-title class="text-subtitle-1 px-4 py-2">{{ $t('Filter by Tags') }}</v-card-title>
        <v-divider></v-divider>
        <v-list density="comfortable" theme="dark" class="py-2">
          <template v-if="tagsList.length > 0">
            <v-list-item
              v-for="tag in tagsList"
              :key="tag.id"
              @click="toggleTagFilter(tag.id)"
              theme="dark"
              class="px-4"
            >
              <v-list-item-title class="d-flex justify-space-between align-center">
                <Tag :item="tag" :size="'sm'" />
                <v-icon
                  v-if="filterState.tags?.includes(tag.id)"
                  size="small"
                  color="primary"
                  class="ml-2"
                >mdi-check</v-icon>
              </v-list-item-title>
            </v-list-item>
          </template>
          <v-list-item v-else class="px-4">
            <v-list-item-title class="text-center text-disabled">
              {{ $t('No tags available') }}
            </v-list-item-title>
          </v-list-item>
        </v-list>
      </v-card>
    </v-menu>
  </div>
</template>

<script>
import Status from "./Status.vue";
import Tag from "./Tag.vue";

export default {
  components: {
    Status,
    Tag,
  },
  props: {
    filterState: {
      type: Object,
      required: true,
    }
  },
  emits: [ "updateFilter" ],
  data() {
    return {
      tagsList: [],
    };
  },
  computed: {
    numFiltersActive() {
      let num = 0;

      Object.values(this.filterState).forEach(item => {
        if (item != null && item.length > 0) {
          num += 1;
        }
      });

      return num;
    }
  },
  mounted() {
    this.getExistingTags();
  },
  methods: {
    toggleStatusFilter(status) {
      let newFilter = {
        ...this.filterState
      };

      if (newFilter.status == null) {
        newFilter.status = [ status ];
      } else {
        if (newFilter.status.includes(status)) {
          newFilter.status = newFilter.status.filter(item => item !== status);
        } else {
          newFilter.status.push(status);
        }
      }
      this.$emit("updateFilter", newFilter);
    },
    toggleActiveFilter(active) {
      let newFilter = {
        ...this.filterState
      };

      if (newFilter.active == null) {
        newFilter.active = [ active ];
      } else {
        if (newFilter.active.includes(active)) {
          newFilter.active = newFilter.active.filter(item => item !== active);
        } else {
          newFilter.active.push(active);
        }
      }
      this.$emit("updateFilter", newFilter);
    },
    toggleTagFilter(tag) {
      let newFilter = {
        ...this.filterState
      };

      if (newFilter.tags == null) {
        newFilter.tags = [ tag.id ];
      } else {
        if (newFilter.tags.includes(tag.id)) {
          newFilter.tags = newFilter.tags.filter(item => item !== tag.id);
        } else {
          newFilter.tags.push(tag.id);
        }
      }
      this.$emit("updateFilter", newFilter);
    },
    clearFilters() {
      this.$emit("updateFilter", {
        status: null,
        active: null,
        tags: null,
      });
    },
    getExistingTags() {
      this.$root.getSocket().emit("getTags", (res) => {
        if (res.ok) {
          this.tagsList = res.tags;
        }
      });
    },
    getTaggedMonitorCount(tag) {
      return Object.values(this.$root.monitorList).filter(monitor => {
        return monitor.tags.find(monitorTag => monitorTag.tag_id === tag.id);
      }).length;
    }
  }
};
</script>

<style lang="scss" scoped>
.filter-container {
  flex-wrap: wrap;
  gap: 8px;
}

.filter-menu {
  border: 1px solid rgba(255, 255, 255, 0.05);
  
  :deep(.v-list-item) {
    min-height: 44px;
    cursor: pointer;
    transition: all 0.2s ease;
    
    &:hover {
      background: rgba(255, 255, 255, 0.05);
    }
  }
}

:deep(.v-btn) {
  min-width: 100px;
}

:deep(.v-card-title) {
  font-weight: 500;
  letter-spacing: 0.0125em;
}
</style> 