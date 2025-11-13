#!/bin/bash

# --- Configuración ---
# Directorio para almacenar los IDs de proceso (PIDs)
PIDS_DIR="./.pids"
FLASK_PID="$PIDS_DIR/flask.pid"
CELERY_PID="$PIDS_DIR/celery.pid"

# Comando de ejecución dentro del entorno virtual (asumiendo 'uv run')
UV_EXEC="uv run" 

# --- Función para Iniciar los Servicios ---
start_services() {
    echo "--- Iniciando Servicios de Desarrollo ---"
    
    # Crear directorios para PIDs y logs
    mkdir -p $PIDS_DIR
    mkdir -p ./logs

    # Advertencia sobre Redis (debe estar activo como servicio)
    echo ""
    echo "NOTA: Asegúrese de que Redis esté activo. Si no, Celery fallará."
    echo ""

    # 1. Iniciar Flask App
    if [ -f $FLASK_PID ]; then
        echo "Flask App ya está corriendo (PID: $(cat $FLASK_PID))."
    else
        # Ejecutamos en segundo plano con nohup y dirigimos la salida a un log
        nohup $UV_EXEC python app.py > logs/flask.log 2>&1 &
        echo $! > $FLASK_PID
        echo "Flask App iniciada (http://127.0.0.1:5001/). PID: $(cat $FLASK_PID)"
    fi

    # 2. Iniciar Celery Worker
    if [ -f $CELERY_PID ]; then
        echo "Celery Worker ya está corriendo (PID: $(cat $CELERY_PID))."
    else
        # El loglevel=info es importante para ver el progreso del scraping
        nohup $UV_EXEC celery -A tasks.celery_app worker --loglevel=info > logs/celery.log 2>&1 &
        echo $! > $CELERY_PID
        echo "Celery Worker iniciado. PID: $(cat $CELERY_PID)"
    fi
    
    echo "----------------------------------------"
    echo "Los logs están en las carpetas './logs/'."
}

# --- Función para Detener los Servicios ---
stop_services() {
    echo "--- Deteniendo Servicios de Desarrollo ---"

    # Función para detener un proceso por PID
    kill_process() {
        if [ -f $1 ]; then
            PID=$(cat $1)
            # El 2>/dev/null suprime el error si el proceso ya murió
            kill $PID 2>/dev/null
            if [ $? -eq 0 ]; then
                echo "$2 detenido (PID: $PID)."
            else
                echo "Advertencia: $2 PID $PID no encontrado o ya estaba detenido."
            fi
            rm -f $1
        else
            echo "$2 PID no encontrado. El servicio estaba detenido."
        fi
    }

    kill_process $FLASK_PID "Flask App"
    kill_process $CELERY_PID "Celery Worker"
    echo "----------------------------------------"
}

# --- Función para Mostrar el Estado ---
status_services() {
    echo "--- Estado de los Servicios ---"
    
    # Función interna para verificar si un PID está activo
    check_pid() {
        if [ -f $1 ]; then
            PID=$(cat $1)
            if ps -p $PID > /dev/null; then
                echo "ACTIVO (PID: $PID)"
            else
                echo "INACTIVO (PID $PID - Archivo viejo)"
            fi
        else
            echo "INACTIVO (PID file not found)"
        fi
    }

    echo -n "Flask App: "
    check_pid $FLASK_PID
    
    echo -n "Celery Worker: "
    check_pid $CELERY_PID
    
    echo "-----------------------------"
}

# --- Manejo de Argumentos ---

case "$1" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        stop_services
        start_services
        ;;
    status)
        status_services
        ;;
    *)
        echo "Uso: $0 {start|stop|restart|status}"
        exit 1
esac

exit 0
