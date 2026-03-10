<script>
  /**
   * Dashboard.svelte — Placeholder Svelte component for the dashboard page.
   *
   * Mount point: <div id="svelte-dashboard"></div> in dashboard.html
   *
   * This component is intentionally minimal. Replace / expand it with reactive
   * widgets (charts, live stats, file tables, etc.) as needed.
   */

  let message = $state('Svelte is running inside Django!')
</script>

<div class="glass-card rounded-2xl p-6 text-cat-text">
  <p class="text-cat-mauve font-bold text-lg">{message}</p>
  <p class="text-cat-subtext0 text-sm mt-1">
    Replace this component with your reactive dashboard widgets.
  </p>
</div>
