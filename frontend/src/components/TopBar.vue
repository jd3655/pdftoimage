<script setup lang="ts">
import Badge from "./ui/Badge.vue";
import Button from "./ui/Button.vue";
import Modal from "./ui/Modal.vue";
import { HelpCircle } from "lucide-vue-next";
import { ref, computed } from "vue";
import type { JobStatus } from "../composables/useJob";

const props = defineProps<{
  status: JobStatus;
  supportedExtensions: string[];
}>();

const open = ref(false);

const statusLabel = computed(() => props.status || "idle");
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
</script>

<template>
  <header class="flex items-center justify-between gap-3 rounded-2xl border border-[var(--border)] bg-white px-5 py-4 card-shadow">
    <div>
      <h1 class="text-2xl font-bold text-[var(--text)]">PDF to Image & Markdown</h1>
      <p class="text-sm text-muted">Modern local web app for preprocessing and MarkItDown export.</p>
    </div>
    <div class="flex items-center gap-3">
      <Badge :variant="statusVariant">{{ statusLabel.toString().toUpperCase() }}</Badge>
      <Button variant="ghost" size="sm" aria-label="Help" @click="open = true">
        <HelpCircle class="h-4 w-4" />
        Help
      </Button>
    </div>
  </header>

  <Modal :open="open" title="Supported files & tips" @close="open = false">
    <ul class="list-disc pl-5 text-sm text-[var(--text)] space-y-1">
      <li>Upload PDFs or images. ZIP archives are supported for batch runs.</li>
      <li>Image-first pipeline offers preview and per-page cleanup controls.</li>
      <li>MarkItDown adds plugins, LLM captions, and Azure Document Intelligence.</li>
      <li>
        Supported extensions:
        <strong>{{ supportedExtensions.length ? supportedExtensions.join(", ") : "PDF, PNG, JPG, TIFF" }}</strong>
      </li>
    </ul>
  </Modal>
</template>
