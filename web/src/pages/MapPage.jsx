import { useState, useEffect, useCallback, useRef } from 'react';
import {
  MapContainer, TileLayer, Marker, Popup, Circle, useMapEvents, useMap
} from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { listPois, createPoi, updatePoi, deletePoi } from '../api/pois';
import {
  FiMapPin, FiPlus, FiTrash2, FiEdit2, FiX, FiCheck,
  FiSearch, FiEye, FiEyeOff, FiNavigation
} from 'react-icons/fi';
import Modal from '../components/Modal';

// Fix Leaflet default icon issue with bundlers
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

const POI_TYPES = [
  'restaurant', 'cafe', 'park', 'museum', 'gym', 'library',
  'hospital', 'school', 'shopping', 'landmark', 'sport', 'other'
];

const TYPE_COLORS = {
  restaurant: '#f97316', cafe: '#a78bfa', park: '#4ade80',
  museum: '#22d3ee', gym: '#f43f5e', library: '#facc15',
  hospital: '#f87171', school: '#60a5fa', shopping: '#e879f9',
  landmark: '#fbbf24', sport: '#34d399', other: '#94a3b8',
};

const makePoiIcon = (type, active = true) => L.divIcon({
  className: '',
  html: `<div style="
    width:28px;height:28px;border-radius:50% 50% 50% 0;
    background:${active ? (TYPE_COLORS[type] || '#6366f1') : '#475569'};
    border:2px solid #fff;transform:rotate(-45deg);
    box-shadow:0 2px 8px rgba(0,0,0,0.4);
    opacity:${active ? 1 : 0.5};
  "></div>`,
  iconSize: [28, 28],
  iconAnchor: [14, 28],
  popupAnchor: [0, -30],
});

// Selected/highlighted icon — larger + pulsing ring
const makeSelectedPoiIcon = (type) => {
  const color = TYPE_COLORS[type] || '#6366f1';
  return L.divIcon({
    className: '',
    html: `
      <div style="position:relative;width:44px;height:44px;">
        <div style="
          position:absolute;inset:0;border-radius:50%;
          background:${color};opacity:0.25;
          animation:poiPulse 1.2s ease-out infinite;
        "></div>
        <div style="
          position:absolute;inset:8px;border-radius:50% 50% 50% 0;
          background:${color};border:3px solid #fff;
          transform:rotate(-45deg);
          box-shadow:0 3px 12px rgba(0,0,0,0.5);
        "></div>
      </div>
      <style>
        @keyframes poiPulse {
          0%   { transform:scale(0.8); opacity:0.5; }
          70%  { transform:scale(1.8); opacity:0; }
          100% { transform:scale(0.8); opacity:0; }
        }
      </style>`,
    iconSize: [44, 44],
    iconAnchor: [22, 38],
    popupAnchor: [0, -42],
  });
};

// Click handler component
function MapClickHandler({ onMapClick }) {
  useMapEvents({ click: (e) => onMapClick(e.latlng) });
  return null;
}

// Smooth fly-to + open popup when the target is a POI marker
function FlyToMarker({ target, markerRefs }) {
  const map = useMap();
  useEffect(() => {
    if (!target) return;
    map.flyTo([target.lat, target.lng], 17, { animate: true, duration: 0.8 });
    if (!target.id) return undefined;
    // Open popup after fly animation finishes
    const timer = setTimeout(() => {
      const marker = markerRefs.current[target.id];
      if (marker) marker.openPopup();
    }, 900);
    return () => clearTimeout(timer);
  }, [target]);
  return null;
}

const DEFAULT_CENTER = [16.047, 108.206]; // Đà Nẵng

