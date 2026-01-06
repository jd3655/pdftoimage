<script setup lang="ts">
import { computed, ref, watchEffect } from "vue";

export type TabOption = { id: string; label: string; disabled?: boolean };

const props = defineProps<{
  modelValue: string;
  tabs: TabOption[];
}>();

const emit = defineEmits<{
  "update:modelValue": [value: string];
}>();

const active = ref(props.modelValue);

watchEffect(() => {
  active.value = props.modelValue;
});

const select = (id: string) => {
  if (props.tabs.find((t) => t.id === id)?.disabled) return;
  emit("update:modelValue", id);
};

const indicatorStyle = computed(() => {
  const index = props.tabs.findIndex((t) => t.id === active.value);
  if (index === -1) return {};
  const percentage = (index / props.tabs.length) * 100;
  return { transform: `translateX(${percentage}%)`, width: `${100 / props.tabs.length}%` };
});
</script>

<template>
  <div class="w-full">
    <div class="flex gap-2 rounded-lg bg-white border border-[var(--border)] p-1">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        class="relative w-full px-3 py-2 text-sm font-semibold rounded-md transition focus-ring"
        :class="[
          tab.id === active ? 'text-primary' : 'text-muted hover:text-[var(--text)]',
          tab.disabled ? 'cursor-not-allowed opacity-50' : '',
        ]"
        @click="select(tab.id)"
        :aria-pressed="tab.id === active"
      >
        {{ tab.label }}
      </button>
    </div>
    <div class="h-0.5 mt-1 bg-transparent relative">
      <div class="absolute top-0 left-0 h-0.5 bg-primary rounded-full transition-transform duration-200" :style="indicatorStyle" />
    </div>
  </div>
</template>
