import React, { useState, useEffect, useRef } from 'react';

// Industrial Color Profiles
const THEMES = {
  black: { bg: '#060606', panel: '#0e0e0e', border: '#222222', accent: '#3b82f6', text: '#e5e7eb', err: '#ef4444', ok: '#10b981', warn: '#f59e0b', sub: '#9ca3af' },
  blue:  { bg: '#020617', panel: '#0f172a', border: '#1e293b', accent: '#38bdf8', text: '#e0f2fe', err: '#f87171', ok: '#34d399', warn: '#fbbf24', sub: '#94a3b8' },
  green: { bg: '#051b11', panel: '#064e3b', border: '#065f46', accent: '#34d399', text: '#d1fae5', err: '#fca5a5', ok: '#6ee7b7', warn: '#fde047', sub: '#a7f3d0' },
  red:   { bg: '#180404', panel: '#450a0a', border: '#7f1d1d', accent: '#fca5a5', text: '#fee2e2', err: '#f87171', ok: '#fde047', warn: '#fb923c', sub: '#fca5a5' }
};

const CLASS_COLORS = {
  'open': '#ef4444',
  'short': '#dc2626',
  'pin-hole': '#f59e0b',
  'mousebite': '#8b5cf6',
  'spur': '#06b6d4',
  'copper': '#3b82f6'
};

