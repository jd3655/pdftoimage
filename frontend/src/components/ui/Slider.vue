<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  modelValue: number;
  min: number;
  max: number;
  step?: number;
  label?: string;
  helper?: string;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: number];
}>();

const percentage = computed(() => ((props.modelValue - props.min) / (props.max - props.min)) * 100);
</script>

<template>
  <div class="space-y-1.5">
    <div class="flex items-center justify-between text-sm">
      <span class="font-medium text-[var(--text)]">{{ label }}</span>
      <span class="text-xs text-muted">{{ modelValue.toFixed(2) }}</span>
    </div>
    <div class="relative">
      <input
        type="range"
        class="w-full accent-primary"
        :min="min"
        :max="max"
        :step="step"
        :value="modelValue"
        @input="emit('update:modelValue', Number(($event.target as HTMLInputElement).value))"
      />
      <div class="pointer-events-none absolute inset-y-0 left-0 h-1 rounded-full bg-indigo-100" />
      <div class="pointer-events-none absolute inset-y-0 left-0 h-1 rounded-full bg-primary" :style="{ width: `${percentage}%` }" />
    </div>
    <p v-if="helper" class="text-xs text-muted">{{ helper }}</p>
  </div>
</template>