export default function MapPage() {
  const [pois, setPois] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filterType, setFilterType] = useState('');
  const [showInactive, setShowInactive] = useState(false);

  // Add POI state
  const [addMode, setAddMode] = useState(false);
  const [pendingLatLng, setPendingLatLng] = useState(null);
  const [addForm, setAddForm] = useState({
    name: '', poi_type: 'landmark', radius_m: 100,
    source: 'admin', external_id: '', external_type: '',
  });

  // Edit/Delete modals
  const [editModal, setEditModal] = useState(null);
  const [editForm, setEditForm] = useState({});
  const [deleteModal, setDeleteModal] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [toast, setToast] = useState(null);
  const [selectedPoi, setSelectedPoi] = useState(null);
  const [flyTarget, setFlyTarget] = useState(null); // { lat, lng, id }
  const [userLocation, setUserLocation] = useState(null);
  const markerRefs = useRef({});
  const flySequenceRef = useRef(0);

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3000);
  };

  const fetchPois = useCallback(async () => {
    setLoading(true);
    try {
      const res = await listPois(1, 1000);
      setPois(res.data.items || []);
    } catch {
      showToast('Failed to load POI list', 'error');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchPois(); }, [fetchPois]);

  const filtered = pois.filter((p) => {
    if (!showInactive && !p.is_active) return false;
    if (filterType && p.poi_type !== filterType) return false;
    if (search && !p.name.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  // ── Map click → add marker ────────────────────────────────────────────────
  const handleMapClick = (latlng) => {
    if (!addMode) return;
    setPendingLatLng(latlng);
  };

  // ── Get browser geolocation ───────────────────────────────────────────────
  const [geoLoading, setGeoLoading] = useState(false);
  const handleGetCurrentLocation = () => {
    if (!navigator.geolocation) {
      showToast('Geolocation is not supported by your browser', 'error');
      return;
    }
    setGeoLoading(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const latlng = { lat: pos.coords.latitude, lng: pos.coords.longitude };
        setUserLocation(latlng);
        flySequenceRef.current += 1;
        setFlyTarget({ ...latlng, ts: flySequenceRef.current });
        if (addMode) {
          setPendingLatLng(latlng);
        }
        showToast(addMode ? 'Using your location for the new POI' : 'Showing your current location');
        setGeoLoading(false);
      },
      (err) => {
        const msgs = {
          1: 'Location access denied',
          2: 'Unable to determine location',
          3: 'Location request timed out',
        };
        showToast(msgs[err.code] || 'Location error', 'error');
        setGeoLoading(false);
      },
      { enableHighAccuracy: true, timeout: 8000 }
    );
  };

  const handleAddSubmit = async () => {
    if (!pendingLatLng) return;
    setActionLoading(true);
    try {
      const payload = {
        name: addForm.name || 'Unnamed POI',
        poi_type: addForm.poi_type,
        latitude: pendingLatLng.lat,
        longitude: pendingLatLng.lng,
        radius_m: parseFloat(addForm.radius_m) || 100,
        source: addForm.source || 'admin',
        external_id: addForm.external_id || undefined,
        external_type: addForm.external_type || undefined,
      };
      await createPoi(payload);
      showToast('POI added successfully');
      setPendingLatLng(null);
      setAddMode(false);
      setAddForm({ name: '', poi_type: 'landmark', radius_m: 100, source: 'admin', external_id: '', external_type: '' });
      fetchPois();
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to add POI', 'error');
    } finally {
      setActionLoading(false);
    }
  };

  const openEdit = (poi) => {
    setEditModal(poi);
    setEditForm({
      name: poi.name,
      poi_type: poi.poi_type,
      radius_m: poi.radius_m,
      is_active: poi.is_active,
    });
  };

  const handleEditSave = async () => {
    setActionLoading(true);
    try {
      await updatePoi(editModal.id, {
        ...editForm,
        radius_m: parseFloat(editForm.radius_m),
      });
      showToast('POI updated');
      setEditModal(null);
      fetchPois();
    } catch {
      showToast('Update failed', 'error');
    } finally {
      setActionLoading(false);
    }
  };

  const handleDelete = async () => {
    setActionLoading(true);
    try {
      await deletePoi(deleteModal.id);
      showToast('POI deleted');
      setDeleteModal(null);
      fetchPois();
    } catch {
      showToast('Delete failed', 'error');
    } finally {
      setActionLoading(false);
    }
  };

  const flyTo = (poi) => {
    setSelectedPoi(poi.id);
    // Trigger FlyToMarker with a new object ref so useEffect fires even for same POI
    flySequenceRef.current += 1;
    setFlyTarget({ lat: poi.latitude, lng: poi.longitude, id: poi.id, ts: flySequenceRef.current });
  };

  return (
    <div className="map-page">
      {toast && <div className={`toast toast-${toast.type}`}>{toast.msg}</div>}

      {/* Sidebar panel */}
      <div className="map-sidebar">
        <div className="map-sidebar-header">
          <div>
            <h2 className="page-title" style={{ fontSize: '1.1rem' }}>
              <FiMapPin style={{ marginRight: 6, color: 'var(--accent)' }} />
              POI Management
            </h2>
            <p className="page-subtitle">{pois.length} total · {filtered.length} shown</p>
          </div>
          <button
            id="add-poi-btn"
            className={`btn-primary ${addMode ? 'btn-active-pulse' : ''}`}
            style={{ fontSize: '0.8rem', padding: '0.45rem 0.9rem' }}
            onClick={() => { setAddMode(!addMode); setPendingLatLng(null); }}
          >
            <FiPlus size={14} />
            {addMode ? 'Cancel' : 'Add POI'}
          </button>
        </div>

        <button
          id="show-my-location"
          className="btn-secondary"
          style={{ width: '100%', fontSize: '0.78rem', justifyContent: 'center', marginBottom: 10 }}
          onClick={handleGetCurrentLocation}
          disabled={geoLoading}
        >
          {geoLoading
            ? <><span className="spinner-sm" /> Getting location...</>
            : <><FiNavigation size={13} /> Show Your Location</>
          }
        </button>

        {addMode && (
          <div className="add-poi-hint">
            <div style={{ marginBottom: 8 }}>📍 Click on the map to select a location</div>
            <button
              id="get-current-location"
              className="btn-secondary"
              style={{ width: '100%', fontSize: '0.78rem', justifyContent: 'center' }}
              onClick={handleGetCurrentLocation}
              disabled={geoLoading}
            >
              {geoLoading
                ? <><span className="spinner-sm" /> Getting location...</>
                : <><FiNavigation size={13} /> My Location</>
              }
            </button>
          </div>
        )}

        {/* Filters */}
        <div className="map-filters">
          <div className="search-box" style={{ maxWidth: '100%' }}>
            <FiSearch className="search-icon" />
            <input
              id="poi-search"
              type="text"
              placeholder="Search POI..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <div className="filter-row">
            <select
              id="poi-type-filter"
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              style={{ flex: 1 }}
            >
              <option value="">All types</option>
              {POI_TYPES.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
            <button
              id="toggle-inactive"
              className={`icon-btn ${showInactive ? 'icon-btn-primary' : ''}`}
              style={{ width: 36, height: 36 }}
              title={showInactive ? 'Hide inactive' : 'Show inactive'}
              onClick={() => setShowInactive(!showInactive)}
            >
              {showInactive ? <FiEye size={15} /> : <FiEyeOff size={15} />}
            </button>
          </div>
        </div>

        {/* POI list */}
        <div className="poi-list">
          {loading ? (
            <div className="loading-center"><span className="spinner" /></div>
          ) : filtered.length === 0 ? (
            <div className="empty-row">No POIs found</div>
          ) : (
            filtered.map((poi) => (
              <div
                key={poi.id}
                id={`poi-item-${poi.id}`}
                className={`poi-list-item ${selectedPoi === poi.id ? 'selected' : ''} ${!poi.is_active ? 'inactive' : ''}`}
                onClick={() => flyTo(poi)}
              >
                <div
                  className="poi-dot"
                  style={{ background: TYPE_COLORS[poi.poi_type] || '#6366f1' }}
                />
                <div className="poi-item-info">
                  <div className="fw-600 text-sm">{poi.name}</div>
                  <div className="text-muted" style={{ fontSize: '0.72rem' }}>
                    {poi.poi_type} · r={poi.radius_m}m
                    {!poi.is_active && <span className="badge badge-danger" style={{ marginLeft: 6, fontSize: '0.65rem' }}>Hidden</span>}
                  </div>
                </div>
                <div className="poi-item-actions">
                  <button
                    id={`edit-poi-${poi.id}`}
                    className="icon-btn icon-btn-primary"
                    style={{ width: 26, height: 26 }}
                    title="Edit"
                    onClick={(e) => { e.stopPropagation(); openEdit(poi); }}
                  >
                    <FiEdit2 size={12} />
                  </button>
                  <button
                    id={`del-poi-${poi.id}`}
                    className="icon-btn icon-btn-danger"
                    style={{ width: 26, height: 26 }}
                    title="Delete"
                    onClick={(e) => { e.stopPropagation(); setDeleteModal(poi); }}
                  >
                    <FiTrash2 size={12} />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Map */}
      <div className="map-container">
        <MapContainer
          center={DEFAULT_CENTER}
          zoom={13}
          style={{ width: '100%', height: '100%' }}
          zoomControl={false}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <MapClickHandler onMapClick={handleMapClick} />
          <FlyToMarker target={flyTarget} markerRefs={markerRefs} />

          {/* Existing POIs */}
          {filtered.map((poi) => {
            const isSelected = selectedPoi === poi.id;
            return (
              <Marker
                key={poi.id}
                position={[poi.latitude, poi.longitude]}
                icon={isSelected ? makeSelectedPoiIcon(poi.poi_type) : makePoiIcon(poi.poi_type, poi.is_active)}
                ref={(el) => { if (el) markerRefs.current[poi.id] = el; }}
                eventHandlers={{ click: () => setSelectedPoi(poi.id) }}
                zIndexOffset={isSelected ? 1000 : 0}
              >
                <Popup>
                  <div style={{ minWidth: 190, fontFamily: 'Inter, sans-serif' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
                      <div style={{
                        width: 10, height: 10, borderRadius: '50%',
                        background: TYPE_COLORS[poi.poi_type] || '#6366f1', flexShrink: 0,
                      }} />
                      <div style={{ fontWeight: 700, fontSize: 14 }}>{poi.name}</div>
                    </div>
                    <div style={{ color: '#64748b', fontSize: 12, marginBottom: 4 }}>
                      {poi.poi_type} · radius {poi.radius_m}m
                    </div>
                    <div style={{ fontSize: 11, color: '#94a3b8', marginBottom: 10 }}>
                      📍 {poi.latitude.toFixed(6)}, {poi.longitude.toFixed(6)}
                    </div>
                    <div style={{ display: 'flex', gap: 6 }}>
                      <button
                        onClick={() => openEdit(poi)}
                        style={{
                          flex: 1, padding: '5px 0', background: 'rgba(99,102,241,0.15)',
                          color: '#818cf8', border: 'none', borderRadius: 6,
                          cursor: 'pointer', fontSize: 12, fontFamily: 'inherit',
                        }}
                      >✏️ Edit</button>
                      <button
                        onClick={() => setDeleteModal(poi)}
                        style={{
                          flex: 1, padding: '5px 0', background: 'rgba(248,113,113,0.15)',
                          color: '#f87171', border: 'none', borderRadius: 6,
                          cursor: 'pointer', fontSize: 12, fontFamily: 'inherit',
                        }}
                      >🗑 Delete</button>
                    </div>
                  </div>
                </Popup>
                <Circle
                  center={[poi.latitude, poi.longitude]}
                  radius={poi.radius_m}
                  pathOptions={{
                    color: TYPE_COLORS[poi.poi_type] || '#6366f1',
                    fillColor: TYPE_COLORS[poi.poi_type] || '#6366f1',
                    fillOpacity: isSelected ? 0.2 : 0.08,
                    weight: isSelected ? 2.5 : 1.5,
                  }}
                />
              </Marker>
            );
          })}

          {/* Pending new POI marker */}
          {pendingLatLng && (
            <Marker position={pendingLatLng} icon={makePoiIcon(addForm.poi_type, true)}>
              <Circle
                center={pendingLatLng}
                radius={parseFloat(addForm.radius_m) || 100}
                pathOptions={{ color: '#6366f1', fillColor: '#6366f1', fillOpacity: 0.15, weight: 2 }}
              />
            </Marker>
          )}

          {/* Admin current location marker */}
          {userLocation && (
            <Marker position={userLocation}>
              <Popup>
                <div style={{ minWidth: 150, fontFamily: 'Inter, sans-serif' }}>
                  <strong>Your location</strong>
                  <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 4 }}>
                    {userLocation.lat.toFixed(6)}, {userLocation.lng.toFixed(6)}
                  </div>
                </div>
              </Popup>
              <Circle
                center={userLocation}
                radius={35}
                pathOptions={{ color: '#3b82f6', fillColor: '#3b82f6', fillOpacity: 0.12, weight: 2 }}
              />
            </Marker>
          )}
        </MapContainer>

        {/* Add POI form overlay */}
        {addMode && pendingLatLng && (
          <div className="add-poi-overlay">
            <h4 className="add-poi-title">
              <FiMapPin size={14} /> Add New POI
            </h4>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: 10 }}>
              📍 {pendingLatLng.lat.toFixed(6)}, {pendingLatLng.lng.toFixed(6)}
            </div>
            <div className="modal-form" style={{ gap: 8 }}>
              <label>Location name *</label>
              <input
                id="new-poi-name"
                type="text"
                placeholder="Enter POI name..."
                value={addForm.name}
                onChange={(e) => setAddForm(f => ({ ...f, name: e.target.value }))}
                autoFocus
              />
              <label>Type</label>
              <select
                id="new-poi-type"
                value={addForm.poi_type}
                onChange={(e) => setAddForm(f => ({ ...f, poi_type: e.target.value }))}
              >
                {POI_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
              </select>
              <label>Radius (m)</label>
              <input
                id="new-poi-radius"
                type="number"
                min="10"
                max="10000"
                value={addForm.radius_m}
                onChange={(e) => setAddForm(f => ({ ...f, radius_m: e.target.value }))}
              />
            </div>
            <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
              <button className="btn-secondary" style={{ flex: 1, fontSize: '0.8rem' }}
                onClick={() => setPendingLatLng(null)}>
                <FiX size={13} /> Cancel
              </button>
              <button
                id="confirm-add-poi"
                className="btn-primary"
                style={{ flex: 1, fontSize: '0.8rem' }}
                onClick={handleAddSubmit}
                disabled={actionLoading || !addForm.name}
              >
                {actionLoading ? <span className="spinner-sm" /> : <FiCheck size={13} />}
                Save
              </button>
            </div>
          </div>
        )}

        {/* Legend */}
        <div className="map-legend">
          {Object.entries(TYPE_COLORS).slice(0, 6).map(([type, color]) => (
            <div key={type} className="legend-item">
              <div className="legend-dot" style={{ background: color }} />
              <span>{type}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Edit Modal */}
      {editModal && (
        <Modal onClose={() => setEditModal(null)}>
          <h3 className="modal-title">✏️ Edit POI</h3>
          <div className="modal-form">
            <label>Name</label>
            <input id="edit-poi-name" type="text" value={editForm.name}
              onChange={(e) => setEditForm(f => ({ ...f, name: e.target.value }))} />
            <label>Type</label>
            <select id="edit-poi-type" value={editForm.poi_type}
              onChange={(e) => setEditForm(f => ({ ...f, poi_type: e.target.value }))}>
              {POI_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
            <label>Radius (m)</label>
            <input id="edit-poi-radius" type="number" min="10" value={editForm.radius_m}
              onChange={(e) => setEditForm(f => ({ ...f, radius_m: e.target.value }))} />
            <label className="checkbox-label">
              <input id="edit-poi-active" type="checkbox" checked={editForm.is_active}
                onChange={(e) => setEditForm(f => ({ ...f, is_active: e.target.checked }))} />
              Activate POI
            </label>
          </div>
          <div className="modal-actions">
            <button className="btn-secondary" onClick={() => setEditModal(null)}><FiX /> Cancel</button>
            <button id="save-poi" className="btn-primary" onClick={handleEditSave} disabled={actionLoading}>
              {actionLoading ? <span className="spinner-sm" /> : <FiCheck />} Save
            </button>
          </div>
        </Modal>
      )}

      {/* Delete Modal */}
      {deleteModal && (
        <Modal onClose={() => setDeleteModal(null)}>
          <div className="modal-icon">🗑️</div>
          <h3 className="modal-title">Delete POI</h3>
          <p className="modal-desc">Are you sure you want to delete <strong>{deleteModal.name}</strong>?<br />
            This action cannot be undone.</p>
          <div className="modal-actions">
            <button className="btn-secondary" onClick={() => setDeleteModal(null)}><FiX /> Cancel</button>
            <button id="confirm-delete-poi" className="btn-danger" onClick={handleDelete} disabled={actionLoading}>
              {actionLoading ? <span className="spinner-sm" /> : <FiCheck />} Delete
            </button>
          </div>
        </Modal>
      )}
    </div>
  );
}
