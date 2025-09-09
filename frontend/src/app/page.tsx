'use client'

import { useState, useEffect } from 'react'
import axios from 'axios'
import { format } from 'date-fns'
import { classifyTender, getCategoryName, getAllCategories } from '@/lib/categories'

interface Source {
  id: number
  name: string
  url: string
  slug: string
}

interface Tender {
  id: number
  title: string
  url: string
  description?: string
  published_at?: string
  created_at: string
  source?: Source
}

interface SourceStats {
  name: string
  slug: string
  count: number
  lastUpdate?: string
}

interface CategoryStats {
  name: string
  key: string
  count: number
  lastUpdate?: string
}

interface Filters {
  query: string
  source_slug: string
  category: string
  date_from: string
  date_to: string
  limit: number
}

export default function Home() {
  const [tenders, setTenders] = useState<Tender[]>([])
  const [allTenders, setAllTenders] = useState<Tender[]>([])
  const [sources, setSources] = useState<Source[]>([])
  const [sourceStats, setSourceStats] = useState<SourceStats[]>([])
  const [categoryStats, setCategoryStats] = useState<CategoryStats[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [showEmailForm, setShowEmailForm] = useState(false)
  const [emailAddress, setEmailAddress] = useState('')
  const [activeTab, setActiveTab] = useState('ALL')
  const [lastUpdate, setLastUpdate] = useState<string>('')
  const [filters, setFilters] = useState<Filters>({
    query: '',
    source_slug: '',
    category: '',
    date_from: '',
    date_to: '',
    limit: 200
  })

  useEffect(() => {
    loadSources()
    loadAllTenders()
  }, [])

  const loadSources = async () => {
    try {
      const response = await axios.get('/api/tenders/sources')
      setSources(response.data)
    } catch (err) {
      console.error('Error loading sources:', err)
    }
  }

  const loadAllTenders = async () => {
    setLoading(true)
    try {
      const response = await axios.post('/api/tenders/search', {
        query: '',
        source_slug: '',
        limit: 500
      })
      const tendersData = response.data
      setAllTenders(tendersData)
      setTenders(tendersData)
      
      // Kaynak istatistiklerini hesapla
      const stats: { [key: string]: SourceStats } = {}
      tendersData.forEach((tender: Tender) => {
        const sourceName = tender.source?.name || 'Bilinmiyor'
        const sourceSlug = tender.source?.slug || 'unknown'
        
        if (!stats[sourceSlug]) {
          stats[sourceSlug] = {
            name: sourceName,
            slug: sourceSlug,
            count: 0,
            lastUpdate: tender.created_at
          }
        }
        stats[sourceSlug].count++
        
        // En son güncelleme tarihini bul
        if (new Date(tender.created_at) > new Date(stats[sourceSlug].lastUpdate || '')) {
          stats[sourceSlug].lastUpdate = tender.created_at
        }
      })
      
      const sortedStats = Object.values(stats).sort((a, b) => b.count - a.count)
      setSourceStats(sortedStats)
      
      // Kategori istatistiklerini hesapla
      const catStats: { [key: string]: CategoryStats } = {}
      tendersData.forEach((tender: Tender) => {
        const category = classifyTender(tender.title, tender.description)
        
        if (!catStats[category]) {
          catStats[category] = {
            name: getCategoryName(category),
            key: category,
            count: 0,
            lastUpdate: tender.created_at
          }
        }
        catStats[category].count++
        
        // En son güncelleme tarihini bul
        if (new Date(tender.created_at) > new Date(catStats[category].lastUpdate || '')) {
          catStats[category].lastUpdate = tender.created_at
        }
      })
      
      const sortedCatStats = Object.values(catStats).sort((a, b) => b.count - a.count)
      setCategoryStats(sortedCatStats)
      
      // Genel son güncelleme
      if (tendersData.length > 0) {
        const latest = tendersData.reduce((latest: Tender, current: Tender) => 
          new Date(current.created_at) > new Date(latest.created_at) ? current : latest
        )
        setLastUpdate(latest.created_at)
      }
      
    } catch (err) {
      setError('İhaleler yüklenirken hata oluştu')
      console.error('Error loading tenders:', err)
    } finally {
      setLoading(false)
    }
  }

  const searchTenders = async () => {
    setLoading(true)
    setError('')
    try {
      const response = await axios.post('/api/tenders/search', {
        ...filters,
        date_from: filters.date_from ? new Date(filters.date_from).toISOString() : null,
        date_to: filters.date_to ? new Date(filters.date_to).toISOString() : null,
      })
      
      let filteredTenders = response.data
      
      // Kategori filtresi uygula
      if (filters.category) {
        filteredTenders = filteredTenders.filter((tender: Tender) => 
          classifyTender(tender.title, tender.description) === filters.category
        )
      }
      
      setTenders(filteredTenders)
    } catch (err) {
      setError('İhaleler yüklenirken hata oluştu')
      console.error('Error searching tenders:', err)
    } finally {
      setLoading(false)
    }
  }

  const filterBySource = (sourceSlug: string) => {
    if (sourceSlug === 'ALL') {
      setTenders(allTenders)
      setActiveTab('ALL')
    } else {
      const filtered = allTenders.filter(tender => tender.source?.slug === sourceSlug)
      setTenders(filtered)
      setActiveTab(sourceSlug)
    }
  }

  const exportCSV = async () => {
    try {
      const response = await axios.post('/api/tenders/export.csv', {
        ...filters,
        date_from: filters.date_from ? new Date(filters.date_from).toISOString() : null,
        date_to: filters.date_to ? new Date(filters.date_to).toISOString() : null,
      }, {
        responseType: 'blob'
      })
      
      const blob = new Blob([response.data], { type: 'text/csv' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = 'ihaleler.csv'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    } catch (err) {
      setError('CSV export hatası')
      console.error('Error exporting CSV:', err)
    }
  }

  const sendEmail = async () => {
    if (!emailAddress) {
      setError('Email adresi gerekli')
      return
    }
    
    try {
      await axios.post('/api/tenders/email', {
        recipient: emailAddress,
        ...filters,
        date_from: filters.date_from ? new Date(filters.date_from).toISOString() : null,
        date_to: filters.date_to ? new Date(filters.date_to).toISOString() : null,
      })
      setShowEmailForm(false)
      setEmailAddress('')
      alert('Email başarıyla gönderildi!')
    } catch (err) {
      setError('Email gönderilirken hata oluştu')
      console.error('Error sending email:', err)
    }
  }

  const triggerScrape = async () => {
    try {
      setLoading(true)
      const response = await axios.post('/api/tenders/scrape-now')
      alert(`Scraping tamamlandı. ${response.data.inserted} yeni ihale eklendi.`)
      loadAllTenders()
    } catch (err) {
      setError('Scraping hatası')
      console.error('Error triggering scrape:', err)
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Tarih belirtilmemiş'
    try {
      return format(new Date(dateString), 'dd.MM.yyyy HH:mm')
    } catch {
      return dateString
    }
  }

  const totalTenders = sourceStats.reduce((sum, stat) => sum + stat.count, 0)
  const totalSources = sourceStats.length

  // Kaynak renk paleti
  const getSourceColor = (index: number) => {
    const colors = [
      'from-blue-500 to-blue-700',
      'from-green-500 to-green-700', 
      'from-purple-500 to-purple-700',
      'from-red-500 to-red-700',
      'from-yellow-500 to-yellow-700',
      'from-indigo-500 to-indigo-700',
      'from-pink-500 to-pink-700',
      'from-teal-500 to-teal-700',
      'from-orange-500 to-orange-700'
    ]
    return colors[index % colors.length]
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      <div className="container mx-auto px-3 py-4 max-w-6xl">
        {/* Header */}
        <div className="text-center mb-6">
          <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-600 bg-clip-text text-transparent mb-2">
            İhale Takip Sistemi
          </h1>
          <p className="text-gray-600 text-sm">Türkiye Kamu İhaleleri Merkezi Takip Platformu</p>
        </div>
        
        {/* Dashboard */}
        <div className="bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-600 text-white p-4 rounded-xl mb-6 shadow-lg border border-white/20">
          <div className="text-center mb-4">
            <h2 className="text-lg font-bold mb-2 drop-shadow">
              📊 Toplam: {totalTenders} İhale ({totalSources} Kaynak)
            </h2>
            <div className="bg-white/10 backdrop-blur-sm rounded-lg p-2 inline-block">
              <p className="text-indigo-100 text-xs">
                🕒 Son güncellenme: {lastUpdate ? formatDate(lastUpdate) : 'Henüz güncellenmedi'}
              </p>
            </div>
          </div>
          
          {/* Kategori İstatistikleri */}
          <div className="mb-4">
            <h3 className="text-sm font-semibold mb-2 text-white/90">📊 Kategori Dağılımı</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-2">
              {categoryStats.map((stat, index) => (
                <div 
                  key={stat.key}
                  className="bg-white/10 backdrop-blur-sm rounded-lg p-2 text-center border border-white/20"
                >
                  <p className="text-xs font-medium mb-1">{stat.name}</p>
                  <p className="text-lg font-bold">{stat.count}</p>
                </div>
              ))}
            </div>
          </div>
          
          {/* Kaynak İstatistikleri */}
          <div>
            <h3 className="text-sm font-semibold mb-2 text-white/90">📊 Kaynak Dağılımı</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
              {sourceStats.map((stat, index) => (
                <div 
                  key={stat.slug} 
                  className={`bg-gradient-to-br ${getSourceColor(index)} rounded-lg p-3 shadow hover:shadow-lg transform hover:scale-105 transition-all duration-200 border border-white/20`}
                >
                  <div className="text-center">
                    <h3 className="font-semibold text-white text-xs mb-1 drop-shadow">{stat.name}</h3>
                    <p className="text-xl font-bold text-white mb-1 drop-shadow">{stat.count}</p>
                    <div className="bg-black/20 rounded px-1 py-0.5">
                      <p className="text-xs text-white/90 leading-tight">
                        {stat.lastUpdate ? formatDate(stat.lastUpdate) : 'Güncelleme yok'}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border-l-4 border-red-500 text-red-700 p-3 rounded-lg mb-4 shadow-sm">
            <div className="flex items-center">
              <span className="text-red-500 mr-2 text-sm">⚠️</span>
              <span className="text-sm">{error}</span>
            </div>
          </div>
        )}
        
        {/* Filter Form */}
        <div className="bg-white/70 backdrop-blur-sm p-4 rounded-lg mb-4 shadow border border-white/50">
          <h3 className="text-sm font-semibold text-gray-800 mb-3 flex items-center">
            🔍 Filtreleme Seçenekleri
          </h3>
          <div className="space-y-3">
            {/* Üst Sıra - Arama ve Kaynak */}
            <div className="flex flex-col sm:flex-row gap-3">
              <div className="flex-1">
                <label className="block text-xs font-medium mb-1 text-gray-700">Arama</label>
                <input
                  type="text"
                  placeholder="İhale başlığında ara..."
                  value={filters.query}
                  onChange={(e) => setFilters({...filters, query: e.target.value})}
                  className="w-full px-3 py-2 text-sm border border-gray-200 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-transparent bg-white/80 backdrop-blur-sm shadow-sm"
                />
              </div>
              
              <div className="sm:w-40">
                <label className="block text-xs font-medium mb-1 text-gray-700">Kaynak</label>
                <select
                  value={filters.source_slug}
                  onChange={(e) => setFilters({...filters, source_slug: e.target.value})}
                  className="w-full px-3 py-2 text-sm border border-gray-200 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-transparent bg-white/80 backdrop-blur-sm shadow-sm"
                >
                  <option value="">Tüm Kaynaklar</option>
                  {sources.map(source => (
                    <option key={source.slug} value={source.slug}>{source.name}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Alt Sıra - Kategori, Tarih ve Ara Butonu */}
            <div className="flex flex-col sm:flex-row gap-3">
              <div className="sm:w-48">
                <label className="block text-xs font-medium mb-1 text-gray-700">Kategori</label>
                <select
                  value={filters.category}
                  onChange={(e) => setFilters({...filters, category: e.target.value})}
                  className="w-full px-3 py-2 text-sm border border-gray-200 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-transparent bg-white/80 backdrop-blur-sm shadow-sm"
                >
                  <option value="">Tüm Kategoriler</option>
                  {getAllCategories().map(([key, name]) => (
                    <option key={key} value={key}>{name}</option>
                  ))}
                </select>
              </div>
              
              <div className="flex-1">
                <label className="block text-xs font-medium mb-1 text-gray-700">Tarih Aralığı</label>
                <div className="flex gap-2">
                  <input
                    type="date"
                    value={filters.date_from}
                    onChange={(e) => setFilters({...filters, date_from: e.target.value})}
                    className="flex-1 px-2 py-2 text-sm border border-gray-200 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-transparent bg-white/80 backdrop-blur-sm shadow-sm"
                  />
                  <input
                    type="date"
                    value={filters.date_to}
                    onChange={(e) => setFilters({...filters, date_to: e.target.value})}
                    className="flex-1 px-2 py-2 text-sm border border-gray-200 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-transparent bg-white/80 backdrop-blur-sm shadow-sm"
                  />
                </div>
              </div>
              
              <div className="sm:w-28 flex items-end">
                <button
                  onClick={searchTenders}
                  className="w-full bg-gradient-to-r from-blue-600 to-blue-700 text-white px-4 py-2 text-sm rounded-md hover:from-blue-700 hover:to-blue-800 focus:outline-none focus:ring-1 focus:ring-blue-500 shadow transform hover:scale-105 transition-all duration-200 font-medium min-h-[38px] flex items-center justify-center"
                >
                  🔍 Ara
                </button>
              </div>
            </div>
          </div>
        </div>
        
        {/* Actions */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
          <button
            onClick={exportCSV}
            className="bg-gradient-to-r from-green-600 to-green-700 text-white px-3 py-2 text-sm rounded-md hover:from-green-700 hover:to-green-800 focus:outline-none focus:ring-1 focus:ring-green-500 shadow transform hover:scale-105 transition-all duration-200 font-medium flex items-center justify-center"
          >
            📊 CSV İndir
          </button>
          <button
            onClick={() => setShowEmailForm(!showEmailForm)}
            className="bg-gradient-to-r from-purple-600 to-purple-700 text-white px-3 py-2 text-sm rounded-md hover:from-purple-700 hover:to-purple-800 focus:outline-none focus:ring-1 focus:ring-purple-500 shadow transform hover:scale-105 transition-all duration-200 font-medium flex items-center justify-center"
          >
            📧 Email Gönder
          </button>
          <a
            href="/mail"
            className="bg-gradient-to-r from-pink-600 to-pink-700 text-white px-3 py-2 text-sm rounded-md hover:from-pink-700 hover:to-pink-800 focus:outline-none focus:ring-1 focus:ring-pink-500 shadow transform hover:scale-105 transition-all duration-200 font-medium flex items-center justify-center"
          >
            🤖 Mail Otomasyonu
          </a>
          <button
            onClick={triggerScrape}
            className="bg-gradient-to-r from-orange-600 to-orange-700 text-white px-3 py-2 text-sm rounded-md hover:from-orange-700 hover:to-orange-800 focus:outline-none focus:ring-1 focus:ring-orange-500 shadow transform hover:scale-105 transition-all duration-200 font-medium flex items-center justify-center"
          >
            🔄 Şimdi Tara
          </button>
        </div>
        
        {/* Email Form */}
        {showEmailForm && (
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-4 rounded-lg mb-4 border border-blue-200 shadow">
            <h3 className="text-sm font-semibold text-gray-800 mb-3">📧 Email Gönderimi</h3>
            <div className="flex flex-wrap gap-2 items-center">
              <input
                type="email"
                placeholder="Email adresi"
                value={emailAddress}
                onChange={(e) => setEmailAddress(e.target.value)}
                className="flex-1 min-w-48 px-3 py-2 text-sm border border-gray-200 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-transparent bg-white shadow-sm"
              />
              <button
                onClick={sendEmail}
                className="bg-gradient-to-r from-green-600 to-green-700 text-white px-4 py-2 text-sm rounded-md hover:from-green-700 hover:to-green-800 font-medium shadow"
              >
                ✉️ Gönder
              </button>
              <button
                onClick={() => setShowEmailForm(false)}
                className="bg-gradient-to-r from-gray-500 to-gray-600 text-white px-4 py-2 text-sm rounded-md hover:from-gray-600 hover:to-gray-700 font-medium shadow"
              >
                ❌ İptal
              </button>
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="mb-4">
          <div className="bg-white/70 backdrop-blur-sm rounded-lg shadow border border-white/50 overflow-hidden">
            <nav className="flex space-x-0 overflow-x-auto">
              <button
                onClick={() => filterBySource('ALL')}
                className={`py-2 px-4 font-medium text-xs whitespace-nowrap transition-all duration-300 ${
                  activeTab === 'ALL'
                    ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow'
                    : 'text-gray-600 hover:text-blue-600 hover:bg-blue-50'
                }`}
              >
                📋 Tüm İhaleler ({totalTenders})
              </button>
              {sourceStats.map((stat, index) => (
                <button
                  key={stat.slug}
                  onClick={() => filterBySource(stat.slug)}
                  className={`py-2 px-4 font-medium text-xs whitespace-nowrap transition-all duration-300 ${
                    activeTab === stat.slug
                      ? `bg-gradient-to-r ${getSourceColor(index)} text-white shadow`
                      : 'text-gray-600 hover:text-blue-600 hover:bg-blue-50'
                  }`}
                >
                  {stat.name} ({stat.count})
                </button>
              ))}
            </nav>
          </div>
        </div>
        
        {/* Loading */}
        {loading && (
          <div className="text-center py-8">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-2 border-blue-500 border-t-transparent shadow"></div>
            <p className="mt-2 text-gray-600 text-sm">Yükleniyor...</p>
          </div>
        )}
        
        {/* Tender List */}
        <div className="space-y-3">
          {tenders.map((tender, index) => (
            <div 
              key={tender.id} 
              className="bg-white/80 backdrop-blur-sm p-4 rounded-lg shadow border border-white/50 hover:shadow-lg transition-all duration-300 hover:bg-white/90"
            >
              <div className="flex items-start justify-between mb-3">
                <h3 className="text-sm font-semibold text-gray-900 flex-1 pr-3 leading-snug">
                  {tender.title}
                </h3>
                <div className="flex gap-2">
                  <div className="px-2 py-1 rounded-full text-xs font-medium text-white bg-gradient-to-r from-indigo-500 to-indigo-600 shadow-sm">
                    {getCategoryName(classifyTender(tender.title, tender.description))}
                  </div>
                  <div className={`px-2 py-1 rounded-full text-xs font-medium text-white bg-gradient-to-r ${getSourceColor(sourceStats.findIndex(s => s.slug === tender.source?.slug))} shadow-sm flex-shrink-0`}>
                    {tender.source?.name || 'Bilinmiyor'}
                  </div>
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-2 text-xs text-gray-600 mb-3">
                <div className="flex items-center">
                  <span className="text-blue-500 mr-1">🏢</span>
                  <strong className="mr-1">Kaynak:</strong> {tender.source?.name || 'Bilinmiyor'}
                </div>
                <div className="flex items-center">
                  <span className="text-green-500 mr-1">📅</span>
                  <strong className="mr-1">Yayın:</strong> {formatDate(tender.published_at)}
                </div>
                <div className="flex items-center">
                  <span className="text-purple-500 mr-1">⏰</span>
                  <strong className="mr-1">Eklenme:</strong> {formatDate(tender.created_at)}
                </div>
              </div>
              
              {tender.description && (
                <div className="bg-gray-50/80 rounded-md p-3 mb-3 text-gray-700 text-sm leading-relaxed">
                  {tender.description.substring(0, 200)}
                  {tender.description.length > 200 && '...'}
                </div>
              )}
              
              <div className="flex justify-between items-center">
                <a
                  href={tender.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center bg-gradient-to-r from-blue-600 to-blue-700 text-white px-4 py-2 text-sm rounded-md hover:from-blue-700 hover:to-blue-800 font-medium shadow transform hover:scale-105 transition-all duration-200"
                >
                  📄 İhale Detayları →
                </a>
                <div className="text-xs text-gray-400">
                  #{index + 1}
                </div>
              </div>
            </div>
          ))}
        </div>
        
        {tenders.length === 0 && !loading && (
          <div className="text-center py-12">
            <div className="bg-white/80 backdrop-blur-sm rounded-lg p-8 shadow border border-white/50 max-w-sm mx-auto">
              <div className="text-4xl mb-3">🔍</div>
              <p className="text-sm font-semibold text-gray-800 mb-1">Henüz ihale bulunamadı.</p>
              <p className="text-xs text-gray-600">Filtreleri değiştirerek tekrar deneyin.</p>
            </div>
          </div>
        )}
        
        {/* Footer */}
        <div className="text-center mt-12 py-6 text-gray-500 text-xs">
          <div className="bg-white/50 backdrop-blur-sm rounded-md p-3 inline-block shadow-sm">
            <p>🏛️ Türkiye Kamu İhaleleri Takip Sistemi</p>
            <p className="mt-1">Güncel veriler ve otomatik takip ile ihale fırsatlarını kaçırmayın</p>
          </div>
        </div>
      </div>
    </div>
  )
}