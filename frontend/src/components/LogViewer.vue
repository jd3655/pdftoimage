<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import Button from "./ui/Button.vue";
import ToggleSwitch from "./ui/ToggleSwitch.vue";
import { useToast } from "../composables/useToast";
import { Copy } from "lucide-vue-next";

const props = defineProps<{
  logs: string;
  running: boolean;
}>();

const autoscroll = ref(true);
const wrap = ref(true);
const filter = ref("");
const viewerRef = ref<HTMLPreElement | null>(null);
const { add } = useToast();

const filteredLogs = computed(() => {
  const query = debouncedFilter.value;
  if (!query) return props.logs;
  const lower = query.toLowerCase();
  return props.logs
    .split("\n")
    .filter((line) => line.toLowerCase().includes(lower))
    .join("\n");
});

watch(
  () => props.logs,
  () => {
    if (autoscroll.value && viewerRef.value) {
      requestAnimationFrame(() => {
        viewerRef.value!.scrollTop = viewerRef.value!.scrollHeight;
      });
    }
  },
);

const copyLogs = async () => {
  try {
    await navigator.clipboard.writeText(props.logs || "");
    add({ title: "Logs copied", variant: "success" });
  } catch (error) {
    add({ title: "Unable to copy logs", variant: "error" });
  }
};

const debounceTimer = ref<number | undefined>();
const debouncedFilter = ref("");
watch(
  () => filter.value,
  (value) => {
    if (debounceTimer.value) window.clearTimeout(debounceTimer.value);
    debounceTimer.value = window.setTimeout(() => {
      debouncedFilter.value = value;
    }, 200);
  },
);

const wrappedLogs = computed(() => (wrap.value ? "whitespace-pre-wrap" : "whitespace-pre"));

onMounted(() => {
  if (viewerRef.value) viewerRef.value.scrollTop = viewerRef.value.scrollHeight;
});

onUnmounted(() => {
  if (debounceTimer.value) clearTimeout(debounceTimer.value);
});
</script>

<template>
  <div class="space-y-3">
    <div class="flex flex-wrap gap-3 items-center justify-between">
      <div class="flex gap-3 items-center">
        <ToggleSwitch v-model="autoscroll" label="Auto-scroll" />
        <ToggleSwitch v-model="wrap" label="Wrap lines" />
      </div>
      <div class="flex gap-2 items-center">
        <input
          v-model="filter"
          type="search"
          class="w-44 rounded-md border border-[var(--border)] px-3 py-2 text-sm focus:ring-primary focus:border-primary"
          placeholder="Search logs"
        />
        <Button variant="secondary" size="sm" @click="copyLogs">
          <Copy class="h-4 w-4" />
          Copy
        </Button>
      </div>
    </div>
    <pre
      ref="viewerRef"
      class="max-h-80 overflow-y-auto rounded-lg border border-[var(--border)] bg-slate-900/90 text-slate-100 p-4 text-xs"
      :class="wrappedLogs"
    >{{ debouncedFilter ? filteredLogs : logs || 'Logs will appear here...' }}</pre>
  </div>
</template>
