document.addEventListener('DOMContentLoaded', () => {
    if (typeof simData === 'undefined') {
        console.error("Simulation data not found.");
        return;
    }

    // Use the final timestep for the live map values to simulate "current state"
    // Or we can calculate averages. Let's use the final state or averages.
    // For a dynamic feel, we will calculate the averages.
    let sumSolar = 0, sumTes = 0, sumElec = 0, sumMed = 0, sumAd = 0, sumRo = 0, sumWater = 0, sumExp = 0;
    
    simData.forEach(row => {
        sumSolar += row['Heat Generated (MWh_th)'];
        sumTes += row['TES State of Charge (%)'];
        sumElec += row['Electricity Generated (MWh_e)'];
        sumMed += row['Water Produced MED (m3)'];
        sumAd += row['Water Produced AD (m3)'];
        sumRo += row['Water Produced RO (m3)'];
        sumWater += row['Total Treated Water (m3)'];
        sumExp += row['Electricity Exported (MWh_e)'];
    });

    const len = simData.length;
    
    const avgSolar = sumSolar / len;
    const avgTes = sumTes / len;
    const avgElec = sumElec / len;
    const avgMed = sumMed / len;
    const avgAd = sumAd / len;
    const avgRo = sumRo / len;
    const avgWater = sumWater / len;
    const avgExp = sumExp / len;

    const formatNum = (num, dec=1) => num.toLocaleString(undefined, {minimumFractionDigits: dec, maximumFractionDigits: dec});

    function setVal(id, val, suffix) {
        const el = document.getElementById(id);
        if(el) el.innerText = formatNum(val) + suffix;
    }

    // Set values with a small delay for effect
    setTimeout(() => {
        setVal('val-solar', avgSolar, ' MWth');
        setVal('val-tes', avgTes, ' %');
        setVal('val-elec', avgElec, ' MWe');
        setVal('val-med', avgMed, ' m³/h');
        setVal('val-ad', avgAd, ' m³/h');
        setVal('val-ro', avgRo, ' m³/h');
        setVal('val-total-water', avgWater, ' m³/h');
        setVal('val-export', avgExp, ' MWe');
    }, 500);

});
