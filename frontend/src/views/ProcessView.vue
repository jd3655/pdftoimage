<script setup lang="ts">
import UploadPanel from "../components/UploadPanel.vue";
import SettingsPanel from "../components/SettingsPanel.vue";
import JobPanel from "../components/JobPanel.vue";
import LogViewer from "../components/LogViewer.vue";
import Card from "../components/ui/Card.vue";
import CardHeader from "../components/ui/CardHeader.vue";
import CardContent from "../components/ui/CardContent.vue";
import { Clock3 } from "lucide-vue-next";
import type { BackendMode } from "../composables/useSettings";
import type { JobStatus } from "../composables/useJob";
import { computed } from "vue";

const props = defineProps<{
  backendMode: { value: BackendMode };
  imageSettings: Record<string, any>;
  markitdown: Record<string, any>;
  files: File[];
  zipFile: File | null;
  supportedExtensions: string[];
  jobStatus: JobStatus;
  jobProgress: number;
  jobMessage: string;
  jobHasDownload: boolean;
  downloadUrl: string;
  jobRunning: boolean;
  elapsedSeconds: number;
  logs: string;
  error: string | null;
  canStart: boolean;
}>();

const emit = defineEmits<{
  addFiles: [files: File[]];
  addZip: [file: File | null];
  removeFile: [index: number];
  clearAll: [];
  drop: [event: DragEvent];
  pickFiles: [event: Event];
  pickZip: [event: Event];
  updateBackendMode: [value: BackendMode];
  resetImage: [];
  startJob: [];
  cancelJob: [];
}>();

const statusText = computed(() => {
  if (!props.jobStatus) return "Idle";
  return props.jobStatus.charAt(0).toUpperCase() + props.jobStatus.slice(1);
});
</script>

<template>
  <div class="grid grid-cols-1 gap-4 xl:grid-cols-[1.1fr_0.9fr]">
    <div class="space-y-4">
      <UploadPanel
        :files="files"
        :zip-file="zipFile"
        :supported-extensions="supportedExtensions"
        :backend-mode="backendMode.value"
        @add-files="emit('addFiles', $event)"
        @add-zip="emit('addZip', $event)"
        @remove-file="emit('removeFile', $event)"
        @clear-all="emit('clearAll')"
        @drop="emit('drop', $event)"
        @pick-files="emit('pickFiles', $event)"
        @pick-zip="emit('pickZip', $event)"
      />
      <SettingsPanel
        :backend-mode="backendMode"
        :image-settings="imageSettings"
        :markitdown="markitdown"
        @update:backend-mode="emit('updateBackendMode', $event)"
        @reset-image="emit('resetImage')"
      />
    </div>

    <div class="space-y-4">
      <JobPanel
        :status="jobStatus"
        :progress="jobProgress"
        :message="jobMessage"
        :has-download="jobHasDownload"
        :download-url="downloadUrl"
        :running="jobRunning"
        :elapsed-seconds="elapsedSeconds"
        :error="error"
        :can-start="canStart"
        @start="emit('startJob')"
        @cancel="emit('cancelJob')"
      />

      <Card>
        <CardHeader>
          <template #title>Progress & status</template>
          <template #description>Track the latest updates from the backend.</template>
          <template #action>
            <div class="flex items-center gap-2 text-sm text-muted">
              <Clock3 class="h-4 w-4" />
              {{ statusText }}
            </div>
          </template>
        </CardHeader>
        <CardContent>
          <LogViewer :logs="logs" :running="jobRunning" />
        </CardContent>
      </Card>
    </div>
  </div>
</template>
