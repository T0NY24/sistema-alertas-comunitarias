"""
API Gateway - Sistema de Alertas Comunitarias Verificadas
FastAPI REST API para consulta de eventos y gestión del sistema
"""
import os
from datetime import datetime
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import psycopg2
from psycopg2.extras import RealDictCursor
import structlog
import pika
import json
import docker

# Configurar logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()

# Configuración
DATABASE_URL = os.getenv('DATABASE_URL')
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'rabbitmq')
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'sacv')
RABBITMQ_PASS = os.getenv('RABBITMQ_PASS', 'sacv_password')

# Pool de conexiones simple
db_pool = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación"""
    global db_pool
    logger.info("api_gateway_starting")
    # Aquí podríamos inicializar un pool de conexiones
    yield
    logger.info("api_gateway_stopping")

# Crear aplicación FastAPI
app = FastAPI(
    title="SACV API",
    description="Sistema de Alertas Comunitarias Verificadas - API REST",
    version="1.0.0",
    lifespan=lifespan
)

# Configurar CORS mejorado
origins = [
    "http://217.216.67.99:3001",
    "http://217.216.67.99:8001",
    "http://localhost:3000",
    "http://localhost:3001",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Modelos Pydantic
# ============================================================================

class RawEventResponse(BaseModel):
    """Modelo de respuesta para eventos crudos"""
    raw_id: str
    source_id: str
    fetched_at: datetime
    raw_hash: str
    title: Optional[str] = None
    url: Optional[str] = None

class EventResponse(BaseModel):
    """Modelo de respuesta para eventos normalizados"""
    event_id: str
    type: str
    occurred_at: datetime
    zone: Optional[str] = None
    severity: Optional[str] = None
    title: str
    description: Optional[str] = None
    evidence_url: Optional[str] = None
    status: str
    score: int
    created_at: datetime

class SourceResponse(BaseModel):
    """Modelo de respuesta para fuentes"""
    source_id: str
    name: str
    type: str
    domain: str
    active: bool
    frequency_sec: int

class ProvinceResponse(BaseModel):
    """Modelo de respuesta para provincias"""
    province_id: int
    name: str

class EventCreateRequest(BaseModel):
    """Modelo para crear un nuevo evento manualmente"""
    type: str
    severity: str
    zone: Optional[str] = None
    province_id: Optional[int] = None  # ID de provincia para notificaciones
    title: str
    description: Optional[str] = None
    evidence_url: Optional[str] = None
    source_id: Optional[str] = None
    status: str = "NO_VERIFICADO"

class EventUpdateRequest(BaseModel):
    """Modelo para actualizar el estado de un evento"""
    status: str = Field(..., description="Nuevo estado: CONFIRMADO o NO_VERIFICADO")

class ContainerInfo(BaseModel):
    """Modelo de información de contenedor Docker"""
    name: str
    status: str
    state: str
    image: str
    created: str

class StatsResponse(BaseModel):
    """Modelo de respuesta para estadísticas"""
    total_sources: int
    active_sources: int
    total_raw_events: int
    total_events: int
    events_by_status: dict
    last_scraping: Optional[datetime] = None

# ============================================================================
# Dependencias
# ============================================================================

def get_db():
    """Obtener conexión a la base de datos"""
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        conn.close()

# ============================================================================
# Endpoints
# ============================================================================

@app.get("/", tags=["Health"])
def read_root():
    """Endpoint raíz - Health check"""
    return {
        "message": "SACV API v1.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health", tags=["Health"])
def health_check():
    """Health check detallado"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        db_status = "healthy"
    except Exception as e:
        logger.error("health_check_db_failed", error=str(e))
        db_status = "unhealthy"
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/raw-events", response_model=List[RawEventResponse], tags=["Events"])
def get_raw_events(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db = Depends(get_db)
):
    """Obtener eventos crudos (raw) capturados por los scrapers"""
    cursor = db.cursor(cursor_factory=RealDictCursor)
    
    try:
        cursor.execute("""
            SELECT 
                raw_id::text,
                source_id::text,
                fetched_at,
                raw_hash,
                raw_payload->>'title' as title,
                raw_payload->>'url' as url
            FROM raw_events
            ORDER BY fetched_at DESC
            LIMIT %s OFFSET %s
        """, (limit, offset))
        
        events = cursor.fetchall()
        
        logger.info("raw_events_fetched", count=len(events))
        
        return [dict(event) for event in events]
        
    except Exception as e:
        logger.error("get_raw_events_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Error fetching raw events")
    finally:
        cursor.close()

