<script>
    import { chartAction } from '../lib/chartAction.js';

    let { widgetResults = [], widgetsMeta = [] } = $props();
</script>

{#if widgetsMeta.length === 0}
    <div class="glass-card rounded-xl p-12 text-center">
        <div class="p-4 bg-cat-surface0/60 rounded-2xl border border-cat-surface1/30 mb-5 inline-block">
            <svg class="text-cat-teal" xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24"
                fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <line x1="18" y1="20" x2="18" y2="10" />
                <line x1="12" y1="20" x2="12" y2="4" />
                <line x1="6" y1="20" x2="6" y2="14" />
            </svg>
        </div>
        <h3 class="text-base font-bold text-cat-text mb-1">Sin widgets</h3>
        <p class="text-cat-subtext0 text-sm">Abre el Builder para agregar gráficas y tablas a este reporte.</p>
    </div>
{:else}
    <div class="space-y-6">
        {#each widgetsMeta as meta, i}
            {@const result = widgetResults[i] || { columns: [], rows: [], total_rows: 0, warnings: [], chart_data: {} }}
            <div class="widget-card glass-card rounded-xl overflow-hidden">
                <!-- Widget Header -->
                <div class="flex items-center justify-between px-5 py-3 border-b border-cat-surface1/30">
                    <div class="flex items-center gap-3">
                        <div class="p-1.5 bg-cat-teal/10 rounded-lg text-cat-teal">
                            {#if meta.widget_type === 'table'}
                                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="3" y1="15" x2="21" y2="15"/><line x1="9" y1="3" x2="9" y2="21"/></svg>
                            {:else if meta.widget_type === 'bar' || meta.widget_type === 'histogram'}
                                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
                            {:else if meta.widget_type === 'pie'}
                                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.21 15.89A10 10 0 1 1 8 2.83"/><path d="M22 12A10 10 0 0 0 12 2v10z"/></svg>
                            {:else if meta.widget_type === 'scatter'}
                                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="7.5" cy="7.5" r="1.5"/><circle cx="18" cy="6" r="1.5"/><circle cx="11" cy="16" r="1.5"/><circle cx="16" cy="13" r="1.5"/><circle cx="6" cy="12" r="1.5"/></svg>
                            {/if}
                        </div>
                        <h3 class="font-bold text-cat-text text-sm">{meta.title}</h3>
                    </div>
                    <div class="flex items-center gap-3 text-[10px] text-cat-overlay0">
                        <span class="px-2 py-0.5 bg-cat-surface0/60 rounded font-bold uppercase tracking-wider">{meta.widget_type}</span>
                        <span>{result.total_rows} filas</span>
                        {#if result.excluded_invalid > 0}
                            <span class="text-cat-yellow">⚠ {result.excluded_invalid} excluidas</span>
                        {/if}
                    </div>
                </div>

                <!-- Widget Body -->
                <div class="p-5">
                    {#if result.warnings && result.warnings.length > 0}
                        <div class="mb-4 p-3 bg-cat-yellow/5 border border-cat-yellow/20 rounded-lg">
                            {#each result.warnings as warning}
                                <p class="text-cat-yellow text-xs flex items-center gap-1.5">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none"
                                        stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="shrink-0">
                                        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                                        <line x1="12" y1="9" x2="12" y2="13"/>
                                        <line x1="12" y1="17" x2="12.01" y2="17"/>
                                    </svg>
                                    {warning}
                                </p>
                            {/each}
                        </div>
                    {/if}

                    {#if meta.widget_type === 'table'}
                        <!-- Table widget -->
                        {#if result.columns.length > 0}
                            <div class="overflow-x-auto">
                                <table class="data-table w-full text-sm">
                                    <thead>
                                        <tr>
                                            {#each result.columns as col}
                                                <th class="px-3 py-2 text-left text-[11px] font-bold uppercase tracking-wider text-cat-subtext0 bg-cat-surface0/50 border-b border-cat-surface1/30">
                                                    {col.label}
                                                </th>
                                            {/each}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {#each result.rows as row, ri}
                                            <tr class="border-b border-cat-surface0/30 hover:bg-cat-surface0/20 transition-colors">
                                                {#each result.columns as col}
                                                    <td class="px-3 py-2 text-cat-text text-xs font-mono">
                                                        {row[col.key] ?? '—'}
                                                    </td>
                                                {/each}
                                            </tr>
                                        {/each}
                                    </tbody>
                                </table>
                            </div>
                        {:else}
                            <p class="text-cat-subtext0 text-sm text-center py-4">Sin datos</p>
                        {/if}
                    {:else}
                        <!-- Chart widget -->
                        {#if result.chart_data && result.chart_data.type}
                            <div class="chart-container" style="height: 320px;">
                                <canvas use:chartAction={{
                                    type: result.chart_data.type,
                                    data: result.chart_data.data,
                                }}></canvas>
                            </div>
                        {:else}
                            <p class="text-cat-subtext0 text-sm text-center py-8">Sin datos para graficar</p>
                        {/if}
                    {/if}
                </div>
            </div>
        {/each}
    </div>
{/if}
