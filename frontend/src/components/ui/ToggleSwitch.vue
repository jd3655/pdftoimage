<script setup lang="ts">
defineProps<{
  modelValue: boolean;
  label?: string;
}>();

const emit = defineEmits<{ "update:modelValue": [value: boolean] }>();
</script>

<template>
  <label class="flex items-center gap-3 cursor-pointer select-none">
    <span v-if="label" class="text-sm text-[var(--text)]">{{ label }}</span>
    <span
      class="relative inline-flex h-6 w-10 items-center rounded-full transition"
      :class="modelValue ? 'bg-primary/80' : 'bg-slate-300'"
      @click="emit('update:modelValue', !modelValue)"
      role="switch"
      :aria-checked="modelValue"
    >
      <span
        class="inline-block h-4 w-4 transform rounded-full bg-white shadow transition"
        :class="modelValue ? 'translate-x-5' : 'translate-x-1'"
      />
    </span>
  </label>
</template>
