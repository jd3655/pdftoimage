<script setup lang="ts">
import Card from "./ui/Card.vue";
import CardHeader from "./ui/CardHeader.vue";
import CardContent from "./ui/CardContent.vue";
import Button from "./ui/Button.vue";
import { ZoomIn, ZoomOut, ImageOff } from "lucide-vue-next";
import { ref } from "vue";

const props = defineProps<{
  before: string | null;
  after: string | null;
  info: string;
  loading: boolean;
  backendMode: string;
}>();

const emit = defineEmits<{
  select: [event: Event];
  preview: [];
}>();

const scale = ref(1);
const adjustScale = (delta: number) => {
  scale.value = Math.min(2, Math.max(0.5, scale.value + delta));
};
</script>

<template>
  <Card>
    <CardHeader>
      <template #title>Preview</template>
      <template #description>Generate a before/after view using the Image-first pipeline.</template>
      <template #action>
        <span class="text-xs text-muted">Scale: {{ Math.round(scale * 100) }}%</span>
      </template>
    </CardHeader>
    <CardContent class="space-y-4">
      <div class="flex flex-wrap items-center gap-2">
        <label class="flex items-center gap-2 rounded-lg border border-[var(--border)] bg-white px-4 py-2 text-sm font-semibold cursor-pointer focus-ring">
          Choose file
          <input type="file" class="hidden" @change="emit('select', $event)" />
        </label>
        <Button :loading="loading" @click="emit('preview')">Run preview</Button>
        <div class="flex items-center gap-1">
          <Button variant="ghost" size="sm" @click="adjustScale(-0.1)">
            <ZoomOut class="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="sm" @click="adjustScale(0.1)">
            <ZoomIn class="h-4 w-4" />
          </Button>
        </div>
      </div>
      <div
        v-if="backendMode !== 'Image-first (existing)'"
        class="flex items-center gap-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800"
      >
        <ImageOff class="h-4 w-4" />
        Preview is only available for Image-first.
      </div>
      <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div>
          <p class="text-sm font-semibold text-[var(--text)] mb-2">Before</p>
          <div class="aspect-[4/5] overflow-hidden rounded-lg border border-[var(--border)] bg-slate-50 flex items-center justify-center">
            <img v-if="before" :src="before" class="h-full w-full object-contain" :style="{ transform: `scale(${scale})` }" />
            <span v-else class="text-xs text-muted">Upload to preview</span>
          </div>
        </div>
        <div>
          <p class="text-sm font-semibold text-[var(--text)] mb-2">After</p>
          <div class="aspect-[4/5] overflow-hidden rounded-lg border border-[var(--border)] bg-slate-50 flex items-center justify-center">
            <img v-if="after" :src="after" class="h-full w-full object-contain" :style="{ transform: `scale(${scale})` }" />
            <span v-else class="text-xs text-muted">Processed image will appear here</span>
          </div>
        </div>
      </div>
      <p class="text-xs text-muted">{{ info }}</p>
    </CardContent>
  </Card>
</template>