function App() {
  const [theme, setTheme] = useState('black');
  const [isSystemStarted, setIsSystemStarted] = useState(false);
  const [activeDetections, setActiveDetections] = useState([]);
  const [fullLogs, setFullLogs] = useState([]);
  const [fps, setFps] = useState(0);
  const [isConnected, setIsConnected] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [soundEnabled, setSoundEnabled] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);

  const [isCameraActive, setIsCameraActive] = useState(true);
  const [uploadedImage, setUploadedImage] = useState(null);
  
  // SPC Analytics State
  const [spcStats, setSpcStats] = useState({
    totalScans: 0,
    passedScans: 0,
    failedScans: 0,
    defectBreakdown: { 'open': 0, 'short': 0, 'pin-hole': 0, 'mousebite': 0, 'spur': 0, 'copper': 0 }
  });

  const videoRef = useRef(null);
  const viewportContainerRef = useRef(null);
  const prevObjectUrlRef = useRef(null);
  const frameCountRef = useRef(0);
  const lastFpsUpdateRef = useRef(Date.now());
  const defectCounterRef = useRef(1);
  const colors = THEMES[theme];

  // Fullscreen change listener
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      if (viewportContainerRef.current) {
        viewportContainerRef.current.requestFullscreen().catch(err => console.error(err));
      }
    } else {
      document.exitFullscreen().catch(err => console.error(err));
    }
  };

  // Sound alert using Web Audio API
  const playAlertSound = () => {
    if (!soundEnabled) return;
    try {
      const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(880, audioCtx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(440, audioCtx.currentTime + 0.12);
      gain.gain.setValueAtTime(0.15, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.12);
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      osc.start();
      osc.stop(audioCtx.currentTime + 0.12);
    } catch (_) {}
  };

  // High-performance WebSocket stream handler
  useEffect(() => {
    if (!isSystemStarted || !isCameraActive) return;

    const ws = new WebSocket('ws://127.0.0.1:8000/ws');
    ws.binaryType = 'arraybuffer';

    ws.onopen = () => setIsConnected(true);
    ws.onclose = () => {
      setIsConnected(false);
      setFps(0);
    };

    ws.onmessage = (event) => {
      frameCountRef.current += 1;
      const now = Date.now();

      let currentDetections = [];

      // Binary ArrayBuffer stream
      if (event.data instanceof ArrayBuffer) {
        const view = new DataView(event.data);
        const headerLen = view.getUint32(2, true);
        
        if (headerLen > 0) {
          const headerBytes = new Uint8Array(event.data, 6, headerLen);
          const headerStr = new TextDecoder().decode(headerBytes);
          try {
            const meta = JSON.parse(headerStr);
            currentDetections = meta.detections || [];
          } catch (_) {}
        }

        const jpegBytes = new Uint8Array(event.data, 6 + headerLen);
        const blob = new Blob([jpegBytes], { type: 'image/jpeg' });
        const objUrl = URL.createObjectURL(blob);

        if (videoRef.current) {
          videoRef.current.src = objUrl;
        }

        if (prevObjectUrlRef.current) {
          URL.revokeObjectURL(prevObjectUrlRef.current);
        }
        prevObjectUrlRef.current = objUrl;
      } 
      // JSON / Base64 fallback
      else if (typeof event.data === 'string') {
        try {
          const data = JSON.parse(event.data);
          if (videoRef.current) {
            videoRef.current.src = 'data:image/jpeg;base64,' + data.image;
          }
          currentDetections = data.detections || [];
        } catch (_) {}
      }

      // Throttled UI state & Analytics update (4Hz)
      if (now - lastFpsUpdateRef.current >= 250) {
        const elapsedSec = (now - lastFpsUpdateRef.current) / 1000;
        const currentFps = Math.round(frameCountRef.current / elapsedSec);
        setFps(currentFps);
        frameCountRef.current = 0;
        lastFpsUpdateRef.current = now;

        setActiveDetections(currentDetections);

        // Update SPC Statistics
        setSpcStats(prev => {
          const hasDefect = currentDetections.length > 0;
          const updatedBreakdown = { ...prev.defectBreakdown };
          currentDetections.forEach(d => {
            const key = d.label.toLowerCase();
            if (updatedBreakdown[key] !== undefined) {
              updatedBreakdown[key] += 1;
            }
          });

          return {
            totalScans: prev.totalScans + 1,
            passedScans: prev.passedScans + (hasDefect ? 0 : 1),
            failedScans: prev.failedScans + (hasDefect ? 1 : 0),
            defectBreakdown: updatedBreakdown
          };
        });

        // Log tracked defect instances with ID & play audio chime
        if (currentDetections.length > 0) {
          playAlertSound();
          const time = new Date().toLocaleTimeString();
          setFullLogs(prev => {
            const newEntries = currentDetections.map(d => {
              const defId = 'DEF-' + String(defectCounterRef.current++).padStart(3, '0');
              return {
                id: defId,
                time: time,
                label: d.label.toUpperCase(),
                conf: (d.conf * 100).toFixed(0) + '%',
                text: '[' + time + '] ' + defId + ': ' + d.label.toUpperCase() + ' (' + (d.conf * 100).toFixed(0) + '%)'
              };
            });
            return [...newEntries, ...prev].slice(0, 100);
          });
        }
      }
    };

    return () => {
      ws.close();
      if (prevObjectUrlRef.current) {
        URL.revokeObjectURL(prevObjectUrlRef.current);
        prevObjectUrlRef.current = null;
      }
    };
  }, [isSystemStarted, isCameraActive, soundEnabled]);

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setIsSystemStarted(true);
    setIsCameraActive(false);
    setFps(0);
    setIsAnalyzing(true);

    const reader = new FileReader();
    reader.onload = (e) => setUploadedImage(e.target.result);
    reader.readAsDataURL(file);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('http://127.0.0.1:8000/analyze', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Server error: ' + response.status);

      const data = await response.json();
      setUploadedImage('data:image/jpeg;base64,' + data.image);

      const detections = data.detections || [];
      setActiveDetections(detections);

      const time = new Date().toLocaleTimeString();
      if (detections.length > 0) {
        playAlertSound();
        setFullLogs(prev => {
          const newEntries = detections.map(d => {
            const defId = 'STATIC-' + String(defectCounterRef.current++).padStart(3, '0');
            return {
              id: defId,
              time: time,
              label: d.label.toUpperCase(),
              conf: (d.conf * 100).toFixed(0) + '%',
              text: '[' + time + '] ' + defId + ': ' + d.label.toUpperCase() + ' (' + (d.conf * 100).toFixed(0) + '%)'
            };
          });
          return [...newEntries, ...prev].slice(0, 100);
        });
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const exportCSV = () => {
    if (fullLogs.length === 0) {
      alert('No anomaly records to export.');
      return;
    }
    const headers = 'ID,Timestamp,DefectClass,Confidence\n';
    const rows = fullLogs.map(l => l.id + ',' + l.time + ',' + l.label + ',' + l.conf).join('\n');
    const blob = new Blob([headers + rows], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'inspection_anomaly_log_' + new Date().toISOString().slice(0, 10) + '.csv';
    link.click();
  };

  const generatePDF = () => {
    const printWindow = window.open('', '', 'width=850,height=650');
    const logsHtml = fullLogs.length > 0 
      ? fullLogs.map(log => '<div style="padding: 6px 0; border-bottom: 1px solid #ddd; font-size: 13px;">' + log.text + '</div>').join('') 
      : '<p>No anomalies detected in session.</p>';

    const yieldRate = spcStats.totalScans > 0 
      ? ((spcStats.passedScans / spcStats.totalScans) * 100).toFixed(1) + '%' 
      : '100%';

    printWindow.document.write(
      '<html><head><title>Inspection Engine Report</title><style>body { font-family: monospace; padding: 40px; color: #111; }</style></head><body>' +
      '<h1 style="border-bottom: 3px solid #111; padding-bottom: 8px;">INSPECTION ENGINE - OFFICIAL QC REPORT</h1>' +
      '<p><strong>Inspection Date:</strong> ' + new Date().toLocaleString() + '</p>' +
      '<p><strong>Vision Core:</strong> NVIDIA RTX 5060 - TensorRT SM 12.0 (YOLO11s DeepPCB)</p>' +
      '<p><strong>Total Inspected Cycles:</strong> ' + spcStats.totalScans + ' | <strong>Line Yield Rate:</strong> ' + yieldRate + '</p>' +
      '<p><strong>Total Defect Instances:</strong> ' + fullLogs.length + '</p><br/>' +
      '<h2>ANOMALY AUDIT TIMELOG</h2>' + logsHtml + '</body></html>'
    );
    printWindow.document.close();
    printWindow.focus();
    setTimeout(() => { printWindow.print(); printWindow.close(); }, 250);
  };

  const yieldPct = spcStats.totalScans > 0 
    ? ((spcStats.passedScans / spcStats.totalScans) * 100).toFixed(1)
    : '100.0';

  return (
    <div style={{ backgroundColor: colors.bg, minHeight: '100vh', color: colors.text, fontFamily: 'system-ui, -apple-system, sans-serif', padding: '20px', display: 'flex', flexDirection: 'column', boxSizing: 'border-box' }}>
      <style dangerouslySetInnerHTML={{__html: 'body { margin: 0; padding: 0; overflow-x: hidden; }'}} />
      
      {/* Top Header */}
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid ' + colors.border, paddingBottom: '14px', marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ fontWeight: '700', letterSpacing: '2px', fontSize: '15px', color: colors.accent, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>INSPECTION_ENGINE</span>
            <span style={{ fontSize: '11px', padding: '2px 6px', backgroundColor: colors.border, borderRadius: '4px', color: colors.text }}>v1.3 PRO</span>
          </div>

          {/* Micro Theme Switcher */}
          <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
            {Object.keys(THEMES).map(t => (
              <div 
                key={t} 
                onClick={() => setTheme(t)} 
                style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: THEMES[t].bg, border: '2px solid ' + THEMES[t].accent, cursor: 'pointer', opacity: theme === t ? 1 : 0.35, transition: 'opacity 0.2s' }} 
                title={t + ' profile'} 
              />
            ))}
          </div>
        </div>

        {/* Live Status Indicators */}
        <div style={{ display: 'flex', gap: '16px', alignItems: 'center', fontFamily: 'monospace', fontSize: '12px' }}>
          <span style={{ color: colors.sub }}>DEVICE: RTX 5060 [TENSORRT]</span>
          
          <span style={{ color: isConnected ? colors.ok : colors.err, fontWeight: 'bold' }}>
            {isConnected ? '[LIVE WS]' : '[DISCONNECTED]'}
          </span>

          <span style={{ color: colors.warn, fontWeight: 'bold', padding: '3px 8px', backgroundColor: colors.panel, borderRadius: '4px', border: '1px solid ' + colors.border }}>
            {isCameraActive && isConnected ? fps + ' FPS' : 'N/A'}
          </span>

          <button 
            onClick={() => setSoundEnabled(!soundEnabled)}
            style={{ backgroundColor: soundEnabled ? colors.accent : colors.panel, color: soundEnabled ? colors.bg : colors.text, border: '1px solid ' + colors.border, padding: '4px 10px', borderRadius: '4px', cursor: 'pointer', fontSize: '11px', fontWeight: 'bold' }}
          >
            {soundEnabled ? 'AUDIO: ON' : 'AUDIO: OFF'}
          </button>
        </div>
      </header>

      {/* Main Layout Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '18px', flex: 1 }}>
        
        {/* Left Column: Viewport + Live SPC Quality Dashboard */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          
          {/* Main Inspection Viewport (Clean Stable Border & Fullscreen Support) */}
          <div 
            ref={viewportContainerRef}
            style={{ 
              border: '1px solid ' + colors.border, 
              backgroundColor: colors.panel, 
              borderRadius: '6px', 
              overflow: 'hidden', 
              display: 'flex', 
              flexDirection: 'column',
              position: 'relative'
            }}
          >
            {/* Viewport Control Bar */}
            <div style={{ padding: '8px 14px', borderBottom: '1px solid ' + colors.border, fontSize: '11px', fontFamily: 'monospace', color: colors.accent, display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: colors.panel }}>
              <span>{isCameraActive ? 'LIVE_STREAM // CH01 (ZERO_COPY)' : 'STATIC_ANALYSIS // LOADED_IMAGE'}</span>
              <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                <span style={{ color: colors.sub, fontSize: '11px' }}>640x480</span>
                
                <button
                  onClick={toggleFullscreen}
                  style={{
                    backgroundColor: colors.bg,
                    border: '1px solid ' + colors.border,
                    color: colors.accent,
                    padding: '3px 8px',
                    borderRadius: '3px',
                    cursor: 'pointer',
                    fontSize: '11px',
                    fontWeight: 'bold',
                    fontFamily: 'monospace'
                  }}
                >
                  {isFullscreen ? '[EXIT FULLSCREEN]' : '[FULLSCREEN]'}
                </button>
              </div>
            </div>

            {/* Video Viewport Content */}
            <div style={{ 
              flex: 1, 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center', 
              padding: isFullscreen ? '0' : '10px', 
              position: 'relative', 
              minHeight: isFullscreen ? '100vh' : '440px',
              backgroundColor: '#000'
            }}>
              {!isSystemStarted ? (
                <button
                  onClick={() => setIsSystemStarted(true)}
                  style={{ padding: '16px 44px', backgroundColor: 'transparent', border: '2px solid ' + colors.accent, color: colors.accent, fontSize: '16px', letterSpacing: '3px', cursor: 'pointer', fontWeight: 'bold', fontFamily: 'monospace', borderRadius: '4px' }}
                  onMouseOver={(e) => { e.target.style.backgroundColor = colors.accent; e.target.style.color = colors.bg; }}
                  onMouseOut={(e) => { e.target.style.backgroundColor = 'transparent'; e.target.style.color = colors.accent; }}
                >
                  START INSPECTION FEED
                </button>
              ) : (
                <img
                  ref={videoRef}
                  src={!isCameraActive && uploadedImage ? uploadedImage : undefined}
                  style={{ 
                    width: '100%', 
                    height: isFullscreen ? '100vh' : 'auto',
                    maxHeight: isFullscreen ? '100vh' : '520px', 
                    objectFit: 'contain', 
                    borderRadius: isFullscreen ? '0' : '4px', 
                    willChange: 'transform' 
                  }}
                  alt="Inspection Stream"
                />
              )}

              {/* Minimalist Floating Overlay when in Fullscreen */}
              {isFullscreen && isSystemStarted && (
                <div style={{
                  position: 'absolute',
                  top: '16px',
                  right: '16px',
                  display: 'flex',
                  gap: '10px',
                  alignItems: 'center',
                  backgroundColor: 'rgba(0,0,0,0.7)',
                  padding: '8px 14px',
                  borderRadius: '6px',
                  border: '1px solid rgba(255,255,255,0.15)',
                  fontFamily: 'monospace',
                  fontSize: '12px',
                  color: '#fff',
                  zIndex: 10
                }}>
                  <span style={{ color: colors.warn, fontWeight: 'bold' }}>{fps} FPS</span>
                  <span>|</span>
                  <span style={{ color: activeDetections.length > 0 ? colors.err : colors.ok, fontWeight: 'bold' }}>
                    {activeDetections.length > 0 ? activeDetections.length + ' ANOMALIES' : 'BOARD CLEAN'}
                  </span>
                  <button
                    onClick={toggleFullscreen}
                    style={{
                      backgroundColor: 'rgba(255,255,255,0.15)',
                      border: 'none',
                      color: '#fff',
                      padding: '4px 8px',
                      borderRadius: '3px',
                      cursor: 'pointer',
                      fontSize: '11px',
                      fontWeight: 'bold',
                      marginLeft: '8px'
                    }}
                  >
                    [EXIT]
                  </button>
                </div>
              )}

              {isAnalyzing && (
                <div style={{
                  position: 'absolute', inset: 0,
                  display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
                  backgroundColor: 'rgba(0,0,0,0.8)', gap: '12px',
                }}>
                  <div style={{
                    width: '36px', height: '36px', border: '3px solid ' + colors.border,
                    borderTop: '3px solid ' + colors.accent, borderRadius: '50%',
                    animation: 'spin 0.8s linear infinite',
                  }} />
                  <span style={{ color: colors.accent, fontFamily: 'monospace', fontSize: '13px', letterSpacing: '3px' }}>
                    ANALYZING PCB DEFECTS...
                  </span>
                  <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
                </div>
              )}
            </div>
          </div>

          {/* Real-time SPC Quality Metrics Panel */}
          <div style={{ border: '1px solid ' + colors.border, backgroundColor: colors.panel, borderRadius: '6px', padding: '14px', display: 'grid', gridTemplateColumns: '150px 1fr', gap: '18px' }}>
            
            {/* Yield Rate Gauge */}
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', borderRight: '1px solid ' + colors.border, paddingRight: '14px' }}>
              <div style={{ fontSize: '10px', fontFamily: 'monospace', color: colors.sub, marginBottom: '4px' }}>LINE YIELD RATE</div>
              <div style={{ fontSize: '32px', fontWeight: '800', fontFamily: 'monospace', color: parseFloat(yieldPct) > 90 ? colors.ok : colors.warn }}>
                {yieldPct}%
              </div>
              <div style={{ fontSize: '11px', color: colors.sub, marginTop: '4px', fontFamily: 'monospace' }}>
                {spcStats.passedScans} PASS / {spcStats.failedScans} FAIL
              </div>
            </div>

            {/* Defect Pareto Breakdown Bars */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <div style={{ fontSize: '10px', fontFamily: 'monospace', color: colors.sub, display: 'flex', justifyContent: 'space-between' }}>
                <span>DEFECT DISTRIBUTION PARETO</span>
                <span>TOTAL INSPECTED: {spcStats.totalScans}</span>
              </div>
              
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px', marginTop: '4px' }}>
                {Object.entries(spcStats.defectBreakdown).map(([defName, count]) => {
                  const barColor = CLASS_COLORS[defName] || colors.accent;
                  return (
                    <div key={defName} style={{ backgroundColor: colors.bg, padding: '6px 8px', borderRadius: '4px', border: '1px solid ' + colors.border }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', fontFamily: 'monospace', color: barColor }}>
                        <span style={{ textTransform: 'uppercase' }}>{defName}</span>
                        <span style={{ fontWeight: 'bold' }}>{count}</span>
                      </div>
                      <div style={{ width: '100%', height: '4px', backgroundColor: colors.border, borderRadius: '2px', marginTop: '4px', overflow: 'hidden' }}>
                        <div style={{ width: Math.min(100, count * 5) + '%', height: '100%', backgroundColor: barColor }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

          </div>

        </div>

        {/* Right Column: System Controls & Tracked Defect Audit Timelog */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          
          {/* Operations Switcher */}
          <div style={{ border: '1px solid ' + colors.border, backgroundColor: colors.panel, borderRadius: '6px', padding: '12px' }}>
            <div style={{ fontSize: '10px', fontFamily: 'monospace', color: colors.sub, marginBottom: '8px' }}>// SYSTEM_OPERATIONS</div>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button 
                onClick={() => { setIsSystemStarted(true); setIsCameraActive(true); setUploadedImage(null); }}
                style={{ flex: 1, padding: '10px', backgroundColor: isCameraActive ? colors.accent : colors.bg, color: isCameraActive ? '#fff' : colors.text, border: '1px solid ' + colors.border, borderRadius: '4px', cursor: 'pointer', fontSize: '11px', fontWeight: 'bold' }}
              >
                LIVE SENSOR
              </button>
              
              <label style={{ flex: 1, padding: '10px', backgroundColor: !isCameraActive ? colors.accent : colors.bg, color: !isCameraActive ? '#fff' : colors.text, border: '1px solid ' + colors.border, borderRadius: '4px', cursor: 'pointer', fontSize: '11px', fontWeight: 'bold', textAlign: 'center' }}>
                STATIC FILE
                <input type="file" accept="image/*" onChange={handleFileUpload} style={{ display: 'none' }} />
              </label>
            </div>
          </div>

          {/* Live Detected Defect Badges */}
          {activeDetections.length > 0 && (
            <div style={{ border: '1px solid ' + colors.border, backgroundColor: colors.bg, borderRadius: '6px', padding: '10px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <div style={{ fontSize: '10px', fontFamily: 'monospace', color: colors.sub, fontWeight: 'bold' }}>// ACTIVE DETECTIONS IN FRAME</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {activeDetections.map((d, i) => (
                  <span key={i} style={{ fontSize: '11px', fontFamily: 'monospace', padding: '3px 8px', borderRadius: '3px', backgroundColor: CLASS_COLORS[d.label.toLowerCase()] || colors.err, color: '#fff', fontWeight: 'bold' }}>
                    {d.label.toUpperCase()}: {(d.conf * 100).toFixed(0)}%
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Real-time Anomaly Audit Log */}
          <div style={{ border: '1px solid ' + colors.border, backgroundColor: colors.panel, borderRadius: '6px', flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
            <div style={{ padding: '10px 12px', borderBottom: '1px solid ' + colors.border, fontSize: '10px', fontFamily: 'monospace', color: colors.sub, display: 'flex', justifyContent: 'space-between' }}>
              <span>// ANOMALY_AUDIT_LOG</span>
              <span>COUNT: {fullLogs.length}</span>
            </div>
            
            <div style={{ flex: 1, padding: '10px', display: 'flex', flexDirection: 'column', gap: '6px', overflowY: 'auto', maxHeight: '280px', fontFamily: 'monospace', fontSize: '11px' }}>
              {fullLogs.length === 0 && <span style={{ color: colors.sub, padding: '10px 0' }}>No defect anomalies detected yet...</span>}
              
              {fullLogs.map((log, i) => {
                const defColor = CLASS_COLORS[log.label?.toLowerCase()] || colors.err;
                return (
                  <div key={i} style={{ borderLeft: '3px solid ' + defColor, backgroundColor: colors.bg, padding: '6px 8px', borderRadius: '0 4px 4px 0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ color: defColor, fontWeight: 'bold' }}>{log.id}: {log.label}</span>
                    <span style={{ color: colors.sub, fontSize: '10px' }}>{log.time}</span>
                  </div>
                );
              })}
            </div>
            
            {/* Export & Actions Toolbar */}
            <div style={{ display: 'flex', gap: '8px', padding: '10px', borderTop: '1px solid ' + colors.border }}>
              <button 
                onClick={exportCSV}
                style={{ flex: 1, padding: '9px', backgroundColor: colors.bg, border: '1px solid ' + colors.border, color: colors.text, cursor: 'pointer', fontSize: '11px', fontWeight: 'bold', fontFamily: 'monospace', borderRadius: '4px' }}
                onMouseOver={(e) => { e.target.style.backgroundColor = colors.border; }}
                onMouseOut={(e) => { e.target.style.backgroundColor = colors.bg; }}
              >
                CSV LOG
              </button>

              <button 
                onClick={generatePDF}
                style={{ flex: 1, padding: '9px', backgroundColor: colors.accent, border: 'none', color: '#fff', cursor: 'pointer', fontSize: '11px', fontWeight: 'bold', fontFamily: 'monospace', borderRadius: '4px' }}
              >
                PDF REPORT
              </button>
            </div>

          </div>

        </div>

      </div>
    </div>
  );
}

export default App;
