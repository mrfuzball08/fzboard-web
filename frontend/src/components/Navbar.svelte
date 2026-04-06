<script>
    let {
        activeNav = "",
        username = "",
        email = "",
        csrfToken = "",
    } = $props();
</script>

<nav
    class="sticky top-0 z-50 bg-cat-mantle/80 backdrop-blur-md border-b border-cat-surface0 px-6 md:px-10 py-4"
>
    <div class="flex justify-between items-center">
        <!-- Left: Logo & Nav -->
        <div class="flex items-center gap-8">
            <a href="/" class="group">
                <h1
                    class="text-2xl font-bold text-cat-mauve tracking-tighter group-hover:opacity-80 transition-opacity"
                >
                    FuzBoard<span class="text-cat-pink">.</span>
                </h1>
            </a>

            <!-- Desktop Nav -->
            <div
                class="hidden md:flex items-center gap-1 bg-cat-surface0/50 p-1 rounded-lg border border-cat-surface0"
            >
                <a
                    href="/"
                    class="px-4 py-1.5 rounded-md text-sm transition-all {activeNav ===
                    'dashboard'
                        ? 'bg-cat-surface1 text-cat-text font-bold shadow-sm'
                        : 'text-cat-subtext0 font-medium hover:text-cat-text hover:bg-cat-surface0'}"
                >
                    Dashboard
                </a>
                <a
                    href="/datasets/"
                    class="px-4 py-1.5 rounded-md text-sm transition-all {activeNav ===
                    'datasets'
                        ? 'bg-cat-surface1 text-cat-text font-bold shadow-sm'
                        : 'text-cat-subtext0 font-medium hover:text-cat-text hover:bg-cat-surface0'}"
                >
                    Datasets
                </a>
                <a
                    href="/reports/"
                    class="px-4 py-1.5 rounded-md text-sm transition-all {activeNav ===
                    'reports'
                        ? 'bg-cat-surface1 text-cat-text font-bold shadow-sm'
                        : 'text-cat-subtext0 font-medium hover:text-cat-text hover:bg-cat-surface0'}"
                >
                    Reportes
                </a>
                <a
                    href="/formatos/"
                    class="px-4 py-1.5 rounded-md text-sm transition-all {activeNav ===
                    'formatos'
                        ? 'bg-cat-surface1 text-cat-text font-bold shadow-sm'
                        : 'text-cat-subtext0 font-medium hover:text-cat-text hover:bg-cat-surface0'}"
                >
                    Formatos
                </a>
            </div>
        </div>

        <!-- User & Actions -->
        <div class="flex items-center gap-6">
            <div
                class="flex items-center gap-3 pl-6 border-l border-cat-surface0"
            >
                <div class="text-right sm:block">
                    <p class="text-sm font-bold text-cat-text leading-none">
                        {username}
                    </p>
                    <p class="text-xs text-cat-subtext0 mt-1">{email}</p>
                </div>
                <div
                    class="w-10 h-10 rounded-full bg-gradient-to-br from-cat-pink to-cat-mauve flex items-center justify-center text-cat-base font-bold shadow-lg shadow-cat-mauve/20 shrink-0"
                >
                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        class="w-5 h-5"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="lightgray"
                        stroke-width="2"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                    >
                        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"
                        ></path>
                        <circle cx="12" cy="7" r="4"></circle>
                    </svg>
                </div>
                <form action="/logout/" method="post">
                    <input
                        type="hidden"
                        name="csrfmiddlewaretoken"
                        value={csrfToken}
                    />
                    <button
                        type="submit"
                        class="p-2 text-cat-subtext0 hover:text-cat-red hover:bg-cat-red/10 rounded-lg transition-all"
                        title="Cerrar Sesión"
                    >
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            width="20"
                            height="20"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            stroke-width="2"
                            stroke-linecap="round"
                            stroke-linejoin="round"
                        >
                            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                            <polyline points="16 17 21 12 16 7" />
                            <line x1="21" y1="12" x2="9" y2="12" />
                        </svg>
                    </button>
                </form>
            </div>
        </div>
    </div>
</nav>
