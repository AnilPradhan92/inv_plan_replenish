import React, { useState, useEffect } from 'react';

const DataSourcesPage = () => {
  const [rows, setRows] = useState([
    { name: 'Inventory', lastUpdated: '', key: 'inventory' },
    { name: 'Sales', lastUpdated: '', key: 'sales' },
    { name: 'DRR', lastUpdated: '', key: 'drr' },
    { name: 'Replenishment', lastUpdated: '', key: 'replenishment' }
  ]);
  const [loading, setLoading] = useState({});

  const fetchLastUpdated = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/sync/status/');
      const data = await res.json();
      setRows(prev =>
        prev.map(row => ({
          ...row,
          lastUpdated: data[row.key] || 'N/A'
        }))
      );
    } catch (err) {
      console.error('Error fetching update timestamps:', err);
    }
  };

  useEffect(() => {
    fetchLastUpdated();
  }, []);

  const handleSync = async (key) => {
    setLoading((prev) => ({ ...prev, [key]: true }));
    try {
      const res = await fetch(`http://localhost:8000/api/sync/${key}/`, {
        method: 'POST'
      });
      const result = await res.json();
      if (res.ok) {
        alert(`✅ Sync complete: ${result.message || 'Done'}`);
      } else {
        alert(`❌ Sync failed: ${result.error || 'Unknown error'}`);
      }
      await fetchLastUpdated();
    } catch (err) {
      console.error('Sync failed:', err);
      alert('❌ Sync failed');
    } finally {
      setLoading((prev) => ({ ...prev, [key]: false }));
    }
  };

  return (
    <div style={{ marginLeft: '10px', padding: '20px' }}>
      <h2>🔗 Data Sources</h2>
      <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '20px' }}>
        <thead>
          <tr style={{ backgroundColor: '#f0f0f0' }}>
            <th style={thStyle}>Database</th>
            <th style={thStyle}>Last update date</th>
            <th style={thStyle}>Sync</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, idx) => (
            <tr key={idx}>
              <td style={tdStyle}>{row.name}</td>
              <td style={tdStyle}>{row.lastUpdated}</td>
              <td style={tdStyle}>
                <button
                  style={{
                    ...btnStyle,
                    backgroundColor: loading[row.key] ? '#999' : btnStyle.backgroundColor,
                    cursor: loading[row.key] ? 'not-allowed' : 'pointer'
                  }}
                  onClick={() => handleSync(row.key)}
                  disabled={loading[row.key]}
                >
                  {loading[row.key] ? '⏳ Syncing...' : 'Sync'}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

const thStyle = { padding: '10px', textAlign: 'left', borderBottom: '1px solid #ccc' };
const tdStyle = { padding: '10px', borderBottom: '1px solid #eee' };
const btnStyle = {
  padding: '6px 12px',
  backgroundColor: '#1976d2',
  color: 'white',
  border: 'none',
  borderRadius: 4,
  cursor: 'pointer'
};

export default DataSourcesPage;