@app.get("/api/raw-events/{raw_id}", response_model=dict, tags=["Events"])
def get_raw_event_detail(raw_id: str, db = Depends(get_db)):
    """Obtener detalle completo de un evento crudo"""
    cursor = db.cursor(cursor_factory=RealDictCursor)
    
    try:
        cursor.execute("""
            SELECT 
                raw_id::text,
                source_id::text,
                fetched_at,
                raw_payload,
                raw_hash
            FROM raw_events
            WHERE raw_id = %s
        """, (raw_id,))
        
        event = cursor.fetchone()
        
        if not event:
            raise HTTPException(status_code=404, detail="Raw event not found")
        
        return dict(event)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_raw_event_detail_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Error fetching event detail")
    finally:
        cursor.close()

@app.get("/api/events", response_model=List[EventResponse], tags=["Events"])
def get_events(
    type: Optional[str] = Query(None),
    zone: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db = Depends(get_db)
):
    """Obtener eventos normalizados con filtros opcionales"""
    cursor = db.cursor(cursor_factory=RealDictCursor)
    
    try:
        query = """
            SELECT 
                event_id::text,
                type,
                occurred_at,
                zone,
                severity,
                title,
                description,
                evidence_url,
                status,
                score,
                created_at
            FROM events
            WHERE 1=1
        """
        params = []
        
        if type:
            query += " AND type = %s"
            params.append(type)
        
        if zone:
            query += " AND zone = %s"
            params.append(zone)
        
        if status:
            query += " AND status = %s"
            params.append(status)
        
        query += " ORDER BY occurred_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        events = cursor.fetchall()
        
        logger.info("events_fetched", count=len(events), filters={
            "type": type, "zone": zone, "status": status
        })
        
        return [dict(event) for event in events]
        
    except Exception as e:
        logger.error("get_events_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Error fetching events")
    finally:
        cursor.close()

@app.get("/api/events/{event_id}", response_model=EventResponse, tags=["Events"])
def get_event_detail(event_id: str, db = Depends(get_db)):
    """Obtener detalle de un evento normalizado"""
    cursor = db.cursor(cursor_factory=RealDictCursor)
    
    try:
        cursor.execute("""
            SELECT 
                event_id::text,
                type,
                occurred_at,
                zone,
                severity,
                title,
                description,
                evidence_url,
                status,
                score,
                created_at
            FROM events
            WHERE event_id = %s
        """, (event_id,))
        
        event = cursor.fetchone()
        
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        return dict(event)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_event_detail_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Error fetching event detail")
    finally:
        cursor.close()

@app.post("/api/events", response_model=EventResponse, tags=["Events"], status_code=201)
def create_event(
    event_data: EventCreateRequest,
    db = Depends(get_db)
):
    """Crear un nuevo evento manualmente (desde simulador)"""
    cursor = db.cursor(cursor_factory=RealDictCursor)
    
    try:
        import hashlib
        from datetime import datetime
        
        logger.info("create_event_request", data=event_data.dict())
        
        # Generar dedup_hash para el evento
        # Para eventos manuales, usamos timestamp completo para permitir múltiples pruebas
        dedup_string = f"{event_data.type}:{event_data.title}:{datetime.utcnow().timestamp()}"
        dedup_hash = hashlib.sha256(dedup_string.encode()).hexdigest()
        
        # Insertar evento en la base de datos
        cursor.execute("""
            INSERT INTO events (
                type, 
                occurred_at, 
                zone, 
                severity, 
                title, 
                description, 
                evidence_url, 
                source_id, 
                dedup_hash, 
                status, 
                score,
                province_id
            )
            VALUES (%s, NOW(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING 
                event_id::text,
                type,
                occurred_at,
                zone,
                severity,
                title,
                description,
                evidence_url,
                status,
                score,
                created_at,
                province_id
        """, (
            event_data.type,
            event_data.zone,
            event_data.severity,
            event_data.title,
            event_data.description,
            event_data.evidence_url,
            event_data.source_id,
            dedup_hash,
            event_data.status,
            50,  # Score default para eventos manuales
            event_data.province_id  # Agregar province_id para notificaciones
        ))
        
        created_event = cursor.fetchone()
        db.commit()
        
        
        logger.info(
            "event_created",
            event_id=created_event['event_id'],
            type=event_data.type,
            title=event_data.title
        )

        # Si el evento nace como CONFIRMADO, publicarlo a RabbitMQ
        if event_data.status == 'CONFIRMADO':
            try:
                publish_confirmed_event(dict(created_event))
                logger.info(
                    "confirmed_event_published_on_create",
                    event_id=created_event['event_id']
                )
            except Exception as e:
                logger.error(
                    "failed_to_publish_confirmed_event_on_create",
                    event_id=created_event['event_id'],
                    error=str(e)
                )
        
        return dict(created_event)
        
    except Exception as e:
        db.rollback()
        logger.error("create_event_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Error creating event: {str(e)}")
    finally:
        cursor.close()

