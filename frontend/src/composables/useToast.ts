import { ref } from "vue";

export interface ToastMessage {
  id: number;
  title: string;
  description?: string;
  variant?: "success" | "error" | "info";
}

const toasts = ref<ToastMessage[]>([]);
let counter = 0;

export function useToast() {
  const add = (toast: Omit<ToastMessage, "id">) => {
    const id = ++counter;
    toasts.value.push({ id, ...toast });
    setTimeout(() => dismiss(id), 4500);
  };

  const dismiss = (id: number) => {
    toasts.value = toasts.value.filter((t) => t.id !== id);
  };

  return { toasts, add, dismiss };
}
