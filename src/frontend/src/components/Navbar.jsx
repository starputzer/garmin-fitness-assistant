// src/frontend/components/Navbar.jsx
import React from 'react';
import { NavLink } from 'react-router-dom';
import { useUser } from '../context/UserContext';
import './Navbar.css';

function Navbar() {
  const { user } = useUser();

  return (
    <nav className="navbar">
      <div className="logo">
        <NavLink to="/">Garmin Fitness Assistant</NavLink>
      </div>
      
      <ul className="nav-links">
        <li>
          <NavLink to="/" end>Dashboard</NavLink>
        </li>
        <li>
          <NavLink to="/upload">Daten Upload</NavLink>
        </li>
        <li>
          <NavLink to="/analysis">Laufanalyse</NavLink>
        </li>
        <li>
          <NavLink to="/training-plan">Trainingsplan</NavLink>
        </li>
        <li>
          <NavLink to="/recommendations">Empfehlungen</NavLink>
        </li>
      </ul>
      
      <div className="user-info">
        {user ? user.name : 'Gast'}
      </div>
    </nav>
  );
}

export default Navbar;