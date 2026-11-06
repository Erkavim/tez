import json
import os
import sys
from pathlib import Path

from mistralai import Mistral

MODEL = "mistral-large-latest"
TEZ_DOSYASI = Path(__file__).parent / "tez_ozet.txt"
CIKTI_DOSYASI = Path(__file__).parent / "ajan_cikti.json"

GOREVLER = {
    "literatur_bosluklari": (
        "Aşağıdaki tez bölümü için alan literatüründe tezde eksik olan, "
        "katkı sağlayabilecek çalışmaları, klasik ve güncel kaynakları bul. "
        "Her öneri için: yazar, yıl, başlık, yayın yeri ve neden alakalı olduğu."
    ),
    "atif_dogrulama": (
        "Aşağıdaki atıf listesinde sayfa numarası eksik ([s.]) olan kayıtları listele. "
        "Her biri için: doğrulanması gereken bilgi (sayfa/baskı), kamuya açık erişim "
        "imkanı (açık erişim dergi, YÖK Tez Merkezi, sozluk.gov.tr, Nişanyan, kamu malı "
        "baskı) varsa belirt; korsan/yetkisiz PDF kaynak önerme."
    ),
    "arama_dizgileri": (
        "Bu tez konusu için YÖK Tez Merkezi, DergiPark, TR Dizin, Scopus ve Web of Science'te "
        "etkili arama dizgileri üret (Türkçe ve İngilizce, Boolean operatörlerle)."
    ),
    "karsilastirmali_terminoloji": (
        "Sinema terminolojisinde editing/montage ayrımının diğer dillerdeki (Almanca, "
        "Fransızca, İtalyanca, İspanyolca, Portekizce, Arapça) karşılıklarını ve bu dillerde "
        "kurgu/öykü ile kesme pratiği ayrımının nasıl yapıldığını derle."
    ),
}


def bolumleri_yukle():
    if not TEZ_DOSYASI.exists():
        return {}
    metin = TEZ_DOSYASI.read_text(encoding="utf-8")
    return {"tez_metni": metin[:60000]}


def ajani_calistir():
    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        sys.exit("MISTRAL_API_KEY ortam değişkeni tanımlı değil.")

    client = Mistral(api_key=api_key)
    bolumler = bolumleri_yukle()
    sonuclar = {}

    for gorev_adi, yönerge in GOREVLER.items():
        mesajlar = [
            {
                "role": "system",
                "content": (
                    "Sen bir akademik araştırma asistanısın. Türkçe sinema terminolojisi "
                    "konulu bir tez için literatür taraması, atıf doğrulama ve arama stratejisi "
                    "üretiyorsun. Yanıtlarını yapısal ve atıf kontrollü ver. Korsan veya "
                    "yetkisiz içerik önerme; yalnızca yasal erişim yolları belirt."
                ),
            },
            {"role": "user", "content": yönerge},
        ]
        if bolumler:
            mesajlar.append({"role": "user", "content": json.dumps(bolumler, ensure_ascii=False)})

        yanit = client.chat.complete(
            model=MODEL,
            messages=mesajlar,
            tools=[{"type": "web_search"}],
            tool_choice="auto",
        )
        icerik = yanit.choices[0].message.content
        sonuclar[gorev_adi] = icerik if isinstance(icerik, str) else str(icerik)

    CIKTI_DOSYASI.write_text(
        json.dumps(sonuclar, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Çıktı yazıldı: {CIKTI_DOSYASI}")


if __name__ == "__main__":
    ajani_calistir()
