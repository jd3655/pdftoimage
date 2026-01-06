import { reactive, watch } from "vue";

export type BackendMode = "Image-first (existing)" | "MarkItDown (document-to-markdown)";

const STORAGE_KEY = "pdftoimage-settings-v1";

const defaultImageSettings = {
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
};

const defaultMarkitdown = {
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
  persist_api_keys: false,
};

export function useSettings() {
  const saved = localStorage.getItem(STORAGE_KEY);
  const parsed = saved ? JSON.parse(saved) : {};

  const backendMode = reactive<{ value: BackendMode }>({
    value: parsed.backendMode || "Image-first (existing)",
  });

  const imageSettings = reactive({ ...defaultImageSettings, ...(parsed.imageSettings || {}) });
  const markitdown = reactive({ ...defaultMarkitdown, ...(parsed.markitdown || {}) });

  const persist = () => {
    const data = {
      backendMode: backendMode.value,
      imageSettings,
      markitdown: {
        ...markitdown,
        ...(markitdown.persist_api_keys
          ? {}
          : { docintel_key: "", llm_api_key: "" }),
      },
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  };

  watch(
    () => ({ ...imageSettings, ...markitdown, backendMode: backendMode.value }),
    persist,
    { deep: true },
  );

  const resetImage = () => Object.assign(imageSettings, defaultImageSettings);
  const resetMarkitdown = () => Object.assign(markitdown, defaultMarkitdown);

  return { backendMode, imageSettings, markitdown, resetImage, resetMarkitdown };
}
