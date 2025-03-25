<template>
    <v-chip
        :color="color"
        :size="size === 'sm' ? 'x-small' : 'small'"
        variant="flat"
        theme="dark"
        class="tag"
        density="compact"
    >
        <span class="tag-name">{{ item.name }}</span>
        <span v-if="item.value" class="tag-value">{{ item.value }}</span>
    </v-chip>
</template>

<script>
import chroma from 'chroma-js';

export default {
    props: {
        item: {
            type: Object,
            required: true,
        },
        size: {
            type: String,
            default: 'md',
        },
    },
    computed: {
        color() {
            if (!this.item.color) {
                return 'grey';
            }
            
            const color = chroma(this.item.color);
            return color.luminance() > 0.5 ? color.darken(2).hex() : this.item.color;
        },
    },
};
</script>

<style lang="scss" scoped>
.tag {
    font-weight: 500;
    letter-spacing: 0.0125em;
    height: 18px !important;
    
    :deep(.v-chip__content) {
        padding: 0 4px;
    }
}

.tag-name {
    opacity: 0.9;
    font-size: 0.7em;
}

.tag-value {
    opacity: 0.7;
    margin-left: 2px;
    font-size: 0.7em;
    
    &:before {
        content: ':';
        margin-right: 2px;
        opacity: 0.5;
    }
}
</style> 