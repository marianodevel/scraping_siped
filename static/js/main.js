/**
 * Gestion del estado de las tareas de Celery via HTMX.
 */
const taskManager = {
    fasesFinalizadas: {},

    init() {
        document.body.addEventListener('htmx:beforeSwap', (evt) => this.handleBeforeSwap(evt));
        document.body.addEventListener('htmx:afterSwap', (evt) => this.handleAfterSwap(evt));
    },

    handleBeforeSwap(evt) {
        if (!evt.target.id || !evt.target.id.startsWith('estado-resultado-')) return;

        const faseId = evt.target.id.replace('estado-resultado-', '');
        if (this.fasesFinalizadas[faseId]) {
            evt.preventDefault();
            evt.target.removeAttribute('hx-trigger');
        }
    },

    handleAfterSwap(evt) {
        if (!evt.target.id || !evt.target.id.startsWith('estado-resultado-')) return;

        const faseId = evt.target.id.replace('estado-resultado-', '');
        if (this.fasesFinalizadas[faseId]) return;

        const badge = evt.target.querySelector('.status-badge');
        if (!badge) return;

        const status = badge.textContent.trim();
        const button = document.querySelector(`button[data-fase="${faseId}"]`);
        
        if (['SUCCESS', 'FAILURE', 'REVOKED'].includes(status)) {
            evt.target.removeAttribute('hx-trigger');
            this.fasesFinalizadas[faseId] = true;

            // Notificar a otros componentes que la tarea termino
            document.body.dispatchEvent(new Event('tareaFinalizada'));
            
            if (button) button.disabled = false;

            if (status === 'SUCCESS') {
                setTimeout(() => window.location.reload(), 1000);
            }
        } else if (['PENDING', 'STARTED', 'RETRY'].includes(status)) {
            if (button) button.disabled = true;
        }
    }
};

document.addEventListener('DOMContentLoaded', () => taskManager.init());