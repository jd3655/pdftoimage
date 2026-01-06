import { computed, ref } from "vue";
import { useToast } from "./useToast";

export function useUploads() {
  const files = ref<File[]>([]);
  const zipFile = ref<File | null>(null);
  const { add } = useToast();

  const addFiles = (incoming: File[]) => {
    files.value = [...files.value, ...incoming];
    if (!incoming.length) {
      add({ title: "No files added", description: "Choose PDF or image files to begin." });
    }
  };

  const addZip = (file: File | null) => {
    zipFile.value = file;
  };

  const removeFile = (index: number) => {
    files.value.splice(index, 1);
  };

  const clearAll = () => {
    files.value = [];
    zipFile.value = null;
  };

  const canStart = computed(() => files.value.length > 0 || zipFile.value !== null);

  const handleDrop = (event: DragEvent) => {
    event.preventDefault();
    if (!event.dataTransfer) return;
    const dropped = Array.from(event.dataTransfer.files || []);
    const zips = dropped.filter((f) => f.name.toLowerCase().endsWith(".zip"));
    const others = dropped.filter((f) => !f.name.toLowerCase().endsWith(".zip"));
    if (others.length) addFiles(others);
    if (zips.length) addZip(zips[0]);
  };

  const handleFileInput = (event: Event) => {
    const target = event.target as HTMLInputElement;
    if (target.files) addFiles(Array.from(target.files));
  };

  const handleZipInput = (event: Event) => {
    const target = event.target as HTMLInputElement;
    if (target.files && target.files.length > 0) addZip(target.files[0]);
  };

  const formattedSize = (bytes: number) => {
    if (!bytes) return "0 B";
    const units = ["B", "KB", "MB", "GB"];
    const idx = Math.floor(Math.log(bytes) / Math.log(1024));
    const size = bytes / Math.pow(1024, idx);
    return `${size.toFixed(1)} ${units[idx]}`;
  };

  return {
    files,
    zipFile,
    addFiles,
    addZip,
    removeFile,
    clearAll,
    canStart,
    handleDrop,
    handleFileInput,
    handleZipInput,
    formattedSize,
  };
}
