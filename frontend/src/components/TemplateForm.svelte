<script>
    import Input from "./ui/Input.svelte";
    import Textarea from "./ui/Textarea.svelte";
    import Select from "./ui/Select.svelte";

    let {
        csrf = "",
        errorsJson = "",
        formsetErrorsJson = "",
        initialTitle = "",
        initialDesc = "",
        initialColumnsJson = "[]",
        dataTypeChoicesJson = "[]", // Expected [{value: 'text', label: 'Texto'}, ...]
        prefix = "form",
    } = $props();

    let errors = $derived.by(() => {
        try {
            return errorsJson ? JSON.parse(errorsJson) : {};
        } catch (e) {
            return {};
        }
    });
    let formsetErrors = $derived.by(() => {
        try {
            return formsetErrorsJson ? JSON.parse(formsetErrorsJson) : [];
        } catch (e) {
            return [];
        }
    });
    let dataTypeOptions = $derived.by(() => {
        try {
            return dataTypeChoicesJson ? JSON.parse(dataTypeChoicesJson) : [];
        } catch (e) {
            return [];
        }
    });

    const getError = (field) =>
        errors[field] && errors[field].length > 0
            ? errors[field][0].message
            : "";
    const getFormsetError = (idx, field) =>
        formsetErrors[idx] && formsetErrors[idx][field]
            ? formsetErrors[idx][field][0].message
            : "";

    // Reactive State
    let name = $state("");
    let description = $state("");
    let columns = $state([]);
    let initialized = $state(false);

    // One-time initialization from props
    $effect(() => {
        if (initialized) return;
        initialized = true;
        
        name = initialTitle;
        description = initialDesc;

        try {
            let parsedCols = JSON.parse(initialColumnsJson);
            // Filter out blank extra forms (no id and no name)
            parsedCols = parsedCols.filter(c => c.id || c.name);
            if (parsedCols.length > 0) {
                columns = parsedCols.map((c) => ({ ...c, deleted: false }));
            } else {
                columns = [{ name: "", data_type: "text", deleted: false }];
            }
        } catch (e) {
            columns = [{ name: "", data_type: "text", deleted: false }];
        }
    });

    const addColumn = () => {
        columns = [...columns, { name: "", data_type: "text", deleted: false }];
    };

    let loading = $state(false);
    let activeColumns = $derived(columns.filter((c) => !c.deleted).length);
    let initialFormsCount = $derived(columns.filter((c) => c.id).length);
</script>

<form
    method="post"
    id="template-form"
    onsubmit={() => {
        loading = true;
    }}
