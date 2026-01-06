<script setup lang="ts">
import { computed } from "vue";
import { useToast } from "../composables/useToast";
import { CircleCheck, CircleX, Info } from "lucide-vue-next";

const { toasts, dismiss } = useToast();

const iconFor = computed(() => ({
  success: CircleCheck,
  error: CircleX,
  info: Info,
}));
</script>

<template>
  <div class="fixed inset-0 pointer-events-none z-50 flex items-start justify-end px-4 py-6">
    <div class="w-full max-w-sm space-y-2">
      <div
        v-for="toast in toasts"
        :key="toast.id"
        class="pointer-events-auto rounded-lg border border-[var(--border)] bg-card p-4 shadow-lg flex gap-3 items-start"
      >
        <component
          :is="iconFor[toast.variant || 'info']"
          class="h-5 w-5"
          :class="toast.variant === 'error' ? 'text-red-500' : toast.variant === 'success' ? 'text-emerald-500' : 'text-primary'"
        />
        <div class="flex-1">
          <p class="text-sm font-semibold text-[var(--text)]">{{ toast.title }}</p>
          <p v-if="toast.description" class="text-xs text-muted mt-1">{{ toast.description }}</p>
        </div>
        <button class="text-muted text-sm hover:text-[var(--text)]" @click="dismiss(toast.id)" aria-label="Dismiss notification">✕</button>
      </div>
    </div>
  </div>
</template>
