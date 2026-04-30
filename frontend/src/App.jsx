import React, { useState, useRef } from 'react';
import { Camera, Upload, Palette, Sun, Moon, Info, Sparkles } from 'lucide-react';

function App() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setPreview(URL.createObjectURL(selectedFile));
      setResult(null);
    }
  };

  const analyzeColors = async () => {
    if (!file) return;
    setLoading(true);
    
    const formData = new FormData();
    formData.append('file', file);

    try {
      // Assuming the API is running on localhost:8000
      const response = await fetch('http://localhost:8000/analyze', {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Error analyzing image:', error);
      // Fallback for demo purposes if backend isn't running
      alert('Certifique-se de que o backend está rodando na porta 8000.');
    } finally {
      setLoading(false);
    }
  };

  const ColorSection = ({ title, colors, icon: Icon }) => (
    <div className="glass-card" style={{ marginTop: '1rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '1rem' }}>
        <Icon size={20} color="var(--primary)" />
        <h3 style={{ fontSize: '1.2rem' }}>{title}</h3>
      </div>
      <div style={{ display: 'flex', gap: '15px', flexWrap: 'wrap' }}>
        {colors.map((color, idx) => (
          <div key={idx} style={{ textAlign: 'center' }}>
            <div 
              className="color-dot" 
              style={{ backgroundColor: color, width: '50px', height: '50px', boxShadow: '0 4px 10px rgba(0,0,0,0.2)' }}
            />
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block', marginTop: '5px' }}>
              {color.toUpperCase()}
            </span>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <div className="app-container">
      <header style={{ textAlign: 'center', maxWidth: '800px' }}>
        <div className="animate-fade-in">
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1rem' }}>
            <div style={{ background: 'var(--glass)', padding: '1rem', borderRadius: '50%', border: '1px solid var(--glass-border)' }}>
              <Palette size={40} color="var(--primary)" />
            </div>
          </div>
          <h1>Fit-Kolors</h1>
          <p className="subtitle">Descubra sua paleta de cores pessoal com inteligência artificial avançada.</p>
        </div>
      </header>

      <main style={{ width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '2rem' }}>
        {!result && (
          <div className="glass-card animate-fade-in" style={{ animationDelay: '0.2s' }}>
            <div className="upload-section">
              <div 
                className="upload-box" 
                onClick={() => fileInputRef.current.click()}
                style={{ borderStyle: preview ? 'solid' : 'dashed', overflow: 'hidden' }}
              >
                {preview ? (
                  <img src={preview} alt="Preview" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                ) : (
                  <>
                    <Camera size={48} color="var(--text-muted)" style={{ marginBottom: '1rem' }} />
                    <p style={{ color: 'var(--text-muted)' }}>Arraste uma foto ou clique para upload</p>
                  </>
                )}
              </div>
              <input 
                type="file" 
                hidden 
                ref={fileInputRef} 
                onChange={handleFileChange} 
                accept="image/*"
              />
              
              <button 
                className="btn-primary" 
                onClick={analyzeColors}
                disabled={!file || loading}
                style={{ opacity: !file || loading ? 0.6 : 1, width: '100%' }}
              >
                {loading ? <span className="loader" style={{ width: '20px', height: '20px', borderThickness: '2px' }}></span> : 'Analisar Meu Perfil'}
              </button>
            </div>
          </div>
        )}

        {result && (
          <div className="animate-fade-in" style={{ width: '100%', maxWidth: '1000px' }}>
            <div className="glass-card" style={{ marginBottom: '2rem', display: 'flex', gap: '2rem', flexWrap: 'wrap' }}>
              <div style={{ flex: '2', minWidth: '300px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '1rem' }}>
                  <Sparkles size={24} color="var(--primary)" />
                  <h2 style={{ fontSize: '1.8rem' }}>Sua Estação: {result.analysis.season}</h2>
                </div>
                <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                  <div className="season-chip">{result.analysis.undertone}</div>
                  <div className="season-chip">{result.analysis.contrast} Contraste</div>
                  <div className="season-chip" style={{ backgroundColor: 'rgba(255, 215, 0, 0.2)', color: '#ffd700' }}>
                    Metais: {result.analysis.metals}
                  </div>
                </div>
                <p style={{ marginTop: '1.5rem', color: 'var(--text-muted)', lineHeight: '1.6' }}>{result.analysis.explanation}</p>
                
                <div style={{ marginTop: '2rem' }}>
                  <h4 style={{ marginBottom: '1rem', fontSize: '1.1rem', color: 'var(--primary)' }}>Cores Detectadas em Você:</h4>
                  <div style={{ display: 'flex', gap: '15px', flexWrap: 'wrap' }}>
                    {Object.entries(result.detected_colors).map(([key, val]) => (
                      <div key={key} style={{ textAlign: 'center' }}>
                        <div className="color-dot" style={{ backgroundColor: val, border: '2px solid var(--glass-border)' }} />
                        <span style={{ fontSize: '0.7rem', textTransform: 'capitalize', display: 'block', marginTop: '5px' }}>{key}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
              
              <div style={{ flex: '1', minWidth: '250px' }}>
                {preview && (
                  <div style={{ width: '100%', aspectRatio: '1/1', borderRadius: '24px', overflow: 'hidden', border: '4px solid var(--glass-border)', marginBottom: '1.5rem' }}>
                    <img src={preview} alt="Analysed" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                  </div>
                )}
                
                <div className="glass-card" style={{ background: 'rgba(255, 255, 255, 0.03)', padding: '1rem' }}>
                  <h4 style={{ marginBottom: '1rem', fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Sparkles size={16} /> Dicas de Beleza
                  </h4>
                  <div style={{ fontSize: '0.85rem', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    <p><strong>💄 Batom:</strong> {result.makeup_tips.lipstick}</p>
                    <p><strong>😊 Blush:</strong> {result.makeup_tips.blush}</p>
                    <p><strong>👁️ Sombras:</strong> {result.makeup_tips.eyeshadow}</p>
                  </div>
                </div>
              </div>
            </div>

            <h2 style={{ textAlign: 'center', margin: '4rem 0 2rem' }}>Estudo de Harmonização Cromática</h2>
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '2rem' }}>
              {Object.entries(result.recommendations).map(([season, data]) => (
                <div key={season} className="glass-card" style={{ padding: '1.5rem', border: season === result.analysis.season.toLowerCase() ? '1px solid var(--primary)' : '1px solid var(--glass-border)' }}>
                  <h3 style={{ textTransform: 'capitalize', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '10px' }}>
                    {season} {season === result.analysis.season.toLowerCase() && <Sparkles size={18} color="var(--primary)" />}
                  </h3>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '1.5rem', fontStyle: 'italic' }}>
                    {data.theory}
                  </p>
                  
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '0.8rem', color: '#ffd700' }}>
                        <Sun size={16} /> <span style={{ fontSize: '0.9rem', fontWeight: 600 }}>Paleta de Dia</span>
                      </div>
                      <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                        {data.day.map((c, i) => (
                          <div key={i} className="color-dot" style={{ backgroundColor: c, width: '35px', height: '35px', boxShadow: '0 2px 5px rgba(0,0,0,0.2)' }} title={c} />
                        ))}
                      </div>
                    </div>
                    
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '0.8rem', color: '#a5b4fc' }}>
                        <Moon size={16} /> <span style={{ fontSize: '0.9rem', fontWeight: 600 }}>Paleta de Noite</span>
                      </div>
                      <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                        {data.night.map((c, i) => (
                          <div key={i} className="color-dot" style={{ backgroundColor: c, width: '35px', height: '35px', boxShadow: '0 2px 5px rgba(0,0,0,0.2)' }} title={c} />
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div style={{ textAlign: 'center', marginTop: '4rem' }}>
              <button className="btn-primary" onClick={() => {
                setResult(null);
                setFile(null);
                setPreview(null);
              }}>
                Fazer Novo Estudo
              </button>
            </div>
          </div>
        )}
      </main>

      <footer style={{ marginTop: '5rem', padding: '2rem', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
        &copy; 2026 Fit-Kolors. All rights reserved.
      </footer>
    </div>
  );
}

export default App;
