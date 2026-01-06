<script setup lang="ts">
import { computed } from "vue";

type Variant = "primary" | "secondary" | "ghost" | "danger";
type Size = "sm" | "md";

const props = withDefaults(
  defineProps<{
    variant?: Variant;
    size?: Size;
    loading?: boolean;
    block?: boolean;
    type?: "button" | "submit" | "reset";
    disabled?: boolean;
    href?: string;
    as?: "button" | "a";
  }>(),
  {
    variant: "primary",
    size: "md",
    loading: false,
    block: false,
    type: "button",
    disabled: false,
    as: "button",
  },
);

const baseClasses =
  "focus-ring inline-flex items-center justify-center rounded-md font-semibold transition whitespace-nowrap disabled:cursor-not-allowed";

const variantClasses: Record<Variant, string> = {
  primary: "bg-primary text-white hover:bg-indigo-600 disabled:bg-indigo-300",
  secondary: "bg-white text-[var(--text)] border border-[var(--border)] hover:bg-slate-50",
  ghost: "bg-transparent text-[var(--text)] hover:bg-slate-100",
  danger: "bg-red-600 text-white hover:bg-red-700 disabled:bg-red-300",
};

const sizeClasses: Record<Size, string> = {
  sm: "text-sm px-3 py-2 gap-2",
  md: "text-sm px-4 py-2.5 gap-2",
};

const classes = computed(() => [
  baseClasses,
  variantClasses[props.variant],
  sizeClasses[props.size],
  props.block ? "w-full" : "",
]);
</script>

<template>
  <component
    :is="props.as === 'a' ? 'a' : 'button'"
    :type="props.as === 'a' ? undefined : type"
    :href="props.as === 'a' ? props.href : undefined"
    :disabled="disabled || loading"
    :class="classes"
  >
    <svg
      v-if="loading"
      class="h-4 w-4 animate-spin text-current"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
      <path
        class="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
      />
    </svg>
    <slot />
  </component>
</template>
