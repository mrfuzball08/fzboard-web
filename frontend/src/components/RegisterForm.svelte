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

    const getError = (field) => {
        return errors[field] && errors[field].length > 0 ? errors[field][0].message : "";
    };

    let loading = $state(false);
</script>

<form method="post" class="space-y-5" onsubmit={() => { loading = true; }}>
    <input type="hidden" name="csrfmiddlewaretoken" value={csrf}>

    <!-- Name fields -->
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Input 
            name="first_name" 
            label="Nombre" 
            autocomplete="given-name"
            required={true}
            error={getError('first_name')} 
        />
        <Input 
            name="last_name" 
            label="Apellido" 
            autocomplete="family-name"
            required={true}
            error={getError('last_name')} 
        />
    </div>

    <!-- Account fields -->
    <Input 
        name="username" 
        label="Nombre de Usuario" 
        autocomplete="username"
        required={true}
        error={getError('username')} 
    />

    <Input 
        type="email"
        name="email" 
        label="Correo Electrónico" 
        autocomplete="email"
        required={true}
        error={getError('email')} 
    />

    <!-- Password fields -->
    <Input 
        type="password"
        name="password1" 
        label="Contraseña" 
        autocomplete="new-password"
        required={true}
        error={getError('password1')} 
    />

    <Input 
        type="password"
        name="password2" 
        label="Confirmar Contraseña" 
        autocomplete="new-password"
        required={true}
        error={getError('password2')} 
    />

    <!-- Terms and conditions -->
    <div class="flex items-start gap-3 p-4 bg-cat-mantle/30 rounded-xl border border-cat-surface1">
        <input type="checkbox" id="terms" name="terms" required
            class="mt-1 rounded border-cat-surface1 text-cat-mauve focus:ring-cat-mauve/30">
        <label for="terms" class="text-sm text-cat-subtext0">
            Acepto los <a href="/" class="link-primary">términos y condiciones</a> y la <a href="/"
                class="link-primary">política de privacidad</a>
        </label>
    </div>

    <button type="submit" class="btn-primary group w-full flex items-center justify-center gap-2" disabled={loading}>
        {#if !loading}
            <svg class="w-5 h-5 transition-transform group-hover:scale-110" xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
                stroke-linejoin="round">
                <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                <circle cx="8.5" cy="7" r="4"></circle>
                <line x1="20" y1="8" x2="20" y2="14"></line>
                <line x1="23" y1="11" x2="17" y2="11"></line>
            </svg>
            Crear Cuenta
        {:else}
            <div class="w-5 h-5 rounded-full border-2 border-current border-t-transparent spinner"></div>
        {/if}
    </button>
</form>
