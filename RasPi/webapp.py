#!/usr/bin/env python3
import sqlite3, time, datetime
from flask import Flask, jsonify, request, Response

DB_FILE = "bme280_data.db"  # same DB your app.py writes to

app = Flask(__name__)

def iso(ts_int):
    # ts_int is Unix seconds (from your pipeline)
    return datetime.datetime.utcfromtimestamp(int(ts_int)).isoformat() + "Z"

def rows_between(since_unix=None):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    if since_unix is None:
        cur.execute("""SELECT device_ts, temp_c, hum_pct, pres_hpa
                       FROM bme280_data ORDER BY device_ts DESC LIMIT 300""")
    else:
        cur.execute("""SELECT device_ts, temp_c, hum_pct, pres_hpa
                       FROM bme280_data WHERE device_ts >= ? ORDER BY device_ts ASC""",
                    (int(since_unix),))
    rows = cur.fetchall()
    conn.close()
    # normalize to ascending order
    rows = rows[::-1] if since_unix is None else rows
    return [{"ts": r[0], "iso": iso(r[0]), "temp_c": r[1], "hum_pct": r[2], "pres_hpa": r[3]} for r in rows]

@app.get("/api/latest")
def api_latest():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""SELECT device_ts, temp_c, hum_pct, pres_hpa
                   FROM bme280_data ORDER BY device_ts DESC LIMIT 1""")
    r = cur.fetchone()
    conn.close()
    if not r:
        return jsonify({"ok": True, "data": None})
    return jsonify({"ok": True, "data": {"ts": r[0], "iso": iso(r[0]), "temp_c": r[1], "hum_pct": r[2], "pres_hpa": r[3]}})

@app.get("/api/series")
def api_series():
    # accept ?last=15m|1h|6h|24h|7d  OR  ?from=<unix>&to=<unix>
    last = request.args.get("last")
    f = request.args.get("from")
    t = request.args.get("to")
    now = int(time.time())
    since = None

    if last:
        mult = {"m":60, "h":3600, "d":86400}
        unit = last[-1].lower()
        num = int(last[:-1])
        since = now - num * mult[unit]
    elif f and t:
        since = int(f)
        # we’ll filter client-side by `to`, but fetch a bit more is fine

    data = rows_between(since)
    if f and t:
        to_int = int(t)
        data = [d for d in data if d["ts"] <= to_int]

    return jsonify({"ok": True, "count": len(data), "data": data})

@app.get("/")
def index():
    # one-file HTML (no templates) for simplicity
    html = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>IoT Dashboard</title>
<link rel="preconnect" href="https://cdn.jsdelivr.net"/>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>

<style>
  body{font-family:system-ui,Arial,sans-serif;margin:20px;background:#0b0f14;color:#e6eef8}
  .row{display:flex;gap:16px;flex-wrap:wrap}
  .card{background:#121926;border:1px solid #1f2a3a;border-radius:14px;padding:16px;box-shadow:0 2px 10px rgba(0,0,0,.35)}
  /* .gauge{width:320px;height:220px} */
  .gauge{width:320px;height:220px;display:block;margin:0 auto}              
  .value{font-size:20px;margin-top:8px;text-align:center}
  select{background:#0f1720;color:#e6eef8;border:1px solid #324153;border-radius:8px;padding:8px}
  h1{font-size:22px;margin:0 0 16px}
  .muted{opacity:.8;font-size:13px}
  #linewrap{flex:1;min-width:420px;height:620px} 
  #linewrap canvas{height:100% !important;width:100% !important}
  .title{font-size:20px;font-weight:700;margin-bottom:8px;text-align:center}
</style>
</head>

<body>
  <h1>ESP32 BME280 — Live Dashboard</h1>
  <div class="row">
    <div class="card">
        <div class="title">Temperature</div>
        <canvas id="gTemp" class="gauge"></canvas>
        <div class="value" id="tLabel"></div>
    </div>
    <div class="card">
        <div class="title">Humidity</div>
        <canvas id="gHum"  class="gauge"></canvas>
        <div class="value" id="hLabel"></div>
    </div>
    <div class="card">
        <div class="title">Pressure</div>
        <canvas id="gPres" class="gauge"></canvas>
        <div class="value" id="pLabel"></div>
    </div>
    <div id="linewrap" class="card">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
        <div><b>Timeframe</b>:
          <select id="range">
            <option value="15m">Last 15 min</option>
            <option value="1h" selected>Last 1 hour</option>
            <option value="6h">Last 6 hours</option>
            <option value="24h">Last 24 hours</option>
            <option value="7d">Last 7 days</option>
          </select>
        </div>
        <div class="muted" id="updated"></div>
      </div>
      <canvas id="lineChart"></canvas>
    </div>
  </div>

<script>
const fmt = n => (n===null||n===undefined) ? "—" : n.toFixed(2);
const doughnut = (ctx,label,units,min,max) => new Chart(ctx,{type:'doughnut',
  data:{labels:[label],datasets:[{data:[0,1],borderWidth:0,cutout:'75%'}]},
  options:{plugins:{legend:{display:false},tooltip:{enabled:false}},
           circumference:180, rotation:270,
           events:[]}});

const gTemp = doughnut(document.getElementById('gTemp'), '°C'); 
const gHum  = doughnut(document.getElementById('gHum'),  '%');
const gPres = doughnut(document.getElementById('gPres'), 'hPa');

const line = new Chart(document.getElementById('lineChart'),{
  type:'line',
  data:{labels:[],datasets:[
    {label:'Temp °C', data:[], yAxisID:'y',  pointRadius:0, borderWidth:2, tension:.2},
    {label:'Hum %',   data:[], yAxisID:'y',  pointRadius:0, borderWidth:2, tension:.2},
    {label:'Pres hPa',data:[], yAxisID:'y1', pointRadius:0, borderWidth:2, tension:.2},
  ]},
  options:{
    responsive:true, maintainAspectRatio:false,
    plugins:{legend:{labels:{boxWidth:12}}},
    interaction:{mode:'index', intersect:false},
    scales:{
      x:{ticks:{maxRotation:0}},
      y:{title:{display:true,text:'Temp °C / Hum %'},
         suggestedMin:0, suggestedMax:100},
      y1:{position:'right',
          title:{display:true,text:'Pressure (hPa)'},
          suggestedMin:950, suggestedMax:1050,
          grid:{drawOnChartArea:false}}
    }
  }
});


function setGauge(g, val, min, max, labelElem, units){
  if(val==null){ g.data.datasets[0].data=[0,1]; g.update(); labelElem.textContent="—"; return; }
  const span = max-min; const pct = Math.max(0, Math.min(1, (val-min)/span));
  g.data.datasets[0].data = [pct, 1-pct]; g.update();
  labelElem.textContent = fmt(val)+" "+units;
}

async function refreshGauges(){
  const r = await fetch('/api/latest'); const js = await r.json();
  const d = js.ok && js.data ? js.data : null;
  setGauge(gTemp, d?d.temp_c:null, -10, 40, document.getElementById('tLabel'), "°C");
  setGauge(gHum,  d?d.hum_pct:null,  0, 100, document.getElementById('hLabel'), "%");
  setGauge(gPres, d?(d.pres_hpa/100.0):null,  950, 1050, document.getElementById('pLabel'), "hPa");
  if(d) document.getElementById('updated').textContent = "Updated: "+d.iso;
}

async function loadSeries(){
  const last = document.getElementById('range').value;
  const r = await fetch('/api/series?last='+last); const js = await r.json();
  const xs = js.data.map(p=>p.iso);
  const ysT= js.data.map(p=>p.temp_c);
  const ysH= js.data.map(p=>p.hum_pct);
  const ysP= js.data.map(p=>p.pres_hpa/100.0);
  line.data.labels = xs;
  line.data.datasets[0].data = ysT;
  line.data.datasets[1].data = ysH;
  line.data.datasets[2].data = ysP;
  line.update();
}

document.getElementById('range').addEventListener('change', loadSeries);
refreshGauges(); loadSeries();
setInterval(()=>{ refreshGauges(); }, 5000);
</script>
</body>
</html>
"""
    return Response(html, mimetype="text/html")

if __name__ == "__main__":
    # pip install flask
    app.run(host="0.0.0.0", port=8080)
