'use client'

import { useState, useEffect } from 'react'
import axios from 'axios'
import { format } from 'date-fns'

interface Source {
  id: number
  name: string
  url: string
  slug: string
}

interface Category {
  key: string
  name: string
}

interface MailSchedule {
  id: string
  sender_email: string
  recipient_emails: string[]
  subject: string
  schedule_type: string
  scheduled_time?: string
  scheduled_date?: string
  filters: any
  is_active: boolean
  created_at: string
  last_sent?: string
  next_run?: string
  times?: string[]
}

interface ManualMailForm {
  sender_email: string
  recipient_emails: string
  subject: string
  filters: {
    query: string
    source_slug: string
    date_from: string
    date_to: string
    limit: number
    category: string
  }
}

interface ScheduleForm {
  sender_email: string
  recipient_emails: string
  subject: string
  schedule_type: 'daily'
  times: string[]
  filters: {
    query: string
    source_slug: string
    date_from: string
    date_to: string
    limit: number
    category: string
  }
  is_active: boolean
}

export default function MailAutomationPage() {
  const [sources, setSources] = useState<Source[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [schedules, setSchedules] = useState<MailSchedule[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [activeTab, setActiveTab] = useState<'manual' | 'schedule' | 'list'>('manual')
  const [newTime, setNewTime] = useState('')

  const [manualForm, setManualForm] = useState<ManualMailForm>({
    sender_email: '',
    recipient_emails: '',
    subject: 'Günlük İhale Raporu',
    filters: {
      query: '',
      source_slug: '',
      date_from: '',
      date_to: '',
      limit: 50,
      category: ''
    }
  })

  const [scheduleForm, setScheduleForm] = useState<ScheduleForm>({
    sender_email: '',
    recipient_emails: '',
    subject: 'Otomatik İhale Raporu',
    schedule_type: 'daily',
    times: [],
    filters: {
      query: '',
      source_slug: '',
      date_from: '',
      date_to: '',
      limit: 50,
      category: ''
    },
    is_active: true
  })

  useEffect(() => {
    loadSources()
    loadCategories()
    loadSchedules()
  }, [])

  const loadSources = async () => {
    try {
      const response = await axios.get('/api/tenders/sources')
      setSources(response.data)
    } catch (err) {
      console.error('Error loading sources:', err)
    }
  }

  const loadCategories = async () => {
    try {
      const response = await axios.get('/api/tenders/categories')
      setCategories(response.data)
    } catch (err) {
      console.error('Error loading categories:', err)
    }
  }

  const loadSchedules = async () => {
    try {
      const response = await axios.get('/api/mail/schedules')
      setSchedules(response.data)
    } catch (err) {
      console.error('Error loading schedules:', err)
    }
  }

  const sendManualMail = async () => {
    if (!manualForm.sender_email || !manualForm.recipient_emails) {
      setError('Gönderen ve alıcı email adresleri gereklidir')
      return
    }

    setLoading(true)
    setError('')
    setSuccess('')

    try {
      const response = await axios.post('/api/mail/send-manual', {
        ...manualForm,
        recipient_emails: manualForm.recipient_emails.split(',').map((email: string) => email.trim())
      })

      setSuccess(`${response.data.message} - ${response.data.tender_count} ihale gönderildi`)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Mail gönderimi hatası')
    } finally {
      setLoading(false)
    }
  }

  const testMailSettings = async () => {
    if (!manualForm.sender_email) {
      setError('Gönderen email adresi gereklidir')
      return
    }

    setLoading(true)
    try {
      const params = new URLSearchParams({
        sender_email: manualForm.sender_email,
        recipient_email: manualForm.sender_email
      })
      await axios.post(`/api/mail/test?${params.toString()}`)
      setSuccess('Test maili gönderildi, gelen kutunuzu kontrol edin')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Test maili hatası')
    } finally {
      setLoading(false)
    }
  }

  const createSchedule = async () => {
    if (!scheduleForm.sender_email || !scheduleForm.recipient_emails) {
      setError('Gönderen ve alıcı email adresleri gereklidir')
      return
    }

    if (scheduleForm.times.length === 0) {
      setError('En az bir gönderim saati belirtmelisiniz')
      return
    }

    setLoading(true)
    setError('')
    setSuccess('')

    try {
      await axios.post('/api/mail/schedule', {
        ...scheduleForm,
        recipient_emails: scheduleForm.recipient_emails.split(',').map((email: string) => email.trim())
      })

      setSuccess('Mail otomasyonu başarıyla oluşturuldu')
      loadSchedules()
      
      setScheduleForm({
        ...scheduleForm,
        sender_email: '',
        recipient_emails: '',
        subject: 'Otomatik İhale Raporu',
        times: []
      })
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Otomasyon oluşturma hatası')
    } finally {
      setLoading(false)
    }
  }

  const toggleSchedule = async (scheduleId: string) => {
    try {
      await axios.put(`/api/mail/schedules/${scheduleId}/toggle`)
      loadSchedules()
      setSuccess('Mail otomasyonu durumu güncellendi')
    } catch (err) {
      setError('Durum güncelleme hatası')
    }
  }

  const deleteSchedule = async (scheduleId: string) => {
    if (!confirm('Bu mail otomasyonunu silmek istediğinizden emin misiniz?')) {
      return
    }

    try {
      await axios.delete(`/api/mail/schedules/${scheduleId}`)
      loadSchedules()
      setSuccess('Mail otomasyonu silindi')
    } catch (err) {
      setError('Silme hatası')
    }
  }

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Yok'
    try {
      return format(new Date(dateString), 'dd.MM.yyyy HH:mm')
    } catch {
      return dateString
    }
  }

  const getScheduleTypeText = (type: string) => {
    switch (type) {
      case 'once': return 'Bir kez'
      case 'daily': return 'Günlük'
      case 'weekly': return 'Haftalık'
      default: return type
    }
  }

  const inputClasses = {
    base: "w-full px-3 py-2 text-sm border border-gray-300 rounded-md " +
          "focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500 " +
          "bg-white text-gray-900 placeholder:text-gray-500 shadow-sm " +
          "disabled:bg-gray-100 disabled:text-gray-500",
    small: "w-full px-2 py-1.5 text-xs border border-gray-300 rounded-md " +
           "focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500 " +
           "bg-white text-gray-900 placeholder:text-gray-500 shadow-sm " +
           "disabled:bg-gray-100 disabled:text-gray-500"
  }

  const cardClasses = "bg-white border border-gray-200 rounded-lg shadow-sm"
  const sectionClasses = "bg-gray-50 border border-gray-200 rounded-lg p-4"

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      <div className="container mx-auto px-3 py-4 max-w-6xl">
        {/* Header */}
        <div className="text-center mb-6">
          <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-600 via-pink-600 to-red-600 bg-clip-text text-transparent mb-2">
            📧 Mail Otomasyonu
          </h1>
          <p className="text-gray-700 text-sm">İhale raporlarını otomatik olarak mail ile gönderin</p>
        </div>

        {/* Error/Success Messages */}
        {error && (
          <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded-md text-sm">
            ❌ {error}
          </div>
        )}
        {success && (
          <div className="mb-4 p-3 bg-green-100 border border-green-400 text-green-700 rounded-md text-sm">
            ✅ {success}
          </div>
        )}

        {/* Tabs */}
        <div className="mb-4">
          <div className={`${cardClasses} overflow-hidden`}>
            <nav className="flex space-x-0 overflow-x-auto">
              <button
                onClick={() => setActiveTab('manual')}
                className={`py-2 px-4 font-medium text-sm whitespace-nowrap transition-all duration-300 ${
                  activeTab === 'manual'
                    ? 'bg-gradient-to-r from-purple-600 to-purple-700 text-white shadow'
                    : 'text-gray-700 hover:text-purple-600 hover:bg-purple-50'
                }`}
              >
                📧 Manuel Mail Gönder
              </button>
              <button
                onClick={() => setActiveTab('schedule')}
                className={`py-2 px-4 font-medium text-sm whitespace-nowrap transition-all duration-300 ${
                  activeTab === 'schedule'
                    ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow'
                    : 'text-gray-700 hover:text-blue-600 hover:bg-blue-50'
                }`}
              >
                ⏰ Otomasyon Oluştur
              </button>
              <button
                onClick={() => setActiveTab('list')}
                className={`py-2 px-4 font-medium text-sm whitespace-nowrap transition-all duration-300 ${
                  activeTab === 'list'
                    ? 'bg-gradient-to-r from-green-600 to-green-700 text-white shadow'
                    : 'text-gray-700 hover:text-green-600 hover:bg-green-50'
                }`}
              >
                📋 Aktif Otomasyonlar ({schedules.length})
              </button>
            </nav>
          </div>
        </div>

        {/* Manuel Mail Tab */}
        {activeTab === 'manual' && (
          <div className={`${cardClasses} p-6`}>
            <h3 className="text-lg font-semibold text-gray-800 mb-6 flex items-center">
              📧 Manuel Mail Gönderimi
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
              <div>
                <label className="block text-sm font-medium mb-2 text-gray-700">Gönderen Email *</label>
                <input
                  type="email"
                  placeholder="gonderen@example.com"
                  value={manualForm.sender_email}
                  onChange={(e) => setManualForm({...manualForm, sender_email: e.target.value})}
                  className={inputClasses.base}
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2 text-gray-700">Alıcı Email(ler) *</label>
                <input
                  type="text"
                  placeholder="alici1@example.com, alici2@example.com"
                  value={manualForm.recipient_emails}
                  onChange={(e) => setManualForm({...manualForm, recipient_emails: e.target.value})}
                  className={inputClasses.base}
                  required
                />
                <p className="mt-1 text-xs text-gray-500">Birden fazla email için virgülle ayırın</p>
              </div>
            </div>

            <div className="mb-6">
              <label className="block text-sm font-medium mb-2 text-gray-700">Mail Konusu</label>
              <input
                type="text"
                placeholder="Günlük İhale Raporu"
                value={manualForm.subject}
                onChange={(e) => setManualForm({...manualForm, subject: e.target.value})}
                className={inputClasses.base}
              />
            </div>

            {/* Filtreler */}
            <div className={`${sectionClasses} mb-6`}>
              <h4 className="text-md font-semibold text-gray-800 mb-4 flex items-center">🔍 İhale Filtreleri ve Kategorizasyon</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2 text-gray-700">Arama Terimi</label>
                  <input
                    type="text"
                    placeholder="İhale başlığında ara..."
                    value={manualForm.filters.query}
                    onChange={(e) => setManualForm({...manualForm, filters: {...manualForm.filters, query: e.target.value}})}
                    className={inputClasses.small}
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-2 text-gray-700">Kaynak Seçimi</label>
                  <select
                    value={manualForm.filters.source_slug}
                    onChange={(e) => setManualForm({...manualForm, filters: {...manualForm.filters, source_slug: e.target.value}})}
                    className={inputClasses.small}
                  >
                    <option value="">🌐 Tüm Kaynaklar</option>
                    {sources.map(source => (
                      <option key={source.slug} value={source.slug}>{source.name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2 text-gray-700">İhale Kategorisi</label>
                  <select
                    value={manualForm.filters.category}
                    onChange={(e) => setManualForm({...manualForm, filters: {...manualForm.filters, category: e.target.value}})}
                    className={inputClasses.small}
                  >
                    <option value="">📋 Tüm Kategoriler</option>
                    {categories.map((category) => (
                      <option key={category.key} value={category.key}>
                        {category.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2 text-gray-700">Başlangıç Tarihi</label>
                  <input
                    type="date"
                    value={manualForm.filters.date_from}
                    onChange={(e) => setManualForm({...manualForm, filters: {...manualForm.filters, date_from: e.target.value}})}
                    className={inputClasses.small}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2 text-gray-700">Bitiş Tarihi</label>
                  <input
                    type="date"
                    value={manualForm.filters.date_to}
                    onChange={(e) => setManualForm({...manualForm, filters: {...manualForm.filters, date_to: e.target.value}})}
                    className={inputClasses.small}
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-2 text-gray-700">İhale Sayısı Limiti</label>
                  <select
                    value={manualForm.filters.limit}
                    onChange={(e) => setManualForm({...manualForm, filters: {...manualForm.filters, limit: parseInt(e.target.value)}})}
                    className={inputClasses.small}
                  >
                    <option value={25}>25 İhale</option>
                    <option value={50}>50 İhale</option>
                    <option value={100}>100 İhale</option>
                    <option value={200}>200 İhale</option>
                  </select>
                </div>
              </div>
              
              <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <h5 className="text-sm font-medium text-blue-800 mb-2">📊 Otomatik Kategorizasyon</h5>
                <p className="text-xs text-blue-700">
                  Sistem, ihale başlıkları ve açıklamalarını analiz ederek otomatik olarak kategorize edecektir. 
                  Manuel kategori seçimi yaparsanız, sadece o kategorideki ihaleler filtrelenecektir.
                </p>
              </div>
            </div>

            <div className="flex gap-3">
              <button
                onClick={sendManualMail}
                disabled={loading}
                className="bg-gradient-to-r from-purple-600 to-purple-700 text-white px-6 py-3 text-sm rounded-lg hover:from-purple-700 hover:to-purple-800 focus:outline-none focus:ring-2 focus:ring-purple-500 shadow-lg transform hover:scale-105 transition-all duration-200 font-medium disabled:opacity-50 flex items-center gap-2"
              >
                {loading ? '📤 Gönderiliyor...' : '📧 Mail Gönder'}
              </button>
              
              <button
                onClick={testMailSettings}
                disabled={loading}
                className="bg-gradient-to-r from-gray-500 to-gray-600 text-white px-6 py-3 text-sm rounded-lg hover:from-gray-600 hover:to-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 shadow-lg transform hover:scale-105 transition-all duration-200 font-medium disabled:opacity-50 flex items-center gap-2"
              >
                🧪 Test Mail
              </button>
            </div>
          </div>
        )}

        {/* Schedule Tab - Otomasyon Oluştur */}
        {activeTab === 'schedule' && (
          <div className={`${cardClasses} p-6`}>
            <h3 className="text-lg font-semibold text-gray-800 mb-6 flex items-center">
              ⏰ Otomatik Mail Planlama
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
              <div>
                <label className="block text-sm font-medium mb-2 text-gray-700">Gönderen Email *</label>
                <input
                  type="email"
                  placeholder="gonderen@example.com"
                  value={scheduleForm.sender_email}
                  onChange={(e) => setScheduleForm({...scheduleForm, sender_email: e.target.value})}
                  className={inputClasses.base}
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2 text-gray-700">Alıcı Email(ler) *</label>
                <input
                  type="text"
                  placeholder="alici1@example.com, alici2@example.com"
                  value={scheduleForm.recipient_emails}
                  onChange={(e) => setScheduleForm({...scheduleForm, recipient_emails: e.target.value})}
                  className={inputClasses.base}
                  required
                />
              </div>
            </div>

            <div className="mb-6">
              <label className="block text-sm font-medium mb-2 text-gray-700">Mail Konusu</label>
              <input
                type="text"
                placeholder="Otomatik İhale Raporu"
                value={scheduleForm.subject}
                onChange={(e) => setScheduleForm({...scheduleForm, subject: e.target.value})}
                className={inputClasses.base}
              />
            </div>

            {/* Zamanlama Ayarları */}
            <div className={`${sectionClasses} mb-6`}>
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-md font-semibold text-gray-800">⏰ Zamanlama ve Tekrar Ayarları</h4>
                <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                  scheduleForm.is_active 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-gray-100 text-gray-800'
                }`}>
                  {scheduleForm.is_active ? '✅ Aktif' : '⏸️ Pasif'}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium mb-2 text-gray-700">Tekrar Türü</label>
                  <select
                    value={scheduleForm.schedule_type}
                    className={`${inputClasses.small} bg-gray-100`}
                    disabled
                  >
                    <option value="daily">🔄 Her gün</option>
                  </select>
                  <p className="mt-1 text-xs text-gray-500">Şu anda sadece günlük tekrar destekleniyor</p>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2 text-gray-700">Otomasyon Durumu</label>
                  <button
                    onClick={() => setScheduleForm({...scheduleForm, is_active: !scheduleForm.is_active})}
                    className={`w-full px-4 py-2 text-sm rounded-lg transition-all duration-200 font-medium ${
                      scheduleForm.is_active
                        ? 'bg-green-500 text-white hover:bg-green-600 shadow-lg'
                        : 'bg-gray-300 text-gray-700 hover:bg-gray-400'
                    }`}
                  >
                    {scheduleForm.is_active ? '✅ Aktif - Otomatik çalışacak' : '⏸️ Pasif - Çalışmayacak'}
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2 text-gray-700">Günlük Gönderim Saatleri</label>
                <div className="flex flex-wrap gap-2 mb-3">
                  {scheduleForm.times.map((time, index) => (
                    <div key={index} className="flex items-center bg-white px-3 py-2 rounded-lg border-2 border-blue-200 shadow-sm">
                      <span className="text-sm font-medium mr-2">🕐 {time}</span>
                      <button
                        onClick={() => {
                          const newTimes = scheduleForm.times.filter((_, i) => i !== index);
                          setScheduleForm({...scheduleForm, times: newTimes});
                        }}
                        className="text-red-500 hover:text-red-600 text-sm font-bold hover:bg-red-50 px-1 rounded"
                      >
                        ✕
                      </button>
                    </div>
                  ))}
                  {scheduleForm.times.length === 0 && (
                    <div className="text-sm text-gray-500 py-2">Henüz saat eklenmemiş</div>
                  )}
                </div>
                
                <div className="flex items-center gap-3">
                  <input
                    type="time"
                    value={newTime}
                    onChange={(e) => setNewTime(e.target.value)}
                    className={`${inputClasses.small} !w-36`}
                  />
                  <button
                    onClick={() => {
                      if (!newTime) {
                        setError('Lütfen bir saat seçin!');
                        return;
                      }
                      if (scheduleForm.times.includes(newTime)) {
                        setError('Bu saat zaten eklenmiş!');
                        return;
                      }
                      const newTimes = [...scheduleForm.times, newTime].sort();
                      setScheduleForm({...scheduleForm, times: newTimes});
                      setNewTime('');
                      setError('');
                      setSuccess(`Saat ${newTime} başarıyla eklendi!`);
                    }}
                    className="bg-green-500 text-white px-4 py-2 rounded-lg hover:bg-green-600 text-sm font-medium transition-colors flex items-center gap-1"
                  >
                    ➕ Saat Ekle
                  </button>
                </div>
                <p className="mt-2 text-xs text-gray-500">
                  💡 Her gün bu saatlerde otomatik mail gönderilecek. Birden fazla saat ekleyebilirsiniz.
                </p>
              </div>
            </div>

            {/* İhale Filtreleri */}
            <div className={`${sectionClasses} mb-6`}>
              <h4 className="text-md font-semibold text-gray-800 mb-4 flex items-center">🔍 İhale Filtreleri ve Kategorizasyon</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2 text-gray-700">Arama Terimi</label>
                  <input
                    type="text"
                    placeholder="İhale başlığında ara..."
                    value={scheduleForm.filters.query}
                    onChange={(e) => setScheduleForm({...scheduleForm, filters: {...scheduleForm.filters, query: e.target.value}})}
                    className={inputClasses.small}
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-2 text-gray-700">Kaynak Seçimi</label>
                  <select
                    value={scheduleForm.filters.source_slug}
                    onChange={(e) => setScheduleForm({...scheduleForm, filters: {...scheduleForm.filters, source_slug: e.target.value}})}
                    className={inputClasses.small}
                  >
                    <option value="">🌐 Tüm Kaynaklar</option>
                    {sources.map(source => (
                      <option key={source.slug} value={source.slug}>{source.name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2 text-gray-700">İhale Kategorisi</label>
                  <select
                    value={scheduleForm.filters.category}
                    onChange={(e) => setScheduleForm({...scheduleForm, filters: {...scheduleForm.filters, category: e.target.value}})}
                    className={inputClasses.small}
                  >
                    <option value="">📋 Tüm Kategoriler</option>
                    {categories.map((category) => (
                      <option key={category.key} value={category.key}>
                        {category.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2 text-gray-700">Başlangıç Tarihi</label>
                  <input
                    type="date"
                    value={scheduleForm.filters.date_from}
                    onChange={(e) => setScheduleForm({...scheduleForm, filters: {...scheduleForm.filters, date_from: e.target.value}})}
                    className={inputClasses.small}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2 text-gray-700">Bitiş Tarihi</label>
                  <input
                    type="date"
                    value={scheduleForm.filters.date_to}
                    onChange={(e) => setScheduleForm({...scheduleForm, filters: {...scheduleForm.filters, date_to: e.target.value}})}
                    className={inputClasses.small}
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-2 text-gray-700">İhale Sayısı Limiti</label>
                  <select
                    value={scheduleForm.filters.limit}
                    onChange={(e) => setScheduleForm({...scheduleForm, filters: {...scheduleForm.filters, limit: parseInt(e.target.value)}})}
                    className={inputClasses.small}
                  >
                    <option value={25}>25 İhale</option>
                    <option value={50}>50 İhale</option>
                    <option value={100}>100 İhale</option>
                    <option value={200}>200 İhale</option>
                  </select>
                </div>
              </div>
              
              <div className="mt-4 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg">
                <h5 className="text-sm font-medium text-blue-800 mb-2 flex items-center">
                  🤖 Akıllı Kategorizasyon Sistemi
                </h5>
                <p className="text-xs text-blue-700 leading-relaxed">
                  Sistem, scraper ile alınan ihale verilerini başlık ve açıklama analizi yaparak otomatik olarak kategorize edecektir. 
                  AI destekli kategorizasyon ile ihaleler doğru kategorilere yerleştirilecek ve size sadece ilgilendiğiniz kategorideki 
                  ihaleler gönderilecektir.
                </p>
              </div>
            </div>

            <button
              onClick={createSchedule}
              disabled={loading || scheduleForm.times.length === 0}
              className="bg-gradient-to-r from-blue-600 to-blue-700 text-white px-6 py-3 text-sm rounded-lg hover:from-blue-700 hover:to-blue-800 focus:outline-none focus:ring-2 focus:ring-blue-500 shadow-lg transform hover:scale-105 transition-all duration-200 font-medium disabled:opacity-50 flex items-center gap-2"
            >
              {loading ? '⏰ Oluşturuluyor...' : '⏰ Otomasyon Oluştur'}
            </button>
            
            {scheduleForm.times.length === 0 && (
              <p className="mt-2 text-xs text-red-600">En az bir gönderim saati eklemelisiniz!</p>
            )}
          </div>
        )}

        {/* Schedule List Tab - Aktif Otomasyonlar */}
        {activeTab === 'list' && (
          <div className="space-y-4">
            {schedules.length === 0 ? (
              <div className="text-center py-16">
                <div className={`${cardClasses} p-12 max-w-md mx-auto`}>
                  <div className="text-6xl mb-4">📧</div>
                  <h3 className="text-lg font-semibold text-gray-800 mb-2">Henüz otomasyon bulunamadı</h3>
                  <p className="text-sm text-gray-600 mb-4">
                    Otomatik mail gönderimleri için yeni bir otomasyon oluşturun.
                  </p>
                  <button
                    onClick={() => setActiveTab('schedule')}
                    className="bg-gradient-to-r from-blue-600 to-blue-700 text-white px-4 py-2 text-sm rounded-lg hover:from-blue-700 hover:to-blue-800 transition-all duration-200"
                  >
                    ⏰ Otomasyon Oluştur
                  </button>
                </div>
              </div>
            ) : (
              schedules.map((schedule) => (
                <div key={schedule.id} className={`${cardClasses} p-6`}>
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-semibold text-gray-900">{schedule.subject}</h3>
                        <div className={`px-3 py-1 rounded-full text-xs font-medium ${
                          schedule.is_active 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {schedule.is_active ? '✅ Aktif' : '⏸️ Pasif'}
                        </div>
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 text-sm text-gray-600 mb-4">
                        <div className="flex items-center gap-2">
                          <span>📧</span>
                          <span><strong>Gönderen:</strong> {schedule.sender_email}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span>👥</span>
                          <span><strong>Alıcılar:</strong> {schedule.recipient_emails.length} kişi</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span>🔄</span>
                          <span><strong>Tekrar:</strong> {getScheduleTypeText(schedule.schedule_type)}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span>⏰</span>
                          <span><strong>Saatler:</strong> {schedule.times?.join(', ') || 'Belirtilmemiş'}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span>📅</span>
                          <span><strong>Son Gönderim:</strong> {formatDate(schedule.last_sent)}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span>🎯</span>
                          <span><strong>Sonraki:</strong> {formatDate(schedule.next_run)}</span>
                        </div>
                      </div>
                      
                      {/* Alıcı Listesi */}
                      <div className={`${sectionClasses} p-3`}>
                        <p className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-1">
                          📧 Alıcı Email Adresleri
                        </p>
                        <div className="flex flex-wrap gap-2">
                          {schedule.recipient_emails.map((email, index) => (
                            <span key={index} className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs">
                              {email}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2 ml-6">
                      <button
                        onClick={() => toggleSchedule(schedule.id)}
                        className={`text-sm px-4 py-2 rounded-lg transition-colors font-medium ${
                          schedule.is_active 
                            ? 'bg-orange-500 text-white hover:bg-orange-600' 
                            : 'bg-green-500 text-white hover:bg-green-600'
                        }`}
                      >
                        {schedule.is_active ? '⏸️ Durdur' : '▶️ Başlat'}
                      </button>
                      <button
                        onClick={() => deleteSchedule(schedule.id)}
                        className="text-sm px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors font-medium"
                      >
                        🗑️ Sil
                      </button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* Footer */}
        <div className="text-center mt-12 py-8 text-gray-500 text-sm">
          <div className={`${cardClasses} p-4 inline-block`}>
            <p className="font-semibold">📧 Mail Otomasyonu Sistemi</p>
            <p className="mt-2">İhale raporlarınızı otomatik olarak planlayın ve gönderin</p>
            <p className="mt-1 text-xs">🤖 AI destekli kategorizasyon ile akıllı filtreleme</p>
          </div>
        </div>
      </div>
    </div>
  )
}
