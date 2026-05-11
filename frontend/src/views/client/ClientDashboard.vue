<script setup>
const cards = [
    {
        title: 'Chamadas',
        value: '128',
        detail: 'Ultimas 24 horas',
        icon: 'pi pi-phone',
        color: '#2563eb'
    },
    {
        title: 'Consumo',
        value: '42 GB',
        detail: 'Ciclo atual',
        icon: 'pi pi-chart-line',
        color: '#16a34a'
    },
    {
        title: 'Faturas',
        value: '2',
        detail: 'Pendentes',
        icon: 'pi pi-file',
        color: '#f59e0b'
    },
    {
        title: 'Status',
        value: 'Online',
        detail: 'Servicos ativos',
        icon: 'pi pi-check-circle',
        color: '#0f766e'
    }
];
</script>

<template>
    <div class="grid">
        <div class="col-12">
            <div class="card mb-0">
                <h1 class="text-3xl font-bold text-900 mb-2">Área do Cliente</h1>
                <p class="text-color-secondary m-0">Resumo dos principais indicadores da sua conta.</p>
            </div>
        </div>

        <div v-for="card in cards" :key="card.title" class="col-12 md:col-6 xl:col-3">
            <div class="card h-full">
                <div class="flex align-items-start justify-content-between gap-3">
                    <div>
                        <span class="text-color-secondary font-medium">{{ card.title }}</span>
                        <div class="text-3xl font-bold mt-2">{{ card.value }}</div>
                        <span class="text-color-secondary text-sm mt-2 block">{{ card.detail }}</span>
                    </div>
                    <span class="client-icon" :style="{ color: card.color, backgroundColor: `${card.color}18` }">
                        <i :class="card.icon"></i>
                    </span>
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>
.client-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 3rem;
    height: 3rem;
    border-radius: 8px;
    font-size: 1.35rem;
}

.text-color-secondary {
    color: var(--text-color-secondary);
}
</style>

