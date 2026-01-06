<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    variant?: "default" | "success" | "error" | "warning";
  }>(),
  { variant: "default" },
);

const styles: Record<string, string> = {
  default: "bg-slate-100 text-slate-700 border-slate-200",
  success: "bg-emerald-100 text-emerald-700 border-emerald-200",
  error: "bg-red-100 text-red-700 border-red-200",
  warning: "bg-amber-100 text-amber-700 border-amber-200",
};
</script>

<template>
  <span class="inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-xs font-semibold" :class="styles[props.variant]">
    <slot />
  </span>
</template>
