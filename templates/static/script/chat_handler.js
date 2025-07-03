if (window.predictionData) {
    const ctx = document.getElementById('scoreChart').getContext('2d');
    const phishingScore = window.predictionData.phishingScore;
    const safeScore = window.predictionData.safeScore;

    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: ['Phishing Probability', 'Legitimate Probability'],
            datasets: [{
                data: [phishingScore, safeScore],
                backgroundColor: ['rgba(239, 68, 68, 0.7)', 'rgba(16, 185, 129, 0.7)'],
                borderColor: ['rgba(239, 68, 68, 1)', 'rgba(16, 185, 129, 1)'],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}
