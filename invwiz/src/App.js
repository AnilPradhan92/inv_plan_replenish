import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';

import Sidebar from './components/Sidebar';
import HomePage from './pages/HomePage';
import AnalyticsPage from './pages/AnalyticsPage';
import ReplenishmentPage from './pages/ReplenishmentPage';
import LogoutPage from './pages/LogoutPage';
import WarehousePage from './pages/WarehousePage';
import ProductMasterPage from './pages/ProductMasterPage';
import DataSourcesPage from './pages/DataSourcesPage';


function App() {
  const [collapsed, setCollapsed] = useState(false);

  const sidebarWidth = collapsed ? 60 : 200;

  return (
    <Router>
      <div style={{ display: 'flex' }}>
        <Sidebar collapsed={collapsed} setCollapsed={setCollapsed} />
        <div style={{ flex: 1, padding: '20px', marginLeft: sidebarWidth }}>
          <Routes>
            <Route path="/" element={<Navigate to="/home" />} />
            <Route path="/home" element={<HomePage />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
            <Route path="/replenishment" element={<ReplenishmentPage />} />
            <Route path="/settings/warehouse" element={<WarehousePage collapsed={collapsed} />} />
            <Route path="/settings/product-master" element={<ProductMasterPage />} />
            <Route path="/settings/data-sources" element={<DataSourcesPage />} />
            <Route path="/logout" element={<LogoutPage />} />            
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;
