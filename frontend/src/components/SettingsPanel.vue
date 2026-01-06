<script setup lang="ts">
import Card from "./ui/Card.vue";
import CardHeader from "./ui/CardHeader.vue";
import CardContent from "./ui/CardContent.vue";
import RadioGroup from "./ui/RadioGroup.vue";
import Checkbox from "./ui/Checkbox.vue";
import ToggleSwitch from "./ui/ToggleSwitch.vue";
import Slider from "./ui/Slider.vue";
import Button from "./ui/Button.vue";
import { computed, ref } from "vue";
import type { BackendMode } from "../composables/useSettings";

const props = defineProps<{
  backendMode: { value: BackendMode };
  imageSettings: Record<string, any>;
  markitdown: Record<string, any>;
}>();

const emit = defineEmits<{
  "update:backendMode": [value: BackendMode];
  resetImage: [];
}>();

const backendOptions = [
  { value: "Image-first (existing)", label: "Image-first", description: "Fast local preprocessing to clean PDFs and images." },
  { value: "MarkItDown (document-to-markdown)", label: "MarkItDown", description: "Document-to-markdown with optional plugins." },
];

const showAdvanced = ref(false);

const markitdownExpanded = computed(() => props.backendMode.value === "MarkItDown (document-to-markdown)");
</script>

