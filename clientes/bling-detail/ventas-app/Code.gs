// ============================================================
//  BLING TIENDA DETAIL — Registro de Ventas
//  Google Apps Script · Code.gs
// ============================================================

// ID del Spreadsheet vinculado (se completa al crear el proyecto)
var SPREADSHEET_ID = '';

// Nombres de las hojas
var HOJA_VENTAS    = 'Ventas';
var HOJA_CONSULTAS = 'Consultas';
var HOJA_CONFIG    = 'Config';

// ============================================================
//  PUNTO DE ENTRADA — sirve la app web
// ============================================================
function doGet() {
  inicializarSheets();
  return HtmlService
    .createHtmlOutputFromFile('Index')
    .setTitle('Bling · Registro de Ventas')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

// ============================================================
//  INICIALIZACIÓN — crea hojas si no existen
// ============================================================
function inicializarSheets() {
  var ss = getSpreadsheet();

  // Ventas
  if (!ss.getSheetByName(HOJA_VENTAS)) {
    var sv = ss.insertSheet(HOJA_VENTAS);
    sv.appendRow(['ID', 'Fecha', 'HoraCarga', 'Canal', 'Productos', 'Monto', 'Anuncio', 'LinkTienda', 'Nota']);
    sv.getRange(1, 1, 1, 9).setFontWeight('bold');
  }

  // Consultas
  if (!ss.getSheetByName(HOJA_CONSULTAS)) {
    var sc = ss.insertSheet(HOJA_CONSULTAS);
    sc.appendRow(['ID', 'Fecha', 'HoraCarga', 'Anuncio', 'Motivo']);
    sc.getRange(1, 1, 1, 5).setFontWeight('bold');
  }

  // Config
  if (!ss.getSheetByName(HOJA_CONFIG)) {
    var scfg = ss.insertSheet(HOJA_CONFIG);
    scfg.appendRow(['Tipo', 'Valor', 'Activo']);
    scfg.getRange(1, 1, 1, 3).setFontWeight('bold');

    // Productos iniciales
    var productos = [
      'Wheel Brite', 'Magic Blue', 'Gel Shine', '3D All Purpose Cleaner',
      '3D Wheel & Tire Cleaner', 'Vonixx Restaurax', 'Vonixx Shiny',
      'Vonixx V10', 'Vonixx V20', 'Vonixx V30', 'Vonixx V-Polish',
      'Vonixx V-Cut', 'Toxic Shine Iron Warning', 'Kit llantas',
      'Kit interior', 'Otro'
    ];
    productos.forEach(function(p) {
      scfg.appendRow(['producto', p, 'TRUE']);
    });

    // Anuncios iniciales
    var anuncios = [
      'Llantas antes/después', 'Molduras antes/después', 'Bajo la Lupa',
      'Combo llantas', 'Facu responde', 'Dato concreto',
      'Publicación orgánica', 'Lo conoce de antes', 'No sabe'
    ];
    anuncios.forEach(function(a) {
      scfg.appendRow(['anuncio', a, 'TRUE']);
    });
  }
}

// ============================================================
//  GUARDAR VENTA
// ============================================================
function guardarVenta(data) {
  var lock = LockService.getScriptLock();
  try {
    lock.waitLock(10000);
    var ss  = getSpreadsheet();
    var sh  = ss.getSheetByName(HOJA_VENTAS);
    var id  = generarId('V');
    var ahora = new Date();
    sh.appendRow([
      id,
      data.fecha,
      Utilities.formatDate(ahora, 'America/Argentina/Buenos_Aires', 'dd/MM/yyyy HH:mm:ss'),
      data.canal,
      data.productos,   // string separado por comas
      data.monto,
      data.anuncio,
      data.linkTienda,
      data.nota || ''
    ]);
    return { ok: true, id: id };
  } catch(e) {
    return { ok: false, error: e.message };
  } finally {
    lock.releaseLock();
  }
}

// ============================================================
//  GUARDAR CONSULTA
// ============================================================
function guardarConsulta(data) {
  var lock = LockService.getScriptLock();
  try {
    lock.waitLock(10000);
    var ss  = getSpreadsheet();
    var sh  = ss.getSheetByName(HOJA_CONSULTAS);
    var id  = generarId('C');
    var ahora = new Date();
    sh.appendRow([
      id,
      data.fecha,
      Utilities.formatDate(ahora, 'America/Argentina/Buenos_Aires', 'dd/MM/yyyy HH:mm:ss'),
      data.anuncio,
      data.motivo
    ]);
    return { ok: true, id: id };
  } catch(e) {
    return { ok: false, error: e.message };
  } finally {
    lock.releaseLock();
  }
}

// ============================================================
//  OBTENER DATOS DE CONFIGURACIÓN
// ============================================================
function getConfigData() {
  try {
    var ss   = getSpreadsheet();
    var sh   = ss.getSheetByName(HOJA_CONFIG);
    var rows = sh.getDataRange().getValues();
    var productos = [], anuncios = [];
    for (var i = 1; i < rows.length; i++) {
      var tipo   = String(rows[i][0]).trim();
      var valor  = String(rows[i][1]).trim();
      var activo = String(rows[i][2]).trim().toUpperCase();
      if (activo !== 'TRUE') continue;
      if (tipo === 'producto') productos.push(valor);
      if (tipo === 'anuncio')  anuncios.push(valor);
    }
    return { ok: true, productos: productos, anuncios: anuncios };
  } catch(e) {
    return { ok: false, error: e.message };
  }
}

// ============================================================
//  OBTENER RESUMEN DEL MES
// ============================================================
function getResumenData(mes, anio) {
  try {
    var ss = getSpreadsheet();

    // --- Ventas del mes ---
    var shV  = ss.getSheetByName(HOJA_VENTAS);
    var rowsV = shV.getDataRange().getValues();
    var ventas = [];
    for (var i = 1; i < rowsV.length; i++) {
      var fila = rowsV[i];
      if (!fila[0]) continue;           // fila vacía
      var fecha = String(fila[1]);      // DD/MM/AAAA
      var partes = fecha.split('/');
      if (partes.length < 3) continue;
      if (parseInt(partes[1]) === mes && parseInt(partes[2]) === anio) {
        ventas.push({
          id:         fila[0],
          fecha:      fila[1],
          canal:      fila[3],
          productos:  fila[4],
          monto:      parseFloat(fila[5]) || 0,
          anuncio:    fila[6],
          linkTienda: fila[7],
          nota:       fila[8]
        });
      }
    }

    // --- Consultas del mes ---
    var shC   = ss.getSheetByName(HOJA_CONSULTAS);
    var rowsC = shC.getDataRange().getValues();
    var consultas = [];
    for (var j = 1; j < rowsC.length; j++) {
      var filac = rowsC[j];
      if (!filac[0]) continue;
      var fechac  = String(filac[1]);
      var partesc = fechac.split('/');
      if (partesc.length < 3) continue;
      if (parseInt(partesc[1]) === mes && parseInt(partesc[2]) === anio) {
        consultas.push({ anuncio: filac[3], motivo: filac[4] });
      }
    }

    // --- Pauta del mes ---
    var clavepauta = 'pauta_' + anio + '_' + mes;
    var shCfg  = ss.getSheetByName(HOJA_CONFIG);
    var rowsCfg = shCfg.getDataRange().getValues();
    var pauta = 0;
    for (var k = 1; k < rowsCfg.length; k++) {
      if (String(rowsCfg[k][0]) === 'pauta' && String(rowsCfg[k][1]) === clavepauta) {
        pauta = parseFloat(rowsCfg[k][2]) || 0;
        break;
      }
    }

    return { ok: true, ventas: ventas, consultas: consultas, pauta: pauta };
  } catch(e) {
    return { ok: false, error: e.message };
  }
}

// ============================================================
//  GUARDAR PAUTA DEL MES
// ============================================================
function savePauta(mes, anio, monto) {
  var lock = LockService.getScriptLock();
  try {
    lock.waitLock(10000);
    var ss      = getSpreadsheet();
    var sh      = ss.getSheetByName(HOJA_CONFIG);
    var rows    = sh.getDataRange().getValues();
    var clave   = 'pauta_' + anio + '_' + mes;
    var encontrado = false;
    for (var i = 1; i < rows.length; i++) {
      if (String(rows[i][0]) === 'pauta' && String(rows[i][1]) === clave) {
        sh.getRange(i + 1, 3).setValue(monto);
        encontrado = true;
        break;
      }
    }
    if (!encontrado) {
      sh.appendRow(['pauta', clave, monto]);
    }
    return { ok: true };
  } catch(e) {
    return { ok: false, error: e.message };
  } finally {
    lock.releaseLock();
  }
}

// ============================================================
//  ELIMINAR VENTA (por ID, borra la fila)
// ============================================================
function deleteVenta(id) {
  var lock = LockService.getScriptLock();
  try {
    lock.waitLock(10000);
    var ss   = getSpreadsheet();
    var sh   = ss.getSheetByName(HOJA_VENTAS);
    var rows = sh.getDataRange().getValues();
    for (var i = 1; i < rows.length; i++) {
      if (String(rows[i][0]) === String(id)) {
        sh.deleteRow(i + 1);
        return { ok: true };
      }
    }
    return { ok: false, error: 'No se encontró la venta con ese ID.' };
  } catch(e) {
    return { ok: false, error: e.message };
  } finally {
    lock.releaseLock();
  }
}

// ============================================================
//  DESCARGAR CSV DEL MES
// ============================================================
function getCSV(mes, anio) {
  try {
    var res = getResumenData(mes, anio);
    if (!res.ok) return { ok: false, error: res.error };
    var lineas = ['ID,Fecha,Canal,Productos,Monto,Anuncio,LinkTienda,Nota'];
    res.ventas.forEach(function(v) {
      lineas.push([
        v.id, v.fecha, v.canal,
        '"' + v.productos + '"',
        v.monto, v.anuncio,
        v.linkTienda, '"' + (v.nota || '') + '"'
      ].join(','));
    });
    return { ok: true, csv: lineas.join('\n') };
  } catch(e) {
    return { ok: false, error: e.message };
  }
}

// ============================================================
//  GUARDAR CONFIG (productos o anuncios)
//  items = [{ valor, activo }]
// ============================================================
function saveConfigItems(tipo, items) {
  var lock = LockService.getScriptLock();
  try {
    lock.waitLock(10000);
    var ss   = getSpreadsheet();
    var sh   = ss.getSheetByName(HOJA_CONFIG);
    var rows = sh.getDataRange().getValues();

    // Construir mapa de valores existentes (fila index → activo)
    var mapa = {};
    for (var i = 1; i < rows.length; i++) {
      if (String(rows[i][0]) === tipo) {
        mapa[String(rows[i][1]).trim()] = i + 1; // número de fila real
      }
    }

    items.forEach(function(item) {
      var val = String(item.valor).trim();
      var act = item.activo ? 'TRUE' : 'FALSE';
      if (mapa[val] !== undefined) {
        // Actualizar activo
        sh.getRange(mapa[val], 3).setValue(act);
      } else {
        // Nuevo ítem
        sh.appendRow([tipo, val, act]);
      }
    });

    return { ok: true };
  } catch(e) {
    return { ok: false, error: e.message };
  } finally {
    lock.releaseLock();
  }
}

// ============================================================
//  OBTENER TODOS LOS ITEMS DE CONFIG (para pantalla Config)
// ============================================================
function getConfigItems(tipo) {
  try {
    var ss   = getSpreadsheet();
    var sh   = ss.getSheetByName(HOJA_CONFIG);
    var rows = sh.getDataRange().getValues();
    var items = [];
    for (var i = 1; i < rows.length; i++) {
      if (String(rows[i][0]) === tipo) {
        items.push({
          valor:  String(rows[i][1]).trim(),
          activo: String(rows[i][2]).trim().toUpperCase() === 'TRUE'
        });
      }
    }
    return { ok: true, items: items };
  } catch(e) {
    return { ok: false, error: e.message };
  }
}

// ============================================================
//  HELPERS
// ============================================================
function getSpreadsheet() {
  // Si SPREADSHEET_ID está vacío, usa el Spreadsheet vinculado al script
  if (SPREADSHEET_ID) {
    return SpreadsheetApp.openById(SPREADSHEET_ID);
  }
  return SpreadsheetApp.getActiveSpreadsheet();
}

function generarId(prefijo) {
  var ahora = new Date();
  return prefijo + '-' +
    Utilities.formatDate(ahora, 'America/Argentina/Buenos_Aires', 'yyyyMMddHHmmss') +
    '-' + Math.floor(Math.random() * 1000);
}
