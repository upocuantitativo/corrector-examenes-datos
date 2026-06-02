# Worker de subida automática (opcional)

Pequeño servicio (Cloudflare Workers, plan gratuito) que recibe los ejemplos de
la app y los guarda en `samples/auto/` de este repo. Así la app sube sola los
ejemplos sin que el token de GitHub esté nunca en el móvil.

> Solo necesario para subida **automática**. Sin esto, usa el flujo
> «Exportar JSONL → subir a `samples/`» que no requiere servidor.

## Desplegar (una vez)

1. Crea un **token de GitHub** (fine-grained) con permiso **Contents: Read and write**
   solo sobre el repo `corrector-examenes-datos`.
2. Instala y entra en Cloudflare:
   ```bash
   npm i -g wrangler
   wrangler login
   ```
3. Desde esta carpeta `worker/`:
   ```bash
   wrangler secret put GH_TOKEN      # pega el token de GitHub
   wrangler secret put API_KEY       # inventa una clave (la pondrás también en la app)
   wrangler deploy
   ```
   Te dará una URL tipo `https://corrector-examenes-ingest.<tu-cuenta>.workers.dev`.
4. En la app → apartado 5 «Aprendizaje»:
   - **Servidor de aprendizaje**: pega esa URL.
   - **Clave (x-api-key)**: la misma `API_KEY`.

A partir de ahí, cada duda que resuelvas se sube sola; la acción de GitHub
reentrena el modelo y la app lo descarga.

## Probar

```bash
curl -X POST <URL_DEL_WORKER> -H "content-type: application/json" \
  -H "x-api-key: TU_API_KEY" \
  -d '{"scores":[0.6,0.05,0.04],"label":"a","examId":"demo"}'
```
Debe responder `{"ok":true,...}` y aparecer un fichero en `samples/auto/`.
