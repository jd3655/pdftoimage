<script setup lang="ts">
import Card from "./ui/Card.vue";
import CardHeader from "./ui/CardHeader.vue";
import CardContent from "./ui/CardContent.vue";
import Button from "./ui/Button.vue";
import Badge from "./ui/Badge.vue";
import { AlertTriangle, Download, Play, StopCircle } from "lucide-vue-next";
import type { JobStatus } from "../composables/useJob";
import { computed } from "vue";

const props = defineProps<{
  status: JobStatus;
  progress: number;
  message: string;
  hasDownload: boolean;
  downloadUrl: string;
  running: boolean;
  elapsedSeconds: number;
  error: string | null;
  canStart: boolean;
}>();

const emit = defineEmits<{
  start: [];
  cancel: [];
}>();

const statusVariant = computed(() => {
  switch (props.status) {
    case "done":
      return "success";
    case "error":
    case "cancelled":
      return "error";
    case "running":
    case "queued":
      return "warning";
    default:
      return "default";
  }
});

const formattedElapsed = computed(() => {
  const m = Math.floor(props.elapsedSeconds / 60);
  const s = props.elapsedSeconds % 60;
  return `${m}m ${s}s`;
});
</script>

<template>
  <Card>
    <CardHeader>
      <template #title>Run job</template>
      <template #description>Start processing and monitor progress. Cancel when needed.</template>
      <template #action>
        <Badge :variant="statusVariant">
          {{ status ? status.toUpperCase() : "IDLE" }}
        </Badge>
      </template>
    </CardHeader>
    <CardContent class="space-y-4">
      <div class="flex flex-wrap gap-2">
        <Button :disabled="running || !canStart" @click="emit('start')">
          <Play class="h-4 w-4" />
          {{ running ? "Running..." : "Start" }}
        </Button>
        <Button variant="danger" :disabled="!running" @click="emit('cancel')">
          <StopCircle class="h-4 w-4" />
          Cancel
        </Button>
        <Button v-if="hasDownload" variant="secondary" :href="downloadUrl" as="a">
          <Download class="h-4 w-4" />
          Download ZIP
        </Button>
      </div>

      <div class="space-y-2">
        <div class="flex items-center justify-between text-sm text-muted">
          <span>{{ message || "Idle" }}</span>
          <span v-if="running">Elapsed: {{ formattedElapsed }}</span>
        </div>
        <div class="h-3 rounded-full bg-slate-200 overflow-hidden">
          <div
            class="h-full bg-gradient-to-r from-primary to-indigo-500 transition-all"
            :style="{ width: `${Math.round(progress * 100)}%` }"
          />
        </div>
        <div v-if="status === 'error' && error" class="flex items-start gap-2 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          <AlertTriangle class="h-4 w-4 mt-0.5" />
          <div>{{ error }}</div>
        </div>
      </div>
    </CardContent>
  </Card>
</template>
