# Corrector de Exámenes — datos y modelo (Fase 2)

Pipeline de aprendizaje del [Corrector de Exámenes](https://github.com/upocuantitativo/corrector-examenes).
La app (PWA/APK) recoge ejemplos cuando el profesor resuelve dudas; aquí se
**entrena un modelo ligero** que la app descarga para tener **cada vez menos
dudas**.

> 🔒 **Sin datos personales**: los ejemplos son solo 3 números (la densidad de
> tinta de cada opción a/b/c) y la letra correcta. **No** hay imágenes ni nombres.

## Cómo funciona

1. **Ejemplos** → carpeta `samples/` (archivos `.jsonl`, una muestra por línea):
   ```json
   {"scores": [0.61, 0.05, 0.04], "label": "a"}
   ```
   `label` ∈ `a` | `b` | `c` | `blank`.
2. **Entrenamiento automático**: cuando cambian los `samples/`, GitHub Actions
   (`.github/workflows/train.yml`) ejecuta `train.py` y publica `model.json`.
   - Con pocos datos (<30) escribe un modelo `heuristic` (la app usa su lógica).
   - Con suficientes datos entrena una **regresión logística** (a/b/c/blank).
3. **La app descarga `model.json`** desde GitHub Pages de este repo:
   `https://upocuantitativo.github.io/corrector-examenes-datos/model.json`
   y lo aplica en el móvil.

## Subir ejemplos

**A) Manual (sin servidor, funciona ya):**
1. En la app: apartado 5 → **«Exportar para el servidor (JSONL)»**.
2. Sube ese archivo a la carpeta `samples/` de este repo (web de GitHub:
   *Add file → Upload files*, o `git`/`gh`). Al hacerlo, la acción reentrena sola.

**B) Automático (opcional, con el Worker de Cloudflare):**
Ver [`worker/README.md`](worker/README.md). Despliega un pequeño Worker que
recibe los ejemplos de la app y los va guardando aquí. Luego, en la app
(apartado 5) pega la URL del Worker en «Servidor de aprendizaje».

## Reentrenar a mano

Actions → *Entrenar modelo* → **Run workflow**. O en local:
```bash
pip install -r requirements.txt
python train.py
```

## Formato de `model.json`

```
type: "logreg" | "heuristic"
classes: ["a","b","c","blank"]
features, mean, std, coef (4×9), intercept (4)   # solo en logreg
doubt_margin: si prob(1ª)-prob(2ª) < margen → DUDA (se pregunta al profesor)
```