<template>
  <Card>
    <CardHeader>
      <template #title>Settings</template>
      <template #description>Organized controls for each backend. Advanced options stay out of the way.</template>
    </CardHeader>
    <CardContent class="space-y-5">
      <div class="space-y-2">
        <p class="text-sm font-semibold text-[var(--text)]">Processing backend</p>
        <RadioGroup
          :options="backendOptions"
          name="backend-mode"
          :model-value="backendMode.value"
          @update:model-value="emit('update:backendMode', $event as BackendMode)"
        />
      </div>

      <div class="space-y-4">
        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-base font-semibold text-[var(--text)]">Image-first settings</h3>
            <p class="text-sm text-muted">Default pipeline controls organized by purpose.</p>
          </div>
          <Button variant="ghost" size="sm" @click="emit('resetImage')">Reset to defaults</Button>
        </div>

        <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div class="space-y-3">
            <p class="text-sm font-semibold text-[var(--text)]">Output quality</p>
            <label class="text-sm space-y-1">
              <span class="text-muted">PDF DPI</span>
              <select
                v-model.number="imageSettings.dpi"
                class="w-full rounded-md border border-[var(--border)] bg-white px-3 py-2 text-sm focus:border-primary focus:ring-primary"
              >
                <option :value="300">300</option>
                <option :value="400">400</option>
                <option :value="450">450</option>
                <option :value="600">600</option>
              </select>
            </label>
            <label class="text-sm space-y-1">
              <span class="text-muted">Color mode</span>
              <select
                v-model="imageSettings.color_mode"
                class="w-full rounded-md border border-[var(--border)] bg-white px-3 py-2 text-sm focus:border-primary focus:ring-primary"
              >
                <option>Grayscale</option>
                <option>Color</option>
              </select>
            </label>
          </div>

          <div class="space-y-3">
            <p class="text-sm font-semibold text-[var(--text)]">Cleanup</p>
            <Checkbox v-model="imageSettings.auto_orient" label="Auto-orient pages" />
            <Checkbox v-model="imageSettings.deskew" label="Deskew" />
            <Slider
              v-model="imageSettings.deskew_sensitivity"
              :min="0"
              :max="1"
              :step="0.05"
              label="Deskew sensitivity"
              helper="Higher values handle heavier skew but may distort lightly skewed scans."
            />
            <Checkbox v-model="imageSettings.trim" label="Trim whitespace" />
          </div>

          <div class="space-y-3">
            <p class="text-sm font-semibold text-[var(--text)]">Contrast & tone</p>
            <Checkbox v-model="imageSettings.contrast_stretch" label="Contrast stretch" />
            <label class="text-sm space-y-1">
              <span class="text-muted">Contrast percentile</span>
              <input
                v-model.number="imageSettings.contrast_percent"
                type="number"
                min="0.2"
                max="2"
                step="0.1"
                class="w-full rounded-md border border-[var(--border)] bg-white px-3 py-2 text-sm focus:border-primary focus:ring-primary"
              />
              <span class="text-xs text-muted">Adjust percentile used for stretching; 0.5 works for most scans.</span>
            </label>
          </div>

          <div class="space-y-3">
            <div class="flex items-center justify-between">
              <p class="text-sm font-semibold text-[var(--text)]">Advanced</p>
              <button class="text-sm text-primary underline" @click="showAdvanced = !showAdvanced">
                {{ showAdvanced ? "Hide" : "Show" }}
              </button>
            </div>
            <transition name="fade">
              <div v-if="showAdvanced" class="space-y-2">
                <Checkbox v-model="imageSettings.adaptive_threshold" label="Adaptive threshold" />
                <p class="text-xs text-muted">Adaptive threshold can make text pop but may over-sharpen photos.</p>
                <label class="text-sm space-y-1">
                  <span class="text-muted">Processing mode</span>
                  <select
                    v-model="imageSettings.mode"
                    class="w-full rounded-md border border-[var(--border)] bg-white px-3 py-2 text-sm focus:border-primary focus:ring-primary"
                  >
                    <option>Balanced</option>
                    <option>Aggressive for scans</option>
                  </select>
                </label>
              </div>
            </transition>
          </div>
        </div>
      </div>

      <div class="space-y-3">
        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-base font-semibold text-[var(--text)]">MarkItDown settings</h3>
            <p class="text-sm text-muted">Progressive disclosure keeps sensitive fields hidden.</p>
          </div>
        </div>
        <transition name="fade">
          <div v-if="markitdownExpanded" class="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div class="space-y-2">
              <ToggleSwitch v-model="markitdown.enable_plugins" label="Enable plugins" />
              <ToggleSwitch v-model="markitdown.use_docintel" label="Azure Document Intelligence" />
              <div v-if="markitdown.use_docintel" class="space-y-2 text-sm">
                <input
                  v-model="markitdown.docintel_endpoint"
                  class="w-full rounded-md border border-[var(--border)] px-3 py-2 text-sm focus:ring-primary focus:border-primary"
                  placeholder="Document Intelligence endpoint"
                />
                <div class="space-y-1">
                  <div class="flex items-center justify-between text-xs text-muted">
                    <span>Key</span>
                    <label class="flex items-center gap-2">
                      <input type="checkbox" v-model="markitdown.persist_api_keys" class="rounded border-[var(--border)] text-primary focus:ring-primary" />
                      <span>Remember locally</span>
                    </label>
                  </div>
                  <input
                    v-model="markitdown.docintel_key"
                    type="password"
                    class="w-full rounded-md border border-[var(--border)] px-3 py-2 text-sm focus:ring-primary focus:border-primary"
                    placeholder="Document Intelligence key"
                  />
                  <p class="text-xs text-muted">Keys stay in memory; enable “Remember” to store locally.</p>
                </div>
              </div>
              <label class="text-sm space-y-1">
                <span class="text-muted">Output format</span>
                <select
                  v-model="markitdown.output_format"
                  class="w-full rounded-md border border-[var(--border)] bg-white px-3 py-2 text-sm focus:border-primary focus:ring-primary"
                >
                  <option>Markdown only</option>
                  <option>Markdown + manifest JSON</option>
                </select>
              </label>
              <label class="text-sm space-y-1">
                <span class="text-muted">YouTube URL (optional)</span>
                <input
                  v-model="markitdown.youtube_url"
                  class="w-full rounded-md border border-[var(--border)] px-3 py-2 text-sm focus:ring-primary focus:border-primary"
                  placeholder="https://youtube.com/..."
                />
              </label>
            </div>
            <div class="space-y-2">
              <ToggleSwitch v-model="markitdown.use_llm_descriptions" label="LLM image descriptions" />
              <div v-if="markitdown.use_llm_descriptions" class="space-y-2 text-sm">
                <label class="space-y-1">
                  <span class="text-muted">Provider</span>
                  <select
                    v-model="markitdown.llm_provider"
                    class="w-full rounded-md border border-[var(--border)] bg-white px-3 py-2 text-sm focus:border-primary focus:ring-primary"
                  >
                    <option>OpenAI</option>
                  </select>
                </label>
                <input
                  v-model="markitdown.llm_model"
                  class="w-full rounded-md border border-[var(--border)] px-3 py-2 text-sm focus:ring-primary focus:border-primary"
                  placeholder="LLM model (e.g., gpt-4o-mini)"
                />
                <div class="space-y-1">
                  <span class="text-xs text-muted">API key</span>
                  <input
                    v-model="markitdown.llm_api_key"
                    type="password"
                    class="w-full rounded-md border border-[var(--border)] px-3 py-2 text-sm focus:ring-primary focus:border-primary"
                    placeholder="LLM API key"
                  />
                  <p class="text-xs text-muted">Keys are not persisted unless you enable “Remember locally”.</p>
                </div>
                <textarea
                  v-model="markitdown.llm_prompt"
                  rows="3"
                  class="w-full rounded-md border border-[var(--border)] px-3 py-2 text-sm focus:ring-primary focus:border-primary"
                  placeholder="Custom LLM prompt (optional)"
                />
              </div>
            </div>
          </div>
        </transition>
      </div>
    </CardContent>
  </Card>
</template>
