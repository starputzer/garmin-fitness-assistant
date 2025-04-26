// src/App.jsx
import React from 'react';
import { createBrowserRouter, RouterProvider, Outlet } from 'react-router-dom';

// Einfache Komponenten für den Start
const Layout = () => (
  <div>
    <h1>Garmin Fitness Assistant</h1>
    <Outlet />
  </div>
);

const Home = () => <div>Willkommen zur Garmin Fitness Assistant App</div>;

// Router für React Router 7
const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,
    children: [
      {
        index: true,
        element: <Home />
      }
    ]
  }
]);

function App() {
  return <RouterProvider router={router} />;
}

export default App;