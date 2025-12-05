document.addEventListener('DOMContentLoaded', () => {
    const fetchBtn = document.getElementById('fetchBtn');
    const simulateBtn = document.getElementById('simulateBtn');
    const convergenceBtn = document.getElementById('convergenceBtn');
    const paramsForm = document.getElementById('paramsForm');

    // Inputs
    const tickerInput = document.getElementById('tickerInput');
    const S0 = document.getElementById('S0');
    const K = document.getElementById('K'); // Strike
    const sigma = document.getElementById('sigma');
    const r = document.getElementById('r');
    const q = document.getElementById('q');
    const methodSelect = document.getElementById('method');
    const volSource = document.getElementById('volSource');

    let currentCurrency = '$'; // Default currency
    let chartInstance = null;
    let convergenceChartInstance = null;

    // Custom Dropdown Elements
    const methodSelectTrigger = document.getElementById('methodSelectTrigger');
    const methodHiddenInput = document.getElementById('method');
    const customOptions = document.querySelectorAll('.custom-option');

    // Custom Dropdown Logic
    if (methodSelectTrigger) {
        methodSelectTrigger.addEventListener('click', () => {
            methodSelectTrigger.classList.toggle('open');
        });
    }

    customOptions.forEach(option => {
        option.addEventListener('click', function (e) {
            e.stopPropagation();
            customOptions.forEach(opt => opt.classList.remove('selected'));
            this.classList.add('selected');

            const text = this.textContent;
            methodSelectTrigger.querySelector('.custom-select__trigger').textContent = text;

            const value = this.dataset.value;
            methodHiddenInput.value = value;

            // Handle Convergence Button Visibility
            if (convergenceBtn) {
                if (value === 'antithetic') {
                    convergenceBtn.classList.add('hidden');
                } else {
                    convergenceBtn.classList.remove('hidden');
                }
            }

            methodSelectTrigger.classList.remove('open');
        });
    });

    document.addEventListener('click', (e) => {
        if (methodSelectTrigger && !methodSelectTrigger.contains(e.target)) {
            methodSelectTrigger.classList.remove('open');
        }
    });

    // Fetch Stock Data
    fetchBtn.addEventListener('click', async () => {
        const ticker = tickerInput.value.toUpperCase();
        if (!ticker) return;

        fetchBtn.textContent = 'Loading...';
        fetchBtn.disabled = true;

        try {
            const response = await fetch('/api/get-stock-data', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ticker: ticker })
            });

            const data = await response.json();

            if (response.ok) {
                S0.value = data.current_price.toFixed(2);
                sigma.value = data.volatility.toFixed(4);
                r.value = data.risk_free_rate;
                K.value = data.current_price.toFixed(2);
                if (q) q.value = "0.0";

                // Update Currency Labels
                const currencySymbol = data.currency || '$';
                currentCurrency = currencySymbol;
                document.querySelectorAll('.currency-label').forEach(el => {
                    el.textContent = `(${currencySymbol})`;
                });

                if (volSource) volSource.textContent = `Historical Volatility (1Y) for ${ticker}`;
            } else {
                alert(data.error || 'Error fetching data');
            }
        } catch (e) {
            console.error(e);
            alert('Failed to connect to server');
        } finally {
            fetchBtn.textContent = 'Fetch Data';
            fetchBtn.disabled = false;
        }
    });

    // Run Simulation
    paramsForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        simulateBtn.textContent = 'Running Simulation...';
        simulateBtn.disabled = true;

        const payload = {
            S0: S0.value,
            K: K.value,
            T: document.getElementById('T').value,
            r: r.value,
            sigma: sigma.value,
            q: q ? q.value : 0.0,
            steps: document.getElementById('steps').value,
            method: methodSelect ? methodSelect.value : 'standard'
        };

        try {
            const response = await fetch('/api/simulate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (response.ok) {
                displayResults(data);
            } else {
                alert(data.error);
            }
        } catch (e) {
            console.error(e);
        } finally {
            simulateBtn.textContent = 'Run Simulation';
            simulateBtn.disabled = false;
        }
    });

    // Run Convergence Analysis
    if (convergenceBtn) {
        convergenceBtn.addEventListener('click', async () => {
            convergenceBtn.textContent = 'Analyzing...';
            convergenceBtn.disabled = true;

            const payload = {
                S0: S0.value,
                K: K.value,
                T: document.getElementById('T').value,
                r: r.value,
                sigma: sigma.value,
                q: q ? q.value : 0.0,
                method: methodSelect ? methodSelect.value : 'standard'
            };

            try {
                const response = await fetch('/api/convergence', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                const data = await response.json();

                if (response.ok) {
                    const section = document.getElementById('convergenceSection');
                    if (section) section.classList.remove('hidden');
                    renderConvergenceChart(data);
                } else {
                    alert(data.error);
                }
            } catch (e) {
                console.error(e);
            } finally {
                convergenceBtn.textContent = 'Analyze Convergence';
                convergenceBtn.disabled = false;
            }
        });
    }

    function displayResults(data) {
        document.getElementById('results').classList.remove('hidden');
        const convSection = document.getElementById('convergenceSection');
        if (convSection) convSection.classList.add('hidden');

        // Update Numbers
        const format = (num) => `${currentCurrency}${num.toFixed(4)}`;

        document.getElementById('bsCall').textContent = format(data.bs.call_price);
        document.getElementById('bsPut').textContent = format(data.bs.put_price);

        document.getElementById('mcCall').textContent = format(data.mc.call_price);
        document.getElementById('mcPut').textContent = format(data.mc.put_price);

        document.getElementById('mcCallErr').textContent = `±${data.mc.call_stderr.toFixed(4)}`;
        document.getElementById('mcPutErr').textContent = `±${data.mc.put_stderr.toFixed(4)}`;

        // Render Chart
        renderChart(data.mc);
    }

    function renderChart(mcData) {
        const ctx = document.getElementById('simulationChart').getContext('2d');

        if (chartInstance) {
            chartInstance.destroy();
        }

        const labels = mcData.steps;
        const datasets = mcData.paths.map((path, index) => ({
            label: `Path ${index + 1}`,
            data: path,
            borderColor: 'rgba(99, 102, 241, 0.3)',
            borderWidth: 1,
            pointRadius: 0,
            fill: false,
            tension: 0.1
        }));

        try {
            chartInstance = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: datasets
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        title: { display: true, text: 'Monte Carlo Sample Paths (First 20)', color: '#fff' }
                    },
                    scales: {
                        x: {
                            grid: { color: 'rgba(255,255,255,0.1)' },
                            ticks: { color: '#a0a0b0', maxTicksLimit: 10 }
                        },
                        y: {
                            grid: { color: 'rgba(255,255,255,0.1)' },
                            ticks: { color: '#a0a0b0' }
                        }
                    }
                }
            });
        } catch (e) {
            console.error(e);
        }
    }

    function renderConvergenceChart(data) {
        const ctx = document.getElementById('convergenceChart').getContext('2d');

        if (convergenceChartInstance) {
            convergenceChartInstance.destroy();
        }

        convergenceChartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.x,
                datasets: [
                    {
                        label: 'Monte Carlo Estimate',
                        data: data.y,
                        borderColor: '#10b981',
                        borderWidth: 2,
                        tension: 0.1,
                        pointRadius: 2
                    },
                    {
                        label: 'Black-Scholes Price',
                        data: data.bs_line,
                        borderColor: '#ef4444',
                        borderWidth: 2,
                        borderDash: [5, 5],
                        pointRadius: 0,
                        fill: false
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: { display: true, text: 'Convergence Check: Price vs Simulations', color: '#fff' },
                    legend: { labels: { color: '#fff' } }
                },
                scales: {
                    x: {
                        title: { display: true, text: 'Number of Simulations', color: '#a0a0b0' },
                        grid: { color: 'rgba(255,255,255,0.1)' },
                        ticks: { color: '#a0a0b0' }
                    },
                    y: {
                        title: { display: true, text: 'Option Price', color: '#a0a0b0' },
                        grid: { color: 'rgba(255,255,255,0.1)' },
                        ticks: { color: '#a0a0b0' }
                    }
                }
            }
        });
    }
});
