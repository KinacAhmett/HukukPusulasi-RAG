// src/components/AccessibilityPanel.jsx
import React, { useState, useEffect } from 'react';

function AccessibilityPanel() {
  const [isOpen, setIsOpen] = useState(false);
  const [settings, setSettings] = useState({
    fontSize: 'normal',
    highContrast: false,
    screenReader: false,
    keyboardNav: true,
    voiceInput: false,
    autoRead: false,
    reducedMotion: false,
    focusIndicator: true
  });

  // LocalStorage'dan ayarları yükle
  useEffect(() => {
    const savedSettings = localStorage.getItem('accessibilitySettings');
    if (savedSettings) {
      setSettings(JSON.parse(savedSettings));
    }
  }, []);

  // Ayarları kaydet ve uygula
  useEffect(() => {
    localStorage.setItem('accessibilitySettings', JSON.stringify(settings));
    applyAccessibilitySettings(settings);
  }, [settings]);

  const applyAccessibilitySettings = (settings) => {
    const root = document.documentElement;
    
    // Font boyutu
    if (settings.fontSize === 'large') {
      root.style.fontSize = '18px';
    } else if (settings.fontSize === 'xlarge') {
      root.style.fontSize = '22px';
    } else {
      root.style.fontSize = '16px';
    }

    // Yüksek kontrast
    if (settings.highContrast) {
      document.body.classList.add('high-contrast');
    } else {
      document.body.classList.remove('high-contrast');
    }

    // Azaltılmış hareket
    if (settings.reducedMotion) {
      document.body.classList.add('reduced-motion');
    } else {
      document.body.classList.remove('reduced-motion');
    }

    // Focus göstergesi
    if (settings.focusIndicator) {
      document.body.classList.add('enhanced-focus');
    } else {
      document.body.classList.remove('enhanced-focus');
    }
  };

  const handleSettingChange = (key, value) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }));

    // Ses bildirimi (screen reader için)
    if (settings.screenReader) {
      announceChange(key, value);
    }
  };

  const announceChange = (setting, value) => {
    const message = `${setting} ${value ? 'açıldı' : 'kapatıldı'}`;
    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', 'polite');
    announcement.setAttribute('aria-atomic', 'true');
    announcement.className = 'sr-only';
    announcement.textContent = message;
    document.body.appendChild(announcement);
    
    setTimeout(() => {
      document.body.removeChild(announcement);
    }, 1000);
  };

  const resetSettings = () => {
    const defaultSettings = {
      fontSize: 'normal',
      highContrast: false,
      screenReader: false,
      keyboardNav: true,
      voiceInput: false,
      autoRead: false,
      reducedMotion: false,
      focusIndicator: true
    };
    setSettings(defaultSettings);
    
    if (settings.screenReader) {
      announceChange('Erişilebilirlik ayarları', 'sıfırlandı');
    }
  };

  return (
    <>
      {/* Erişilebilirlik Butonu */}
      <button
        className="accessibility-toggle"
        onClick={() => setIsOpen(!isOpen)}
        aria-label="Erişilebilirlik ayarlarını aç"
        aria-expanded={isOpen}
        title="Erişilebilirlik Ayarları (Alt+A)"
      >
        <span className="accessibility-icon">♿</span>
        <span className="accessibility-text">Erişilebilirlik</span>
      </button>

      {/* Erişilebilirlik Paneli */}
      {isOpen && (
        <div 
          className="accessibility-panel"
          role="dialog"
          aria-labelledby="accessibility-title"
          aria-modal="true"
        >
          <div className="accessibility-header">
            <h2 id="accessibility-title">🔍 Erişilebilirlik Ayarları</h2>
            <button 
              className="close-btn"
              onClick={() => setIsOpen(false)}
              aria-label="Paneli kapat"
            >
              ×
            </button>
          </div>

          <div className="accessibility-content">
            
            {/* Görsel Erişilebilirlik */}
            <section className="accessibility-section">
              <h3>👁️ Görsel Erişilebilirlik</h3>
              
              <div className="setting-item">
                <label htmlFor="fontSize">Yazı Boyutu:</label>
                <select 
                  id="fontSize"
                  value={settings.fontSize}
                  onChange={(e) => handleSettingChange('fontSize', e.target.value)}
                >
                  <option value="normal">Normal (16px)</option>
                  <option value="large">Büyük (18px)</option>
                  <option value="xlarge">Çok Büyük (22px)</option>
                </select>
              </div>

              <div className="setting-item">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={settings.highContrast}
                    onChange={(e) => handleSettingChange('highContrast', e.target.checked)}
                  />
                  <span className="checkmark"></span>
                  Yüksek Kontrast
                </label>
                <small>Renkler arasındaki kontrastı artırır</small>
              </div>

              <div className="setting-item">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={settings.reducedMotion}
                    onChange={(e) => handleSettingChange('reducedMotion', e.target.checked)}
                  />
                  <span className="checkmark"></span>
                  Azaltılmış Hareket
                </label>
                <small>Animasyonları ve geçişleri azaltır</small>
              </div>
            </section>

            {/* Navigasyon Erişilebilirlik */}
            <section className="accessibility-section">
              <h3>⌨️ Navigasyon</h3>
              
              <div className="setting-item">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={settings.keyboardNav}
                    onChange={(e) => handleSettingChange('keyboardNav', e.target.checked)}
                  />
                  <span className="checkmark"></span>
                  Klavye Navigasyonu
                </label>
                <small>Tab ile gezinme ve kısayol tuşları</small>
              </div>

              <div className="setting-item">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={settings.focusIndicator}
                    onChange={(e) => handleSettingChange('focusIndicator', e.target.checked)}
                  />
                  <span className="checkmark"></span>
                  Gelişmiş Odak Göstergesi
                </label>
                <small>Seçili öğeleri daha belirgin gösterir</small>
              </div>
            </section>

            {/* Ekran Okuyucu Desteği */}
            <section className="accessibility-section">
              <h3>🔊 Ekran Okuyucu</h3>
              
              <div className="setting-item">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={settings.screenReader}
                    onChange={(e) => handleSettingChange('screenReader', e.target.checked)}
                  />
                  <span className="checkmark"></span>
                  Ekran Okuyucu Desteği
                </label>
                <small>NVDA, JAWS ve diğer ekran okuyucular için optimizasyon</small>
              </div>

              <div className="setting-item">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={settings.autoRead}
                    onChange={(e) => handleSettingChange('autoRead', e.target.checked)}
                  />
                  <span className="checkmark"></span>
                  Otomatik Okuma
                </label>
                <small>Chatbot yanıtlarını otomatik seslendirir</small>
              </div>
            </section>

          </div>

          <div className="accessibility-footer">
            <button 
              className="reset-btn"
              onClick={resetSettings}
            >
              🔄 Ayarları Sıfırla
            </button>
            
            <div className="accessibility-info">
              <h4>📋 Klavye Kısayolları:</h4>
              <ul>
                <li><kbd>Alt + A</kbd>: Erişilebilirlik paneli</li>
                <li><kbd>Tab</kbd>: Sonraki öğe</li>
                <li><kbd>Shift + Tab</kbd>: Önceki öğe</li>
                <li><kbd>Enter</kbd>: Mesaj gönder</li>
                <li><kbd>Esc</kbd>: Paneli kapat</li>
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Klavye Kısayolları */}
      <KeyboardShortcuts 
        isAccessibilityOpen={isOpen}
        onToggleAccessibility={() => setIsOpen(!isOpen)}
        settings={settings}
      />
    </>
  );
}

