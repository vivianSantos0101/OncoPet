import { useCallback, useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import Cropper from 'react-easy-crop'
import { RotateCw, ZoomIn, ZoomOut } from 'lucide-react'
import { cropImage } from '../image'

/**
 * Modal para ajustar a foto: arrastar para posicionar, zoom (controle,
 * roda do mouse ou pinca no celular) e girar 90 graus.
 * src: URL da imagem escolhida. onConfirm recebe o JPEG recortado.
 *
 * Renderizado direto no <body> (portal): os cards tem animacao com transform,
 * e um position: fixed dentro deles ficaria preso ao card.
 */
function PhotoCropper({ src, onCancel, onConfirm }) {
  const [crop, setCrop] = useState({ x: 0, y: 0 })
  const [zoom, setZoom] = useState(1)
  const [rotation, setRotation] = useState(0)
  const [area, setArea] = useState(null)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const onCropComplete = useCallback((_, pixels) => setArea(pixels), [])

  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape' && !saving) onCancel() }
    window.addEventListener('keydown', onKey)
    document.body.style.overflow = 'hidden'  // trava a rolagem da pagina atras do modal
    return () => {
      window.removeEventListener('keydown', onKey)
      document.body.style.overflow = ''
    }
  }, [onCancel, saving])

  const handleConfirm = async () => {
    if (!area) return
    setSaving(true)
    setError('')
    try {
      onConfirm(await cropImage(src, area, rotation))
    } catch (err) {
      setError(err.message)
      setSaving(false)
    }
  }

  const changeZoom = (delta) => setZoom(z => Math.min(3, Math.max(1, +(z + delta).toFixed(2))))

  return createPortal(
    <div className="modal-backdrop" onMouseDown={e => { if (e.target === e.currentTarget && !saving) onCancel() }}>
      <div className="modal cropper-modal" role="dialog" aria-modal="true" aria-labelledby="cropper-title">
        <h3 id="cropper-title">Ajustar foto</h3>
        <p className="modal-hint">Arraste para posicionar e use o zoom para enquadrar o pet.</p>

        <div className="cropper-area">
          <Cropper
            image={src}
            crop={crop}
            zoom={zoom}
            rotation={rotation}
            aspect={1}
            cropShape="rect"
            showGrid={false}
            onCropChange={setCrop}
            onZoomChange={setZoom}
            onCropComplete={onCropComplete}
          />
        </div>

        <div className="cropper-controls">
          <button type="button" className="notif-icon" onClick={() => changeZoom(-0.2)} aria-label="Diminuir zoom"><ZoomOut size={18} /></button>
          <input
            type="range" min={1} max={3} step={0.01} value={zoom}
            onChange={e => setZoom(Number(e.target.value))} aria-label="Zoom"
          />
          <button type="button" className="notif-icon" onClick={() => changeZoom(0.2)} aria-label="Aumentar zoom"><ZoomIn size={18} /></button>
          <button type="button" className="outline cropper-rotate" onClick={() => setRotation(r => (r + 90) % 360)}>
            <RotateCw size={16} /> Girar
          </button>
        </div>

        {error && <p className="error">{error}</p>}

        <div className="modal-actions">
          <button type="button" className="outline" onClick={onCancel} disabled={saving}>Cancelar</button>
          <button type="button" className="primary" onClick={handleConfirm} disabled={saving || !area}>
            {saving ? 'Salvando...' : 'Usar foto'}
          </button>
        </div>
      </div>
    </div>,
    document.body
  )
}

export default PhotoCropper
