import React, { useState, useEffect, useRef } from 'react';

// Industrial Color Profiles
const THEMES = {
  black: { bg: '#050505', panel: '#0a0a0a', border: '#1f1f1f', accent: '#888', text: '#e5e5e5', err: '#ef4444', ok: '#10b981' },
  blue:  { bg: '#020617', panel: '#0f172a', border: '#1e293b', accent: '#38bdf8', text: '#e0f2fe', err: '#f87171', ok: '#34d399' },
  green: { bg: '#052e16', panel: '#064e3b', border: '#065f46', accent: '#34d399', text: '#d1fae5', err: '#fca5a5', ok: '#6ee7b7' },
  red:   { bg: '#2a0505', panel: '#450a0a', border: '#7f1d1d', accent: '#fca5a5', text: '#fee2e2', err: '#f87171', ok: '#fde047' }
};

function App() {
  const [theme, setTheme] = useState('black');
  const [isSystemStarted, setIsSystemStarted] = useState(false);
  const [defects, setDefects] = useState([]);
  const [fullLogs, setFullLogs] = useState([]); // Stored for PDF Generation
  const [fps, setFps] = useState(0);
  const [isConnected, setIsConnected] = useState(false);
  
  const [isCameraActive, setIsCameraActive] = useState(true);
  const [uploadedImage, setUploadedImage] = useState(null);
  
  const videoRef = useRef(null);
  const lastFrameTime = useRef(Date.now());
  const colors = THEMES[theme];

  useEffect(() => {
    if (!isSystemStarted) return;

    const ws = new WebSocket('ws://127.0.0.1:8000/ws');
    ws.onopen = () => setIsConnected(true);
    ws.onclose = () => setIsConnected(false);

    ws.onmessage = (event) => {
      if (!isCameraActive) return;

      const data = JSON.parse(event.data);
      
      if (videoRef.current) {
        videoRef.current.src = "data:image/jpeg;base64," + data.image;
      }

      if (data.defects.length > 0) {
        setDefects(prev => [...new Set([...data.defects, ...prev])].slice(0, 10));
        
        // Add to historical logs for the PDF
        const time = new Date().toLocaleTimeString();
        data.defects.forEach(d => {
          setFullLogs(prev => {
            const entry = `[${time}] DETECTED: ${d.toUpperCase()}`;
            return prev.includes(entry) ? prev : [entry, ...prev];
          });
        });
      }

      const now = Date.now();
      setFps(Math.round(1000 / (now - lastFrameTime.current)));
      lastFrameTime.current = now;
    };

    return () => ws.close();
  }, [isSystemStarted, isCameraActive]);

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setIsSystemStarted(true); // Auto-start if they upload an image
    setIsCameraActive(false);
    setFps(0);

    const reader = new FileReader();
    reader.onload = (e) => {
      setUploadedImage(e.target.result);
      setDefects(['AWAITING STATIC ANALYSIS...']); 
    };
    reader.readAsDataURL(file);
  };

  const generatePDF = () => {
    const printWindow = window.open('', '', 'width=800,height=600');
    const logsHtml = fullLogs.length > 0 
      ? fullLogs.map(log => `<div style="padding: 5px 0; border-bottom: 1px solid #ccc;">${log}</div>`).join('') 
      : '<p>No anomalies detected.</p>';

    printWindow.document.write(`
      <html>
        <head>
          <title>Inspection Report</title>
          <style>body { font-family: monospace; padding: 40px; color: #000; }</style>
        </head>
        <body>
          <h1 style="border-bottom: 2px solid #000; padding-bottom: 10px;">INSPECTION ENGINE - OFFICIAL REPORT</h1>
          <p><strong>Date:</strong> ${new Date().toLocaleDateString()}</p>
          <p><strong>Hardware:</strong> NVIDIA RTX 5060 (Blackwell SM 12.0)</p>
          <p><strong>Model Base:</strong> YOLO11s (Proprietary weights)</p>
          <p><strong>Total Anomalies:</strong> ${fullLogs.length}</p>
          <br/>
          <h2>ANOMALY TIMELOG</h2>
          ${logsHtml}
        </body>
      </html>
    `);
    printWindow.document.close();
    printWindow.focus();
    setTimeout(() => { printWindow.print(); printWindow.close(); }, 250);
  };

  return (
    <div style={{ backgroundColor: colors.bg, minHeight: '100vh', color: colors.text, fontFamily: 'system-ui, sans-serif', padding: '24px', display: 'flex', flexDirection: 'column', transition: 'background-color 0.3s' }}>
      <style dangerouslySetInnerHTML={{__html: 'body { margin: 0; padding: 0; overflow-x: hidden; }'}} />
      
      {/* Top Header */}
      <header style={{ display: 'flex', justifyContent: 'space-between', borderBottom: `1px solid ${colors.border}`, paddingBottom: '16px', marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
          <div style={{ fontWeight: '600', letterSpacing: '2px', fontSize: '14px', color: colors.accent }}>
            INSPECTION_ENGINE // <span style={{ color: colors.text }}>v1.2</span>
          </div>
          {/* Micro Theme Switcher */}
          <div style={{ display: 'flex', gap: '5px' }}>
            {Object.keys(THEMES).map(t => (
              <div key={t} onClick={() => setTheme(t)} style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: THEMES[t].bg, border: `1px solid ${THEMES[t].accent}`, cursor: 'pointer', opacity: theme === t ? 1 : 0.3 }} title={`${t} theme`} />
            ))}
          </div>
        </div>
        <div style={{ display: 'flex', gap: '20px', fontFamily: 'monospace', fontSize: '13px' }}>
          <span style={{ color: colors.accent }}>ARCH: SM_12.0 (BLACKWELL)</span>
          <span style={{ color: isConnected ? colors.ok : colors.err }}>
            {isConnected ? '● WS_CONNECTED' : '● WS_DISCONNECTED'}
          </span>
          <span style={{ color: '#fbbf24' }}>FPS: {fps}</span>
        </div>
      </header>

      {/* Main Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: '24px', flex: 1 }}>
        
        {/* Massive Central Viewport */}
        <div style={{ border: `1px solid ${colors.border}`, backgroundColor: colors.panel, display: 'flex', flexDirection: 'column' }}>
          <div style={{ padding: '8px 12px', borderBottom: `1px solid ${colors.border}`, fontSize: '11px', fontFamily: 'monospace', color: colors.accent, display: 'flex', justifyContent: 'space-between' }}>
            <span>{isCameraActive ? 'LIVE_STREAM_CH01' : 'STATIC_ANALYSIS_MODE'}</span>
            <span>TARGET_RES: 640x480</span>
          </div>
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '12px', position: 'relative' }}>
            
            {!isSystemStarted ? (
              <button 
                onClick={() => setIsSystemStarted(true)}
                style={{ padding: '15px 40px', backgroundColor: 'transparent', border: `2px solid ${colors.accent}`, color: colors.accent, fontSize: '18px', letterSpacing: '3px', cursor: 'pointer', fontWeight: 'bold', fontFamily: 'monospace' }}
                onMouseOver={(e) => { e.target.style.backgroundColor = colors.accent; e.target.style.color = colors.bg; }}
                onMouseOut={(e) => { e.target.style.backgroundColor = 'transparent'; e.target.style.color = colors.accent; }}
              >
                START SENSOR FEED
              </button>
            ) : (
              <img 
                ref={videoRef} 
                src={!isCameraActive && uploadedImage ? uploadedImage : undefined}
                style={{ width: '100%', maxHeight: 'calc(100vh - 160px)', objectFit: 'contain' }} 
                alt="Scan Feed"
              />
            )}

          </div>
        </div>

        {/* Right Sidebar Controls & Logs */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          
          {/* Operations Module */}
          <div>
            <div style={{ fontSize: '11px', fontFamily: 'monospace', color: colors.accent, marginBottom: '8px' }}>// SYSTEM_OPERATIONS</div>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button 
                onClick={() => { setIsSystemStarted(true); setIsCameraActive(true); setUploadedImage(null); setDefects([]); }}
                style={{ flex: 1, padding: '12px', backgroundColor: isCameraActive ? colors.accent : colors.border, color: isCameraActive ? colors.bg : colors.text, border: 'none', cursor: 'pointer', fontSize: '12px', fontWeight: 'bold' }}
              >
                LIVE CAMERA
              </button>
              
              <label style={{ flex: 1, padding: '12px', backgroundColor: !isCameraActive ? colors.accent : colors.border, color: !isCameraActive ? colors.bg : colors.text, border: 'none', cursor: 'pointer', fontSize: '12px', fontWeight: 'bold', textAlign: 'center' }}>
                UPLOAD IMAGE
                <input type="file" accept="image/*" onChange={handleFileUpload} style={{ display: 'none' }} />
              </label>
            </div>
          </div>

          {/* Real-time Anomaly Log */}
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
            <div style={{ fontSize: '11px', fontFamily: 'monospace', color: colors.accent, marginBottom: '8px' }}>// ANOMALY_LOG</div>
            <div style={{ border: `1px solid ${colors.border}`, backgroundColor: colors.panel, flex: 1, padding: '12px', display: 'flex', flexDirection: 'column', gap: '8px', overflowY: 'auto', fontFamily: 'monospace', fontSize: '13px' }}>
              
              {defects.length === 0 && <span style={{ color: colors.accent }}>Awaiting valid detections...</span>}
              
              {defects.map((d, i) => (
                <div key={i} style={{ color: d.includes('AWAITING') ? '#fbbf24' : colors.err, borderLeft: `2px solid ${d.includes('AWAITING') ? '#fbbf24' : colors.err}`, paddingLeft: '8px' }}>
                  {d.includes('AWAITING') ? `[SYS] ${d}` : `[ERR] ${d.toUpperCase()}`}
                </div>
              ))}

            </div>
            
            {/* Download Report Button */}
            <button 
              onClick={generatePDF}
              style={{ marginTop: '8px', padding: '12px', backgroundColor: 'transparent', border: `1px solid ${colors.accent}`, color: colors.text, cursor: 'pointer', fontSize: '12px', fontWeight: 'bold', fontFamily: 'monospace' }}
              onMouseOver={(e) => { e.target.style.backgroundColor = colors.border; }}
              onMouseOut={(e) => { e.target.style.backgroundColor = 'transparent'; }}
            >
              [↓] GENERATE PDF REPORT
            </button>

          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