// Klavye kısayolları bileşeni
function KeyboardShortcuts({ isAccessibilityOpen, onToggleAccessibility, settings }) {
  useEffect(() => {
    const handleKeyDown = (event) => {
      // Alt + A: Erişilebilirlik paneli
      if (event.altKey && event.key === 'a') {
        event.preventDefault();
        onToggleAccessibility();
      }

      // Esc: Paneli kapat
      if (event.key === 'Escape' && isAccessibilityOpen) {
        onToggleAccessibility();
      }

      // Screen reader duyuru
      if (settings.screenReader && event.key === 'F1') {
        event.preventDefault();
        const announcement = "HukukPusulası erişilebilir tüketici hakları platformuna hoş geldiniz. Alt+A ile erişilebilirlik ayarlarını açabilirsiniz.";
        announceToScreenReader(announcement);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isAccessibilityOpen, onToggleAccessibility, settings.screenReader]);

  const announceToScreenReader = (message) => {
    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', 'assertive');
    announcement.setAttribute('aria-atomic', 'true');
    announcement.className = 'sr-only';
    announcement.textContent = message;
    document.body.appendChild(announcement);
    
    setTimeout(() => {
      if (document.body.contains(announcement)) {
        document.body.removeChild(announcement);
      }
    }, 2000);
  };

  return null;
}

export default AccessibilityPanel;