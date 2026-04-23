<template>
  <div class="radar-chart-container">
    <canvas ref="chartCanvas"></canvas>
  </div>
</template>

<script>
import Chart from 'chart.js/auto';

export default {
  name: 'RadarChart',
  props: {
    evaluation: {
      type: Object,
      default: () => ({
        logic_score: 0, creativity_score: 0,
        expression_score: 0, knowledge_score: 0, overall_score: 0
      })
    }
  },
  data() { return { chart: null }; },
  watch: {
    evaluation: { handler() { this.updateChart(); }, deep: true }
  },
  mounted() { this.initChart(); },
  beforeUnmount() { if (this.chart) this.chart.destroy(); },
  methods: {
    initChart() {
      const ctx = this.$refs.chartCanvas.getContext('2d');
      this.chart = new Chart(ctx, {
        type: 'radar',
        data: {
          labels: ['逻辑思维', '创造力', '表达能力', '知识储备', '综合能力'],
          datasets: [{
            label: '能力评分',
            data: [
              this.evaluation.logic_score || 0,
              this.evaluation.creativity_score || 0,
              this.evaluation.expression_score || 0,
              this.evaluation.knowledge_score || 0,
              this.evaluation.overall_score || 0
            ],
            backgroundColor: 'rgba(0, 229, 255, 0.08)',
            borderColor: 'rgba(0, 229, 255, 0.8)',
            borderWidth: 2,
            pointBackgroundColor: [
              '#7c4dff', '#00e676', '#ffab00', '#448aff', '#00e5ff'
            ],
            pointBorderColor: '#0d1421',
            pointBorderWidth: 2,
            pointRadius: 5,
            pointHoverRadius: 7
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            r: {
              grid: {
                color: 'rgba(255, 255, 255, 0.06)',
                circular: true
              },
              angleLines: {
                color: 'rgba(255, 255, 255, 0.08)'
              },
              pointLabels: {
                color: '#8892a4',
                font: {
                  family: "'JetBrains Mono', monospace",
                  size: 11,
                  weight: '500'
                }
              },
              suggestedMin: 0,
              suggestedMax: 100,
              ticks: {
                backdropColor: 'transparent',
                color: '#5a6275',
                font: {
                  family: "'JetBrains Mono', monospace",
                  size: 9
                },
                stepSize: 20
              }
            }
          },
          plugins: {
            legend: {
              display: false
            },
            tooltip: {
              backgroundColor: 'rgba(13, 20, 33, 0.9)',
              titleColor: '#e8eaed',
              titleFont: { family: "'Orbitron', sans-serif", size: 11 },
              bodyColor: '#8892a4',
              bodyFont: { family: "'JetBrains Mono', monospace", size: 11 },
              padding: 12,
              borderColor: 'rgba(0, 229, 255, 0.15)',
              borderWidth: 1,
              cornerRadius: 8,
              callbacks: {
                label: function(context) {
                  return context.label + ': ' + context.parsed.r + ' 分';
                }
              }
            }
          }
        }
      });
    },
    updateChart() {
      if (this.chart) {
        this.chart.data.datasets[0].data = [
          this.evaluation.logic_score || 0,
          this.evaluation.creativity_score || 0,
          this.evaluation.expression_score || 0,
          this.evaluation.knowledge_score || 0,
          this.evaluation.overall_score || 0
        ];
        this.chart.update();
      }
    }
  }
};
</script>

<style scoped>
.radar-chart-container {
  width: 100%;
  height: 340px;
  position: relative;
}
</style>
