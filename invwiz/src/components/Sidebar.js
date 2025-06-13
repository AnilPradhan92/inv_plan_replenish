import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import {
  FaHome,
  FaChartBar,
  FaBoxOpen,
  FaCog,
  FaSignOutAlt,
  FaAngleLeft,
  FaAngleRight,
  FaChevronDown,
  FaChevronRight
} from 'react-icons/fa';

const Sidebar = ({ collapsed, setCollapsed }) => {
  
  const [settingsOpen, setSettingsOpen] = useState(false);

  const toggleSidebar = () => setCollapsed(!collapsed);
  const toggleSettings = () => setSettingsOpen(!settingsOpen);

  const sidebarStyle = {
    width: collapsed ? '60px' : '200px',
    height: '100vh',
    backgroundColor: '#f5f5f5',
    boxShadow: '2px 0 5px rgba(156, 148, 148, 0.1)',
    position: 'fixed',
    top: 0,
    left: 0,
    transition: 'width 0.3s ease',
    overflowX: 'hidden',
    display: 'flex',
    flexDirection: 'column',
  };

  const navItemStyle = {
    padding: '12px 20px',
    display: 'flex',
    alignItems: 'center',
    color: '#333',
    textDecoration: 'none',
    whiteSpace: 'nowrap',
    cursor: 'pointer'
  };

  const subItemStyle = {
    padding: '8px 40px',
    color: '#555',
    textDecoration: 'none',
    fontSize: '0.9rem',
    display: collapsed ? 'none' : 'block'
  };

  const activeStyle = {
    backgroundColor: '#e0e0e0',
    fontWeight: 'bold'
  };

  return (
    <div style={sidebarStyle}>
      <div
        style={{
          textAlign: 'center',
          padding: '20px 0',
          cursor: 'pointer',
          borderBottom: '1px solid #ddd'
        }}
        onClick={toggleSidebar}
      >
        {collapsed ? <FaAngleRight size={20} /> : <FaAngleLeft size={20} />}
      </div>

      <NavLink to="/home" style={navItemStyle} activeStyle={activeStyle}>
        <FaHome style={{ marginRight: collapsed ? 0 : 10 }} />
        {!collapsed && 'Home'}
      </NavLink>

      <NavLink to="/analytics" style={navItemStyle} activeStyle={activeStyle}>
        <FaChartBar style={{ marginRight: collapsed ? 0 : 10 }} />
        {!collapsed && 'Analytics'}
      </NavLink>

      <NavLink to="/replenishment" style={navItemStyle} activeStyle={activeStyle}>
        <FaBoxOpen style={{ marginRight: collapsed ? 0 : 10 }} />
        {!collapsed && 'Replenishment'}
      </NavLink>

      {/* Settings Parent */}
      <div onClick={toggleSettings} style={navItemStyle}>
        <FaCog style={{ marginRight: collapsed ? 0 : 10 }} />
        {!collapsed && (
          <>
            Settings
            <span style={{ marginLeft: 'auto' }}>
              {settingsOpen ? <FaChevronDown /> : <FaChevronRight />}
            </span>
          </>
        )}
      </div>

      {/* Settings Submenu */}
      {settingsOpen && !collapsed && (
        <>
          <NavLink to="/settings/warehouse" style={subItemStyle} activeStyle={activeStyle}>
            Warehouse
          </NavLink>
          <NavLink to="/settings/product-master" style={subItemStyle} activeStyle={activeStyle}>
            Product Master
          </NavLink>
          <NavLink to="/settings/data-sources" style={subItemStyle} activeStyle={activeStyle}>
            Data Sources
          </NavLink>
        </>
      )}

      <NavLink to="/logout" style={navItemStyle} activeStyle={activeStyle}>
        <FaSignOutAlt style={{ marginRight: collapsed ? 0 : 10 }} />
        {!collapsed && 'Logout'}
      </NavLink>
    </div>
  );
};

export default Sidebar;
