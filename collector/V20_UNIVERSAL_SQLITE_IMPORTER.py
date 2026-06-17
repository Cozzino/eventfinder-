
"""
EVENT PLATFORM V16.5 MULTISOURCE (TEST BUILD)

Based on V16.4
Adds:
- Adapter framework
- OpenDataAdapter
- PloneAdapter (foundation)
- source_stats table
- /sources endpoint
"""

import hashlib
import sqlite3
from pathlib import Path
from datetime import datetime, UTC
import requests
import yaml
from fastapi import FastAPI
from bs4 import BeautifulSoup

DB_NAME = "event_platform_v16.db"
CONFIG_FILE = "sources.yaml"

DEFAULT_YAML = """
sources:
  - name: emiliaromagnaturismo
    adapter: opendata
    enabled: true

  - name: parma
    adapter: plone
    enabled: false
    endpoint: https://www.comune.parma.it/api/it/vivere-parma/eventi/@querystring-search

  - name: reggio_emilia
    adapter: plone
    enabled: false
    endpoint: https://www.comune.reggioemilia.it/++api++/vivere-reggio-emilia/eventi/tutti-gli-eventi/@querystring-search
"""

app = FastAPI(title="Event Platform V16.5")


def ensure_config():
    if not Path(CONFIG_FILE).exists():
        Path(CONFIG_FILE).write_text(DEFAULT_YAML, encoding="utf-8")


def conn():
    return sqlite3.connect(DB_NAME)


