<script setup lang="ts">
defineProps<{
  modelValue: boolean;
  label?: string;
}>();

const emit = defineEmits<{ "update:modelValue": [value: boolean] }>();
</script>

<template>
  <label class="flex items-center gap-2 text-sm text-[var(--text)] cursor-pointer">
    <input
      type="checkbox"
      class="rounded border-[var(--border)] text-primary focus:ring-primary"
      :checked="modelValue"
      @change="emit('update:modelValue', ($event.target as HTMLInputElement).checked)"
    />
    <span v-if="label">{{ label }}</span>
    <slot />
  </label>
</template>
