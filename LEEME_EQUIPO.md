# Rumbo - Agencia de viajes (versión de prueba)

## Cómo usarlo

1. Descomprime el .zip en cualquier carpeta (por ejemplo, en el Escritorio).
2. Haz doble clic en **Rumbo.exe** (Windows) o ejecuta **./Rumbo** (Linux/Mac).
3. Se abre una ventana negra (déjala abierta) y, en unos segundos, tu navegador
   en http://127.0.0.1:5000. Si no se abre solo, escribe esa dirección tú.
4. Para apagarlo, cierra la ventana negra.

## Importante

- **Tus datos viven en el archivo `agencia.db`**, que se crea junto al programa.
  Si lo borras, empiezas desde cero. Para respaldarlo, cópialo.
- **Cada persona tiene su propia base de datos.** Lo que captures en tu computadora
  no lo ve el resto del equipo.
- Flujo sugerido para probar:
  1. *Solicitudes* -> crea una solicitud (te da un folio).
  2. *Cotizador* -> busca el destino y carga un vuelo y un hospedaje.
  3. *Armar viaje* -> elige la solicitud, selecciona vuelo, hospedaje y servicios.
  4. Genera los bloqueos y, por último, la cotización.

## Avisos normales

- **Windows** puede mostrar "Windows protegió su PC" porque el programa no está
  firmado. Pulsa **Más información -> Ejecutar de todas formas**.
- **Mac/Linux:** si no deja ejecutarlo, corre `chmod +x Rumbo` en esa carpeta.
- Si el programa dice que el puerto 5000 está ocupado, es que ya hay otro Rumbo abierto.

## Reportar errores

Anota qué hiciste, qué esperabas y qué pasó (una captura ayuda mucho), y copia
el texto de la ventana negra si apareció algún error.
