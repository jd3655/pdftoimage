<script setup lang="ts">
import axios from "axios";
import { computed, onBeforeUnmount, onMounted, reactive, ref } from "vue";

type BackendMode = "Image-first (existing)" | "MarkItDown (document-to-markdown)";

type JobStatus = "queued" | "running" | "done" | "error" | "cancelled";

interface JobResponse {
  job_id: string;
  status: JobStatus;
  progress: number;
  message: string;
  error: string | null;
  has_download: boolean;
  logs_tail: string;
}

const backendMode = ref<BackendMode>("Image-first (existing)");
const activeTab = ref<"process" | "preview">("process");
const files = ref<File[]>([]);
const zipFile = ref<File | null>(null);
const jobId = ref<string | null>(null);
const jobStatus = ref<JobStatus | null>(null);
const progress = ref(0);
const statusMessage = ref("");
const logs = ref("");
const hasDownload = ref(false);
const pollTimer = ref<number | undefined>(undefined);
const supportedExtensions = ref<string[]>([]);

const imageSettings = reactive({
  dpi: 400,
  color_mode: "Grayscale",
  auto_orient: true,
  deskew: true,
  deskew_sensitivity: 0.4,
  contrast_stretch: true,
  contrast_percent: 0.5,
  trim: true,
  adaptive_threshold: false,
  mode: "Balanced",
});

const markitdownOptions = reactive({
  enable_plugins: false,
  use_docintel: false,
  docintel_endpoint: "",
  docintel_key: "",
  use_llm_descriptions: false,
  llm_provider: "OpenAI",
  llm_model: "",
  llm_api_key: "",
  llm_prompt: "",
  output_format: "Markdown + manifest JSON",
  youtube_url: "",
});

const previewFile = ref<File | null>(null);
const previewBefore = ref<string | null>(null);
const previewAfter = ref<string | null>(null);
const previewInfo = ref<string>("Upload a file to preview the image-first pipeline.");

const isRunning = computed(() => jobStatus.value === "running" || jobStatus.value === "queued");

function handleFileInput(event: Event) {
  const target = event.target as HTMLInputElement;
  if (target.files) {
    files.value = [...files.value, ...Array.from(target.files)];
  }
}

function handleZipInput(event: Event) {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files.length > 0) {
    zipFile.value = target.files[0];
  }
}

function removeFile(index: number) {
  files.value.splice(index, 1);
}

function onDrop(event: DragEvent) {
  event.preventDefault();
  if (!event.dataTransfer) return;
  const droppedFiles = Array.from(event.dataTransfer.files || []);
  const zips = droppedFiles.filter((f) => f.name.toLowerCase().endsWith(".zip"));
  const nonZips = droppedFiles.filter((f) => !f.name.toLowerCase().endsWith(".zip"));
  if (nonZips.length) {
    files.value = [...files.value, ...nonZips];
  }
  if (zips.length) {
    zipFile.value = zips[0];
  }
}

function preventDefault(event: DragEvent) {
  event.preventDefault();
}

