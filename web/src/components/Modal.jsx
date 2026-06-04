import { useEffect, useRef } from 'react';
import { FiX } from 'react-icons/fi';

export default function Modal({ children, onClose, wide = false }) {
  const backdropRef = useRef(null);

  useEffect(() => {
    const handler = (e) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [onClose]);

  return (
    <div
      className="modal-backdrop"
      ref={backdropRef}
      onClick={(e) => e.target === backdropRef.current && onClose()}
    >
      <div className={`modal-box ${wide ? 'modal-wide' : ''}`}>
        <button className="modal-close" onClick={onClose}><FiX /></button>
        {children}
      </div>
    </div>
  );
}
