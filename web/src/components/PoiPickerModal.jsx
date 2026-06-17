import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { listPois } from '../api/pois';
import { FiSearch, FiMapPin, FiX, FiCheck } from 'react-icons/fi';
import Modal from './Modal';

// Fix Leaflet default icon issue with bundlers
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

const DEFAULT_CENTER = [16.047, 108.206]; // Đà Nẵng

const TYPE_COLORS = {
  restaurant: '#f97316', cafe: '#a78bfa', park: '#4ade80',
  museum: '#22d3ee', gym: '#f43f5e', library: '#facc15',
  hospital: '#f87171', school: '#60a5fa', shopping: '#e879f9',
  landmark: '#fbbf24', sport: '#34d399', other: '#94a3b8',
};

const makePoiIcon = (type, active = true) => L.divIcon({
  className: '',
  html: `<div style="
    width:24px;height:24px;border-radius:50% 50% 50% 0;
    background:${active ? (TYPE_COLORS[type] || '#6366f1') : '#475569'};
    border:2px solid #fff;transform:rotate(-45deg);
    box-shadow:0 2px 6px rgba(0,0,0,0.3);
  "></div>`,
  iconSize: [24, 24],
  iconAnchor: [12, 24],
  popupAnchor: [0, -26],
});

const makeSelectedPoiIcon = (type) => L.divIcon({
  className: '',
  html: `<div style="
    width:32px;height:32px;border-radius:50% 50% 50% 0;
    background:${TYPE_COLORS[type] || '#6366f1'};
    border:3px solid #fff;transform:rotate(-45deg);
    box-shadow:0 3px 10px rgba(0,0,0,0.4);
  "></div>`,
  iconSize: [32, 32],
  iconAnchor: [16, 32],
  popupAnchor: [0, -34],
});

function FlyToMarker({ target }) {
  const map = useMap();
  useEffect(() => {
    if (target) {
      map.flyTo([target.latitude, target.longitude], 16, { animate: true, duration: 0.8 });
    }
  }, [target, map]);
  return null;
}

export default function PoiPickerModal({ onClose, onSelect, initialPoiId }) {
  const [pois, setPois] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedPoi, setSelectedPoi] = useState(null);
  const [flyTarget, setFlyTarget] = useState(null);

  useEffect(() => {
    const fetchPois = async () => {
      try {
        const res = await listPois(1, 1000);
        const activePois = (res.data.items || []).filter(p => p.is_active);
        setPois(activePois);
        if (initialPoiId) {
          const found = activePois.find(p => p.id === initialPoiId);
          if (found) {
            setSelectedPoi(found);
            setFlyTarget(found);
          }
        }
      } catch (err) {
        console.error('Failed to load POIs', err);
      } finally {
        setLoading(false);
      }
    };
    fetchPois();
  }, [initialPoiId]);

  const filteredPois = useMemo(() => {
    const term = search.trim().toLowerCase();
    if (!term) return pois;
    return pois.filter(p => p.name.toLowerCase().includes(term));
  }, [pois, search]);

  const handleSelectPoi = (poi) => {
    setSelectedPoi(poi);
    setFlyTarget(poi);
  };

  const handleConfirm = () => {
    if (selectedPoi) {
      onSelect(selectedPoi);
      onClose();
    }
  };

  return (
    <Modal onClose={onClose} wide className="poi-picker-modal">
      <h3 className="modal-title">Select Location from POIs</h3>
      <div className="poi-picker-layout" style={{ display: 'flex', height: 600, marginTop: 16, border: '1px solid var(--border)', borderRadius: 8, overflow: 'hidden' }}>
        {/* Left list panel */}
        <div className="poi-picker-sidebar" style={{ width: 280, display: 'flex', flexDirection: 'column', borderRight: '1px solid var(--border)', background: 'var(--bg-card)' }}>
          <div style={{ padding: 12, borderBottom: '1px solid var(--border)' }}>
            <div className="search-box" style={{ width: '100%', margin: 0 }}>
              <FiSearch className="search-icon" />
              <input
                type="text"
                placeholder="Search POIs..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                style={{ width: '100%', paddingLeft: 30 }}
              />
            </div>
          </div>
          <div style={{ flex: 1, overflowY: 'auto', padding: 8 }}>
            {loading ? (
              <div style={{ display: 'flex', justifyContent: 'center', padding: 20 }}><span className="spinner"></span></div>
            ) : filteredPois.length === 0 ? (
              <div style={{ textAlign: 'center', padding: 20, color: 'var(--text-muted)', fontSize: 13 }}>No POIs found</div>
            ) : (
              filteredPois.map((p) => {
                const isSelected = selectedPoi?.id === p.id;
                return (
                  <div
                    key={p.id}
                    onClick={() => handleSelectPoi(p)}
                    style={{
                      padding: '10px 12px',
                      borderRadius: 6,
                      cursor: 'pointer',
                      background: isSelected ? 'rgba(99,102,241,0.1)' : 'transparent',
                      border: isSelected ? '1px solid var(--primary)' : '1px solid transparent',
                      marginBottom: 4,
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8,
                    }}
                  >
                    <FiMapPin style={{ color: isSelected ? 'var(--primary)' : 'var(--text-muted)', flexShrink: 0 }} />
                    <div style={{ minWidth: 0 }}>
                      <div style={{ fontWeight: isSelected ? 600 : 500, fontSize: 13, color: 'var(--text-main)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.name}</div>
                      <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Radius: {p.radius_m}m</div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Right map panel */}
        <div style={{ flex: 1, position: 'relative' }}>
          <MapContainer
            center={selectedPoi ? [selectedPoi.latitude, selectedPoi.longitude] : DEFAULT_CENTER}
            zoom={13}
            style={{ width: '100%', height: '100%' }}
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            <FlyToMarker target={flyTarget} />
            {pois.map((p) => {
              const isSelected = selectedPoi?.id === p.id;
              return (
                <React.Fragment key={p.id}>
                  <Marker
                    position={[p.latitude, p.longitude]}
                    icon={isSelected ? makeSelectedPoiIcon(p.poi_type) : makePoiIcon(p.poi_type)}
                    eventHandlers={{ click: () => setSelectedPoi(p) }}
                  >
                    <Popup>
                      <div style={{ fontFamily: 'Inter, sans-serif', fontSize: 13 }}>
                        <strong style={{ display: 'block', marginBottom: 4 }}>{p.name}</strong>
                        <span style={{ color: '#64748b', fontSize: 11 }}>Radius: {p.radius_m}m</span>
                      </div>
                    </Popup>
                  </Marker>
                  {isSelected && (
                    <Circle
                      center={[p.latitude, p.longitude]}
                      radius={p.radius_m}
                      pathOptions={{ fillColor: 'rgba(99,102,241,0.2)', color: '#6366f1', weight: 1.5 }}
                    />
                  )}
                </React.Fragment>
              );
            })}
          </MapContainer>
        </div>
      </div>
      <div className="modal-actions" style={{ marginTop: 16 }}>
        <button className="btn-secondary" onClick={onClose}>
          <FiX /> Cancel
        </button>
        <button className="btn-primary" onClick={handleConfirm} disabled={!selectedPoi}>
          <FiCheck /> Select Location
        </button>
      </div>
    </Modal>
  );
}
