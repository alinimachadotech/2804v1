<script setup>
import { computed } from 'vue';
import { useRouter } from 'vue-router';
import { getCurrentUser, hasPermission, hasUserType, logout } from '@/services/auth';
import AppMenuItem from './AppMenuItem.vue';

const router = useRouter();
const currentUser = computed(() => getCurrentUser());

function handleLogout(event) {
    event?.originalEvent?.preventDefault();
    logout();
    router.push('/login');
}

const model = computed(() => {
    const sections = [];

    if (currentUser.value && hasUserType('employee') && hasPermission('dashboard:noc:view')) {
        sections.push({
            label: 'Gerax Hub',
            items: [
                {
                    label: 'NOC Dashboard',
                    icon: 'pi pi-chart-line',
                    to: '/gerax/dashboard'
                }
            ]
        });
    }

    if (currentUser.value && hasUserType('client') && hasPermission('dashboard:client:view')) {
        sections.push({
            label: 'Área do Cliente',
            items: [
                {
                    label: 'Dashboard',
                    icon: 'pi pi-fw pi-home',
                    to: '/client/dashboard'
                }
            ]
        });
    }

    if (currentUser.value) {
        sections.push({
            label: 'Conta',
            items: [
                {
                    label: 'Sair',
                    icon: 'pi pi-fw pi-sign-out',
                    command: handleLogout
                }
            ]
        });
    }

    return sections;
});
</script>

<template>
    <ul class="layout-menu">
        <template v-for="(item, i) in model" :key="item">
            <app-menu-item v-if="!item.separator" :item="item" :index="i"></app-menu-item>
            <li v-if="item.separator" class="menu-separator"></li>
        </template>
    </ul>
</template>

<style lang="scss" scoped></style>
