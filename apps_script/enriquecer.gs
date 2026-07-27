/**
 * ============================================================================
 * Enriquecedor de emails — corre DENTRO de tu Google Sheet (Google Apps Script).
 *
 * Por qué existe: cuando la organización bloquea las llaves de cuenta de
 * servicio (política iam.disableServiceAccountKeyCreation), no se puede escribir
 * el Sheet desde afuera. Este script se ejecuta COMO VOS, adentro de la planilla,
 * así que ninguna política lo frena y no hay que instalar nada.
 *
 * Qué hace: recorre los leads con WEB pero sin EMAIL, entra a cada sitio, busca
 * el mail (con los mismos filtros anti-basura del sistema en Python) y lo escribe
 * en la columna EMAIL. Si no encuentra, deja la nota para ir por WhatsApp.
 *
 * Cómo usarlo: ver apps_script/README.md. Resumen: Extensiones → Apps Script,
 * pegar este archivo, guardar, recargar la planilla y usar el menú "JumpBox".
 *
 * Es SEGURO: nunca borra nada; sólo completa EMAIL y NOTAS. Es re-ejecutable:
 * saltea las filas que ya tienen mail o ya fueron marcadas para WhatsApp, así
 * que lo podés correr varias veces (procesa de a lotes por el límite de tiempo).
 * ============================================================================
 */

// --- Configuración (coincide con el CRM JumpBox; cambiá si tu Sheet difiere) --
var COL_WEB   = 'WEB';
var COL_EMAIL = 'EMAIL';
var COL_NOTAS = 'NOTAS';
var NOTA_SIN  = 'sin mail — ir por WhatsApp';
var LOTE      = 40;   // filas por corrida (para no pasar el límite de ~6 min)

var PATHS = ['', 'contacto', 'contact', 'nosotros', 'institucional',
             'quienes-somos', 'contactanos', 'atencion-al-cliente'];
var PRIORIDAD = ['ventas', 'compras', 'mayorista', 'mayoreo', 'info', 'hola', 'contacto'];

var ASSET = ['woff','woff2','ttf','eot','otf','png','jpg','jpeg','gif','svg',
             'webp','ico','bmp','css','js','map','json','xml','mp4','webm',
             'mp3','wav','pdf','zip'];
var BADTLD = ['loc','local','localhost','test','invalid','example','lan',
              'internal','home','corp','dev','min'];
var BLOCK = ['sentry','wixpress','@wix','cloudflare','godaddy','example',
             'ejemplo','@dominio','@mail.com','@email.com','tumail','tucorreo',
             'youremail','your@','test@','sample@','usuario@','nombre@','name@',
             'user@','noreply','no-reply'];
var PLAT = ['tiendanube','mitiendanube','mercadoshops','mercadolibre',
            'empretienda','wix.com'];

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('JumpBox')
    .addItem('Enriquecer emails (lote)', 'enriquecerLote')
    .addToUi();
}

function enriquecerLote() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sh = ss.getActiveSheet();
  var datos = sh.getDataRange().getValues();
  var head = datos[0];
  var iWeb = head.indexOf(COL_WEB);
  var iMail = head.indexOf(COL_EMAIL);
  var iNota = head.indexOf(COL_NOTAS);
  if (iWeb < 0 || iMail < 0) {
    SpreadsheetApp.getUi().alert('No encuentro las columnas ' + COL_WEB + ' / ' + COL_EMAIL +
      '. Revisá que estés en la pestaña del CRM.');
    return;
  }

  var hechos = 0, encontrados = 0, wa = 0, restantes = 0;
  for (var r = 1; r < datos.length; r++) {
    var web = (datos[r][iWeb] || '').toString().trim();
    var mail = (datos[r][iMail] || '').toString().trim().toLowerCase();
    var nota = (iNota >= 0 ? (datos[r][iNota] || '') : '').toString();
    var yaProcesado = (mail && mail !== 'sin email' && mail !== 'sin mail') ||
                      nota.indexOf('sin mail') >= 0;
    if (!web || yaProcesado) continue;
    if (hechos >= LOTE) { restantes++; continue; }

    var found = buscarEmail(web);
    if (found) {
      sh.getRange(r + 1, iMail + 1).setValue(found);
      encontrados++;
    } else if (iNota >= 0) {
      sh.getRange(r + 1, iNota + 1).setValue(NOTA_SIN);
      wa++;
    }
    hechos++;
  }

  SpreadsheetApp.getUi().alert(
    'Lote listo ✅\n\n' +
    'Mails nuevos encontrados: ' + encontrados + '\n' +
    'Marcados para WhatsApp: ' + wa + '\n' +
    'Procesados en este lote: ' + hechos + '\n' +
    'Quedan para otra corrida: ' + restantes +
    (restantes > 0 ? '\n\nVolvé a correr "Enriquecer emails (lote)" para seguir.' :
                     '\n\n¡Terminaste todo el CRM! 🎉'));
}

