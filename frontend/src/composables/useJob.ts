import axios from "axios";
import { computed, reactive, ref } from "vue";
import { useToast } from "./useToast";
import type { BackendMode } from "./useSettings";

export type JobStatus = "queued" | "running" | "done" | "error" | "cancelled" | null;

interface JobResponse {
  job_id: string;
  status: Exclude<JobStatus, null>;
  progress: number;
  message: string;
  error: string | null;
  has_download: boolean;
  logs_tail: string;
}

export function useJob() {
  const jobId = ref<string | null>(null);
  const status = ref<JobStatus>(null);
  const progress = ref(0);
  const message = ref("");
  const hasDownload = ref(false);
  const logs = ref("");
  const error = ref<string | null>(null);
  const startedAt = ref<number | null>(null);
  const polling = ref<number | undefined>(undefined);
  const { add } = useToast();

  const running = computed(() => status.value === "running" || status.value === "queued");
  const elapsedSeconds = computed(() => {
    if (!startedAt.value) return 0;
    return Math.floor((Date.now() - startedAt.value) / 1000);
  });

  const start = async (
    backendMode: BackendMode,
    imageSettings: Record<string, any>,
    markitdown: Record<string, any>,
    files: File[],
    zipFile: File | null,
  ) => {
    if (running.value) return;
    if (files.length === 0 && !zipFile) {
      add({ title: "Add files to start", description: "Upload at least one file or a ZIP." });
      return;
    }
    const form = new FormData();
    files.forEach((file) => form.append("files", file));
    if (zipFile) form.append("zip_file", zipFile);
    form.append("backend_mode", backendMode);
    Object.entries(imageSettings).forEach(([key, value]) => form.append(key, String(value)));
    Object.entries(markitdown).forEach(([key, value]) => {
      if (key === "persist_api_keys") return;
      form.append(key, String(value));
    });

    status.value = "queued";
    progress.value = 0;
    message.value = "Submitting job...";
    logs.value = "";
    hasDownload.value = false;
    error.value = null;
    startedAt.value = Date.now();

    try {
      const { data } = await axios.post<{ job_id: string }>("/api/jobs", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      jobId.value = data.job_id;
      message.value = "Job queued";
      beginPolling();
    } catch (err: any) {
      status.value = "error";
      message.value = err?.response?.data?.detail || "Failed to start job.";
      error.value = message.value;
      add({ title: "Job failed to start", description: message.value, variant: "error" });
    }
  };

  const beginPolling = () => {
    stopPolling();
    polling.value = window.setInterval(async () => {
      if (!jobId.value) return;
      try {
        const { data } = await axios.get<JobResponse>(`/api/jobs/${jobId.value}`);
        status.value = data.status;
        progress.value = data.progress;
        message.value = data.message || data.status;
        logs.value = data.logs_tail || "";
        hasDownload.value = data.has_download;
        if (data.error) error.value = data.error;
        if (["done", "error", "cancelled"].includes(data.status)) {
          stopPolling();
          if (data.status === "done") {
            add({ title: "Processing completed", variant: "success" });
          } else if (data.status === "error") {
            add({ title: "Processing error", description: data.error || "Unknown error", variant: "error" });
          }
        }
      } catch (err) {
        stopPolling();
        status.value = "error";
        message.value = "Failed to poll job status.";
      }
    }, 600);
  };

  const stopPolling = () => {
    if (polling.value) {
      clearInterval(polling.value);
      polling.value = undefined;
    }
  };

  const cancel = async () => {
    if (!jobId.value) return;
    try {
      await axios.post(`/api/jobs/${jobId.value}/cancel`);
      status.value = "cancelled";
      message.value = "Cancellation requested";
      add({ title: "Job cancelled", variant: "info" });
    } catch (err) {
      add({ title: "Cancellation failed", variant: "error" });
    }
  };

  const downloadUrl = computed(() => (jobId.value ? `/api/jobs/${jobId.value}/download` : "#"));

  return {
    jobId,
    status,
    progress,
    message,
    logs,
    hasDownload,
    error,
    running,
    elapsedSeconds,
    start,
    cancel,
    downloadUrl,
    stopPolling,
  };
}
