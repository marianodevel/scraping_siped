/* static/js/formularios.js */

document.addEventListener("DOMContentLoaded", function() {
    // Referencias al DOM
    const localidadSelect = document.getElementById('localidad_select');
    const dependenciaSelect = document.getElementById('dependencia_select');
    const dataContainer = document.getElementById('dependencias-data');

    // Solo ejecutamos la lógica si los elementos existen en el DOM
    if (localidadSelect && dependenciaSelect && dataContainer) {
        
        // Parseamos el JSON inyectado de forma segura
        let dependenciasPorLocalidad = {};
        try {
            dependenciasPorLocalidad = JSON.parse(dataContainer.dataset.dependencias || '{}');
        } catch (e) {
            console.error("Error parseando dependencias:", e);
        }

        function actualizarDependencias() {
            const locId = localidadSelect.value;
            dependenciaSelect.innerHTML = '<option value="">Seleccione una dependencia...</option>';
            
            if (locId && dependenciasPorLocalidad[locId]) {
                for (const [depId, depName] of Object.entries(dependenciasPorLocalidad[locId])) {
                    const option = document.createElement('option');
                    option.value = depId;
                    option.textContent = depName;
                    dependenciaSelect.appendChild(option);
                }
            }
        }

        // Listeners
        localidadSelect.addEventListener('change', actualizarDependencias);
        
        // Ejecución inicial por si la página carga con una opción preseleccionada (ej. id 18)
        actualizarDependencias();
    }
});