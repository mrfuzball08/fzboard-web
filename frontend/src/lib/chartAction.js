/**
 * Svelte action wrapping Chart.js for use with `use:chartAction`.
 *
 * Usage:
 *   <canvas use:chartAction={{ type: 'bar', data: {...}, options: {...} }}></canvas>
 */
import { Chart } from 'chart.js/auto';

// Catppuccin Mocha palette for chart colors
const CAT_COLORS = [
    'rgb(137, 180, 250)',   // blue
    'rgb(166, 227, 161)',   // green
    'rgb(250, 179, 135)',   // peach
    'rgb(203, 166, 247)',   // mauve
    'rgb(245, 194, 231)',   // pink
    'rgb(148, 226, 213)',   // teal
    'rgb(249, 226, 175)',   // yellow
    'rgb(243, 139, 168)',   // red
    'rgb(180, 190, 254)',   // lavender
    'rgb(242, 205, 205)',   // flamingo
];

const CAT_COLORS_ALPHA = CAT_COLORS.map(c => c.replace('rgb', 'rgba').replace(')', ', 0.6)'));

// Global Chart.js defaults for Catppuccin Mocha
Chart.defaults.color = 'rgb(166, 173, 200)';       // subtext0
Chart.defaults.borderColor = 'rgba(88, 91, 112, 0.3)'; // surface1/30
Chart.defaults.font.family = '"JetBrains Mono", "Fira Code", monospace';
Chart.defaults.font.size = 11;

export function chartAction(node, options) {
    if (!options || !options.type) return;

    // Apply Catppuccin palette to datasets if not already set
    const data = options.data || {};
    if (data.datasets) {
        data.datasets.forEach((ds, i) => {
            if (!ds.backgroundColor) {
                if (options.type === 'pie' || options.type === 'doughnut') {
                    ds.backgroundColor = CAT_COLORS_ALPHA;
                    ds.borderColor = CAT_COLORS;
                    ds.borderWidth = 2;
                } else if (options.type === 'scatter') {
                    ds.backgroundColor = CAT_COLORS_ALPHA[i % CAT_COLORS_ALPHA.length];
                    ds.borderColor = CAT_COLORS[i % CAT_COLORS.length];
                    ds.borderWidth = 2;
                    ds.pointRadius = 4;
                } else {
                    ds.backgroundColor = CAT_COLORS_ALPHA[i % CAT_COLORS_ALPHA.length];
                    ds.borderColor = CAT_COLORS[i % CAT_COLORS.length];
                    ds.borderWidth = 2;
                    ds.borderRadius = 4;
                }
            }
        });
    }

    // Merge in default options for dark theme
    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 600, easing: 'easeOutQuart' },
        plugins: {
            legend: {
                labels: {
                    usePointStyle: true,
                    padding: 16,
                    font: { size: 11 },
                },
            },
            tooltip: {
                backgroundColor: 'rgba(30, 30, 46, 0.95)',
                titleColor: 'rgb(205, 214, 244)',
                bodyColor: 'rgb(166, 173, 200)',
                borderColor: 'rgba(88, 91, 112, 0.5)',
                borderWidth: 1,
                padding: 12,
                cornerRadius: 8,
            },
        },
        scales: options.type !== 'pie' && options.type !== 'doughnut' ? {
            x: {
                grid: { color: 'rgba(88, 91, 112, 0.15)' },
                ticks: { color: 'rgb(166, 173, 200)', font: { size: 10 } },
            },
            y: {
                grid: { color: 'rgba(88, 91, 112, 0.15)' },
                ticks: { color: 'rgb(166, 173, 200)', font: { size: 10 } },
            },
        } : undefined,
        ...(options.options || {}),
    };

    let chart = new Chart(node, {
        type: options.type,
        data: data,
        options: chartOptions,
    });

    return {
        update(newOptions) {
            if (!newOptions || !newOptions.type) return;

            // If type changed, destroy and recreate
            if (newOptions.type !== chart.config.type) {
                chart.destroy();
                chart = new Chart(node, {
                    type: newOptions.type,
                    data: newOptions.data || {},
                    options: chartOptions,
                });
                return;
            }

            chart.data = newOptions.data || {};
            chart.options = { ...chartOptions, ...(newOptions.options || {}) };
            chart.update('none');
        },
        destroy() {
            chart.destroy();
        },
    };
}
