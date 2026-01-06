<script setup lang="ts">
import { computed } from "vue";
import Card from "./ui/Card.vue";
import CardHeader from "./ui/CardHeader.vue";
import CardContent from "./ui/CardContent.vue";
import Button from "./ui/Button.vue";
import Badge from "./ui/Badge.vue";
import { Upload, X, FileArchive, File } from "lucide-vue-next";
import type { BackendMode } from "../composables/useSettings";

const props = defineProps<{
  files: File[];
  zipFile: File | null;
  supportedExtensions: string[];
  backendMode: BackendMode;
}>();

const emit = defineEmits<{
  addFiles: [files: File[]];
  addZip: [file: File | null];
  removeFile: [index: number];
  clearAll: [];
  drop: [event: DragEvent];
  pickFiles: [event: Event];
  pickZip: [event: Event];
}>();

const supportedText = computed(() =>
  props.supportedExtensions?.length ? props.supportedExtensions.join(", ") : "PDF, PNG, JPG and more",
);
</script>

<template>
  <Card
    class="border-dashed border-2 border-indigo-100 bg-gradient-to-b from-white to-indigo-50/30 transition hover:border-primary"
    @dragover.prevent
    @dragenter.prevent
    @drop="emit('drop', $event)"
  >
    <CardHeader>
      <template #title>Upload files</template>
      <template #description>Drag and drop or use the pickers. Start is enabled once you add files or a ZIP.</template>
      <template #action>
        <Badge>{{ backendMode }}</Badge>
      </template>
    </CardHeader>
    <CardContent>
      <div class="flex flex-wrap gap-2">
        <label class="flex items-center gap-2 rounded-lg border border-[var(--border)] bg-white px-4 py-2 text-sm font-semibold cursor-pointer focus-ring">
          <Upload class="h-4 w-4 text-primary" />
          Add files
          <input type="file" multiple class="hidden" @change="emit('pickFiles', $event)" />
        </label>
        <label class="flex items-center gap-2 rounded-lg border border-[var(--border)] bg-white px-4 py-2 text-sm font-semibold cursor-pointer focus-ring">
          <FileArchive class="h-4 w-4 text-primary" />
          Add ZIP
          <input type="file" accept=".zip" class="hidden" @change="emit('pickZip', $event)" />
        </label>
        <Button variant="ghost" size="sm" @click="emit('clearAll')">Clear all</Button>
      </div>
      <p class="text-xs text-muted">Supported: {{ supportedText }}</p>
      <div class="space-y-2">
        <div v-if="files.length === 0 && !zipFile" class="text-sm text-muted">
          Drop PDF or images here, or select with the buttons.
        </div>
        <div v-else class="space-y-2">
          <div class="flex items-center justify-between text-xs text-muted">
            <span>Files ({{ files.length }})</span>
            <span class="font-medium">{{ zipFile ? "ZIP added" : "ZIP optional" }}</span>
          </div>
          <ul class="space-y-1">
            <li
              v-for="(file, index) in files"
              :key="file.name + index"
              class="flex items-center justify-between rounded-md border border-[var(--border)] bg-white px-3 py-2 text-sm"
            >
              <div class="flex items-center gap-2 min-w-0">
                <File class="h-4 w-4 text-primary" />
                <div class="min-w-0">
                  <div class="truncate font-medium">{{ file.name }}</div>
                  <div class="text-xs text-muted">{{ (file.size / 1024 / 1024).toFixed(2) }} MB</div>
                </div>
              </div>
              <button class="text-muted hover:text-red-500" @click="emit('removeFile', index)">
                <X class="h-4 w-4" />
              </button>
            </li>
          </ul>
          <div v-if="zipFile" class="flex items-center gap-2 text-sm text-[var(--text)]">
            <FileArchive class="h-4 w-4 text-primary" />
            ZIP: <span class="font-semibold">{{ zipFile.name }}</span>
          </div>
        </div>
      </div>
    </CardContent>
  </Card>
</template>
