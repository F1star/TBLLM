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
        logic_score: 0,
        creativity_score: 0,
        expression_score: 0,
        knowledge_score: 0,
        overall_score: 0
      })
    }
  },
  data() {
    return {
      chart: null
    };
  },
  watch: {
    evaluation: {
      handler() {
        this.updateChart();
      },
      deep: true
    }
  },
  mounted() {
    this.initChart();
  },
  beforeUnmount() {
    if (this.chart) {
      this.chart.destroy();
    }
  },
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
            backgroundColor: 'rgba(102, 126, 234, 0.2)',
            borderColor: 'rgba(102, 126, 234, 1)',
            borderWidth: 2,
            pointBackgroundColor: 'rgba(102, 126, 234, 1)',
            pointBorderColor: '#fff',
            pointHoverBackgroundColor: '#fff',
            pointHoverBorderColor: 'rgba(102, 126, 234, 1)'
          }]
        },
        options: {
          scales: {
            r: {
              angleLines: {
                display: true
              },
              suggestedMin: 0,
              suggestedMax: 100
            }
          },
          plugins: {
            legend: {
              display: true,
              position: 'top'
            },
            tooltip: {
              callbacks: {
                label: function(context) {
                  return context.label + ': ' + context.parsed.r + '分';
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
  height: 400px;
  position: relative;
}
</style>