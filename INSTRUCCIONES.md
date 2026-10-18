# Cómo crear y programar un video de Nubi (para la tarea automática)

Cuenta: TikTok **@nubi.pe**, publicada con **Metricool** (marca `blogId` **7491431**, zona horaria America/Lima).
Frecuencia acordada: **un video cada 2 días, solo TikTok**, a las **19:00 hora de Perú**.
El dueño **aprueba cada video**: siempre programar con `autoPublish: false` (le llega una notificación a la app de Metricool y publica con un toque). Nunca usar `autoPublish: true`.

## Pasos
1. Elegir tema: el primer elemento de `calendar.json` cuyo `id` no esté en `posted.json`. Si ya se usaron todos, inventar uno nuevo en la misma línea (receta peruana casera, truco de cocina, reto con XP o función de la app) y agregarlo al calendario.
2. Escribir el guion en `specs/AAAA-MM-DD-<id>.json` con el formato descrito al inicio de `kit/make_video.py`:
   - En español peruano, cercano y alegre. Gancho de 1 a 3 líneas cortas que despierte curiosidad.
   - De 3 a 5 pasos con cantidades reales y cocción segura (carnes bien cocidas; para ceviche, pescado apto para consumo crudo de proveedor confiable). Cada paso con 60 caracteres como máximo.
   - `xp` entre 90 y 200 según la dificultad. `seed` = día del año (cambia la música).
   - Nada de marcas, personas reales, precios inventados ni promesas de salud.
3. Renderizar: `python3 kit/make_video.py specs/<archivo>.json videos/AAAA-MM-DD-<id>.mp4` (unos 2 minutos).
4. Revisar `videos/AAAA-MM-DD-<id>-revision.jpg` (12 cuadros): que ningún texto se salga ni se corte y que los emojis se vean. Si hay un problema, acortar textos y volver a renderizar. Después borrar el archivo `-revision.jpg` (no se sube).
5. Subir a GitHub: `git add videos specs calendar.json posted.json && git commit && git push`. URL pública del video:
   `https://raw.githubusercontent.com/lionelsantamaria94-cloud/nubi-videos/main/videos/<archivo>.mp4`
   (desde el entorno de trabajo esa URL puede dar 403 por el proxy: es normal, Metricool sí la descarga).
6. Programar en Metricool con `createScheduledPost`: `providers: [{"network":"tiktok"}]`, `media: [URL]`, `autoPublish: false`, fecha = hoy 19:00 America/Lima (si ya pasó, mañana 19:00). `tiktokData`: `privacyOption: PUBLIC_TO_EVERYONE`, `commercialContentOwnBrand: true`, `isAigc: true`, `title` corto. Texto: 2-4 líneas + «Pruébala gratis 👉 link en la bio» + 5-7 hashtags (#comidaperuana #recetasfaciles #quecocinohoy #recetasperuanas + temáticos).
7. Agregar la entrada a `posted.json` (id, fecha, video, metricool_id), hacer commit y push.
8. Avisar al dueño con un resumen corto: tema, hora programada y que debe aprobarlo en la app de Metricool.

## Si algo falla
- Metricool devuelve error de cuota o de plan: no reintentar en bucle; avisar al dueño con el mensaje exacto.
- `git push` rechazado por permisos: avisar al dueño que la app de Claude en GitHub debe tener acceso a `nubi-videos`.