// --- Motor de búsqueda de email (portado del sistema en Python) --------------
function buscarEmail(web) {
  var bases = variantes(web);
  var encontrados = [];
  var baseOk = null;
  for (var i = 0; i < bases.length && !baseOk; i++) {
    var html = fetch(bases[i]);
    if (html !== null) { baseOk = bases[i]; encontrados = validos(html); }
  }
  if (!baseOk) return '';

  for (var p = 1; p < PATHS.length; p++) {
    var url = baseOk.replace(/\/+$/, '') + '/' + PATHS[p];
    var h = fetch(url);
    if (h) {
      var vs = validos(h);
      for (var k = 0; k < vs.length; k++) {
        if (encontrados.indexOf(vs[k]) < 0) encontrados.push(vs[k]);
      }
    }
  }
  return elegir(encontrados, baseOk);
}

function fetch(url) {
  try {
    var resp = UrlFetchApp.fetch(url, {
      muteHttpExceptions: true,
      followRedirects: true,
      validateHttpsCertificates: false,
      headers: { 'User-Agent': 'Mozilla/5.0 (compatible; JumpBoxBot/1.0)' }
    });
    if (resp.getResponseCode() < 400) return resp.getContentText();
  } catch (e) {}
  return null;
}

function variantes(web) {
  var w = (web || '').toString().trim().replace(/\/+$/, '');
  if (!w) return [];
  var dom = w.replace(/^https?:\/\//, '');
  var out = [];
  var schemes = ['https://', 'http://'];
  for (var s = 0; s < schemes.length; s++) {
    var hosts = [dom];
    if (dom.indexOf('www.') !== 0) hosts.push('www.' + dom);
    for (var h = 0; h < hosts.length; h++) {
      var u = schemes[s] + hosts[h];
      if (out.indexOf(u) < 0) out.push(u);
    }
  }
  return out;
}

function validos(texto) {
  var out = [];
  var candidatos = [];
  var mailto = texto.match(/mailto:([^"'>?\s]+)/gi) || [];
  for (var i = 0; i < mailto.length; i++) candidatos.push(mailto[i].replace(/mailto:/i, ''));
  var crudos = desofuscar(texto).match(/[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}/g) || [];
  candidatos = candidatos.concat(crudos);

  for (var j = 0; j < candidatos.length; j++) {
    var m = candidatos[j].toString().trim().replace(/^[.,;:()<>\[\]"']+|[.,;:()<>\[\]"']+$/g, '').toLowerCase();
    if (!m || out.indexOf(m) >= 0) continue;
    if (tieneBloque(m) || esAsset(m) || !tldValido(m)) continue;
    out.push(m);
  }
  return out;
}

function tieneBloque(m) {
  for (var i = 0; i < BLOCK.length; i++) if (m.indexOf(BLOCK[i]) >= 0) return true;
  return false;
}
function esAsset(m) {
  var tld = m.split('@').pop().split('.').pop();
  return ASSET.indexOf(tld) >= 0;
}
function tldValido(m) {
  var dom = m.split('@').pop();
  if (dom.indexOf('.') < 0) return false;
  var labels = dom.split('.');
  var tld = labels[labels.length - 1];
  if (!/^[a-z]{2,24}$/.test(tld)) return false;
  if (ASSET.indexOf(tld) >= 0 || BADTLD.indexOf(tld) >= 0) return false;
  if (labels.length >= 2 && labels[labels.length - 2].length < 2) return false;
  return true;
}
function desofuscar(t) {
  t = t.replace(/[\(\[\{]\s*(at|arroba)\s*[\)\]\}]/gi, '@');
  t = t.replace(/[\(\[\{]\s*(dot|punto)\s*[\)\]\}]/gi, '.');
  return t;
}
function raizDominio(url) {
  var s = (url || '').replace(/^https?:\/\//, '').split('/')[0].replace(/^www\./, '');
  return s.split('.')[0] || '';
}
function elegir(mails, baseOk) {
  if (!mails.length) return '';
  var raiz = raizDominio(baseOk);
  var propios = mails.filter(function (m) {
    for (var i = 0; i < PLAT.length; i++) if (m.indexOf(PLAT[i]) >= 0) return false;
    return true;
  });
  var pool = propios.length ? propios : mails;
  var delDom = pool.filter(function (m) { return raiz && m.split('@').pop().indexOf(raiz) >= 0; });
  var cand = delDom.length ? delDom : pool;
  for (var p = 0; p < PRIORIDAD.length; p++) {
    for (var i = 0; i < cand.length; i++) {
      if (cand[i].split('@')[0].indexOf(PRIORIDAD[p]) === 0) return cand[i];
    }
    for (var j = 0; j < cand.length; j++) {
      if (cand[j].split('@')[0].indexOf(PRIORIDAD[p]) >= 0) return cand[j];
    }
  }
  return cand[0];
}
