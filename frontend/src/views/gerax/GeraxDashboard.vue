<template>
  <div class="grid">
    <!-- Header -->
    <div class="col-12">
      <div class="card mb-0">
        <div class="flex align-items-center justify-content-between mb-3">
          <div>
            <h1 class="text-3xl font-bold text-900 mb-2">Gerax Hub</h1>
            <p class="text-color-secondary">NOC Dashboard — Visão central para monitoramento de infraestrutura, telefonia e chamadas</p>
          </div>
          <div class="flex gap-2">
            <Button icon="pi pi-refresh" rounded severity="secondary" @click="refreshData" :loading="isLoading" />
          </div>
        </div>
      </div>
    </div>

    <!-- KPI Cards - Row 1 -->
    <div class="col-12 lg:col-3 md:col-6">
      <div class="card">
        <div class="flex justify-content-between align-items-start mb-3">
          <div>
            <span class="text-color-secondary font-medium">CPU</span>
            <div class="text-3xl font-bold mt-2">{{ metrics.cpu }}%</div>
          </div>
          <span class="pi pi-microchip text-2xl" :style="{ color: getStatusColor(metrics.cpu) }"></span>
        </div>
        <ProgressBar :value="metrics.cpu" :show-value="false" :style="{ height: '6px' }"></ProgressBar>
        <span class="text-xs text-color-secondary mt-2 block">Status: {{ getStatusLabel(metrics.cpu) }}</span>
      </div>
    </div>

    <div class="col-12 lg:col-3 md:col-6">
      <div class="card">
        <div class="flex justify-content-between align-items-start mb-3">
          <div>
            <span class="text-color-secondary font-medium">Memória</span>
            <div class="text-3xl font-bold mt-2">{{ metrics.memory }}%</div>
          </div>
          <span class="pi pi-server text-2xl" :style="{ color: getStatusColor(metrics.memory) }"></span>
        </div>
        <ProgressBar :value="metrics.memory" :show-value="false" :style="{ height: '6px' }"></ProgressBar>
        <span class="text-xs text-color-secondary mt-2 block">Status: {{ getStatusLabel(metrics.memory) }}</span>
      </div>
    </div>

    <div class="col-12 lg:col-3 md:col-6">
      <div class="card">
        <div class="flex justify-content-between align-items-start mb-3">
          <div>
            <span class="text-color-secondary font-medium">Disco</span>
            <div class="text-3xl font-bold mt-2">{{ metrics.disk }}%</div>
          </div>
          <span class="pi pi-database text-2xl" :style="{ color: getStatusColor(metrics.disk) }"></span>
        </div>
        <ProgressBar :value="metrics.disk" :show-value="false" :style="{ height: '6px' }"></ProgressBar>
        <span class="text-xs text-color-secondary mt-2 block">Status: {{ getStatusLabel(metrics.disk) }}</span>
      </div>
    </div>

    <div class="col-12 lg:col-3 md:col-6">
      <div class="card">
        <div class="flex justify-content-between align-items-start mb-3">
          <div>
            <span class="text-color-secondary font-medium">Chamadas Ativas</span>
            <div class="text-3xl font-bold mt-2">{{ metrics.activeCalls }}</div>
          </div>
          <span class="pi pi-phone text-2xl" style="color: #2196F3"></span>
        </div>
        <div class="flex gap-2 mt-3">
          <div class="flex-1">
            <span class="text-xs text-color-secondary">Entrantes</span>
            <div class="font-bold text-lg">{{ metrics.inboundCalls }}</div>
          </div>
          <div class="flex-1">
            <span class="text-xs text-color-secondary">Saintes</span>
            <div class="font-bold text-lg">{{ metrics.outboundCalls }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- KPI Cards - Row 2 (Telephony Metrics) -->
    <div class="col-12 lg:col-3 md:col-6">
      <div class="card">
        <div class="flex justify-content-between align-items-start mb-3">
          <div>
            <span class="text-color-secondary font-medium">ASR</span>
            <div class="text-3xl font-bold mt-2">{{ metrics.asr }}%</div>
          </div>
          <span class="pi pi-check-circle text-2xl" style="color: #4CAF50"></span>
        </div>
        <div class="text-xs text-color-secondary">Taxa de Sucesso de Chamadas</div>
        <ProgressBar :value="metrics.asr" :show-value="false" :style="{ height: '6px', marginTop: '0.5rem' }"></ProgressBar>
      </div>
    </div>

    <div class="col-12 lg:col-3 md:col-6">
      <div class="card">
        <div class="flex justify-content-between align-items-start mb-3">
          <div>
            <span class="text-color-secondary font-medium">ACD</span>
            <div class="text-3xl font-bold mt-2">{{ metrics.acd }}s</div>
          </div>
          <span class="pi pi-hourglass text-2xl" style="color: #FF9800"></span>
        </div>
        <div class="text-xs text-color-secondary">Duração Média de Atendimento</div>
      </div>
    </div>

    <div class="col-12 lg:col-3 md:col-6">
      <div class="card">
        <div class="flex justify-content-between align-items-start mb-3">
          <div>
            <span class="text-color-secondary font-medium">PDD</span>
            <div class="text-3xl font-bold mt-2">{{ metrics.pdd }}ms</div>
          </div>
          <span class="pi pi-exclamation-triangle text-2xl" style="color: #F44336"></span>
        </div>
        <div class="text-xs text-color-secondary">Atraso de Discagem Pós-Chamada</div>
        <ProgressBar :value="Math.min(metrics.pdd / 10, 100)" :show-value="false" :style="{ height: '6px', marginTop: '0.5rem' }"></ProgressBar>
      </div>
    </div>

    <!-- Charts Row 1 -->
    <div class="col-12 lg:col-6">
      <div class="card">
        <h5 class="text-xl font-bold mb-3">CPU por Host</h5>
        <Chart type="bar" :data="cpuByHostChartData" :options="chartOptions"></Chart>
      </div>
    </div>

    <div class="col-12 lg:col-6">
      <div class="card">
        <h5 class="text-xl font-bold mb-3">Memória por Host</h5>
        <Chart type="bar" :data="memoryByHostChartData" :options="chartOptions"></Chart>
      </div>
    </div>

    <!-- Charts Row 2 -->
    <div class="col-12 lg:col-6">
      <div class="card">
        <h5 class="text-xl font-bold mb-3">Disco por Host</h5>
        <Chart type="doughnut" :data="diskByHostChartData" :options="chartOptions"></Chart>
      </div>
    </div>

    <div class="col-12 lg:col-6">
      <div class="card">
        <h5 class="text-xl font-bold mb-3">Chamadas Ativas por Horário</h5>
        <Chart type="line" :data="callsByTimeChartData" :options="chartOptions"></Chart>
      </div>
    </div>

    <!-- Charts Row 3 -->
    <div class="col-12 lg:col-6">
      <div class="card">
        <h5 class="text-xl font-bold mb-3">ASR por Router</h5>
        <Chart type="radar" :data="asrByRouterChartData" :options="chartOptions"></Chart>
      </div>
    </div>

    <div class="col-12 lg:col-6">
      <div class="card">
        <h5 class="text-xl font-bold mb-3">PDD por Router</h5>
        <Chart type="line" :data="pddByRouterChartData" :options="chartOptions"></Chart>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { Chart } from 'primevue/chart';
import { Button } from 'primevue/button';
import { ProgressBar } from 'primevue/progressbar';
import { apiGet } from '@/services/api';

// Loading state
const isLoading = ref(false);

// Main metrics
const metrics = ref({
  cpu: 62,
  memory: 48,
  disk: 35,
  activeCalls: 1247,
  inboundCalls: 742,
  outboundCalls: 505,
  asr: 94.2,
  acd: 245,
  pdd: 85
});

// Chart data computed properties
const cpuByHostChartData = computed(() => ({
  labels: ['Host-01', 'Host-02', 'Host-03', 'Host-04', 'Host-05'],
  datasets: [{
    label: 'CPU (%)',
    data: [62, 58, 71, 45, 55],
    backgroundColor: '#3B82F6',
    borderRadius: 4
  }]
}));

const memoryByHostChartData = computed(() => ({
  labels: ['Host-01', 'Host-02', 'Host-03', 'Host-04', 'Host-05'],
  datasets: [{
    label: 'Memória (%)',
    data: [48, 52, 41, 58, 44],
    backgroundColor: '#10B981',
    borderRadius: 4
  }]
}));

const diskByHostChartData = computed(() => ({
  labels: ['Host-01', 'Host-02', 'Host-03', 'Host-04', 'Host-05'],
  datasets: [{
    data: [35, 28, 42, 31, 26],
    backgroundColor: ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'],
    borderWidth: 2,
    borderColor: '#ffffff'
  }]
}));

const callsByTimeChartData = computed(() => ({
  labels: ['08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00'],
  datasets: [{
    label: 'Chamadas Ativas',
    data: [450, 680, 920, 1100, 950, 780, 1050, 1247, 1180, 920, 650],
    borderColor: '#3B82F6',
    backgroundColor: 'rgba(59, 130, 246, 0.1)',
    tension: 0.4,
    fill: true,
    pointRadius: 3,
    pointBackgroundColor: '#3B82F6'
  }]
}));

const asrByRouterChartData = computed(() => ({
  labels: ['Router-A', 'Router-B', 'Router-C', 'Router-D', 'Router-E'],
  datasets: [{
    label: 'ASR (%)',
    data: [94.2, 92.8, 95.1, 91.5, 93.7],
    borderColor: '#10B981',
    backgroundColor: 'rgba(16, 185, 129, 0.2)',
    borderWidth: 2,
    pointRadius: 4,
    pointBackgroundColor: '#10B981'
  }]
}));

const pddByRouterChartData = computed(() => ({
  labels: ['Router-A', 'Router-B', 'Router-C', 'Router-D', 'Router-E'],
  datasets: [{
    label: 'PDD (ms)',
    data: [85, 92, 78, 105, 88],
    borderColor: '#F59E0B',
    backgroundColor: 'rgba(245, 158, 11, 0.1)',
    tension: 0.4,
    fill: true,
    pointRadius: 3,
    pointBackgroundColor: '#F59E0B'
  }]
}));

// Chart options
const chartOptions = ref({
  maintainAspectRatio: true,
  responsive: true,
  plugins: {
    legend: {
      position: 'bottom',
      labels: {
        padding: 15,
        font: { size: 12 }
      }
    }
  },
  scales: {
    y: {
      beginAtZero: true,
      ticks: { font: { size: 11 } }
    },
    x: {
      ticks: { font: { size: 11 } }
    }
  }
});

// Utility functions
const getStatusColor = (value) => {
  if (value < 50) return '#4CAF50'; // Green
  if (value < 80) return '#F59E0B'; // Orange
  return '#F44336'; // Red
};

const getStatusLabel = (value) => {
  if (value < 50) return 'Ótimo';
  if (value < 80) return 'Bom';
  return 'Crítico';
};

// Refresh data from API
const refreshData = async () => {
  isLoading.value = true;
  try {
    // Aqui você pode fazer chamadas à API quando o backend estiver pronto
    // const data = await apiGet('/api/v1/gerax/dashboard');
    // Atualizar metrics com dados da API
    console.log('Dashboard atualizado');
  } catch (error) {
    console.error('Erro ao atualizar dashboard:', error);
  } finally {
    isLoading.value = false;
  }
};

// Load initial data
onMounted(async () => {
  // Aqui você pode carregar dados iniciais da API
  // await refreshData();
});
</script>

<style scoped>
:deep(.card) {
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
}

:deep(.p-progressbar) {
  height: 6px;
  border-radius: 4px;
}

.text-color-secondary {
  color: var(--text-color-secondary);
}

h1 {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
</style>
