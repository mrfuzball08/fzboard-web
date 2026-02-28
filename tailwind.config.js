/** @type {import('tailwindcss').Config} */
module.exports = {
    //  rutas de clases para generar el CSS
    content: [
        './templates/**/*.html',      // Templates globales
        './**/templates/**/*.html',   // Templates dentro de apps
        './static/**/*.js',           // Scripts JS propios si usas clases ahí
        './**/forms.py',              // Si defines clases CSS en widgets de Django
    ],
    theme: {
        extend: {
            // JetBrains Mono como la fuente "mono" por defecto
            fontFamily: {
                mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
                sans: ['"JetBrains Mono"', 'system-ui', 'sans-serif'],
            },
            // Paleta de colores Catppuccin Mocha
            colors: {
                cat: {
                    base: '#1e1e2e',      // Fondo principal
                    mantle: '#181825',    // Barras laterales / fondos más oscuros
                    crust: '#11111b',     // El fondo más oscuro posible
                    surface0: '#313244',  // Contenedores / Tarjetas
                    surface1: '#45475a',  // Bordes suaves / Hover
                    surface2: '#585b70',  // Hover más intenso
                    text: '#cdd6f4',      // Texto principal
                    subtext0: '#a6adc8',  // Texto secundario
                    overlay0: '#6c7086',  // Texto deshabilitado / iconos

                    // Acentos
                    mauve: '#cba6f7',     // Color primario (Morado)
                    blue: '#89b4fa',      // Información
                    green: '#a6e3a1',     // Éxito / Logs OK
                    yellow: '#f9e2af',    // Advertencia
                    peach: '#fab387',     // Naranja suave
                    red: '#f38ba8',       // Error / Peligro
                    pink: '#f5c2e7',      // Acento secundario
                }
            }
        },
    },
    plugins: [],
}
