<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from "vue";
import Tabs from "./components/ui/Tabs.vue";
import TopBar from "./components/TopBar.vue";
import ProcessView from "./views/ProcessView.vue";
import PreviewView from "./views/PreviewView.vue";
import ToastHost from "./components/ToastHost.vue";
import { useSettings } from "./composables/useSettings";
import { useUploads } from "./composables/useUploads";
import { useJob } from "./composables/useJob";
import { usePreview } from "./composables/usePreview";
import axios from "axios";

const activeTab = ref<"process" | "preview">("process");
const supportedExtensions = ref<string[]>([]);

const { backendMode, imageSettings, markitdown, resetImage } = useSettings();
const uploads = useUploads();
const job = useJob();
const preview = usePreview();
const previewFile = ref<File | null>(null);

const tabs = [
  { id: "process", label: "Process" },
  { id: "preview", label: "Preview" },
];

const handlePreviewInput = (event: Event) => {
  const target = event.target as HTMLInputElement;
  previewFile.value = target.files && target.files[0] ? target.files[0] : null;
};

const runPreview = () => {
  const source = previewFile.value || uploads.files.value[0] || null;
  preview.runPreview(source, backendMode.value, imageSettings);
};

onMounted(async () => {
  try {
    const { data } = await axios.get<{ supported_extensions: string[] }>("/api/meta");
    supportedExtensions.value = data.supported_extensions;
  } catch (error) {
    supportedExtensions.value = [];
  }
});

onBeforeUnmount(() => job.stopPolling());
</script>

<template>
  <div class="min-h-screen bg-[var(--bg)]">
    <div class="mx-auto max-w-6xl px-4 py-6 space-y-5">
      <TopBar :status="job.status.value" :supported-extensions="supportedExtensions" />
      <Tabs v-model="activeTab" :tabs="tabs" />
      <div>
        <ProcessView
          v-if="activeTab === 'process'"
          :backend-mode="backendMode"
          :image-settings="imageSettings"
          :markitdown="markitdown"
          :files="uploads.files.value"
          :zip-file="uploads.zipFile.value"
          :supported-extensions="supportedExtensions"
          :job-status="job.status.value"
          :job-progress="job.progress.value"
          :job-message="job.message.value"
          :job-has-download="job.hasDownload.value"
          :download-url="job.downloadUrl.value"
          :job-running="job.running.value"
          :elapsed-seconds="job.elapsedSeconds.value"
          :logs="job.logs.value"
          :error="job.error.value"
          :can-start="uploads.canStart.value"
          @add-files="uploads.addFiles"
          @add-zip="uploads.addZip"
          @remove-file="uploads.removeFile"
          @clear-all="uploads.clearAll"
          @drop="uploads.handleDrop"
          @pick-files="uploads.handleFileInput"
          @pick-zip="uploads.handleZipInput"
          @update:backendMode="(mode) => (backendMode.value = mode)"
          @reset-image="resetImage"
          @start-job="() => job.start(backendMode.value, imageSettings, markitdown, uploads.files.value, uploads.zipFile.value)"
          @cancel-job="job.cancel"
        />
        <PreviewView
          v-else
          :before="preview.before.value"
          :after="preview.after.value"
          :info="preview.info.value"
          :loading="preview.loading.value"
          :backend-mode="backendMode.value"
          @select="handlePreviewInput"
          @preview="runPreview"
        />
      </div>
    </div>
    <ToastHost />
  </div>
</template>
