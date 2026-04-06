<script>
    import { chartAction } from '../lib/chartAction.js';

    let {
        csrf = '',
        reportPk = 0,
        reportName = '',
        datasetName = '',
        templateName = '',
        fields = [],
        widgets: initialWidgets = [],
        filters: initialFilters = [],
    } = $props();

    // ─── State ────────────────────────────────────────────────────
    let widgets = $state(initialWidgets.map(w => ({ ...w })));
    let globalFilters = $state(initialFilters.map(f => ({ ...f })));
    let selectedWidgetIdx = $state(null);
    let saveStatus = $state('saved'); // saved | saving | error
    let previewResult = $state(null);
    let previewLoading = $state(false);
    let previewError = $state(null);

    // Editing state for global filters
    let newFilterField = $state(fields.length > 0 ? fields[0].id : 0);
    let newFilterOperator = $state('equals');
    let newFilterValue = $state('');

    let selectedWidget = $derived(selectedWidgetIdx !== null ? widgets[selectedWidgetIdx] : null);

    // Widget type metadata
    const WIDGET_TYPES = [
        { value: 'table', label: 'Tabla', icon: '⊞', desc: 'Tabla de datos con filas y columnas' },
        { value: 'bar', label: 'Barras', icon: '▊', desc: 'Gráfico de barras verticales' },
        { value: 'pie', label: 'Pastel', icon: '◔', desc: 'Gráfico circular de proporciones' },
        { value: 'scatter', label: 'Dispersión', icon: '⊙', desc: 'Nube de puntos X/Y' },
        { value: 'histogram', label: 'Histograma', icon: '▋', desc: 'Distribución de frecuencias' },
    ];

    const AGG_LABELS = {
        count: 'Contar', distinct_count: 'Contar únicos', sum: 'Sumar',
        avg: 'Promedio', min: 'Mínimo', max: 'Máximo',
    };

    const GROUP_LABELS = {
        raw: 'Valor Exacto', day: 'Por día', week: 'Por semana',
        month: 'Por mes', year: 'Por año',
    };

    const OP_LABELS = {
        equals: 'Igual a', not_equals: 'Diferente de', contains: 'Contiene',
        not_contains: 'No contiene', in_list: 'En lista', gt: 'Mayor que',
        gte: 'Mayor o igual', lt: 'Menor que', lte: 'Menor o igual',
        between: 'Entre', is_null: 'Es vacío', is_not_null: 'No es vacío',
    };

    function getFieldById(id) {
        return fields.find(f => f.id === id) || null;
    }

    // ─── API Helpers ──────────────────────────────────────────────
    async function apiCall(url, method, body) {
        saveStatus = 'saving';
        try {
            const res = await fetch(url, {
                method,
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrf,
                },
                body: body ? JSON.stringify(body) : undefined,
            });
            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.error || `HTTP ${res.status}`);
            }
            saveStatus = 'saved';
            return await res.json();
        } catch (e) {
            saveStatus = 'error';
            console.error('API error:', e);
            throw e;
        }
    }

    // ─── Widget CRUD ──────────────────────────────────────────────
    async function addWidget() {
        const body = {
            title: `Widget ${widgets.length + 1}`,
            widget_type: 'table',
            config_json: { dimensions: [], metrics: [], filters: [], sort: [], options: {} },
            sort_order: widgets.length,
        };
        const result = await apiCall(`/reports/${reportPk}/api/widgets/`, 'POST', body);
        widgets = [...widgets, result];
        selectedWidgetIdx = widgets.length - 1;
    }

    async function saveWidget(idx) {
        const w = widgets[idx];
        if (!w || !w.id) return;
        await apiCall(`/reports/${reportPk}/api/widgets/${w.id}/`, 'PUT', {
            title: w.title,
            widget_type: w.widget_type,
            config_json: w.config_json,
            sort_order: w.sort_order,
        });
    }

    async function deleteWidget(idx) {
        const w = widgets[idx];
        if (!w || !w.id) return;
        await apiCall(`/reports/${reportPk}/api/widgets/${w.id}/`, 'DELETE');
        widgets = widgets.filter((_, i) => i !== idx);
        if (selectedWidgetIdx === idx) {
            selectedWidgetIdx = null;
            previewResult = null;
        } else if (selectedWidgetIdx !== null && selectedWidgetIdx > idx) {
            selectedWidgetIdx--;
        }
    }

    async function moveWidget(idx, direction) {
        const newIdx = idx + direction;
        if (newIdx < 0 || newIdx >= widgets.length) return;
        const temp = widgets[idx];
        widgets[idx] = widgets[newIdx];
        widgets[newIdx] = temp;
        // Update sort orders
        widgets[idx].sort_order = idx;
        widgets[newIdx].sort_order = newIdx;
        widgets = [...widgets];
        if (selectedWidgetIdx === idx) selectedWidgetIdx = newIdx;
        else if (selectedWidgetIdx === newIdx) selectedWidgetIdx = idx;
        await saveWidget(idx);
        await saveWidget(newIdx);
    }

    // ─── Dimension/Metric Editing ─────────────────────────────────
    function addDimension() {
        if (!selectedWidget) return;
        const available = fields.filter(f =>
            !selectedWidget.config_json.dimensions?.some(d => d.field_ref === f.id)
        );
        if (available.length === 0) return;
        const field = available[0];
        if (!selectedWidget.config_json.dimensions) selectedWidget.config_json.dimensions = [];
        selectedWidget.config_json.dimensions = [...selectedWidget.config_json.dimensions, {
            field_kind: 'template_column',
            field_ref: field.id,
            group_by: 'raw',
        }];
        widgets = [...widgets];
    }

    function removeDimension(dimIdx) {
        if (!selectedWidget) return;
        selectedWidget.config_json.dimensions = selectedWidget.config_json.dimensions.filter((_, i) => i !== dimIdx);
        widgets = [...widgets];
    }

    function addMetric() {
        if (!selectedWidget) return;
        const available = fields;
        if (available.length === 0) return;
        const field = available[0];
        if (!selectedWidget.config_json.metrics) selectedWidget.config_json.metrics = [];
        selectedWidget.config_json.metrics = [...selectedWidget.config_json.metrics, {
            field_kind: 'template_column',
            field_ref: field.id,
            aggregation: field.is_numeric ? 'sum' : 'count',
            label: `${AGG_LABELS[field.is_numeric ? 'sum' : 'count']} de ${field.name}`,
        }];
        widgets = [...widgets];
    }

    function removeMetric(metIdx) {
        if (!selectedWidget) return;
        selectedWidget.config_json.metrics = selectedWidget.config_json.metrics.filter((_, i) => i !== metIdx);
        widgets = [...widgets];
    }

    // ─── Preview ──────────────────────────────────────────────────
    async function loadPreview() {
        if (!selectedWidget) return;
        previewLoading = true;
        previewError = null;
        previewResult = null;

        try {
            const res = await fetch(`/reports/${reportPk}/api/preview/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrf,
                },
                body: JSON.stringify({
                    widget_type: selectedWidget.widget_type,
                    config_json: selectedWidget.config_json,
                }),
            });

            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                previewError = err.errors ? err.errors.join('\n') : `Error ${res.status}`;
                return;
            }

            previewResult = await res.json();
        } catch (e) {
            previewError = e.message;
        } finally {
            previewLoading = false;
        }
    }

    // ─── Global Filter CRUD ───────────────────────────────────────
    async function addGlobalFilter() {
        const body = {
            field_kind: 'template_column',
            field_ref: newFilterField,
            operator: newFilterOperator,
            value_json: { value: newFilterValue },
            sort_order: globalFilters.length,
        };
        const result = await apiCall(`/reports/${reportPk}/api/filters/`, 'POST', body);
        globalFilters = [...globalFilters, result];
        newFilterValue = '';
    }

    async function deleteGlobalFilter(idx) {
        const f = globalFilters[idx];
        if (!f || !f.id) return;
        await apiCall(`/reports/${reportPk}/api/filters/${f.id}/`, 'DELETE');
        globalFilters = globalFilters.filter((_, i) => i !== idx);
    }

    // Debounced auto-save & auto-preview
    let saveTimer;
    function scheduleSave() {
        clearTimeout(saveTimer);
        saveTimer = setTimeout(() => {
            if (selectedWidgetIdx !== null) {
                saveWidget(selectedWidgetIdx).then(loadPreview);
            }
        }, 800);
    }
</script>

<div class="builder-layout">
    <!-- ─── Left: Widget List ──────────────────────────────────── -->
    <aside class="builder-sidebar">
        <div class="flex items-center justify-between mb-4">
            <h3 class="text-sm font-bold text-cat-text uppercase tracking-wider flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none"
                    stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
                    <rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>
                </svg>
                Widgets
            </h3>
            <span class="text-[10px] text-cat-overlay0 px-2 py-0.5 bg-cat-surface0/60 rounded font-bold">
                {widgets.length}
            </span>
        </div>

        <div class="space-y-2 mb-4">
            {#each widgets as w, i}
                <button
                    class="w-full text-left px-3 py-2.5 rounded-lg text-sm transition-all flex items-center gap-2 group
                        {selectedWidgetIdx === i
                            ? 'bg-cat-mauve/15 border border-cat-mauve/30 text-cat-text'
                            : 'bg-cat-surface0/30 border border-transparent text-cat-subtext0 hover:bg-cat-surface0/60 hover:text-cat-text'}"
                    onclick={() => { selectedWidgetIdx = i; previewResult = null; previewError = null; }}
                >
                    <span class="text-xs opacity-60">{i + 1}.</span>
                    <span class="truncate flex-1 font-medium">{w.title}</span>
                    <span class="text-[9px] uppercase tracking-wider opacity-60 font-bold">{w.widget_type}</span>
                </button>

                {#if selectedWidgetIdx === i}
                    <div class="flex items-center gap-1 px-2">
                        <button class="p-1 text-cat-overlay0 hover:text-cat-text rounded transition-colors"
                            onclick={() => moveWidget(i, -1)} disabled={i === 0} title="Subir">↑</button>
                        <button class="p-1 text-cat-overlay0 hover:text-cat-text rounded transition-colors"
                            onclick={() => moveWidget(i, 1)} disabled={i === widgets.length - 1} title="Bajar">↓</button>
                        <div class="flex-1"></div>
                        <button class="p-1 text-cat-red/60 hover:text-cat-red rounded transition-colors text-xs"
                            onclick={() => deleteWidget(i)} title="Eliminar">✕</button>
                    </div>
                {/if}
            {/each}
        </div>

        <button onclick={addWidget}
            class="w-full px-3 py-2.5 rounded-lg text-sm font-bold bg-cat-green/10 text-cat-green border border-cat-green/20 hover:bg-cat-green/20 transition-all flex items-center justify-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none"
                stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
            Agregar Widget
        </button>

        <!-- Save Status -->
        <div class="mt-4 flex items-center gap-2 text-[10px]">
            {#if saveStatus === 'saved'}
                <span class="w-2 h-2 rounded-full bg-cat-green"></span>
                <span class="text-cat-green">Guardado</span>
            {:else if saveStatus === 'saving'}
                <span class="w-2 h-2 rounded-full bg-cat-yellow animate-pulse"></span>
                <span class="text-cat-yellow">Guardando...</span>
            {:else}
                <span class="w-2 h-2 rounded-full bg-cat-red"></span>
                <span class="text-cat-red">Error al guardar</span>
            {/if}
        </div>

        <!-- Report Info -->
        <div class="mt-6 pt-4 border-t border-cat-surface1/30">
            <p class="text-[10px] text-cat-overlay0 uppercase tracking-wider font-bold mb-2">Reporte</p>
            <p class="text-xs text-cat-text font-bold">{reportName}</p>
            <p class="text-[10px] text-cat-overlay0 mt-1">{datasetName} · {templateName}</p>
        </div>
    </aside>

    <!-- ─── Right: Main Content ───────────────────────────────── -->
    <div class="builder-main flex flex-col gap-5">
        <header class="flex items-center justify-end">
            <a href="{"/reports/" + reportPk + "/"}" class="px-4 py-2 bg-gradient-to-r from-cat-mauve to-cat-pink text-cat-base font-bold rounded-lg transition-transform hover:scale-105 active:scale-95 shadow hover:shadow-cat-mauve/20 flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
                Ver Reporte
            </a>
        </header>

        {#if selectedWidget}
            <div class="builder-editor-grid">
                <!-- Config Column -->
                <div class="flex flex-col gap-5">
            <!-- Widget Title -->
            <div class="glass-card rounded-xl p-5 mb-5">
                <div class="flex items-center gap-3 mb-4">
                    <input type="text" bind:value={selectedWidget.title}
                        oninput={scheduleSave}
                        class="flex-1 bg-transparent border-b border-cat-surface1 focus:border-cat-mauve text-cat-text font-bold text-lg outline-none pb-1 transition-colors"
                        placeholder="Título del widget"
                    />
                </div>

                <!-- Widget Type Selector -->
                <p class="text-[10px] text-cat-overlay0 uppercase tracking-wider font-bold mb-3">Tipo de Widget</p>
                <div class="grid grid-cols-5 gap-2">
                    {#each WIDGET_TYPES as wt}
                        <button
                            class="widget-type-btn px-3 py-3 rounded-lg text-center transition-all border
                                {selectedWidget.widget_type === wt.value
                                    ? 'bg-cat-mauve/15 border-cat-mauve/40 text-cat-mauve'
                                    : 'bg-cat-surface0/30 border-transparent text-cat-subtext0 hover:bg-cat-surface0/60 hover:text-cat-text'}"
                            onclick={() => {
                                selectedWidget.widget_type = wt.value;
                                widgets = [...widgets];
                                scheduleSave();
                            }}
                        >
                            <span class="text-lg block mb-1">{wt.icon}</span>
                            <span class="text-[10px] font-bold block">{wt.label}</span>
                        </button>
                    {/each}
                </div>
            </div>

            <!-- Dimensions -->
            <div class="glass-card rounded-xl p-5 mb-5">
                <div class="flex items-center justify-between mb-3">
                    <p class="text-[10px] text-cat-overlay0 uppercase tracking-wider font-bold">Dimensiones (Agrupar por)</p>
                    <button onclick={addDimension}
                        class="text-[10px] font-bold text-cat-blue hover:text-cat-blue/80 transition-colors">+ Agregar</button>
                </div>
                {#if selectedWidget.config_json?.dimensions?.length > 0}
                    <div class="space-y-2">
                        {#each selectedWidget.config_json.dimensions as dim, di}
                            {@const field = getFieldById(dim.field_ref)}
                            <div class="flex items-center gap-2 p-2 bg-cat-surface0/30 rounded-lg">
                                <select bind:value={dim.field_ref}
                                    onchange={() => { widgets = [...widgets]; scheduleSave(); }}
                                    class="flex-1 bg-transparent text-cat-text text-xs outline-none cursor-pointer">
                                    {#each fields as f}
                                        <option value={f.id}>{f.name} ({f.data_type_display})</option>
                                    {/each}
                                </select>
                                <select bind:value={dim.group_by}
                                    onchange={() => { widgets = [...widgets]; scheduleSave(); }}
                                    class="bg-transparent text-cat-text text-xs outline-none cursor-pointer">
                                    {#each (field ? field.group_bys : ['raw']) as gb}
                                        <option value={gb}>{GROUP_LABELS[gb] || gb}</option>
                                    {/each}
                                </select>
                                <button onclick={() => { removeDimension(di); scheduleSave(); }}
                                    class="text-cat-red/60 hover:text-cat-red p-1 transition-colors text-xs">✕</button>
                            </div>
                        {/each}
                    </div>
                {:else}
                    <p class="text-cat-overlay0 text-xs text-center py-3">Sin dimensiones. Las tablas pueden mostrar datos sin agrupar.</p>
                {/if}
            </div>

            <!-- Metrics -->
            <div class="glass-card rounded-xl p-5 mb-5">
                <div class="flex items-center justify-between mb-3">
                    <p class="text-[10px] text-cat-overlay0 uppercase tracking-wider font-bold">Métricas (Valores)</p>
                    <button onclick={addMetric}
                        class="text-[10px] font-bold text-cat-blue hover:text-cat-blue/80 transition-colors">+ Agregar</button>
                </div>
                {#if selectedWidget.config_json?.metrics?.length > 0}
                    <div class="space-y-2">
                        {#each selectedWidget.config_json.metrics as met, mi}
                            {@const field = getFieldById(met.field_ref)}
                            <div class="p-2 bg-cat-surface0/30 rounded-lg space-y-2">
                                <div class="flex items-center gap-2">
                                    <select bind:value={met.field_ref}
                                        onchange={() => {
                                            const f = getFieldById(met.field_ref);
                                            if (f && !f.aggregations.includes(met.aggregation)) {
                                                met.aggregation = f.aggregations[0] || 'count';
                                            }
                                            met.label = `${AGG_LABELS[met.aggregation] || met.aggregation} de ${f?.name || '?'}`;
                                            widgets = [...widgets]; scheduleSave();
                                        }}
                                        class="flex-1 bg-transparent text-cat-text text-xs outline-none cursor-pointer">
                                        {#each fields as f}
                                            <option value={f.id}>{f.name} ({f.data_type_display})</option>
                                        {/each}
                                    </select>
                                    <select bind:value={met.aggregation}
                                        onchange={() => {
                                            const f = getFieldById(met.field_ref);
                                            met.label = `${AGG_LABELS[met.aggregation] || met.aggregation} de ${f?.name || '?'}`;
                                            widgets = [...widgets]; scheduleSave();
                                        }}
                                        class="bg-transparent text-cat-text text-xs outline-none cursor-pointer">
                                        {#each (field ? field.aggregations : ['count']) as agg}
                                            <option value={agg}>{AGG_LABELS[agg] || agg}</option>
                                        {/each}
                                    </select>
                                    <button onclick={() => { removeMetric(mi); scheduleSave(); }}
                                        class="text-cat-red/60 hover:text-cat-red p-1 transition-colors text-xs">✕</button>
                                </div>
                                <input type="text" bind:value={met.label}
                                    oninput={() => { widgets = [...widgets]; scheduleSave(); }}
                                    class="w-full bg-cat-surface0/50 text-cat-text text-[10px] px-2 py-1 rounded outline-none border border-transparent focus:border-cat-mauve/30"
                                    placeholder="Etiqueta personalizada"
                                />
                            </div>
                        {/each}
                    </div>
                {:else}
                    <p class="text-cat-overlay0 text-xs text-center py-3">Sin métricas. Agrega campos y agregaciones.</p>
                {/if}
            </div>

                </div>

                <!-- Preview Column -->
                <div class="flex flex-col gap-5">
                    <!-- Preview -->
                    <div class="glass-card rounded-xl p-5 flex flex-col min-h-[400px]">
                        <div class="flex items-center justify-between mb-4">
                            <h3 class="text-[10px] text-cat-overlay0 uppercase tracking-wider font-bold flex items-center gap-2">
                                Vista Previa
                                {#if previewLoading}
                                    <span class="animate-spin text-cat-mauve">⟳</span>
                                {/if}
                            </h3>
                            <button onclick={loadPreview} class="text-cat-subtext0 hover:text-cat-text transition-colors p-1 rounded" title="Refrescar">
                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M3 21v-5h5"/></svg>
                            </button>
                        </div>

                {#if previewError}
                    <div class="p-3 bg-cat-red/5 border border-cat-red/20 rounded-lg text-cat-red text-xs whitespace-pre-wrap mb-4">
                        {previewError}
                    </div>
                {/if}

                {#if previewResult}
                    <div class="text-[10px] text-cat-overlay0 mb-3 flex items-center gap-3">
                        <span>{previewResult.total_rows} filas</span>
                        {#if previewResult.excluded_invalid > 0}
                            <span class="text-cat-yellow">{previewResult.excluded_invalid} excluidas</span>
                        {/if}
                    </div>

                    {#if previewResult.chart_data?.type}
                        <div class="chart-container" style="height: 280px; position: relative;">
                            <canvas use:chartAction={{
                                type: previewResult.chart_data.type,
                                data: JSON.parse(JSON.stringify(previewResult.chart_data.data)),
                            }}></canvas>
                        </div>
                    {:else if previewResult.columns?.length > 0}
                        <div class="overflow-x-auto max-h-64">
                            <table class="data-table w-full text-xs">
                                <thead class="sticky top-0 shadow-sm">
                                    <tr>
                                        {#each previewResult.columns as col}
                                            <th class="px-2 py-1.5 text-left text-[10px] font-bold uppercase tracking-wider text-cat-subtext0 bg-cat-surface0 border-b border-cat-surface1/30">{col.label}</th>
                                        {/each}
                                    </tr>
                                </thead>
                                <tbody>
                                    {#each previewResult.rows as row}
                                        <tr class="border-b border-cat-surface0/20">
                                            {#each previewResult.columns as col}
                                                <td class="px-2 py-1 text-cat-text font-mono">{row[col.key] ?? '—'}</td>
                                            {/each}
                                        </tr>
                                    {/each}
                                </tbody>
                            </table>
                        </div>
                    {:else}
                        <p class="text-cat-overlay0 text-xs text-center py-6">
                            Sin datos para previsualizar.
                        </p>
                    {/if}
                {:else if !previewError}
                    <p class="text-cat-overlay0 text-xs text-center py-6">
                        Configura dimensiones y métricas, luego haz clic en "Previsualizar".
                    </p>
                {/if}
                    </div>
                </div> <!-- End Preview Column -->
            </div> <!-- End Editor Grid -->
        {:else}
            <!-- No widget selected -->
            <div class="glass-card rounded-xl p-12 text-center h-full flex flex-col justify-center items-center">
                <div class="p-5 bg-cat-surface0/60 rounded-full border border-cat-surface1/30 mb-5 inline-flex">
                    <svg class="text-cat-mauve" xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24"
                        fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
                        <rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>
                    </svg>
                </div>
                <h3 class="text-lg font-bold text-cat-text mb-2">Selecciona un widget</h3>
                <p class="text-cat-subtext0 text-sm">Elige uno de la lista a la izquierda o agrega uno nuevo para comenzar a editar.</p>
            </div>
        {/if}

        <!-- Global Filters -->
        <div class="glass-card rounded-xl p-5">
            <div class="flex items-center justify-between mb-4">
                <p class="text-[10px] text-cat-overlay0 uppercase tracking-wider font-bold">Filtros Globales del Reporte</p>
                <span class="text-[10px] text-cat-overlay0 px-2 py-0.5 bg-cat-surface0/60 rounded font-bold">{globalFilters.length}</span>
            </div>

            {#if globalFilters.length > 0}
                <div class="space-y-2 mb-4">
                    {#each globalFilters as gf, gi}
                        {@const field = getFieldById(gf.field_ref)}
                        <div class="flex items-center gap-2 p-2 bg-cat-surface0/30 rounded-lg text-xs">
                            <span class="font-bold text-cat-text">{field?.name || `#${gf.field_ref}`}</span>
                            <span class="text-cat-mauve">{OP_LABELS[gf.operator] || gf.operator}</span>
                            <span class="text-cat-subtext0 truncate flex-1">{JSON.stringify(gf.value_json?.value ?? gf.value_json)}</span>
                            <button onclick={() => deleteGlobalFilter(gi)}
                                class="text-cat-red/60 hover:text-cat-red p-1 transition-colors">✕</button>
                        </div>
                    {/each}
                </div>
            {/if}

            <div class="flex items-end gap-2">
                <div class="flex-1">
                    <label class="text-[10px] text-cat-overlay0 block mb-1">Campo</label>
                    <select bind:value={newFilterField}
                        class="w-full bg-cat-surface0/50 text-cat-text text-xs px-2 py-1.5 rounded outline-none border border-cat-surface1/30 focus:border-cat-mauve/30">
                        {#each fields as f}
                            <option value={f.id}>{f.name}</option>
                        {/each}
                    </select>
                </div>
                <div>
                    <label class="text-[10px] text-cat-overlay0 block mb-1">Operador</label>
                    <select bind:value={newFilterOperator}
                        class="bg-cat-surface0/50 text-cat-text text-xs px-2 py-1.5 rounded outline-none border border-cat-surface1/30 focus:border-cat-mauve/30">
                        {#each (getFieldById(newFilterField)?.operators ?? Object.keys(OP_LABELS)) as op}
                            <option value={op}>{OP_LABELS[op] || op}</option>
                        {/each}
                    </select>
                </div>
                <div class="flex-1">
                    <label class="text-[10px] text-cat-overlay0 block mb-1">Valor</label>
                    <input type="text" bind:value={newFilterValue}
                        class="w-full bg-cat-surface0/50 text-cat-text text-xs px-2 py-1.5 rounded outline-none border border-cat-surface1/30 focus:border-cat-mauve/30"
                        placeholder="Valor..."
                    />
                </div>
                <button onclick={addGlobalFilter}
                    class="px-3 py-1.5 rounded text-[10px] font-bold bg-cat-blue/10 text-cat-blue border border-cat-blue/20 hover:bg-cat-blue/20 transition-all shrink-0">
                    + Filtro
                </button>
            </div>
        </div>
    </div>
</div>

<style>
    .builder-layout {
        display: grid;
        grid-template-columns: 280px 1fr;
        gap: 1.5rem;
        min-height: calc(100vh - 120px);
        align-items: start;
    }
    .builder-editor-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1.5rem;
        align-items: start;
    }
    @media (max-width: 1024px) {
        .builder-editor-grid {
            grid-template-columns: 1fr;
        }
    }
    .builder-sidebar {
        position: sticky;
        top: 80px;
        align-self: start;
        padding: 1rem;
        border-radius: 0.75rem;
        border: 1px solid rgba(88, 91, 112, 0.3);
        background: rgba(30, 30, 46, 0.6);
    }
    @media (max-width: 768px) {
        .builder-layout {
            grid-template-columns: 1fr;
        }
        .builder-sidebar {
            position: static;
        }
    }
</style>
