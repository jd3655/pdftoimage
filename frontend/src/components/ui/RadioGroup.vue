<script setup lang="ts">
export interface RadioOption {
  value: string;
  label: string;
  description?: string;
}

defineProps<{
  modelValue: string;
  options: RadioOption[];
  name: string;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: string];
}>();
</script>

<template>
  <div class="space-y-2">
    <label
      v-for="option in options"
      :key="option.value"
      class="flex cursor-pointer items-start gap-3 rounded-lg border border-[var(--border)] bg-white px-3 py-2 hover:border-primary transition"
    >
      <input
        type="radio"
        :name="name"
        class="mt-1 h-4 w-4 text-primary focus:ring-primary"
        :checked="modelValue === option.value"
        @change="emit('update:modelValue', option.value)"
      />
      <div class="space-y-0.5">
        <div class="text-sm font-semibold text-[var(--text)]">{{ option.label }}</div>
        <p v-if="option.description" class="text-xs text-muted">{{ option.description }}</p>
      </div>
    </label>
  </div>
</template>
