/**
 * Worker de Cloudflare (opcional) para la subida automática de ejemplos.
 * Recibe POST {scores:[3], label, examId} desde la app y guarda cada ejemplo
 * como un fichero en samples/auto/ del repo de datos, usando un token de GitHub
 * que queda A SALVO aquí (nunca en la app).
 *
 * Variables (secrets) a configurar en el Worker:
 *   GH_TOKEN  : PAT de GitHub (fine-grained) con permiso Contents:write en el repo de datos
 *   GH_REPO   : "upocuantitativo/corrector-examenes-datos"
 *   API_KEY   : clave compartida; la app la envía en la cabecera x-api-key (evita spam)
 */
export default {
  async fetch(req, env) {
    if (req.method === 'OPTIONS') return cors(new Response(null, { status: 204 }));
    // Diagnóstico (GET): comprueba configuración SIN revelar el token
    if (req.method === 'GET') {
      let repoStatus = null;
      try {
        const rr = await fetch(`https://api.github.com/repos/${env.GH_REPO}`, {
          headers: { 'Authorization': `Bearer ${env.GH_TOKEN}`, 'User-Agent': 'corrector-diag', 'Accept': 'application/vnd.github+json' },
        });
        repoStatus = rr.status;
      } catch (e) { repoStatus = 'fetch-error'; }
      return cors(json({
        ok: true,
        gh_repo: env.GH_REPO || '(NO DEFINIDO)',
        token_presente: !!env.GH_TOKEN,
        token_longitud: (env.GH_TOKEN || '').length,
        api_key_presente: !!env.API_KEY,
        acceso_al_repo_status: repoStatus,
      }));
    }
    if (req.method !== 'POST') return cors(json({ error: 'usa POST' }, 405));
    if (env.API_KEY && req.headers.get('x-api-key') !== env.API_KEY)
      return cors(json({ error: 'no autorizado' }, 401));

    let s;
    try { s = await req.json(); } catch { return cors(json({ error: 'json inválido' }, 400)); }
    if (!Array.isArray(s.scores) || s.scores.length !== 3)
      return cors(json({ error: 'se requiere scores[3]' }, 400));

    const label = ['a', 'b', 'c', 'blank', 'void'].includes(s.label) ? s.label : 'blank';
    const slim = { scores: s.scores.map(Number), label, examId: s.examId || null, ts: Date.now() };
    const path = `samples/auto/${slim.ts}-${Math.random().toString(36).slice(2, 8)}.json`;
    const url = `https://api.github.com/repos/${env.GH_REPO}/contents/${path}`;
    const content = btoa(unescape(encodeURIComponent(JSON.stringify(slim))));
    const r = await fetch(url, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${env.GH_TOKEN}`,
        'User-Agent': 'corrector-examenes-worker',
        'Accept': 'application/vnd.github+json',
      },
      body: JSON.stringify({ message: `sample ${path}`, content }),
    });
    if (!r.ok) return cors(json({ error: 'github', status: r.status, detail: await r.text() }, 502));
    return cors(json({ ok: true, path }));
  },
};

function cors(resp) {
  resp.headers.set('Access-Control-Allow-Origin', '*');
  resp.headers.set('Access-Control-Allow-Headers', 'content-type,x-api-key');
  resp.headers.set('Access-Control-Allow-Methods', 'POST,OPTIONS');
  return resp;
}
function json(o, st = 200) {
  return new Response(JSON.stringify(o), { status: st, headers: { 'content-type': 'application/json' } });
}
