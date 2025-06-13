import React, { useState, useEffect } from 'react';

const ProductMasterPage = () => {
  const [productData, setProductData] = useState([]);

  const fetchProductMaster = async () => {
  try {
    const res = await fetch('http://localhost:8000/api/product-master/');
    if (!res.ok) throw new Error('Failed to fetch');
    const data = await res.json();

    const formatted = data.map((item) => ({
      'SKU': item.sku,
      'Group1': item.group1,
      'Sub_Group1.1': item.sub_group1_1,
      'DRR': item.drr,
      'Required DOH': item.required_doh,
      'Seasonality': item.seasonality,
      'LifeCycle Status': item.lifecycle_status,
      'Current Inventory': item.current_inventory,
      'GRN Inventory': item.grn_inventory,
      'Buffer Inventory': item.buffer_inventory,
    }));

    setProductData(formatted);
  } catch (err) {
    console.error("Fetch error:", err);
  }
};
  useEffect(() => {
    fetchProductMaster();
  }, []);

  const handleDownload = () => {
    const headers = [
      'SKU', 'Group1', 'Sub_Group1.1', 'DRR', 'Required DOH',
      'Seasonality', 'LifeCycle Status', 'Current Inventory',
      'GRN Inventory', 'Buffer Inventory'
    ];
    const csvRows = [headers.join(',')];
    productData.forEach(row => {
      const values = headers.map(h => JSON.stringify(row[h] || ''));
      csvRows.push(values.join(','));
    });
    const csvContent = csvRows.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'product_master.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = async (event) => {
      const lines = event.target.result.trim().split('\n');
      const headers = lines[0].split(',');
      const data = lines.slice(1).map(line => {
        const values = line.split(',');
        const obj = {};
        headers.forEach((header, index) => {
          obj[header.trim()] = values[index]?.trim();
        });

        return {
          sku: obj['SKU'],
          group1: obj['Group1'],
          sub_group1_1: obj['Sub_Group1.1'],
          drr: parseFloat(obj['DRR']),
          required_doh: parseInt(obj['Required DOH']),
          seasonality: obj['Seasonality'],
          lifecycle_status: obj['LifeCycle Status'],
          current_inventory: parseInt(obj['Current Inventory']),
          grn_inventory: parseInt(obj['GRN Inventory']),
          buffer_inventory: parseInt(obj['Buffer Inventory']),
        };
      });

      console.log("Uploading JSON payload:", data);

      try {
        const res = await fetch('http://localhost:8000/api/product-master/upload/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
        });

        if (!res.ok) {
          const error = await res.json();
          console.error("Upload failed with response:", error);
          alert('Upload failed: ' + JSON.stringify(error));
          return;
        }

        const result = await res.json();
        alert(`✅ Upload complete!\n🆕 New SKUs: ${result.new_skus}\n✏️ Overwritten SKUs: ${result.updated_skus}`);
        await fetchProductMaster();
      } catch (err) {
        console.error('Upload error:', err);
        alert('Upload error. See console for details.');
      }
    };

    reader.readAsText(file);
  };

  return (
    <div style={{ marginLeft: '10px', padding: '10px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
        <h2>🧾 Product Master</h2>
        <div>
          <input type="file" accept=".csv" onChange={handleUpload} style={{ display: 'none' }} id="csvUpload" />
          <label htmlFor="csvUpload" style={buttonStyle}>Upload CSV</label>
          <button onClick={handleDownload} style={buttonStyle}>Download CSV</button>
        </div>
      </div>

      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ backgroundColor: '#f0f0f0' }}>
            <th style={thStyle}>SKU</th>
            <th style={thStyle}>Group1</th>
            <th style={thStyle}>Sub_Group1.1</th>
            <th style={thStyle}>DRR</th>
            <th style={thStyle}>Required DOH</th>
            <th style={thStyle}>Seasonality</th>
            <th style={thStyle}>LifeCycle Status</th>
            <th style={thStyle}>Current Inventory</th>
            <th style={thStyle}>GRN Inventory</th>
            <th style={thStyle}>Buffer Inventory</th>
          </tr>
        </thead>
        <tbody>
          {productData.length === 0 ? (
            <tr><td colSpan={10} style={{ textAlign: 'center', padding: '2px' }}>No product data uploaded yet.</td></tr>
          ) : (
            productData.map((row, idx) => (
              <tr key={idx}>
                <td style={tdStyle}>{row['SKU']}</td>
                <td style={tdStyle}>{row['Group1']}</td>
                <td style={tdStyle}>{row['Sub_Group1.1']}</td>
                <td style={tdStyle}>{row['DRR']}</td>
                <td style={tdStyle}>{row['Required DOH']}</td>
                <td style={tdStyle}>{row['Seasonality']}</td>
                <td style={tdStyle}>{row['LifeCycle Status']}</td>
                <td style={tdStyle}>{row['Current Inventory']}</td>
                <td style={tdStyle}>{row['GRN Inventory']}</td>
                <td style={tdStyle}>{row['Buffer Inventory']}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
};

const thStyle = { padding: '10px', textAlign: 'left', borderBottom: '1px solid #ccc' };
const tdStyle = { padding: '10px', borderBottom: '1px solid #eee' };
const buttonStyle = { marginLeft: 10, padding: '8px 12px', backgroundColor: '#1976d2', color: 'white', border: 'none', borderRadius: 4, cursor: 'pointer' };

export default ProductMasterPage;
