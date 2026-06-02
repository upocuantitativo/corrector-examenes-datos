"""
train.py — Entrena el modelo del Corrector de Exámenes (Fase 2).

Lee los ejemplos de samples/*.jsonl (y *.json) — cada ejemplo son los 3 valores
de tinta de una pregunta [sa, sb, sc] y la letra que el profesor confirmó
(a/b/c/blank). NO usa imágenes ni datos personales.

Entrena una regresión logística multiclase (a/b/c/blank) sobre rasgos derivados
de esos 3 valores y escribe model.json en un formato que la app (JS) puede
aplicar directamente en el móvil. Si hay pocos datos, escribe un modelo
"heuristic" para que la app use su lógica por defecto.

Lo ejecuta automáticamente GitHub Actions (.github/workflows/train.yml).
"""
import json
import glob
import os
import datetime

OUT = "model.json"
CLASSES = ["a", "b", "c", "blank"]


def _now():
    return datetime.datetime.now(datetime.timezone.utc)


def featurize(sa, sb, sc):
    s = [float(sa), float(sb), float(sc)]
    srt = sorted(s, reverse=True)
    mx, mid, mn = srt[0], srt[1], srt[2]
    return [s[0], s[1], s[2], mx, mid, mn, mx - mid, mid - mn, s[0] + s[1] + s[2]]


FEATURES = ["sa", "sb", "sc", "max", "mid", "min", "gap1", "gap2", "sum"]


def load_samples():
    rows = []
    files = sorted(glob.glob("samples/*.jsonl")) + sorted(glob.glob("samples/*.json"))
    for f in files:
        try:
            txt = open(f, encoding="utf-8").read().strip()
        except Exception:
            continue
        if not txt:
            continue
        # admite JSONL (una muestra por línea) o un array JSON
        items = []
        if txt.lstrip().startswith("["):
            try:
                items = json.loads(txt)
            except Exception:
                items = []
        else:
            for line in txt.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    items.append(json.loads(line))
                except Exception:
                    pass
        for it in items:
            sc = it.get("scores")
            lab = it.get("label")
            if lab == "void":
                lab = "blank"            # 'anulada' no es detectable: cuenta como blanco para el modelo
            if (isinstance(sc, list) and len(sc) == 3 and lab in CLASSES):
                rows.append((sc, lab))
    return rows


def write_heuristic(n, reason):
    model = {
        "version": int(_now().timestamp()),
        "trained_at": _now().isoformat() + "Z",
        "type": "heuristic",
        "n_samples": n,
        "note": reason,
    }
    json.dump(model, open(OUT, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"Modelo heurístico escrito ({reason}); muestras={n}")


def main():
    rows = load_samples()
    n = len(rows)
    labels_present = set(l for _, l in rows)
    # Necesitamos datos suficientes y variedad de clases para un modelo fiable
    if n < 30 or len(labels_present) < 2:
        write_heuristic(n, "pocos datos: la app usa su heurística por defecto")
        return

    import numpy as np
    from sklearn.linear_model import LogisticRegression

    X = np.array([featurize(*sc) for sc, _ in rows], dtype=float)
    y = np.array([l for _, l in rows])
    mean = X.mean(axis=0)
    std = X.std(axis=0)
    std[std == 0] = 1.0
    Xs = (X - mean) / std

    clf = LogisticRegression(max_iter=2000, C=1.0, multi_class="multinomial")
    clf.fit(Xs, y)

    # Reordenar coef/intercept al orden fijo de CLASSES (las clases ausentes → ceros)
    coef = [[0.0] * X.shape[1] for _ in CLASSES]
    inter = [(-1e9 if c not in labels_present else 0.0) for c in CLASSES]  # clases no vistas: prob ~0
    for i, c in enumerate(clf.classes_):
        ci = CLASSES.index(c)
        coef[ci] = clf.coef_[i].tolist() if clf.coef_.shape[0] > 1 else clf.coef_[0].tolist()
        inter[ci] = float(clf.intercept_[i] if clf.intercept_.shape[0] > 1 else clf.intercept_[0])

    # accuracy en train (informativo)
    acc = float((clf.predict(Xs) == y).mean())

    model = {
        "version": int(_now().timestamp()),
        "trained_at": _now().isoformat() + "Z",
        "type": "logreg",
        "n_samples": n,
        "train_accuracy": round(acc, 4),
        "features": FEATURES,
        "classes": CLASSES,
        "mean": mean.tolist(),
        "std": std.tolist(),
        "coef": coef,
        "intercept": inter,
        "doubt_margin": 0.18,   # si prob(top1)-prob(top2) < margen → DUDA (preguntar al profesor)
        "floor_blank": 0.14,
    }
    json.dump(model, open(OUT, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"Modelo logreg escrito. muestras={n}, clases={sorted(labels_present)}, acc={acc:.3f}")


if __name__ == "__main__":
    main()
