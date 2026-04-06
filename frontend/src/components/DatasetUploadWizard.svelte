<script>
    import Select from "./ui/Select.svelte";

    let {
        csrf = "",
        datasetPk = 0,
        templateName = "",
        columns = [],
        mappingUrl = "",
        uploadUrl = "",
        hasExistingData = false,
        existingRowCount = 0,
    } = $props();

    // ─── Wizard State ────────────────────────────────────────────────
    let currentStep = $state(1);
    let loading = $state(false);
    let error = $state("");

    // Step 1: File
    let selectedFile = $state(null);
    let dragOver = $state(false);
    let fileHeaders = $state([]);

    // Step 2: Mapping
    let mapping = $state({});     // file header → template column id
    let extraColumns = $state([]);
    let missingColumns = $state([]);

    // Step 3: Mode
    let importMode = $state("replace");

    // ─── Column options for select dropdowns ─────────────────────────
    let columnOptions = $derived([
        { value: "", label: "— Sin mapear —" },
        ...columns.map(c => ({ value: String(c.id), label: `${c.name} (${c.data_type_display})` }))
    ]);

    // ─── Step labels ─────────────────────────────────────────────────
    const steps = [
        { num: 1, label: "Archivo" },
        { num: 2, label: "Mapeo" },
        { num: 3, label: "Modo" },
        { num: 4, label: "Importar" },
    ];

    // ─── File Handling ───────────────────────────────────────────────
    function handleFileSelect(event) {
        const file = event.target.files?.[0];
        if (file) selectFile(file);
    }

    function handleDrop(event) {
        event.preventDefault();
        dragOver = false;
        const file = event.dataTransfer?.files?.[0];
        if (file) selectFile(file);
    }

    function selectFile(file) {
        const ext = file.name.split('.').pop().toLowerCase();
        if (!['csv', 'xlsx', 'xls'].includes(ext)) {
            error = "Solo se aceptan archivos CSV y Excel (.xlsx, .xls).";
            return;
        }
        selectedFile = file;
        error = "";
    }

    // ─── Step 1 → 2: Upload file for header extraction ──────────────
    async function extractHeaders() {
        if (!selectedFile) return;
        loading = true;
        error = "";

        try {
            // Read file locally for CSV, or send to server
            if (selectedFile.name.endsWith('.csv')) {
                const text = await selectedFile.text();
                const firstLine = text.split('\n')[0];
                fileHeaders = firstLine
                    .split(',')
                    .map(h => h.trim().replace(/^"|"$/g, ''));
            } else {
                // For Excel, we need to send to the server
                // Use a FormData to upload and parse headers
                const formData = new FormData();
                formData.append('file', selectedFile);
                const resp = await fetch(uploadUrl, {
                    method: 'POST',
                    headers: { 'X-CSRFToken': csrf, 'X-Extract-Headers': '1' },
                    body: formData,
                });
                if (!resp.ok) throw new Error('Error al leer el archivo');
                const data = await resp.json();
                fileHeaders = data.headers || [];
            }

            // Get suggested mapping from server
            const resp = await fetch(mappingUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrf,
                },
                body: JSON.stringify({ headers: fileHeaders }),
            });

            if (!resp.ok) throw new Error('Error al obtener el mapeo sugerido');
            const result = await resp.json();

            // Apply suggested mapping
            mapping = {};
            for (const [header, colId] of Object.entries(result.mapping)) {
                mapping[header] = colId !== null ? String(colId) : "";
            }
            extraColumns = result.extra_columns || [];
            missingColumns = result.missing_columns || [];

            currentStep = 2;
        } catch (e) {
            error = e.message || "Error al procesar el archivo";
        } finally {
            loading = false;
        }
    }

    // ─── Step Logic ──────────────────────────────────────────────────
    function goToStep3() {
        currentStep = 3;
    }

    function goToStep4() {
        currentStep = 4;
    }

    function goBack() {
        if (currentStep > 1) currentStep -= 1;
    }

    // ─── Step 4: Submit the import ───────────────────────────────────
    let submitting = $state(false);

    function submitImport() {
        submitting = true;
        // Build the form and submit natively (multipart/form-data for file)
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = uploadUrl;
        form.enctype = 'multipart/form-data';

        // CSRF
        const csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrfmiddlewaretoken';
        csrfInput.value = csrf;
        form.appendChild(csrfInput);

        // Mode
        const modeInput = document.createElement('input');
        modeInput.type = 'hidden';
        modeInput.name = 'mode';
        modeInput.value = importMode;
        form.appendChild(modeInput);

        // Mapping JSON
        const mappingInput = document.createElement('input');
        mappingInput.type = 'hidden';
        mappingInput.name = 'header_mapping';

        // Convert mapping: "" → null, "123" → 123
        const cleanMapping = {};
        for (const [k, v] of Object.entries(mapping)) {
            cleanMapping[k] = v ? parseInt(v) : null;
        }
        mappingInput.value = JSON.stringify(cleanMapping);
        form.appendChild(mappingInput);

        // File — use a DataTransfer to set the file on a file input
        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.name = 'file';
        const dt = new DataTransfer();
        dt.items.add(selectedFile);
        fileInput.files = dt.files;
        form.appendChild(fileInput);

        document.body.appendChild(form);
        form.submit();
    }

    // Helper: count mapped columns
    let mappedCount = $derived(
        Object.values(mapping).filter(v => v !== "" && v !== null).length
    );

    // Format file size
    function formatSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / 1048576).toFixed(1) + ' MB';
    }
