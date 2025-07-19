import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

base_url = "https://kodepos.nomor.net/"
provinsi_url = base_url + "?kk=1"

data = []

res = requests.get(provinsi_url)
soup = BeautifulSoup(res.text, "html.parser")

provinsi_links = soup.select(".panel-body a")

for prov_link in provinsi_links:
    provinsi_name = prov_link.text.strip()
    provinsi_href = prov_link["href"]

    res_prov = requests.get(base_url + provinsi_href)
    soup_prov = BeautifulSoup(res_prov.text, "html.parser")

    kota_links = soup_prov.select(".panel-body a")

    for kota_link in kota_links:
        kota_name = kota_link.text.strip()
        kota_href = kota_link["href"]

        res_kota = requests.get(base_url + kota_href)
        soup_kota = BeautifulSoup(res_kota.text, "html.parser")

        kecamatan_links = soup_kota.select(".panel-body a")

        for kec_link in kecamatan_links:
            kecamatan_name = kec_link.text.strip()
            data.append([provinsi_name, kota_name, kecamatan_name])

        time.sleep(0.5)  # supaya tidak membebani server

df = pd.DataFrame(data, columns=["Provinsi", "Kota/Kabupaten", "Kecamatan"])

df.to_excel("kodepos_wilayah.xlsx", index=False)
print("✅ Data Kodepos disimpan ke kodepos_wilayah.xlsx")
