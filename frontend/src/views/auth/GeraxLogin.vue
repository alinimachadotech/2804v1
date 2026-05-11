<script setup>
import { login } from '@/services/auth';
import { ref } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();

const email = ref('');
const password = ref('');
const errorMessage = ref('');
const isLoading = ref(false);

async function handleSubmit() {
    errorMessage.value = '';
    isLoading.value = true;

    try {
        const { user } = await login(email.value, password.value);
        await router.push(user.user_type === 'client' ? '/client/dashboard' : '/gerax/dashboard');
    } catch {
        errorMessage.value = 'Nao foi possivel entrar. Confira seu e-mail e senha.';
    } finally {
        isLoading.value = false;
    }
}
</script>

<template>
    <div class="login-page bg-surface-50 dark:bg-surface-950">
        <section class="login-shell bg-surface-0 dark:bg-surface-900">
            <div class="login-brand">
                <span class="brand-mark">G</span>
                <div>
                    <h1>Gerax Hub</h1>
                    <p>Acesso seguro ao Gerax Hub</p>
                </div>
            </div>

            <form class="login-form" @submit.prevent="handleSubmit">
                <Message v-if="errorMessage" severity="error" :closable="false">{{ errorMessage }}</Message>

                <div class="field-group">
                    <label for="email">Email</label>
                    <InputText id="email" v-model="email" type="email" autocomplete="email" placeholder="voce@empresa.com" fluid required />
                </div>

                <div class="field-group">
                    <label for="password">Senha</label>
                    <Password id="password" v-model="password" autocomplete="current-password" placeholder="Sua senha" :feedback="false" toggleMask fluid required />
                </div>

                <Button type="submit" label="Entrar" icon="pi pi-sign-in" class="w-full" :loading="isLoading" />
            </form>
        </section>
    </div>
</template>

<style scoped>
.login-page {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 2rem;
}

.login-shell {
    width: min(100%, 28rem);
    border: 1px solid var(--surface-border);
    border-radius: 8px;
    padding: 2rem;
    box-shadow: 0 12px 35px rgba(15, 23, 42, 0.12);
}

.login-brand {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 2rem;
}

.brand-mark {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 3rem;
    height: 3rem;
    border-radius: 8px;
    background: var(--primary-color);
    color: var(--primary-contrast-color);
    font-size: 1.5rem;
    font-weight: 700;
}

h1 {
    margin: 0 0 0.25rem;
    color: var(--text-color);
    font-size: 1.75rem;
}

p {
    margin: 0;
    color: var(--text-color-secondary);
}

.login-form,
.field-group {
    display: flex;
    flex-direction: column;
}

.login-form {
    gap: 1.25rem;
}

.field-group {
    gap: 0.5rem;
}

label {
    color: var(--text-color);
    font-weight: 600;
}
</style>