async function startJob() {
  if (isRunning.value) return;
  const form = new FormData();
  files.value.forEach((file) => form.append("files", file));
  if (zipFile.value) {
    form.append("zip_file", zipFile.value);
  }
  form.append("backend_mode", backendMode.value);
  Object.entries(imageSettings).forEach(([key, value]) => form.append(key, String(value)));
  Object.entries(markitdownOptions).forEach(([key, value]) => form.append(key, String(value)));

  jobId.value = null;
  jobStatus.value = "queued";
  progress.value = 0;
  statusMessage.value = "Submitting job...";
  logs.value = "";
  hasDownload.value = false;

  try {
    const { data } = await axios.post<{ job_id: string }>("/api/jobs", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    jobId.value = data.job_id;
    statusMessage.value = "Job queued";
    beginPolling();
  } catch (error: any) {
    statusMessage.value = error?.response?.data?.detail || "Failed to start job.";
    jobStatus.value = "error";
  }
}

function beginPolling() {
  stopPolling();
  pollTimer.value = window.setInterval(async () => {
    if (!jobId.value) return;
    try {
      const { data } = await axios.get<JobResponse>(`/api/jobs/${jobId.value}`);
      jobStatus.value = data.status;
      progress.value = data.progress;
      statusMessage.value = data.message || data.status;
      logs.value = data.logs_tail || "";
      hasDownload.value = data.has_download;
      if (["done", "error", "cancelled"].includes(data.status)) {
        stopPolling();
      }
    } catch (error) {
      stopPolling();
      jobStatus.value = "error";
      statusMessage.value = "Failed to poll job status.";
    }
  }, 500);
}

function stopPolling() {
  if (pollTimer.value) {
    clearInterval(pollTimer.value);
    pollTimer.value = undefined;
  }
}

async function cancelJob() {
  if (!jobId.value) return;
  try {
    await axios.post(`/api/jobs/${jobId.value}/cancel`);
    statusMessage.value = "Cancellation requested";
    jobStatus.value = "cancelled";
  } catch (error) {
    statusMessage.value = "Failed to cancel job";
  }
}

function downloadUrl() {
  if (!jobId.value) return "#";
  return `/api/jobs/${jobId.value}/download`;
}

async function runPreview() {
  if (backendMode.value !== "Image-first (existing)") {
    previewInfo.value = "Preview is only available for the image-first pipeline.";
    return;
  }
  const source = previewFile.value || files.value[0] || null;
  if (!source) {
    previewInfo.value = "Add a file to preview.";
    return;
  }
  const form = new FormData();
  form.append("file", source);
  Object.entries(imageSettings).forEach(([key, value]) => form.append(key, String(value)));
  try {
    const { data } = await axios.post("/api/preview", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    previewBefore.value = `data:image/png;base64,${data.before_png_b64}`;
    previewAfter.value = `data:image/png;base64,${data.after_png_b64}`;
    previewInfo.value = data.info;
  } catch (error: any) {
    previewInfo.value = error?.response?.data?.detail || "Failed to generate preview.";
  }
}

onMounted(async () => {
  try {
    const { data } = await axios.get<{ supported_extensions: string[] }>("/api/meta");
    supportedExtensions.value = data.supported_extensions;
  } catch (error) {
    supportedExtensions.value = [];
  }
});

onBeforeUnmount(() => stopPolling());

const hasLLMOptions = computed(() => markitdownOptions.use_llm_descriptions);
const hasDocIntel = computed(() => markitdownOptions.use_docintel);

function handlePreviewInput(event: Event) {
  const target = event.target as HTMLInputElement;
  previewFile.value = target.files && target.files[0] ? target.files[0] : null;
}
</script>

<template>
  <div class="mx-auto max-w-6xl px-4 py-6 space-y-6">
    <header class="flex flex-col gap-2">
      <h1 class="text-3xl font-bold text-slate-900">PDF to Image & Document Converter</h1>
      <p class="text-slate-600">Local web app for Image-first preprocessing and MarkItDown document-to-markdown.</p>
    </header>

    <nav class="flex gap-3 border-b border-slate-200 pb-3 text-sm font-medium">
      <button
        class="btn btn-secondary"
        :class="{ 'bg-indigo-50 text-indigo-700 border-indigo-200': activeTab === 'process' }"
        @click="activeTab = 'process'"
      >
        Process
      </button>
      <button
        class="btn btn-secondary"
        :class="{ 'bg-indigo-50 text-indigo-700 border-indigo-200': activeTab === 'preview' }"
        @click="activeTab = 'preview'"
      >
        Preview
      </button>
    </nav>

    <section v-if="activeTab === 'process'" class="space-y-4">
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div class="lg:col-span-2 space-y-4">
          <div
            class="section-card flex flex-col gap-3 border-dashed border-2 border-slate-200"
            @dragover="preventDefault"
            @dragenter="preventDefault"
            @drop="onDrop"
          >
            <div class="flex items-center justify-between">
              <div>
                <h2 class="section-title">Upload</h2>
                <p class="text-sm text-slate-600">Drag and drop files or add them with the pickers below.</p>
              </div>
              <div class="text-xs text-slate-500">Accepted: {{ supportedExtensions.join(', ') || 'multiple formats' }}</div>
            </div>
            <div class="flex flex-wrap gap-2">
              <label class="btn btn-secondary cursor-pointer">
                Add Files
                <input type="file" class="hidden" multiple @change="handleFileInput" />
              </label>
              <label class="btn btn-secondary cursor-pointer">
                Add Folder (ZIP)
                <input type="file" class="hidden" accept=".zip" @change="handleZipInput" />
              </label>
            </div>
            <div class="space-y-2">
              <div v-if="files.length === 0" class="text-sm text-slate-500">No files added yet.</div>
              <ul class="space-y-1" v-else>
                <li v-for="(file, index) in files" :key="file.name + index" class="flex items-center justify-between text-sm">
                  <span class="truncate">{{ file.name }}</span>
                  <button class="text-indigo-600 hover:underline" @click="removeFile(index)">Remove</button>
                </li>
              </ul>
              <div v-if="zipFile" class="text-sm text-slate-600">ZIP: {{ zipFile.name }}</div>
            </div>
          </div>

          <div class="section-card space-y-4">
            <div class="flex flex-wrap gap-4 items-center justify-between">
              <div>
                <h2 class="section-title mb-0">Processing Backend</h2>
                <p class="text-sm text-slate-600">Choose Image-first or MarkItDown.</p>
              </div>
              <div class="flex gap-3">
                <label class="flex items-center gap-2 text-sm">
                  <input type="radio" value="Image-first (existing)" v-model="backendMode" />
                  Image-first
                </label>
                <label class="flex items-center gap-2 text-sm">
                  <input type="radio" value="MarkItDown (document-to-markdown)" v-model="backendMode" />
                  MarkItDown
                </label>
              </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="space-y-3">
                <h3 class="font-semibold text-slate-800">Image-first options</h3>
                <div class="grid grid-cols-2 gap-3 text-sm">
                  <label class="space-y-1">
                    <span>PDF DPI</span>
                    <select v-model.number="imageSettings.dpi" class="input">
                      <option :value="300">300</option>
                      <option :value="400">400</option>
                      <option :value="450">450</option>
                      <option :value="600">600</option>
                    </select>
                  </label>
                  <label class="space-y-1">
                    <span>Color mode</span>
                    <select v-model="imageSettings.color_mode" class="input">
                      <option>Grayscale</option>
                      <option>Color</option>
                    </select>
                  </label>
                  <label class="flex items-center gap-2"><input type="checkbox" v-model="imageSettings.auto_orient" /> Auto-orient</label>
                  <label class="flex items-center gap-2"><input type="checkbox" v-model="imageSettings.deskew" /> Deskew</label>
                  <label class="space-y-1 col-span-2">
                    <span>Deskew sensitivity</span>
                    <input type="range" min="0" max="1" step="0.05" v-model.number="imageSettings.deskew_sensitivity" class="w-full" />
                    <span class="text-xs text-slate-500">{{ imageSettings.deskew_sensitivity }}</span>
                  </label>
                  <label class="flex items-center gap-2"><input type="checkbox" v-model="imageSettings.contrast_stretch" /> Contrast stretch</label>
                  <label class="space-y-1">
                    <span>Contrast percentile</span>
                    <input type="number" class="input" step="0.1" min="0.2" max="2" v-model.number="imageSettings.contrast_percent" />
                  </label>
                  <label class="flex items-center gap-2"><input type="checkbox" v-model="imageSettings.trim" /> Trim whitespace</label>
                  <label class="flex items-center gap-2"><input type="checkbox" v-model="imageSettings.adaptive_threshold" /> Adaptive threshold</label>
                  <label class="space-y-1 col-span-2">
                    <span>Processing Mode</span>
                    <select v-model="imageSettings.mode" class="input">
                      <option>Balanced</option>
                      <option>Aggressive for scans</option>
                    </select>
                  </label>
                </div>
              </div>

              <div class="space-y-3">
                <h3 class="font-semibold text-slate-800">MarkItDown options</h3>
                <label class="flex items-center gap-2 text-sm"><input type="checkbox" v-model="markitdownOptions.enable_plugins" /> Enable plugins</label>
                <label class="flex items-center gap-2 text-sm"><input type="checkbox" v-model="markitdownOptions.use_docintel" /> Use Azure Document Intelligence</label>
                <div v-if="hasDocIntel" class="space-y-2 text-sm">
                  <input v-model="markitdownOptions.docintel_endpoint" class="input" placeholder="Document Intelligence endpoint" />
                  <input v-model="markitdownOptions.docintel_key" class="input" placeholder="Document Intelligence key" type="password" />
                </div>
                <label class="flex items-center gap-2 text-sm"><input type="checkbox" v-model="markitdownOptions.use_llm_descriptions" /> Use LLM for image descriptions</label>
                <div v-if="hasLLMOptions" class="space-y-2 text-sm">
                  <select v-model="markitdownOptions.llm_provider" class="input">
                    <option>OpenAI</option>
                  </select>
                  <input v-model="markitdownOptions.llm_model" class="input" placeholder="LLM model (e.g., gpt-4o-mini)" />
                  <input v-model="markitdownOptions.llm_api_key" class="input" placeholder="LLM API key" type="password" />
                  <textarea v-model="markitdownOptions.llm_prompt" class="input" rows="3" placeholder="Custom LLM prompt (optional)"></textarea>
                </div>
                <label class="space-y-1 text-sm">
                  <span>Output format</span>
                  <select v-model="markitdownOptions.output_format" class="input">
                    <option>Markdown only</option>
                    <option>Markdown + manifest JSON</option>
                  </select>
                </label>
                <label class="space-y-1 text-sm">
                  <span>YouTube URL (optional)</span>
                  <input v-model="markitdownOptions.youtube_url" class="input" placeholder="https://youtube.com/..." />
                </label>
              </div>
            </div>

            <div class="flex flex-wrap gap-3 items-center">
              <button class="btn btn-primary" :disabled="isRunning" @click="startJob">Start Processing</button>
              <button class="btn btn-secondary" :disabled="!isRunning" @click="cancelJob">Cancel</button>
              <a
                v-if="hasDownload"
                class="btn btn-secondary"
                :href="downloadUrl()"
                download
              >
                Download ZIP
              </a>
              <div class="text-sm text-slate-600" v-if="jobStatus">
                Status: <span class="font-semibold">{{ jobStatus }}</span> — {{ statusMessage }}
              </div>
            </div>

            <div class="w-full bg-slate-100 rounded-full h-3 overflow-hidden">
              <div class="h-full bg-indigo-600" :style="{ width: `${Math.round(progress * 100)}%` }"></div>
            </div>
          </div>

          <div class="section-card">
            <h2 class="section-title">Logs</h2>
            <pre class="max-h-80 overflow-y-auto whitespace-pre-wrap text-xs bg-slate-50 border border-slate-200 rounded p-3">{{ logs || "Logs will appear here..." }}</pre>
          </div>
        </div>

        <div class="section-card space-y-4">
          <h2 class="section-title">Quick Preview</h2>
          <p class="text-sm text-slate-600">Preview the first page of a PDF or an image using the image-first pipeline.</p>
          <label class="btn btn-secondary w-full justify-center">
            Choose preview file
            <input type="file" class="hidden" @change="handlePreviewInput" />
          </label>
          <button class="btn btn-primary w-full" @click="runPreview">Run Preview</button>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <div class="text-sm font-semibold mb-1">Before</div>
              <div class="aspect-[4/5] rounded border border-slate-200 bg-slate-50 flex items-center justify-center overflow-hidden">
                <img v-if="previewBefore" :src="previewBefore" class="object-contain max-h-full" />
                <span v-else class="text-xs text-slate-500">Awaiting preview</span>
              </div>
            </div>
            <div>
              <div class="text-sm font-semibold mb-1">After</div>
              <div class="aspect-[4/5] rounded border border-slate-200 bg-slate-50 flex items-center justify-center overflow-hidden">
                <img v-if="previewAfter" :src="previewAfter" class="object-contain max-h-full" />
                <span v-else class="text-xs text-slate-500">Awaiting preview</span>
              </div>
            </div>
          </div>
          <p class="text-xs text-slate-600">{{ previewInfo }}</p>
        </div>
      </div>
    </section>

    <section v-if="activeTab === 'preview'" class="section-card space-y-4">
      <h2 class="section-title">Preview</h2>
      <p class="text-sm text-slate-600">Upload a file to see before/after for the image-first pipeline.</p>
      <div class="flex flex-wrap gap-2">
        <label class="btn btn-secondary cursor-pointer">
          Choose file
          <input type="file" class="hidden" @change="handlePreviewInput" />
        </label>
        <button class="btn btn-primary" @click="runPreview">Run Preview</button>
      </div>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div class="space-y-2">
          <div class="font-semibold text-sm">Before</div>
          <div class="rounded border border-slate-200 bg-slate-50 min-h-[200px] flex items-center justify-center overflow-hidden">
            <img v-if="previewBefore" :src="previewBefore" class="object-contain max-h-96" />
            <span v-else class="text-xs text-slate-500">Upload a file to preview</span>
          </div>
        </div>
        <div class="space-y-2">
          <div class="font-semibold text-sm">After</div>
          <div class="rounded border border-slate-200 bg-slate-50 min-h-[200px] flex items-center justify-center overflow-hidden">
            <img v-if="previewAfter" :src="previewAfter" class="object-contain max-h-96" />
            <span v-else class="text-xs text-slate-500">Processed output will appear here</span>
          </div>
        </div>
      </div>
      <p class="text-xs text-slate-600">{{ previewInfo }}</p>
    </section>
  </div>
</template>
