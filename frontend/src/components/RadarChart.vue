<script setup>
import { ref, onMounted, watch } from 'vue'
import { Radar } from 'vue-chartjs'
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
} from 'chart.js'

ChartJS.register(RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend)

const props = defineProps({
  labels: { type: Array, required: true },
  values: { type: Array, required: true },
})

const chartData = ref({
  labels: props.labels,
  datasets: [
    {
      label: '评分',
      data: props.values,
      fill: true,
      backgroundColor: 'rgba(0, 122, 255, 0.12)',
      borderColor: 'rgba(0, 122, 255, 0.8)',
      borderWidth: 2,
      pointBackgroundColor: '#007aff',
      pointBorderColor: '#fff',
      pointBorderWidth: 2,
      pointRadius: 5,
      pointHoverRadius: 7,
    },
  ],
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: true,
  scales: {
    r: {
      beginAtZero: true,
      max: 100,
      min: 0,
      ticks: {
        stepSize: 20,
        backdropColor: 'transparent',
        font: { size: 11 },
        color: '#aeaeb2',
      },
      pointLabels: {
        font: { size: 14, weight: '600' },
        color: '#1d1d1f',
      },
      grid: {
        color: 'rgba(0, 0, 0, 0.06)',
      },
      angleLines: {
        color: 'rgba(0, 0, 0, 0.06)',
      },
    },
  },
  plugins: {
    legend: { display: false },
  },
}

watch(() => [props.labels, props.values], () => {
  chartData.value = {
    labels: props.labels,
    datasets: [{
      label: '评分',
      data: props.values,
      fill: true,
      backgroundColor: 'rgba(0, 122, 255, 0.12)',
      borderColor: 'rgba(0, 122, 255, 0.8)',
      borderWidth: 2,
      pointBackgroundColor: '#007aff',
      pointBorderColor: '#fff',
      pointBorderWidth: 2,
      pointRadius: 5,
      pointHoverRadius: 7,
    }],
  }
})
</script>

<template>
  <div style="max-width:500px;margin:0 auto;">
    <Radar :data="chartData" :options="chartOptions" />
  </div>
</template>
