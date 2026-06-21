// ============================================================
// Global temperature anomaly chart — Berkeley Earth annual data
// Data: Berkeley Earth, CC BY-NC 4.0, berkeleyearth.org
// Baseline: anomalies relative to the Jan 1951–Dec 1980 average
// ============================================================

(function () {
  const container = document.getElementById('chart-global-temp');
  if (!container) return;

  // ---- read theme colors from CSS variables so the chart matches the site ----
  const styles = getComputedStyle(document.documentElement);
  const color = (name) => styles.getPropertyValue(name).trim();
  const COLORS = {
    ice: color('--ice') || '#5FA8D3',
    ember: color('--ember') || '#D1495B',
    fog: color('--fog') || '#8A93A0',
    line: color('--line') || '#262C34',
    paper: color('--paper') || '#F2F0EA',
  };

  const margin = { top: 16, right: 24, bottom: 28, left: 44 };
  let width, height;

  const svg = d3.select(container)
    .append('svg')
    .attr('width', '100%')
    .attr('preserveAspectRatio', 'xMidYMid meet');

  const g = svg.append('g');
  const gridG = g.append('g').attr('class', 'grid');
  const zeroLine = g.append('line').attr('class', 'zero-line')
    .attr('stroke', COLORS.fog).attr('stroke-dasharray', '2,3').attr('stroke-width', 1);
  const annualPath = g.append('path').attr('class', 'line-annual')
    .attr('fill', 'none').attr('stroke', COLORS.fog).attr('stroke-width', 1).attr('opacity', 0.55);
  const trendPath = g.append('path').attr('class', 'line-trend')
    .attr('fill', 'none').attr('stroke', COLORS.ember).attr('stroke-width', 2.5);
  const xAxisG = g.append('g').attr('class', 'x-axis');
  const yAxisG = g.append('g').attr('class', 'y-axis');

  const focus = g.append('g').attr('class', 'focus').style('display', 'none');
  focus.append('line').attr('class', 'focus-line')
    .attr('stroke', COLORS.fog).attr('stroke-width', 1);
  focus.append('circle').attr('r', 4).attr('fill', COLORS.ember)
    .attr('stroke', COLORS.paper).attr('stroke-width', 1.5);

  const tooltip = d3.select(container)
    .append('div')
    .attr('class', 'chart-tooltip')
    .style('opacity', 0);

  const overlay = g.append('rect').attr('class', 'overlay').attr('fill', 'none')
    .attr('pointer-events', 'all');

  let data = [];

  function render() {
    width = container.clientWidth - margin.left - margin.right;
    height = container.clientHeight - margin.top - margin.bottom;
    if (width <= 0 || height <= 0 || data.length === 0) return;

    svg.attr('viewBox', `0 0 ${width + margin.left + margin.right} ${height + margin.top + margin.bottom}`);
    g.attr('transform', `translate(${margin.left},${margin.top})`);

    const x = d3.scaleLinear().domain(d3.extent(data, d => d.year)).range([0, width]);
    const y = d3.scaleLinear()
      .domain([d3.min(data, d => d.annual) - 0.1, d3.max(data, d => d.annual) + 0.1])
      .range([height, 0]);

    gridG.attr('opacity', 0.5).call(
      d3.axisLeft(y).tickSize(-width).tickFormat('').ticks(6)
    );
    gridG.selectAll('line').attr('stroke', COLORS.line);
    gridG.select('.domain').remove();

    zeroLine.attr('x1', 0).attr('x2', width).attr('y1', y(0)).attr('y2', y(0));

    const lineAnnual = d3.line().x(d => x(d.year)).y(d => y(d.annual));
    annualPath.datum(data).attr('d', lineAnnual);

    const trendData = data.filter(d => d.trend !== null);
    const lineTrend = d3.line().x(d => x(d.year)).y(d => y(d.trend));
    trendPath.datum(trendData).attr('d', lineTrend);

    xAxisG.attr('transform', `translate(0,${height})`)
      .call(d3.axisBottom(x).tickFormat(d3.format('d')).ticks(Math.min(8, width / 80)));
    yAxisG.call(d3.axisLeft(y).ticks(6).tickFormat(d => (d > 0 ? '+' : '') + d.toFixed(1) + '°'));

    [xAxisG, yAxisG].forEach(axis => {
      axis.selectAll('text').attr('fill', COLORS.fog).attr('font-size', '11px').attr('font-family', 'IBM Plex Mono, monospace');
      axis.selectAll('line,path').attr('stroke', COLORS.line);
    });

    const bisect = d3.bisector(d => d.year).left;
    overlay.attr('width', width).attr('height', height)
      .on('mouseover', () => { focus.style('display', null); tooltip.style('opacity', 1); })
      .on('mouseout', () => { focus.style('display', 'none'); tooltip.style('opacity', 0); })
      .on('mousemove', function (event) {
        const x0 = x.invert(d3.pointer(event, this)[0]);
        const i = bisect(data, x0, 1);
        const d0 = data[i - 1], d1 = data[i];
        const d = d1 && (x0 - d0.year > d1.year - x0) ? d1 : d0;
        if (!d) return;
        focus.select('.focus-line').attr('x1', x(d.year)).attr('x2', x(d.year)).attr('y1', 0).attr('y2', height);
        focus.select('circle').attr('cx', x(d.year)).attr('cy', y(d.annual));
        tooltip
          .style('left', (x(d.year) + margin.left + 12) + 'px')
          .style('top', (y(d.annual) + margin.top - 10) + 'px')
          .html(`<strong>${d.year}</strong><br>${d.annual > 0 ? '+' : ''}${d.annual.toFixed(2)}°C vs. 1951–1980`);
      });
  }

  d3.csv('dataAnnualTemperatureGlobalBerkeley.csv', d3.autoType).then(rows => {
    data = rows
      .filter(d => d.annual_anomaly_c !== null && !Number.isNaN(d.annual_anomaly_c))
      .map(d => ({
        year: d.year,
        annual: d.annual_anomaly_c,
        trend: (d.five_year_anomaly_c === null || Number.isNaN(d.five_year_anomaly_c)) ? null : d.five_year_anomaly_c,
      }));
    render();
  }).catch(err => {
    container.innerHTML = '<p class="chart-error">Could not load temperature data. Check if DataWorldAnnualBerkeleyGlobalTempAvg.csv is present next to this page.</p>';
    console.error(err);
  });

  window.addEventListener('resize', render);
})();