>
    <input type="hidden" name="csrfmiddlewaretoken" value={csrf} />

    <!-- Management form fields injected manually to track standard Django Formset state -->
    <input type="hidden" name="{prefix}-TOTAL_FORMS" value={columns.length} />
    <input type="hidden" name="{prefix}-INITIAL_FORMS" value={initialFormsCount} />
    <input type="hidden" name="{prefix}-MIN_NUM_FORMS" value="0" />
    <input type="hidden" name="{prefix}-MAX_NUM_FORMS" value="1000" />

    <!-- Template Info Section -->
    <div class="glass-card rounded-xl p-6 mb-5">
        <div class="flex items-center gap-2.5 mb-5">
            <div class="p-1.5 bg-cat-mauve/10 rounded-lg text-cat-mauve">
                <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                >
                    <path
                        d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"
                    />
                    <path
                        d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"
                    />
                </svg>
            </div>
            <h3 class="font-bold text-cat-text">Información General</h3>
        </div>

        <div class="space-y-5">
            <Input
                name="name"
                label="Nombre del Formato"
                bind:value={name}
                required={true}
                error={getError("name")}
            />
            <Textarea
                name="description"
                label="Descripción del formato"
                bind:value={description}
                error={getError("description")}
            />
        </div>
    </div>

    <!-- Columns Section -->
    <div class="glass-card rounded-xl p-6 mb-5">
        <div class="flex items-center justify-between mb-5">
            <div class="flex items-center gap-2.5">
                <div class="p-1.5 bg-cat-blue/10 rounded-lg text-cat-blue">
                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="16"
                        height="16"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                    >
                        <rect
                            x="3"
                            y="3"
                            width="18"
                            height="18"
                            rx="2"
                            ry="2"
                        />
                        <line x1="3" y1="9" x2="21" y2="9" />
                        <line x1="9" y1="21" x2="9" y2="9" />
                    </svg>
                </div>
                <h3 class="font-bold text-cat-text">Columnas</h3>
            </div>
            <span
                class="text-xs text-cat-overlay0 bg-cat-mantle px-2.5 py-1 rounded-full font-bold"
            >
                {activeColumns} columna{activeColumns !== 1 ? "s" : ""}
            </span>
        </div>

        <!-- Table Header -->
        <div class="grid grid-cols-[2rem_1fr_10rem_2rem] gap-3 px-3 mb-2">
            <div></div>
            <span
                class="text-[10px] font-bold text-cat-overlay0 uppercase tracking-widest"
                >Encabezado</span
            >
            <span
                class="text-[10px] font-bold text-cat-overlay0 uppercase tracking-widest"
                >Tipo de dato</span
            >
            <div></div>
        </div>

        <div class="space-y-1.5">
            {#each columns as col, i}
                <div
                    class="column-row grid grid-cols-[2rem_1fr_10rem_2rem] gap-3 items-center px-3 py-2.5 rounded-xl bg-cat-mantle/40 border border-cat-surface1/40 transition-all hover:border-cat-surface2/60 hover:bg-cat-mantle/60 group {col.deleted
                        ? 'opacity-30 scale-95'
                        : ''}"
                >
                    <!-- Auto-Incrementing specific to active rows -->
                    <div
                        class="w-7 h-7 rounded-lg bg-cat-surface0/80 flex items-center justify-center text-[11px] font-bold text-cat-overlay0"
                    >
                        {i + 1}
                    </div>

                    <Input
                        name="{prefix}-{i}-name"
                        bind:value={col.name}
                        error={getFormsetError(i, "name")}
                    />

                    <Select
                        name="{prefix}-{i}-data_type"
                        bind:value={col.data_type}
                        options={dataTypeOptions}
                        error={getFormsetError(i, "data_type")}
                    />

                    <!-- Hidden Fields -->
                    <input type="hidden" name="{prefix}-{i}-order" value={i + 1} />
                    {#if col.id}
                        <input
                            type="hidden"
                            name="{prefix}-{i}-id"
                            value={col.id}
                        />
                    {/if}
                    <input
                        type="checkbox"
                        name="{prefix}-{i}-DELETE"
                        bind:checked={col.deleted}
                        class="hidden"
                    />

                    <!-- Delete Toggle -->
                    <div class="flex justify-center">
                        <button
                            type="button"
                            onclick={() => {
                                col.deleted = !col.deleted;
                            }}
                            class="cursor-pointer w-7 h-7 flex items-center justify-center text-cat-surface2 hover:text-cat-red hover:bg-cat-red/10 rounded-lg transition-all {col.deleted
                                ? 'opacity-100 text-cat-red bg-cat-red/10'
                                : 'opacity-0 group-hover:opacity-100'}"
                            title={col.deleted
                                ? "Restaurar columna"
                                : "Eliminar columna"}
                        >
                            {#if col.deleted}
                                <svg
                                    xmlns="http://www.w3.org/2000/svg"
                                    width="13"
                                    height="13"
                                    viewBox="0 0 24 24"
                                    fill="none"
                                    stroke="currentColor"
                                    stroke-width="2.5"
                                    stroke-linecap="round"
                                    stroke-linejoin="round"
                                >
                                    <polyline points="9 14 4 9 9 4"></polyline>
                                    <path d="M20 20v-7a4 4 0 0 0-4-4H4"></path>
                                </svg>
                            {:else}
                                <svg
                                    xmlns="http://www.w3.org/2000/svg"
                                    width="13"
                                    height="13"
                                    viewBox="0 0 24 24"
                                    fill="none"
                                    stroke="currentColor"
                                    stroke-width="2.5"
                                    stroke-linecap="round"
                                    stroke-linejoin="round"
                                >
                                    <line x1="18" y1="6" x2="6" y2="18" />
                                    <line x1="6" y1="6" x2="18" y2="18" />
                                </svg>
                            {/if}
                        </button>
                    </div>
                </div>
            {/each}
        </div>

        <button
            type="button"
            onclick={addColumn}
            class="mt-3 w-full py-2.5 border border-dashed border-cat-surface1/60 hover:border-cat-mauve/40 rounded-xl text-cat-overlay0 hover:text-cat-mauve text-xs font-bold transition-all flex items-center justify-center gap-1.5 hover:bg-cat-mauve/5 cursor-pointer"
        >
            <svg
                xmlns="http://www.w3.org/2000/svg"
                width="13"
                height="13"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2.5"
                stroke-linecap="round"
                stroke-linejoin="round"
            >
                <line x1="12" y1="5" x2="12" y2="19" />
                <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            Agregar Columna
        </button>
    </div>

    <!-- Submit Actions -->
    <div class="flex items-center gap-4 pt-2">
        <button
            type="submit"
            disabled={loading}
            class="bg-gradient-to-r from-cat-mauve to-cat-pink text-cat-base px-8 py-3 rounded-xl font-bold transition-all duration-300 hover:scale-105 hover:shadow-xl hover:shadow-cat-mauve/25 active:scale-95 flex items-center gap-2"
        >
            {#if !loading}
                <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                >
                    <path
                        d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"
                    />
                    <polyline points="17 21 17 13 7 13 7 21" />
                    <polyline points="7 3 7 8 15 8" />
                </svg>
                Guardar Formato
            {:else}
                <div
                    class="w-4 h-4 rounded-full border-2 border-cat-base border-t-transparent spinner"
                ></div>
            {/if}
        </button>
        <a
            href="/formatos/"
            class="text-cat-subtext0 hover:text-cat-text text-sm font-bold transition-colors px-4 py-3"
        >
            Cancelar
        </a>
    </div>
</form>
