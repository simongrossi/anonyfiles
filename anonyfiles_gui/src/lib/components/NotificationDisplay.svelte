<script lang="ts">
    import { notificationStore } from '../utils/jobService'; // Assurez-vous que le chemin est correct
    import { onDestroy } from 'svelte';

    let notification: { message: string, type: 'success' | 'error' } | null = null;
    const unsubscribe = notificationStore.subscribe(value => {
        notification = value;
        if (value) {
            setTimeout(() => {
                if (notification === value) { // Efface seulement si c'est la même notification
                    notificationStore.set(null);
                }
            }, 5000); // 5 secondes
        }
    });

    onDestroy(unsubscribe);
</script>

{#if notification}
    <div class="notification-banner type-{notification.type}" role="alert">
        <p>{notification.message}</p>
        <button class="close-button" on:click={() => notificationStore.set(null)} aria-label="Fermer la notification">&times;</button>
    </div>
{/if}

<style>
    .notification-banner {
        position: fixed;
        top: 20px;
        left: 50%;
        transform: translateX(-50%);
        padding: 1rem 1.5rem;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 1000;
        display: flex;
        justify-content: space-between;
        align-items: center;
        min-width: 300px;
        max-width: 600px;
        font-size: 0.9rem;
    }
    .notification-banner.type-success {
        background-color: var(--green-light, #e6f4ea);
        color: var(--green-dark, #256029);
        border: 1px solid var(--green-medium, #4caf50);
    }
    .notification-banner.type-error {
        background-color: #fdecea; /* Approx. .card-error de app.css */
        color: #a92323; /* Approx. .card-error de app.css */
        border: 1px solid #d9534f; /* Approx. .card-error de app.css */
    }
    .notification-banner .close-button {
        background: none;
        border: none;
        color: inherit;
        font-size: 1.5rem; /* Taille augmentée pour accessibilité */
        line-height: 1;
        margin-left: 1rem;
        cursor: pointer;
        padding: 0.25rem;
    }
</style>