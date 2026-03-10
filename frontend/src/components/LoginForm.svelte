<script>
    import Input from './ui/Input.svelte';
    
    let { csrf = "", errorsJson = "" } = $props();
    
    let errors = $derived.by(() => {
        try {
            return errorsJson ? JSON.parse(errorsJson) : {};
        } catch(e) {
            return {};
        }
    });

    // Helper to get first error message for a field
    const getError = (field) => {
        return errors[field] && errors[field].length > 0 ? errors[field][0].message : "";
    };

    let loading = $state(false);
</script>

<!-- Login Form -->
<form method="post" class="space-y-5" onsubmit={() => { loading = true; }}>
    <input type="hidden" name="csrfmiddlewaretoken" value={csrf}>

    <Input 
        name="username" 
        label="Nombre de Usuario" 
        autocomplete="username"
        required={true}
        error={getError('username')} 
    />

    <Input 
        type="password"
        name="password" 
        label="Contraseña" 
        autocomplete="current-password"
        required={true}
        error={getError('password')} 
    />

    <button type="submit" class="btn-primary group w-full flex items-center justify-center gap-2" disabled={loading}>
        {#if !loading}
            <svg class="w-5 h-5 transition-transform group-hover:translate-x-1"
                xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4" />
                <polyline points="10 17 15 12 10 7" />
                <line x1="15" y1="12" x2="3" y2="12" />
            </svg>
            Iniciar Sesión
        {:else}
            <div class="w-5 h-5 rounded-full border-2 border-current border-t-transparent spinner"></div>
        {/if}
    </button>
</form>