@app.patch("/api/events/{event_id}", response_model=EventResponse, tags=["Events"])
def update_event_status(
    event_id: str,
    update_data: EventUpdateRequest,
    db = Depends(get_db)
):
    """Actualizar el estado de un evento (Confirmar o Rechazar)"""
    cursor = db.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Validar que el estado sea válido
        valid_statuses = ['CONFIRMADO', 'NO_VERIFICADO']
        if update_data.status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Status inválido. Valores permitidos: {valid_statuses}"
            )
        
        # Actualizar el evento en la base de datos
        cursor.execute("""
            UPDATE events
            SET status = %s, updated_at = NOW()
            WHERE event_id = %s
            RETURNING 
                event_id::text,
                type,
                occurred_at,
                zone,
                severity,
                title,
                description,
                evidence_url,
                status,
                score,
                created_at
        """, (update_data.status, event_id))
        
        updated_event = cursor.fetchone()
        
        if not updated_event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        db.commit()
        
        logger.info(
            "event_status_updated",
            event_id=event_id,
            new_status=update_data.status
        )
        
        # Si el evento fue CONFIRMADO, publicarlo a RabbitMQ
        if update_data.status == 'CONFIRMADO':
            try:
                publish_confirmed_event(dict(updated_event))
                logger.info(
                    "confirmed_event_published",
                    event_id=event_id
                )
            except Exception as e:
                logger.error(
                    "failed_to_publish_confirmed_event",
                    event_id=event_id,
                    error=str(e)
                )
                # No fallar la request si RabbitMQ falla
        
        return dict(updated_event)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("update_event_status_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Error updating event status")
    finally:
        cursor.close()

@app.get("/api/provinces", response_model=List[ProvinceResponse], tags=["Provinces"])
def get_provinces(db = Depends(get_db)):
    """Obtener lista de provincias del Ecuador"""
    cursor = db.cursor(cursor_factory=RealDictCursor)
    
    try:
        cursor.execute("""
            SELECT province_id, name
            FROM provinces
            ORDER BY name
        """)
        provinces = cursor.fetchall()
        
        logger.info("provinces_fetched", count=len(provinces))
        return [dict(p) for p in provinces]
        
    except Exception as e:
        logger.error("get_provinces_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Error fetching provinces")
    finally:
        cursor.close()

@app.get("/api/sources", response_model=List[SourceResponse], tags=["Sources"])
def get_sources(
    active_only: bool = Query(True),
    db = Depends(get_db)
):
    """Obtener lista de fuentes configuradas"""
    cursor = db.cursor(cursor_factory=RealDictCursor)
    
    try:
        query = """
            SELECT 
                source_id::text,
                name,
                type,
                domain,
                active,
                frequency_sec
            FROM sources
        """
        
        if active_only:
            query += " WHERE active = true"
        
        query += " ORDER BY name"
        
        cursor.execute(query)
        sources = cursor.fetchall()
        
        logger.info("sources_fetched", count=len(sources))
        
        return [dict(source) for source in sources]
        
    except Exception as e:
        logger.error("get_sources_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Error fetching sources")
    finally:
        cursor.close()

