// src/frontend/context/DataContext.jsx
import React, { createContext, useContext, useState, useEffect } from 'react';
import { listAvailableData } from '../services/api.service';
import { useUser } from './UserContext';

const DataContext = createContext();

export function useData() {
  return useContext(DataContext);
}

export function DataProvider({ children }) {
  const { user } = useUser();
  const [availableData, setAvailableData] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true);
        const data = await listAvailableData(user?.id);
        setAvailableData(data);
        setError(null);
      } catch (err) {
        console.error('Error fetching data list:', err);
        setError('Fehler beim Laden der Datenliste');
      } finally {
        setIsLoading(false);
      }
    };

    if (user) {
      fetchData();
    }
  }, [user]);

  const refreshData = async () => {
    try {
      setIsLoading(true);
      const data = await listAvailableData(user?.id);
      setAvailableData(data);
      setError(null);
      return true;
    } catch (err) {
      console.error('Error refreshing data list:', err);
      setError('Fehler beim Aktualisieren der Datenliste');
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const value = {
    availableData,
    isLoading,
    error,
    refreshData
  };

  return (
    <DataContext.Provider value={value}>
      {children}
    </DataContext.Provider>
  );
}