import React, { useState, useEffect } from 'react';
import { FaEdit, FaTrash, FaWarehouse } from 'react-icons/fa';

const WarehousePage = ({ collapsed }) => {
  const [warehouses, setWarehouses] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState({ id: null, name: '', doh: '', maxInventory: '' });
  const [isEditing, setIsEditing] = useState(false);

  const sidebarWidth = collapsed ? '60px' : '10px';

  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  const fetchWarehouses = async () => {
    try {
      const res = await fetch(`${API_URL}/api/warehouses/`);
      const data = await res.json();
      setWarehouses(data);
    } catch (err) {
      console.error('Failed to fetch warehouses:', err);
    }
  };

  useEffect(() => {
    fetchWarehouses();
  }, []);

  const handleOpen = () => {
    setForm({ id: null, name: '', doh: '', maxInventory: '' });
    setIsEditing(false);
    setShowModal(true);
  };

  const handleClose = () => setShowModal(false);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSave = async () => {
    const payload = {
      name: form.name,
      doh: parseInt(form.doh),
      max_inventory: parseInt(form.maxInventory)
    };

    try {
      let res, data;

      if (isEditing) {
        res = await fetch(`${API_URL}/api/warehouses/${form.id}/`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        data = await res.json();
        setWarehouses(warehouses.map(w => (w.id === data.id ? data : w)));
      } else {
        res = await fetch(`${API_URL}/api/warehouses/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        data = await res.json();
        setWarehouses([...warehouses, data]);
      }
      setShowModal(false);
    } catch (err) {
      console.error('Error saving warehouse:', err);
    }
  };

  const handleEdit = (wh) => {
    setForm({
      id: wh.id,
      name: wh.name,
      doh: wh.doh,
      maxInventory: wh.max_inventory
    });
    setIsEditing(true);
    setShowModal(true);
  };

  const handleDelete = async (id) => {
    try {
      await fetch(`${API_URL}/api/warehouses/${id}/`, {
        method: 'DELETE'
      });
      setWarehouses(warehouses.filter(w => w.id !== id));
    } catch (err) {
      console.error('Error deleting warehouse:', err);
    }
  };

  return (
    <div style={{ marginLeft: sidebarWidth, padding: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
        <FaWarehouse size={24} style={{ marginRight: '10px' }} />
        <h2 style={{ textAlign: 'center' }}>Warehouse Settings</h2>
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '10px' }}>
        <button onClick={handleOpen} style={buttonStyle}>+ Add Warehouse</button>
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
        <table style={{ width: '100%', maxWidth: '1000px', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ backgroundColor: '#f0f0f0' }}>
              <th style={thStyle}>Name</th>
              <th style={thStyle}>DOH</th>
              <th style={thStyle}>Max Inventory</th>
              <th style={thStyle}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {warehouses.length === 0 ? (
              <tr><td colSpan={4} style={{ textAlign: 'center', padding: '20px' }}>No warehouses added yet.</td></tr>
            ) : (
              warehouses.map((wh) => (
                <tr key={wh.id}>
                  <td style={tdStyle}>{wh.name}</td>
                  <td style={tdStyle}>{wh.doh}</td>
                  <td style={tdStyle}>{wh.max_inventory}</td>
                  <td style={tdStyle}>
                    <button onClick={() => handleEdit(wh)} style={iconButtonStyle}><FaEdit /></button>
                    <button onClick={() => handleDelete(wh.id)} style={iconButtonStyleRed}><FaTrash /></button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {showModal && (
        <div style={modalBackdrop}>
          <div style={modalContent}>
            <h3>{isEditing ? 'Edit' : 'Add'} Warehouse</h3>
            <input name="name" value={form.name} onChange={handleChange} placeholder="Warehouse Name" style={inputStyle} />
            <input name="doh" value={form.doh} onChange={handleChange} placeholder="DOH" type="number" style={inputStyle} />
            <input name="maxInventory" value={form.maxInventory} onChange={handleChange} placeholder="Max Inventory" type="number" style={inputStyle} />
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 20 }}>
              <button onClick={handleClose} style={btnStyleGray}>Cancel</button>
              <button onClick={handleSave} style={btnStyleBlue}>Save</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Styles
const thStyle = { padding: '10px', textAlign: 'left', borderBottom: '1px solid #ddd' };
const tdStyle = { padding: '10px', borderBottom: '1px solid #eee' };
const inputStyle = { padding: '8px', marginBottom: 10, width: '100%', borderRadius: 4, border: '1px solid #ccc' };
const btnStyleBlue = { padding: '8px 16px', backgroundColor: '#1976d2', color: 'white', border: 'none', borderRadius: 4, marginLeft: 10 };
const btnStyleGray = { padding: '8px 10px', backgroundColor: '#ddd', color: 'black', border: 'none', borderRadius: 4, marginRight: 5 };
const buttonStyle = { padding: '6px 12px', backgroundColor: '#1976d2', color: 'white', border: 'none', borderRadius: 4, cursor: 'pointer', fontSize: 14 };
const iconButtonStyle = { backgroundColor: '#ddd', border: 'none', padding: '6px', borderRadius: 4, marginRight: '5px', cursor: 'pointer' };
const iconButtonStyleRed = { backgroundColor: '#e74c3c', border: 'none', padding: '6px', borderRadius: 4, color: 'white', cursor: 'pointer' };

const modalBackdrop = {
  position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
  backgroundColor: 'rgba(0, 0, 0, 0.5)',
  display: 'flex', alignItems: 'center', justifyContent: 'center',
  zIndex: 1000
};

const modalContent = {
  backgroundColor: 'white',
  padding: 20,
  borderRadius: 8,
  width: 400,
  boxShadow: '0 2px 10px rgba(0,0,0,0.3)'
};

export default WarehousePage;
