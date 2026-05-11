<script setup>
import { getCurrentUser } from '@/services/auth';
import { computed } from 'vue';

const currentUser = computed(() => getCurrentUser());
const backTo = computed(() => (currentUser.value?.user_type === 'client' ? '/client/dashboard' : '/gerax/dashboard'));
</script>

<template>
    <div class="access-page bg-surface-50 dark:bg-surface-950">
        <section class="access-panel bg-surface-0 dark:bg-surface-900">
            <span class="access-icon">
                <i class="pi pi-lock"></i>
            </span>
            <h1>Acesso negado</h1>
            <p>Seu perfil não tem permissão para acessar esta área.</p>
            <Button label="Voltar ao sistema" icon="pi pi-arrow-left" as="router-link" :to="backTo" />
        </section>
    </div>
</template>

<style scoped>
.access-page {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 2rem;
}

.access-panel {
    width: min(100%, 34rem);
    border: 1px solid var(--surface-border);
    border-radius: 8px;
    padding: 2.5rem;
    text-align: center;
    box-shadow: 0 12px 35px rgba(15, 23, 42, 0.12);
}

.access-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 3.5rem;
    height: 3.5rem;
    margin-bottom: 1.25rem;
    border-radius: 8px;
    background: color-mix(in srgb, var(--primary-color) 14%, transparent);
    color: var(--primary-color);
    font-size: 1.5rem;
}

h1 {
    margin: 0 0 0.75rem;
    color: var(--text-color);
    font-size: 2rem;
}

p {
    margin: 0 0 1.5rem;
    color: var(--text-color-secondary);
}
</style>
