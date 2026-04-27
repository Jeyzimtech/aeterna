// Initialize Dashboard
document.addEventListener('DOMContentLoaded', () => {
    if (typeof simData === 'undefined') {
        console.error("Simulation data not found. Please ensure data.js is loaded.");
        return;
    }

    // 1. Calculate and Update KPIs
    let totalElecGen = 0;
    let totalElecExp = 0;
    let totalWater = 0;
    let tesSum = 0;

    simData.forEach(row => {
        totalElecGen += row['Electricity Generated (MWh_e)'];
        totalElecExp += row['Electricity Exported (MWh_e)'];
        totalWater += row['Total Treated Water (m3)'];
        tesSum += row['TES State of Charge (%)'];
    });

    const avgTes = tesSum / simData.length;

    // Format numbers
    const formatNum = (num, dec=2) => num.toLocaleString(undefined, {minimumFractionDigits: dec, maximumFractionDigits: dec});

    // Animate counter
    function animateValue(id, start, end, duration, decimals=2, suffix="") {
        const obj = document.getElementById(id);
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            // easeOutQuart
            const easeProgress = 1 - Math.pow(1 - progress, 4);
            const current = start + easeProgress * (end - start);
            obj.innerHTML = formatNum(current, decimals) + suffix;
            if (progress < 1) {
                window.requestAnimationFrame(step);
            } else {
                obj.innerHTML = formatNum(end, decimals) + suffix;
            }
        };
        window.requestAnimationFrame(step);
    }

    animateValue("kpi-elec-gen", 0, totalElecGen, 2000, 2, " MWh");
    animateValue("kpi-elec-exp", 0, totalElecExp, 2000, 2, " MWh");
    animateValue("kpi-water", 0, totalWater, 2000, 0, " m³");
    animateValue("kpi-tes", 0, avgTes, 2000, 1, " %");


    // 2. Setup Charts
    Chart.defaults.color = '#8e8e9f';
    Chart.defaults.font.family = "'Outfit', sans-serif";
    
    const labels = simData.map(d => `H${Math.round(d['Time (h)'])}`);
    
    // Chart options template
    const commonOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                labels: { color: '#f0f0f5', usePointStyle: true, boxWidth: 8 }
            },
            tooltip: {
                mode: 'index',
                intersect: false,
                backgroundColor: 'rgba(18, 18, 26, 0.9)',
                titleColor: '#fff',
                bodyColor: '#e0e0e0',
                borderColor: 'rgba(255,255,255,0.1)',
                borderWidth: 1
            }
        },
        scales: {
            x: {
                grid: { color: 'rgba(255, 255, 255, 0.05)', drawBorder: false },
                ticks: { maxTicksLimit: 12 }
            },
            y: {
                grid: { color: 'rgba(255, 255, 255, 0.05)', drawBorder: false }
            }
        },
        interaction: {
            mode: 'nearest',
            axis: 'x',
            intersect: false
        }
    };

    // A. Energy Chart
    const ctxEnergy = document.getElementById('energyChart').getContext('2d');
    new Chart(ctxEnergy, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Generated (MWh)',
                    data: simData.map(d => d['Electricity Generated (MWh_e)']),
                    borderColor: '#00ff99',
                    backgroundColor: 'rgba(0, 255, 153, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true,
                    pointRadius: 0
                },
                {
                    label: 'Exported (MWh)',
                    data: simData.map(d => d['Electricity Exported (MWh_e)']),
                    borderColor: '#00d2ff',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    tension: 0.4,
                    fill: false,
                    pointRadius: 0
                }
            ]
        },
        options: commonOptions
    });

    // B. Water Chart (Stacked Area)
    const ctxWater = document.getElementById('waterChart').getContext('2d');
    new Chart(ctxWater, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'RO (Electrical)',
                    data: simData.map(d => d['Water Produced RO (m3)']),
                    backgroundColor: 'rgba(0, 85, 255, 0.8)',
                    borderColor: '#0055ff',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0
                },
                {
                    label: 'MED (Thermal)',
                    data: simData.map(d => d['Water Produced MED (m3)']),
                    backgroundColor: 'rgba(0, 153, 255, 0.8)',
                    borderColor: '#0099ff',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0
                },
                {
                    label: 'AD (Waste Heat)',
                    data: simData.map(d => d['Water Produced AD (m3)']),
                    backgroundColor: 'rgba(0, 221, 255, 0.8)',
                    borderColor: '#00ddff',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0
                }
            ]
        },
        options: {
            ...commonOptions,
            scales: {
                ...commonOptions.scales,
                y: { stacked: true, grid: { color: 'rgba(255, 255, 255, 0.05)' } }
            }
        }
    });

    // C. TES Chart
    const ctxTes = document.getElementById('tesChart').getContext('2d');
    new Chart(ctxTes, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'TES State of Charge (%)',
                    data: simData.map(d => d['TES State of Charge (%)']),
                    borderColor: '#ff9900',
                    backgroundColor: 'rgba(255, 153, 0, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true,
                    pointRadius: 0
                }
            ]
        },
        options: {
            ...commonOptions,
            scales: {
                ...commonOptions.scales,
                y: { min: 0, max: 100, grid: { color: 'rgba(255, 255, 255, 0.05)' } }
            }
        }
    });

});
