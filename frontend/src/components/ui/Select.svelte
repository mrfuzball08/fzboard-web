<script>
    let { 
        name = "",
        id = "",
        value = $bindable(""),
        required = false,
        error = "",
        label = "",
        options = [] // Array of { value: string, label: string }
    } = $props();

    let focused = $state(false);
</script>

<div class="field-group w-full">
    {#if label}
        <label for="id_{name}" class="field-label flex justify-between items-center w-full">
            <span>{label} {required ? '*' : ''}</span>
            {#if error}
                <span class="text-xs text-cat-red font-semibold">{error}</span>
            {/if}
        </label>
    {/if}
    
    <div class="relative group">
        <select
            {name}
            id={id || `id_${name}`}
            bind:value
            {required}
            class="form-input-hover w-full appearance-none pr-10 {error ? 'border-cat-red/50 focus:border-cat-red focus:ring-cat-red/20' : ''}"
            onfocus={() => { focused = true; }}
            onblur={() => { focused = false; }}
        >
            {#each options as opt}
                <option value={opt.value}>{opt.label}</option>
            {/each}
        </select>
        
        <!-- Custom dropdown arrow -->
        <div class="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-cat-subtext0 {focused ? 'text-cat-mauve' : ''} transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="6 9 12 15 18 9"></polyline>
            </svg>
        </div>

        <!-- Focus indicator bar -->
        <div class="absolute bottom-0 left-0 h-0.5 bg-gradient-to-r from-cat-mauve to-cat-pink transition-all duration-300 pointer-events-none {focused ? 'w-full opacity-100' : 'w-0 opacity-0'}"></div>
    </div>
</div>