@app.get("/api/stats", response_model=StatsResponse, tags=["Statistics"])
def get_stats(db = Depends(get_db)):
    """Obtener estadísticas del sistema"""
    cursor = db.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Estadísticas de fuentes
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE active = true) as active
            FROM sources
        """)
        sources_stats = cursor.fetchone()
        
        # Estadísticas de eventos crudos
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                MAX(fetched_at) as last_fetch
            FROM raw_events
        """)
        raw_stats = cursor.fetchone()
        
        # Estadísticas de eventos normalizados
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE status = 'CONFIRMADO') as confirmados,
                COUNT(*) FILTER (WHERE status = 'EN_VERIFICACION') as en_verificacion,
                COUNT(*) FILTER (WHERE status = 'NO_VERIFICADO') as no_verificados
            FROM events
        """)
        events_stats = cursor.fetchone()
        
        return {
            "total_sources": sources_stats['total'],
            "active_sources": sources_stats['active'],
            "total_raw_events": raw_stats['total'],
            "total_events": events_stats['total'] if events_stats else 0,
            "events_by_status": {
                "confirmados": events_stats['confirmados'] if events_stats else 0,
                "en_verificacion": events_stats['en_verificacion'] if events_stats else 0,
                "no_verificados": events_stats['no_verificados'] if events_stats else 0
            },
            "last_scraping": raw_stats['last_fetch']
        }
        
    except Exception as e:
        logger.error("get_stats_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Error fetching statistics")
    finally:
        cursor.close()

# ============================================================================
# Docker Container Management
# ============================================================================

@app.get("/api/containers", response_model=List[ContainerInfo], tags=["Docker"])
def get_containers():
    """Listar todos los contenedores Docker del proyecto"""
    try:
        import subprocess
        import json as json_lib
        
        # Usar docker CLI en lugar de SDK (funciona mejor en Windows)
        result = subprocess.run(
            ['docker', 'ps', '-a', '--format', '{{json .}}'],
            capture_output=True,
            text=True,
            check=True
        )
        
        container_list = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            container_data = json_lib.loads(line)
            
            # Filtrar solo contenedores de SACV
            if container_data['Names'].startswith('sacv') or 'sistema-alertas' in container_data['Names']:
                container_list.append({
                    "name": container_data['Names'],
                    "status": container_data['State'],
                    "state": container_data['Status'],
                    "image": container_data['Image'],
                    "created": container_data['CreatedAt']
                })
        
        logger.info("containers_fetched", count=len(container_list))
        return container_list
        
    except subprocess.CalledProcessError as e:
        logger.error("get_containers_failed", error=str(e), stderr=e.stderr)
        raise HTTPException(status_code=500, detail=f"Error executing docker command: {e.stderr}")
    except Exception as e:
        logger.error("get_containers_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Error fetching containers: {str(e)}")

@app.post("/api/containers/{container_name}/restart", tags=["Docker"])
def restart_container(container_name: str):
    """Reiniciar un contenedor específico"""
    try:
        import subprocess
        
        # Usar docker CLI para reiniciar
        result = subprocess.run(
            ['docker', 'restart', container_name],
            capture_output=True,
            text=True,
            check=True,
            timeout=30
        )
        
        logger.info(
            "container_restarted",
            container_name=container_name
        )
        
        return {
            "success": True,
            "message": f"Container '{container_name}' restarted successfully",
            "container": container_name
        }
        
    except subprocess.TimeoutExpired:
        logger.error("restart_container_timeout", container_name=container_name)
        raise HTTPException(status_code=504, detail=f"Timeout restarting container '{container_name}'")
    except subprocess.CalledProcessError as e:
        if 'No such container' in e.stderr:
            raise HTTPException(status_code=404, detail=f"Container '{container_name}' not found")
        logger.error("restart_container_failed", container_name=container_name, error=e.stderr)
        raise HTTPException(status_code=500, detail=f"Error restarting container: {e.stderr}")
    except Exception as e:
        logger.error("restart_container_failed", container_name=container_name, error=str(e))
        raise HTTPException(status_code=500, detail=f"Error restarting container: {str(e)}")

# ============================================================================
# Eventos de inicio
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Evento de inicio de la aplicación"""
    logger.info("api_gateway_started", version="1.0.0")

@app.on_event("shutdown")
async def shutdown_event():
    """Evento de cierre de la aplicación"""
    logger.info("api_gateway_shutdown")

# ============================================================================
# Funciones de RabbitMQ
# ============================================================================

def publish_confirmed_event(event: dict):
    """Publicar evento confirmado a la cola de RabbitMQ"""
    try:
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                credentials=credentials
            )
        )
        channel = connection.channel()
        
        # Declarar la cola confirmed_events
        channel.queue_declare(queue='confirmed_events', durable=True)
        
        # Publicar el mensaje
        message = json.dumps({
            'event_id': event['event_id'],
            'type': event['type'],
            'occurred_at': event['occurred_at'].isoformat() if isinstance(event['occurred_at'], datetime) else event['occurred_at'],
            'zone': event['zone'],
            'severity': event['severity'],
            'title': event['title'],
            'description': event['description'],
            'evidence_url': event['evidence_url'],
            'status': event['status'],
            'score': event['score'],
            'province_id': event.get('province_id')
        })
        
        channel.basic_publish(
            exchange='',
            routing_key='confirmed_events',
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=2,  # Mensaje persistente
            )
        )
        
        connection.close()
        logger.info(
            "event_published_to_rabbitmq",
            event_id=event['event_id'],
            queue='confirmed_events'
        )
        
    except Exception as e:
        logger.error(
            "rabbitmq_publish_failed",
            event_id=event.get('event_id'),
            error=str(e)
        )
        raise
