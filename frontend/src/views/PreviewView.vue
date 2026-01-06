<script setup lang="ts">
import PreviewPanel from "../components/PreviewPanel.vue";
import Card from "../components/ui/Card.vue";
import CardHeader from "../components/ui/CardHeader.vue";
import CardContent from "../components/ui/CardContent.vue";

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
</script>

<template>
  <div class="space-y-4">
    <PreviewPanel
      :before="before"
      :after="after"
      :info="info"
      :loading="loading"
      :backend-mode="backendMode"
      @select="emit('select', $event)"
      @preview="emit('preview')"
    />
    <Card>
      <CardHeader>
        <template #title>Tips</template>
        <template #description>Preview is ideal for single pages; run the job for batch output.</template>
      </CardHeader>
      <CardContent>
        <ul class="list-disc pl-5 text-sm text-[var(--text)] space-y-1">
          <li>Deskew sensitivity and contrast sliders update preview results.</li>
          <li>Use zoom controls to inspect fine details without re-running.</li>
          <li>MarkItDown mode skips preview to keep flows predictable.</li>
        </ul>
      </CardContent>
    </Card>
  </div>
</template>
