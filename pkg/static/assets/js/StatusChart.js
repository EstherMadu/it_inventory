const statusData = {
  labels: ['inventory', 'assigned', 'repair', 'retired'],
  datasets: [{
    data: [
      statusCounts.inventory,
      statusCounts.assigned,
      statusCounts.repair,
      statusCounts.retired
    ],
    backgroundColor: ['#0d6efd', '#20c997', '#ffc107', '#6c757d'],
    hoverOffset: 6
  }]
};

const ctx = document.getElementById('statusChart');
if (ctx) {
  new Chart(ctx, {
    type: 'doughnut',
    data: statusData,
    options: { plugins: { legend: { position: 'bottom' } } }
  });
}
