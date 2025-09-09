def normalize_text(text: str) -> str:
    """Türkçe karakterleri normalize et"""
    return (text.lower()
        .replace('ç', 'c')
        .replace('ğ', 'g')
        .replace('ı', 'i')
        .replace('ö', 'o')
        .replace('ş', 's')
        .replace('ü', 'u'))

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
            'kartlı geçiş', 'yüz tanıma'
        ],
        'secondary_keywords': [
            'sistem', 'altyapı', 'ağ', 'elektronik', 'digital',
            'dijital', 'teknoloji', 'yazıcı', 'tarayıcı', 'scanner',
            'kablolama', 'kurulum', 'güncelleme', 'yedekleme',
            'bakım', 'onarım', 'teknik servis', 'it', 'bt'
        ],
        'exclude_keywords': [
            # Yanlış sınıflandırmayı önlemek için
            'fuel', 'kalyak', 'yakıt', 'petrol', 'lpg', 'doğalgaz',
            'mutfak', 'yemek', 'gıda', 'temizlik', 'kırtasiye',
            'mobilya', 'taşınmaz', 'gayrimenkul', 'arsa', 'bina',
            'inşaat', 'tadilat', 'onarım', 'bakım', 'malzeme',
            'hırdavat', 'tekstil', 'giyim', 'kıyafet', 'ilaç',
            'tıbbi', 'medikal', 'araç', 'vasıta', 'otomobil'
        ]
    },
    'diger': {
        'name': '📦 Diğer',
        'primary_keywords': [],
        'secondary_keywords': [],
        'exclude_keywords': []
    }
}

def classifyTender(title: str, description: str = "") -> str:
    """İhaleyi kategorize et"""
    
    # Metni normalize et
    text = normalize_text(title + " " + description)
    category = categories['bilisim_teknolojileri']
    
    # Önce hariç tutulan kelimeleri kontrol et
    for exclude_word in category['exclude_keywords']:
        if normalize_text(exclude_word) in text:
            return 'diger'
    
    # Ana ve ikincil anahtar kelime eşleşmelerini say
    primary_matches = sum(1 for keyword in category['primary_keywords'] 
                        if normalize_text(keyword) in text)
    
    secondary_matches = sum(1 for keyword in category['secondary_keywords'] 
                          if normalize_text(keyword) in text)
    
    # Sınıflandırma kuralları:
    # 1. En az 1 ana anahtar kelime eşleşmesi olmalı
    # 2. Ya birden fazla ana anahtar kelime eşleşmesi
    # 3. Ya da bir ana anahtar kelime + en az bir ikincil kelime eşleşmesi
    if primary_matches > 0 and (primary_matches > 1 or secondary_matches > 0):
        return 'bilisim_teknolojileri'
    
    return 'diger'