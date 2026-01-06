<template>
  <div class="flex items-start justify-between gap-3 pb-3 border-b border-[var(--border)] mb-4">
    <div>
      <h2 class="text-lg font-semibold text-[var(--text)]"><slot name="title" /></h2>
      <p class="text-sm text-muted mt-1"><slot name="description" /></p>
    </div>
    <slot name="action" />
  </div>
</template>
