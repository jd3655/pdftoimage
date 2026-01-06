<script setup lang="ts">
import { computed, onMounted, onUnmounted } from "vue";

const props = defineProps<{
  open: boolean;
  title: string;
}>();

const emit = defineEmits<{
  close: [];
}>();

const handleEscape = (event: KeyboardEvent) => {
  if (event.key === "Escape" && props.open) emit("close");
};

onMounted(() => window.addEventListener("keydown", handleEscape));
onUnmounted(() => window.removeEventListener("keydown", handleEscape));

const ariaHidden = computed(() => (!props.open).toString());
</script>

<template>
  <teleport to="body">
    <div
      v-if="open"
      class="fixed inset-0 z-50 flex items-center justify-center px-4"
      role="dialog"
      :aria-hidden="ariaHidden"
      aria-modal="true"
    >
      <div class="absolute inset-0 bg-black/40 backdrop-blur-sm" @click="emit('close')" />
      <div class="relative z-10 w-full max-w-lg rounded-xl bg-card border border-[var(--border)] card-shadow">
        <div class="flex items-center justify-between border-b border-[var(--border)] px-5 py-4">
          <h2 class="text-lg font-semibold text-[var(--text)]">{{ title }}</h2>
          <button class="focus-ring rounded-full p-1 hover:bg-slate-100" @click="emit('close')" aria-label="Close dialog">
            <span class="block h-5 w-5">✕</span>
          </button>
        </div>
        <div class="p-5 space-y-3">
          <slot />
        </div>
      </div>
    </div>
  </teleport>
</template>