</script>

<div class="space-y-6">
    <!-- Wizard Step Indicator -->
    <div class="glass-card rounded-xl p-4">
        <div class="flex items-center justify-between">
            {#each steps as step, i}
                <div class="flex items-center gap-2 {i < steps.length - 1 ? 'flex-1' : ''}">
                    <div class="wizard-step-number {currentStep === step.num
                        ? 'wizard-step-number-active'
                        : currentStep > step.num
                            ? 'wizard-step-number-complete'
                            : 'wizard-step-number-pending'}">
                        {#if currentStep > step.num}
                            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24"
                                fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                                <polyline points="20 6 9 17 4 12" />
                            </svg>
                        {:else}
                            {step.num}
                        {/if}
                    </div>
                    <span class="text-xs font-bold hidden sm:inline {currentStep === step.num
                        ? 'text-cat-mauve'
                        : currentStep > step.num
                            ? 'text-cat-green'
                            : 'text-cat-overlay0'}">
                        {step.label}
                    </span>
                    {#if i < steps.length - 1}
                        <div class="flex-1 h-px mx-2 {currentStep > step.num
                            ? 'bg-cat-green/30'
                            : 'bg-cat-surface1/40'}"></div>
                    {/if}
                </div>
            {/each}
        </div>
    </div>

    <!-- Error Display -->
    {#if error}
        <div class="alert-error flex items-center gap-3">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none"
                stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="shrink-0">
                <circle cx="12" cy="12" r="10" />
                <line x1="15" y1="9" x2="9" y2="15" />
                <line x1="9" y1="9" x2="15" y2="15" />
            </svg>
            <span class="text-sm font-medium">{error}</span>
        </div>
    {/if}

    <!-- STEP 1: File Upload -->
    {#if currentStep === 1}
        <div class="glass-card rounded-xl p-6">
            <div class="flex items-center gap-2.5 mb-5">
                <div class="p-1.5 bg-cat-mauve/10 rounded-lg text-cat-mauve">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none"
                        stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                        <polyline points="14 2 14 8 20 8" />
                    </svg>
                </div>
                <h3 class="font-bold text-cat-text">Seleccionar Archivo</h3>
            </div>

            <!-- Dropzone -->
            <!-- svelte-ignore a11y_no_static_element_interactions -->
            <div
                class="dropzone {dragOver ? 'dropzone-active' : ''}"
                ondragover={(e) => { e.preventDefault(); dragOver = true; }}
                ondragleave={() => { dragOver = false; }}
                ondrop={handleDrop}
                onclick={() => document.getElementById('file-input').click()}
            >
                {#if selectedFile}
                    <div class="space-y-2">
                        <div class="p-3 bg-cat-green/10 rounded-xl inline-block">
                            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"
                                fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                                class="text-cat-green">
                                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                                <polyline points="22 4 12 14.01 9 11.01" />
                            </svg>
                        </div>
                        <p class="text-sm font-bold text-cat-text">{selectedFile.name}</p>
                        <p class="text-xs text-cat-overlay0">{formatSize(selectedFile.size)}</p>
                        <button
                            type="button"
                            onclick={(e) => { e.stopPropagation(); selectedFile = null; }}
                            class="text-xs text-cat-red hover:text-cat-red/80 font-bold transition-colors">
                            Cambiar archivo
                        </button>
                    </div>
                {:else}
                    <div class="space-y-3">
                        <div class="p-3 bg-cat-surface0/60 rounded-xl inline-block">
                            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"
                                fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                                class="text-cat-overlay0">
                                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                                <polyline points="17 8 12 3 7 8" />
                                <line x1="12" x2="12" y1="3" y2="15" />
                            </svg>
                        </div>
                        <p class="text-sm text-cat-text font-bold">Arrastra un archivo aquí</p>
                        <p class="text-xs text-cat-overlay0">o haz clic para seleccionar</p>
                        <p class="text-[10px] text-cat-overlay0/60 uppercase tracking-wider font-bold">.CSV · .XLSX · .XLS</p>
                    </div>
                {/if}
            </div>

            <input id="file-input" type="file" accept=".csv,.xlsx,.xls" class="hidden" onchange={handleFileSelect} />

            <!-- Continue Button -->
            {#if selectedFile}
                <button
                    type="button"
                    onclick={extractHeaders}
                    disabled={loading}
                    class="mt-4 bg-gradient-to-r from-cat-mauve to-cat-pink text-cat-base px-8 py-3 rounded-xl font-bold transition-all duration-300 hover:scale-105 hover:shadow-xl hover:shadow-cat-mauve/25 active:scale-95 flex items-center gap-2 cursor-pointer">
                    {#if loading}
                        <div class="w-4 h-4 spinner"></div>
                        Analizando...
                    {:else}
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none"
                            stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <polyline points="9 18 15 12 9 6" />
                        </svg>
                        Continuar
                    {/if}
                </button>
            {/if}
        </div>
    {/if}

    <!-- STEP 2: Header Mapping -->
    {#if currentStep === 2}
        <div class="glass-card rounded-xl p-6">
            <div class="flex items-center justify-between mb-5">
                <div class="flex items-center gap-2.5">
                    <div class="p-1.5 bg-cat-blue/10 rounded-lg text-cat-blue">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none"
                            stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <line x1="22" y1="2" x2="11" y2="13" />
                            <polygon points="22 2 15 22 11 13 2 9 22 2" />
                        </svg>
                    </div>
                    <h3 class="font-bold text-cat-text">Mapeo de Columnas</h3>
                </div>
                <span class="text-xs text-cat-overlay0 bg-cat-mantle px-2.5 py-1 rounded-full font-bold">
                    {mappedCount}/{columns.length} mapeadas
                </span>
            </div>

            <p class="text-xs text-cat-subtext0 mb-4">
                Vincula las columnas del archivo con las columnas del formato <span class="text-cat-mauve font-bold">{templateName}</span>.
            </p>

            <!-- Warnings -->
            {#if extraColumns.length > 0}
                <div class="alert-info flex items-start gap-2 mb-4 text-xs">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none"
                        stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="shrink-0 mt-0.5">
                        <circle cx="12" cy="12" r="10" />
                        <line x1="12" y1="16" x2="12" y2="12" />
                        <line x1="12" y1="8" x2="12.01" y2="8" />
                    </svg>
                    <span><strong>Columnas extra del archivo:</strong> {extraColumns.join(', ')} — serán ignoradas.</span>
                </div>
            {/if}

            {#if missingColumns.length > 0}
                <div class="alert-error flex items-start gap-2 mb-4 text-xs">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none"
                        stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="shrink-0 mt-0.5">
                        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                        <line x1="12" y1="9" x2="12" y2="13" />
                        <line x1="12" y1="17" x2="12.01" y2="17" />
                    </svg>
                    <span><strong>Columnas del formato sin datos:</strong> {missingColumns.map(c => c.name).join(', ')} — se guardarán como vacías.</span>
                </div>
            {/if}

            <!-- Mapping Table -->
            <div class="rounded-xl overflow-hidden border border-cat-surface1/30">
                <table class="w-full text-left text-sm">
                    <thead>
                        <tr class="bg-cat-mantle/60">
                            <th class="px-4 py-3 text-[10px] font-bold text-cat-overlay0 uppercase tracking-widest">Columna del Archivo</th>
                            <th class="px-2 py-3 text-center text-[10px] font-bold text-cat-overlay0 w-10">→</th>
                            <th class="px-4 py-3 text-[10px] font-bold text-cat-overlay0 uppercase tracking-widest">Columna del Formato</th>
                        </tr>
                    </thead>
                    <tbody>
                        {#each fileHeaders as header, i}
                            <tr class="border-t border-cat-surface1/20 hover:bg-cat-mantle/30 transition-colors">
                                <td class="px-4 py-3 font-medium text-cat-text text-xs">{header}</td>
                                <td class="px-2 py-3 text-center text-cat-overlay0">→</td>
                                <td class="px-4 py-2">
                                    <Select
                                        name="mapping-{i}"
                                        bind:value={mapping[header]}
                                        options={columnOptions}
                                    />
                                </td>
                            </tr>
                        {/each}
                    </tbody>
                </table>
            </div>

            <!-- Actions -->
            <div class="flex items-center gap-4 mt-5">
                <button type="button" onclick={goToStep3}
                    class="bg-gradient-to-r from-cat-mauve to-cat-pink text-cat-base px-8 py-3 rounded-xl font-bold transition-all duration-300 hover:scale-105 hover:shadow-xl hover:shadow-cat-mauve/25 active:scale-95 flex items-center gap-2 cursor-pointer">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none"
                        stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="9 18 15 12 9 6" />
                    </svg>
                    Continuar
                </button>
                <button type="button" onclick={goBack}
                    class="text-cat-subtext0 hover:text-cat-text text-sm font-bold transition-colors px-4 py-3 cursor-pointer">
                    Atrás
                </button>
            </div>
        </div>
    {/if}

    <!-- STEP 3: Import Mode -->
    {#if currentStep === 3}
        <div class="glass-card rounded-xl p-6">
            <div class="flex items-center gap-2.5 mb-5">
                <div class="p-1.5 bg-cat-yellow/10 rounded-lg text-cat-yellow">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none"
                        stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="3" />
                        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06A1.65 1.65 0 0 0 19.36 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
                    </svg>
                </div>
                <h3 class="font-bold text-cat-text">Modo de Importación</h3>
            </div>

            <div class="space-y-3">
                <!-- Replace -->
                <label class="flex items-start gap-4 p-4 rounded-xl border cursor-pointer transition-all
                    {importMode === 'replace'
                        ? 'border-cat-mauve/40 bg-cat-mauve/5'
                        : 'border-cat-surface1/30 hover:border-cat-surface2/60 bg-cat-mantle/20'}">
                    <input type="radio" name="import-mode" value="replace"
                        bind:group={importMode}
                        class="mt-1 accent-cat-mauve" />
                    <div>
                        <p class="text-sm font-bold text-cat-text">Reemplazar</p>
                        <p class="text-xs text-cat-overlay0 mt-0.5">
                            Eliminar todos los datos existentes y subir solo los nuevos.
                            {#if hasExistingData}
                                <span class="text-cat-red font-bold">Se eliminarán {existingRowCount} filas existentes.</span>
                            {/if}
                        </p>
                    </div>
                </label>

                <!-- Append -->
                <label class="flex items-start gap-4 p-4 rounded-xl border cursor-pointer transition-all
                    {importMode === 'append'
                        ? 'border-cat-mauve/40 bg-cat-mauve/5'
                        : 'border-cat-surface1/30 hover:border-cat-surface2/60 bg-cat-mantle/20'}">
                    <input type="radio" name="import-mode" value="append"
                        bind:group={importMode}
                        class="mt-1 accent-cat-mauve" />
                    <div>
                        <p class="text-sm font-bold text-cat-text">Agregar</p>
                        <p class="text-xs text-cat-overlay0 mt-0.5">
                            Mantener los datos existentes y añadir las filas nuevas.
                            {#if hasExistingData}
                                <span class="text-cat-blue font-bold">Se mantendrán {existingRowCount} filas existentes.</span>
                            {/if}
                        </p>
                    </div>
                </label>
            </div>

            {#if importMode === 'replace' && hasExistingData}
                <div class="alert-error flex items-start gap-2 mt-4 text-xs">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none"
                        stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="shrink-0 mt-0.5">
                        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                        <line x1="12" y1="9" x2="12" y2="13" />
                        <line x1="12" y1="17" x2="12.01" y2="17" />
                    </svg>
                    <span><strong>Atención:</strong> Se eliminarán permanentemente las {existingRowCount} filas existentes antes de importar los datos nuevos.</span>
                </div>
            {/if}

            <!-- Actions -->
            <div class="flex items-center gap-4 mt-5">
                <button type="button" onclick={goToStep4}
                    class="bg-gradient-to-r from-cat-mauve to-cat-pink text-cat-base px-8 py-3 rounded-xl font-bold transition-all duration-300 hover:scale-105 hover:shadow-xl hover:shadow-cat-mauve/25 active:scale-95 flex items-center gap-2 cursor-pointer">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none"
                        stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="9 18 15 12 9 6" />
                    </svg>
                    Continuar
                </button>
                <button type="button" onclick={goBack}
                    class="text-cat-subtext0 hover:text-cat-text text-sm font-bold transition-colors px-4 py-3 cursor-pointer">
                    Atrás
                </button>
            </div>
        </div>
    {/if}

    <!-- STEP 4: Confirm & Execute -->
    {#if currentStep === 4}
        <div class="glass-card rounded-xl p-6">
            <div class="flex items-center gap-2.5 mb-5">
                <div class="p-1.5 bg-cat-green/10 rounded-lg text-cat-green">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none"
                        stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                            <polyline points="22 4 12 14.01 9 11.01" />
                    </svg>
                </div>
                <h3 class="font-bold text-cat-text">Confirmar Importación</h3>
            </div>

            <!-- Summary -->
            <div class="space-y-3 mb-6">
                <div class="flex items-center justify-between py-2 border-b border-cat-surface1/20">
                    <span class="text-xs text-cat-overlay0 font-bold uppercase tracking-wider">Archivo</span>
                    <span class="text-sm text-cat-text font-bold">{selectedFile?.name}</span>
                </div>
                <div class="flex items-center justify-between py-2 border-b border-cat-surface1/20">
                    <span class="text-xs text-cat-overlay0 font-bold uppercase tracking-wider">Tamaño</span>
                    <span class="text-sm text-cat-text">{selectedFile ? formatSize(selectedFile.size) : ''}</span>
                </div>
                <div class="flex items-center justify-between py-2 border-b border-cat-surface1/20">
                    <span class="text-xs text-cat-overlay0 font-bold uppercase tracking-wider">Modo</span>
                    <span class="text-sm font-bold {importMode === 'replace' ? 'text-cat-yellow' : 'text-cat-blue'}">
                        {importMode === 'replace' ? 'Reemplazar' : 'Agregar'}
                    </span>
                </div>
                <div class="flex items-center justify-between py-2 border-b border-cat-surface1/20">
                    <span class="text-xs text-cat-overlay0 font-bold uppercase tracking-wider">Columnas mapeadas</span>
                    <span class="text-sm text-cat-text">{mappedCount} de {columns.length}</span>
                </div>
                <div class="flex items-center justify-between py-2">
                    <span class="text-xs text-cat-overlay0 font-bold uppercase tracking-wider">Columnas del archivo</span>
                    <span class="text-sm text-cat-text">{fileHeaders.length}</span>
                </div>
            </div>

            <!-- Actions -->
            <div class="flex items-center gap-4">
                <button type="button" onclick={submitImport}
                    disabled={submitting}
                    class="bg-gradient-to-r from-cat-green to-cat-blue text-cat-base px-8 py-3 rounded-xl font-bold transition-all duration-300 hover:scale-105 hover:shadow-xl hover:shadow-cat-green/25 active:scale-95 flex items-center gap-2 cursor-pointer">
                    {#if submitting}
                        <div class="w-4 h-4 spinner"></div>
                        Importando...
                    {:else}
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none"
                            stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                            <polyline points="17 8 12 3 7 8" />
                            <line x1="12" x2="12" y1="3" y2="15" />
                        </svg>
                        Iniciar Importación
                    {/if}
                </button>
                <button type="button" onclick={goBack}
                    disabled={submitting}
                    class="text-cat-subtext0 hover:text-cat-text text-sm font-bold transition-colors px-4 py-3 cursor-pointer">
                    Atrás
                </button>
            </div>
        </div>
    {/if}
</div>
