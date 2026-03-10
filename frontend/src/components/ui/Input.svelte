<script>
    let { 
        type = "text",
        name = "",
        id = "",
        value = $bindable(""),
        placeholder = "",
        required = false,
        autocomplete = "",
        error = "",
        label = ""
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
        <input
            {type}
            {name}
            id={id || `id_${name}`}
            value={value}
            oninput={(e) => { value = e.target.value; }}
            {placeholder}
            {required}
            {autocomplete}
            class="form-input-hover w-full {error ? 'border-cat-red/50 focus:border-cat-red focus:ring-cat-red/20' : ''}"
            onfocus={() => { focused = true; }}
            onblur={() => { focused = false; }}
        />
        
        <!-- Focus indicator bar -->
        <div class="absolute bottom-0 left-0 h-0.5 bg-gradient-to-r from-cat-mauve to-cat-pink transition-all duration-300 pointer-events-none {focused ? 'w-full opacity-100' : 'w-0 opacity-0'}"></div>
    </div>
</div>
