# Modulador de Voz en Directo V57 - Recuperación de Audio Pro

## Novedad principal

El directo ya no se queda "colgado" si el audio falla: la app detecta
la desconexión y se reconecta sola.

### Guardián del stream

Cada bloque de audio procesado cuenta como un latido. Un vigilante
comprueba el latido cada 2 segundos: si el directo está activo pero el
audio dejó de fluir (desenchufaste los auriculares USB, Windows cambió
de dispositivo, el driver falló), la app lo detecta al momento.

### Reconexión automática

Al detectar la pérdida:

1. Cierra el stream muerto y avisa: "⚠ audio perdido · reconectando…".
2. Reintenta cada 2 segundos, hasta 6 veces.
3. Al tercer intento reescanea los dispositivos (al desenchufar y
   enchufar cambian los índices) y vuelve a casar tu micrófono y tu
   salida POR NOMBRE.
4. Si lo consigue: "✅ directo recuperado", sin tocar nada.
5. Si no: lo explica claro y te deja el botón ▶ para cuando conectes
   el dispositivo.

Todo el proceso es silencioso (sin ventanas emergentes) salvo el aviso
final si no hay recuperación posible.

### Bloques por segundo

El estado de Rendimiento ahora muestra "Cortes de audio: N · bloques/s:
M" con el directo activo: de un vistazo ves que el audio fluye y a qué
ritmo.

## Mantiene

EQ Real, Mis Voces, Reducción de Ruido, Atajos Globales, Motor
Continuo, Voz Gaming Pro, Clip Instantáneo, Studio Dashboard, Karaoke,
Autotune, Cable Virtual, Benchmark, vigilante de cortes, limitador
suave, Streamer Hub, Favoritos, perfiles y el instalador Windows.

## Verificado

Ciclo completo probado en simulación: latido sano sin falsas alarmas,
congelación detectada en 2-4 s, reconexión al tercer intento con
reescaneo, recasado de dispositivos por nombre con índices cambiados,
y sin dobles reconexiones una vez recuperado.
