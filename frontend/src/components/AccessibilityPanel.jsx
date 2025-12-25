// src/components/AccessibilityPanel.jsx
import React, { useState, useEffect } from 'react';

function AccessibilityPanel() {
  const [isOpen, setIsOpen] = useState(false);
  const [settings, setSettings] = useState({
    fontSize: 'normal',
    highContrast: false,
    reducedMotion: false,
    focusIndicator: true,
    lineHeight: 'normal',
    letterSpacing: 'normal'
  });

  // LocalStorage'dan ayarları yükle
  useEffect(() => {
    const savedSettings = localStorage.getItem('accessibilitySettings');
    if (savedSettings) {
      try {
        const parsed = JSON.parse(savedSettings);
        setSettings(prev => ({
          ...prev,
          ...parsed,
          // Eski ayarları temizle
          screenReader: undefined,
          keyboardNav: undefined,
          voiceInput: undefined,
          autoRead: undefined
        }));
      } catch (e) {
        console.error('Ayarlar yüklenirken hata:', e);
      }
    }
  }, []);

  // Ayarları kaydet ve uygula
  useEffect(() => {
    localStorage.setItem('accessibilitySettings', JSON.stringify(settings));
    applyAccessibilitySettings(settings);
  }, [settings]);

  const applyAccessibilitySettings = (settings) => {
    const root = document.documentElement;

    // Font boyutu - CSS custom property kullan
    if (settings.fontSize === 'large') {
      root.style.setProperty('--base-font-size', '18px');
      root.style.setProperty('--font-size-multiplier', '1.125');
    } else if (settings.fontSize === 'xlarge') {
      root.style.setProperty('--base-font-size', '22px');
      root.style.setProperty('--font-size-multiplier', '1.375');
    } else {
      root.style.setProperty('--base-font-size', '16px');
      root.style.setProperty('--font-size-multiplier', '1');
    }

    // Satır yüksekliği
    if (settings.lineHeight === 'large') {
      root.style.setProperty('--line-height-multiplier', '1.8');
    } else if (settings.lineHeight === 'xlarge') {
      root.style.setProperty('--line-height-multiplier', '2.2');
    } else {
      root.style.setProperty('--line-height-multiplier', '1.5');
    }

    // Harf aralığı
    if (settings.letterSpacing === 'wide') {
      root.style.setProperty('--letter-spacing', '0.1em');
    } else if (settings.letterSpacing === 'xwide') {
      root.style.setProperty('--letter-spacing', '0.15em');
    } else {
      root.style.setProperty('--letter-spacing', 'normal');
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
  };

  const resetSettings = () => {
    const defaultSettings = {
      fontSize: 'normal',
      highContrast: false,
      reducedMotion: false,
      focusIndicator: true,
      lineHeight: 'normal',
      letterSpacing: 'normal'
    };
    setSettings(defaultSettings);
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
            <h2 id="accessibility-title">♿ Erişilebilirlik Ayarları</h2>
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
              <h3>👁️ Görsel Ayarlar</h3>

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
                <small>Tüm sayfadaki yazı boyutunu değiştirir</small>
              </div>

              <div className="setting-item">
                <label htmlFor="lineHeight">Satır Yüksekliği:</label>
                <select
                  id="lineHeight"
                  value={settings.lineHeight}
                  onChange={(e) => handleSettingChange('lineHeight', e.target.value)}
                >
                  <option value="normal">Normal</option>
                  <option value="large">Büyük</option>
                  <option value="xlarge">Çok Büyük</option>
                </select>
                <small>Metin satırları arasındaki boşluğu artırır</small>
              </div>

              <div className="setting-item">
                <label htmlFor="letterSpacing">Harf Aralığı:</label>
                <select
                  id="letterSpacing"
                  value={settings.letterSpacing}
                  onChange={(e) => handleSettingChange('letterSpacing', e.target.value)}
                >
                  <option value="normal">Normal</option>
                  <option value="wide">Geniş</option>
                  <option value="xwide">Çok Geniş</option>
                </select>
                <small>Harf arasındaki boşluğu artırır (disleksi için faydalı)</small>
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
                <small>Renkler arasındaki kontrastı artırır, okumayı kolaylaştırır</small>
              </div>
            </section>

            {/* Hareket ve Navigasyon */}
            <section className="accessibility-section">
              <h3>🎬 Hareket ve Navigasyon</h3>

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
                <small>Animasyonları ve geçişleri azaltır (vestibüler bozukluklar için)</small>
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
                <small>Klavye ile gezinirken seçili öğeleri daha belirgin gösterir</small>
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
              <h4>⌨️ Klavye Kısayolları:</h4>
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
      />
    </>
  );
}

// Klavye kısayolları bileşeni
function KeyboardShortcuts({ isAccessibilityOpen, onToggleAccessibility }) {
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
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isAccessibilityOpen, onToggleAccessibility]);

  return null;
}

export default AccessibilityPanel;
