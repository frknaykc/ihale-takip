export interface Category {
  name: string
  primaryKeywords: string[]   // Ana anahtar kelimeler (kesin eşleşme)
  secondaryKeywords: string[] // İkincil anahtar kelimeler (destekleyici)
  excludeKeywords: string[]   // Hariç tutulacak kelimeler
}

export interface Categories {
  [key: string]: Category
}

export const categories: Categories = {
  'bilisim_teknolojileri': {
    name: '💻 Bilişim & Güvenlik',
    primaryKeywords: [
      // Temel Bilişim
      'bilgisayar', 'bilişim', 'yazılım', 'donanım', 'network',
      'server', 'sunucu', 'veri merkezi', 'datacenter',

      // Donanım
      'masaüstü', 'laptop', 'dizüstü', 'işlemci', 'cpu',
      'ram', 'bellek', 'harddisk', 'ssd', 'hdd', 'anakart',
      'ekran kartı', 'gpu', 'monitör', 'ups', 'printer',

      // Yazılım
      'microsoft', 'windows', 'linux', 'oracle', 'sql',
      'erp', 'crm', 'lisans', 'antivirüs', 'antivirus',

      // Network
      'switch', 'router', 'modem', 'firewall', 'güvenlik duvarı',
      'access point', 'fiber', 'cat6', 'cat7',

      // Güvenlik
      'kamera sistemi', 'cctv', 'ip kamera', 'nvr', 'dvr',
      'kartlı geçiş', 'yüz tanıma'
    ],
    secondaryKeywords: [
      'sistem', 'altyapı', 'ağ', 'elektronik', 'digital',
      'dijital', 'teknoloji', 'yazıcı', 'tarayıcı', 'scanner',
      'kablolama', 'kurulum', 'güncelleme', 'yedekleme',
      'bakım', 'onarım', 'teknik servis', 'it', 'bt'
    ],
    excludeKeywords: [
      // Yanlış sınıflandırmayı önlemek için
      'fuel', 'kalyak', 'yakıt', 'petrol', 'lpg', 'doğalgaz',
      'mutfak', 'yemek', 'gıda', 'temizlik', 'kırtasiye',
      'mobilya', 'taşınmaz', 'gayrimenkul', 'arsa', 'bina',
      'inşaat', 'tadilat', 'onarım', 'bakım', 'malzeme',
      'hırdavat', 'tekstil', 'giyim', 'kıyafet', 'ilaç',
      'tıbbi', 'medikal', 'araç', 'vasıta', 'otomobil'
    ]
  },
  'diger': {
    name: '📋 Diğer',
    primaryKeywords: [],
    secondaryKeywords: [],
    excludeKeywords: []
  }
}

export function classifyTender(title: string, description?: string): string {
  const text = (title + ' ' + (description || '')).toLowerCase()
  
  // Türkçe karakterleri normalize et
  const normalizedText = text
    .replace(/ç/g, 'c')
    .replace(/ğ/g, 'g')
    .replace(/ı/g, 'i')
    .replace(/ö/g, 'o')
    .replace(/ş/g, 's')
    .replace(/ü/g, 'u')
  
  const category = categories.bilisim_teknolojileri
  
  // Önce hariç tutulan kelimeleri kontrol et
  for (const excludeWord of category.excludeKeywords) {
    const normalizedExclude = excludeWord
      .toLowerCase()
      .replace(/ç/g, 'c')
      .replace(/ğ/g, 'g')
      .replace(/ı/g, 'i')
      .replace(/ö/g, 'o')
      .replace(/ş/g, 's')
      .replace(/ü/g, 'u')
    
    // Eğer hariç tutulan bir kelime varsa, direkt diğer kategorisine at
    if (normalizedText.includes(normalizedExclude)) {
      return 'diger'
    }
  }
  
  let primaryMatches = 0
  let secondaryMatches = 0
  
  // Ana anahtar kelimeleri kontrol et
  for (const keyword of category.primaryKeywords) {
    const normalizedKeyword = keyword
      .toLowerCase()
      .replace(/ç/g, 'c')
      .replace(/ğ/g, 'g')
      .replace(/ı/g, 'i')
      .replace(/ö/g, 'o')
      .replace(/ş/g, 's')
      .replace(/ü/g, 'u')
    
    if (normalizedText.includes(normalizedKeyword)) {
      primaryMatches++
    }
  }
  
  // İkincil anahtar kelimeleri kontrol et
  for (const keyword of category.secondaryKeywords) {
    const normalizedKeyword = keyword
      .toLowerCase()
      .replace(/ç/g, 'c')
      .replace(/ğ/g, 'g')
      .replace(/ı/g, 'i')
      .replace(/ö/g, 'o')
      .replace(/ş/g, 's')
      .replace(/ü/g, 'u')
    
    if (normalizedText.includes(normalizedKeyword)) {
      secondaryMatches++
    }
  }
  
  // Sınıflandırma kuralları:
  // 1. En az 1 ana anahtar kelime eşleşmesi olmalı
  // 2. Ya birden fazla ana anahtar kelime eşleşmesi
  // 3. Ya da bir ana anahtar kelime + en az bir ikincil kelime eşleşmesi
  if (primaryMatches > 0 && (primaryMatches > 1 || secondaryMatches > 0)) {
    return 'bilisim_teknolojileri'
  }
  
  return 'diger'
}

export function getCategoryName(categoryKey: string): string {
  return categories[categoryKey]?.name || categories.diger.name
}

export function getAllCategories(): [string, string][] {
  return Object.entries(categories).map(([key, category]) => [key, category.name])
}