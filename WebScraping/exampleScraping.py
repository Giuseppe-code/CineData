import json
import time
import os
import requests
from datetime import datetime

BOXOFFICE_DATA = [
  {'pos': 1, 'titolo': 'BUEN CAMINO', 'prima_progr': '25/12/2025', 'prima_progr_iso': '2025-12-25', 'nazione': 'ITA', 'distribuzione': 'MEDUSA FILM', 'incasso': 75046996.85, 'presenze': 9357667, 'incasso_al': 75046996.85, 'presenze_al': 9357667},
  {'pos': 2, 'titolo': 'AVATAR: FUOCO E CENERE (AVATAR: FIRE AND ASH)', 'prima_progr': '17/12/2025', 'prima_progr_iso': '2025-12-17', 'nazione': 'USA', 'distribuzione': 'WALT DISNEY S.M.P. ITALIA', 'incasso': 25688409.25, 'presenze': 2763478, 'incasso_al': 25688409.25, 'presenze_al': 2763478},
  {'pos': 3, 'titolo': 'ZOOTROPOLIS 2 (ZOOTOPIA 2)', 'prima_progr': '26/11/2025', 'prima_progr_iso': '2025-11-26', 'nazione': 'USA', 'distribuzione': 'WALT DISNEY S.M.P. ITALIA', 'incasso': 19372414.9, 'presenze': 2501337, 'incasso_al': 19372414.9, 'presenze_al': 2501337},
  {'pos': 4, 'titolo': 'THE CONJURING - IL RITO FINALE', 'prima_progr': '04/09/2025', 'prima_progr_iso': '2025-09-04', 'nazione': 'GBR', 'distribuzione': 'WARNER BROS. ITALIA', 'incasso': 9512323.08, 'presenze': 1210235, 'incasso_al': 9512323.08, 'presenze_al': 1210235},
  {'pos': 5, 'titolo': 'OI VITA MIA', 'prima_progr': '27/11/2025', 'prima_progr_iso': '2025-11-27', 'nazione': 'ITA', 'distribuzione': 'PIPER FILM', 'incasso': 8968714.2, 'presenze': 1196921, 'incasso_al': 8968714.2, 'presenze_al': 1196921},
  {'pos': 6, 'titolo': 'NORIMBERGA (NUREMBERG)', 'prima_progr': '18/12/2025', 'prima_progr_iso': '2025-12-18', 'nazione': 'USA', 'distribuzione': 'EAGLE PICTURES', 'incasso': 8798905.86, 'presenze': 1159317, 'incasso_al': 8798905.86, 'presenze_al': 1159317},
  {'pos': 7, 'titolo': "LA VITA VA COSI'", 'prima_progr': '23/10/2025', 'prima_progr_iso': '2025-10-23', 'nazione': 'ITA', 'distribuzione': 'MEDUSA FILM', 'incasso': 7015324.04, 'presenze': 1012224, 'incasso_al': 7015324.04, 'presenze_al': 1012224},
  {'pos': 8, 'titolo': 'LA GRAZIA', 'prima_progr': '15/01/2026', 'prima_progr_iso': '2026-01-15', 'nazione': 'ITA', 'distribuzione': 'PIPER FILM', 'incasso': 6318646.87, 'presenze': 871332, 'incasso_al': 6318646.87, 'presenze_al': 871332},
  {'pos': 9, 'titolo': "DRACULA - L'AMORE PERDUTO (DRACULA: A LOVE TALE)", 'prima_progr': '29/10/2025', 'prima_progr_iso': '2025-10-29', 'nazione': 'FRA', 'distribuzione': 'LUCKY RED DISTRIBUZIONE', 'incasso': 5508683.63, 'presenze': 724088, 'incasso_al': 5508683.63, 'presenze_al': 724088},
  {'pos': 10, 'titolo': "UNA BATTAGLIA DOPO L'ALTRA (ONE BATTLE AFTER ANOTHER)", 'prima_progr': '25/09/2025', 'prima_progr_iso': '2025-09-25', 'nazione': 'USA', 'distribuzione': 'WARNER BROS. ITALIA', 'incasso': 5103009.11, 'presenze': 704258, 'incasso_al': 5103009.11, 'presenze_al': 704258},
]

SINK_URL = os.environ.get("SINK_URL", "http://fluentbit:9880/topBoxOffice")
DELAY = float(os.environ.get("DELAY", "0.2"))
LOOP = os.environ.get("LOOP", "true").lower() in ("1", "true", "yes")
TIMEOUT = float(os.environ.get("TIMEOUT", "5"))

def send_event(ev: dict):
    payload = dict(ev)
    payload["@timestamp"] = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    payload["source"] = "boxoffice_static_stub"
    r = requests.post(SINK_URL, json=payload, timeout=TIMEOUT)
    r.raise_for_status()

def main():
    while True:
        for ev in BOXOFFICE_DATA:
            send_event(ev)
            # print(ev)
            time.sleep(DELAY)
        if not LOOP:
            break

if __name__ == "__main__":
    main()
