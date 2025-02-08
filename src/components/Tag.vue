<template>
    <div
        class="tag-wrapper rounded d-inline-flex"
        :class="{ 'px-2': size == 'normal',
                  'py-1': size == 'normal',
                  'm-1': size == 'normal',
                  'px-1': size == 'sm',
                  'py-0': size == 'sm',
                  'mx-1': size == 'sm',
        }"
        :style="{ backgroundColor: item.color, fontSize: size == 'sm' ? '0.65em' : '0.85em' }"
    >
        <span class="tag-text">{{ displayText }}</span>
        <span v-if="remove != null" class="ps-1 btn-remove" @click="remove(item)">
            <font-awesome-icon icon="times" size="xs" />
        </span>
    </div>
</template>

<script>
/**
 * @typedef {import('./TagsManager.vue').Tag} Tag
 */

export default {
    props: {
        /**
         * Object representing tag
         * @type {Tag}
         */
        item: {
            type: Object,
            required: true,
        },
        /** Function to remove tag */
        remove: {
            type: Function,
            default: null,
        },
        /**
         * Size of tag
         * @type {"normal" | "small"}
         */
        size: {
            type: String,
            default: "normal",
        }
    },
    computed: {
        displayText() {
            if (this.item.value === "" || this.item.value === undefined) {
                return this.item.name;
            } else {
                return `${this.item.name}: ${this.item.value}`;
            }
        }
    }
};
</script>

<style lang="scss" scoped>
.tag-wrapper {
    color: white;
    opacity: 0.85;
    line-height: 1.2;

    .dark & {
        opacity: 1;
    }
}

.tag-text {
    padding-bottom: 0 !important;
    text-overflow: ellipsis;
    overflow: hidden;
    white-space: nowrap;
    max-width: 120px;
}

.btn-remove {
    font-size: 0.8em;
    line-height: 18px;
    opacity: 0.3;
    padding: 0 2px;
}

.btn-remove:hover {
    opacity: 1;
}
</style>
