import axios from "axios";
import { ref } from "vue";
import type { BackendMode } from "./useSettings";
import { useToast } from "./useToast";

export function usePreview() {
  const before = ref<string | null>(null);
  const after = ref<string | null>(null);
  const info = ref<string>("Upload a file to preview the image-first pipeline.");
  const loading = ref(false);
  const { add } = useToast();

  const runPreview = async (file: File | null, backendMode: BackendMode, imageSettings: Record<string, any>) => {
    if (backendMode !== "Image-first (existing)") {
      info.value = "Preview is only available for the Image-first pipeline.";
      return;
    }
    if (!file) {
      info.value = "Add a file to preview.";
      return;
    }
    const form = new FormData();
    form.append("file", file);
    Object.entries(imageSettings).forEach(([key, value]) => form.append(key, String(value)));
    loading.value = true;
    try {
      const { data } = await axios.post("/api/preview", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      before.value = `data:image/png;base64,${data.before_png_b64}`;
      after.value = `data:image/png;base64,${data.after_png_b64}`;
      info.value = data.info;
      add({ title: "Preview generated", variant: "success" });
    } catch (err: any) {
      info.value = err?.response?.data?.detail || "Failed to generate preview.";
      add({ title: "Preview failed", description: info.value, variant: "error" });
    } finally {
      loading.value = false;
    }
  };

  return { before, after, info, loading, runPreview };
}