def create_schema():
    c = conn()
    cur = c.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS events(
        event_id TEXT PRIMARY KEY,
        source_name TEXT,
        title TEXT,
        excerpt TEXT,
        description_text TEXT,
        city TEXT,
        province TEXT,
        latitude REAL,
        longitude REAL,
        start_date TEXT,
        end_date TEXT,
        source_url TEXT,
        fingerprint TEXT,
        updated_at TEXT
    );

    CREATE TABLE IF NOT EXISTS event_fingerprints(
        fingerprint TEXT PRIMARY KEY,
        master_event_id TEXT
    );

    CREATE TABLE IF NOT EXISTS source_stats(
        source_name TEXT PRIMARY KEY,
        last_sync TEXT,
        events_found INTEGER,
        events_inserted INTEGER,
        events_skipped INTEGER
    );

    CREATE VIRTUAL TABLE IF NOT EXISTS events_fts
    USING fts5(
        event_id,title,excerpt,description_text,city,province
    );
    """)
    c.commit()
    c.close()


def fingerprint(title, date, city):
    raw = f"{title}|{date}|{city}".lower()
    return hashlib.sha256(raw.encode()).hexdigest()


class OpenDataAdapter:
    API = "https://emiliaromagnaturismo.it/opendata/v1/events"

    def fetch(self):
        page = 1
        out = []
        while True:
            r = requests.get(self.API, params={"page": page}, timeout=60)
            r.raise_for_status()
            payload = r.json()
            out.extend(payload["data"])
            if page >= payload["meta"]["last_page"]:
                break
            page += 1
        return out


class PloneAdapter:
    def build_payload(self, start=0):
        return {
            "metadata_fields":"_all",
            "b_size":24,
            "query":[
                {"i":"portal_type","o":"plone.app.querystring.operation.selection.any","v":["Event"]},
                {"i":"path","o":"plone.app.querystring.operation.string.relativePath","v":"../"},
                {"i":"end","o":"plone.app.querystring.operation.date.afterToday","v":""}
            ],
            "sort_on":"start",
            "sort_order":"ascending",
            "b_start":start
        }

    def fetch(self, endpoint):
        import urllib3, time
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/137.0 Safari/537.36",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        events=[]
        start=0

        print(f"SOURCE: {endpoint}")

        while True:
            try:
                r=requests.post(
                    endpoint,
                    json=self.build_payload(start),
                    headers=headers,
                    timeout=60,
                    verify=False
                )
                r.raise_for_status()

                data=r.json()
                events.extend(data.get("items",[]))

                if not data.get("batching",{}).get("next"):
                    break

                start += 24
                time.sleep(1)

            except Exception as ex:
                print(f"[PLONE ERROR] {endpoint} -> {ex}")
                break

        return events




class ParmaPloneAdapter:

    def build_payload(self, start=0):
        return {
            "metadata_fields": "_all",
            "b_size": 6,
            "b_start": start,
            "query": [
                {
                    "i": "portal_type",
                    "o": "plone.app.querystring.operation.selection.any",
                    "v": ["Event"]
                }
            ],
            "sort_on": "end",
            "sort_order": "descending"
        }

    def fetch(self, endpoint):
        import urllib3, time
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        session = requests.Session()
        session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Origin": "https://www.comune.parma.it",
            "Referer": "https://www.comune.parma.it/it/vivere-parma/eventi",
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "it-IT,it;q=0.9",
            "DNT": "1",
            "Connection": "keep-alive"
        })

        events = []
        start = 0

        while True:

            success = False

            for attempt in range(5):

                try:
                    r = session.post(
                        endpoint,
                        json=self.build_payload(start),
                        timeout=60,
                        verify=False
                    )

                    r.raise_for_status()
                    data = r.json()
                    success = True
                    break

                except Exception as ex:
                    print(f"[PARMA RETRY {attempt+1}/5] {ex}")
                    time.sleep(5)

            if not success:
                print(f"[PARMA ERROR] {endpoint} -> max retries exceeded")
                break

            items = data.get("items", [])
            if not items:
                break

            events.extend(items)

            if not data.get("batching", {}).get("next"):
                break

            start += 6
            time.sleep(1)

        return events



class BolognaSagreAdapter:
    def fetch(self, endpoint):
        r = requests.get(endpoint, timeout=60)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        events = []

        for a in soup.find_all("a", href=True):
            href = a.get("href", "")
            title = a.get_text(" ", strip=True)

            if not title or len(title) < 5:
                continue

            if "/sagrefeste/" not in href:
                continue

            if href.endswith(("Home_Page","eventi","sagre1")):
                continue

            url = href if href.startswith("http") else "https://www.cittametropolitana.bo.it" + href

            uid = hashlib.sha256(url.encode()).hexdigest()

            events.append({
                "UID": uid,
                "Title": title[:300],
                "start": None,
                "end": None,
                "getURL": url
            })

        return events



class RiminiJsonAdapter:
    def fetch(self, endpoint):
        r = requests.get(endpoint, timeout=60)
        r.raise_for_status()
        data = r.json()
        events = []
        for e in data:
            url = e.get("percorso")
            if not url:
                continue
            uid = hashlib.sha256(url.encode()).hexdigest()
            events.append({
                "UID": uid,
                "Title": e.get("nome"),
                "Description": e.get("descrizione_aggiuntiva"),
                "getURL": url
            })
        return events


class UniversalAdapter:
    def fetch(self, endpoint):
        import requests, hashlib
        from bs4 import BeautifulSoup

        r = requests.get(endpoint, timeout=60, verify=False)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        events = []

        for a in soup.find_all("a", href=True):
            href = a.get("href","")
            title = a.get_text(" ", strip=True)

            if len(title) < 5:
                continue

            if not any(k in href.lower() for k in ["event","evento","eventi","festival","manifest"]):
                continue

            uid = hashlib.sha256(href.encode()).hexdigest()

            events.append({
                "UID": uid,
                "Title": title[:300],
                "Description": None,
                "getURL": href
            })

        return events


ADAPTERS = {
    "opendata": OpenDataAdapter(),
    "plone": PloneAdapter(),
    "parma_plone": ParmaPloneAdapter(),
    "bologna_sagre": BolognaSagreAdapter(),
    "rimini_json": RiminiJsonAdapter(),
    "universal": UniversalAdapter(),
}



def cleanup_expired_events():
    db = conn()
    cur = db.cursor()

    cur.execute("""
    DELETE FROM events
    WHERE end_date IS NOT NULL
      AND datetime(substr(end_date,1,19)) < datetime('now','-1 day')
    """)

    deleted = cur.rowcount

    cur.execute("""
    DELETE FROM event_fingerprints
    WHERE master_event_id NOT IN (
        SELECT event_id FROM events
    )
    """)

    db.commit()
    db.close()

    print(f"CLEANUP EXPIRED EVENTS: {deleted}")


def sync():
    create_schema()
    ensure_config()

    cfg = yaml.safe_load(open(CONFIG_FILE, encoding="utf-8"))
    sources = cfg.get("sources", [])

    db = conn()
    cur = db.cursor()

    for source in sources:
        if not source.get("enabled", True):
            continue

        adapter = source.get("adapter")

        found = inserted = skipped = 0

        if adapter == "opendata":
            rows = ADAPTERS["opendata"].fetch()
            found = len(rows)

            for e in rows:
                loc = e["locations"][0] if e.get("locations") else {}

                fp = fingerprint(
                    e.get("title"),
                    e.get("dates", {}).get("from"),
                    loc.get("city")
                )

                exists = cur.execute(
                    "SELECT 1 FROM event_fingerprints WHERE fingerprint=?",
                    (fp,)
                ).fetchone()

                if exists:
                    skipped += 1
                    continue

                event_id = f'emiliaromagnaturismo:{e["id"]}'

                cur.execute(
                    "INSERT OR REPLACE INTO events VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        event_id,
                        source["name"],
                        e.get("title"),
                        e.get("excerpt"),
                        e.get("description"),
                        loc.get("city"),
                        loc.get("province"),
                        loc.get("lat"),
                        loc.get("lng"),
                        e.get("dates", {}).get("from"),
                        e.get("dates", {}).get("to"),
                        e.get("permalink"),
                        fp,
                        e.get("updated_at")
                    )
                )

                cur.execute(
                    "INSERT OR REPLACE INTO event_fingerprints VALUES(?,?)",
                    (fp, event_id)
                )

                inserted += 1

        elif adapter == "parma_plone":
            rows = ADAPTERS["parma_plone"].fetch(source.get("endpoint"))
            found = len(rows)
            print(f"FOUND {source['name']}: {found}")

            for e in rows:
                city = "Parma"
                fp = fingerprint(e.get("Title"), e.get("start"), city)
                exists = cur.execute("SELECT 1 FROM event_fingerprints WHERE fingerprint=?", (fp,)).fetchone()
                if exists:
                    skipped += 1
                    continue
                event_id = f'{source["name"]}:{e.get("UID")}'
                geo = e.get("geolocation") or {}
                cur.execute("INSERT OR REPLACE INTO events VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(
                    event_id, source["name"], e.get("Title"), e.get("Description"), e.get("description"),
                    city, None, geo.get("latitude"), geo.get("longitude"), e.get("start"), e.get("end"),
                    e.get("getURL"), fp, datetime.now(UTC).isoformat()))
                cur.execute("INSERT OR REPLACE INTO event_fingerprints VALUES(?,?)",(fp,event_id))
                inserted += 1


        elif adapter == "bologna_sagre":
            rows = ADAPTERS["bologna_sagre"].fetch(source.get("endpoint"))
            found = len(rows)
            print(f"FOUND {source['name']}: {found}")

            for e in rows:
                fp = fingerprint(e.get("Title"), "", "Bologna")

                exists = cur.execute(
                    "SELECT 1 FROM event_fingerprints WHERE fingerprint=?",
                    (fp,)
                ).fetchone()

                if exists:
                    skipped += 1
                    continue

                event_id = f'{source["name"]}:{e.get("UID")}'

                cur.execute(
                    "INSERT OR REPLACE INTO events VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        event_id,
                        source["name"],
                        e.get("Title"),
                        None,
                        None,
                        "Bologna",
                        "BO",
                        None,
                        None,
                        None,
                        None,
                        e.get("getURL"),
                        fp,
                        datetime.now(UTC).isoformat()
                    )
                )

                cur.execute(
                    "INSERT OR REPLACE INTO event_fingerprints VALUES(?,?)",
                    (fp, event_id)
                )

                inserted += 1

        
        elif adapter == "rimini_json":
            rows = ADAPTERS["rimini_json"].fetch(source.get("endpoint"))
            found = len(rows)
            print(f"FOUND {source['name']}: {found}")

            for e in rows:
                fp = fingerprint(e.get("Title"), "", "Rimini")

                exists = cur.execute(
                    "SELECT 1 FROM event_fingerprints WHERE fingerprint=?",
                    (fp,)
                ).fetchone()

                if exists:
                    skipped += 1
                    continue

                event_id = f'{source["name"]}:{e.get("UID")}'

                cur.execute(
                    "INSERT OR REPLACE INTO events VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        event_id,
                        source["name"],
                        e.get("Title"),
                        e.get("Description"),
                        e.get("Description"),
                        "Rimini",
                        "RN",
                        None,
                        None,
                        None,
                        None,
                        e.get("getURL"),
                        fp,
                        datetime.now(UTC).isoformat()
                    )
                )

                cur.execute(
                    "INSERT OR REPLACE INTO event_fingerprints VALUES(?,?)",
                    (fp, event_id)
                )

                inserted += 1

        
        elif adapter == "universal":
            rows = ADAPTERS["universal"].fetch(source.get("endpoint"))
            found = len(rows)
            print(f"FOUND {source['name']}: {found}")

            for e in rows:
                fp = fingerprint(e.get("Title"), "", source["name"])

                exists = cur.execute(
                    "SELECT 1 FROM event_fingerprints WHERE fingerprint=?",
                    (fp,)
                ).fetchone()

                if exists:
                    skipped += 1
                    continue

                event_id = f'{source["name"]}:{e.get("UID")}'

                cur.execute(
                    "INSERT OR REPLACE INTO events VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        event_id, source["name"], e.get("Title"),
                        e.get("Description"), e.get("Description"),
                        None, None, None, None, None, None,
                        e.get("getURL"), fp,
                        datetime.now(UTC).isoformat()
                    )
                )

                cur.execute(
                    "INSERT OR REPLACE INTO event_fingerprints VALUES(?,?)",
                    (fp, event_id)
                )
                inserted += 1

        elif adapter == "plone":
            rows = ADAPTERS["plone"].fetch(source.get("endpoint"))
            found = len(rows)
            print(f"FOUND {source['name']}: {found}")

            for e in rows:
                city = "Reggio Emilia" if source["name"]=="reggio_emilia" else None
                fp = fingerprint(
                    e.get("Title"),
                    e.get("start"),
                    city
                )

                exists = cur.execute(
                    "SELECT 1 FROM event_fingerprints WHERE fingerprint=?",
                    (fp,)
                ).fetchone()

                if exists:
                    skipped += 1
                    continue

                event_id = f'{source["name"]}:{e.get("UID")}'

                geo = e.get("geolocation") or {}

                cur.execute(
                    "INSERT OR REPLACE INTO events VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        event_id,
                        source["name"],
                        e.get("Title"),
                        e.get("Description"),
                        e.get("description"),
                        city,
                        None,
                        geo.get("latitude"),
                        geo.get("longitude"),
                        e.get("start"),
                        e.get("end"),
                        e.get("getURL"),
                        fp,
                        datetime.now(UTC).isoformat()
                    )
                )

                cur.execute(
                    "INSERT OR REPLACE INTO event_fingerprints VALUES(?,?)",
                    (fp, event_id)
                )

                inserted += 1

        cur.execute("""
        INSERT OR REPLACE INTO source_stats
        VALUES(?,?,?,?,?)
        """, (
            source["name"],
            datetime.now(UTC).isoformat(),
            found,
            inserted,
            skipped
        ))

        db.commit()

    db.close()
    cleanup_expired_events()
    print("V17.3 MULTISOURCE sync completed")


@app.get("/health")
def health():
    return {"status": "ok", "version": "17.3"}


@app.get("/stats")
def stats():
    c = conn()
    total = c.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    c.close()
    return {"events": total}


@app.get("/sources")
def sources():
    c = conn()
    rows = c.execute("SELECT * FROM source_stats").fetchall()
    c.close()
    return rows

@app.get("/active_events")
def active_events():
    c = conn()
    rows = c.execute("""
    SELECT *
    FROM events
    WHERE end_date IS NULL
       OR datetime(substr(end_date,1,19)) >= datetime('now','-1 day')
    """).fetchall()
    c.close()
    return {"count": len(rows), "events": rows}


@app.get("/archive_events")
def archive_events():
    c = conn()
    rows = c.execute("""
    SELECT *
    FROM events
    WHERE end_date IS NOT NULL
      AND datetime(substr(end_date,1,19)) < datetime('now','-1 day')
    """).fetchall()
    c.close()
    return {"count": len(rows), "events": rows}



if __name__ == "__main__":
    sync()
