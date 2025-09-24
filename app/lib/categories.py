import re
import unicodedata

def normalize_text(s: str) -> str:
    # Türkçe için güvenli casefold ve diakritik sadeleştirme
    s = s.casefold()  # İ/ı problemlerinde casefold daha güvenli
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(ch for ch in s if not unicodedata.combining(ch))
    # noktalama boşluklaştır, çoklu boşlukları tekille
    s = re.sub(r"[^a-z0-9çğıöşü\s]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def count_kw_matches(text: str, keywords: list[str]) -> int:
    # Tam kelime/ifade eşleşmesi: \b ile sınırla, çok kelimeli ifadeleri re.escape ile koru
    c = 0
    for kw in keywords:
        pat = r'\b' + re.escape(normalize_text(kw)) + r'\b'
        if re.search(pat, text, flags=re.UNICODE):
            c += 1
    return c

def contains_any(text: str, keywords: list[str]) -> bool:
    for kw in keywords:
        pat = r'\b' + re.escape(normalize_text(kw)) + r'\b'
        if re.search(pat, text, flags=re.UNICODE):
            return True
    return False

# Güçlü birincil anahtar sözcükler (tek başına yeterli)
STRONG_PRIMARY = [
    # Ağ güvenliği
    'güvenlik duvarı', 'yeni nesil güvenlik duvarı', 'firewall', 'next generation firewall', 'ngfw',
    # SOC / SIEM / EDR
    'soc', 'güvenlik operasyonları merkezi', 'siem', 'edr', 'xdr',
    # Kötü amaçlı yazılım / cdr
    'zararlı yazılım', 'malware', 'dosya sterilize', 'content disarm', 'cdr',
    # Olay müdahale
    'olay müdahale', 'incident response',
]

# Kurumsal bağlam ipuçları (ikincil sinyal olarak sayılır)
CONTEXT_HINTS_SECONDARY = [
    'bilgi işlem', 'bilgi teknolojileri', 'bt', 'dijital dönüşüm',
    'kategori: bilgisayar', 'kategori: bilgisayar paket programları', 'dmo',
]

# Kategori tanımları
categories = {
    'bilisim_teknolojileri': {
        'name': '💻 Bilişim & Güvenlik',
        'primary_keywords': [
            # Temel Bilişim
            'bilgisayar', 'bilişim', 'yazılım', 'donanım', 'network',
            'server', 'sunucu', 'veri merkezi', 'datacenter',

            # Donanım
            'masaüstü', 'laptop', 'dizüstü', 'işlemci', 'cpu',
            'ram', 'bellek', 'harddisk', 'ssd', 'hdd', 'anakart',
            'ekran kartı', 'gpu', 'monitör', 'ups', 'printer',

            # Yazılım
            'microsoft', 'windows', 'linux', 'oracle', 'sql',
            'erp', 'crm', 'lisans', 'antivirüs', 'antivirus',

            # Network
            'switch', 'router', 'modem', 'firewall', 'güvenlik duvarı',
            'access point', 'fiber', 'cat6', 'cat7',

            # Güvenlik
            'kamera sistemi', 'cctv', 'ip kamera', 'nvr', 'dvr',
            'kartlı geçiş', 'yüz tanıma',

            # Kritik BT Güvenlik Terimleri
            'soc', 'siem', 'edr', 'xdr', 'zararlı yazılım', 'malware',
            'dlp', 'waf', 'ids', 'ips', 'siber güvenlik', 'security',
            'yazılım lisansı', 'lisans yenileme', 'license renewal',
            'analiz yazılımı', 'forensic', 'threat', 'endpoint', 'firewall',
            'olay müdahale', 'cdr', 'dosya sterilize'
        ],
        'secondary_keywords': [
            'sistem', 'altyapı', 'ağ', 'elektronik', 'digital',
            'dijital', 'teknoloji', 'yazıcı', 'tarayıcı', 'scanner',
            'kablolama', 'kurulum', 'güncelleme', 'yedekleme',
            'bakım', 'onarım', 'teknik servis', 'it', 'bt',
            'bakım destek', 'destek hizmeti', 'yama', 'patch', 'güncelleme',
            'log', 'olay kayıt', 'uygulama güvenliği', 'file sterilize', 'cdr'
        ],
        'exclude_keywords': [
            # Yanlış sınıflandırmayı önlemek için
            'fuel', 'kalyak', 'yakıt', 'petrol', 'lpg', 'doğalgaz',
            'mutfak', 'yemek', 'gıda', 'temizlik', 'kırtasiye',
            'mobilya', 'taşınmaz', 'gayrimenkul', 'arsa', 'bina',
            'inşaat', 'tadilat', 'onarım', 'bakım', 'malzeme',
            'hırdavat', 'tekstil', 'giyim', 'kıyafet', 'ilaç',
            'tıbbi', 'medikal', 'araç', 'vasıta', 'otomobil',
            # Yeni dışlamalar
            'madeni yağ', 'yağ', 'motor yağı', 'hidrolik yağ', 'gres', 'lubricant',
            'akaryakıt', 'motorin', 'benzin'
        ]
    },
    'diger': {
        'name': '📋 Diğer',
        'primary_keywords': [],
        'secondary_keywords': [],
        'exclude_keywords': []
    }
}

def debug_classify(title: str, desc: str = "") -> dict:
    """Debug amaçlı sınıflandırma detaylarını göster"""
    text = normalize_text(f"{title} {desc}")
    cat = categories['bilisim_teknolojileri']
    
    hits = {
        "exclude": [k for k in cat['exclude_keywords'] if re.search(r'\b'+re.escape(normalize_text(k))+r'\b', text)],
        "strong": [k for k in STRONG_PRIMARY if re.search(r'\b'+re.escape(normalize_text(k))+r'\b', text)],
        "primary": [k for k in cat['primary_keywords'] if re.search(r'\b'+re.escape(normalize_text(k))+r'\b', text)],
        "secondary": [k for k in cat['secondary_keywords'] if re.search(r'\b'+re.escape(normalize_text(k))+r'\b', text)],
        "ctx": [k for k in CONTEXT_HINTS_SECONDARY if re.search(r'\b'+re.escape(normalize_text(k))+r'\b', text)],
    }
    return hits

def classifyTender(title: str, description: str = "") -> str:
    """İhaleyi kategorize et"""
    text = normalize_text(f"{title} {description}")
    cat = categories['bilisim_teknolojileri']
    
    # 1) Exclude kontrolü
    if contains_any(text, cat['exclude_keywords']):
        return 'diger'
    
    # 2) Güçlü birincil kelime kontrolü
    if contains_any(text, STRONG_PRIMARY):
        return 'bilisim_teknolojileri'
    
    # 3) Sinyal güçlendiriciler
    sm_bonus = 1 if contains_any(text, CONTEXT_HINTS_SECONDARY) else 0
    
    # 4) Normal kural kontrolü
    primary_matches = count_kw_matches(text, cat['primary_keywords'])
    secondary_matches = count_kw_matches(text, cat['secondary_keywords']) + sm_bonus
    
    if primary_matches > 0 and (primary_matches > 1 or secondary_matches > 0):
        return 'bilisim_teknolojileri'
    
    return 'diger'

# Test fonksiyonları
def test_examples():
    assert classifyTender('TC GSB BİDB İhtiyacı "2 Adet Yeni Nesil Güvenlik Duvarı" Satın Alınacak') == 'bilisim_teknolojileri'
    assert classifyTender('SGK BTGM İhtiyacı "Güvenlik Operasyonları Merkezi Ürünü"') == 'bilisim_teknolojileri'
    assert classifyTender('2025/1538302 - Olay Müdahale ve Analiz Lisans Yenileme ve Bakım Destek Hizmeti Temini') == 'bilisim_teknolojileri'
    assert classifyTender('2025/1523980 - Zararlı Yazılım Analiz ve Dosya Sterilize Yazılımı Temini') == 'bilisim_teknolojileri'
    assert classifyTender('MADENİ YAĞ ALIMI') == 'diger'